"""판독 B 배관의 계약 — PLAN-047 §13.6 R1–R8.

이 파일이 지키는 것은 성능이 아니라 **순서와 경계**다.

- 봉인은 기본 거부이고, 여는 데에는 명시적 플래그가 필요하다(R3).
- B층 검색은 A층 동결 run 을 덮어쓸 수 없다(R4).
- run 은 정답 없이 만들어진다 — 그래야 "run 먼저, 개봉 나중"이 성립한다(R2).
- T2 판정은 A층 전용이다(R6·R7).
- 계측기(모델·프롬프트·K·온도·max_tokens·회차)는 한 글자도 바뀌지 않는다(R8).

외부 데이터가 필요한 검사는 parquet 이 있을 때만 돈다(없으면 skip · CLAUDE.md §5).
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from sdkb_paper import config
from sdkb_paper.analysis import metrics
from sdkb_paper.retrieval import layers
from sdkb_paper.validate import seal_audit


# --- R1 · A층 불변 ------------------------------------------------------------

def test_r1_a_layer_run_paths_unchanged():
    """A층 run 경로 상수가 그대로다 — 층 접미는 B 에만 붙는다."""
    from sdkb_paper.retrieval.bm25 import RUN_B0
    from sdkb_paper.retrieval.dense import RUN_B2
    from sdkb_paper.retrieval.hybrid import RUN_B3

    assert RUN_B0.name == "bm25_b0_claim.txt"
    assert RUN_B2.name == "dense_b2_claim.txt"
    assert RUN_B3.name == "hybrid_b3_rrf.txt"
    for base in (RUN_B0, RUN_B2, RUN_B3):
        assert layers.run_path_for_layer(base, layers.LAYER_A) == base


def test_r1_a_layer_qrel_resolver_unchanged():
    """A층 분할의 정답지는 examiner qrel 그대로 — 봉인 통로를 타지 않는다."""
    for split in ("train", "dev", "test", "all"):
        assert metrics.qrel_path_for_split(split) == Path(config.QREL_EXAMINER)
    assert metrics.qrel_path_for_split("test_b") == Path(config.B_QREL_SEALED)


# --- R2 · qid 원천은 분할이지 정답이 아니다 -----------------------------------

def test_r2_build_runs_b_layer_does_not_read_qrel(monkeypatch):
    """`build_runs("test_b", unseal=False)` 는 qrel 을 한 번도 읽지 않는다.

    읽으면 그 자리에서 실패시킨다 — "안 읽었을 것이다"가 아니라 "읽으면 깨진다"로 둔다.
    """
    from sdkb_paper.analysis import results_table

    def boom(*a, **kw):   # noqa: ANN002, ANN003
        raise AssertionError("판독 B 의 run 산출이 qrel 을 읽었다 — G7 위반(PLAN-047 §13.1)")

    monkeypatch.setattr(results_table, "load_qrel", boom)
    monkeypatch.setattr(results_table, "load_qrel_for_split", boom)
    monkeypatch.setattr(metrics, "load_qrel", boom, raising=False)

    called: dict[str, object] = {}

    def fake_split_qids(split: str) -> list[str]:
        called["split"] = split
        raise RuntimeError("stop-after-qids")   # 여기까지 왔으면 qid 원천은 분할이다

    monkeypatch.setattr(layers, "split_qids", fake_split_qids)
    with pytest.raises(RuntimeError, match="stop-after-qids"):
        results_table.build_runs("test_b", write=False, unseal=False)
    assert called["split"] == "test_b"


def test_r2_split_qids_is_sorted_and_qrel_free():
    if not Path(config.IR_SPLIT).exists():
        pytest.skip("split.parquet 없음 — `make corpus` 후 검증")
    qids = layers.split_qids("test_b")
    assert qids == sorted(qids)
    assert len(qids) == 200, f"B층 확증분할은 200 질의여야 한다(실측 {len(qids)})"


# --- R3 · 봉인은 기본 거부 ----------------------------------------------------

def test_r3_sealed_access_denied_by_default():
    with pytest.raises(seal_audit.SealedAccessError):
        seal_audit.open_sealed(config.B_QREL_SEALED, reason="테스트", allow=False)


def test_r3_load_qrel_for_split_b_requires_unseal():
    with pytest.raises(seal_audit.SealedAccessError):
        metrics.load_qrel_for_split("test_b", unseal=False)


def test_r3_build_runs_refuses_evaluation_without_unseal():
    """run 만 만드는 경로는 통과하고, **평가하려는 경로는 막힌다.**"""
    from sdkb_paper.analysis import results_table

    if not Path(config.IR_SPLIT).exists():
        pytest.skip("split.parquet 없음")
    with pytest.raises(seal_audit.SealedAccessError):
        results_table.build_runs("test_b", write=False, unseal=False, runs_only=False)


def test_r3_open_sealed_requires_reason(tmp_path, monkeypatch):
    target = tmp_path / "qrel_b_sealed.parquet"
    target.write_bytes(b"not-a-real-qrel")
    monkeypatch.setattr(config, "SEAL_ACCESS_LOG", tmp_path / "seal_access.jsonl")
    with pytest.raises(seal_audit.SealedAccessError):
        seal_audit.open_sealed(target, reason="  ", allow=True)


def test_r3_open_sealed_records_one_line(tmp_path, monkeypatch):
    target = tmp_path / "qrel_b_sealed.parquet"
    target.write_bytes(b"payload")
    log = tmp_path / "seal_access.jsonl"
    monkeypatch.setattr(config, "SEAL_ACCESS_LOG", log)
    seal_audit.open_sealed(target, reason="판독 B 개봉", allow=True)
    rows = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines() if x]
    assert len(rows) == 1
    assert rows[0]["sha256"] == hashlib.sha256(b"payload").hexdigest()
    assert rows[0]["reason"] == "판독 B 개봉"
    assert "test_b_layer_readout" in rows[0]["caller"]


# --- R4 · A층 run 보호 --------------------------------------------------------

def test_r4_guard_rejects_a_layer_target_for_b_layer():
    from sdkb_paper.retrieval.hybrid import RUN_B3

    with pytest.raises(ValueError, match="A층"):
        layers.guard_run_target(RUN_B3, layers.LAYER_B, RUN_B3)
    # A층 자신은 통과한다
    layers.guard_run_target(RUN_B3, layers.LAYER_A, RUN_B3)


def test_r4_b_layer_paths_are_distinct():
    from sdkb_paper.retrieval.bm25 import RUN_B0

    b = layers.run_path_for_layer(RUN_B0, layers.LAYER_B)
    assert b != RUN_B0 and b.name == "bm25_b0_claim_B.txt"


# --- R5 · 분할 선택지 ---------------------------------------------------------

@pytest.mark.parametrize("mod", [
    "sdkb_paper.analysis.metrics",
    "sdkb_paper.analysis.results_table",
    "sdkb_paper.analysis.subgroup",
    "sdkb_paper.analysis.ablation",
    "sdkb_paper.analysis.increment",
    "sdkb_paper.validate.runset",
])
def test_r5_cli_accepts_test_b(mod):
    out = subprocess.run([sys.executable, "-m", mod, "--help"],
                         capture_output=True, text=True, cwd=config.ROOT)
    assert out.returncode == 0, out.stderr
    assert "test_b" in out.stdout


# --- R6 · T-gate 는 B층을 거부한다 -------------------------------------------

def test_r6_tgate_rejects_test_b():
    out = subprocess.run([sys.executable, "-m", "sdkb_paper.validate.t_gate",
                          "--split", "test_b"],
                         capture_output=True, text=True, cwd=config.ROOT)
    assert out.returncode != 0
    assert "test_b" in (out.stderr + out.stdout)


# --- R7 · B층 층화 라벨 -------------------------------------------------------

def test_r7_b_layer_queries_get_no_label():
    """B층 질의는 공정군·거절근거가 '라벨없음' 이다 — 'other'·'unlabeled' 로 뭉치지 않는다."""
    from sdkb_paper.analysis import subgroup

    if not Path(config.IR_CORPUS).exists():
        pytest.skip("코퍼스 없음 — `make corpus` 후 검증")
    qids = layers.split_qids("test_b")
    if not qids:
        pytest.skip("test_b 분할 없음")
    fake_qrel = {qids[0]: {"any-doc"}}
    labels = subgroup.query_labels(fake_qrel)
    assert labels[qids[0]]["proc_group"] == subgroup.NO_LABEL
    assert labels[qids[0]]["rejection"] == subgroup.NO_LABEL


# --- R8 · 계측기 서명 ---------------------------------------------------------

def test_r8_rag_instrument_signature_frozen():
    """모델·프롬프트·K·온도·max_tokens·회차·팔·고장 임계 — 한 글자라도 바뀌면 실패한다.

    §1-11("프롬프트를 결과 보고 고치지 않는다")을 기억이 아니라 테스트로 지킨다. 값을
    바꾸려면 **이 해시를 함께 바꿔야** 하고, 그 커밋은 사전등록 개정으로 보인다.
    """
    from sdkb_paper.rag import frozen

    payload = json.dumps({
        "model_id": frozen.MODEL_ID,
        "k": frozen.K,
        "temperature": frozen.TEMPERATURE,
        "n_repeats": frozen.N_REPEATS,
        "max_tokens": frozen.MAX_TOKENS,
        "arms": list(frozen.ARMS),
        "system_prompt": frozen.SYSTEM_PROMPT,
        "user_template": frozen.USER_TEMPLATE,
        "fail_parse": frozen.FAILURE_THRESHOLD_PARSE,
        "fail_trunc": frozen.FAILURE_THRESHOLD_TRUNCATION,
    }, ensure_ascii=False, sort_keys=True)
    assert hashlib.sha256(payload.encode()).hexdigest() == INSTRUMENT_SHA256


def test_r8_readout_b_changes_only_what_it_may():
    """판독 B 가 바꾸는 것은 runset·split·status 셋뿐이다."""
    from sdkb_paper.rag import frozen

    a = frozen.frozen_manifest()
    b = frozen.frozen_manifest(runset=frozen.RUNSET_B, split=frozen.SPLIT_B,
                               status=frozen.STATUS_B)
    assert {k for k in a if a[k] != b[k]} == {"runset", "split", "status"}


# 계측기 서명 — PLAN-038 §12.1 + §15 수리분의 현재 상태(2026-08-08 산출).
INSTRUMENT_SHA256 = "7a472e3c1c6aa2745340b8479a66878e70355b386cc124f178e9a7e3f51ec6f5"
