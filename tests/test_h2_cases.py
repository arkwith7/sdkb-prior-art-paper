"""H2 검증 사례의 동결 계약 (PLAN-006).

이 파일이 지키는 것:
  mappings/h2_cases.csv → SDKB 어휘        : 사례 개념이 실재한다 (새 어휘를 만들지 않았다)
  mappings/h2_cases.csv → code_to_concept  : 대조 코드 제목이 스킴 원문과 일치한다
  mappings/h2_cases.csv → 룰 테이블         : subset_flag 가 **유도값과 일치한다**

**사례는 시계열을 보기 전에 동결됐다.** 아래 상수가 바뀌면 사전등록이 깨진 것이다 —
시계열을 보고 유리한 사례만 남기거나 대조 코드를 갈아끼우는 것을 막는 것이 이 테스트의
목적이다 (CLAUDE.md §1.2 · PLAN-006).

subset_flag 를 손으로 적은 값으로 믿지 않고 룰 테이블에서 **유도해서 대조**한다.
이 플래그가 §4.5 의 "대조 코드 제거 재검정" 대상을 정하므로, 룰이 바뀌었는데 플래그가
그대로면 구조적 비대칭의 보고가 거짓이 된다.
"""
from __future__ import annotations

import re

import pandas as pd
from rdflib import Graph, URIRef
from rdflib.namespace import SKOS

from sdkb_paper.config import CODE_MAPPING, EXTERNAL_SDKB, H2_CASES, TERM_ALIASES
from sdkb_paper.ontology.emerging import load_aliases, load_combinations
from sdkb_paper.ontology.mapping import _norm_code

# 동결된 사례 7건. 3건(HBM·GAA·FinFET)으로는 단측 부호검정이 최선의 경우에도 p=0.125 라
# α=0.05 에 구조적으로 도달할 수 없다 — 그래서 시계열을 보기 전에 7건으로 늘렸다.
FROZEN_CASES = {
    "hbm": ("device/hbm", "H10B80/00", False),
    "gaa": ("device/gaa_fet", "H10D30/6735", True),
    "finfet": ("device/finfet", "H10D30/62", True),
    "3d_nand": ("device/3d_nand", "H10B43/27", True),
    "mram": ("device/mram", "H10B61/00", True),
    "fowlp": ("device/fan_out_wlp", "H10W70/09", False),
    "tsv": ("device/tsv", "H10W20/211", True),
}
BASE = "https://w3id.org/sdkb/data/"


def cases() -> pd.DataFrame:
    return pd.read_csv(H2_CASES)


# --- 동결 계약 --------------------------------------------------------------

def test_cases_are_frozen():
    """사례·대조코드·subset_flag 가 바뀌면 사전등록이 깨진다."""
    df = cases().set_index("case_id")
    assert set(df.index) == set(FROZEN_CASES)
    for case_id, (slug, code, subset) in FROZEN_CASES.items():
        row = df.loc[case_id]
        assert row["concept_iri"] == BASE + slug
        assert row["control_code"] == code
        assert bool(row["subset_flag"]) is subset
        assert row["status"] == "frozen-2026-07-13"


def test_cases_carry_evidence_and_source():
    """부상 근거 없이 고른 사례는 우리가 결과를 보고 고른 사례와 구별되지 않는다."""
    df = cases()
    for col in ("evidence", "evidence_source", "control_title"):
        assert df[col].notna().all() and (df[col].str.strip() != "").all()


# --- 계약: h2_cases → SDKB 어휘 ---------------------------------------------

def test_case_concepts_exist_in_sdkb():
    """새 어휘를 만들지 않는다 (CLAUDE.md §1.4). 개념은 SDKB 스냅샷에 실재해야 한다."""
    g = Graph()
    for ttl in sorted(EXTERNAL_SDKB.glob("*.ttl")):
        g.parse(ttl)
    for _, row in cases().iterrows():
        iri = URIRef(row["concept_iri"])
        assert (iri, SKOS.prefLabel, None) in g, f"{iri} 가 SDKB 에 없다"


# --- 계약: h2_cases → code_to_concept (스킴 원문) -----------------------------

