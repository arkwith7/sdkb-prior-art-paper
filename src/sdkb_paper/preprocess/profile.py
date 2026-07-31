"""수집물 정제 + 데이터 프로파일 생성 (CLAUDE.md §4 의무).

원시 parquet → 정규화 → 출원인 정확일치 → 중복 제거 → G₀ 겹침 제거 → 룰 매핑
  → data/interim/patents_delta.parquet   (델타 후보 = 병합 대상)
  → data/profiles/kipris_samsung_hynix.md (구조·형태·기술통계·사용목적)

프로파일은 손으로 쓰지 않는다. 논문 표 4(수집 데이터 기술통계)의 원천이다.
"""
from __future__ import annotations

import argparse

import pandas as pd

from sdkb_paper.config import DATA, INTERIM, RAW_KIPRIS, ROOT
from sdkb_paper.ontology.mapping import load_code_mapping, map_codes_to_concepts
from sdkb_paper.preprocess.clean import (
    TARGET_APPLICANTS,
    drop_g0_overlap,
    dedup,
    filter_and_tag_ksia,
    filter_applicants,
    g0_application_numbers,
    load_ksia_crosswalk,
    normalize,
)

RAW = RAW_KIPRIS / "patents_raw.parquet"
DELTA = INTERIM / "patents_delta.parquet"
PROFILE = DATA / "profiles" / "kipris_samsung_hynix.md"

KSIA_RAW = RAW_KIPRIS / "patents_ksia_equipment_raw.parquet"
KSIA_DELTA = INTERIM / "patents_ksia_equipment_delta.parquet"
KSIA_PROFILE = DATA / "profiles" / "kipris_ksia_equipment.md"

# PLAN-009 · 좌측절단 교정분 (2005–2009). **G₁ 에 병합되지 않는다** — S2(구 H2) 시계열 전용이다.
# 정제 규칙은 main 과 **동일**하다(정규화 → 정확일치 → dedup → G₀ 겹침 제거). 기간마다 규칙이
# 다르면 시계열의 앞뒤가 다른 자로 재어진다. G₀ 겹침은 104건(0.4%)이라 규칙을 바꿀 이유가 없다.
PERIODS = {
    "main": (RAW, DELTA, PROFILE, "KIPRIS 삼성전자·SK하이닉스 특허 (PLAN-002)", True),
    "extended": (
        RAW_KIPRIS / "patents_2005_2009.parquet",
        INTERIM / "patents_2005_2009.parquet",
        DATA / "profiles" / "kipris_2005_2009.md",
        "KIPRIS 삼성전자·SK하이닉스 특허 2005–2009 (PLAN-009 · S2(구 H2) 좌측절단 교정)",
        False,
    ),
}

COLUMN_MEANING = {
    "application_number": ("출원번호 (하이픈 제거, 키)", "KIPRIS applicationNumber"),
    "applicant_name": ("출원인 명칭", "KIPRIS applicantName"),
    "application_date": ("출원일 — S2(구 H2) 시계열의 시간축 · v0.9 에서는 시점유효 컷(F10)의 기준", "KIPRIS applicationDate"),
    "invention_title": ("발명의 명칭 — 텍스트 매칭(HBM·EUV) 입력", "KIPRIS inventionTitle"),
    "ipc_number": ("IPC 코드 원문 ('|' 구분)", "KIPRIS ipcNumber"),
    "ipc_codes": ("IPC 코드 리스트 — 룰 매핑 입력", "ipc_number 파생"),
    "abstract": ("요약 — 텍스트 매칭 입력", "KIPRIS astrtCont"),
    "open_date": ("공개일 (출원일과 혼동 금지)", "KIPRIS openDate"),
    "register_date": ("등록일 (결측 = 미등록)", "KIPRIS registerDate"),
    "register_status": ("등록 상태 (공개/등록/거절 등)", "KIPRIS registerStatus"),
    "query_applicant": ("이 행을 가져온 질의의 출원인", "수집기 부여"),
    "query_ipc": ("이 행을 가져온 질의의 IPC 클래스", "수집기 부여"),
    "n_process": ("매핑된 공정 개념 수", "룰 매핑 파생"),
    "n_device": ("매핑된 소자 개념 수", "룰 매핑 파생"),
}


