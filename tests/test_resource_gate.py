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


# --- E4 dirty 범위 (2026-08-01 · 사용자 승인 · 사전등록 동결 전 변경) ---------

def test_dirty_scope_is_code_paths_only():
    """dirty 판정의 범위는 **코드 경로**다. `data/` 는 자원이지 코드가 아니다.

    O 팔은 정의상 `data/external/sdkb/` 를 구 스냅샷으로 되돌린 상태로 동결된다. 범위가
    트리 전체면 O 팔은 영구히 dirty 이고 E4 가 자원 델타 측정 자체를 불가능하게 만든다.
    """
    assert RS.CODE_PATHS == ("src", "tests", "Makefile", "pyproject.toml", "uv.lock")
    assert not any(p.startswith("data") for p in RS.CODE_PATHS)


def test_code_signature_passes_scope_to_git(monkeypatch):
    """`git status` 호출이 실제로 코드 경로로 한정되는가 — 주석이 아니라 인자를 검사한다."""
    seen: list[list[str]] = []

    class _R:
        stdout = ""

    def _fake_run(cmd, **kw):
        seen.append(list(cmd))
        return _R()

    monkeypatch.setattr(RS.subprocess, "run", _fake_run)
    sig = RS.code_signature()
    status_cmd = next(c for c in seen if "status" in c)
    assert status_cmd[-len(RS.CODE_PATHS):] == list(RS.CODE_PATHS)
    assert "--" in status_cmd
    assert sig["dirty"] is False
    assert sig["dirty_scope"] == list(RS.CODE_PATHS)


def test_code_dirty_still_disqualifies(monkeypatch):
    """범위를 좁혔다고 안전장치가 사라지지 않는다 — src/ 가 더러우면 여전히 미검정이다."""
    class _R:
        stdout = " M src/sdkb_paper/retrieval/hybrid.py"

    monkeypatch.setattr(RS.subprocess, "run", lambda cmd, **kw: _R())
    assert RS.code_signature()["dirty"] is True


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


# --- 자원 델타 가시성 (D-43 · PLAN-051) ---------------------------------
#
# 적격심사(E1–E7)와 **다른 질문**이다. 적격심사는 두 팔을 놓고 "비교할 자격이 있는가"를 묻고,
# 여기서는 팔이 하나뿐인 `system` 모드에서 "이 승인은 무엇을 본 승인인가"를 묻는다.
# `make gate` 의 기본 경로가 `system` 이므로, 이 절이 비면 D-43 은 다시 조용해진다.

# 실측 서명 (2026-08-15 · PLAN-051 §7). 축약형을 그대로 쓴다 — 값이 무엇이었는지가 증거다.
_SIG_PIPE_NOW = "9745a7d932c9"          # 현 트리 파이프라인 서명
_SIG_SNAP_NOW = "665c27d1c774"          # 현 트리 스냅샷 서명 (상류 0a7ff153)
_SIG_SNAP_BLAYER = "9b7f79ef06a6"       # B_layer_readout 이 동결한 스냅샷
_SIG_PIPE_LINKER = "156c0ccd36f5"       # O_pre_linker ↔ O_d578bf3_linkercode 공유 (D-19)
_SIG_SNAP_PRELINKER = "b98ad787d1fe"
_SIG_SNAP_LINKERCODE = "6cfb743d3d88"


def _write_manifests(tmp_path, monkeypatch, *manifests: dict) -> None:
    d = tmp_path / "runsets"
    d.mkdir(parents=True, exist_ok=True)
    for mf in manifests:
        (d / f"{mf['label']}.json").write_text(json.dumps(mf, ensure_ascii=False),
                                               encoding="utf-8")
    monkeypatch.setattr(config, "RUNSET_DIR", d)


def _pipe(sig: str, *, parts: dict | None = None) -> dict:
    return {"sig": sig, "short": sig[:12],
            "parts": parts if parts is not None else {"ir_corpus": "c", "concept_axis": "a",
                                                      "graph_v1": "g"}}


def _snap(sig: str) -> dict:
    return {"sig": sig, "short": sig[:12], "upstream_commit": "u1", "n_files": 22, "files": {}}


def test_visibility_flags_the_live_tree_state(tmp_path, monkeypatch):
    """V1 — 2026-08-15 실측 상태가 `invisible` 로 잡혀야 한다.

    스냅샷은 665c27d1 로 움직였는데 파이프라인 서명은 B_layer_readout 이 동결한 9745a7d9 그대로다.
    이 상태의 ΔR₁₀₀ 은 측정된 0 이 아니라 **구성상 0** 이다(D-43).
    """
    _write_manifests(tmp_path, monkeypatch,
                     _mf("B_layer_readout", snap_sig=_SIG_SNAP_BLAYER, pipe_sig=_SIG_PIPE_NOW))
    v = RS.resource_visibility(pipeline=_pipe(_SIG_PIPE_NOW), snapshot=_snap(_SIG_SNAP_NOW))
    assert v["note"] == RS.VIS_INVISIBLE
    assert v["basis"] == ["B_layer_readout"]
    assert v["error"] is None


