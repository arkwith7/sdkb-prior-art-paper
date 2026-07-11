"""검증 게이트를 통과한 델타만 SDKB 그래프에 머지한다."""
from __future__ import annotations

from pathlib import Path

from rdflib import Graph

from sdkb_paper.validate.shacl_gate import validate_graph


class GateFailure(RuntimeError):
    pass


def merge_with_gate(base_ttl: Path, delta_ttl: Path, out_ttl: Path) -> Graph:
    """base + delta 를 합친 그래프가 SHACL 게이트를 통과할 때만 저장.

    실패 시 GateFailure(리포트 포함) — 델타를 그래프에 넣지 않는다.
    """
    g = Graph()
    g.parse(base_ttl)
    g.parse(delta_ttl)
    conforms, report = validate_graph(g)
    if not conforms:
        raise GateFailure(f"SHACL gate failed for {delta_ttl}:\n{report}")
    g.serialize(out_ttl, format="turtle")
    return g
