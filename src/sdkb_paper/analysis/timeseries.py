"""H2 — 개념 단위 시계열이 코드 단위 시계열보다 신흥기술을 조기 탐지하는가 (PLAN-006).

**신호 규칙·판정 규칙은 시계열을 보기 전에 동결됐다** (PLAN-006 · 커밋 `beacc35`).
이 모듈은 그 규칙을 그대로 계산할 뿐 임계값을 고르지 않는다 (CLAUDE.md §1.2).

말뭉치는 수집 **34,521건 전체**다. G₁ 병합분(24,179)만 쓰면 대조 코드만 달린 미매핑 특허가
빠져 **코드 측이 불리해진다** — 그것은 H2 에 유리한 편향이다. 개념 시계열은 G₁ 과 일치한다
(개념이 1개 이상 붙은 특허는 정의상 전부 병합됐다 — 통합 테스트로 고정).

관측창은 **2010–2023** 이다. 2024–2025 는 출원 후 18개월 비공개로 인한 **절단**이므로 탐지
판정에서 제외한다 (2024: 3,884 → 2025: 423 은 출원 감소가 아니다).
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from scipy.stats import binomtest

from sdkb_paper.config import H2_CASES
from sdkb_paper.ontology.emerging import (
    DEFAULT_VARIANT,
    emerging_devices,
    load_aliases,
    load_combinations,
)
from sdkb_paper.ontology.mapping import _norm_code, load_code_mapping

# 동결된 관측창과 신호 규칙 (PLAN-006). 결과를 보고 바꾸지 않는다.
WINDOW_START, WINDOW_END = 2010, 2023
SEARCH_START = 2013  # 직전 3년 후행창을 확보할 수 있는 첫 해
THETA = 2.0
N_MIN = 3
LOOKBACK = 3


def load_cases(path=H2_CASES) -> pd.DataFrame:
    return pd.read_csv(path)


# ── 시계열 ──────────────────────────────────────────────────────────────
def annual_counts(years: pd.Series) -> pd.Series:
    """연도 -> 건수. 관측창 전체를 0 으로 채운다 (빈 해가 빠지면 직전 3년 평균이 틀어진다)."""
    idx = range(WINDOW_START, WINDOW_END + 1)
    counts = years[(years >= WINDOW_START) & (years <= WINDOW_END)].value_counts()
    return pd.Series({y: int(counts.get(y, 0)) for y in idx}, name="n").sort_index()


def _patent_concepts(row, table, aliases, combos, exclude_code: str | None) -> set[str]:
    """특허 1건이 가리키는 개념(Process ∪ Device). delta.build_delta 와 같은 3층 규칙이다.

    exclude_code 는 §4.5 의 **대조 코드 제거 재검정**용이다 — 대조 코드를 개념 시계열에서
    빼도 결론이 서는지 본다. 부분집합 관계(개념 ⊇ 코드)가 결론을 만들지 않았음을 보이기 위해서.
    """
    codes = [c.strip() for c in row.ipc_codes if c.strip()]
    if exclude_code:
        drop = _norm_code(exclude_code)
        codes = [c for c in codes if not _norm_code(c).startswith(drop)]

    hits = _map(codes, table)
    text = f"{row.invention_title or ''} {row.abstract or ''}"
    hits |= set(emerging_devices(codes, text, aliases, combos))
    return hits


def _map(codes: list[str], table: dict[str, list[tuple[str, str]]]) -> set[str]:
    norm = [_norm_code(c) for c in codes]
    return {
        iri
        for prefix, pairs in table.items()
        for c in norm
        if c.startswith(prefix)
        for iri, _axis in pairs
    }


def assign_concepts(
    df: pd.DataFrame, variant: str = DEFAULT_VARIANT, exclude_code: str | None = None
) -> pd.Series:
    """특허별 개념 집합. **설정(variant · exclude_code)당 한 번만** 계산한다 —
    사례마다 34,521건을 다시 스캔하면 민감도 분석에서 같은 매칭을 수십 번 반복한다.
    """
    table = load_code_mapping()
    aliases = load_aliases(variant=variant)
    combos = load_combinations(variant=variant)
    return pd.Series(
        [_patent_concepts(row, table, aliases, combos, exclude_code) for row in df.itertuples()],
        index=df.index,
    )


def concept_series(df: pd.DataFrame, concept_iri: str, assigned: pd.Series) -> pd.Series:
    """개념 단위 연도별 출원 건수. 0층(룰) ∪ 1층(별칭) ∪ 2층(조합)."""
    hit = assigned.map(lambda s: concept_iri in s)
    return annual_counts(df.loc[hit, "application_date"].dt.year)


def code_series(df: pd.DataFrame, code: str) -> pd.Series:
    """코드 단위 연도별 출원 건수 — H2 의 대조군. 접두어 일치다 (하위 코드를 포함한다)."""
    prefix = _norm_code(code)
    years = [
        row.application_date.year
        for row in df.itertuples()
        if any(_norm_code(c).startswith(prefix) for c in row.ipc_codes)
    ]
    return annual_counts(pd.Series(years, dtype="int64"))


# ── 탐지 ────────────────────────────────────────────────────────────────
def detect_year(
    series: pd.Series, theta: float = THETA, n_min: int = N_MIN
) -> int | None:
    """최초 탐지 연도 = y(t) >= n_min **이고** y(t) >= theta * mean(y(t-3..t-1)) 인 최초의 t.

    직전 3년 평균이 0이면(무에서 출현) y(t) >= n_min 만으로 충족한다.
    어느 해도 만족하지 않으면 None — **"탐지되지 않음"** 이다. 임의의 큰 값으로 대체하지
    않는다 (우편향 절단으로 보고한다 · PLAN-006 의 사전 약속).
    """
    for t in range(SEARCH_START, WINDOW_END + 1):
        y = series.get(t, 0)
        if y < n_min:
            continue
        prior = [series.get(t - k, 0) for k in range(1, LOOKBACK + 1)]
        mean_prior = sum(prior) / LOOKBACK
        if mean_prior == 0 or y >= theta * mean_prior:
            return t
    return None


# ── 시차와 검정 ─────────────────────────────────────────────────────────
@dataclass(frozen=True)
class SignTest:
    """단측 정확 부호검정. 개념이 앞선 쌍의 수가 우연보다 많은가."""

    n_pairs: int       # 유효쌍 (동률·양쪽미탐지 제외)
    n_concept_first: int
    n_code_first: int
    n_excluded: int
    p_value: float

    @property
    def rejects(self) -> bool:
        return self.p_value < 0.05


def lead_times(
    df: pd.DataFrame,
    cases: pd.DataFrame,
    variant: str = DEFAULT_VARIANT,
    theta: float = THETA,
    n_min: int = N_MIN,
    drop_control_code: bool = False,
) -> pd.DataFrame:
    """사례별 탐지 연도와 시차 L = (코드 탐지연도) − (개념 탐지연도). 양수 = 개념이 앞섬.

    판정 규칙 (사전 · PLAN-006):
      양쪽 미탐지 → 정보 없는 쌍, 검정에서 제외 (표에는 남긴다)
      코드만 미탐지 → 개념 승 (우편향 절단: lead >= WINDOW_END − concept_year)
      개념만 미탐지 → 코드 승
      동률(같은 해) → 동점, 검정에서 제외
    """
    rows = []
    # 대조 코드 제거 재검정은 사례마다 빼는 코드가 다르므로 설정이 사례별이다.
    shared = None if drop_control_code else assign_concepts(df, variant=variant)
    for case in cases.itertuples():
        assigned = (
            assign_concepts(df, variant=variant, exclude_code=case.control_code)
            if drop_control_code
            else shared
        )
        cs = concept_series(df, case.concept_iri, assigned)
        ks = code_series(df, case.control_code)
        cy, ky = detect_year(cs, theta, n_min), detect_year(ks, theta, n_min)

        if cy is None and ky is None:
            outcome, lead = "both_undetected", pd.NA
        elif ky is None:
            outcome, lead = "concept_first", WINDOW_END - cy  # 하한 (우편향 절단)
        elif cy is None:
            outcome, lead = "code_first", pd.NA
        elif cy < ky:
            outcome, lead = "concept_first", ky - cy
        elif cy > ky:
            outcome, lead = "code_first", ky - cy
        else:
            outcome, lead = "tie", 0

        rows.append(
            {
                "case_id": case.case_id,
                "concept_iri": case.concept_iri,
                "control_code": case.control_code,
                "subset_flag": bool(case.subset_flag),
                "concept_total": int(cs.sum()),
                "code_total": int(ks.sum()),
                "concept_year": cy,
                "code_year": ky,
                "lead": lead,
                "lead_is_lower_bound": ky is None and cy is not None,
                "outcome": outcome,
            }
        )
    return pd.DataFrame(rows)


def sign_test(leads: pd.DataFrame) -> SignTest:
    """동률과 양쪽 미탐지는 제외한다 (H1 의 Wilcoxon 동점 처리와 같은 규약)."""
    effective = leads[leads["outcome"].isin(["concept_first", "code_first"])]
    n_first = int((effective["outcome"] == "concept_first").sum())
    n = len(effective)
    p = binomtest(n_first, n, 0.5, alternative="greater").pvalue if n else 1.0
    return SignTest(
        n_pairs=n,
        n_concept_first=n_first,
        n_code_first=n - n_first,
        n_excluded=len(leads) - n,
        p_value=float(p),
    )
