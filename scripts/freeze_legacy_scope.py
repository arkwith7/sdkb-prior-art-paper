"""복원 이전 공정 집합(20개)을 커밋된 스냅샷에서 추출해 동결한다.

H1 은 두 표본 집합으로 병기 보고된다 — 확장 49 와 **복원 이전 20**(PLAN-001 §3.5).
복원된 단계는 G₀ 에서 C₀(s)=0 이라 H1 에 유리한 편향이 있으므로, 독자가 "새로 추가한 단계
덕분에 산 결과인가"를 판별할 수 있어야 한다.

문제는 20개가 무엇인지 **현재 그래프만 보고는 알 수 없다**는 것이다 — 복원분과 원래분이
똑같이 `dcterms:source = semikong`, `Table 7` 이다 (복원이었으니 당연하다). 손으로 고르면
사후에 유리한 20개를 고를 여지가 남는다.

그래서 **복원 이전의 vendor 스냅샷**(커밋 SOURCE_COMMIT, SDKB c49dea0)에서 기계적으로 뽑는다.
멱등하다 — 같은 커밋 → 같은 CSV.
"""
from __future__ import annotations

import csv
import subprocess
import tempfile
from pathlib import Path

from rdflib import RDF, Graph, URIRef

from sdkb_paper.config import LEGACY_SCOPE, ONT, ROOT

# 복원 이전 마지막 vendor 스냅샷을 담은 커밋 (SDKB c49dea0 · Process 8 + SubProcess 12).
SOURCE_COMMIT = "eaf8406"
SNAPSHOT_DIR = "data/external/sdkb"

PREF_LABEL = URIRef("http://www.w3.org/2004/02/skos/core#prefLabel")


def _snapshot_graph(commit: str) -> Graph:
    """해당 커밋의 스냅샷 TTL 을 워킹트리를 건드리지 않고 읽는다."""
    listing = subprocess.run(
        ["git", "ls-tree", "--name-only", commit, f"{SNAPSHOT_DIR}/"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout.split()

    g = Graph()
    with tempfile.TemporaryDirectory() as tmp:
        for path in (p for p in listing if p.endswith(".ttl")):
            blob = subprocess.run(
                ["git", "show", f"{commit}:{path}"],
                cwd=ROOT, capture_output=True, text=True, check=True,
            ).stdout
            f = Path(tmp) / Path(path).name
            f.write_text(blob, encoding="utf-8")
            g.parse(f)
    return g


def freeze(out: Path = LEGACY_SCOPE, commit: str = SOURCE_COMMIT) -> list[dict[str, str]]:
    g = _snapshot_graph(commit)
    rows = [
        {
            "iri": str(s),
            "level": level,
            "label": str(next(g.objects(s, PREF_LABEL), "")),
            "source_commit": commit,
        }
        for level, cls in (("process", ONT["Process"]), ("subprocess", ONT["SubProcess"]))
        for s in sorted(g.subjects(RDF.type, cls), key=str)
    ]

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["iri", "level", "label", "source_commit"])
        w.writeheader()
        w.writerows(rows)
    return rows


def main() -> None:
    rows = freeze()
    n_p = sum(r["level"] == "process" for r in rows)
    print(f"✓ 복원 이전 집합 동결: Process {n_p} + SubProcess {len(rows) - n_p} = {len(rows)}개")
    print(f"  출처 커밋 {SOURCE_COMMIT} · {LEGACY_SCOPE}")


if __name__ == "__main__":
    main()
