"""PLAN-075 §12.7 검증 — 관계 항·투영 항·재정규화.

ⓐ 단위: `s(a,a)=0` · 빈 집합 · 결측 재정규화 · 표 대칭성 · `side` 인자 부재(§7 ②)
ⓑ 통합: 두 신설 가중 0 → 기존 경로와 동일(§7 ⑤) · 한 항만 켠 두 구성이 갈린다(§7 ⑥′)
"""
from __future__ import annotations

import inspect

import pytest

from sdkb_paper.ontology import concept_relations as CR
from sdkb_paper.retrieval import claim_projection as CP
from sdkb_paper.retrieval import systems as S

EDGES = [
    {"src": "process:a", "predicate": "HAS_SUBPROCESS", "dst": "subprocess:b", "weight": 1.0},
    {"src": "subprocess:b", "predicate": "USES_MATERIAL", "dst": "material:c", "weight": 0.6},
    {"src": "subprocess:b", "predicate": "REQUIRES_SKILL", "dst": "skill:s", "weight": 1.0},
    {"src": "subprocess:b", "predicate": "NOT_ALLOWED_WITH", "dst": "material:x", "weight": -1.0},
]


def _adj(**kw):
    kw.setdefault("drop_expert", True)
    kw.setdefault("drop_negative", True)
    kw.setdefault("use_weight", False)
    return CR._adjacency(EDGES, **kw)


def test_slug_strips_axis_prefix():
    """정규화는 접두 제거 하나 — 빠뜨리면 항이 항상 0 이 된다(PLAN-073 §10.2a)."""
    assert CR._slug("process:etch") == "etch"
    assert CR._slug("etch") == "etch"


def test_expert_and_negative_predicates_are_excluded():
    """A8 음성대조군 오염 방지(전문가 축)와 부호 역전 방지(음수 가중) — §12.3."""
    adj = _adj()
    assert "s" not in adj["b"], "전문가 축 술어가 남으면 A8 이 경로항을 함께 흔든다"
    assert "x" not in adj["b"], "비양립 관계는 유사도 경로가 아니다"
    assert adj["b"]["c"] == 1.0, "weight 기본 미사용 → 전 엣지 1.0"


def test_weight_toggle_uses_absolute_value():
    adj = _adj(use_weight=True, drop_negative=False)
    assert adj["b"]["c"] == pytest.approx(0.6)
    assert adj["b"]["x"] == pytest.approx(1.0)


def test_hops_excludes_self_and_respects_max_hop():
    adj = _adj()
    assert CR._hops(adj, "a", 1) == {"b": 1}
    assert CR._hops(adj, "a", 2) == {"b": 1, "c": 2}
    assert "a" not in CR._hops(adj, "a", 3), "s(a,a)=0 — 자기 자신은 표에 없다"


class _Feats:
    """`OntologyFeatures.rel_sim` 만 떼어 쓰는 최소 대역(대칭 표 · 결측 판정)."""

    from sdkb_paper.retrieval.ontology_rerank import OntologyFeatures

    rel_sim = OntologyFeatures.rel_sim
    has_rel = OntologyFeatures.has_rel

    def __init__(self, table):
        self._rel = table
        self._rel_nodes = None

    @property
    def rel(self):
        return self._rel


TABLE = {("a", "b"): 1.0, ("a", "c"): 0.5}


def test_rel_sim_exact_match_is_zero():
    """정확 일치에 0 — 겹침은 ConceptOverlap 이 이미 센다(§12.2 이중 계상 금지)."""
    f = _Feats(TABLE)
    assert f.rel_sim(frozenset({"a"}), frozenset({"a"})) == 0.0
    assert f.rel_sim(frozenset({"a"}), frozenset({"b"})) == 1.0
    assert f.rel_sim(frozenset({"a"}), frozenset({"c"})) == 0.5


def test_rel_sim_is_key_order_independent():
    """표는 상삼각만 보관하므로 조회는 정렬 키로 한다."""
    f = _Feats(TABLE)
    assert f.rel_sim(frozenset({"b"}), frozenset({"a"})) == 1.0


def test_rel_sim_empty_sets_and_empty_table():
    f = _Feats(TABLE)
    assert f.rel_sim(frozenset(), frozenset({"a"})) == 0.0
    assert f.rel_sim(frozenset({"a"}), frozenset()) == 0.0
    assert _Feats({}).rel_sim(frozenset({"a"}), frozenset({"b"})) == 0.0


def test_rel_sim_aggregates_mean_of_max():
    f = _Feats(TABLE)
    got = f.rel_sim(frozenset({"a", "zzz"}), frozenset({"b"}))
    assert got == pytest.approx(0.5), "mean_q max_d — 관계 없는 개념은 0 으로 평균에 든다"


