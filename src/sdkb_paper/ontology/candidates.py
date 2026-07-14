"""3층 · 후보 발굴 — 1·2층에 넣을 후보를 코퍼스에서 뽑는다 (PLAN-004).

**발견은 자동, 채택은 사람이다.** 이 모듈은 후보 리포트만 만들고 어떤 링크도 그래프에 넣지
않는다. 자동 채택을 허용하면 우리 데이터 분포가 곧 정의가 되어, 조합 정의를 외부 근거로
동결한 의미가 사라진다 (CLAUDE.md §1.2).

두 신호를 본다:
  A. **코드 동시출현** — 이미 아는 신기술 개념(HBM·GAA)과 함께 나타나는데 룰이 없는 코드.
     "이 개념을 가진 특허는 왜 늘 이 코드를 달고 있는가"를 사람이 판단할 재료다.
  B. **최근 급증 코드** — 룰이 없으면서 최근 3년 출원이 급증한 코드. 신설 개념의 후보다.
     급증 자체가 채택 근거는 아니다 — 외부 원천으로 확인해야 한다.
"""
from __future__ import annotations

import pandas as pd

from sdkb_paper.config import PROCESSED
from sdkb_paper.ontology.emerging import (
    DEFAULT_VARIANT,
    emerging_devices,
    load_aliases,
    load_combinations,
)
from sdkb_paper.ontology.mapping import _norm_code, load_code_mapping, map_codes_to_concepts
from sdkb_paper.preprocess.profile import DELTA as DELTA_PARQUET

CANDIDATES_MD = PROCESSED / "candidates_report.md"
RECENT_FROM = 2022  # "최근" 의 정의. 절단 구간(2025~)은 아래에서 별도로 경고한다.


def _codes(row) -> list[str]:
    return [_norm_code(c) for c in row.ipc_codes if str(c).strip()]


def annotate(df: pd.DataFrame, variant: str = DEFAULT_VARIANT) -> pd.DataFrame:
    """특허별로 (매핑된 개념, 신기술 개념, 코드, 연도)를 붙인다."""
    table = load_code_mapping()
    aliases = load_aliases(variant=variant)
    combos = load_combinations(variant=variant)

    rows = []
    for row in df.itertuples():
        codes = _codes(row)
        text = f"{row.invention_title or ''} {row.abstract or ''}"
        hits = map_codes_to_concepts(codes, table)
        rows.append({
            "codes": codes,
            "year": row.application_date.year,
            "mapped": bool(hits["process"] or hits["device"]),
            "emerging": emerging_devices(codes, text, aliases, combos),
        })
    return pd.DataFrame(rows)


def cooccurring_unruled_codes(ann: pd.DataFrame, table: dict, top: int = 15) -> pd.DataFrame:
    """A. 신기술 개념과 함께 나타나는데 룰이 없는 코드."""
    ruled = set(table)
    rows = []
    for concept in sorted({c for cs in ann["emerging"] for c in cs}):
        sub = ann[ann["emerging"].apply(lambda cs, k=concept: k in cs)]
        counts: dict[str, int] = {}
        for codes in sub["codes"]:
            for c in codes:
                if not any(c.startswith(p) for p in ruled):
                    counts[c] = counts.get(c, 0) + 1
        for code, n in sorted(counts.items(), key=lambda kv: -kv[1])[:top]:
            rows.append({
                "concept": concept.rsplit("/", 1)[-1],
                "code": code,
                "n": n,
                "share": round(n / len(sub), 3) if len(sub) else 0.0,
            })
    return pd.DataFrame(rows, columns=["concept", "code", "n", "share"])


def surging_unruled_codes(ann: pd.DataFrame, table: dict, top: int = 20) -> pd.DataFrame:
    """B. 룰이 없으면서 최근 출원이 급증한 코드."""
    ruled = set(table)
    rows = []
    for r in ann.itertuples():
        for c in r.codes:
            if not any(c.startswith(p) for p in ruled):
                rows.append({"code": c, "year": r.year})
    if not rows:
        return pd.DataFrame(columns=["code", "recent", "earlier", "ratio"])

    long = pd.DataFrame(rows)
    recent = long[long["year"] >= RECENT_FROM].groupby("code").size()
    earlier = long[long["year"] < RECENT_FROM].groupby("code").size()
    out = pd.DataFrame({"recent": recent, "earlier": earlier}).fillna(0).astype(int)
    out = out[out["recent"] >= 20]
    out["ratio"] = (out["recent"] / out["earlier"].replace(0, 1)).round(2)
    return out.sort_values("ratio", ascending=False).head(top).reset_index()


def _md(df: pd.DataFrame) -> str:
    """DataFrame → 마크다운 표. pandas.to_markdown 은 tabulate 를 요구하므로 쓰지 않는다."""
    if df.empty:
        return "_(해당 없음)_"
    head = "| " + " | ".join(df.columns) + " |"
    sep = "|" + "|".join("---" for _ in df.columns) + "|"
    rows = ["| " + " | ".join(str(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join([head, sep, *rows])


def main() -> int:
    df = pd.read_parquet(DELTA_PARQUET)
    ann = annotate(df)
    table = load_code_mapping()

    n_emerging = (ann["emerging"].str.len() > 0).sum()
    lines = [
        "# 후보 리포트 (3층) — 발견은 자동, **채택은 사람**",
        "",
        f"델타 {len(df):,}건 중 신기술 개념이 붙은 특허 **{n_emerging:,}건**"
        f" (variant={DEFAULT_VARIANT}).",
        "",
        "여기의 어떤 행도 자동으로 룰이 되지 않는다. 외부 원천으로 확인한 것만",
        "`term_aliases.csv` / `emerging_concepts.csv` 에 손으로 추가하고 재동결한다.",
        "",
        "## A. 신기술 개념과 동시출현하는데 룰이 없는 코드",
        "",
        _md(cooccurring_unruled_codes(ann, table)),
        "",
        f"## B. 룰이 없으면서 최근({RECENT_FROM}~) 급증한 코드",
        "",
        "> 2025년은 18개월 비공개로 **절단**되어 있다 — 급증/급감 해석에 주의.",
        "",
        _md(surging_unruled_codes(ann, table)),
        "",
    ]
    PROCESSED.mkdir(parents=True, exist_ok=True)
    CANDIDATES_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\n✓ {CANDIDATES_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
