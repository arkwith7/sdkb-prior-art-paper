"""L3–T3 검출 표면 분리 + 중복제거 면제의 불변량 (PLAN-022 · N5c).

여기 있는 테스트는 편의 검사가 아니라 **사전등록 규칙의 강제**다. 특히 `test_no_delta_newly_accepted`
는 층 재정의가 게이트를 완화하지 않았다는 §0.1 논증을 코드로 붙잡아 둔다 — 이 성질이 깨지면
"귀속만 바꿨다"는 논문의 주장이 거짓이 된다.
"""
from __future__ import annotations

import random

import pytest
from pyoxigraph import NamedNode, Quad, Store

from sdkb_paper import config
from sdkb_paper.validate import fault_inject as FI
from sdkb_paper.validate.cq_runner import CQResult, layer_pass_counts, suite_pass_rates
from sdkb_paper.validate.dedup_exempt import entity_signature, verify_groups

ONT = str(config.ONT)
RDF_TYPE = NamedNode("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")


# --- 층 정의 불변량 -----------------------------------------------------------

def test_l3_t3_are_disjoint_and_exhaustive():
    """서로소 ∧ 합집합 = 전량. 둘 중 하나라도 깨지면 H1″ 판정식이 무의미해진다."""
    assert set(config.L3_SUITES) & set(config.T3_SUITES) == set()
    assert set(config.L3_SUITES) | set(config.T3_SUITES) == set(config.CQ_SUITES)


def _mk(name, suite, rows, expect_min=1, mono="up"):
    return CQResult(name, "", expect_min, rows, suite, mono)


def test_layer_pass_counts_splits_by_suite():
    res = [_mk("CQa", "pa", 5), _mk("CQb", "em", 3), _mk("CQc", "tf", 0), _mk("CQd", "core", 2)]
    layers = layer_pass_counts(res)
    assert layers["L3"]["n_total"] == 1 and layers["L3"]["n_pass"] == 1
    assert layers["T3"]["n_total"] == 3 and layers["T3"]["n_pass"] == 2   # tf 0행 = 존재검사 실패


@pytest.mark.parametrize("tau", config.CQ_TAU_GRID)
def test_no_delta_newly_accepted(tau):
    """**검출력 불변** (PLAN-022 §0.1) — `L3_all ⟺ L3_pa ∨ T3`.

    구 귀속에서 거부되던 델타가 신 귀속에서 승인되는 일이 없어야 한다. 무작위 CQ 결과 200벌로
    확인한다(경계값이 아니라 성질을 본다).
    """
    rng = random.Random(20260728)
    suites = list(config.CQ_SUITES)
    for _ in range(200):
        base = {}
        res = []
        for i in range(12):
            suite = rng.choice(suites)
            b = rng.randint(1, 20)
            rows = max(0, b + rng.randint(-6, 6))
            name = f"CQ{i:02d}"
            base[name] = b
            res.append(_mk(name, suite, rows, expect_min=rng.choice([0, 1])))
        per = suite_pass_rates(res, base, tau)              # v2 판정
        base_per = suite_pass_rates(res, None, tau)         # 기준선(존재검사만 = 회귀 없음)
        layers = layer_pass_counts(res, base, tau)
        base_layers = layer_pass_counts(res, None, tau)

        l3_all = sum(r.judge(base.get(r.name), tau) for r in res) < sum(r.passed for r in res)
        l3_pa = layers["L3"]["n_pass"] < base_layers["L3"]["n_pass"]
        t3 = any(per.get(s, {}).get("n_pass", 0) < base_per.get(s, {}).get("n_pass", 0)
                 for s in config.T3_SUITES)
        assert l3_all == (l3_pa or t3)


# --- 중복제거 면제 -------------------------------------------------------------

def _store_with(pairs_identical: bool) -> tuple[Store, list[list[str]]]:
    """A·B 두 개체를 만든다. `pairs_identical` 이면 서명이 완전히 같다."""
    s = Store()
    a, b = NamedNode(ONT + "A"), NamedNode(ONT + "B")
    cls, ref = NamedNode(ONT + "Skill"), NamedNode(ONT + "R")
    for n in (a, b):
        s.add(Quad(n, RDF_TYPE, cls))
        s.add(Quad(n, NamedNode(ONT + "p"), NamedNode(ONT + "v1")))
        s.add(Quad(ref, NamedNode(ONT + "uses"), n))
    if not pairs_identical:
        s.add(Quad(b, NamedNode(ONT + "p"), NamedNode(ONT + "v2")))
    return s, [[str(a), str(b)]]


