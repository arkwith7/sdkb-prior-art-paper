"""논문 그림은 전부 이 모듈이 생성한다 -> paper/figures/ (수작업 그림 금지)."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from sdkb_paper.config import FIGURES


def fig_coverage_delta(df: pd.DataFrame, out: Path | None = None) -> Path:
    """compare_coverage() 산출물 -> 보강 전/후 막대 그래프."""
    out = out or FIGURES / "fig_coverage_delta.png"
    ax = df[["before", "after"]].plot.barh(figsize=(8, max(3, 0.4 * len(df))))
    ax.set_xlabel("patents mapped")
    ax.set_ylabel("process step")
    plt.tight_layout()
    plt.savefig(out, dpi=200)
    plt.close()
    return out


def fig_h1_coverage(df: pd.DataFrame, out: Path | None = None) -> Path:
    """H1 그림 — 공정 단계별 커버리지 G₀ vs G₁.

    복원 이전 20개 단계(`in_legacy20`)를 레이블에 표시한다. 복원된 단계는 G₀ 에서 0 이라
    H1 에 유리하므로, 어느 막대가 그쪽인지 그림에서 바로 보여야 한다.
    """
    out = out or FIGURES / "fig_h1_coverage.png"
    plot = df.sort_values(["level", "delta"], ascending=[True, True]).copy()
    marker = plot["in_legacy20"].map({True: "", False: " *"}) if "in_legacy20" in plot else ""
    plot.index = plot["label"] + marker

    ax = plot[["before", "after"]].plot.barh(figsize=(9, max(4, 0.28 * len(plot))))
    ax.set_xscale("symlog")
    # 라벨은 영문이다 — matplotlib 기본 글꼴(DejaVu Sans)에 한글 글리프가 없어 두부(□)가 된다.
    ax.set_xlabel("mapped patents (symlog)   * = step restored from SemiKong Table 7")
    ax.set_ylabel("process step")
    ax.legend(["G₀ (before)", "G₁ (after)"])
    plt.tight_layout()
    FIGURES.mkdir(parents=True, exist_ok=True)
    plt.savefig(out, dpi=200)
    plt.close()
    return out


def fig_h2_timeseries(
    ts: pd.DataFrame, leads: pd.DataFrame, out: Path | None = None
) -> Path:
    """H2 그림 — 사례 7건의 개념 vs 코드 시계열 (소형 다중).

    개념 실선 · 코드 점선 · 탐지연도 마커. 관측창 밖(2024–2025)은 이 프레임에 없다 —
    18개월 비공개 절단이라 탐지 판정에서 제외했고, 그림도 같은 창을 쓴다 (PLAN-006).

    코드가 끝내 탐지되지 않은 사례는 마커가 없다. 그 공백이 관측값이다 —
    다만 GAA·TSV 의 0건은 **대조 코드가 CPC 전용**이라 IPC 말뭉치에 존재할 수 없는
    측정 인공물이다. 제목에 그렇게 적는다 (거짓 해석을 그림이 만들지 않도록).
    """
    out = out or FIGURES / "fig4_h2_timeseries.png"
    cases = list(leads["case_id"])
    fig, axes = plt.subplots(2, 4, figsize=(16, 7), sharex=True)

    for ax, case_id in zip(axes.flat, cases, strict=False):
        row = leads[leads["case_id"] == case_id].iloc[0]
        sub = ts[ts["case_id"] == case_id].pivot(index="year", columns="kind", values="n")
        ax.plot(sub.index, sub["concept"], "-", label="concept (ontology)")
        ax.plot(sub.index, sub["code"], "--", label="code (control CPC/IPC)")
        for kind, year in (("concept", row["concept_year"]), ("code", row["code_year"])):
            if pd.notna(year):
                ax.axvline(int(year), ls=":", lw=0.8)
                ax.plot(int(year), sub.loc[int(year), kind], "o", ms=6)
        zero = " — code absent (CPC-only)" if row["code_total"] == 0 else ""
        ax.set_title(f"{case_id} · {row['control_code']}{zero}", fontsize=9)
        ax.set_ylabel("filings")
    for ax in axes.flat[len(cases) :]:
        ax.axis("off")
    axes.flat[0].legend(fontsize=8)
    fig.suptitle("H2 — concept-unit vs code-unit filing series (2010–2023; 2024–25 truncated)")
    plt.tight_layout()
    FIGURES.mkdir(parents=True, exist_ok=True)
    plt.savefig(out, dpi=200)
    plt.close()
    return out


def main() -> None:
    print("figure generators ready — analysis 결과 DataFrame 을 넘겨 호출하세요")


if __name__ == "__main__":
    main()
