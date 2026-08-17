"""PLAN-055 전복 문턱·조성 대조의 단위 검증 — 손으로 셀 수 있는 크기에서만 검사한다."""
from __future__ import annotations

import numpy as np
import pytest

from sdkb_paper.analysis import judgment_robustness as jr


def test_delta_monotone_decreasing():
    """적대적 추가는 짝지은 차이를 단조 감소시킨다 — 정의의 전제(PLAN-055 §2.3)."""
    rw, rl, R = np.array([3.0]), np.array([1.0]), np.array([4.0])
    prev = np.inf
    for a in range(0, 5):
        d = jr._delta(rw, rl, R, np.array([float(a)]))[0]
        assert d < prev
        prev = d


def test_delta_hand_computed():
    """R=4·우위 3·열위 1 에 2건 추가 → (3−1−2)/(4+2) = 0."""
    d = jr._delta(np.array([3.0]), np.array([1.0]), np.array([4.0]), np.array([2.0]))
    assert d[0] == pytest.approx(0.0)


def test_greedy_respects_per_query_cap():
    """질의당 상한 U 를 넘겨 배치하지 않는다 — 없는 후보를 적대자가 쓸 수 없다."""
    rw = np.array([2.0, 2.0])
    rl = np.array([0.0, 0.0])
    R = np.array([2.0, 2.0])
    U = np.array([1.0, 3.0])
    add = jr._greedy_add(rw, rl, R, U, 10)
    assert add[0] <= 1 and add[1] <= 3
    assert add.sum() == 4                      # 상한 합을 넘지 않는다


def test_reversal_threshold_reaches_zero_and_reports_ratio():
    """정답 1건 질의에서는 1건 추가로 그 질의의 차이가 0 이 된다."""
    rw = np.array([1.0, 1.0])
    rl = np.array([0.0, 0.0])
    R = np.array([1.0, 1.0])
    U = np.array([1.0, 1.0])
    r = jr.reversal_threshold(rw, rl, R, U, n_boot=200)
    assert r["delta_point"] == pytest.approx(1.0)
    assert r["n_star_point"] == 2               # 두 질의 모두 뒤집어야 평균이 0
    assert r["n_star_point_ratio"] == pytest.approx(1.0)
    assert r["n_star_point_queries"] == 2


def test_reversal_threshold_unreachable_returns_none():
    """상한까지 채워도 0 에 못 닿으면 None — 억지로 수를 만들지 않는다."""
    rw = np.array([5.0])
    rl = np.array([0.0])
    R = np.array([10.0])
    U = np.array([1.0])
    r = jr.reversal_threshold(rw, rl, R, U, n_boot=100)
    assert r["n_star_point"] is None
    assert r["n_star_point_ratio"] is None


def test_cpc_main_takes_section_and_class():
    assert jr._cpc_main("H01L21/02;H01L29/06") == "H01"
    assert jr._cpc_main(None) == jr.YEAR_UNKNOWN
    assert jr._cpc_main([]) == jr.YEAR_UNKNOWN


def test_composition_empty_input():
    import pandas as pd

    meta = pd.DataFrame(columns=["lang", "pub_year", "cpc_main", "n_concepts"])
    assert jr.composition([], meta) == {"n": 0}
