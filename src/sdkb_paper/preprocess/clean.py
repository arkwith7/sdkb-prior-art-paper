"""수집 원시 데이터 정규화 · 중복 제거 (PLAN-002).

세 단계다. 순서가 의미를 갖는다.

1. **정규화** — 출원번호 하이픈 제거, 출원일 파싱, IPC 코드 분해.
2. **출원인 정확일치 필터** — KIPRIS `applicant` 는 부분일치라 계열사(삼성디스플레이 등)가
   섞여 나온다. 수집기는 가져오기만 하고, 걸러내는 것은 여기다.
3. **G₀ 중복 제거** — G₀(현행 SDKB)에 SIRP 거절특허로 삼성·하이닉스 특허가 이미 들어 있다.
   이를 델타에 또 넣으면 **같은 특허가 H1 의 before 와 after 양쪽에 계수되어** 대응표본
   비교가 오염된다. 출원번호로 뺀다.
"""
from __future__ import annotations

import re

import pandas as pd
import rdflib

from sdkb_paper.config import GRAPH_V0, KSIA_CROSSWALK, ONT

TARGET_APPLICANTS = ("삼성전자주식회사", "에스케이하이닉스 주식회사")


def load_ksia_crosswalk() -> pd.DataFrame:
    """소부장 188사 사전동결 크로스워크 (KSIA명 → G₀ organization slug · match_key · company_type).

    company_type ∈ {equipment, material, component} 가 층별 H1(§4.6 · 표 5b)의 층화 키다.
    생성은 preprocess.ksia_crosswalk (`make crosswalk`) — 결정적·검토 가능한 산출.
    """
    return pd.read_csv(KSIA_CROSSWALK, dtype=str)

# 법인격 표기(㈜↔(주)·주식회사 …)와 문장부호·공백을 걷어낸 핵심 토큰. KSIA 명부와 KIPRIS
# applicantName 의 표기가 달라(㈜넥스틴 vs (주)넥스틴), 삼성용 문자열 정확일치로는 소부장이
# 전량 탈락한다(스모크 실측 2026-07-15). **이 함수가 정본이다** — 크로스워크의 match_key 도,
# 런타임 필터도 같은 함수를 써야 한다. 두 쪽이 갈리면 필터가 조용히 0행을 낸다.
_LEGAL_TOKENS = ("주식회사", "유한회사", "가부시끼가이샤")


def normalize_company_name(s: str) -> str:
    s = s.lower().replace("㈜", "").replace("(주)", "").replace("(유)", "")
    for t in _LEGAL_TOKENS:
        s = s.replace(t, "")
    return re.sub(r"[^0-9a-z가-힣]", "", s)


def _digits(s: pd.Series) -> pd.Series:
    return s.astype(str).str.replace(r"\D", "", regex=True)


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """출원번호·출원일·IPC 를 계약된 형태로 맞춘다."""
    out = df.copy()
    out["application_number"] = _digits(out["application_number"])
    out["application_date"] = pd.to_datetime(
        out["application_date"], format="%Y%m%d", errors="coerce"
    )
    out["ipc_codes"] = (
        out["ipc_number"].fillna("").apply(lambda s: [c.strip() for c in s.split("|") if c.strip()])
    )
    out = out[out["application_number"].str.len() > 0]
    return out.dropna(subset=["application_date"])


def filter_applicants(df: pd.DataFrame, names=TARGET_APPLICANTS) -> pd.DataFrame:
    """applicantName 정확일치. 계열사·공동출원 표기 변형은 버린다."""
    return df[df["applicant_name"].isin(names)]


def filter_and_tag_ksia(df: pd.DataFrame, key_to_slug: dict[str, str]) -> pd.DataFrame:
    """KSIA 코퍼스용 출원인 필터 + 태깅.

    KIPRIS `applicant` 부분일치는 짧은 이름에서 심하게 오염된다(질의 '디아이' → 삼성에스디아이
    921건 · 실측). 그래서 **정규화-정확일치**로 거른다: 공동출원(`applicantName='A|B'`)은 `|` 로
    분리해 어느 한 출원인이 타깃 핵심토큰과 정확일치하면 채택하고, 그 회사의 `org_slug` 를
    `matched_slug` 로 태깅한다 — delta 가 이 열로 기존 G₀ organization 노드에 assignedTo 를 건다.

    한 특허가 둘 이상의 KSIA 회원사 공동출원이면 각 회사로 복제한다(포트폴리오는 양쪽에 속한다).
    """
    keys = df["applicant_name"].apply(
        lambda name: sorted({key_to_slug[normalize_company_name(tok)]
                             for tok in str(name).split("|")
                             if normalize_company_name(tok) in key_to_slug})
    )
    out = df.assign(matched_slug=keys)
    out = out[out["matched_slug"].apply(len) > 0].explode("matched_slug", ignore_index=True)
    return out


def dedup(df: pd.DataFrame) -> pd.DataFrame:
    """출원번호 기준. 같은 특허가 여러 IPC 클래스 질의로 중복 수집된다."""
    return df.sort_values("application_number").drop_duplicates(subset=["application_number"])


def g0_application_numbers(graph_path=GRAPH_V0) -> set[str]:
    """G₀ 에 이미 있는 특허의 출원번호 (숫자만)."""
    g = rdflib.Graph()
    g.parse(graph_path, format="turtle")
    pred = rdflib.URIRef(str(ONT) + "applicationNumber")
    return {"".join(ch for ch in str(o) if ch.isdigit()) for o in g.objects(None, pred)}


def drop_g0_overlap(df: pd.DataFrame, g0: set[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(델타로 쓸 신규분, G₀ 와 겹쳐 제외된 분) 을 함께 돌려준다 — 제외분도 보고 대상이다."""
    overlap = df[df["application_number"].isin(g0)]
    return df[~df["application_number"].isin(g0)], overlap
