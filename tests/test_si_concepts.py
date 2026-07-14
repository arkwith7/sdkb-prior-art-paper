"""분류체계 독립 개념 정의 (PLAN-009) — 동결 계약.

이 테스트가 지키는 것은 코드가 아니라 **사전등록**이다. si 정의는 시계열을 보기 전에
동결됐고(커밋이 증거다), 정의가 바뀌면 사전등록이 깨진다.

가장 중요한 계약은 `test_si_definitions_contain_no_classification_codes` 다 —
si 정의에 분류코드가 한 개라도 섞이면 개념 팔이 다시 **미래에서 온 분류**(2021년 이후
신설된 H10 스킴)를 받게 되고, H2 는 검정되기 전에 진다 (PLAN-007 · PLAN-008).
"""
from __future__ import annotations

import re

import pandas as pd
import pytest

from sdkb_paper.config import SI_CONCEPTS
from sdkb_paper.ontology.emerging import (
    VARIANTS,
    TextCombination,
    load_si_combinations,
    parse_text_definition,
    si_devices,
)

HBM = "https://w3id.org/sdkb/data/device/hbm"
GAA = "https://w3id.org/sdkb/data/device/gaa_fet"

# H2 사례 7건 중 FOWLP 는 **사전 배제**다 — 팬아웃 어휘가 전 말뭉치 21건이라 어떤 정의로도
# 시계열이 서지 않는다. 결과를 보고 뺀 것이 아니라 텍스트 가용성 관찰에서 뺐다 (PLAN-009 §3-2).
SI_CONCEPT_IRIS = {
    HBM,
    GAA,
    "https://w3id.org/sdkb/data/device/tsv",
    "https://w3id.org/sdkb/data/device/3d_nand",
    "https://w3id.org/sdkb/data/device/mram",
    "https://w3id.org/sdkb/data/device/finfet",
}

# 동결된 HBM base 구조식 — JEDEC JESD235 ('TSV 로 연결된 적층 DRAM').
FROZEN_HBM_BASE_STRUCTURE = (
    ("적층", "스택", "stack"),
    ("관통전극", "관통 실리콘", "실리콘 관통", "through-silicon", "through silicon", "tsv"),
    ("메모리", "memory", "dram", "디램"),
)

# 분류코드처럼 생긴 토큰 (IPC/CPC 섹션+클래스+서브클래스: H01L · G11C · H10B80 …)
CODE_LIKE = re.compile(r"\b[A-HY]\d{2}[A-Z]\d*")


# --- 동결 계약 --------------------------------------------------------------

def test_si_definitions_contain_no_classification_codes():
    """**si 정의는 분류코드를 일절 담지 않는다.**

    이것이 PLAN-009 의 존재 이유다. 코드가 한 개라도 들어오면 개념이 코드에 기생하고,
    그 코드(H10*)는 2021년 이후 신설되어 과거 특허에 소급 부여되므로 개념은 코드보다
    앞설 수 없게 된다 (PLAN-007 §실측 · PLAN-008 §1).
    """
    df = pd.read_csv(SI_CONCEPTS)
    for row in df.itertuples():
        assert not CODE_LIKE.search(row.definition), f"{row.concept_iri} ({row.variant}) 에 분류코드가 있다"


def test_hbm_base_structure_is_frozen():
    """정의가 바뀌면 사전등록이 깨진다. 바꿔야 한다면 그 사실을 논문에 쓰고 이 상수를 고쳐라."""
    combos = load_si_combinations(variant="base")
    hbm = [c for c in combos if c.concept_iri == HBM]
    assert FROZEN_HBM_BASE_STRUCTURE in {c.groups for c in hbm}


def test_every_variant_is_defined_for_every_concept():
    """민감도 분석은 세 변이 전부가 있어야 성립한다 — 결과를 보고 변이를 추가하지 않는다."""
    df = pd.read_csv(SI_CONCEPTS)
    for concept, sub in df.groupby("concept_iri"):
        assert set(sub["variant"]) == set(VARIANTS), f"{concept} 의 변이가 불완전하다"


def test_si_covers_exactly_the_preregistered_cases():
    """FOWLP 배제는 사전 결정이다 — 결과를 보고 사례를 빼거나 더하지 않는다."""
    df = pd.read_csv(SI_CONCEPTS)
    assert set(df["concept_iri"]) == SI_CONCEPT_IRIS


def test_definitions_carry_sources():
    """출처 없는 정의는 우리가 지어낸 정의다 (CLAUDE.md §1.2)."""
    df = pd.read_csv(SI_CONCEPTS)
    assert df["source"].notna().all() and (df["source"].str.strip() != "").all()


# --- 매칭 규칙 --------------------------------------------------------------

def test_parse_is_and_of_ors():
    assert parse_text_definition("가|나 AND 다") == (("가", "나"), ("다",))


def test_combination_requires_every_group():
    """논리곱이다 — 적층만으로는 HBM 이 아니고, TSV 만으로도 아니다."""
    c = TextCombination(HBM, "base", FROZEN_HBM_BASE_STRUCTURE)
    assert c.matches("관통전극으로 연결된 적층 메모리 장치")
    assert not c.matches("적층 메모리 장치")           # TSV 없음
    assert not c.matches("관통전극을 갖는 반도체 소자")  # 적층·메모리 없음
    assert not c.matches("")


def test_rows_of_same_variant_are_ored():
    """구조식 경로와 이름 경로는 합집합이다 — 이름만 쓴 특허도 잡혀야 한다."""
    combos = load_si_combinations(variant="base")
    assert si_devices("고대역폭 메모리 인터페이스 제어 회로", combos) == [HBM]


def test_ascii_terms_respect_word_boundaries():
    """'gaa' 가 'gaas'(갈륨비소)에 걸리면 개념이 오염된다."""
    combos = load_si_combinations(variant="strict")
    assert si_devices("GaAs 기판 위의 화합물 반도체", combos) == []
    assert si_devices("gate-all-around 구조의 트랜지스터", combos) == [GAA]


def test_si_ignores_codes_entirely():
    """si 개념은 텍스트만 본다 — 코드가 무엇이든 판정에 영향이 없다."""
    combos = load_si_combinations(variant="base")
    assert si_devices("반도체 장치의 제조 방법", combos) == []


def test_concepts_are_not_mutually_exclusive():
    """HBM 특허는 TSV 특허이기도 하다 — JEDEC 정의가 TSV 적층을 전제하므로 당연하다.
    개념은 배타적 분류가 아니다 (코드 체계와 다른 점이다)."""
    combos = load_si_combinations(variant="base")
    hits = si_devices("관통전극을 통해 적층된 디램 다이", combos)
    assert hits == sorted([HBM, "https://w3id.org/sdkb/data/device/tsv"])


def test_deterministic():
    combos = load_si_combinations(variant="base")
    text = "나노시트 채널을 갖는 트랜지스터"
    assert si_devices(text, combos) == si_devices(text, combos) == [GAA]


def test_unknown_variant_raises():
    with pytest.raises(ValueError):
        load_si_combinations(variant="whatever")