def test_has_rel_detects_missing():
    f = _Feats(TABLE)
    assert f.has_rel(frozenset({"a"})) is True
    assert f.has_rel(frozenset({"zzz"})) is False


# --- 결측 재정규화 (§12.2) ---------------------------------------------------
def test_renormalize_drops_and_rescales():
    """결측 항은 0 이 아니라 제외 — 남은 가중이 그 몫을 비례로 받는다."""
    w = S.renormalize({"c": 0.5, "f2": 0.5}, {"f2": False})
    assert w["f2"] == 0.0
    assert w["c"] == pytest.approx(1.0)
    assert sum(w.values()) == pytest.approx(1.0)


def test_renormalize_is_identity_when_all_available():
    w = {"c": 0.25, "f": 0.5, "r": 0.25}
    assert S.renormalize(w, {}) == w


def test_renormalize_survives_total_absence():
    w = {"r": 1.0}
    assert S.renormalize(w, {"r": False}) == w, "전부 결측이면 순위가 바뀌지 않으므로 그대로 둔다"


# --- §7 ② 대칭: 적용 함수가 질의/후보를 구분하지 않는다 ----------------------
def test_no_side_argument_anywhere():
    """비대칭 적용은 T1 을 오염시키므로 **구조로** 막는다(§7 ②)."""
    for fn in (CR.build, CR._adjacency, CR._hops, CP.ProjectionIndex.u2, CP.ProjectionIndex.has):
        assert "side" not in inspect.signature(fn).parameters


def test_projection_slug_normalization():
    assert CP._slug("process:deposition") == "deposition"


# --- §7 ⑤ / ⑥′ 회귀 ---------------------------------------------------------
def test_onto_config_label_unchanged_when_new_weights_zero():
    """run 파일 경로가 바뀌면 바이트 동일성이 경로에서부터 깨진다."""
    assert S.OntoConfig().label() == "a0.5_c1.0_h0.0_i0.0_ax14_p1_i1"
    assert S.OntoConfig(w_r=0.1).label().endswith("_r0.1")
    assert S.OntoConfig(w_f2=0.2).label().endswith("_f20.2")


def test_lambda_grid_keeps_p1_ratios():
    """P1 을 재선택하지 않는다 — 네 항의 비율은 고정, 새 항의 몫만 뗀다(§12.6)."""
    from sdkb_paper.analysis.ontology_eval import lambda_grid

    w4 = (0.25, 0.0, 0.25, 0.5)
    assert lambda_grid(w4) == (*w4, 0.0, 0.0)
    w6 = lambda_grid(w4, lam_r=0.1)
    assert sum(w6) == pytest.approx(1.0)
    assert w6[0] / w6[3] == pytest.approx(w4[0] / w4[3])
    assert w6[4] == 0.1
    with pytest.raises(ValueError):
        lambda_grid(w4, lam_r=0.7, lam_f2=0.7)


def test_rerank_p2_matches_p1_when_new_weights_zero():
    """§7 ⑤ — 두 신설 가중이 0 이면 기존 P1 순위와 **동일**하다."""
    from sdkb_paper.analysis.ontology_eval import rerank_p1, rerank_p2

    rows_p1 = [("d1", 1.0, 0.4, 0.0, 0.1, (0.2,)), ("d2", 0.5, 0.9, 0.0, 0.0, (0.1,))]
    rows_p2 = [(*r, 1.0, True, 1.0, True) for r in rows_p1]
    w4 = (0.25, 0.0, 0.25, 0.5)
    assert (rerank_p2({"q": rows_p2}, 0, 0.75, (*w4, 0.0, 0.0))
            == rerank_p1({"q": rows_p1}, 0, 0.75, w4))


def test_terms_are_separable():
    """§7 ⑥′ — 한 항만 켠 두 구성의 산출이 서로 다르다."""
    from sdkb_paper.analysis.ontology_eval import rerank_p2

    rows = [("d1", 1.0, 0.0, 0.0, 0.0, (0.0,), 1.0, True, 0.0, True),
            ("d2", 1.0, 0.0, 0.0, 0.0, (0.0,), 0.0, True, 1.0, True)]
    only_r = rerank_p2({"q": rows}, 0, 1.0, (0.0, 0.0, 0.0, 0.0, 1.0, 0.0))
    only_f2 = rerank_p2({"q": rows}, 0, 1.0, (0.0, 0.0, 0.0, 0.0, 0.0, 1.0))
    assert only_r["q"][0] == "d1"
    assert only_f2["q"][0] == "d2"
