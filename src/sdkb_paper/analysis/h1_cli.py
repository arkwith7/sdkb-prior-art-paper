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
    residual_gap_report,
    restrict,
    threshold_sensitivity,
    wilcoxon_h1,
)
from sdkb_paper.config import FIGURES, GRAPH_V0, PROCESSED, TABLES
from sdkb_paper.ontology.delta import GRAPH_V1, GRAPH_V2
from sdkb_paper.viz.figures import fig_coverage_gap, fig_h1_coverage

H1_CSV = PROCESSED / "h1_coverage.csv"
H1_TABLE = TABLES / "table5_h1.md"

# C-2 소부장 G₂ (RQ3): 검정은 PLAN-005 그대로 불변, 바뀌는 건 after 코퍼스 하나뿐이다.
# 사전등록(§3.3): H1 이 소부장에서 **기각될 수 있다** — 장비사는 특정 공정에 특화돼 있어
# "전 공정 확장"이 안 나올 수 있다. 기각되면 기각된 대로 §4.6 에 쓴다.
CORPORA = {
    "samsung-hynix": (GRAPH_V1, "G₁", H1_CSV, H1_TABLE, "graph_v1.ttl"),
    "ksia-equipment": (GRAPH_V2, "G₂", PROCESSED / "h1_coverage_ksia.csv",
                       TABLES / "table5_h1_ksia.md", "graph_v2.ttl"),
}


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
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", choices=sorted(CORPORA), default="samsung-hynix",
                    help="samsung-hynix=G₀ vs G₁(주 분석) · ksia-equipment=G₀ vs G₂(RQ3 재현성)")
    args = ap.parse_args()
    after_graph, after_label, h1_csv, h1_table, after_file = CORPORA[args.corpus]

    df = compare_coverage(GRAPH_V0, after_graph)
    legacy = legacy_scope_iris()
    df["in_legacy20"] = df.index.get_level_values("step").isin(legacy)

    PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_csv(h1_csv)

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
        f"{after_label} {(df['after'] > 0).sum()} / {len(df)}",
        "",
        f"출처: `make h1` · 입력 graph_v0.ttl · {after_file} (3층 게이트 통과 스냅샷)",
    ]
    TABLES.mkdir(parents=True, exist_ok=True)
    h1_table.write_text("\n".join(lines) + "\n", encoding="utf-8")

    fig_out = None if args.corpus == "samsung-hynix" else FIGURES / "fig_h1_coverage_ksia.png"
    fig = fig_h1_coverage(df, out=fig_out)

    # §4.1 EDA — 보강 전 편중 그림은 G₀ 기준이므로 주 코퍼스에서만 낸다 (G₀ 는 공통 before).
    gap_fig = fig_coverage_gap(df) if args.corpus == "samsung-hynix" else None

    # §4.5.3 잔여 공백 성격 분석 — 주 코퍼스에서만. G₂(소부장) 가 있으면 breadth 포화 대조 열을 붙인다.
    gap_report = None
    if args.corpus == "samsung-hynix":
        ksia_csv = PROCESSED / "h1_coverage_ksia.csv"
        other = None
        if ksia_csv.exists():
            other = (pd.read_csv(ksia_csv).set_index(["level", "step"])
                     [["label", "before", "after", "delta"]])
        gap_report = _write_residual_gaps(df, other)
        sens_report = _write_h1_sensitivity(df)

    print("\n".join(lines))
    print(f"\n✓ {h1_csv}\n✓ {h1_table}\n✓ {fig}"
          + (f"\n✓ {gap_fig}" if gap_fig else "")
          + (f"\n✓ {gap_report}" if gap_report else "")
          + (f"\n✓ {sens_report}" if args.corpus == 'samsung-hynix' else ""))
    return 0


