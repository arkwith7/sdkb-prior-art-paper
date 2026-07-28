"""CQ 판정 v2(존재검사 ∧ 분포검사)의 계약 — W4b · PLAN-021 동결 규칙.

여기서 지키는 명제는 넷이다.
1. **극성이 강제된다** — `# monotone:` 없는 CQ 는 에러다. 조용한 기본값은 공백 탐색 질의
   (CQ03·CQ06)의 정당한 개선을 회귀로 오판시킨다.
2. **v1 하위호환** — 기준선을 주지 않으면 판정은 존재검사 그대로다(기존 세대·게이트가 안 깨진다).
3. **τ 는 인자로 느슨해지지 않는다** — 동결 주값이 config 에 있고 격자는 사전 동결이다.
4. **N03 은 결함이 아니다** — 완전중복 병합은 정보를 잃지 않는 정당 델타이며, 서명이
   나가는 간선만 보면 별개 개체를 병합해 위양성 분모를 조작하게 된다.
"""
from __future__ import annotations

import random

import pytest
from pyoxigraph import Literal, NamedNode, Quad, Store

from sdkb_paper import config
from sdkb_paper.validate import fault_inject as FI
from sdkb_paper.validate.cq_runner import (
    CQResult,
    _parse_meta,
    regressions,
    run_cqs,
    suite_pass_rates,
)

RDFT = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"


def _r(name="CQ", rows=100, suite="em", mono="up", expect_min=1) -> CQResult:
    return CQResult(name, "", expect_min, rows, suite, mono)


# --- 1. 극성 라벨 강제 ---------------------------------------------------------
def test_missing_monotone_label_is_an_error():
    with pytest.raises(ValueError, match="극성"):
        _parse_meta("# suite: em\n# expect-min: 1\nSELECT * WHERE {}")


def test_bad_monotone_value_is_an_error():
    with pytest.raises(ValueError, match="극성"):
        _parse_meta("# suite: em\n# monotone: sideways\nSELECT * WHERE {}")


def test_every_shipped_cq_declares_polarity():
    """28개 전량이 동결 대상이다 — 하나라도 빠지면 T3 의 분모가 조용히 달라진다."""
    res = run_cqs(config.SAMPLES / "mini_graph.ttl")
    assert res
    assert all(r.monotone in config.CQ_MONOTONE for r in res)


# --- 2. 판정 산술 -------------------------------------------------------------
def test_v1_is_unchanged_when_no_baseline_given():
    res = [_r(rows=1), _r(name="CQb", rows=0)]
    assert suite_pass_rates(res)["em"] == {"n_pass": 1, "n_total": 2, "rate": 0.5}


def test_up_polarity_flags_drop_beyond_tau():
    r = _r(rows=94)
    assert r.regressed(100, 0.05) and not r.regressed(100, 0.10)
    assert not _r(rows=95).regressed(100, 0.05)      # 경계는 회귀가 아니다(엄격 부등호)


def test_down_polarity_flags_growth_not_drop():
    """공백 탐색 질의 — 행이 줄면 개선이고 늘면 회귀다. 부호를 뒤집으면 정반대가 된다."""
    gap = _r(rows=5, mono="down", expect_min=0)
    assert not gap.regressed(29, 0.05)               # 29 → 5 은 커버리지 개선
    assert _r(rows=40, mono="down", expect_min=0).regressed(29, 0.05)


def test_flat_polarity_is_two_sided():
    assert _r(rows=120, mono="flat").regressed(100, 0.05)
    assert _r(rows=80, mono="flat").regressed(100, 0.05)


def test_zero_baseline_disables_distribution_check():
    """base=0 이면 비율이 정의되지 않는다 — 존재검사만 남는다(CQ27 이 여기 해당)."""
    assert not _r(rows=0).regressed(0, 0.0)
    assert not _r(rows=0, expect_min=1).judge(0)     # 존재검사로는 여전히 불통과


def test_regression_requires_both_existence_and_distribution():
    assert _r(rows=94).judge(100, 0.05) is False     # 존재 통과 · 분포 회귀
    assert _r(rows=0).judge(100, 0.05) is False      # 둘 다 실패
    assert _r(rows=99).judge(100, 0.05) is True


def test_suite_rates_use_v2_when_baseline_given():
    res = [_r(name="A", rows=94), _r(name="B", rows=100)]
    base = {"A": 100, "B": 100}
    assert suite_pass_rates(res, base, 0.05)["em"]["n_pass"] == 1
    assert suite_pass_rates(res, base, 0.10)["em"]["n_pass"] == 2
    assert [x["cq"] for x in regressions(res, base, 0.05)] == ["A"]


def test_frozen_tau_grid_contains_main_value():
    """주값이 격자 밖이면 민감도 보고가 주 판정을 포함하지 못한다."""
    assert config.CQ_TAU in config.CQ_TAU_GRID


# --- 3. N03 정상 델타의 계약 ---------------------------------------------------
def _pair(store: Store, a: str, b: str, *, same_in: bool, label: str) -> None:
    """나가는 트리플이 같은 두 개체. same_in 이면 들어오는 간선도 같다.

    쌍마다 라벨을 달리한다 — 같은 라벨을 쓰면 네 개체가 한 군으로 합쳐져 검사가 무의미해진다.
    """
    for u in (a, b):
        store.add(Quad(NamedNode(u), NamedNode(RDFT), NamedNode(FI.ONT + "Problem")))
        store.add(Quad(NamedNode(u), NamedNode(FI.SKOS + "prefLabel"), Literal(label)))
    store.add(Quad(NamedNode("urn:c1"), NamedNode(FI.ONT + "exhibits"), NamedNode(a)))
    src = "urn:c1" if same_in else "urn:c2"
    store.add(Quad(NamedNode(src), NamedNode(FI.ONT + "exhibits"), NamedNode(b)))


def test_n03_merges_only_indistinguishable_entities():
    s = Store()
    _pair(s, "urn:same_a", "urn:same_b", same_in=True, label="구별불가")
    _pair(s, "urn:diff_a", "urn:diff_b", same_in=False, label="인용주체 다름")
    stats = FI.n03_exact_duplicate_merge(s, 1.0, random.Random(0))
    assert stats["n_candidates"] == 1, "인용 주체가 다른 쌍까지 병합하면 별개 개체를 잃는다"
    assert stats["n_entities_merged"] == 1
    remaining = {q.subject.value for q in s.quads_for_pattern(None, NamedNode(RDFT), None)}
    assert remaining == {"urn:same_a", "urn:diff_a", "urn:diff_b"}


def test_n03_is_registered_as_a_normal_delta_not_a_fault():
    """분모를 틀리면 위양성률이 조작된다 — N03 은 결함 목록에 들어가면 안 된다."""
    assert "N03" in {f.key for f in FI.NORMALS}
    assert "N03" not in {f.key for f in FI.FAULTS}
    assert FI.BY_KEY["N03"].cross_task is False
