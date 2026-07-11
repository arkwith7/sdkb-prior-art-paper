"""SHACL 게이트: queries/shapes/*.ttl 전체로 데이터 그래프를 검증.

CLI:  python -m sdkb_paper.validate.shacl_gate <graph.ttl>
      (부적합 시 exit code 1 -> CI 에서 게이트로 동작)
"""
from __future__ import annotations

import sys
from pathlib import Path

from pyshacl import validate
from rdflib import Graph

from sdkb_paper.config import QUERIES_SHAPES


def load_shapes(shapes_dir: Path = QUERIES_SHAPES) -> Graph:
    shapes = Graph()
    for ttl in sorted(shapes_dir.glob("*.ttl")):
        shapes.parse(ttl)
    return shapes


def validate_graph(data: Graph | Path, shapes_dir: Path = QUERIES_SHAPES) -> tuple[bool, str]:
    g = data if isinstance(data, Graph) else Graph().parse(data)
    conforms, _, report_text = validate(g, shacl_graph=load_shapes(shapes_dir), inference="rdfs")
    return bool(conforms), report_text


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: python -m sdkb_paper.validate.shacl_gate <graph.ttl>")
        sys.exit(2)
    conforms, report = validate_graph(Path(sys.argv[1]))
    print(report)
    print(f"[shacl_gate] conforms = {conforms}")
    sys.exit(0 if conforms else 1)


if __name__ == "__main__":
    main()
