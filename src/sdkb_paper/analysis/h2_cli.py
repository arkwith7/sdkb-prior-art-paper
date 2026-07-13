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
    predecessor_codes,
    prepare,
    sign_test,
    vintage_lead_times,
)
from sdkb_paper.config import FIGURES, PROCESSED
from sdkb_paper.preprocess.profile import DELTA as DELTA_PARQUET
from sdkb_paper.viz.figures import fig_h2_timeseries

TIMESERIES_CSV = PROCESSED / "h2_timeseries.csv"
LEADTIME_CSV = PROCESSED / "h2_leadtime.csv"
REPORT_MD = PROCESSED / "h2_report.md"
PREDECESSOR_CSV = PROCESSED / "h2_predecessor_codes.csv"

# §4.5 민감도 — 사전 정의 (PLAN-006). 결과를 보고 추가하지 않는다.
THETAS = (1.5, 2.0, 3.0)
N_MINS = (1, 3, 5)
VARIANTS = ("strict", "base", "loose")


def build_timeseries(df: pd.DataFrame, cases: pd.DataFrame, assigned: pd.Series) -> pd.DataFrame:
    """사례 × 연도 × (개념|코드) 롱 포맷. 그림 4 의 입력이다."""
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
        assigned = assign_concepts(df, variant=variant)  # θ·n_min 은 배정을 바꾸지 않는다
        for theta in THETAS:
            for n_min in N_MINS:
                r = sign_test(
                    lead_times(
                        df, cases, variant=variant, theta=theta, n_min=n_min, assigned=assigned
                    )
                )
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


def _verdict(t) -> str:
    return "H₀ 기각 → **H2 지지**" if t.rejects else "**기각 실패 — H2 미지지**"


def _vintage_rows(vin: dict) -> str:
    if not vin:
        return "| **C. 당시 분류** | — | — | — | — | — | 스냅샷 미수집 (`make cpc-vintage`) |"
    c, p = vin["test"], vin["pred_test"]
    return (
        f"| **C. 당시 분류** | 스냅샷 S(T) · 사전등록 대조코드 | {c.n_pairs} | {c.n_concept_first} | "
        f"{c.n_code_first} | {c.p_value:.4g} | {_verdict(c)} |\n"
        f"| **C′. 당시 분류 · 선행코드** | 스냅샷 S(T) · 2017-10 최빈 선행코드 | {p.n_pairs} | "
        f"{p.n_concept_first} | {p.n_code_first} | {p.p_value:.4g} | {_verdict(p)} |"
    )


def run(df: pd.DataFrame, cases: pd.DataFrame) -> dict:
    """한 분류 데이터(IPC 또는 IPC∪CPC) 위에서 검정 일습을 낸다."""
    base = assign_concepts(df)
    leads = lead_times(df, cases, assigned=base)
    dropped = lead_times(df, cases, drop_control_code=True)
    return {
        "ts": build_timeseries(df, cases, base),
        "leads": leads,
        "test": sign_test(leads),
        "dropped": dropped,
        "dropped_test": sign_test(dropped),
        "bidir_test": sign_test(leads[~leads["subset_flag"]]),
        "sens": sensitivity(df, cases),
    }


def run_vintage(raw: pd.DataFrame, cases: pd.DataFrame) -> dict:
    """C 경로 (PLAN-007) — 두 팔 모두 **당시 분류**로 잰다. 스냅샷이 없으면 건너뛴다."""
    from sdkb_paper.collect.bq_cpc import VINTAGE_MAP, load_cpc, load_vintage

    if not VINTAGE_MAP.exists():
        return {}

    vintage = load_vintage()
    leads = vintage_lead_times(raw, cases, vintage)

    # 선행 코드는 **우리가 고르지 않는다** — 2017-10 스냅샷의 최빈 코드다 (PLAN-007 §3-2).
    pred = predecessor_codes(cases, load_cpc(), vintage)
    pred.to_csv(PREDECESSOR_CSV, index=False)
    pred_map = dict(zip(pred["case_id"], pred["predecessor_code"], strict=True))
    pred_leads = vintage_lead_times(raw, cases, vintage, control_codes=pred_map)

    return {
        "leads": leads,
        "test": sign_test(leads),
        "pred": pred,
        "pred_leads": pred_leads,
        "pred_test": sign_test(pred_leads),
    }


