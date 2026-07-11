"""H1: 공정 단계별 특허 커버리지 — 보강 전/후 비교.

관측 단위는 SDKB 의 공정 계층 두 층위다:
  - process    (8개)  ont:Process     — 거친 단위. 검정 표본이 안정적이지만 공백 해상도가 낮다.
  - subprocess (12개) ont:SubProcess  — 세밀한 단위. 공백이 선명하게 드러난다.
두 층위를 같이 보고해야 "보강이 어디를 메웠는가"를 논증할 수 있다.

SDKB 는 rdfs:label 이 아니라 skos:prefLabel(en) / skos:altLabel(ko) 을 쓴다.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from rdflib import Graph

# 층위를 VALUES 로 명시 — RDFS 추론 없이 Process/SubProcess 를 각각 집계한다.
# (SubProcess ⊑ Process 라서 추론을 켜면 SubProcess 가 두 층위에 이중 계상된다.)
# OPTIONAL 이므로 특허 0건인 단계도 행으로 남는다 — 그 공백이 곧 H1 의 대상이다.
COVERAGE_SPARQL = """
PREFIX ont:  <https://w3id.org/sdkb/ont/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?level ?step ?stepLabel (COUNT(?patent) AS ?n)
WHERE {
  VALUES (?stepType ?level) { (ont:Process "process") (ont:SubProcess "subprocess") }
  ?step a ?stepType ; skos:prefLabel ?stepLabel .
  OPTIONAL { ?patent a ont:Patent ; ont:realizesProcess ?step . }
}
GROUP BY ?level ?step ?stepLabel
"""


def coverage_by_process_step(graph_path: Path) -> pd.DataFrame:
    """(level, step) 별 특허 수. 인덱스는 IRI — 레이블은 표시용 컬럼."""
    g = Graph().parse(graph_path)
    rows = [
        {"level": str(r.level), "step": str(r.step), "label": str(r.stepLabel), "patents": int(r.n)}
        for r in g.query(COVERAGE_SPARQL)
    ]
    return (
        pd.DataFrame(rows, columns=["level", "step", "label", "patents"])
        .set_index(["level", "step"])
        .sort_index()
    )


def compare_coverage(before: Path, after: Path) -> pd.DataFrame:
    """보강 전/후 커버리지 표 + 검정용 데이터.

    before 는 baseline(graph_v0, 특허 0건)이므로 모든 단계가 0 에서 출발한다.

    통계 검정은 **층위별로 따로** 한다 — SubProcess 는 Process 에 중첩되어 독립 관측이 아니다:
        from scipy.stats import wilcoxon
        sub = df.loc["subprocess"]
        wilcoxon(sub["after"], sub["before"], alternative="greater")
    """
    b, a = coverage_by_process_step(before), coverage_by_process_step(after)
    df = pd.DataFrame({
        "label": a["label"].combine_first(b["label"]),
        "before": b["patents"],
        "after": a["patents"],
    })
    df[["before", "after"]] = df[["before", "after"]].fillna(0).astype(int)
    df["delta"] = df["after"] - df["before"]
    return df.sort_values(["level", "delta"], ascending=[True, False])
