"""봉인 열람 배선 회귀 — A층 접근이 원장에 남는가 (PLAN-076 · O-6).

**왜 이 파일이 있는가.** `analysis.metrics` 의 통로는 `test_b` 만 `open_sealed()` 로 보내고
A층 `test` 는 `QREL_EXAMINER` 를 직접 읽었다. 그래서 원고가 자랑하는 감사 장치가 **A층에서는
한 줄도 남기지 않았다.** 배선을 고친 뒤에는 그 우회가 **다시 생기지 않는 것**이 중요하므로,
경로·기록·소스 스캔을 함께 고정한다.

**이 테스트는 판정을 재지 않는다** — 지표는 하나도 계산하지 않는다.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from sdkb_paper import config
from sdkb_paper.analysis import metrics
from sdkb_paper.validate import seal_audit

ROOT = Path(config.ROOT)


@pytest.fixture()
def tmp_ledger(tmp_path, monkeypatch):
    """원장을 임시 파일로 돌린다 — 실제 원장(25행)은 테스트가 건드리지 않는다."""
    log = tmp_path / "seal_access.jsonl"
    monkeypatch.setattr(config, "SEAL_ACCESS_LOG", log)
    return log


def _rows(log: Path) -> list[dict]:
    if not log.exists():
        return []
    return [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines() if x]


# --- T1 · 경로 배선 -----------------------------------------------------------
def test_qrel_path_for_split():
    assert metrics.qrel_path_for_split("test") == Path(config.IR_QREL_TEST_SEALED)
    assert metrics.qrel_path_for_split("test_b") == Path(config.B_QREL_SEALED)
    for split in ("train", "dev", "all"):
        assert metrics.qrel_path_for_split(split) == Path(config.QREL_EXAMINER)


# --- T2 · S2 동일성 (PLAN-076 §7.1) -------------------------------------------
@pytest.mark.skipif(not (config.QREL_EXAMINER.exists() and config.IR_QREL_TEST_SEALED.exists()
                         and config.IR_SPLIT.exists()), reason="IR 코퍼스 산출물 없음")
def test_a_layer_set_identity(tmp_ledger):
    """봉인 사본 = 전량 qrel 의 test 부분. **배선 교체가 수치를 바꾸지 않는 근거다.**"""
    import pandas as pd

    full = metrics.load_qrel(config.QREL_EXAMINER)
    sp = pd.read_parquet(config.IR_SPLIT, columns=["doc_id", "split"])
    keep = set(sp.loc[sp["split"] == "test", "doc_id"].astype(str))
    expected = {q: pos for q, pos in full.items() if q in keep}

    assert metrics.load_qrel_for_split("test") == expected
    assert sum(len(v) for v in expected.values()) == 479
    assert len(expected) == 198


# --- T3 · A층 기록 ------------------------------------------------------------
@pytest.mark.skipif(not config.IR_QREL_TEST_SEALED.exists(), reason="A층 봉인 사본 없음")
def test_a_layer_access_is_logged(tmp_ledger):
    assert _rows(tmp_ledger) == []
    metrics.load_qrel_for_split("test", reason="회귀 테스트")
    rows = _rows(tmp_ledger)
    assert len(rows) == 1
    r = rows[0]
    assert r["layer"] == "A" and r["split"] == "test"
    assert r["file"].endswith(Path(config.IR_QREL_TEST_SEALED).name)
    assert r["caller"] == "sdkb_paper.analysis.metrics:load_qrel_for_split"
    assert r["reason"] == "회귀 테스트"


@pytest.mark.skipif(not config.QREL_EXAMINER.exists(), reason="qrel 없음")
def test_all_split_is_logged(tmp_ledger):
    """`all` 은 필터를 걸지 않아 test 정답이 들어온다 — 뒷문을 남기지 않는다(§8.2)."""
    metrics.load_qrel_for_split("all")
    rows = _rows(tmp_ledger)
    assert len(rows) == 1 and rows[0]["layer"] == "A" and rows[0]["split"] == "all"


# --- T4 · dev 무기록 ----------------------------------------------------------
@pytest.mark.skipif(not (config.QREL_EXAMINER.exists() and config.IR_SPLIT.exists()),
                    reason="qrel/분할 없음")
def test_dev_split_is_not_logged(tmp_ledger):
    metrics.load_qrel_for_split("dev")
    assert _rows(tmp_ledger) == []


# --- T5 · 우회 금지 (소스 스캔) -----------------------------------------------
def test_no_bypass_in_sources():
    """인자 없는 `load_qrel()` 과 봉인 사본 직독은 **통로를 우회한다** — 0건이어야 한다."""
    out = subprocess.run(
        ["grep", "-rn", "-e", r"load_qrel()", "-e", r"load_qrel(config.IR_QREL_TEST_SEALED)",
         "--include=*.py", str(ROOT / "src"), str(ROOT / "scripts")],
        capture_output=True, text=True)
    assert out.stdout.strip() == "", f"통로 우회 잔존:\n{out.stdout}"


# --- T6 · B층 불변 ------------------------------------------------------------
def test_b_layer_still_refuses(tmp_ledger):
    with pytest.raises(seal_audit.SealedAccessError):
        metrics.load_qrel_for_split("test_b", unseal=False)
    assert _rows(tmp_ledger) == []


def test_b_layer_reason_is_required(tmp_ledger):
    with pytest.raises(seal_audit.SealedAccessError):
        seal_audit.open_sealed(config.B_QREL_SEALED, reason="   ", allow=True)
    assert _rows(tmp_ledger) == []


def test_access_log_backfills_layer_for_legacy_rows(tmp_ledger):
    """구 25행에는 `layer` 가 없다 — 디스크를 고치지 않고 판독에서 보정한다."""
    tmp_ledger.write_text(json.dumps({"file": "data/processed/ir/qrel_b_sealed.parquet"},
                                     ensure_ascii=False) + "\n", encoding="utf-8")
    assert seal_audit.access_log()[0]["layer"] == "B"


# --- T7 · 검사기 키 함정 ------------------------------------------------------
def test_check_verdicts_rejects_unknown_key(tmp_path):
    """`allowed` 오타가 조용히 무시되지 않고 rc 2 로 멈춘다(PLAN-076 C-3)."""
    yml = tmp_path / "verdicts.yaml"
    yml.write_text(
        "meta:\n  scan_targets: []\n"
        "verdicts:\n  X:\n    forbidden: []\n    allowed: []\n", encoding="utf-8")
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_verdicts.py"),
                          "--yaml", str(yml), "--root", str(tmp_path)],
                         capture_output=True, text=True)
    assert out.returncode == 2
    assert "allowed" in out.stderr


def test_check_verdicts_accepts_real_ssot():
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_verdicts.py")],
                         cwd=ROOT, capture_output=True, text=True)
    assert out.returncode == 0, out.stdout + out.stderr
