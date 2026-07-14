"""신기술 인식 레이어의 계약 (PLAN-004).

이 파일이 지키는 것:
  mappings/*.csv  → ontology.emerging : 동결된 정의가 코드와 어긋나지 않는다
  ontology.emerging → ontology.delta  : 디바이스 축에만 링크를 더한다 (H1 불변)
  ontology.delta   → 그래프           : 별칭이 skos:altLabel(언어태그)로 실체화된다

**정의는 동결됐다.** 아래 상수가 바뀌면 사전등록이 깨진 것이다 — 시계열을 보고 정의를
고치는 것을 막는 것이 이 테스트의 목적이다 (CLAUDE.md §1.2).
"""
from __future__ import annotations

import pandas as pd
import pytest
from rdflib import RDF, SKOS, Literal, URIRef

from sdkb_paper.config import EMERGING_CONCEPTS, ONT, TERM_ALIASES
from sdkb_paper.ontology.emerging import (
    VARIANTS,
    Combination,
    alias_labels,
    emerging_devices,
    load_aliases,
    load_combinations,
    match_aliases,
    parse_definition,
)

HBM = "https://w3id.org/sdkb/data/device/hbm"
GAA = "https://w3id.org/sdkb/data/device/gaa_fet"
FINFET = "https://w3id.org/sdkb/data/device/finfet"

# 동결된 base 정의. 외부 원천(CPC 2026.01 스킴 · H10B80/00 WARNING)에서 왔다.
FROZEN_HBM_BASE = (("H10B80", "H10W90"), ("H10W20/20", "H10W20/211", "H10W20/023"))
FROZEN_GAA_BASE = (("H10D30/6735", "H10D30/501"),)


# --- 동결 계약 --------------------------------------------------------------

def test_base_definitions_are_frozen():
    """정의가 바뀌면 사전등록이 깨진다. 바꿔야 한다면 그 사실을 논문에 쓰고 이 상수를 고쳐라."""
    combos = {c.concept_iri: c.groups for c in load_combinations(variant="base")}
    assert combos[HBM] == FROZEN_HBM_BASE
    assert combos[GAA] == FROZEN_GAA_BASE


def test_every_variant_is_defined_for_every_concept():
    """민감도 분석은 세 변이 전부가 있어야 성립한다 — 결과를 보고 변이를 추가하지 않는다."""
    df = pd.read_csv(EMERGING_CONCEPTS)
    for concept, sub in df.groupby("concept_iri"):
        assert set(sub["variant"]) == set(VARIANTS), f"{concept} 의 변이가 불완전하다"


def test_definitions_and_aliases_carry_sources():
    """출처 없는 정의는 우리가 지어낸 정의다 (CLAUDE.md §1.2)."""
    for path in (EMERGING_CONCEPTS, TERM_ALIASES):
        df = pd.read_csv(path)
        assert df["source"].notna().all() and (df["source"].str.strip() != "").all()


def test_aliases_use_bcp47_language_codes():
    """SDKB 의 라벨 설계는 prefLabel@en 기준 · altLabel@ko 별칭이다. 'kr' 은 언어코드가 아니다."""
    df = pd.read_csv(TERM_ALIASES)
    assert set(df["lang"]) <= {"en", "ko", "ja"}


# --- 조합 정의 (2층) --------------------------------------------------------

def test_parse_definition_is_and_of_ors():
    assert parse_definition("A|B AND C") == (("A", "B"), ("C",))


def test_combination_requires_every_group():
    """논리곱이다 — 적층 메모리만으로는 HBM 이 아니고, TSV 만으로도 아니다."""
    c = Combination(HBM, "base", FROZEN_HBM_BASE)
    assert c.matches(["H10B 80/00", "H10W 20/20"])       # 적층 ∧ TSV
    assert not c.matches(["H10B 80/00"])                  # 적층만
    assert not c.matches(["H10W 20/20"])                  # TSV 만
    assert not c.matches([])


def test_combination_normalizes_kipris_spacing():
    """KIPRIS 는 'H10B 80/00' 처럼 공백을 넣는다 — 정규화 없이는 조합이 통째로 0건이 된다."""
    c = Combination(HBM, "base", FROZEN_HBM_BASE)
    assert c.matches(["H10B 80/00", "H10W 20/211"])
    assert c.matches(["h10b80/00", "h10w20/211"])


