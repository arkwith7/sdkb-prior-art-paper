"""H2: 개념 단위 출원 시계열 -> emerging technology 신호."""
from __future__ import annotations

import pandas as pd


def concept_filing_timeseries(patents: pd.DataFrame, concept_col: str = "concepts") -> pd.DataFrame:
    """특허 DF (application_date, concepts[list]) -> 개념 x 연도 출원 건수 매트릭스."""
    exploded = patents.explode(concept_col).dropna(subset=[concept_col])
    exploded["year"] = exploded["application_date"].dt.year
    return exploded.pivot_table(
        index=concept_col, columns="year", values="application_number",
        aggfunc="count", fill_value=0,
    )


def emerging_score(ts: pd.DataFrame, recent_years: int = 3) -> pd.Series:
    """단순 성장 신호 v0: 최근 N년 평균 / 전체 평균. 논문에서는 회귀 기울기,
    지수성장 적합 등으로 고도화하고 이 v0 를 베이스라인으로 사용."""
    recent = ts.iloc[:, -recent_years:].mean(axis=1)
    overall = ts.mean(axis=1).replace(0, pd.NA)
    return (recent / overall).fillna(0).sort_values(ascending=False)
