"""EP5 판정 장치의 계약 (PLAN-064 A-4 · SPEC-010).

여기서 지키는 명제는 다섯이다.
1. **인스턴스 구성** — 사전등록 §4.2 의 21 이 코드에서도 21 이다.
2. **결정성** — 정상 델타 생성기와 델타 그래프가 같은 입력에서 같은 것을 낸다.
3. **조용한 오염 차단** — 워크스페이스 재사용으로 결함이 두 번 주입되지 않는다.
4. **L1 판정 형태** — 기준 대비 신규 위반만 실패로 센다.
5. **사영의 가시성** — OWL Full 트리플을 몇 개 뺐는지 셀 수 있다(조용히 빼지 않는다).
"""
from __future__ import annotations

import pytest
from rdflib import Graph, Literal, Namespace, OWL, RDF, RDFS, URIRef

from sdkb_paper import profile as P
from sdkb_paper.validate import reasoner_gate as RG

EX = Namespace("http://example.org/ep5#")
SH = Namespace("http://www.w3.org/ns/shacl#")

# --- 1. 인스턴스 구성 ---------------------------------------------------------
def test_fault_matrix_is_twentyone():
    """사전등록 §4.2 — (M) 9+9 와 (S) 3. 개수가 바뀌면 사전등록이 바뀐 것이다."""
    from sdkb_paper.analysis.ep5 import fault_instances

    inst = fault_instances("brick")
    assert len(inst) == 21
    per = {k: sum(1 for a, _s, _r in inst if a == k) for k in ("X2", "X3", "X4")}
    assert per == {"X2": 9, "X3": 3, "X4": 9}

def test_x3_has_one_rep_because_it_is_deterministic():
    """무작위 요소가 없는 조작에 반복을 주면 같은 결과를 세 번 세게 된다."""
    assert P.load("brick").faults["X3"].reps == (1,)

def test_brick_profile_has_no_approval_formula():
    """T1·T2 가 없으므로 `accept` 는 null 이다 — 부분 승인식을 승인식이라 부르지 않는다."""
    assert P.load("brick").has_t1_t2 is False

# --- 2. 결정성 ---------------------------------------------------------------

def test_normal_deltas_are_deterministic_and_declare_substitution():
    """규칙에 재료가 없으면 **대체를 기록한다** — 라벨만 남기고 내용이 다르면 표가 거짓이다."""
    from sdkb_paper.ontology import ep5_graphs as EG

    a = EG.synthetic_normal_deltas("d0", 8, abox_files=EG.DEV_ABOX)
    b = EG.synthetic_normal_deltas("d0", 8, abox_files=EG.DEV_ABOX)
    assert [x["digest"] for x in a] == [x["digest"] for x in b]
    for rec in a:
        if "substituted_from" in rec:
            assert rec["rule"] != rec["substituted_from"]

def test_tbox_delta_excludes_bnodes_and_counts_them():
    """공백노드는 적재마다 라벨이 달라 차집합을 흔든다 — 빼되 개수는 남긴다."""
    from sdkb_paper.ontology import ep5_graphs as EG

    d = EG.tbox_delta("d2", "d3")
    assert all(not EG._has_bnode(t) for t in d.added)
    assert d.n_bnode_added > 0
    assert d.summary()["n_added"] == len(d.added)

# --- 3. 조용한 오염 차단 -------------------------------------------------------
def test_load_wipes_a_stale_store(tmp_path):
    """방향 역전처럼 멱등이 아닌 조작은 두 번 걸면 원상 복구된다 — 재사용을 막는다."""
    from pyoxigraph import NamedNode, Quad

    from sdkb_paper.validate import fault_inject as FI

    src = tmp_path / "g.ttl"
    src.write_text("<http://a> <http://p> <http://b> .\n")
    ws = tmp_path / "ws"
    ws.mkdir()
    s1 = FI.load(src, ws)
    s1.add(Quad(NamedNode("http://x"), NamedNode("http://p"), NamedNode("http://y")))
    del s1
    s2 = FI.load(src, ws)
    assert len(list(s2.quads_for_pattern(NamedNode("http://x"), None, None, None))) == 0

# --- 4. L1 판정 형태 -----------------------------------------------------------
def _shapes() -> Graph:
    g = Graph()
    g.add((EX.S, RDF.type, SH.NodeShape))
    g.add((EX.S, SH.targetClass, EX.Thing))
    b = URIRef("http://example.org/ep5#prop")
    g.add((EX.S, SH.property, b))
    g.add((b, SH.path, RDFS.label))
    g.add((b, SH.minCount, Literal(1)))
    return g

def test_new_violations_ignores_preexisting_ones(tmp_path):
    """무결한 그래프도 위반을 내는 자원이 있다 — 절대값이 아니라 **변화**를 본다."""
    from sdkb_paper.validate.shacl_gate import new_violations

    base = Graph()
    base.add((EX.a, RDF.type, EX.Thing))          # 라벨 없음 = 이미 위반
    bp = tmp_path / "base.ttl"
    base.serialize(bp, format="turtle")
    same = tmp_path / "same.ttl"
    base.serialize(same, format="turtle")
    r = new_violations(same, bp, shapes=_shapes())
    assert r["n_base"] > 0 and r["n_added"] == 0 and r["pass"]

    worse = Graph()
    for t in base:
        worse.add(t)
    worse.add((EX.b, RDF.type, EX.Thing))         # 신규 위반 1건
    wp = tmp_path / "worse.ttl"
    worse.serialize(wp, format="turtle")
    r2 = new_violations(wp, bp, shapes=_shapes())
    assert r2["n_added"] == 1 and not r2["pass"]

def test_unknown_l1_mode_dies_at_load():
    from sdkb_paper.profile import ProfileError

    p = P.load("brick")
    bad = type(p)(**{**p.__dict__, "l1_mode": "whatever"})
    with pytest.raises(ProfileError):
        from sdkb_paper.profile import _validate
        _validate(bad)

# --- 5. 사영의 가시성 ----------------------------------------------------------
def test_dl_projection_is_counted_and_applied():
    """클래스 계층에 OWL 빌트인을 얹으면 DL 밖이다 — 빼되 몇 개를 뺐는지 말한다."""
    g = Graph()
    g.add((EX.EntityProperty, RDF.type, OWL.Class))
    g.add((EX.EntityProperty, RDFS.subClassOf, OWL.ObjectProperty))
    g.add((EX.A, RDFS.subClassOf, EX.B))
    assert RG.dl_projection_count(g) == 1
    view = RG.reasoning_view(g)
    assert (EX.EntityProperty, RDFS.subClassOf, OWL.ObjectProperty) not in view
    assert (EX.A, RDFS.subClassOf, EX.B) in view

def test_dl_projection_is_a_noop_on_sdkb():
    """SDKB 경로의 동작은 한 글자도 바뀌지 않아야 한다(SPEC-009 계약 ①)."""
    from sdkb_paper import config

    g = Graph().parse(config.GRAPH_V0)
    assert RG.dl_projection_count(g) == 0
