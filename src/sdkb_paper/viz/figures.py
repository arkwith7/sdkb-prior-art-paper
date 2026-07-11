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


def main() -> None:
    print("figure generators ready — analysis 결과 DataFrame 을 넘겨 호출하세요")


if __name__ == "__main__":
    main()
