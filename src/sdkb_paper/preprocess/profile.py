"""수집물 정제 + 데이터 프로파일 생성 (CLAUDE.md §4 의무).

원시 parquet → 정규화 → 출원인 정확일치 → 중복 제거 → G₀ 겹침 제거 → 룰 매핑
  → data/interim/patents_delta.parquet   (델타 후보 = 병합 대상)
  → data/profiles/kipris_samsung_hynix.md (구조·형태·기술통계·사용목적)

프로파일은 손으로 쓰지 않는다. 논문 표 4(수집 데이터 기술통계)의 원천이다.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from sdkb_paper.config import DATA, INTERIM, RAW_KIPRIS, ROOT
from sdkb_paper.ontology.mapping import load_code_mapping, map_codes_to_concepts
from sdkb_paper.preprocess.clean import (
    TARGET_APPLICANTS,
    drop_g0_overlap,
    dedup,
    filter_applicants,
    g0_application_numbers,
    normalize,
)

RAW = RAW_KIPRIS / "patents_raw.parquet"
DELTA = INTERIM / "patents_delta.parquet"
PROFILE = DATA / "profiles" / "kipris_samsung_hynix.md"

COLUMN_MEANING = {
    "application_number": ("출원번호 (하이픈 제거, 키)", "KIPRIS applicationNumber"),
    "applicant_name": ("출원인 명칭", "KIPRIS applicantName"),
    "application_date": ("출원일 — H2 시계열의 시간축", "KIPRIS applicationDate"),
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


def build(raw_path: Path = RAW) -> pd.DataFrame:
    raw = pd.read_parquet(raw_path)
    norm = normalize(raw)
    kept = filter_applicants(norm)
    uniq = dedup(kept)
    g0 = g0_application_numbers()
    delta, overlap = drop_g0_overlap(uniq, g0)
    delta = add_mapping(delta)

    INTERIM.mkdir(parents=True, exist_ok=True)
    delta.to_parquet(DELTA, index=False)

    PROFILE.parent.mkdir(parents=True, exist_ok=True)
    PROFILE.write_text(_render(raw, norm, kept, uniq, overlap, delta), encoding="utf-8")
    return delta


def _render(raw, norm, kept, uniq, overlap, delta) -> str:
    mapped = delta[(delta.n_process > 0) | (delta.n_device > 0)]
    by_app = delta.groupby("applicant_name").size()
    ov_app = overlap.groupby("applicant_name").size() if len(overlap) else pd.Series(dtype=int)
    years = delta["application_date"].dt.year

    s = ["# 프로파일 — KIPRIS 삼성전자·SK하이닉스 특허 (PLAN-002)\n",
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
             ("G₀ 겹침 제외", f"−{len(overlap):,}", "SIRP 거절특허로 이미 G₀ 에 있음 (H1 오염 방지)"),
             ("**델타 후보**", f"**{len(delta):,}**", "병합 대상"),
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
         _md_table([(a, f"{by_app.get(a, 0):,}", f"{ov_app.get(a, 0):,}") for a in TARGET_APPLICANTS],
                   ("출원인", "델타 건수", "G₀ 겹침(제외됨)")),
         f"\n### 출원연도 (범위 {years.min()}–{years.max()})\n\n",
         _md_table([(y, f"{n:,}", _trunc_flag(y, n, years))
                    for y, n in years.value_counts().sort_index().items()],
                   ("연도", "건수", "비고")),
         "\n> **최근 연도는 절단(truncation)되어 있다.** 특허는 출원 후 18개월이 지나야 공개되므로, "
         "최근 2년의 출원 건수는 아직 다 드러나지 않았다. **감소가 아니라 미공개다.** "
         "H2 의 시계열은 이 구간을 추세 판단에서 제외하거나 절단을 명시해야 한다 (§4.4·§4.5).\n",
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
         "| `application_date` | H2 시계열의 시간축 (§4.4). 공개일이 아니라 **출원일**이다 |\n"
         "| `ipc_codes` | 룰 매핑 → `realizesProcess`/`concernsDevice` 트리플 (§3.3) |\n"
         "| `invention_title`·`abstract` | 텍스트 매칭 경로 — **HBM·EUV/DUV 는 IPC 로 안 갈린다** (§3.3) |\n"
         "| `applicant_name` | §4.5 출원인별 강건성 재검정 |\n"
         "| `application_number` | G₀ 중복 제거의 키. 특허 IRI 생성 |\n"
         "| `register_date`·`register_status` | **이번 검정에는 쓰지 않는다.** 등록 여부는 H1·H2 의 "
         "관측 단위가 아니다. 후속 연구(등록/거절 대비)를 위해 남긴다 |\n"
         "| `query_applicant`·`query_ipc` | 출처 추적 — 어느 질의가 이 행을 가져왔는가 |\n",
         ]
    return "".join(s)


def main() -> int:
    delta = build()
    print(f"✓ 델타 후보 {len(delta):,}건 → {DELTA.relative_to(ROOT)}")
    print(f"✓ 프로파일 → {PROFILE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
