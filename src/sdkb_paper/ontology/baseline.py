"""baseline 그래프(graph_v0) 조립 — H1 의 "before".

vendor 한 SDKB 스냅샷(TBox + 도메인 ABox)을 합쳐 `data/processed/graph_v0.ttl` 로 굳힌다.
특허는 한 건도 들어있지 않다 — KIPRIS 보강 델타가 머지되면서 graph_v1 이 되고,
H1 은 v0 대비 v1 의 공정 단계 커버리지 증가를 검정한다.

산출물은 결정적(deterministic)이다: 같은 스냅샷 -> 같은 그래프. 그래서 graph_v0.ttl 자체는
gitignore 두고, 커밋되는 것은 `data/external/sdkb/` 스냅샷 + PROVENANCE.json 이다.

CLI:  python -m sdkb_paper.ontology.baseline
"""
from __future__ import annotations

import json
from pathlib import Path

from rdflib import RDF, Graph

from sdkb_paper.config import EXTERNAL_SDKB, GRAPH_V0, ONT, bind_namespaces

# TBox 3종 + 도메인 ABox 1종. 순서 = 머지 순서.
BASELINE_PARTS = [
    "sdkb-core.ttl",
    "sdkb-patent.ttl",
    "sdkb-foresight.ttl",
    "sdkb-core-data.ttl",
]


def build_baseline(snapshot: Path = EXTERNAL_SDKB, out: Path = GRAPH_V0) -> Graph:
    prov_path = snapshot / "PROVENANCE.json"
    if not prov_path.exists():
        raise SystemExit(
            f"[baseline] 스냅샷이 없다: {snapshot}\n"
            f"           먼저 `make vendor` 를 실행할 것."
        )

    g = Graph()
    bind_namespaces(g)
    for part in BASELINE_PARTS:
        g.parse(snapshot / part, format="turtle")

    out.parent.mkdir(parents=True, exist_ok=True)
    g.serialize(out, format="turtle")

    prov = json.loads(prov_path.read_text(encoding="utf-8"))
    counts = summarize(g)
    print(f"[baseline] {out}  ({len(g):,} triples)")
    print(f"[baseline] SDKB commit {prov['source_commit'][:12]}")
    print(f"[baseline] Process={counts['Process']}  SubProcess={counts['SubProcess']}  "
          f"Patent={counts['Patent']}  (Patent=0 이어야 정상 — 보강 전 상태)")
    if counts["Patent"]:
        raise SystemExit(
            f"[baseline] ✗ baseline 에 특허 {counts['Patent']}건이 들어있다. "
            f"SIRP ABox 가 섞였는지 확인할 것 — before 에 특허가 있으면 H1 이 성립하지 않는다."
        )
    return g


def summarize(g: Graph) -> dict[str, int]:
    """baseline 의 관측 단위(공정 계층)와 특허 수. SubProcess ⊑ Process 이므로 명시 타입으로 센다."""
    return {
        name: sum(1 for _ in g.subjects(RDF.type, ONT[name]))
        for name in ("Process", "SubProcess", "Patent")
    }


def main() -> None:
    build_baseline()


if __name__ == "__main__":
    main()
