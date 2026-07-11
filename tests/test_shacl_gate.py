from rdflib import Graph

from sdkb_paper.config import SAMPLES
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


def test_sample_graph_conforms():
    conforms, report = validate_graph(SAMPLE)
    assert conforms, report


def test_gate_rejects_patent_without_filing_date():
    g = _sample_plus("""
        pat:9999999999999 a ont:Patent ;
            ont:applicationNumber "9999999999999" ;
            ont:realizesProcess <https://w3id.org/sdkb/data/process/etch> .
    """)
    conforms, _ = validate_graph(g)
    assert not conforms  # filingDate 누락 -> 게이트가 막아야 함


def test_gate_rejects_patent_with_no_process_link():
    g = _sample_plus("""
        pat:9999999999998 a ont:Patent ;
            ont:applicationNumber "9999999999998" ;
            ont:filingDate "2022-05-01"^^xsd:date .
    """)
    conforms, _ = validate_graph(g)
    assert not conforms  # 공정 미매핑 -> 커버리지 분석의 전제가 깨짐


def test_gate_rejects_link_to_non_process():
    """ont:realizesProcess 의 객체가 공정이 아니면(예: 재료) 막아야 한다."""
    g = _sample_plus("""
        <https://w3id.org/sdkb/data/material/photoresist> a ont:Material ;
            skos:prefLabel "Photoresist"@en .
        pat:9999999999997 a ont:Patent ;
            ont:applicationNumber "9999999999997" ;
            ont:filingDate "2022-06-01"^^xsd:date ;
            ont:realizesProcess <https://w3id.org/sdkb/data/material/photoresist> .
    """)
    conforms, _ = validate_graph(g)
    assert not conforms


def test_gate_accepts_subprocess_link():
    """SubProcess ⊑ Process — RDFS 추론 하에서 하위 공정 링크는 통과해야 한다.

    이 계층이 깨지면 커버리지의 세밀한 층위(12개 SubProcess)를 아예 쓸 수 없다.
    """
    g = _sample_plus("""
        pat:9999999999996 a ont:Patent ;
            ont:applicationNumber "9999999999996" ;
            ont:filingDate "2022-07-01"^^xsd:date ;
            ont:realizesProcess <https://w3id.org/sdkb/data/subprocess/plasma_etch> .
    """)
    conforms, report = validate_graph(g)
    assert conforms, report
