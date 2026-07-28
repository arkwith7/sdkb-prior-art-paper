"""T-gate 단위·통합 테스트 (PLAN-019 W3 · 원고 §4.9).

외부 산출물(run·코퍼스·qrel parquet) 없이 **판정 로직**만 때린다 — 경계값·게이트 우회 차단·
waiver 회계·CQ 스위트 계약. 게이트는 초록불이 쉬우면 안 되므로 경계는 전부 "불통과" 쪽으로
검증한다.
"""
from __future__ import annotations

import json

import pytest

from sdkb_paper import config
from sdkb_paper.validate import t3_cross_task_cq as T3
from sdkb_paper.validate.cq_runner import CQResult, suite_pass_rates
from sdkb_paper.validate.t1_noninferiority import t1_decide
from sdkb_paper.validate.t2_subgroup import t2_decide, t2_gate
from sdkb_paper.validate.t_gate import accept


# --- T1 -----------------------------------------------------------------

def test_t1_boundary_is_strict():
    """LB95 가 정확히 −ε 이면 **불통과**(원고 §4.9 수식의 엄격 부등호)."""
    eps = config.T_EPSILON
    assert t1_decide(-eps + 1e-9, eps) is True
    assert t1_decide(-eps, eps) is False
    assert t1_decide(-eps - 1e-9, eps) is False


def test_t1_passes_when_improved():
    assert t1_decide(+0.03, config.T_EPSILON) is True


def test_t1_gate_uses_frozen_epsilon_by_default():
    """기본 ε 는 사전등록 동결값 0.02 여야 한다(사후 조정 방지)."""
    assert config.T_EPSILON == 0.02
    assert config.T_DELTA == 0.05
    assert config.T2_MIN_N == 20


# --- T2 -----------------------------------------------------------------

def test_t2_boundary_is_strict():
    d = config.T_DELTA
    assert t2_decide(d - 1e-9, d) is True
    assert t2_decide(d, d) is False
    assert t2_decide(d + 0.01, d) is False


def test_t2_ignores_small_subgroups_but_flags_undetermined():
    """n<20 집단은 차단에 쓰지 않는다. 신뢰집단이 하나도 없으면 통과이되 '미결' 표시."""
    run_new = {f"q{i}": ["a"] for i in range(5)}
    run_old = {f"q{i}": ["b"] for i in range(5)}
    qrel = {f"q{i}": {"b"} for i in range(5)}          # 구 시스템만 정답 회수 = 큰 하락
    labels = {f"q{i}": {"pos_lang": "kr_only"} for i in range(5)}
    r = t2_gate(run_new, run_old, qrel, family=None, labels=labels, dims=("pos_lang",))
    assert r["undetermined"] is True
    assert r["pass"] is True          # 차단하지 못하지만
    assert r["max_drop"] is None      # 조용히 초록불이 되지 않도록 미결이 남는다


def test_t2_blocks_local_regression_in_reliable_subgroup():
    """신뢰집단(n≥20)에서 δ 이상 하락하면 전체가 좋아도 차단한다."""
    n = 25
    run_new = {f"q{i}": ["x"] for i in range(n)}
    run_old = {f"q{i}": ["b"] for i in range(n)}
    qrel = {f"q{i}": {"b"} for i in range(n)}
    labels = {f"q{i}": {"pos_lang": "has_foreign"} for i in range(n)}
    r = t2_gate(run_new, run_old, qrel, family=None, labels=labels, dims=("pos_lang",))
    assert r["pass"] is False
    assert r["max_drop"] == pytest.approx(1.0)
    assert r["worst"]["group"] == "has_foreign"


# --- T3 -----------------------------------------------------------------

def _rates(**kw):
    return {k: {"n_pass": int(v * 10), "n_total": 10, "rate": v} for k, v in kw.items()}


def test_t3_is_deterministic_not_statistical():
    """아주 작은 하락도 실패다 — CQ 는 명세이므로 표본오차 완충재가 없다."""
    old = _rates(em=1.0, tf=1.0, core=1.0)
    new = _rates(em=0.9, tf=1.0, core=1.0)
    r = T3.t3_gate(new, old)
    assert r["pass"] is False and r["regressed"] == ["em"]


def test_t3_ignores_primary_task_suite():
    """pa(선행기술검색)는 T3 분모가 아니다 — 그 회귀는 T1 이 본다."""
    old = _rates(pa=1.0, em=1.0, tf=1.0, core=1.0)
    new = _rates(pa=0.0, em=1.0, tf=1.0, core=1.0)
    assert T3.t3_gate(new, old)["pass"] is True


def test_t3_deleted_cq_suite_counts_as_regression():
    """CQ 를 지워 스위트를 없애는 우회로를 막는다(없으면 통과율 0)."""
    old = _rates(em=1.0, tf=1.0, core=1.0)
    new = _rates(tf=1.0, core=1.0)
    assert T3.t3_gate(new, old)["pass"] is False


def test_t3_improvement_passes():
    old = _rates(em=0.8, tf=1.0, core=1.0)
    new = _rates(em=0.9, tf=1.0, core=1.0)
    r = T3.t3_gate(new, old)
    assert r["pass"] is True and r["waived"] is False


