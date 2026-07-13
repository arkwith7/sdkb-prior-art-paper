"""`make h2` 의 진입점 — H2 검정과 §4.5 민감도를 한 번에 낸다 (PLAN-006).

산출: data/processed/h2_timeseries.csv · h2_leadtime.csv · h2_report.md (논문 표 6 · §4.4)

검정력의 한계를 미리 적어둔다: 유효쌍 7/7 이면 p = 0.0078 이지만, 동률·미탐지로 유효쌍이
4건 이하로 줄면 α=0.05 도달이 **불가능**해진다. 그 경우 그대로 "검정력 부족"으로 보고한다 —
임계값을 움직여 유의성을 만들지 않는다 (CLAUDE.md §1.2).
"""
from __future__ import annotations

import pandas as pd

from sdkb_paper.analysis.timeseries import (
    N_MIN,
    THETA,
    WINDOW_END,
    WINDOW_START,
    assign_concepts,
    code_series,
    concept_series,
    lead_times,
    load_cases,
    sign_test,
)
from sdkb_paper.config import PROCESSED
from sdkb_paper.preprocess.profile import DELTA as DELTA_PARQUET
from sdkb_paper.viz.figures import fig_h2_timeseries

TIMESERIES_CSV = PROCESSED / "h2_timeseries.csv"
LEADTIME_CSV = PROCESSED / "h2_leadtime.csv"
REPORT_MD = PROCESSED / "h2_report.md"

# §4.5 민감도 — 사전 정의 (PLAN-006). 결과를 보고 추가하지 않는다.
THETAS = (1.5, 2.0, 3.0)
N_MINS = (1, 3, 5)
VARIANTS = ("strict", "base", "loose")


def build_timeseries(df: pd.DataFrame, cases: pd.DataFrame) -> pd.DataFrame:
    """사례 × 연도 × (개념|코드) 롱 포맷. 그림 4 의 입력이다."""
    assigned = assign_concepts(df)
    rows = []
    for case in cases.itertuples():
        for kind, s in (
            ("concept", concept_series(df, case.concept_iri, assigned)),
            ("code", code_series(df, case.control_code)),
        ):
            for year, n in s.items():
                rows.append({"case_id": case.case_id, "kind": kind, "year": year, "n": int(n)})
    return pd.DataFrame(rows)


