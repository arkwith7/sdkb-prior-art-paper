"""DART 정기보고서 수집 — H2 의 **외부 준거** (PLAN-009 §3-3).

**왜 특허 밖의 원천이 필요한가.** H2 는 "개념 시계열이 코드 시계열보다 빠른가"를 묻는데, 두 팔
모두 같은 특허 말뭉치에서 나온다. 어느 쪽이 빨라도 그것이 **현실의 부상**과 맞는지는 말뭉치
안에서 알 수 없다 — 특허로 특허를 검증할 수는 없다.

**왜 하필 공시인가.** 사업보고서는 **제출 시점의 기록이고 소급 수정되지 않는다.** 특허 분류를
무너뜨린 결함(H10 스킴의 소급 재분류 · PLAN-007)이 여기에는 없다. 2014년 보고서에 HBM 이
적혀 있으면 하이닉스는 2014년에 HBM 을 말하고 있었던 것이고, 그 사실은 나중에 바뀌지 않는다.

**매출은 준거가 못 된다** (실측): 최고 해상도가 삼성 "메모리" 한 줄 · 하이닉스 "DRAM, NAND
Flash 등" 한 줄이다. HBM 매출 항목이 **없다.** 그래서 준거는 **본문 언급**으로 잡는다.

준거 신호 규칙은 **시계열을 보기 전에 동결**됐다 (`mappings/dart_terms.csv`):
  기술 T 의 준거 연도 = 그 용어가 **연 1회 이상** 등장하는 **최초 연도** (원제출본만)

검정력을 미리 밝힌다: 준거로 쓸 수 있는 사례는 **4건**(HBM·3D NAND·TSV·GAA)이라 부호검정의
최소 p 는 0.0625 다 — **α=0.05 에 도달할 수 없다.** 따라서 이것은 검정이 아니라 **서술적
타당성 점검**이다. 결과를 본 뒤 사례를 늘려 유의성을 만들지 않는다 (CLAUDE.md §1.2).
"""
from __future__ import annotations

import html
import io
import json
import re
import time
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

from sdkb_paper.config import DART_TERMS, DATA, get_secret

RAW_DART = DATA / "raw" / "dart"
DOCUMENTS = RAW_DART / "documents"
TERM_COUNTS = RAW_DART / "term_counts.parquet"

# 삼성전자 · SK하이닉스의 DART 고유번호 (OpenDART corpCode.xml)
CORPS = {"삼성전자": "00126380", "SK하이닉스": "00164779"}
YEARS = range(2010, 2026)
REPORT_NAME = re.compile(r"(사업보고서|반기보고서|분기보고서)")

# 정정공시는 **원제출본만** 센다 — 정정본은 나중에 쓰인 문서라 '그때의 기록'이 아니다.
AMENDMENT = re.compile(r"\[기재정정\]|\[첨부정정\]|정정")


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=60).read()  # noqa: S310


def list_reports(corp_code: str, year: int) -> list[tuple[str, str, str]]:
    """(접수번호, 보고서명, 접수일). 정기보고서(pblntf_ty=A)만."""
    key = get_secret("DART_API_KEY")
    url = (
        f"https://opendart.fss.or.kr/api/list.json?crtfc_key={key}&corp_code={corp_code}"
        f"&bgn_de={year}0101&end_de={year}1231&pblntf_ty=A&page_count=100"
    )
    data = json.loads(_get(url))
    if data.get("status") != "000":  # 해당 연도에 공시가 없으면 013 을 준다
        return []
    return [
        (r["rcept_no"], r["report_nm"].strip(), r["rcept_dt"])
        for r in data["list"]
        if REPORT_NAME.search(r["report_nm"]) and not AMENDMENT.search(r["report_nm"])
    ]


def document_text(rcept_no: str) -> str:
    """보고서 본문 전체(태그 제거). 한 번 받으면 캐시한다 — API 를 다시 때리지 않는다."""
    cached = DOCUMENTS / f"{rcept_no}.txt"
    if cached.exists():
        return cached.read_text(encoding="utf-8")

    key = get_secret("DART_API_KEY")
    raw = _get(f"https://opendart.fss.or.kr/api/document.xml?crtfc_key={key}&rcept_no={rcept_no}")
    text = ""
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for name in z.namelist():
            body = z.read(name).decode("utf-8", "replace")
            text += re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body)))

    DOCUMENTS.mkdir(parents=True, exist_ok=True)
    cached.write_text(text, encoding="utf-8")
    time.sleep(0.3)
    return text


def load_terms(path: Path = DART_TERMS) -> pd.DataFrame:
    return pd.read_csv(path)


def count_terms(text: str, terms: pd.DataFrame) -> dict[str, int]:
    return {
        row.tech: len(re.findall(row.pattern, text, re.IGNORECASE))
        for row in terms.itertuples()
    }


def build(out: Path = TERM_COUNTS) -> pd.DataFrame:
    """보고서 × 기술 → 언급 횟수. 결과는 raw 에 저장한다 (커밋하지 않는다)."""
    terms = load_terms()
    rows = []
    for firm, corp in CORPS.items():
        for year in YEARS:
            for rcept, name, rcept_dt in list_reports(corp, year):
                text = document_text(rcept)
                rows.append({
                    "firm": firm, "year": year, "rcept_no": rcept,
                    "report": name, "rcept_dt": rcept_dt, "chars": len(text),
                    **count_terms(text, terms),
                })
    df = pd.DataFrame(rows).sort_values(["firm", "rcept_dt"])
    RAW_DART.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    return df


def reference_years(counts: pd.DataFrame, terms: pd.DataFrame) -> pd.DataFrame:
    """**동결된 준거 규칙**: 기술 T 의 준거 연도 = 언급이 연 1회 이상인 **최초 연도**.

    회사별로 따로 낸다 — 하이닉스가 HBM 을 2014년에, 삼성이 2017년에 말한 **차이 자체**가
    준거의 타당성을 보여준다(하이닉스가 원조다). 합산하면 그 정보가 사라진다.
    """
    rows = []
    for row in terms.itertuples():
        by_year = counts.groupby(["firm", "year"])[row.tech].sum().reset_index()
        for firm in CORPS:
            hit = by_year[(by_year["firm"] == firm) & (by_year[row.tech] > 0)]
            rows.append({
                "tech": row.tech,
                "concept_iri": row.concept_iri,
                "is_reference": bool(row.is_reference),
                "firm": firm,
                "reference_year": int(hit["year"].min()) if len(hit) else None,
                "n_reports_with_mention": int(len(hit)),
            })
    return pd.DataFrame(rows)


def earliest_reference(counts: pd.DataFrame, terms: pd.DataFrame) -> dict[str, int]:
    """{개념 IRI: 두 회사 중 **더 이른** 준거 연도}. 산업이 그 기술을 말하기 시작한 해다."""
    ref = reference_years(counts, terms)
    ref = ref[ref["is_reference"] & ref["reference_year"].notna()]
    return {
        iri: int(sub["reference_year"].min())
        for iri, sub in ref.groupby("concept_iri")
    }
