"""IR family 수집기의 순수 정규화 로직 단위 테스트 (collect/bq_family_ir).

BQ 접근 없이 `normalize_pub`(doc_id → 정규화 공개번호 키)만 검증한다 — KR 타입접두 특례 포함.
"""
from __future__ import annotations

from sdkb_paper.collect.bq_family_ir import normalize_pub


def test_non_kr_single_key():
    # CN: kind code(A) 제거 · 앞0 제거 없음.
    assert normalize_pub("cn_CN102403077A") == ("CN", ["CN102403077"])
    assert normalize_pub("us_US5308414") == ("US", ["US5308414"])


def test_kr_type_prefix_variant():
    # KR 등록번호 100146263 = 10(특허접두)+0146263 → 접두 제거 변형 추가.
    cc, keys = normalize_pub("kr_KR100146263B1")
    assert cc == "KR"
    assert "KR100146263" in keys        # 원형(앞0 제거)
    assert "KR146263" in keys            # 접두 10 + 앞0 제거 변형 → BQ KR-0146263-B1 과 매칭


def test_kr_utility_prefix():
    # 20 = 실용신안 접두.
    _, keys = normalize_pub("kr_KR200146153U")
    assert "KR146153" in keys            # 20 제거 변형


def test_leading_zero_stripped():
    _, keys = normalize_pub("jp_JP03138980A")
    assert keys[0] == "JP3138980"        # 앞 0 제거


def test_unparseable_returns_none():
    assert normalize_pub("nofmt") is None
    assert normalize_pub("xx_") is None
