"""L1 SHACL 게이트.

L1 은 두 겹이다:
  queries/shapes/graph/  — 그래프 전체(G₀·G₁). 레거시 SIRP 특허를 포함하므로 완화 제약.
  queries/shapes/delta/  — 이 논문이 병합하는 델타. 개념 매핑(Process ∪ Device) ≥1 을 요구.

게이트의 의미는 "그래프에 넣어도 되는 데이터인가"이지 상류가 남긴 데이터의 소급 처벌이 아니다.

CLI:  python -m sdkb_paper.validate.shacl_gate <graph.ttl> [--shapes graph|delta|<경로>]
      (부적합 시 exit code 1 -> CI 에서 게이트로 동작)
"""
from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable
from pathlib import Path

from pyshacl import validate
from rdflib import RDF, BNode, Graph, URIRef
from rdflib.namespace import SH

from sdkb_paper import profile as _profile
from sdkb_paper.config import SHAPES_GRAPH

def resolve_shapes(spec: str | Path = "graph", profile=None) -> Path:
    """'graph' / 'delta' 같은 이름이나 경로를 shapes 로 푼다 — **경로는 프로파일 값이다.**"""
    if isinstance(spec, str) and spec in ("graph", "delta"):
        prof = _profile.resolve(profile)
        return prof.shapes_graph if spec == "graph" else prof.shapes_delta
    return Path(spec)


def load_shapes(shapes_dir: Path | str = SHAPES_GRAPH, profile=None) -> Graph:
    """shapes 를 적재한다. **디렉터리와 단일 TTL 을 모두 받는다.**

    SDKB 의 shape 은 `queries/shapes/{graph,delta}/` 디렉터리이지만, 자원에 따라서는 배포
    TTL 자체에 SHACL 이 내장돼 있어(예: Brick) 디렉터리가 아니다. 빈 shapes 를 조용히
    통과시키지 않는 규율은 그대로 둔다 — 빈 검사는 검사가 아니다.
    """
    shapes_dir = resolve_shapes(shapes_dir, profile)
    shapes = Graph()
    if shapes_dir.is_file():
        shapes.parse(shapes_dir)
    else:
        for ttl in sorted(shapes_dir.glob("*.ttl")):
            shapes.parse(ttl)
    if not len(shapes):
        raise SystemExit(f"[shacl_gate] shapes 가 비었다: {shapes_dir}")
    return shapes


def target_only(shapes: Graph, nodes: Iterable[URIRef]) -> Graph:
    """shape 의 sh:targetClass 를 주어진 노드들로 좁힌 사본을 만든다.

    델타 검증에 필요하다. 델타를 **단독으로** 검증할 수는 없다 — 델타에는 TBox 도, 델타가
    가리키는 공정 인스턴스도 없어서 `sh:class ont:Process` 가 성립하지 않는다. 그렇다고
    base+delta 전체에 엄격 shape 를 걸면 레거시 특허까지 소급 처벌한다. 그래서 그래프는
    합치되 **대상만 델타의 특허로 좁힌다.**
    """
    scoped = Graph()
    for t in shapes:
        scoped.add(t)
    for s, _, _ in shapes.triples((None, SH.targetClass, None)):
        scoped.remove((s, SH.targetClass, None))
        for n in nodes:
            scoped.add((s, SH.targetNode, n))
    return scoped


def validate_graph(
    data: Graph | Path, shapes: Path | str | Graph = SHAPES_GRAPH, profile=None
) -> tuple[bool, str]:
    g = data if isinstance(data, Graph) else Graph().parse(data)
    shapes_graph = shapes if isinstance(shapes, Graph) else load_shapes(shapes, profile)
    conforms, _, report_text = validate(g, shacl_graph=shapes_graph, inference="rdfs")
    return bool(conforms), report_text


# --- EP5 · 기준 대비 신규 위반 (SPEC-010 §6.2) --------------------------------
#
# **왜 `conforms` 이진이 아닌가.** 제2 도메인에서는 무결한 그래프도 `conforms=False` 다
# (Brick 공식 예제가 Brick 자신의 shape 을 통과하지 않는다 — 실측 `sh:Violation` 293건).
# 상수를 내는 게이트는 결함을 구분하지 못하므로, 판정을 **변화**로 옮긴다. T3 가 행 수 회귀를
# 보는 것과 같은 형태이며, 두 층을 같은 자로 읽을 수 있게 된다.
#
# 텍스트 보고서를 파싱하지 않는다 — 결과 그래프를 직접 읽는다. 문구가 바뀌면 조용히 틀리는
# 파서를 만들지 않기 위해서다.

def violation_set(data: Graph | Path, shapes: Path | str | Graph = SHAPES_GRAPH,
                  profile=None, *, inference: str = "rdfs") -> set[tuple]:
    """`sh:Violation` 등급 결과의 정규화 튜플 집합. `sh:Warning`·`sh:Info` 는 세지 않는다."""
    g = data if isinstance(data, Graph) else Graph().parse(data)
    shapes_graph = shapes if isinstance(shapes, Graph) else load_shapes(shapes, profile)
    _conforms, results, _txt = validate(g, shacl_graph=shapes_graph, inference=inference,
                                        advanced=True)
    out: set[tuple] = set()
    for r in results.subjects(RDF.type, SH.ValidationResult):
        if results.value(r, SH.resultSeverity) != SH.Violation:
            continue
        out.add(tuple(_term(results.value(r, k)) for k in
                      (SH.sourceShape, SH.focusNode, SH.resultPath,
                       SH.sourceConstraintComponent, SH.value)))
    return out


def _term(v) -> str:
    """공백노드는 라벨이 적재마다 달라지므로 종류만 남긴다 — 차집합이 흔들리지 않게."""
    if v is None:
        return ""
    return "_:bnode" if isinstance(v, BNode) else str(v)


def new_violations(new: Graph | Path, base: Graph | Path,
                   shapes: Path | str | Graph = SHAPES_GRAPH, profile=None) -> dict:
    """L1 판정 — 기준 대비 **신규** 위반이 하나라도 있으면 실패다(SPEC-010 §6.2)."""
    v_base = violation_set(base, shapes, profile)
    v_new = violation_set(new, shapes, profile)
    added = sorted(v_new - v_base)
    removed = sorted(v_base - v_new)
    return {"pass": not added, "n_base": len(v_base), "n_new": len(v_new),
            "n_added": len(added), "n_removed": len(removed),
            "added": [list(a) for a in added[:50]]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("graph", type=Path)
    ap.add_argument(
        "--shapes", default="graph",
        help="graph(기본, 전체 그래프) | delta(병합 델타) | shapes 디렉터리·파일 경로",
    )
    ap.add_argument("--profile", default=None, help="자원 프로파일(기본: SDKB_PROFILE 또는 sdkb)")
    args = ap.parse_args()

    conforms, report = validate_graph(args.graph, args.shapes, args.profile)
    print(report)
    print(f"[shacl_gate] {args.graph}  shapes={args.shapes}  conforms = {conforms}")
    sys.exit(0 if conforms else 1)


if __name__ == "__main__":
    main()
