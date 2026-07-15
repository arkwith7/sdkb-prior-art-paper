"""통합 테스트 — merge → validate 경계 (CLAUDE.md §5(b)).

깨지는 방식: 게이트를 우회한 델타가 그래프에 들어간다.
고정할 계약: **게이트 실패 시 그래프는 불변이다** (출력 파일이 생기지 않는다).

거부 경로를 확인하지 않은 게이트는 게이트가 아니다.
"""
from __future__ import annotations

import pytest
from rdflib import Graph

from sdkb_paper.config import SAMPLES
from sdkb_paper.ontology.merge import GateFailure, merge_with_gate

BASE = SAMPLES / "mini_graph.ttl"

PREFIXES = """
@prefix ont:  <https://w3id.org/sdkb/ont/> .
@prefix pat:  <https://w3id.org/sdkb/data/patent/> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .
"""

GOOD_DELTA = PREFIXES + """
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
pat:1020240000001 a ont:Patent ;
    skos:prefLabel "플라즈마 식각 장치"@ko ;
    ont:applicationNumber "1020240000001" ;
    ont:patentOffice "KR" ;
    ont:filingDate "2024-02-01"^^xsd:date ;
    ont:realizesProcess <https://w3id.org/sdkb/data/subprocess/plasma_etch> .
"""

# 출원일 없음 — H2 시계열의 전제가 깨진다
NO_DATE_DELTA = PREFIXES + """
pat:1020240000002 a ont:Patent ;
    ont:applicationNumber "1020240000002" ;
    ont:realizesProcess <https://w3id.org/sdkb/data/process/etch> .
"""

# 개념 매핑 없음 — 커버리지에도 시계열에도 기여할 수 없다
NO_CONCEPT_DELTA = PREFIXES + """
pat:1020240000003 a ont:Patent ;
    ont:applicationNumber "1020240000003" ;
    ont:filingDate "2024-03-01"^^xsd:date .
"""


def _delta(tmp_path, turtle: str):
    p = tmp_path / "delta.ttl"
    p.write_text(turtle, encoding="utf-8")
    return p


def test_gate_passes_and_merges(tmp_path):
    out = tmp_path / "graph_v1.ttl"
    g = merge_with_gate(BASE, _delta(tmp_path, GOOD_DELTA), out)

    assert out.exists()
    assert len(g) > len(Graph().parse(BASE))


@pytest.mark.parametrize(
    ("name", "turtle"),
    [("출원일_없음", NO_DATE_DELTA), ("개념_매핑_없음", NO_CONCEPT_DELTA)],
)
def test_gate_rejects_bad_delta_and_leaves_graph_untouched(tmp_path, name, turtle):
    out = tmp_path / "graph_v1.ttl"

    with pytest.raises(GateFailure):
        merge_with_gate(BASE, _delta(tmp_path, turtle), out)

    assert not out.exists(), f"{name}: 게이트가 실패했는데 그래프가 쓰였다 — 우회 경로가 생겼다"
