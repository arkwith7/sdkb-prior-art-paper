"""S2 (구 시계열 H2/RQ2) — 개념 단위 시계열이 코드 단위보다 신흥기술을 조기 탐지하는가 (PLAN-006).

v0.9: 공유 코어 시간분석의 2차 재사용 증거(C1). v0.9 확증 가설과 다른 개념 — RECONCILIATION-v09.md §1.

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
    load_name_terms,
    load_si_combinations,
    si_devices,
    strip_name_terms,
)
from sdkb_paper.ontology.emerging import _term_in
from sdkb_paper.ontology.mapping import _norm_code, load_code_mapping

# 동결된 관측창과 신호 규칙 (PLAN-006). 결과를 보고 바꾸지 않는다.
WINDOW_START, WINDOW_END = 2010, 2023
SEARCH_START = 2013  # 직전 3년 후행창을 확보할 수 있는 첫 해

# PLAN-009 · 좌측절단 교정. **신호 규칙(θ·n_min·후행창)은 만지지 않는다 — 창만 넓힌다.**
# 사전등록 창에서는 HBM 의 구조적 부상(적층 ∧ 관통전극)이 첫 해(2010)에 이미 정점이라
# 상대성장 규칙의 기저가 정의되지 않았다. 확장은 **두 팔에 대칭**이므로 설계상 한쪽에
# 유리할 수 없다. 두 창의 결과를 **나란히** 보고한다 (PLAN-009 §4).
WINDOWS = {"prereg": (2010, 2023), "extended": (2005, 2023)}
DEFAULT_WINDOW = WINDOWS["prereg"]

# 개념을 무엇으로 정의하는가 (PLAN-009 §3-2).
#   legacy — 0층 룰(분류코드) ∪ 1층 별칭 ∪ 2층 코드조합.  사전등록 경로. **코드에 기생한다.**
#   si     — 텍스트 구조 어휘만. 분류코드를 일절 보지 않는다.
DEFINITIONS = ("legacy", "si")

# H2′ (PLAN-010) — **시점 유효한 대조군**. 코드가 아니라 기술의 **명칭**으로 검색하기.
# 명세 텍스트는 소급 재작성되지 않으므로 이 대조군은 분류코드가 무효였던 이유를 피해 간다.
#   si        — 온톨로지 전체 (구조 ∪ 명칭). 명칭 대조군을 **포함한다**(개념 ⊇ 이름)
#   si_struct — 정의에서 **명칭 용어를 뺀** 구조 전용 개념. 대조군과 **서로소**다
# 주 검정은 si, 강건성은 si_struct 로 낸다 — 부분집합 자명성이 결론을 만들지 않았음을 보인다.
H2P_DEFINITIONS = ("si", "si_struct")
# C 경로(PLAN-007)의 **관측 시점** 하한. BigQuery 동결 스냅샷이 2017-10 부터 존재한다 —
# 그 이전의 분류 상태는 복원할 수 없으므로 "2016년에 이미 알 수 있었는가"는 묻지 않는다.
OBS_START = 2017
THETA = 2.0
N_MIN = 3
LOOKBACK = 3


def load_cases(path=H2_CASES) -> pd.DataFrame:
    return pd.read_csv(path)


# ── 분류 데이터 (사전등록 IPC · 교정 IPC∪CPC) ─────────────────────────────
def prepare(df: pd.DataFrame, use_cpc: bool) -> pd.DataFrame:
    """분석에 쓸 분류코드 컬럼 `codes` 를 만든다.

    use_cpc=False → **사전등록 그대로** (KIPRIS IPC 만). 이 경로를 지우지 않는다 — 교정본이
    사전등록 결과를 조용히 대체하는 것을 막기 위해서다 (CLAUDE.md §1.2).

    use_cpc=True → IPC ∪ CPC (BigQuery `patents-public-data`). 대조 코드 2개가 **CPC 전용**이라
    IPC 말뭉치에서 구조적으로 0건이었던 측정 결함을 고친다. 두 팔(개념·코드)이 **같은** 분류
    데이터를 쓴다 — 한쪽만 풍부해지면 비교가 공정하지 않다.
    관측창(2010–2023)의 CPC 커버리지는 100% 다 (결측 1,255건은 전부 절단 구간인 2024–25).
    """
    out = df.copy()
    if not use_cpc:
        out["codes"] = out["ipc_codes"].map(list)
        return out

    from sdkb_paper.collect.bq_cpc import load_cpc

    cpc = load_cpc()
    out["codes"] = [
        sorted({*row.ipc_codes, *cpc.get(row.application_number, [])})
        for row in out.itertuples()
    ]
    return out


# ── 시계열 ──────────────────────────────────────────────────────────────
def annual_counts(years: pd.Series, window: tuple[int, int] = DEFAULT_WINDOW) -> pd.Series:
    """연도 -> 건수. 관측창 전체를 0 으로 채운다 (빈 해가 빠지면 직전 3년 평균이 틀어진다).

    말뭉치는 항상 합집합(2005–2025)을 넘기고 **창이 잘라낸다** — 그래야 사전등록 창의
    결과가 교정 창과 같은 코드로 재현된다 (회귀 테스트로 고정).
    """
    lo, hi = window
    counts = years[(years >= lo) & (years <= hi)].value_counts()
    return pd.Series({y: int(counts.get(y, 0)) for y in range(lo, hi + 1)}, name="n").sort_index()


def _patent_concepts(row, table, aliases, combos, exclude_code: str | None,
                     definition: str = "legacy") -> set[str]:
    """특허 1건이 가리키는 개념(Process ∪ Device). delta.build_delta 와 같은 3층 규칙이다.

    exclude_code 는 §4.5 의 **대조 코드 제거 재검정**용이다 — 대조 코드를 개념 시계열에서
    빼도 결론이 서는지 본다. 부분집합 관계(개념 ⊇ 코드)가 결론을 만들지 않았음을 보이기 위해서.
    """
    text = f"{row.invention_title or ''} {row.abstract or ''}"
    if definition in ("si", "si_struct"):
        # **분류코드를 일절 보지 않는다** (PLAN-009). 0층 룰이 사례 7건 중 6건의 개념을 신설
        # H10 코드로 매핑하고 있었고, 그 코드는 소급 부여된다 — 개념이 코드보다 앞설 수 없었다.
        return set(si_devices(text, combos))

    codes = [c.strip() for c in row.codes if c.strip()]
    if exclude_code:
        drop = _norm_code(exclude_code)
        codes = [c for c in codes if not _norm_code(c).startswith(drop)]

    hits = _map(codes, table)
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


def _si_or_legacy_combos(definition: str, variant: str):
    """정의 축에 따라 조합 테이블을 고른다. si_struct 는 si 에서 명칭 용어를 뺀 것이다."""
    if definition == "si":
        return load_si_combinations(variant=variant)
    if definition == "si_struct":
        return strip_name_terms(load_si_combinations(variant=variant), load_name_terms())
    return load_combinations(variant=variant)


def name_series(
    df: pd.DataFrame, concept_iri: str, names: dict[str, list[str]],
    window: tuple[int, int] = DEFAULT_WINDOW,
) -> pd.Series:
    """**명칭 대조군** 시계열 (H2′) — 그 기술의 이름을 명세에 쓴 특허의 연도별 건수.

    온톨로지 없는 실무자가 하는 일이다: 'HBM' 으로 검색. 명세 텍스트는 소급 재작성되지
    않으므로 **시점 유효**하다 — 분류코드가 무효였던 바로 그 이유를 피해 간다.
    """
    terms = names.get(concept_iri, [])
    years = [
        row.application_date.year
        for row in df.itertuples()
        if any(_term_in(t, f"{row.invention_title or ''} {row.abstract or ''}".lower())
               for t in terms)
    ]
    return annual_counts(pd.Series(years, dtype="int64"), window)


def assign_concepts(
    df: pd.DataFrame,
    variant: str = DEFAULT_VARIANT,
    exclude_code: str | None = None,
    definition: str = "legacy",
) -> pd.Series:
    """특허별 개념 집합. **설정(variant · exclude_code)당 한 번만** 계산한다 —
    사례마다 34,521건을 다시 스캔하면 민감도 분석에서 같은 매칭을 수십 번 반복한다.
    """
    table = load_code_mapping()
    aliases = load_aliases(variant=variant)
    combos = _si_or_legacy_combos(definition, variant)
    return pd.Series(
        [
            _patent_concepts(row, table, aliases, combos, exclude_code, definition)
            for row in df.itertuples()
        ],
        index=df.index,
    )


def concept_series(
    df: pd.DataFrame, concept_iri: str, assigned: pd.Series,
    window: tuple[int, int] = DEFAULT_WINDOW,
) -> pd.Series:
    """개념 단위 연도별 출원 건수. legacy=0층∪1층∪2층 · si=텍스트 구조 어휘만."""
    hit = assigned.map(lambda s: concept_iri in s)
    return annual_counts(df.loc[hit, "application_date"].dt.year, window)


def code_series(
    df: pd.DataFrame, code: str, window: tuple[int, int] = DEFAULT_WINDOW
) -> pd.Series:
    """코드 단위 연도별 출원 건수 — H2 의 대조군. 접두어 일치다 (하위 코드를 포함한다)."""
    prefix = _norm_code(code)
    years = [
        row.application_date.year
        for row in df.itertuples()
        if any(_norm_code(c).startswith(prefix) for c in row.codes)
    ]
    return annual_counts(pd.Series(years, dtype="int64"), window)


# ── 탐지 ────────────────────────────────────────────────────────────────
def detect_year(
    series: pd.Series, theta: float = THETA, n_min: int = N_MIN,
    window: tuple[int, int] = DEFAULT_WINDOW,
) -> int | None:
    """최초 탐지 연도 = y(t) >= n_min **이고** y(t) >= theta * mean(y(t-3..t-1)) 인 최초의 t.

    직전 3년 평균이 0이면(무에서 출현) y(t) >= n_min 만으로 충족한다.
    어느 해도 만족하지 않으면 None — **"탐지되지 않음"** 이다. 임의의 큰 값으로 대체하지
    않는다 (우편향 절단으로 보고한다 · PLAN-006 의 사전 약속).
    """
    lo, hi = window
    for t in range(lo + LOOKBACK, hi + 1):  # 후행창을 확보할 수 있는 첫 해부터
        y = series.get(t, 0)
        if y < n_min:
            continue
        prior = [series.get(t - k, 0) for k in range(1, LOOKBACK + 1)]
        mean_prior = sum(prior) / LOOKBACK
        if mean_prior == 0 or y >= theta * mean_prior:
            return t
    return None


# ── 당시(vintage) 분류로 하는 탐지 — PLAN-007 ────────────────────────────
def vintage_detect_year(
    df: pd.DataFrame,
    hit_fn,
    vintage: dict[int, dict[str, list[str]]],
    theta: float = THETA,
    n_min: int = N_MIN,
    window: tuple[int, int] = DEFAULT_WINDOW,
) -> int | None:
    """**관측 시점** T — 그때의 분류체계로 이 기술을 처음 알아볼 수 있었던 해 (PLAN-007 §2).

    **관측 시점 T 와 출원연도 t 는 다르다.** 이것을 섞으면 측정이 무너진다:
    T 의 관측자는 t=T 의 출원을 **볼 수 없다**(출원 후 18개월 비공개). 신호 규칙을 y(T) 에
    걸면 언제나 0 이라 아무것도 탐지되지 않는다.

    그래서 관측자 T 는
      1. 스냅샷 S(T) 에 보이는 특허만 세고 (없는 특허 = 미공개 · 없는 코드 = 미신설),
      2. **성숙한 출원연도** t ≤ T − 2 에 대해서만 신호 규칙(θ · n_min)을 적용한다.
    어느 t 에서든 규칙이 걸리면 그 **관측 시점 T** 가 탐지 연도다 (t 가 아니다 — 관측자가
    실제로 알 수 있었던 해를 보고한다).

    관측 시점은 스냅샷이 실재하는 **2017–2023** 뿐이다. 그 이전은 스냅샷이 없어 재구성할 수
    없다 — 2016년 이전에 이미 탐지 가능했는지는 이 방법으로 말할 수 없고, 그 사실을 §5.3 에
    적는다. 따라서 C 의 탐지 연도는 **상한이 아니라 하한도 아닌, 관측 가능 구간 안의 값**이다.

    개념 팔과 코드 팔은 **같은 스냅샷**을 본다 — 한쪽만 미래 정보를 받으면 비교가 아니다.
    """
    from sdkb_paper.collect.bq_cpc import SNAPSHOT_FOR_YEAR

    lo, hi = window
    for obs in range(OBS_START, hi + 1):
        snap = vintage.get(SNAPSHOT_FOR_YEAR[obs], {})
        years = [
            row.application_date.year
            for row in df.itertuples()
            if row.application_number in snap and hit_fn(snap[row.application_number], row)
        ]
        s = annual_counts(pd.Series(years, dtype="int64"), window)
        for t in range(lo + LOOKBACK, obs - 1):  # 성숙한 출원연도만 (t <= obs-2)
            y = s.get(t, 0)
            if y < n_min:
                continue
            prior = [s.get(t - k, 0) for k in range(1, LOOKBACK + 1)]
            mean_prior = sum(prior) / LOOKBACK
            if mean_prior == 0 or y >= theta * mean_prior:
                return obs
    return None


def vintage_lead_times(
    df: pd.DataFrame,
    cases: pd.DataFrame,
    vintage: dict[int, dict[str, list[str]]],
    control_codes: dict[str, str] | None = None,
    variant: str = DEFAULT_VARIANT,
    window: tuple[int, int] = DEFAULT_WINDOW,
    definition: str = "legacy",
) -> pd.DataFrame:
    """C 경로 — 두 팔 모두 당시 분류(+ 텍스트) 위에서 잰다.

    control_codes 를 주면 대조 코드를 갈아끼운다 (PLAN-007 §3-2 의 **선행 코드 검정**).
    선행 코드는 우리가 고르지 않는다 — 2017-10 스냅샷의 최빈 코드로 결정적으로 뽑는다.
    """
    table = load_code_mapping()
    aliases = load_aliases(variant=variant)
    si_combos = load_si_combinations(variant=variant)
    combos = load_combinations(variant=variant)

    rows = []
    for case in cases.itertuples():
        ctrl = (control_codes or {}).get(case.case_id, case.control_code)
        prefix = _norm_code(ctrl)

        def concept_hit(codes, row, iri=case.concept_iri):
            text = f"{row.invention_title or ''} {row.abstract or ''}"
            if definition == "si":
                return iri in set(si_devices(text, si_combos))
            hits = _map(codes, table) | set(emerging_devices(codes, text, aliases, combos))
            return iri in hits

        def code_hit(codes, _row, prefix=prefix):
            return any(_norm_code(c).startswith(prefix) for c in codes)

        cy = vintage_detect_year(df, concept_hit, vintage, window=window)
        ky = vintage_detect_year(df, code_hit, vintage, window=window)

        if cy is None and ky is None:
            outcome, lead = "both_undetected", pd.NA
        elif ky is None:
            outcome, lead = "concept_first", window[1] - cy
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
                "control_code": ctrl,
                "subset_flag": bool(case.subset_flag),
                "concept_year": cy,
                "code_year": ky,
                "lead": lead,
                "lead_is_lower_bound": ky is None and cy is not None,
                "outcome": outcome,
            }
        )
    return pd.DataFrame(rows)


def predecessor_codes(
    cases: pd.DataFrame,
    current: dict[str, list[str]],
    vintage: dict[int, dict[str, list[str]]],
    snapshot: int = 201710,
) -> pd.DataFrame:
    """당시 관측자가 이 기술을 찾는 데 **실제로 썼을 코드** (PLAN-007 §3-2).

    우리가 고르지 않는다 — 지금 대조 코드를 달고 있는 특허들이 2017-10 스냅샷에서 실제로
    달고 있던 코드 중 **최빈 코드 1개**다(동률이면 코드 문자열 오름차순). 결정적 규칙이다.
    이것이 없으면 "전용 코드가 없던 시기에 전용 코드가 신호를 못 준다"는 동어반복만 남는다.
    """
    from collections import Counter

    old = vintage.get(snapshot, {})
    rows = []
    for case in cases.itertuples():
        prefix = _norm_code(case.control_code)
        bearers = [
            app
            for app, codes in current.items()
            if any(_norm_code(c).startswith(prefix) for c in codes)
        ]
        counter = Counter(
            _norm_code(c) for app in bearers if app in old for c in old[app]
        )
        best = min(counter.items(), key=lambda kv: (-kv[1], kv[0]))[0] if counter else None
        rows.append(
            {
                "case_id": case.case_id,
                "control_code": case.control_code,
                "predecessor_code": best,
                "n_bearers": len(bearers),
                "n_in_snapshot": sum(1 for a in bearers if a in old),
                "support": counter.get(best, 0) if best else 0,
            }
        )
    return pd.DataFrame(rows)


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
    assigned: pd.Series | None = None,
    window: tuple[int, int] = DEFAULT_WINDOW,
    definition: str = "legacy",
) -> pd.DataFrame:
    """사례별 탐지 연도와 시차 L = (코드 탐지연도) − (개념 탐지연도). 양수 = 개념이 앞섬.

    판정 규칙 (사전 · PLAN-006):
      양쪽 미탐지 → 정보 없는 쌍, 검정에서 제외 (표에는 남긴다)
      코드만 미탐지 → 개념 승 (우편향 절단: lead >= WINDOW_END − concept_year)
      개념만 미탐지 → 코드 승
      동률(같은 해) → 동점, 검정에서 제외
    """
    rows = []
    # 개념 배정은 variant 에만 의존한다 — θ·n_min 을 훑는 민감도에서 재계산하지 않도록
    # 호출자가 미리 계산해 넘길 수 있다. 대조 코드 제거 재검정만 사례별 배정이 필요하다.
    shared = (
        None
        if drop_control_code
        else (
            assigned
            if assigned is not None
            else assign_concepts(df, variant=variant, definition=definition)
        )
    )
    for case in cases.itertuples():
        case_assigned = (
            assign_concepts(
                df, variant=variant, exclude_code=case.control_code, definition=definition
            )
            if drop_control_code
            else shared
        )
        cs = concept_series(df, case.concept_iri, case_assigned, window)
        ks = code_series(df, case.control_code, window)
        cy = detect_year(cs, theta, n_min, window)
        ky = detect_year(ks, theta, n_min, window)

        if cy is None and ky is None:
            outcome, lead = "both_undetected", pd.NA
        elif ky is None:
            outcome, lead = "concept_first", window[1] - cy  # 하한 (우편향 절단)
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
