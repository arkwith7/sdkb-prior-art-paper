"""`make h1` 의 진입점 — H1 검정을 돌리고 논문 표 5 와 그림을 만든다.

입력은 게이트를 통과한 두 스냅샷(graph_v0 · graph_v1)이다. 그래프를 다시 만들지 않는다 —
검정이 그래프를 조립하기 시작하면 "검정할 때마다 before 가 달라지는" 사태가 열린다.

결정적이다: 난수 없음. 같은 그래프 → 같은 CSV.
"""
from __future__ import annotations

import pandas as pd

from sdkb_paper.analysis.coverage import (
    WilcoxonResult,
    compare_coverage,
    legacy_scope_iris,
    restrict,
    wilcoxon_h1,
)
from sdkb_paper.config import GRAPH_V0, PROCESSED, TABLES
from sdkb_paper.ontology.delta import GRAPH_V1
from sdkb_paper.viz.figures import fig_h1_coverage

H1_CSV = PROCESSED / "h1_coverage.csv"
H1_TABLE = TABLES / "table5_h1.md"


def _scopes(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """사전 확정된 표본 집합 (PLAN-005 §3). 결과를 본 뒤 추가하지 않는다."""
    legacy = legacy_scope_iris()
    return {
        "expanded49": df,                                   # 주 검정
        "legacy20": restrict(df, legacy),                   # 복원 편향을 뺀 병기 검정
        "process11": df.loc[["process"]],                   # 층위별 — 중첩 비독립성 강건성
        "subprocess38": df.loc[["subprocess"]],
    }


def _fmt(r: WilcoxonResult) -> str:
    p = "—" if r.p_value is None else f"{r.p_value:.2e}"
    w = "—" if r.statistic is None else f"{r.statistic:.1f}"
    verdict = "H₀ 기각 → H1 지지" if r.rejects_null else "기각 못 함"
    return (
        f"| {r.scope} | {r.n} | {r.n_positive} ({r.share_increased:.0%}) | {r.n_negative} | "
        f"{r.n_tied} | {r.median_delta:.1f} | {r.median_delta_positive:.1f} | {w} | {p} | {verdict} |"
    )


def main() -> int:
    df = compare_coverage(GRAPH_V0, GRAPH_V1)
    legacy = legacy_scope_iris()
    df["in_legacy20"] = df.index.get_level_values("step").isin(legacy)

    PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_csv(H1_CSV)

    results = [wilcoxon_h1(sub, scope) for scope, sub in _scopes(df).items()]

    lines = [
        "# 표 5 · H1 — 공정 단계별 개념 커버리지 증가 (Wilcoxon 부호순위, 단측)",
        "",
        "H₀: 비영 차이의 유사중앙값(C₁(s) − C₀(s)) ≤ 0 · H₁(= 논문의 H1): > 0 · α = 0.05.",
        "표본 단위는 공정 단계 s(특허가 아니다). 동점 쌍(Δ=0)은 zero_method=\"wilcox\" 로 제외되므로,",
        "동점이 과반인 집합에서는 **전 단계 중앙값이 0 인데도 검정이 기각**할 수 있다 — 둘 다 싣는다.",
        "",
        "효과크기로 rank-biserial r 을 싣지 않는다: 병합이 특허를 더하기만 하므로 Δ<0 이 구조적으로",
        "불가능하고 r 은 항상 +1 이다(설계의 귀결이지 관측이 아니다). 크기는 **증가 단계 비율**과",
        "**증가 단계의 중앙값 증가폭**으로 읽는다. §5.3 의 한계로 자인한다.",
        "",
        "| 표본 집합 | n | Δ>0 (비율) | Δ<0 | Δ=0 | 전체 중앙값 Δ | 증가 단계 중앙값 Δ | W | p | 판정 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        *(_fmt(r) for r in results),
        "",
        f"커버된 단계: G₀ {(df['before'] > 0).sum()} / {len(df)} → "
        f"G₁ {(df['after'] > 0).sum()} / {len(df)}",
        "",
        "출처: `make h1` · 입력 graph_v0.ttl · graph_v1.ttl (3층 게이트 통과 스냅샷)",
    ]
    TABLES.mkdir(parents=True, exist_ok=True)
    H1_TABLE.write_text("\n".join(lines) + "\n", encoding="utf-8")

    fig = fig_h1_coverage(df)

    print("\n".join(lines))
    print(f"\n✓ {H1_CSV}\n✓ {H1_TABLE}\n✓ {fig}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
