"""자원 델타 O/O′ 게이트 테스트 (D-19 · CLAUDE.md §0 델타 유형표).

외부 산출물(코퍼스·색인·그래프) 없이 **매니페스트와 판정 로직**만 때린다. 게이트는 초록불이
쉬우면 안 되므로 경계는 전부 "미검정" 쪽으로 검증한다 — 특히 D-19 재발(자원은 자랐는데
파이프라인이 읽지 않아 Δ≡0)이 **통과로 보고되지 않는지**가 이 파일의 존재 이유다.
"""
from __future__ import annotations

import json

import pytest

from sdkb_paper import config
from sdkb_paper.validate import runset as RS


# --- fixture ------------------------------------------------------------

def _mf(label: str, *, snap_sig: str = "aaa", pipe_sig: str = "ppp",
        files: dict | None = None, tbox: dict | None = None,
        commit: str = "c0ffee", dirty: bool = False, split: str = "test",
        systems: tuple[str, ...] = ("P1", "B3_rrf")) -> dict:
    return {
        "label": label, "split": split,
        "code_git": {"commit": commit, "dirty": dirty},
        "snapshot": {"sig": snap_sig, "short": snap_sig[:12], "upstream_commit": "u1",
                     "files": files or {"sdkb-core.ttl": "h1", "sdkb-abox-patents.ttl": "h2"}},
        "pipeline": {"sig": pipe_sig, "short": pipe_sig[:12], "parts": {}},
        "tbox_counts": tbox or {"owl_class": 103, "object_property": 97,
                                "datatype_property": 81, "skos_broader": 11},
        "qrel": {"examiner": "q1", "test_sealed": "q2"},
        "runs": {s: {"file": f"sys_{s}_{split}.txt", "sha256": f"r_{s}", "n_queries": 197}
                 for s in systems},
    }


# --- 서명 결정성 --------------------------------------------------------

def test_signature_is_deterministic_and_order_independent(tmp_path):
    """같은 파일 집합은 순서가 달라도 같은 서명이어야 한다(재실행 불변)."""
    a = {"files": [{"file": "b.ttl", "sha256": "2"}, {"file": "a.ttl", "sha256": "1"}],
         "source_commit": "u1"}
    b = {"files": [{"file": "a.ttl", "sha256": "1"}, {"file": "b.ttl", "sha256": "2"}],
         "source_commit": "u1"}
    pa, pb = tmp_path / "a.json", tmp_path / "b.json"
    pa.write_text(json.dumps(a), encoding="utf-8")
    pb.write_text(json.dumps(b), encoding="utf-8")
    assert RS.snapshot_signature(pa)["sig"] == RS.snapshot_signature(pb)["sig"]
    assert RS.snapshot_signature(pa)["sig"] == RS.snapshot_signature(pa)["sig"]


def test_signature_moves_when_any_file_hash_moves(tmp_path):
    base = {"files": [{"file": "a.ttl", "sha256": "1"}], "source_commit": "u1"}
    moved = {"files": [{"file": "a.ttl", "sha256": "2"}], "source_commit": "u1"}
    pa, pb = tmp_path / "a.json", tmp_path / "b.json"
    pa.write_text(json.dumps(base), encoding="utf-8")
    pb.write_text(json.dumps(moved), encoding="utf-8")
    assert RS.snapshot_signature(pa)["sig"] != RS.snapshot_signature(pb)["sig"]


def test_missing_provenance_is_an_error_not_a_default(tmp_path):
    with pytest.raises(FileNotFoundError):
        RS.snapshot_signature(tmp_path / "없음.json")


# --- 적격심사 -----------------------------------------------------------

def test_identical_snapshot_is_vacuous_not_pass():
    """스냅샷 서명이 같으면 Δ 는 정의상 0 — 통과가 아니라 미검정이다."""
    old, new = _mf("O"), _mf("O2")           # 기본값이 같은 서명
    r = RS.eligibility(old, new, "P1")
    assert r["eligible"] is False
    assert r["verdict"] == RS.VERDICT_VACUOUS


def test_snapshot_changed_but_pipeline_unchanged_is_unreached():
    """D-19 회귀 테스트 — 자원은 자랐으나 파이프라인이 읽지 않은 상태.

    2026-08-01 실측이 정확히 이 상태였다: PROVENANCE 는 움직였는데 ir_corpus_v09.parquet 의
    sha256 이 바이트 단위로 동일했다. 이때 ΔR₁₀₀=0 이고, 그것은 H2 지지가 아니다.
    """
    old = _mf("O", snap_sig="aaa", pipe_sig="ppp")
    new = _mf("O2", snap_sig="bbb", pipe_sig="ppp")
    r = RS.eligibility(old, new, "P1")
    assert r["eligible"] is False
    assert r["verdict"] == RS.VERDICT_UNREACHED


