"""C-2 소부장 G₂ (RQ3) 의 경계 계약 — KSIA 코퍼스.

여기서 깨지는 방식:
- KSIA 명부 표기(㈜)와 KIPRIS applicantName((주))가 달라 정확일치 필터가 전량 탈락한다.
- 짧은 이름의 부분일치 오염(질의 '디아이' → 삼성에스디아이)이 필터를 통과한다.
- getBibliographyDetailInfoSearch 응답의 청구항 파싱이 어긋나 FTO 자기완결성이 깨진다.
네트워크는 타지 않는다 — 실제 응답을 잘라 만든 픽스처와 인메모리 프레임을 쓴다.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from sdkb_paper.collect.kipris_client import _parse_detail
from sdkb_paper.preprocess.clean import filter_and_tag_ksia, normalize_company_name

DETAIL_FIXTURE = Path(__file__).parent / "fixtures" / "kipris_bibliography_detail.xml"


def test_normalize_strips_legal_forms():
    """㈜ / (주) / 주식회사 표기차를 흡수한다 — 삼성용 문자열 정확일치의 실패 지점."""
    assert normalize_company_name("㈜넥스틴") == "넥스틴"
    assert normalize_company_name("(주)넥스틴") == "넥스틴"
    assert normalize_company_name("주성엔지니어링(주)") == "주성엔지니어링"
    assert normalize_company_name("주식회사 아이에스티이") == "아이에스티이"
    # 서로 다른 회사는 서로 다른 키로 남는다 (붕괴하지 않는다)
    assert normalize_company_name("디아이") != normalize_company_name("삼성에스디아이")
    assert normalize_company_name("디아이") != normalize_company_name("디아이티")


def _df(names: list[str]) -> pd.DataFrame:
    return pd.DataFrame({"application_number": [f"10201900000{i:02d}" for i in range(len(names))],
                         "applicant_name": names})


def test_filter_and_tag_ksia_matches_and_rejects_noise():
    """정규화-정확일치 + 파이프분리. 오염(삼성에스디아이)은 배제, 태깅은 org_slug."""
    key_to_slug = {"넥스틴": "nextin_inc", "디아이": "di_corporation"}
    df = _df([
        "(주)넥스틴",                       # ㈜↔(주) 표기차 — 채택
        "(주)넥스틴|삼성전자주식회사",        # 공동출원 — 채택 (파이프분리)
        "삼성에스디아이 주식회사",           # 부분일치 오염 — 배제 (핵심토큰 다름)
        "디아이티 주식회사",                 # 다른 KSIA 회원사 — 배제
    ])
    out = filter_and_tag_ksia(df, key_to_slug)
    assert set(out["applicant_name"]) == {"(주)넥스틴", "(주)넥스틴|삼성전자주식회사"}
    assert set(out["matched_slug"]) == {"nextin_inc"}


def test_filter_and_tag_ksia_explodes_joint_ksia_members():
    """한 특허가 둘 이상의 KSIA 회원사 공동출원이면 각 회사로 복제된다(포트폴리오 양쪽 귀속)."""
    key_to_slug = {"넥스틴": "nextin_inc", "주성엔지니어링": "jusung_engineering"}
    df = _df(["(주)넥스틴|주성엔지니어링(주)"])
    out = filter_and_tag_ksia(df, key_to_slug)
    assert len(out) == 2
    assert set(out["matched_slug"]) == {"nextin_inc", "jusung_engineering"}
    assert out["application_number"].nunique() == 1, "같은 특허 — IRI 는 하나로 병합된다"


def test_parse_detail_recovers_all_claims_and_count():
    """FTO 자기완결성: 청구항 전문이 번호순으로 전량 · claimCount 일치 · 초록 포함."""
    body = DETAIL_FIXTURE.read_text(encoding="utf-8")
    d = _parse_detail(body, "1020130025286")
    assert d.claim_count == 3
    assert len(d.claims) == 3, "claimText 트리플 수 == claimCount (자기완결)"
    assert d.claims[0].startswith("1.") and d.claims[2].startswith("3.")
    assert "웨이퍼" in d.abstract