def test_gaa_dedicated_codes_match_nothing_in_our_corpus():
    """GAA 전용 코드는 존재하는데 부여되지 않는다 — H2 의 논지에 대한 관측 증거다.

    이 테스트가 실패한다면 KIPRIS 가 GAA 코드를 부여하기 시작한 것이고, 그것은 H2 의
    전제가 바뀌었다는 뜻이다. 조용히 지나가면 안 된다.
    """
    combos = load_combinations(variant="base")
    gaa = next(c for c in combos if c.concept_iri == GAA)
    assert not gaa.matches(["H10D 30/67", "H10D 62/10"])  # 상위군은 GAA 가 아니다
    assert gaa.matches(["H10D 30/501"])                    # 나노시트 채널이면 GAA 다


# --- 별칭 (1층) -------------------------------------------------------------

def test_korean_alias_matches_korean_abstract():
    """국문 명세를 영문 라벨로 매칭하던 것이 이 레이어 이전의 결함이었다."""
    aliases = load_aliases(variant="base")
    assert match_aliases("적층 나노시트 채널을 갖는 트랜지스터", aliases) == [GAA]
    assert match_aliases("고대역폭 메모리 장치 및 그 제조 방법", aliases) == [HBM]


def test_ascii_alias_respects_word_boundary():
    """'GAA' 가 'GAAS'(갈륨비소) 안에서 걸리면 안 된다."""
    aliases = load_aliases(variant="base")
    assert match_aliases("GaAs 기판 위의 소자", aliases) == []
    assert match_aliases("GAA 구조의 트랜지스터", aliases) == [GAA]


def test_loose_variant_adds_nanowire_but_base_does_not():
    """나노와이어는 정밀도 위험이 있어 base 에서 뺐다 — 민감도(loose)에서만 잡힌다."""
    text = "나노와이어를 이용한 반도체 소자"
    assert match_aliases(text, load_aliases(variant="base")) == []
    assert match_aliases(text, load_aliases(variant="loose")) == [GAA]


def test_alias_labels_are_language_tagged():
    labels = alias_labels(variant="base")
    assert (HBM, "고대역폭 메모리", "ko") in labels
    assert (GAA, "MBCFET", "en") in labels
    assert not any(lang == "loose" for _, _, lang in labels)


# --- 두 층의 합 -------------------------------------------------------------

def test_name_path_and_combination_path_are_both_needed():
    """이름을 쓴 특허는 1층이, 이름도 코드도 없는 특허는 2층이 잡는다.

    HBM 조합 209건 중 명세에 이름을 쓴 것은 4건뿐이다 — 한 층만으로는 나머지를 놓친다.
    """
    aliases, combos = load_aliases(variant="base"), load_combinations(variant="base")

    only_name = emerging_devices(["G11C 7/10"], "고대역폭 메모리 인터페이스", aliases, combos)
    only_code = emerging_devices(["H10B 80/00", "H10W 20/20"], "적층형 반도체 장치", aliases, combos)
    assert only_name == [HBM]
    assert only_code == [HBM]


def test_unrelated_patent_gets_nothing():
    aliases, combos = load_aliases(variant="base"), load_combinations(variant="base")
    assert emerging_devices(["G11C 7/10"], "메모리 회로의 리프레시 제어", aliases, combos) == []


def test_emerging_is_deterministic():
    aliases, combos = load_aliases(variant="base"), load_combinations(variant="base")
    args = (["H10B 80/00", "H10W 20/20"], "MBCFET 및 고대역폭 메모리", aliases, combos)
    assert emerging_devices(*args) == emerging_devices(*args)


def test_unknown_variant_is_rejected():
    with pytest.raises(ValueError):
        load_combinations(variant="whatever")


# --- delta 경계: 디바이스 축만 건드린다 (H1 불변) -----------------------------

def test_delta_adds_device_links_and_altlabels_only(tmp_path):
    """신기술 레이어가 공정 축을 건드리면 H1 이 사후에 움직인다 — 그것을 여기서 막는다."""
    from sdkb_paper.ontology.delta import build_delta

    df = pd.DataFrame([{
        "application_number": "1020230000001",
        "applicant_name": "삼성전자주식회사",
        "application_date": pd.Timestamp("2023-05-01"),
        "invention_title": "적층형 반도체 장치",
        "abstract": "관통 전극을 포함하는 적층 메모리",
        "ipc_codes": ["H10B 80/00", "H10W 20/20"],   # 공정 룰에 걸리지 않는 코드만
        "open_date": "20240101",
    }])
    g = build_delta(df)

    pat = next(iter(g.subjects(RDF.type, ONT.Patent)))
    assert (pat, ONT.concernsDevice, URIRef(HBM)) in g
    assert list(g.objects(pat, ONT.realizesProcess)) == []          # 공정 축 불변
    assert (URIRef(HBM), SKOS.altLabel, Literal("고대역폭 메모리", lang="ko")) in g