def test_visibility_catches_the_historical_d19_pair(tmp_path, monkeypatch):
    """V2 — 과거에 실제로 일어난 상태를 이 검사가 잡는가.

    O_pre_linker(snap b98ad787)와 O_d578bf3_linkercode(snap 6cfb743d)는 파이프라인 서명
    156c0ccd 를 공유한다. 스냅샷이 두 번 움직이는 동안 파이프라인은 한 번도 움직이지 않았다.
    """
    _write_manifests(
        tmp_path, monkeypatch,
        _mf("O_pre_linker", snap_sig=_SIG_SNAP_PRELINKER, pipe_sig=_SIG_PIPE_LINKER),
        _mf("O_d578bf3_linkercode", snap_sig=_SIG_SNAP_LINKERCODE, pipe_sig=_SIG_PIPE_LINKER))
    v = RS.resource_visibility(pipeline=_pipe(_SIG_PIPE_LINKER),
                               snapshot=_snap(_SIG_SNAP_LINKERCODE))
    assert v["note"] == RS.VIS_INVISIBLE
    assert v["basis"] == ["O_pre_linker"]          # 스냅샷이 다른 쪽만 근거가 된다
    assert v["matched"] == ["O_d578bf3_linkercode", "O_pre_linker"]


def test_visibility_without_matching_manifest_is_unknown(tmp_path, monkeypatch):
    """V3a — 대조할 매니페스트가 없으면 `unknown` 이다. 근거 없음은 통과가 아니다."""
    _write_manifests(tmp_path, monkeypatch,
                     _mf("O_other", snap_sig="zzz", pipe_sig="다른파이프라인"))
    v = RS.resource_visibility(pipeline=_pipe(_SIG_PIPE_NOW), snapshot=_snap(_SIG_SNAP_NOW))
    assert v["note"] == RS.VIS_UNKNOWN
    assert v["matched"] == [] and v["basis"] == []


def test_visibility_without_runset_dir_is_unknown(tmp_path, monkeypatch):
    """V3b — 매니페스트 디렉터리 자체가 없어도 죽지 않고 `unknown` 을 낸다."""
    monkeypatch.setattr(config, "RUNSET_DIR", tmp_path / "없음")
    v = RS.resource_visibility(pipeline=_pipe(_SIG_PIPE_NOW), snapshot=_snap(_SIG_SNAP_NOW))
    assert v["note"] == RS.VIS_UNKNOWN


def test_no_evidence_does_not_bleed_into_invisible(tmp_path, monkeypatch):
    """V4 — 파이프라인·스냅샷이 함께 일치하면 `no_evidence` 다.

    **`visible` 이라고 쓰지 않는다** — 확인된 것은 "비가시라는 증거가 없다"이지 "델타가
    보였다"가 아니다(PLAN-051 §8 A).
    """
    _write_manifests(tmp_path, monkeypatch,
                     _mf("O_same", snap_sig=_SIG_SNAP_NOW, pipe_sig=_SIG_PIPE_NOW))
    v = RS.resource_visibility(pipeline=_pipe(_SIG_PIPE_NOW), snapshot=_snap(_SIG_SNAP_NOW))
    assert v["note"] == RS.VIS_NO_EVIDENCE
    assert v["basis"] == [] and v["matched"] == ["O_same"]


def test_invisible_wins_over_no_evidence(tmp_path, monkeypatch):
    """V4b — 같은 스냅샷 매니페스트가 함께 있어도 비가시의 증거는 흡수되지 않는다.

    `classify_delta` 가 A-Box 오염을 우선하는 것과 같은 원칙이다.
    """
    _write_manifests(tmp_path, monkeypatch,
                     _mf("O_same", snap_sig=_SIG_SNAP_NOW, pipe_sig=_SIG_PIPE_NOW),
                     _mf("O_older", snap_sig=_SIG_SNAP_BLAYER, pipe_sig=_SIG_PIPE_NOW))
    v = RS.resource_visibility(pipeline=_pipe(_SIG_PIPE_NOW), snapshot=_snap(_SIG_SNAP_NOW))
    assert v["note"] == RS.VIS_INVISIBLE
    assert v["basis"] == ["O_older"]


