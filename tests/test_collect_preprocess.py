"""collect → preprocess 경계의 계약 (CLAUDE.md §5(b)).

여기서 깨지는 방식: KIPRIS 응답 필드명·타입이 바뀌면 raw 스키마가 조용히 어긋나고,
정규화되지 않은 출원번호·계열사 표기가 매핑과 중복 제거를 통과해 버린다.
네트워크는 타지 않는다 — 실제 응답을 잘라 만든 픽스처를 쓴다.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from sdkb_paper.collect.kipris_client import _parse, _result_code
from sdkb_paper.preprocess.clean import (
    dedup,
    drop_g0_overlap,
    filter_applicants,
    normalize,
)

FIXTURE = Path(__file__).parent / "fixtures" / "kipris_advanced_search.xml"


@pytest.fixture
def body() -> str:
    return FIXTURE.read_text(encoding="utf-8")


def test_raw_schema_contract(body):
    """응답 → KiprisRecord: 필드가 계약대로 채워진다."""
    recs = _parse(body, applicant="삼성전자주식회사", ipc="G03F")
    assert recs, "픽스처에 item 이 있어야 한다"
    r = recs[0]
    assert r.application_number.isdigit() and len(r.application_number) == 13
    assert len(r.application_date) == 8 and r.application_date.isdigit()
    assert r.applicant_name
    assert r.query_applicant == "삼성전자주식회사" and r.query_ipc == "G03F"  # 출처 추적


def test_result_code(body):
    assert _result_code(body) == "00"


def _df(rows: list[dict]) -> pd.DataFrame:
    cols = {"application_number": "", "applicant_name": "", "application_date": "",
            "ipc_number": ""}
    return pd.DataFrame([{**cols, **r} for r in rows])


def test_normalize_handles_hyphens_and_bad_dates():
    df = _df([
        {"application_number": "10-2022-0121121", "application_date": "20220923",
         "ipc_number": "G03F 7/20|H10P 14/24"},
        {"application_number": "1020150000001", "application_date": "",          # 결측 출원일
         "ipc_number": "G03F 7/20"},
        {"application_number": "", "application_date": "20200101",               # 결측 출원번호
         "ipc_number": ""},
    ])
    out = normalize(df)
    assert len(out) == 1, "출원일·출원번호 결측 행은 떨어진다"
    row = out.iloc[0]
    assert row.application_number == "1020220121121", "하이픈 제거 — G₀ 중복 제거의 키"
    assert row.ipc_codes == ["G03F 7/20", "H10P 14/24"]


def test_filter_applicants_is_exact():
    """KIPRIS applicant 는 부분일치라 계열사가 섞여 온다 — 여기서 걸러야 한다."""
    df = _df([
        {"applicant_name": "삼성전자주식회사"},
        {"applicant_name": "삼성디스플레이 주식회사"},
        {"applicant_name": "에스케이하이닉스 주식회사"},
        {"applicant_name": "삼성전자주식회사 외 1"},
    ])
    kept = filter_applicants(df)
    assert sorted(kept.applicant_name) == ["삼성전자주식회사", "에스케이하이닉스 주식회사"]


def test_dedup_by_application_number():
    """한 특허가 여러 IPC 클래스 질의로 중복 수집된다."""
    df = _df([{"application_number": "1020220121121"}, {"application_number": "1020220121121"}])
    assert len(dedup(df)) == 1


def test_drop_g0_overlap_reports_both_sides():
    """G₀ 에 이미 있는 특허를 델타에 넣으면 H1 의 before/after 가 같은 특허를 센다."""
    df = _df([{"application_number": "1020220121121"}, {"application_number": "1019970082313"}])
    delta, overlap = drop_g0_overlap(df, {"1019970082313"})
    assert list(delta.application_number) == ["1020220121121"]
    assert list(overlap.application_number) == ["1019970082313"], "제외분도 보고 대상이다"
