from pathlib import Path

from rdflib import Graph

from sdkb_paper.config import SAMPLES
from sdkb_paper.validate.shacl_gate import validate_graph

SAMPLE = SAMPLES / "mini_graph.ttl"


def test_sample_graph_conforms():
    conforms, report = validate_graph(SAMPLE)
    assert conforms, report


def test_gate_rejects_patent_without_filing_date():
    g = Graph().parse(SAMPLE)
    g.parse(data="""
        @prefix sdkb: <https://w3id.org/sdkb#> .
        sdkb:PBroken a sdkb:Patent ;
            sdkb:applicationNumber "9999999999999" ;
            sdkb:appliesToProcessStep sdkb:Etching .
    """, format="turtle")
    conforms, _ = validate_graph(g)
    assert not conforms  # filingDate 누락 -> 게이트가 막아야 함