def _canon(title: str) -> str:
    """스킴 HTML 의 span 경계에서 생긴 공백 차이는 스킴의 *내용*이 아니다 ('{ x }' vs '{x}')."""
    return re.sub(r"\s+", " ", title).replace("{ ", "{").replace(" }", "}").strip()


def test_control_titles_match_the_scheme_verbatim():
    """대조 코드 제목은 CPC 스킴 원문이다. 룰 테이블과 같은 코드면 제목도 같아야 한다.

    제목이 서로 다르면 둘 중 하나는 스킴을 보지 않고 쓴 것이다 (mappings/PROVENANCE.md).
    """
    rules = pd.read_csv(CODE_MAPPING).set_index("code_prefix")["code_title"].to_dict()
    checked = 0
    for _, row in cases().iterrows():
        if row["control_code"] in rules:
            assert _canon(row["control_title"]) == _canon(rules[row["control_code"]]), (
                row["control_code"]
            )
            checked += 1
    assert checked >= 4, "룰 테이블과 대조된 코드가 너무 적다 — 검사가 vacuous 하다"


# --- 계약: h2_cases → 룰 테이블 (구조적 비대칭) --------------------------------

def derived_subset_flag(concept_iri: str, control_code: str) -> bool:
    """개념 시계열이 대조 코드를 **구조적으로 포함**하는가.

    포함하면 개념이 코드보다 늦게 탐지되는 것이 불가능하다 — H2 에 유리한 비대칭이므로
    사례 표에 싣고 §4.5 에서 대조 코드를 제거해 재검정한다 (PLAN-006).

    0층(룰)만 본다. 2층(조합)은 논리곱이라 대조 코드 하나만으로는 개념이 부여되지 않고,
    1층(별칭)은 코드가 아니라 텍스트 경로다 — 둘 다 포함 관계를 만들지 않는다.
    """
    rules = pd.read_csv(CODE_MAPPING)
    prefixes = rules[rules["concept_iri"] == concept_iri]["code_prefix"]
    code = _norm_code(control_code)
    return any(code.startswith(_norm_code(p)) for p in prefixes)


def test_subset_flag_is_derived_not_asserted():
    """플래그가 룰과 어긋나면 구조적 비대칭의 보고가 거짓이 된다."""
    for _, row in cases().iterrows():
        derived = derived_subset_flag(row["concept_iri"], row["control_code"])
        assert bool(row["subset_flag"]) is derived, (
            f"{row['case_id']}: 표는 {row['subset_flag']} 인데 룰에서 유도하면 {derived}"
        )


def test_bidirectional_cases_are_not_covered_by_combinations_alone():
    """양방향 사례(HBM·FOWLP)의 대조 코드는 조합 정의 **단독으로** 개념을 부여하지 않는다.

    HBM(base) = (H10B80 ∨ H10W90) ∧ TSV — H10B80 만 달린 특허는 HBM 이 아니다.
    이것이 성립해야 HBM 사례가 "개념이 늦을 수도 있는" 진짜 양방향 사례다.
    """
    combos = {c.concept_iri: c for c in load_combinations(variant="base")}
    for _, row in cases().iterrows():
        if row["subset_flag"]:
            continue
        combo = combos.get(row["concept_iri"])
        if combo is not None:
            assert not combo.matches([row["control_code"]]), row["case_id"]


# --- 계약: h2_cases → term_aliases (1층이 사례를 덮는가) -----------------------

def test_every_case_has_base_aliases():
    """개념 시계열의 1층(이름 경로)이 사례마다 살아 있어야 한다.

    GAA 처럼 코드가 0건인 개념은 별칭이 유일한 경로다 — 별칭이 없으면 그 사례는
    검정이 아니라 결측이 된다.
    """
    aliases = load_aliases(variant="base")
    for _, row in cases().iterrows():
        assert aliases.get(row["concept_iri"]), f"{row['case_id']}: base 별칭이 없다"


def test_aliases_carry_language_tags_and_sources():
    """별칭은 G₁ 에 skos:altLabel 로 실체화된다 — 언어 태그와 출처가 없으면 넣지 않는다."""
    df = pd.read_csv(TERM_ALIASES)
    assert set(df["lang"]) <= {"en", "ko"}
    assert df["source"].notna().all() and (df["source"].str.strip() != "").all()
