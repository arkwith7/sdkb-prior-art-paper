"""userdict 빌더 단위 테스트 (PLAN-018 §6.2.1 · SPEC-008).

무거운 원천(온톨로지 파싱·Kiwi 수확·JVM)은 통합 경로이므로 여기서는 순수 함수 —
정규식 메타 제거·논리토큰 처리·정규화 — 만 결정적으로 검증한다.
"""
from __future__ import annotations

from sdkb_paper.retrieval import userdict as ud


def test_norm_collapses_whitespace():
    assert ud._norm("  물리   기상 증착 ") == "물리 기상 증착"
    assert ud._norm("") == ""
    assert ud._norm(None) == ""


def test_split_pattern_strips_regex_meta():
    # dart_terms 스타일: 단어경계·물음표 제거
    assert ud._split_pattern(r"\bHBM\b|고대역폭") == ["HBM", "고대역폭"]
    assert ud._split_pattern(r"V-?NAND|3D ?NAND|3차원 ?낸드") == ["V-NAND", "3D NAND", "3차원 낸드"]


def test_split_pattern_drops_logic_tokens():
    # si_concepts 스타일: 'AND' 논리토큰은 표층형이 아니다
    out = ud._split_pattern("적층|스택|stack AND 관통전극")
    assert "적층" in out and "스택" in out
    assert "stack 관통전극" in out       # AND 만 제거, 남은 표층형은 보존
    assert "AND" not in out and "and" not in out


def test_frozen_params_unchanged():
    # 사전등록 동결값 (U5/U6) — 회귀 차단
    assert ud.DF_MIN == 30
    assert ud.HARVEST_MAX == 2000
    assert "Vendor" in ud.EXCLUDED_CLASSES and "Organization" in ud.EXCLUDED_CLASSES
    assert "CitedPatent" in ud.EXCLUDED_CLASSES
    assert "Process" in ud.DOMAIN_CLASSES and "FailureMode" in ud.DOMAIN_CLASSES
    # 회사명 클래스는 도메인 화이트리스트에 없어야 한다
    assert not (set(ud.DOMAIN_CLASSES) & set(ud.EXCLUDED_CLASSES))