def main() -> int:
    raw = pd.read_parquet(DELTA_PARQUET)
    cases = load_cases()

    # 세 경로를 **나란히** 낸다. 뒤의 것이 앞의 것을 대체하지 않는다 (CLAUDE.md §1.2).
    pre = run(prepare(raw, use_cpc=False), cases)   # A 사전등록: KIPRIS IPC
    cor = run(prepare(raw, use_cpc=True), cases)    # B 교정: IPC ∪ CPC (두 팔 같은 데이터)
    vin = run_vintage(prepare(raw, use_cpc=False), cases)  # C 당시 분류 (텍스트는 시점 불변)

    PROCESSED.mkdir(parents=True, exist_ok=True)
    pd.concat(
        [pre["ts"].assign(scheme="ipc"), cor["ts"].assign(scheme="ipc_cpc")]
    ).to_csv(TIMESERIES_CSV, index=False)
    pd.concat(
        [pre["leads"].assign(scheme="ipc"), cor["leads"].assign(scheme="ipc_cpc")]
    ).to_csv(LEADTIME_CSV, index=False)

    report = f"""# H2 — 개념 단위 시계열의 조기 탐지 (PLAN-006 · 논문 §4.4)

말뭉치: 수집 {len(raw):,}건 전체 · 관측창 {WINDOW_START}–{WINDOW_END} (2024–2025 는 18개월 비공개 절단)
주 분석: variant=base · θ={THETA} · n_min={N_MIN} · 단측 정확 부호검정

**두 개의 결과를 나란히 싣는다.**

| | 분류 데이터 | 유효쌍 | 개념 우선 | 코드 우선 | p | 판정 |
|---|---|---:|---:|---:|---:|---|
| **A. 사전등록** | KIPRIS IPC | {pre["test"].n_pairs} | {pre["test"].n_concept_first} | {pre["test"].n_code_first} | {pre["test"].p_value:.4g} | {_verdict(pre["test"])} |
| **B. 교정** | IPC ∪ CPC | {cor["test"].n_pairs} | {cor["test"].n_concept_first} | {cor["test"].n_code_first} | {cor["test"].p_value:.4g} | {_verdict(cor["test"])} |
{_vintage_rows(vin)}

**왜 두 개인가.** 사전등록한 대조 코드 7개 중 2개(`H10D30/6735` GAA · `H10W20/211` TSV)는 CPC
스킴에서 중괄호로 표시된 **CPC 전용 코드**인데, 말뭉치는 KIPRIS 의 **IPC** 다 — CPC 전용 코드는
34,521건에서 출현 0회다. A 의 "코드 미탐지"는 코드 단위 시계열의 실패가 아니라 **분류체계
불일치**이고, 방향은 **H2 에 유리**하다(두 사례 모두 개념 승). B 는 BigQuery
`patents-public-data` 에서 CPC 를 받아 **두 팔을 같은 분류 데이터 위에 올린** 교정이다
(관측창 2010–2023 의 CPC 커버리지 100%). 임계값은 건드리지 않았다 — 측정 도구를 고쳤을 뿐이다.
**결과를 본 뒤의 변경이므로 A 를 지우지 않는다.**

---

## A. 사전등록 (KIPRIS IPC · 커밋 `beacc35` 의 규칙 그대로)

{_md_table(pre["leads"].drop(columns=["concept_iri"]))}

유효쌍 {pre["test"].n_pairs} (동률·양쪽미탐지 {pre["test"].n_excluded}건 제외) ·
**p = {pre["test"].p_value:.4g}** → {_verdict(pre["test"])}

## B. 교정 — 두 팔 모두 IPC ∪ CPC

{_md_table(cor["leads"].drop(columns=["concept_iri"]))}

유효쌍 {cor["test"].n_pairs} (동률·양쪽미탐지 {cor["test"].n_excluded}건 제외) ·
**p = {cor["test"].p_value:.4g}** → {_verdict(cor["test"])}

> 유효쌍이 4건 이하면 α=0.05 는 구조적으로 도달 불가능하다 (5건이라야 p=0.031).
> 그 경우 이 결과는 "검정력 부족"이지 "H2 기각"이 아니다.

## C. 당시(vintage) 분류 — PLAN-007

**A·B 의 코드 팔은 미래에서 왔다.** H10 스킴은 전량 2021년 이후의 소급 재분류다 (2017-10 ·
2021-01 스냅샷의 H10 코드 = **0개** / 현재 = 588k 행). 특허청이 이미 과거로 돌아가 새 코드를
붙였으므로, 현재 스냅샷으로 만든 코드 시계열은 **구조적으로 늦을 수 없다**.

C 는 연도 T 의 관측자가 **그때의 스냅샷 S(T)** 로만 보는 재구성이다. 두 팔이 같은 스냅샷을 본다.

{_md_table(vin["leads"].drop(columns=["concept_iri"])) if vin else "(스냅샷 미수집)"}

> ⚠️ **이 결과는 동어반복에 가깝다 — 그렇게 읽어야 한다.** 대조 코드 7개가 전부 H10\* 이고
> 2022년 이전 스냅샷에 없으므로, 코드 팔이 그 이전에 탐지할 길은 **구조적으로 없다**. C 가
> H2 를 지지하더라도 그것이 말하는 바는 **"전용 코드가 신설되기 전에는 전용 코드가 신호를 줄 수
> 없고, 온톨로지는 이름·조합으로 표현할 수 있다"** 뿐이다. 이 범위를 넘는 주장을 하지 않는다.

### C′. 선행 코드 검정 (동어반복 우려의 실증적 점검 · PLAN-007 §3-2)

당시 관측자는 전용 코드가 없어도 **그때 있던 코드**로 이 기술을 찾았을 수 있다. 선행 코드는
우리가 고르지 않는다 — 지금 대조 코드를 달고 있는 특허들이 2017-10 스냅샷에서 실제로 달고 있던
**최빈 코드 1개**다(동률이면 문자열 오름차순).

{_md_table(vin["pred"]) if vin else ""}

{_md_table(vin["pred_leads"].drop(columns=["concept_iri", "subset_flag"])) if vin else ""}

## PLAN-006 의 전제 하나는 틀렸다 (숨기지 않는다)

"개념 ⊇ 코드면 개념이 늦을 수 없다"는 **거짓**이다. 탐지가 절대량이 아니라 **상대 성장**
(θ × 직전 3년 평균)이라, 상위집합은 기저가 커서 도약이 늦게 온다. MRAM 이 반례다 —
개념이 코드를 포함하는데도 늦게 탐지됐다(개념 시계열에 `G11C11/15·16` 자기메모리 **회로**가
들어와 2013년에 이미 연 56건이라 "부상"할 여지가 없었다).

양방향 사례(subset_flag=False)만: A p = {pre["bidir_test"].p_value:.4g} ·
B p = {cor["bidir_test"].p_value:.4g} (사례 2건뿐 — **검정이 아니라 기술(descriptive)이다**)

## §4.5 대조 코드 제거 재검정 (교정본 B 기준)

{_md_table(cor["dropped"].drop(columns=["concept_iri", "subset_flag"]))}

유효쌍 {cor["dropped_test"].n_pairs} · 개념 우선 {cor["dropped_test"].n_concept_first} ·
**p = {cor["dropped_test"].p_value:.4g}** → {"기각" if cor["dropped_test"].rejects else "기각 실패"}
(A 기준: p = {pre["dropped_test"].p_value:.4g})

## §4.5 민감도 (θ × n_min × 조합 정의 · 교정본 B)

{_md_table(cor["sens"])}

## §4.5 민감도 (사전등록 A)

{_md_table(pre["sens"])}
"""
    REPORT_MD.write_text(report, encoding="utf-8")
    fig = fig_h2_timeseries(cor["ts"], cor["leads"])
    fig_pre = fig_h2_timeseries(
        pre["ts"], pre["leads"], out=FIGURES / "fig4b_h2_timeseries_preregistered.png"
    )

    for label, r in (("A 사전등록 IPC", pre), ("B 교정 IPC∪CPC", cor)):
        t = r["test"]
        print(
            f"[H2 · {label}] 유효쌍 {t.n_pairs} · 개념우선 {t.n_concept_first} · "
            f"코드우선 {t.n_code_first} · p = {t.p_value:.4g} · "
            f"{'H₀ 기각 → H2 지지' if t.rejects else '기각 실패 → H2 미지지'}"
        )
    print(f"✓ {TIMESERIES_CSV}\n✓ {LEADTIME_CSV}\n✓ {REPORT_MD}\n✓ {fig}\n✓ {fig_pre}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
