#!/usr/bin/env python3
"""Generate the PLAN-087 running-example excerpt from ``mini_graph.ttl``.

The manuscript must not hand-copy RDF facts from the fixture.  This generator
selects the exact nine statements used by Example 1, verifies that every
statement still exists, and writes a stable Markdown/Turtle block.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from rdflib import Graph, Namespace, RDF, URIRef

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "samples" / "mini_graph.ttl"
DEFAULT_OUT = ROOT / "paper" / "tables" / "example_1_graph.md"

ONT = Namespace("https://w3id.org/sdkb/ont/")
PAT = Namespace("https://w3id.org/sdkb/data/patent/")
DATA = Namespace("https://w3id.org/sdkb/data/")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")

SUBJECT = PAT["1020130000004"]
PLASMA = URIRef(DATA["subprocess/plasma_etch"])
SKILL = URIRef(DATA["skill/endpoint_detection"])
EXPERT = URIRef(DATA["expert/EXP_M01"])
PRIOR = URIRef(DATA["patent/us_US7000001"])


def required_triples() -> list[tuple]:
    """The nine RDF statements narrated in Example 1 (two rdf:type objects)."""
    from rdflib import Literal

    return [
        (SUBJECT, RDF.type, ONT.Patent),
        (SUBJECT, RDF.type, ONT.RejectedPatent),
        (SUBJECT, SKOS.prefLabel, Literal("플라즈마 식각 종점 검출 방법", lang="ko")),
        (SUBJECT, ONT.filingDate, Literal("2013-05-10", datatype=XSD.date)),
        (SUBJECT, ONT.realizesProcess, PLASMA),
        (SUBJECT, ONT.rejectedFor, ONT.Rejection_Inventiveness),
        (SUBJECT, ONT.hasPriorArtExaminer, PRIOR),
        (PLASMA, ONT.requiresSkill, SKILL),
        (EXPERT, ONT.hasSkill, SKILL),
    ]


def render(source: Path = SOURCE) -> str:
    graph = Graph().parse(source, format="turtle")
    missing = [triple for triple in required_triples() if triple not in graph]
    if missing:
        details = "\n".join(f"  - {triple!r}" for triple in missing)
        raise ValueError(f"예시 1의 필수 트리플이 픽스처에 없다:\n{details}")

    return """```turtle
pat:1020130000004  a  ont:Patent, ont:RejectedPatent ;
    skos:prefLabel          \"플라즈마 식각 종점 검출 방법\"@ko ;
    ont:filingDate          \"2013-05-10\"^^xsd:date ;
    ont:realizesProcess     <…/subprocess/plasma_etch> ;
    ont:rejectedFor         ont:Rejection_Inventiveness ;
    ont:hasPriorArtExaminer <…/patent/us_US7000001> .
<…/subprocess/plasma_etch>  ont:requiresSkill <…/skill/endpoint_detection> .
<…/expert/EXP_M01>          ont:hasSkill      <…/skill/endpoint_detection> .
```
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("-o", "--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    text = render(args.source)
    if args.check:
        if not args.out.exists() or args.out.read_text(encoding="utf-8") != text:
            print(f"불일치: {args.out} — gen_example_excerpt.py 로 재생성한다")
            return 1
        print(f"통과: {args.out} (픽스처 유래 트리플 9건)")
        return 0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")
    print(f"wrote {args.out} (픽스처 유래 트리플 9건)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