def add_mapping(df: pd.DataFrame) -> pd.DataFrame:
    table = load_code_mapping()
    hits = df["ipc_codes"].apply(lambda cs: map_codes_to_concepts(list(cs), table))
    out = df.copy()
    out["n_process"] = hits.apply(lambda h: len(h["process"]))
    out["n_device"] = hits.apply(lambda h: len(h["device"]))
    return out


def _trunc_flag(year: int, n: int, years: pd.Series) -> str:
    """공개 지연으로 절단된 연도를 표시한다. 직전 연도의 절반 미만이면 절단으로 본다."""
    prev = (years == year - 1).sum()
    return "⚠ 미공개분 절단 추정" if prev and n < prev * 0.5 else ""


def _missing(col: pd.Series) -> float:
    """빈 문자열도 결측이다 — KIPRIS 는 미등록 특허의 registerDate 를 빈 태그로 준다."""
    if pd.api.types.is_datetime64_any_dtype(col):
        return float(col.isna().mean())
    return float((col.isna() | (col.astype(str).str.strip() == "")).mean())


def _md_table(rows: list[tuple], header: tuple) -> str:
    line = "| " + " | ".join(header) + " |\n"
    line += "|" + "|".join("---" for _ in header) + "|\n"
    for r in rows:
        line += "| " + " | ".join(str(x) for x in r) + " |\n"
    return line


def build(period: str = "main") -> pd.DataFrame:
    raw_path, delta_path, profile_path, title, merged = PERIODS[period]
    raw = pd.read_parquet(raw_path)
    norm = normalize(raw)
    kept = filter_applicants(norm)
    uniq = dedup(kept)
    g0 = g0_application_numbers()
    delta, overlap = drop_g0_overlap(uniq, g0)
    delta = add_mapping(delta)

    app_rows = [(a, f"{delta.groupby('applicant_name').size().get(a, 0):,}",
                 f"{(overlap.groupby('applicant_name').size().get(a, 0) if len(overlap) else 0):,}")
                for a in TARGET_APPLICANTS]

    INTERIM.mkdir(parents=True, exist_ok=True)
    delta.to_parquet(delta_path, index=False)

    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(
        _render(raw, norm, kept, uniq, overlap, delta, title, merged, app_rows,
                ("출원인", "델타 건수", "G₀ 겹침(제외됨)")), encoding="utf-8"
    )
    return delta


def build_ksia() -> pd.DataFrame:
    """C-2 소부장 G₂ (S3(구 RQ3) · v0.9 에서는 검색 후보 모집단). 삼성 경로와 **정제 규칙은 동일**하되 출원인 필터만 정규화-정확일치
    (filter_and_tag_ksia)로 교체하고, 중복 제거를 (출원번호 × 매칭회사)로 한다 — 공동출원 특허가
    두 KSIA 회원사 포트폴리오에 함께 속하는 것을 보존하기 위해서다."""
    cw = load_ksia_crosswalk()
    key_to_slug = dict(zip(cw["match_key"], cw["org_slug"]))
    slug_to_name = dict(zip(cw["org_slug"], cw["name_ko"]))

    raw = pd.read_parquet(KSIA_RAW)
    norm = normalize(raw)
    kept = filter_and_tag_ksia(norm, key_to_slug)
    uniq = kept.sort_values(["application_number", "matched_slug"]).drop_duplicates(
        subset=["application_number", "matched_slug"])
    g0 = g0_application_numbers()
    delta, overlap = drop_g0_overlap(uniq, g0)
    delta = add_mapping(delta)

    cnt = delta.groupby("matched_slug").size().sort_values(ascending=False)
    ov = overlap.groupby("matched_slug").size() if len(overlap) else pd.Series(dtype=int)
    app_rows = [(f"{slug_to_name.get(s, s)} (`{s}`)", f"{n:,}", f"{ov.get(s, 0):,}")
                for s, n in cnt.head(20).items()]

    INTERIM.mkdir(parents=True, exist_ok=True)
    delta.to_parquet(KSIA_DELTA, index=False)
    KSIA_PROFILE.parent.mkdir(parents=True, exist_ok=True)
    KSIA_PROFILE.write_text(
        _render(raw, norm, kept, uniq, overlap, delta,
                "KIPRIS KSIA 소부장 188사 특허 (S3(구 RQ3) · PLAN-014 C-2 · G₂ · 장비·재료·부분품)", True, app_rows,
                ("KSIA 회원사 (상위 20)", "델타 건수", "G₀ 겹침(제외됨)")), encoding="utf-8")
    return delta


