"""explore.store 스모크 테스트 — 읽기 전용 pyoxigraph 계층의 계약.

논문 산출물을 만들지 않는 진단 도구이지만, SELECT/ASK/CONSTRUCT 직렬화와
미바인딩 처리는 회귀로 고정한다(프런트가 이 스키마에 의존한다).
큰 그래프(G₀/G₁/G₂)는 건드리지 않고 합성 픽스처 mini_graph.ttl 만 쓴다.
"""
from __future__ import annotations

import pytest

from sdkb_paper.config import ROOT
from sdkb_paper.explore import store

MINI = ROOT / "data" / "samples" / "mini_graph.ttl"


@pytest.fixture
def mini(monkeypatch):
    """store 의 그래프 레지스트리에 mini_graph 를 'mini' 키로 임시 등록."""
    store.GRAPHS["mini"] = (MINI, "mini fixture")
    store._stores.pop("mini", None)
    yield "mini"
    store.GRAPHS.pop("mini", None)
    store._stores.pop("mini", None)


def test_select_serializes_terms(mini):
    res = store.run_query(mini, "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 5")
    assert res.kind == "select"
    assert res.columns == ["s", "p", "o"]
    assert res.rows
    cell = res.rows[0][0]
    assert cell["type"] in {"uri", "bnode", "literal"}
    assert "value" in cell


def test_ask(mini):
    res = store.run_query(mini, "ASK { ?s ?p ?o }")
    assert res.kind == "ask"
    assert res.boolean is True


def test_construct_shape(mini):
    res = store.run_query(mini, "CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o } LIMIT 3")
    assert res.kind == "construct"
    assert res.triples and set(res.triples[0]) == {"s", "p", "o"}


def test_unbound_is_none(mini):
    # OPTIONAL 로 절대 바인딩되지 않는 변수 → 셀은 None 이어야 한다(프런트가 '—' 로 렌더).
    res = store.run_query(
        mini, "SELECT ?s ?nope WHERE { ?s ?p ?o . OPTIONAL { ?s <urn:no-such-pred> ?nope } } LIMIT 1"
    )
    assert res.rows[0][1] is None


def test_unknown_graph_key():
    with pytest.raises(KeyError):
        store.run_query("nonexistent", "ASK {}")
