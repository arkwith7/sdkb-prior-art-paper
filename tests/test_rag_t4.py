"""T4 판정 산출의 회귀 테스트 (PLAN-047 §18.2 설계 · 판정 전에 쓴다).

이 파일이 지키는 것 넷 — ① 마진은 코드 상수이고 인자로 바뀌지 않는다 ② 부트스트랩은 결정적이다
③ 비율은 `aggregate()` 와 같은 정의로 재계산된다 ④ 판정식은 두 조건의 논리곱이다.
"""
from __future__ import annotations

import pytest

pytest.importorskip("numpy")

from sdkb_paper.rag import t4  # noqa: E402


def _q(n_cited, n_correct, n_out=0, n_pos=1, n_quotes=0, n_grounded=0):
    return {"n_cited": n_cited, "n_cited_correct": n_correct,
            "n_cited_out_of_context": n_out, "n_pos_in_context": n_pos,
            "n_quotes": n_quotes, "n_quotes_grounded": n_grounded}


def _arm(spec):
    return {f"q{i}": _q(*s) for i, s in enumerate(spec)}


def test_margins_are_module_constants_frozen_by_plan047():
    """§4.2 동결값. 바뀌면 그것은 재측정이 아니라 사전등록 위반이다(§1-3)."""
    assert (t4.EPS_T4, t4.ETA, t4.N_BOOT) == (0.02, 0.01, 10000)
    # 판정 함수는 마진을 인자로 받지 않는다 — 호출자가 바꿀 수 있으면 동결이 아니다.
    import inspect
    assert list(inspect.signature(t4.verdict).parameters) == ["stats"]


def test_bootstrap_is_deterministic():
    """같은 입력·같은 seed → 같은 CI(§18.2-8)."""
    a, b = _arm([(2, 1)] * 30), _arm([(2, 0)] * 30)
    r1 = t4.bootstrap_ratio_delta(a, b, "n_cited_correct", "n_cited", n_boot=200)
    r2 = t4.bootstrap_ratio_delta(a, b, "n_cited_correct", "n_cited", n_boot=200)
    assert r1 == r2


def test_ratio_is_sum_over_sum_not_mean_of_ratios():
    """§18.2-3 — 인용을 많이 한 질의가 분모에서 더 무겁다. 질의당 비율의 평균이 아니다."""
    # q0: 10건 중 0건 정답 · q1: 1건 중 1건 정답 → 비율의 비율 = 1/11, 질의평균이면 0.5
    arm = _arm([(10, 0), (1, 1)])
    assert t4._ratio(list(arm.values()), "n_cited_correct", "n_cited", False) == pytest.approx(1 / 11)


def test_identical_arms_give_zero_delta_and_ci_containing_zero():
    same = _arm([(2, 1), (3, 2), (1, 0)] * 10)
    r = t4.bootstrap_ratio_delta(same, dict(same), "n_cited_correct", "n_cited", n_boot=300)
    assert r["delta"] == pytest.approx(0.0)
    assert r["lb95"] == pytest.approx(0.0) and r["ub95"] == pytest.approx(0.0)


def test_conditional_uses_each_arm_own_denominator():
    """§11.4-① — 조건부는 팔마다 `n_pos_in_context>0` 인 질의만 센다. 분모가 달라도 정의다."""
    rows = [_q(2, 2, n_pos=1), _q(2, 0, n_pos=0)]
    assert t4._ratio(rows, "n_cited_correct", "n_cited", True) == pytest.approx(1.0)
    assert t4._ratio(rows, "n_cited_correct", "n_cited", False) == pytest.approx(0.5)


def test_zero_denominator_resamples_are_dropped_and_counted():
    """§18.2-4 — 버리되 센다. 조용히 0 으로 적지 않는다."""
    arm = _arm([(0, 0), (0, 0)])       # 아무도 인용하지 않았다 → 모든 리샘플의 분모가 0
    r = t4.bootstrap_ratio_delta(arm, dict(arm), "n_cited_correct", "n_cited", n_boot=50)
    assert r["n_dropped"] == 50 and r["lb95"] is None and r["delta"] is None


def test_verdict_is_conjunction_of_the_two_frozen_conditions():
    def st(lb_prec, ub_hall):
        return {"citation_precision": {"lb95": lb_prec, "ub95": 1.0},
                "hallucination_rate": {"lb95": -1.0, "ub95": ub_hall}}
    assert t4.verdict(st(-0.01, 0.005))["T4"] is True         # 둘 다 만족
    assert t4.verdict(st(-0.03, 0.005))["T4"] is False        # 정확도 하락이 마진 초과
    assert t4.verdict(st(-0.01, 0.02))["T4"] is False         # 환각률 상승이 η 초과
    # 경계는 등호를 포함하지 않는다 — 판정식이 `>` 와 `<` 이다(§4.2).
    assert t4.verdict(st(-t4.EPS_T4, 0.0))["T4"] is False
    assert t4.verdict(st(0.0, t4.ETA))["T4"] is False


def test_a_layer_is_refused():
    """§18.3 — A층은 탐색적이고 마진 동결 이전이다. T4 를 소급 적용하지 않는다."""
    import subprocess
    import sys
    r = subprocess.run([sys.executable, "-m", "sdkb_paper.rag.t4", "--split", "test"],
                       capture_output=True, text=True)
    assert r.returncode == 2 and "차단" in r.stdout
