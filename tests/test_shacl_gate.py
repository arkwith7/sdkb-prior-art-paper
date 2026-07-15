"""L1 SHACL — 두 겹의 계약.

  graph shapes (queries/shapes/graph/) : G₀·G₁ 전체. 레거시 SIRP 특허를 포함하므로
      출원번호·출원일만 요구한다. 공정 링크 없는 디바이스 특허(G11C·H10B 등)를
      소급 처벌하지 않는다 — 그들을 공정에 억지 매핑하는 것이 날조이기 때문이다.
  delta shapes (queries/shapes/delta/) : 이 논문이 **병합하는** 특허. 개념 매핑
      (Process ∪ Device) ≥1 을 요구한다. 게이트의 의미는 "넣어도 되는 데이터인가"다.
"""
from rdflib import Graph

from sdkb_paper.config import SAMPLES, SHAPES_DELTA, SHAPES_GRAPH
from sdkb_paper.validate.shacl_gate import validate_graph

SAMPLE = SAMPLES / "mini_graph.ttl"

PREFIXES = """
@prefix ont:  <https://w3id.org/sdkb/ont/> .
@prefix pat:  <https://w3id.org/sdkb/data/patent/> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .
"""


def _sample_plus(turtle: str) -> Graph:
    g = Graph().parse(SAMPLE)
    g.parse(data=PREFIXES + turtle, format="turtle")
    return g


def test_sample_graph_conforms_to_both():
    for shapes in (SHAPES_GRAPH, SHAPES_DELTA):
        conforms, report = validate_graph(SAMPLE, shapes)
        assert conforms, f"{shapes.name}: {report}"


# --- 그래프 shapes: 출원번호·출원일 ------------------------------------------

def test_graph_gate_rejects_patent_without_filing_date():
    """출원일은 H2 시계열의 전제다 — 레거시든 신규든 예외 없다."""
    g = _sample_plus("""
        pat:9999999999999 a ont:Patent ;
            ont:applicationNumber "9999999999999" ;
            ont:realizesProcess <https://w3id.org/sdkb/data/process/etch> .
    """)
    conforms, _ = validate_graph(g, SHAPES_GRAPH)
    assert not conforms


def test_graph_gate_allows_patent_with_no_concept_link():
    """레거시 SIRP 에는 공정 링크 없는 디바이스 특허가 118건 있다. 그래프 shapes 는
    그것을 통과시켜야 한다 — 통과시키지 않으면 G₀ 자체가 조립되지 않는다."""
    g = _sample_plus("""
        pat:9999999999998 a ont:Patent ;
            skos:prefLabel "레거시 디바이스 특허"@ko ;
            ont:applicationNumber "9999999999998" ;
            ont:patentOffice "KR" ;
            ont:filingDate "2022-05-01"^^xsd:date .
    """)
    conforms, report = validate_graph(g, SHAPES_GRAPH)
    assert conforms, report


# --- 델타 shapes: 개념 매핑 ≥1 (Process ∪ Device) -----------------------------

def test_delta_gate_rejects_patent_with_no_concept_link():
    """병합되는 특허가 어떤 개념에도 안 걸리면 커버리지·시계열 분석에 기여할 수 없다."""
    g = _sample_plus("""
        pat:9999999999998 a ont:Patent ;
            ont:applicationNumber "9999999999998" ;
            ont:filingDate "2022-05-01"^^xsd:date .
    """)
    conforms, _ = validate_graph(g, SHAPES_DELTA)
    assert not conforms


def test_delta_gate_accepts_device_only_patent():
    """개념 축은 Process ∪ Device 다 — HBM·GAA 같은 H2 사례는 공정이 아니라 디바이스다."""
    g = _sample_plus("""
        <https://w3id.org/sdkb/data/device/hbm> a ont:Device ;
            skos:prefLabel "HBM"@en .
        pat:9999999999995 a ont:Patent ;
            ont:applicationNumber "9999999999995" ;
            ont:filingDate "2023-03-01"^^xsd:date ;
            ont:concernsDevice <https://w3id.org/sdkb/data/device/hbm> .
    """)
    conforms, report = validate_graph(g, SHAPES_DELTA)
    assert conforms, report


def test_delta_gate_rejects_link_to_non_process():
    """ont:realizesProcess 의 객체가 공정이 아니면(예: 재료) 막아야 한다."""
    g = _sample_plus("""
        <https://w3id.org/sdkb/data/material/photoresist> a ont:Material ;
            skos:prefLabel "Photoresist"@en .
        pat:9999999999997 a ont:Patent ;
            ont:applicationNumber "9999999999997" ;
            ont:filingDate "2022-06-01"^^xsd:date ;
            ont:realizesProcess <https://w3id.org/sdkb/data/material/photoresist> .
    """)
    conforms, _ = validate_graph(g, SHAPES_DELTA)
    assert not conforms


def test_delta_gate_accepts_subprocess_link():
    """SubProcess ⊑ Process — RDFS 추론 하에서 하위 공정 링크는 통과해야 한다.

    이 계층이 깨지면 커버리지의 세밀한 층위(12개 SubProcess)를 아예 쓸 수 없다.
    """
    g = _sample_plus("""
        pat:9999999999996 a ont:Patent ;
            ont:applicationNumber "9999999999996" ;
            ont:filingDate "2022-07-01"^^xsd:date ;
            ont:realizesProcess <https://w3id.org/sdkb/data/subprocess/plasma_etch> .
    """)
    conforms, report = validate_graph(g, SHAPES_DELTA)
    assert conforms, report