def sensitivity(df: pd.DataFrame, cases: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for variant in VARIANTS:
        for theta in THETAS:
            for n_min in N_MINS:
                r = sign_test(lead_times(df, cases, variant=variant, theta=theta, n_min=n_min))
                rows.append(
                    {
                        "variant": variant,
                        "theta": theta,
                        "n_min": n_min,
                        "n_pairs": r.n_pairs,
                        "concept_first": r.n_concept_first,
                        "code_first": r.n_code_first,
                        "p": r.p_value,
                        "rejects": r.rejects,
                    }
                )
    return pd.DataFrame(rows)


def _cell(v: object) -> str:
    if v is pd.NA or (isinstance(v, float) and pd.isna(v)):
        return "—"
    return f"{v:.4g}" if isinstance(v, float) else str(v)


def _md_table(df: pd.DataFrame) -> str:
    """의존성을 늘리지 않는다 (tabulate 미설치 · CLAUDE.md §3). h1_cli 와 같은 손수 렌더다."""
    head = "| " + " | ".join(df.columns) + " |"
    rule = "|" + "|".join("---" for _ in df.columns) + "|"
    body = [
        "| " + " | ".join(_cell(v) for v in row) + " |"
        for row in df.itertuples(index=False, name=None)
    ]
    return "\n".join([head, rule, *body])


def main() -> int:
    df = pd.read_parquet(DELTA_PARQUET)
    cases = load_cases()

    ts = build_timeseries(df, cases)
    leads = lead_times(df, cases)
    main_test = sign_test(leads)

    dropped = lead_times(df, cases, drop_control_code=True)
    dropped_test = sign_test(dropped)
    sens = sensitivity(df, cases)

    PROCESSED.mkdir(parents=True, exist_ok=True)
    ts.to_csv(TIMESERIES_CSV, index=False)
    leads.to_csv(LEADTIME_CSV, index=False)

    bidir = leads[~leads["subset_flag"]]
    bidir_test = sign_test(bidir)

    report = f"""# H2 — 개념 단위 시계열의 조기 탐지 (PLAN-006 · 논문 §4.4)

말뭉치: 수집 {len(df):,}건 전체 · 관측창 {WINDOW_START}–{WINDOW_END} (2024–2025 는 18개월 비공개 절단)
주 분석: variant=base · θ={THETA} · n_min={N_MIN} · 단측 정확 부호검정

## 표 6 — 사례별 탐지 연도와 시차 (L = 코드 − 개념, 양수 = 개념이 앞섬)

{_md_table(leads.drop(columns=["concept_iri"]))}

## 검정 (주 분석)

유효쌍 {main_test.n_pairs} (동률·양쪽미탐지 {main_test.n_excluded}건 제외) ·
개념 우선 {main_test.n_concept_first} · 코드 우선 {main_test.n_code_first} ·
**p = {main_test.p_value:.4g}** → {"H₀ 기각 → **H2 지지**" if main_test.rejects else "**기각 실패 — H2 미지지**"}

> 유효쌍이 4건 이하면 α=0.05 는 구조적으로 도달 불가능하다 (5건이라야 p=0.031).
> 그 경우 이 결과는 "검정력 부족"이지 "H2 기각"이 아니다.

## 두 가지 측정 결함 (결과와 함께 반드시 읽어야 한다)

**(1) 대조 코드 2건은 이 말뭉치에서 측정 불가다.** `H10D30/6735`(GAA)와 `H10W20/211`(TSV)은
CPC 스킴에서 중괄호로 표시된 **CPC 전용 코드**이고, 말뭉치는 KIPRIS 의 **IPC**(`ipc_number`)다.
CPC 전용 코드는 34,521건에서 출현 0회다 — 저 0 은 "코드가 신기술을 놓쳤다"가 아니라
"그 코드는 이 데이터의 분류체계에 존재할 수 없다"이다. **이 인공물은 H2 에 유리하게 작동한다**
(두 사례 모두 개념 승). 그런데도 주 분석은 기각에 실패했다.

**(2) PLAN-006 의 "개념 ⊇ 코드면 개념이 늦을 수 없다"는 전제는 틀렸다.** 탐지 규칙이 절대량이
아니라 **상대 성장**(θ × 직전 3년 평균)이므로, 상위집합은 기저가 커서 도약이 늦게 온다.
MRAM 이 반례다 — 개념이 코드를 포함하는데도 6년 늦게 탐지됐다(개념 시계열에 `G11C11/15·16`
자기메모리 회로가 들어와 2013년에 이미 연 56건이라 "부상"할 여지가 없었다).

양방향 사례(subset_flag=False)만의 검정: 유효쌍 {bidir_test.n_pairs} ·
개념 우선 {bidir_test.n_concept_first} · p = {bidir_test.p_value:.4g}
(사례 2건뿐이라 최선의 경우에도 p=0.25 — **검정이 아니라 기술(descriptive)이다**)

## §4.5 대조 코드 제거 재검정

개념 시계열에서 각 사례의 대조 코드를 제거하고 다시 검정한다 — 부분집합 관계가 결론을
만들지 않았음을 보이기 위해서다.

{_md_table(dropped.drop(columns=["concept_iri", "subset_flag"]))}

유효쌍 {dropped_test.n_pairs} · 개념 우선 {dropped_test.n_concept_first} ·
**p = {dropped_test.p_value:.4g}** → {"기각" if dropped_test.rejects else "기각 실패"}

## §4.5 민감도 (θ × n_min × 조합 정의)

{_md_table(sens)}
"""
    REPORT_MD.write_text(report, encoding="utf-8")
    fig = fig_h2_timeseries(ts, leads)

    print(_md_table(leads.drop(columns=["concept_iri"])))
    print(f"✓ {fig}")
    print(
        f"\n[H2] 유효쌍 {main_test.n_pairs} · 개념우선 {main_test.n_concept_first} · "
        f"코드우선 {main_test.n_code_first} · p = {main_test.p_value:.4g} · "
        f"{'H₀ 기각 → H2 지지' if main_test.rejects else '기각 실패 → H2 미지지'}"
    )
    print(f"✓ {TIMESERIES_CSV}\n✓ {LEADTIME_CSV}\n✓ {REPORT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
