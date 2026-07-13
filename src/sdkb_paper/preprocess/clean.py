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

import pandas as pd
import rdflib

from sdkb_paper.config import GRAPH_V0, ONT

TARGET_APPLICANTS = ("삼성전자주식회사", "에스케이하이닉스 주식회사")


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
