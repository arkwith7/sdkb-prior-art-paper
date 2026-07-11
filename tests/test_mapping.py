import pandas as pd
import pytest
from rdflib import RDF, Graph, URIRef

from sdkb_paper.config import GRAPH_V0, IPC_MAPPING, ONT
from sdkb_paper.ontology.mapping import (
    load_code_mapping,
    load_term_table,
    map_codes_to_concepts,
    map_text_to_concepts,
    rule_coverage,
)

ETCH = "https://w3id.org/sdkb/data/process/etch"
PLASMA_ETCH = "https://w3id.org/sdkb/data/subprocess/plasma_etch"
EUV = "https://w3id.org/sdkb/data/subprocess/euv_lithography"


@pytest.fixture(scope="module")
def baseline() -> Graph:
    if not GRAPH_V0.exists():
        pytest.skip("graph_v0 없음 — `make vendor && make baseline` 필요")
    return Graph().parse(GRAPH_V0)


# ── 룰 테이블 자체의 무결성 ────────────────────────────────────────────
def test_every_concept_iri_exists_in_sdkb(baseline: Graph):
    """룰이 가리키는 IRI 가 SDKB 에 실제로 없으면, 그 특허는 SHACL 게이트에서 죽는다."""
    types = {ONT.Process, ONT.SubProcess}
    for iris in load_code_mapping().values():
        for iri in iris:
            actual = set(baseline.objects(URIRef(iri), RDF.type))
            assert actual & types, f"{iri} 는 SDKB 의 Process/SubProcess 가 아니다 (실제: {actual})"


def test_no_duplicate_prefixes():
    """같은 접두어가 두 줄에 있으면 매핑이 조용히 다중 개념을 뱉는다."""
    df = pd.read_csv(IPC_MAPPING)
    dupes = df[df.duplicated("code_prefix", keep=False)]["code_prefix"].unique()
    assert not len(dupes), f"중복 접두어: {list(dupes)}"


def test_level_column_matches_actual_type(baseline: Graph):
    """CSV 의 level 컬럼이 SDKB 실제 타입과 어긋나면 커버리지 층위 집계가 틀어진다."""
    df = pd.read_csv(IPC_MAPPING)
    for _, row in df.iterrows():
        expected = ONT.SubProcess if row["level"] == "subprocess" else ONT.Process
        types = set(baseline.objects(URIRef(row["concept_iri"]), RDF.type))
        assert expected in types, f"{row['code_prefix']}: level={row['level']} 인데 실제 타입은 {types}"


# ── 접두어 매칭 ────────────────────────────────────────────────────────
def test_longest_prefix_wins():
    """H01L21/3065(플라즈마 식각)는 H01L21/306(식각 일반)을 이겨야 한다 — 아니면 하위 공정이 사라진다."""
    assert map_codes_to_concepts(["H01L21/3065"], load_code_mapping()) == [PLASMA_ETCH]


def test_fallback_to_shorter_prefix():
    assert map_codes_to_concepts(["H01L21/30621"], load_code_mapping()) == [ETCH]


def test_kipris_spacing_is_normalized():
    """KIPRIS 는 'H01L  21/3065' 처럼 공백을 넣어 준다."""
    assert map_codes_to_concepts(["H01L  21/3065"], load_code_mapping()) == [PLASMA_ETCH]


def test_unmapped_code_returns_empty():
    """미매핑은 버그가 아니라 관측값 — 빈 리스트여야 하고, 그 특허는 게이트에서 걸린다."""
    assert map_codes_to_concepts(["B60W30/00"], load_code_mapping()) == []


# ── 텍스트 매칭 경로 ───────────────────────────────────────────────────
def test_euv_is_unreachable_by_ipc_but_reachable_by_text(baseline: Graph):
    """EUV/DUV 는 둘 다 G03F7/70 아래라 IPC 로는 구분 불가 — 별칭 텍스트로만 갈린다."""
    assert EUV not in {i for iris in load_code_mapping().values() for i in iris}

    terms = load_term_table(baseline)
    hits = map_text_to_concepts("EUV 노광용 마스크 결함 검사 방법", terms)
    assert EUV in hits


def test_text_matching_respects_word_boundary(baseline: Graph):
    """ASCII 약어는 단어경계를 지켜야 한다 — 'ALD' 가 'WALDO' 에 걸리면 안 된다."""
    terms = load_term_table(baseline)
    assert "https://w3id.org/sdkb/data/subprocess/ald" not in map_text_to_concepts("WALDO 장치", terms)


# ── 룰 커버리지 진단 ───────────────────────────────────────────────────
def test_rule_coverage_flags_euv_duv_gap(baseline: Graph):
    """룰 없는 단계를 리포트가 실제로 드러내는지 — 사각지대를 조용히 넘기면 안 된다."""
    df = rule_coverage(baseline)
    assert len(df) == 20
    gaps = set(df[~df["has_rule"]].index.get_level_values("label"))
    assert gaps == {"EUV Lithography", "DUV Lithography"}
