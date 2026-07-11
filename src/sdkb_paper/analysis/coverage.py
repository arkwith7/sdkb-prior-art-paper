"""H1: 공정 단계별 특허 커버리지 — 보강 전/후 비교."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from rdflib import Graph

COVERAGE_SPARQL = """
PREFIX sdkb: <https://w3id.org/sdkb#>
SELECT ?stepLabel (COUNT(?patent) AS ?n)
WHERE {
  ?patent a sdkb:Patent ; sdkb:appliesToProcessStep ?step .
  ?step rdfs:label ?stepLabel .
}
GROUP BY ?stepLabel
"""


def coverage_by_process_step(graph_path: Path) -> pd.Series:
    g = Graph().parse(graph_path)
    rows = {str(r.stepLabel): int(r.n) for r in g.query(COVERAGE_SPARQL)}
    return pd.Series(rows, name="patents").sort_index()


def compare_coverage(before: Path, after: Path) -> pd.DataFrame:
    """보강 전/후 커버리지 표 + 검정용 데이터.

    통계 검정 예: 공정 단계를 관측 단위로 한 paired 비교
        from scipy.stats import wilcoxon
        wilcoxon(df["after"] - df["before"])
    """
    df = pd.DataFrame({
        "before": coverage_by_process_step(before),
        "after": coverage_by_process_step(after),
    }).fillna(0).astype(int)
    df["delta"] = df["after"] - df["before"]
    return df