def test_exemption_granted_only_for_exact_duplicates():
    s, groups = _store_with(True)
    assert verify_groups(s, groups)["ok"] is True
    s2, groups2 = _store_with(False)
    v = verify_groups(s2, groups2)
    assert v["ok"] is False and v["n_mismatch"] == 1


def test_incoming_edges_are_part_of_the_signature():
    """나가는 간선만 보면 별개 개체가 중복으로 잡힌다 — 실측에서 CitedPatent 12군 중 10군."""
    s, groups = _store_with(True)
    s.add(Quad(NamedNode(ONT + "other"), NamedNode(ONT + "cites"), NamedNode(ONT + "B")))
    out_a, in_a = entity_signature(s, ONT + "A")
    out_b, in_b = entity_signature(s, ONT + "B")
    assert out_a == out_b and in_a != in_b
    assert verify_groups(s, groups)["ok"] is False


def test_exemption_does_not_waive_existence_check():
    """면제는 분포검사만 푼다. 존재검사까지 풀면 CQ 를 0행으로 만드는 결함이 통과한다."""
    r = _mk("CQx", "pa", rows=0, expect_min=1)
    assert r.judge(10, 0.05, exempt_regress=True) is False
    r2 = _mk("CQy", "pa", rows=3, expect_min=1)
    assert r2.judge(10, 0.05, exempt_regress=False) is False   # 회귀
    assert r2.judge(10, 0.05, exempt_regress=True) is True     # 면제로 통과


# --- N03A (면제 악용 결함) ------------------------------------------------------

def test_n03a_is_a_fault_not_a_normal_delta():
    """분류가 접두어가 아니라 등록부여야 한다 — 'N' 으로 시작하지만 위양성 분모가 아니다."""
    from sdkb_paper.analysis.faults import NORMAL_KEYS

    assert "N03A" in FI.BY_KEY
    assert "N03A" not in NORMAL_KEYS
    assert FI.BY_KEY["N03A"].delta_type == "dedup"      # 선언은 dedup(거짓 선언)
    assert FI.BY_KEY["N03"].delta_type == "dedup"


def test_n03a_selects_only_non_identical_pairs():
    s = Store()
    cls = NamedNode(ONT + "Skill")
    for i in range(4):
        n = NamedNode(f"{ONT}E{i}")
        s.add(Quad(n, RDF_TYPE, cls))
        s.add(Quad(n, NamedNode(ONT + "p"), NamedNode(f"{ONT}v{i}")))   # 전부 서명이 다르다
    groups = FI._fake_dup_groups(s)
    assert groups and all(len(g) == 2 for g in groups)
    assert verify_groups(s, [[str(m) for m in g] for g in groups])["ok"] is False


def test_selection_never_includes_blank_nodes():
    """공백노드는 후보에서 빠져야 한다 — 라벨이 적재마다 달라 정렬 키에 섞이면 **같은 시드가
    같은 선택을 내지 못한다**(F16 위반). 실제로 N03A 첫 주입이 이 이유로 폐기됐다.
    """
    from pyoxigraph import BlankNode

    s = Store()
    cls = NamedNode(ONT + "Skill")
    for i in range(3):
        n = NamedNode(f"{ONT}E{i}")
        s.add(Quad(n, RDF_TYPE, cls))
        s.add(Quad(n, NamedNode(ONT + "p"), NamedNode(f"{ONT}v{i}")))
    for _ in range(2):                     # 타입이 붙은 공백노드(OWL 제약 등이 이렇게 생긴다)
        b = BlankNode()
        s.add(Quad(b, RDF_TYPE, cls))
        s.add(Quad(b, NamedNode(ONT + "p"), NamedNode(ONT + "vb")))
    for groups in (FI._dup_groups(s), FI._fake_dup_groups(s)):
        assert all(isinstance(m, NamedNode) for g in groups for m in g)


def test_dedup_selection_is_deterministic():
    """재판정이 병합쌍을 복원하려면 같은 시드가 같은 선택을 내야 한다."""
    s, _ = _store_with(True)
    a = FI.dedup_selection(s, "N03", 1.0, 7)
    b = FI.dedup_selection(s, "N03", 1.0, 7)
    assert a == b and a
    assert FI.dedup_selection(s, "F11", 1.0, 7) == []    # dedup 델타가 아닌 결함은 빈 목록