def build_details_profile() -> "pd.DataFrame":
    """G₁ 삼성·SK하이닉스 상세(초록+전체청구항) 프로파일 (§G1 Phase A · CLAUDE.md §4 의무).

    서지 프로파일과 형태가 다르다 — 관측 단위가 청구항 리스트·초록이다. 이 데이터는 그래프에
    claimText/abstractText/claimCount 로 실체화되어 RQ2 선행기술조사 feature 대비의 원천이 된다.
    """
    from sdkb_paper.collect.collect import SH_DETAILS
    df = pd.read_parquet(SH_DETAILS)
    prof = DATA / "profiles" / "kipris_samsung_hynix_details.md"

    n = len(df)
    n_claim_bearing = int((df["claims"].apply(len) > 0).sum())
    n_abs = int((df["abstract"].astype(str).str.strip() != "").sum())
    claims_len = df["claims"].apply(len)
    # claim_count(KIPRIS) > 실제 적재 청구항 수 → 미적재 신호 (자기완결성 결함 탐지).
    undercount = int((df["claim_count"] > claims_len).sum())
    cc = df["claim_count"]

    prof.parent.mkdir(parents=True, exist_ok=True)
    prof.write_text("".join([
        "# 프로파일 — KIPRIS 삼성·SK하이닉스 상세 (초록+전체청구항 · §G1 Phase A · G₁ 선행기술 feature 축)\n",
        "> 이 파일은 `python -m sdkb_paper.preprocess.profile --corpus samsung-hynix --details` 이 생성한다. 손으로 고치지 않는다.\n",
        "\n## 1. 구조 (structure)\n\n",
        _md_table([
            ("application_number", "출원번호 (하이픈 제거, 키)", str(df["application_number"].dtype),
             "KIPRIS applicationNumber"),
            ("abstract", "초록 전문 → ont:abstractText", str(df["abstract"].dtype), "KIPRIS astrtCont"),
            ("claims", "청구항 전문 리스트 (번호순, 선두번호 보존)", "object(list[str])",
             "KIPRIS claim — 청구항당 1원소"),
            ("claim_count", "KIPRIS 신고 청구항 수 (>len(claims)면 미적재)", str(cc.dtype), "KIPRIS claimCount"),
        ], ("컬럼", "의미", "dtype", "원천")),
        "\n키: `application_number` (병합 24,179건 = build_delta 병합필터와 동일 집합). "
        "**초록·청구항 원문은 그래프(gitignore·로컬 전용)에만 실체화되고 재배포하지 않는다 (§1.3).**\n",
        "\n## 2. 형태 (shape)\n\n",
        _md_table([
            ("상세 수집 특허", f"{n:,}", "병합 특허 전량 (룰 OR 인식층 · 사용자 결정 2026-07-22)"),
            ("고유 출원번호", f"{df['application_number'].nunique():,}", "키 — 중복 0"),
            ("청구항 보유", f"{n_claim_bearing:,} ({n_claim_bearing/max(n,1):.1%})", "FTO 자기완결성"),
            ("초록 보유", f"{n_abs:,} ({n_abs/max(n,1):.1%})", "선행기술 텍스트 대비 입력"),
            ("**claimText 트리플(예상)**", f"**{int(claims_len.sum()):,}**", "청구항당 1트리플 (번호 보존)"),
            ("claim_count 미적재 특허", f"{undercount:,}", "KIPRIS claimCount > 실제 청구항 수 (정직 계상)"),
        ], ("항목", "값", "설명")),
        "\n## 3. 기술통계 (descriptive)\n\n",
        "### 특허당 청구항 수 (실제 적재 기준)\n\n",
        _md_table([
            ("count", f"{n:,}"), ("mean", f"{claims_len.mean():.1f}"),
            ("std", f"{claims_len.std():.1f}"), ("min", f"{int(claims_len.min())}"),
            ("median", f"{int(claims_len.median())}"), ("max", f"{int(claims_len.max())}"),
        ], ("통계", "값")),
        "\n### KIPRIS 신고 claim_count\n\n",
        _md_table([
            ("count", f"{n:,}"), ("mean", f"{cc.mean():.1f}"),
            ("median", f"{int(cc.median())}"), ("max", f"{int(cc.max())}"),
            ("합계", f"{int(cc.sum()):,}"),
        ], ("통계", "값")),
        "\n## 4. 사용 목적 (purpose)\n\n",
        "| 컬럼 | 논문에서 쓰이는 곳 |\n|---|---|\n"
        "| `claims` | `ont:claimText`(청구항당 1)·`ont:firstClaimText` → **claim-feature 분해**의 원천 "
        "(RQ2 선행기술조사 feature 대비 · §G1 Phase C `src_g1`) |\n"
        "| `abstract` | `ont:abstractText` — 선행기술 텍스트 대비·설명 |\n"
        "| `claim_count` | `ont:claimCount` — FTO 자기완결성 지표 (신고 대비 적재율) |\n"
        "| `application_number` | 특허 IRI 키 (`data:patent/kr_…`) — G₀→G₁ 주 대비축 |\n"
        "\n> **엣지 중립**: 이 데이터는 datatype 속성만 더한다 — `realizesProcess`·`concernsDevice` 엣지와 "
        "병합 특허 집합을 건드리지 않으므로 **S1(구 H1) 커버리지는 원리적으로 불변**이다 (회귀 테스트 "
        "`test_delta_details_are_edge_neutral`).\n",
    ]), encoding="utf-8")
    print(f"✓ 상세 프로파일 → {prof.relative_to(ROOT)}")
    return df