def test_t3_waiver_requires_regression_and_is_logged(tmp_path, monkeypatch):
    """waiver 는 하락이 있을 때만 켜지고, 켜지면 반드시 원장에 남는다(횟수 보고 의무)."""
    old = _rates(em=1.0, tf=1.0, core=1.0)
    new = _rates(em=0.5, tf=1.0, core=1.0)
    r = T3.t3_gate(new, old, waiver="상류 CQ 재설계 진행 중")
    assert r["pass"] is True and r["waived"] is True

    monkeypatch.setattr(config, "CQ_GEN_DIR", tmp_path)
    monkeypatch.setattr(config, "T3_WAIVER_LOG", tmp_path / "waiver_log.jsonl")
    assert T3.waiver_count() == 0
    T3.log_waiver({"reason": r["waiver_reason"], "regressed": r["regressed"]})
    assert T3.waiver_count() == 1
    rec = json.loads((tmp_path / "waiver_log.jsonl").read_text(encoding="utf-8").strip())
    assert rec["regressed"] == ["em"]


def _write_gen(d, label, *, against=None, verdict=None, pa=1.0, em=1.0):
    rec = {"generation": label, "against": against,
           "suites": {"pa": {"n_pass": 5, "n_total": 5, "rate": pa},
                      "em": {"n_pass": 6, "n_total": 6, "rate": em},
                      "tf": {"n_pass": 5, "n_total": 5, "rate": 1.0},
                      "core": {"n_pass": 12, "n_total": 12, "rate": 1.0}}}
    if verdict is not None:
        rec["verdict"] = verdict
        rec["rule_version"], rec["tau"] = "v2", 0.05
    (d / f"cq_{label}.json").write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")


def test_table_refuses_placeholder_verdict(tmp_path, monkeypatch):
    """표 6.6 의 T3 열은 아티팩트에서만 온다 — 판정 없는 세대는 에러다 (N5e).

    자리표시자(`[기입]`)를 찍으면 사람이 채우게 되고, 원고의 `graph_v1` 행이 정확히 그렇게
    수기 기입됐다(CLAUDE.md §1-7 위반). 자리표시자를 되살리면 이 테스트가 막는다.
    """
    monkeypatch.setattr(config, "CQ_GEN_DIR", tmp_path)
    monkeypatch.setattr(config, "T3_WAIVER_LOG", tmp_path / "waiver_log.jsonl")
    monkeypatch.setattr(config, "DEDUP_EXEMPTION_LOG", tmp_path / "dedup.jsonl")
    _write_gen(tmp_path, "g0")
    table = T3.render_generations()
    assert "[기입]" not in table and "— (기준 세대)" in table

    _write_gen(tmp_path, "gN", against="g0")          # 판정 없는 비-기준 세대
    with pytest.raises(ValueError, match="T3 판정이 없다"):
        T3.render_generations()

    _write_gen(tmp_path, "gN", against="g0",
               verdict={"baseline": "g0", "pass": True, "regressed": [], "waived": False,
                        "waiver_reason": None, "rows": []})
    assert "**승인** (하락 0) vs g0" in T3.render_generations()


def test_table_reports_rejection_and_waiver(tmp_path, monkeypatch):
    """거부·waiver 도 표에 그대로 나온다 — 조용한 면제는 게이트를 장식으로 만든다."""
    monkeypatch.setattr(config, "CQ_GEN_DIR", tmp_path)
    monkeypatch.setattr(config, "T3_WAIVER_LOG", tmp_path / "waiver_log.jsonl")
    monkeypatch.setattr(config, "DEDUP_EXEMPTION_LOG", tmp_path / "dedup.jsonl")
    _write_gen(tmp_path, "g0")
    _write_gen(tmp_path, "gN", against="g0", em=0.5,
               verdict={"baseline": "g0", "pass": False, "regressed": ["em"], "waived": False,
                        "waiver_reason": None, "rows": []})
    assert "**거부** (em 하락)" in T3.render_generations()
    _write_gen(tmp_path, "gN", against="g0", em=0.5,
               verdict={"baseline": "g0", "pass": True, "regressed": ["em"], "waived": True,
                        "waiver_reason": "상류 재설계", "rows": []})
    t = T3.render_generations()
    assert "waiver" in t and "| 1 |" in t


def test_t3_waiver_token_parsed_from_commit_message():
    assert T3.commit_waiver("feat: x\n\nT3-WAIVER: em 스위트 재설계 중") == "em 스위트 재설계 중"
    assert T3.commit_waiver("feat: x") is None


# --- 승인식·스위트 계약 ---------------------------------------------------

def test_accept_is_a_product_no_bypass():
    assert accept(True, True, True, True) is True
    for i in range(4):
        flags = [True] * 4
        flags[i] = False
        assert accept(*flags) is False, f"조건 {i} 실패인데 승인됐다 — 게이트 우회"


def test_suite_pass_rates_partitions_results():
    rs = [CQResult("a", "", 1, 1, "em"), CQResult("b", "", 1, 0, "em"),
          CQResult("c", "", 1, 5, "core")]
    out = suite_pass_rates(rs)
    assert out["em"] == {"n_pass": 1, "n_total": 2, "rate": 0.5}
    assert out["core"]["rate"] == 1.0