def test_missing_pipeline_part_is_unknown_not_a_guess(tmp_path, monkeypatch):
    """V5 — 구성요소가 없으면 서명은 계산되지만 비교할 의미가 없다. 모르는 것을 안다고 적지 않는다."""
    _write_manifests(tmp_path, monkeypatch,
                     _mf("B_layer_readout", snap_sig=_SIG_SNAP_BLAYER, pipe_sig=_SIG_PIPE_NOW))
    v = RS.resource_visibility(
        pipeline=_pipe(_SIG_PIPE_NOW, parts={"ir_corpus": "c", "concept_axis": None,
                                             "graph_v1": "g"}),
        snapshot=_snap(_SIG_SNAP_NOW))
    assert v["note"] == RS.VIS_UNKNOWN
    assert "concept_axis" in v["detail"]


def test_missing_provenance_is_reported_not_raised_and_not_silent(tmp_path, monkeypatch):
    """V6 — PROVENANCE 부재는 게이트를 죽이지 않는다. **그러나 조용하지도 않다.**

    D-42 의 교훈은 "검사기가 눈을 감는 방식은 늘 예외를 삼키는 것이었다"이고, 그것을 지키는
    방식은 예외를 올리는 것이 아니라 사유를 남기는 것이다.
    """
    monkeypatch.setattr(config, "RUNSET_DIR", tmp_path / "runsets")
    monkeypatch.setattr(RS, "snapshot_signature",
                        lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError("PROVENANCE 없음")))
    v = RS.resource_visibility(pipeline=_pipe(_SIG_PIPE_NOW))
    assert v["note"] == RS.VIS_UNKNOWN
    assert v["error"] and "PROVENANCE" in v["error"]


def test_visibility_is_deterministic(tmp_path, monkeypatch):
    """V8 — 같은 입력에 두 번 부르면 바이트 단위로 같다(시각·난수 없음)."""
    _write_manifests(tmp_path, monkeypatch,
                     _mf("B_layer_readout", snap_sig=_SIG_SNAP_BLAYER, pipe_sig=_SIG_PIPE_NOW))
    a = RS.resource_visibility(pipeline=_pipe(_SIG_PIPE_NOW), snapshot=_snap(_SIG_SNAP_NOW))
    b = RS.resource_visibility(pipeline=_pipe(_SIG_PIPE_NOW), snapshot=_snap(_SIG_SNAP_NOW))
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_visibility_is_recorded_without_touching_the_verdict(monkeypatch):
    """V7 — `system` 모드에서 기록은 남되 **승인식은 그대로다**(PLAN-051 S4 의 단위 형태)."""
    from sdkb_paper.validate import t_gate as TG
    from sdkb_paper.validate import t1_noninferiority as T1
    from sdkb_paper.validate import t2_subgroup as T2
    from sdkb_paper.validate import t3_cross_task_cq as T3

    sentinel = {"note": RS.VIS_INVISIBLE, "pipeline_short": "p", "snapshot_short": "s",
                "matched": ["M"], "basis": ["M"], "detail": "d", "error": None}
    monkeypatch.setattr(RS, "resource_visibility", lambda *a, **k: sentinel)
    monkeypatch.setattr(T1, "t1_gate", lambda *a, **k: {"pass": True})
    monkeypatch.setattr(T2, "t2_gate", lambda *a, **k: {"pass": True})
    monkeypatch.setattr(T3, "t3_gate", lambda *a, **k: {"pass": True, "waived": False})
    # 판정 dict 를 얇게 두는 대신 **출력기를 막는다** — 이 테스트가 묻는 것은 서식이 아니라
    # "가시성 기록이 승인식에 새어 들어가는가"이다.
    for mod in (T1, T2, T3):
        monkeypatch.setattr(mod, "format_report", lambda r: "(stub)")
    monkeypatch.setattr(T3, "run_cqs", lambda *a, **k: {})
    monkeypatch.setattr(T3, "suite_pass_rates", lambda *a, **k: {})
    monkeypatch.setattr(T3, "load_generation", lambda *a, **k: {"suites": {}, "generation": "g0"})
    monkeypatch.setattr(T3, "commit_waiver", lambda *a, **k: None)
    monkeypatch.setattr("sdkb_paper.analysis.metrics.load_run", lambda p: {})
    monkeypatch.setattr("sdkb_paper.analysis.results_table._split_qrel", lambda s: {})
    monkeypatch.setattr("sdkb_paper.analysis.results_table.run_path",
                        lambda n, s: __import__("pathlib").Path(f"sys_{n}_{s}.txt"))
    monkeypatch.setattr("sdkb_paper.analysis.subgroup.query_labels", lambda q: {})
    monkeypatch.setattr("sdkb_paper.collect.bq_family_ir.load_family_map", lambda: {})

    res = TG.run_tgate(split="dev", skip_leakage=True)
    # 비가시여도 승인은 T1·T2·T3·L0–L3 의 곱 그대로다 — 기록은 판정에 관여하지 않는다.
    assert res["accept"] is True
    assert res["resource_visibility"]["note"] == RS.VIS_INVISIBLE
    assert "이 게이트로는 보이지 않는 델타다" in TG.format_report(res)
