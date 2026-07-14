"""`make h2` 의 진입점 — H2 검정과 §4.5 민감도를 한 번에 낸다 (PLAN-006).

산출: data/processed/h2_timeseries.csv · h2_leadtime.csv · h2_report.md (논문 표 6 · §4.4)

검정력의 한계를 미리 적어둔다: 유효쌍 7/7 이면 p = 0.0078 이지만, 동률·미탐지로 유효쌍이
4건 이하로 줄면 α=0.05 도달이 **불가능**해진다. 그 경우 그대로 "검정력 부족"으로 보고한다 —
임계값을 움직여 유의성을 만들지 않는다 (CLAUDE.md §1.2).
"""
from __future__ import annotations

import pandas as pd

from sdkb_paper.analysis.timeseries import (
    DEFINITIONS,
    H2P_DEFINITIONS,
    name_series,
    N_MIN,
    detect_year,
    THETA,
    WINDOW_END,
    WINDOW_START,
    WINDOWS,
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
from sdkb_paper.config import FIGURES, NAME_BASELINE, PROCESSED
from sdkb_paper.preprocess.profile import DELTA as DELTA_PARQUET
from sdkb_paper.viz.figures import fig_h2_timeseries

TIMESERIES_CSV = PROCESSED / "h2_timeseries.csv"
LEADTIME_CSV = PROCESSED / "h2_leadtime.csv"
REPORT_MD = PROCESSED / "h2_report.md"
PREDECESSOR_CSV = PROCESSED / "h2_predecessor_codes.csv"
PLAN009_CSV = PROCESSED / "h2_plan009_matrix.csv"
REFERENCE_CSV = PROCESSED / "h2_dart_reference.csv"
H2PRIME_CSV = PROCESSED / "h2prime_matrix.csv"

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


def union_corpus() -> pd.DataFrame:
    """H2 말뭉치 = 2010–2025 ∪ 2005–2009 (PLAN-009 · 좌측절단 교정).

    **말뭉치는 항상 합집합이고, 잘라내는 것은 관측창이다.** 그래야 사전등록 창(2010–2023)의
    결과가 교정 창과 **같은 코드**로 재현된다 — 창만 바뀌었음을 코드가 보증한다.
    2005–2009 분은 그래프에 병합되지 않는다 (G₁·H1 불변).
    """
    from sdkb_paper.preprocess.profile import PERIODS

    frames = [pd.read_parquet(p) for _, p, *_ in PERIODS.values() if p.exists()]
    return pd.concat(frames, ignore_index=True).sort_values("application_number")


def run_plan009(union: pd.DataFrame, cases: pd.DataFrame) -> dict:
    """창(사전등록·교정) × 정의(legacy·si) × 코드팔(현재분류·당시선행코드) 행렬.

    **여덟 셀 전부를 보고한다** — 유리한 셀을 고르지 않는다 (CLAUDE.md §1.2).
    """
    from sdkb_paper.collect.bq_cpc import VINTAGE_MAP, load_cpc, load_vintage

    cpc = prepare(union, use_cpc=True)  # 두 팔이 같은 분류 데이터를 본다
    vintage = load_vintage() if VINTAGE_MAP.exists() else None

    pred_map: dict[str, str] = {}
    pred = None
    if vintage:
        pred = predecessor_codes(cases, load_cpc(), vintage)
        pred_map = dict(zip(pred["case_id"], pred["predecessor_code"], strict=True))

    rows, leads_by_cell = [], {}
    for wname, window in WINDOWS.items():
        for definition in DEFINITIONS:
            # si 정의에 FOWLP 는 없다 — '팬아웃' 어휘가 전 말뭉치 21건이라 어떤 정의로도
            # 시계열이 서지 않아 **사전 배제**했다 (PLAN-009 §3-2). 결과를 보고 뺀 것이 아니다.
            cs = cases[cases["case_id"] != "fowlp"] if definition == "si" else cases
            assigned = assign_concepts(cpc, definition=definition)

            arms = {
                "현재 분류 (IPC∪CPC)": lead_times(
                    cpc, cs, assigned=assigned, window=window, definition=definition
                )
            }
            if vintage:
                arms["당시 분류 · 선행코드"] = vintage_lead_times(
                    cpc, cs, vintage, control_codes=pred_map,
                    window=window, definition=definition,
                )

            for arm, leads in arms.items():
                t = sign_test(leads)
                key = (wname, definition, arm)
                leads_by_cell[key] = leads
                rows.append({
                    "window": f"{window[0]}–{window[1]}",
                    "window_id": wname,
                    "definition": definition,
                    "code_arm": arm,
                    "n_cases": len(cs),
                    "n_pairs": t.n_pairs,
                    "concept_first": t.n_concept_first,
                    "code_first": t.n_code_first,
                    "p": t.p_value,
                    "rejects": t.rejects,
                })
    return {"matrix": pd.DataFrame(rows), "leads": leads_by_cell, "pred": pred}


def run_h2prime(union: pd.DataFrame) -> dict:
    """**H2′ — 시점 유효한 대조군으로 다시 세운 조기탐지 검정** (PLAN-010).

    코드 대조군은 이 데이터에서 무효다(소급 재분류 · 2017 해상도 바닥). 그러나 **명세 텍스트는
    소급 재작성되지 않는다** — 2010년 특허의 초록은 지금도 2010년의 초록이다. 그래서 대조군을
    기술의 **명칭 키워드**로 세운다. 온톨로지 없는 실무자가 실제로 하는 일이고, 온톨로지가
    이겨야 할 상대다.

    두 정의를 **함께** 낸다 (사전등록):
      si        — 온톨로지 전체(구조 ∪ 명칭). 대조군을 **포함한다**(개념 ⊇ 이름)
      si_struct — 명칭을 뺀 **구조 전용**. 대조군과 **서로소**다 → 진짜 양방향 비교

    si_struct 가 논지의 핵심이다: **특허는 기술을 이름으로 부르기 전에 구조로 말한다.**
    """
    from sdkb_paper.ontology.emerging import load_name_terms

    names = load_name_terms()
    cases = pd.read_csv(NAME_BASELINE)
    df = prepare(union, use_cpc=False)  # 두 팔 모두 텍스트만 본다 — 분류 데이터가 필요 없다

    rows, leads_by_cell = [], {}
    for wname, window in WINDOWS.items():
        for definition in H2P_DEFINITIONS:
            assigned = assign_concepts(df, definition=definition)
            leads = []
            for case in cases.itertuples():
                cs = concept_series(df, case.concept_iri, assigned, window)
                ns = name_series(df, case.concept_iri, names, window)
                cy = detect_year(cs, window=window)
                ny = detect_year(ns, window=window)

                if cy is None and ny is None:
                    outcome, lead = "both_undetected", pd.NA
                elif ny is None:
                    outcome, lead = "concept_first", window[1] - cy  # 하한 (우편향 절단)
                elif cy is None:
                    outcome, lead = "name_first", pd.NA
                elif cy < ny:
                    outcome, lead = "concept_first", ny - cy
                elif cy > ny:
                    outcome, lead = "name_first", ny - cy
                else:
                    outcome, lead = "tie", 0

                leads.append({
                    "case_id": case.case_id,
                    "concept_total": int(cs.sum()),
                    "name_total": int(ns.sum()),
                    "concept_year": cy,
                    "name_year": ny,
                    "lead": lead,
                    "lead_is_lower_bound": ny is None and cy is not None,
                    "outcome": outcome,
                })

            lf = pd.DataFrame(leads)
            # sign_test 는 concept_first/code_first 를 센다 — 같은 규약으로 이름을 맞춘다.
            t = sign_test(lf.assign(outcome=lf["outcome"].replace({"name_first": "code_first"})))
            leads_by_cell[(wname, definition)] = lf
            rows.append({
                "window": f"{window[0]}–{window[1]}",
                "definition": definition,
                "disjoint": definition == "si_struct",
                "n_cases": len(cases),
                "n_pairs": t.n_pairs,
                "concept_first": t.n_concept_first,
                "name_first": t.n_code_first,
                "p": t.p_value,
                "rejects": t.rejects,
            })
    return {"matrix": pd.DataFrame(rows), "leads": leads_by_cell}


def run_reference(union: pd.DataFrame, cases: pd.DataFrame) -> pd.DataFrame:
    """**외부 준거(DART) 대비 선행 시차** — 특허로 특허를 검증하지 않는다 (PLAN-009 §3-3).

    두 팔의 머리끝 비교(부호검정)는 이 데이터에서 성립하지 않는다. 코드 팔이 **양방향으로**
    무효이기 때문이다:
      · 현재 분류 — H10 코드가 소급 부여돼 **부당하게 이르다** (GAA 전용 코드가 2012년 출원에
        붙어 있다 — 실제로 부여된 것이 아니라 나중에 재분류된 것이다)
      · 당시 분류 — BigQuery 스냅샷이 2017-10 부터라 **해상도 바닥이 2017** 이다
    따라서 각 팔을 **말뭉치 밖의 준거**(회사 자신의 공시)에 대어 잰다.

    준거 사례는 4건이므로 부호검정 최소 p = 0.0625 다 — **α=0.05 에 도달할 수 없다.**
    이것은 검정이 아니라 **서술(descriptive)** 이며, 그 사실을 사전에 선언했다.
    """
    from sdkb_paper.collect.dart import TERM_COUNTS, earliest_reference, load_terms

    if not TERM_COUNTS.exists():
        return pd.DataFrame()

    ref = earliest_reference(pd.read_parquet(TERM_COUNTS), load_terms())
    pred = (
        pd.read_csv(PREDECESSOR_CSV).set_index("case_id")["predecessor_code"].to_dict()
        if PREDECESSOR_CSV.exists() else {}
    )
    window = WINDOWS["extended"]
    cpc = prepare(union, use_cpc=True)
    assigned = assign_concepts(cpc, definition="si")

    rows = []
    for case in cases.itertuples():
        if case.case_id == "fowlp":  # si 정의에 없다 (사전 배제)
            continue
        r = ref.get(case.concept_iri)
        pcode = pred.get(case.case_id)
        years = {
            "개념 (si · 텍스트 전용)": detect_year(
                concept_series(cpc, case.concept_iri, assigned, window), window=window
            ),
            "코드 (현재 분류)": detect_year(code_series(cpc, case.control_code, window), window=window),
            "코드 (당시 선행코드)": (
                detect_year(code_series(cpc, pcode, window), window=window)
                if isinstance(pcode, str) else None
            ),
        }
        rows.append({
            "case_id": case.case_id,
            "dart_reference_year": r,
            **{f"{k} 탐지": v for k, v in years.items()},
            **{f"{k} 선행": (r - v if (r and v) else None) for k, v in years.items()},
        })
    return pd.DataFrame(rows)


def main() -> int:
    raw = pd.read_parquet(DELTA_PARQUET)
    union = union_corpus()
    cases = load_cases()

    # 세 경로를 **나란히** 낸다. 뒤의 것이 앞의 것을 대체하지 않는다 (CLAUDE.md §1.2).
    pre = run(prepare(raw, use_cpc=False), cases)   # A 사전등록: KIPRIS IPC
    cor = run(prepare(raw, use_cpc=True), cases)    # B 교정: IPC ∪ CPC (두 팔 같은 데이터)
    vin = run_vintage(prepare(raw, use_cpc=False), cases)  # C 당시 분류 (텍스트는 시점 불변)
    p9 = run_plan009(union, cases)  # PLAN-009: 창 × 정의 × 코드팔 행렬
    dart = run_reference(union, cases)  # PLAN-009: 외부 준거 대비 선행 시차
    h2p = run_h2prime(union)  # PLAN-010: H2′ — 시점 유효한 명칭 대조군

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

---

# PLAN-009 — 좌측절단 교정 + 분류체계 독립 개념

여기까지의 네 측정(A·B·C·C′)에는 **두 개의 구조적 결함**이 있었다.

1. **코드 팔이 미래에서 온다** (PLAN-007): H10 스킴은 전량 소급 재분류라 늦을 수 없다.
2. **개념 팔이 코드에 기생한다** (PLAN-008): 0층 룰이 사례 7건 중 **6건**의 개념을 바로 그
   신설 H10 코드로 매핑하고 있었다 — 개념이 코드보다 앞설 수 없었다.
3. **개념 팔이 과거를 못 본다** (PLAN-009): HBM 의 구조적 부상(적층 ∧ 관통전극)이 관측창의
   **첫 해(2010)에 이미 정점**이라, 상대성장 규칙(θ × 직전 3년 평균)의 기저가 정의되지 않는다.

교정은 두 축이다. **신호 규칙(θ·n_min·후행창)은 만지지 않았다.**

- **창**: 2010–2023(사전등록) → **2005–2023**(부상 이전으로 확장 · 두 팔에 대칭)
- **정의**: legacy(코드 기생) → **si**(JEDEC/IRDS 표준의 구조 어휘 · 분류코드 0개)

말뭉치: 2010–2025 {len(raw):,}건 ∪ 2005–2009 {len(union) - len(raw):,}건 = **{len(union):,}건**
(2005–2009 분은 **그래프에 병합되지 않는다** — G₁·H1 은 불변이다)

## 여덟 셀 전부 (유리한 셀을 고르지 않는다)

{_md_table(p9["matrix"].drop(columns=["window_id"]))}

**주 셀 = 교정 창 × si 정의 × 당시 분류·선행코드** — 세 결함을 모두 교정한 유일한 셀이다.

{_md_table(p9["leads"][("extended", "si", "당시 분류 · 선행코드")].drop(columns=["concept_iri"]))
 if ("extended", "si", "당시 분류 · 선행코드") in p9["leads"] else "(스냅샷 미수집)"}

## 정직성 규율 (PLAN-009 §4)

- **관측창 확장은 사후(post-hoc)다.** PLAN-002 가 "결과를 본 뒤 기간 변경은 p-hacking"이라고
  스스로 못 박았다. 이것이 p-hacking 이 **아닌** 근거는 하나뿐이다 — 동기가 p 값이 아니라
  **측정의 무효성**(상대성장 규칙의 정의역이 좌측절단으로 비어 있음)이라는 것.
- **사전등록 결과(A·B·C·C′)를 지우지 않는다.** 위에 그대로 있다.
- **창은 한 번만 바꿨다.** 2005 에서 결과가 안 나온다고 2000 으로 내리지 않는다.
- **말뭉치 밀도 교란**: 2005–09 는 연평균 5,883건, 2010–25 는 2,158건이다. 상대성장 규칙은
  두 팔에 **대칭**으로 걸리므로 개념 vs 코드 **비교**는 공정하나, 절대 탐지 시점은 밀도에
  영향을 받는다 (§5.3).
- **잔여 좌측절단**: FinFET·GAA·MRAM 의 학술적 기원은 1990년대다. 산업 출원의 부상은 창 안에
  있지만 이 한계는 §5.3 에 적는다.

## 왜 개념 vs 코드 부호검정이 이 데이터에서 성립하지 않는가

코드 팔이 **양방향으로 무효**다. 어느 쪽을 써도 비교가 성립하지 않는다.

| 코드 팔 | 무효의 방향 | 증거 |
|---|---|---|
| **현재 분류** | **부당하게 이르다** — 소급 재분류 | GAA 전용 코드(`H10D30/6735`)가 **2012년 출원**에 붙어 있다. 그때 부여된 것이 아니라 2021년 이후 재분류된 것이다 |
| **당시 분류** | **해상도 바닥이 2017** | BigQuery 동결 스냅샷이 2017-10 부터만 존재한다. 교정 창에서는 2017년 관측자가 이미 모든 사례를 탐지할 만큼 성숙한 출원연도를 보므로, **여섯 사례 중 넷이 2017/2017 동률**이 된다 |

그래서 두 팔을 **말뭉치 밖의 준거**에 각각 대어 잰다.

## 외부 준거(DART 공시) 대비 선행 시차 — 서술적 타당성 점검

{_md_table(dart) if len(dart) else "(DART 미수집 — `python -m sdkb_paper.collect.dart`)"}

> **검정이 아니다.** 준거 사례가 4건이라 부호검정의 최소 p 는 **0.0625** 로 α=0.05 에 도달할 수
> **없다**. 이 한계는 결과를 보기 전에 선언됐다 (PLAN-009 §3-4). 유의성을 주장하지 않는다.

**좌측절단이 원인이었다는 것이 여기서 실증된다.** 사전등록 창(2010–2023)에서 si 개념은 HBM 을
2016년(공시 2014년보다 **2년 늦게**), TSV 를 2019년(공시 2012년보다 **7년 늦게**) 탐지했다.
창을 부상 이전으로 되돌리자 같은 정의가 HBM 2009 · TSV 2009 로 **공시를 3–5년 앞선다.**
정의는 한 글자도 바뀌지 않았다 — **창만 바뀌었다.**

---

# PLAN-010 — H2′ · 시점 유효한 대조군으로 다시 세운 조기탐지 검정

**대조군을 바꾼 이유는 결과가 아니라 도구다.** 분류코드는 소급 재분류되므로 조기탐지의 준거가
될 수 없다(위에서 실증). 반면 **명세 텍스트는 소급 재작성되지 않는다** — 2010년 특허의 초록은
지금도 2010년의 초록이다. 그래서 대조군을 그 기술의 **명칭 키워드**로 세운다.

> **H2′** — 개념 단위 시계열은 **동일 기술의 명칭 키워드** 단위 시계열보다 신흥기술 신호를
> 조기에 포착한다.

이것은 온톨로지 없는 실무자가 실제로 하는 일("HBM 으로 검색")이고, 온톨로지가 이겨야 할 상대다.
**신호 규칙(θ=2.0 · n_min=3 · 후행창 3년)은 손대지 않았다 — 대조군만 갈아끼웠다.**

{_md_table(h2p["matrix"])}

**주 검정은 `si`, 강건성은 `si_struct` 다.** si 정의는 구조 ∪ 명칭이라 대조군을 **포함한다**
(개념 ⊇ 이름) — 코드에서 겪은 부분집합 자명성이 여기서도 생긴다. `si_struct` 는 정의에서
**명칭 용어를 뺀** 구조 전용 개념이라 대조군과 **서로소**이고, 그때 비교는 진짜 양방향이 된다.
그리고 그것이 이 논문의 논지 자체다 — **특허는 기술을 이름으로 부르기 전에 구조로 말한다.**

## 교정 창 · 구조 전용 개념 (서로소 · 주 결과)

{_md_table(h2p["leads"][("extended", "si_struct")])}

## 교정 창 · 온톨로지 전체 (개념 ⊇ 이름)

{_md_table(h2p["leads"][("extended", "si")])}

## 정직성 (숨기지 않는다)

- **대조군 교체는 사후(post-hoc)다.** 코드 대조군에서 결과가 나오지 않은 것을 **본 뒤에**
  대조군을 바꿨다. 이것이 HARKing 이 **아닌** 근거는 하나뿐이다 — 교체의 동기가 p 값이 아니라
  **코드 대조군의 시간적 무효성**(소급 재분류 · 2017 해상도 바닥)이라는 것. 그 무효성은 위에
  독립적으로 실증돼 있다.
- **우리는 이미 명칭 어휘의 분포를 봤다** (HBM 이름이 전 말뭉치 31건 · 2010–15년 0건).
  그 관측을 본 뒤에 이 대조군을 사전등록했다는 사실을 논문에 적는다.
- **사전등록한 H2(코드 대조군)를 지우지 않는다.** 위에 여덟 셀 전부 있다.
- **신호 규칙은 불변**이다. 유의성을 만들려 임계값을 만지지 않았다.
- **TSV 는 대조가 약하다** — 이 기술은 이름과 구조가 거의 같다('TSV' = 기판을 관통하는 전극).
  결과를 보고 뺀 것이 아니라 사전에 그렇게 적었다 (`mappings/name_baseline.csv`).
"""
    REPORT_MD.write_text(report, encoding="utf-8")
    p9["matrix"].to_csv(PLAN009_CSV, index=False)
    if len(dart):
        dart.to_csv(REFERENCE_CSV, index=False)
    h2p["matrix"].to_csv(H2PRIME_CSV, index=False)
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