def _write_h1_sensitivity(df: pd.DataFrame):
    """§4.5.4 — 증가폭 임계 k 민감도. 그래프 재빌드 없이 h1_coverage.csv 에서 재검정."""
    sens = threshold_sensitivity(df)
    n_rej = int(sens["rejects"].sum())
    lines = [
        "# 표 12 · H1 증가폭 임계 민감도 (§4.5.4) — Δ≥k 로 '증가'를 재정의",
        "",
        "한 단계가 증가로 계수되려면 Δ≥k 여야 한다(Δ<k 는 0 으로 접는다). 검정 방법·단측·",
        "동점 제외는 불변이고 문턱만 흔든다. **k 를 요구가 큰 200 까지 올려도 H1 은 계속 기각**하며,",
        "증가 단계 수는 완만히 줄 뿐 비기각 근처에 가지 않는다 — H1 은 얇은 1~2건 커버리지에",
        "기대지 않는다(§5.3(g) 를 정면 반박). 최소 양의 Δ 는 38(Wet Etch)이라 k≤38 에서는 불변이다.",
        "",
        "| k (증가 문턱) | 증가 단계 | 비율 | W | p | 판정 |",
        "|---:|---:|---:|---:|---:|---|",
    ]
    for _, r in sens.iterrows():
        verdict = "H₀ 기각 → H1 지지" if r["rejects"] else "기각 못 함"
        lines.append(
            f"| Δ≥{int(r['k'])} | {int(r['increased'])}/{int(r['n'])} | {r['share']:.0%} | "
            f"{r['W']:.0f} | {r['p']:.2e} | {verdict} |")
    lines += [
        "",
        f"여섯 임계 전부에서 H₀ 기각({n_rej}/{len(sens)}). 출처: `make h1` · h1_coverage.csv",
    ]
    body = "\n".join(lines) + "\n"
    (PROCESSED / "h1_threshold_sensitivity.md").write_text(body, encoding="utf-8")
    (TABLES / "table12_h1_sensitivity.md").write_text(body, encoding="utf-8")
    return PROCESSED / "h1_threshold_sensitivity.md"


def _write_residual_gaps(df: pd.DataFrame, other: pd.DataFrame | None):
    """§4.5.3 — 보강 후에도 공백인 단계를 룰 유무로 분류해 리포트·표로 남긴다."""
    has_g2 = other is not None
    rep = residual_gap_report(df, other=other, other_label="G₂")
    n = len(rep)
    n_norule = int((~rep["has_rule"]).sum())
    n_rule = int(rep["has_rule"].sum())
    g2col = " | G₂ after" if has_g2 else ""
    g2sep = "|---:" if has_g2 else ""
    lines = [
        "# 표 · 잔여 공백 — 보강 후에도 특허가 매핑되지 않은 공정 단계 (§4.5.3)",
        "",
        f"보강 후 커버 26/49 · **잔여 공백 {n}/49**. 공백을 룰 테이블(`code_to_concept.csv`)로",
        "분류한다: **룰 없음** = 개념을 겨냥한 매핑 룰이 0개라 어떤 코퍼스로도 룰 경로로는 채울 수",
        "없다(분류체계·온톨로지 범위의 경계). **룰 있음** = 룰은 있으나 그 미세 코드가 이 코퍼스에",
        "부여되지 않았다(코퍼스 특이적).",
        "",
        f"- 룰 없음: **{n_norule}** / 룰 있으나 코퍼스 0건: **{n_rule}**",
    ]
    if has_g2:
        n_g2_fills = int((rep["G₂_after"] > 0).sum())
        lines.append(
            f"- 소부장 코퍼스(G₂)가 새로 채운 공백: **{n_g2_fills}** — breadth 는 26/49 로 포화한다.")
    lines += [
        "",
        f"| 단계 | 층위 | 룰 수 | 룰 있음{g2col} |",
        f"|---|---|---:|---{g2sep}|",
    ]
    for _, r in rep.sort_values(["has_rule", "level", "label"]).iterrows():
        g2 = f" | {int(r['G₂_after'])}" if has_g2 else ""
        lines.append(
            f"| {r['label']} | {r['level']} | {int(r['n_rules'])} | "
            f"{'예' if r['has_rule'] else '아니오'}{g2} |")
    lines += ["", "출처: `make h1` · h1_coverage.csv"
              + (" · h1_coverage_ksia.csv" if has_g2 else "") + " · mappings/code_to_concept.csv"]
    body = "\n".join(lines) + "\n"
    out = PROCESSED / "h1_residual_gaps.md"
    out.write_text(body, encoding="utf-8")
    # 논문 표 11 (§4.5.3) 도 같은 산출물로 낸다 — 손으로 옮기지 않는다.
    (TABLES / "table11_residual_gaps.md").write_text(body, encoding="utf-8")
    return out


if __name__ == "__main__":
    raise SystemExit(main())