def _render(raw, norm, kept, uniq, overlap, delta, title, merged, app_rows, app_header) -> str:
    mapped = delta[(delta.n_process > 0) | (delta.n_device > 0)]
    years = delta["application_date"].dt.year

    s = [f"# 프로파일 — {title}\n",
         "> 이 파일은 `python -m sdkb_paper.preprocess.profile` 이 생성한다. 손으로 고치지 않는다.\n",
         "\n## 1. 구조 (structure)\n\n",
         _md_table(
             [(c, COLUMN_MEANING.get(c, ("—", "—"))[0], str(delta[c].dtype),
               COLUMN_MEANING.get(c, ("—", "—"))[1]) for c in delta.columns],
             ("컬럼", "의미", "dtype", "원천")),
         "\n키: `application_number` (하이픈 제거 후 고유). "
         "**CPC 는 KIPRIS 고급검색 응답에 없다 — IPC 만 수집된다.**\n",
         "\n## 2. 형태 (shape)\n\n",
         _md_table([
             ("원시 수집 행", f"{len(raw):,}", "IPC 클래스 × 출원인 질의의 합 (중복 포함)"),
             ("정규화 후", f"{len(norm):,}", "출원번호·출원일 결측 제거"),
             ("출원인 정확일치 후", f"{len(kept):,}", "계열사·타사 제외 (부분일치 부작용 제거)"),
             ("출원번호 중복 제거 후", f"{len(uniq):,}", "한 특허가 여러 IPC 클래스에 잡힌다"),
             ("G₀ 겹침 제외", f"−{len(overlap):,}", "SIRP 거절특허로 이미 G₀ 에 있음 (S1 오염 방지)"),
             ("**정제 후 특허**", f"**{len(delta):,}**",
              "G₁ 병합 대상" if merged else
              "**G₁ 에 병합되지 않는다** — S2 시계열 전용 (PLAN-009 §2). G₁ 과 S1 은 불변이다"),
             ("└ 룰 매핑됨", f"{len(mapped):,} ({len(mapped)/max(len(delta),1):.1%})",
              "개념 ≥1 — L1(델타) 통과 조건"),
             ("└ 미매핑", f"{len(delta)-len(mapped):,}", "룰의 한계로 탈락. 정직하게 보고한다"),
         ], ("단계", "건수", "설명")),
         f"\n결측률 (델타 {len(delta):,}건 기준). **빈 문자열도 결측으로 센다** — KIPRIS 는 "
         "미등록 특허의 `registerDate` 를 빈 태그로 준다.\n\n",
         _md_table([(c, f"{_missing(delta[c]):.1%}")
                    for c in ["application_date", "invention_title", "abstract",
                              "register_date", "register_status"]],
                   ("컬럼", "결측/빈값")),
         "\n## 3. 기술통계 (descriptive)\n\n",
         "### 출원인별\n\n",
         _md_table(app_rows, app_header),
         f"\n### 출원연도 (범위 {years.min()}–{years.max()})\n\n",
         _md_table([(y, f"{n:,}", _trunc_flag(y, n, years))
                    for y, n in years.value_counts().sort_index().items()],
                   ("연도", "건수", "비고")),
         # 우측 절단 경고는 최근 출원이 담긴 수집분에만 해당한다 (2005–2009 분은 전량 공개됐다).
         ("\n> **최근 연도는 절단(truncation)되어 있다.** 특허는 출원 후 18개월이 지나야 공개되므로, "
          "최근 2년의 출원 건수는 아직 다 드러나지 않았다. **감소가 아니라 미공개다.** "
          "S2 의 시계열은 이 구간을 추세 판단에서 제외하거나 절단을 명시해야 한다 (§4.4·§4.5).\n"
          if years.max() >= 2024 else
          "\n> **이 구간에 우측 절단은 없다** — 2005–2009 출원은 전량 공개됐다. 대신 **좌측**을 보라: "
          "2005년(관측창의 첫 해)은 직전 3년 후행창이 없으므로 상대성장 규칙의 기저가 정의되지 "
          "않는다. 탐지는 창시작+3년(2008)부터 가능하다 (PLAN-009 §3-1).\n"),
         "\n### IPC 클래스 상위 (질의 클래스 기준, 중복 계수)\n\n",
         _md_table([(c, f"{n:,}") for c, n in delta["query_ipc"].value_counts().head(10).items()],
                   ("IPC 클래스", "건수")),
         "\n### 개념 매핑\n\n",
         _md_table([
             ("공정 개념 ≥1", f"{(delta.n_process > 0).sum():,}"),
             ("소자 개념 ≥1", f"{(delta.n_device > 0).sum():,}"),
             ("둘 다 없음 (미매핑)", f"{((delta.n_process == 0) & (delta.n_device == 0)).sum():,}"),
         ], ("축", "건수")),
         "\n## 4. 사용 목적 (purpose)\n\n",
         "| 컬럼 | 논문에서 쓰이는 곳 |\n|---|---|\n"
         "| `application_date` | S2 시계열의 시간축(구 §4.4) · v0.9 에서는 시점유효 컷(F10)의 기준. 공개일이 아니라 **출원일**이다 |\n"
         "| `ipc_codes` | 룰 매핑 → `realizesProcess`/`concernsDevice` 트리플 (§3.3) |\n"
         "| `invention_title`·`abstract` | 텍스트 매칭 경로 — **HBM·EUV/DUV 는 IPC 로 안 갈린다** (§3.3) |\n"
         "| `applicant_name` | §4.5 출원인별 강건성 재검정 |\n"
         "| `application_number` | G₀ 중복 제거의 키. 특허 IRI 생성 |\n"
         "| `register_date`·`register_status` | **이번 검정에는 쓰지 않는다.** 등록 여부는 S1·S2 의 "
         "관측 단위가 아니다. 후속 연구(등록/거절 대비)를 위해 남긴다 |\n"
         "| `query_applicant`·`query_ipc` | 출처 추적 — 어느 질의가 이 행을 가져왔는가 |\n",
         ]
    return "".join(s)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", choices=["samsung-hynix", "ksia-equipment"], default="samsung-hynix",
                    help="samsung-hynix=G₁(PLAN-002) · ksia-equipment=G₂ 소부장(S3 · PLAN-014 C-2)")
    ap.add_argument("--period", choices=sorted(PERIODS), default="main",
                    help="main=2010–2025 (G₁ 의 원천) · extended=2005–2009 (PLAN-009 · S2 전용)")
    ap.add_argument("--details", action="store_true",
                    help="samsung-hynix 상세(초록+청구항) 프로파일 (§G1 Phase A)")
    args = ap.parse_args()

    if args.details:
        if args.corpus != "samsung-hynix":
            ap.error("--details 프로파일은 samsung-hynix 코퍼스에만 쓴다")
        build_details_profile()
        return 0

    if args.corpus == "ksia-equipment":
        delta = build_ksia()
        delta_path, profile_path = KSIA_DELTA, KSIA_PROFILE
    else:
        _, delta_path, profile_path, *_ = PERIODS[args.period]
        delta = build(args.period)
    print(f"✓ 정제 후 특허 {len(delta):,}건 → {delta_path.relative_to(ROOT)}")
    print(f"✓ 프로파일 → {profile_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