def test_system_mismatch_is_ineligible():
    """P1 대 B3 같은 시스템 간 비교는 H2 의 증거가 아니다(CLAUDE.md §0)."""
    old = _mf("O", snap_sig="aaa", pipe_sig="ppp", systems=("B3_rrf",))
    new = _mf("O2", snap_sig="bbb", pipe_sig="qqq", systems=("P1",))
    r = RS.eligibility(old, new, "P1")
    assert r["eligible"] is False
    assert r["verdict"] == RS.VERDICT_INELIGIBLE


def test_qrel_change_is_ineligible():
    old = _mf("O", snap_sig="aaa", pipe_sig="ppp")
    new = _mf("O2", snap_sig="bbb", pipe_sig="qqq")
    new["qrel"] = {"examiner": "q1", "test_sealed": "DIFFERENT"}
    r = RS.eligibility(old, new, "P1")
    assert r["eligible"] is False
    assert r["verdict"] == RS.VERDICT_INELIGIBLE


@pytest.mark.parametrize("mut", [{"commit": "beef00"}, {"dirty": True}])
def test_code_change_is_ineligible(mut):
    """코드가 바뀌면 재측정이 아니라 새 방법이다(CLAUDE.md §2.1 안전장치)."""
    old = _mf("O", snap_sig="aaa", pipe_sig="ppp")
    new = _mf("O2", snap_sig="bbb", pipe_sig="qqq", **mut)
    r = RS.eligibility(old, new, "P1")
    assert r["eligible"] is False
    assert r["verdict"] == RS.VERDICT_INELIGIBLE


def test_split_mismatch_is_ineligible():
    old = _mf("O", snap_sig="aaa", pipe_sig="ppp", split="dev")
    new = _mf("O2", snap_sig="bbb", pipe_sig="qqq", split="test")
    assert RS.eligibility(old, new, "P1")["eligible"] is False


def test_valid_resource_delta_is_eligible():
    old = _mf("O", snap_sig="aaa", pipe_sig="ppp")
    new = _mf("O2", snap_sig="bbb", pipe_sig="qqq",
              files={"sdkb-core.ttl": "CHANGED", "sdkb-abox-patents.ttl": "h2"})
    r = RS.eligibility(old, new, "P1")
    assert r["eligible"] is True
    assert r["verdict"] == RS.VERDICT_OK


# --- 델타 유형 분류 (CLAUDE.md §0 표) --------------------------------------

def test_abox_delta_is_disqualified():
    """③ A-Box 코퍼스 델타(문서 추가)는 비교 불성립 — 자격 없음."""
    old = _mf("O", snap_sig="aaa", pipe_sig="ppp")
    new = _mf("O2", snap_sig="bbb", pipe_sig="qqq",
              files={"sdkb-core.ttl": "h1", "sdkb-abox-patents.ttl": "MORE_DOCS"})
    r = RS.eligibility(old, new, "P1")
    assert r["delta_type"] == "abox"
    assert r["eligible"] is False
    assert "abox" not in config.H2_ELIGIBLE_DELTA_TYPES


def test_tbox_delta_is_classified_by_predicate_counts():
    """① T-Box 델타 — 술어 카운트가 움직이면 T-Box 다(2026-08-01 실측: ObjectProperty 97→98)."""
    old = _mf("O", snap_sig="aaa", pipe_sig="ppp")
    new = _mf("O2", snap_sig="bbb", pipe_sig="qqq",
              files={"sdkb-core.ttl": "CHANGED", "sdkb-abox-patents.ttl": "h2"},
              tbox={"owl_class": 103, "object_property": 98, "datatype_property": 81,
                    "skos_broader": 18})
    d = RS.classify_delta(old, new)
    assert d["type"] == "tbox"
    assert d["tbox_delta"]["object_property"] == [97, 98]


def test_concept_layer_delta_is_classified():
    """② 개념층 델타 — 파일은 바뀌었으나 T-Box 카운트는 불변(어휘·링크·매핑)."""
    old = _mf("O", snap_sig="aaa", pipe_sig="ppp")
    new = _mf("O2", snap_sig="bbb", pipe_sig="qqq",
              files={"sdkb-core.ttl": "CHANGED", "sdkb-abox-patents.ttl": "h2"})
    assert RS.classify_delta(old, new)["type"] == "concept"
    assert "concept" in config.H2_ELIGIBLE_DELTA_TYPES


def test_no_change_is_type_none():
    assert RS.classify_delta(_mf("O"), _mf("O2"))["type"] == "none"


def test_abox_wins_over_tbox_when_mixed():
    """섞이면 A-Box 오염이 우선 — 자격 없음을 자격 있음이 흡수하지 않는다."""
    old = _mf("O", snap_sig="aaa", pipe_sig="ppp")
    new = _mf("O2", snap_sig="bbb", pipe_sig="qqq",
              files={"sdkb-core.ttl": "CHANGED", "sdkb-abox-patents.ttl": "MORE_DOCS"},
              tbox={"owl_class": 104, "object_property": 97, "datatype_property": 81,
                    "skos_broader": 11})
    assert RS.classify_delta(old, new)["type"] == "abox"


