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


def main() -> None:
    print("figure generators ready — analysis 결과 DataFrame 을 넘겨 호출하세요")


if __name__ == "__main__":
    main()