# --- T-gate 통합 (부적격이면 T1·T2 를 **돌리지 않는다**) ----------------------

def _patch_runsets(monkeypatch, old: dict, new: dict):
    monkeypatch.setattr(RS, "load", lambda label: {old["label"]: old, new["label"]: new}[label])


def test_ineligible_comparison_never_computes_t1(monkeypatch):
    """부적격 비교의 T1·T2 수치는 만들지 않는다 — 남으면 언젠가 인용된다."""
    from sdkb_paper.validate import t1_noninferiority as T1
    from sdkb_paper.validate import t_gate as TG

    old = _mf("O", snap_sig="aaa", pipe_sig="ppp")
    new = _mf("O2", snap_sig="bbb", pipe_sig="ppp")          # unreached
    _patch_runsets(monkeypatch, old, new)

    def _boom(*a, **kw):
        raise AssertionError("부적격인데 T1 이 실행됐다")
    monkeypatch.setattr(T1, "t1_gate", _boom)

    res = TG.run_tgate(mode="resource", old_runset="O", new_runset="O2", system="P1")
    assert res["accept"] is False
    assert res["untested"] is True
    assert res["h2_eligible"] is False
    assert res["verdict"] == RS.VERDICT_UNREACHED
    assert res["t1"] is None and res["t2"] is None
    assert "미검정" in TG.format_report(res)


def test_resource_mode_requires_both_runsets():
    from sdkb_paper.validate import t_gate as TG

    with pytest.raises(ValueError):
        TG.run_tgate(mode="resource", old_runset="O", new_runset=None)


def test_system_mode_stays_the_default():
    """기존 동작 불변 — 기본 모드는 여전히 system 이고 기본 run 은 P1 대 B3 다."""
    import inspect

    from sdkb_paper.validate import t_gate as TG

    p = inspect.signature(TG.run_tgate).parameters
    assert p["mode"].default == "system"
    assert p["split"].default == "dev"
    assert p["system"].default == "P1"
    src = inspect.getsource(TG.run_tgate)
    assert 'run_path("P1", split)' in src and 'run_path("B3_rrf", split)' in src


def test_freeze_copies_runs_and_records_signatures(tmp_path, monkeypatch):
    """동결은 run 사본 + 매니페스트를 남긴다 — 매니페스트만으로 O/O′ 판정이 가능해야 한다."""
    src = tmp_path / "src"
    src.mkdir()
    run = src / "sys_P1_test.txt"
    run.write_text("q1 Q0 d1 1 1.0 P1\nq2 Q0 d2 1 1.0 P1\n", encoding="utf-8")

    monkeypatch.setattr(config, "RUNSET_DIR", tmp_path / "mf")
    monkeypatch.setattr(config, "IR_RUNSETS_DIR", tmp_path / "runsets")
    monkeypatch.setattr(RS, "snapshot_signature", lambda *a, **k:
                        {"sig": "aaa", "short": "aaa", "upstream_commit": "u1", "files": {}})
    monkeypatch.setattr(RS, "pipeline_signature", lambda: {"sig": "ppp", "short": "ppp", "parts": {}})
    monkeypatch.setattr(RS, "tbox_counts", lambda *a, **k: {"owl_class": 103})
    monkeypatch.setattr(RS, "qrel_signature", lambda: {"examiner": "q1", "test_sealed": "q2"})

    out = RS.freeze("O_test", "test", sources={"P1": run})
    mf = json.loads(out.read_text(encoding="utf-8"))
    assert mf["runs"]["P1"]["n_queries"] == 2
    assert (tmp_path / "runsets" / "O_test" / "sys_P1_test.txt").exists()
    assert RS.run_file(mf, "P1").exists()
    assert mf["snapshot"]["sig"] == "aaa" and mf["pipeline"]["sig"] == "ppp"
    assert mf["qrel"] and mf["code_git"]


def test_freeze_without_runs_is_an_error(tmp_path, monkeypatch):
    """얼릴 run 이 없으면 빈 매니페스트를 남기지 않는다 — 빈 O 는 나중에 통과로 읽힌다."""
    monkeypatch.setattr(config, "RUNSET_DIR", tmp_path / "mf")
    monkeypatch.setattr(config, "IR_RUNSETS_DIR", tmp_path / "runsets")
    with pytest.raises(FileNotFoundError):
        RS.freeze("O_empty", "test", sources={"P1": tmp_path / "없음.txt"})


def test_accept_is_still_a_product():
    """승인식은 곱이다 — 자원 모드가 생겨도 완충재는 없다."""
    from sdkb_paper.validate.t_gate import accept

    assert accept(True, True, True, True) is True
    for flags in ((False, True, True, True), (True, False, True, True),
                  (True, True, False, True), (True, True, True, False)):
        assert accept(*flags) is False
