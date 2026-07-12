import pandas as pd
import pytest
from rdflib import RDF, Graph, URIRef

from sdkb_paper.config import CODE_MAPPING, GRAPH_V0, ONT
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
DRAM = "https://w3id.org/sdkb/data/device/dram"
EPROM = "https://w3id.org/sdkb/data/device/eprom"
DICING = "https://w3id.org/sdkb/data/subprocess/dicing"

# 축별 타입 계약 — 룰의 axis 가 SDKB 실제 타입과 어긋나면 잘못된 술어로 트리플이 나간다.
AXIS_TYPES = {
    "process": {ONT.Process, ONT.SubProcess},
    "device": {ONT.Device},
}


@pytest.fixture(scope="module")
def baseline() -> Graph:
    if not GRAPH_V0.exists():
        pytest.skip("graph_v0 없음 — `make vendor && make baseline` 필요")
    return Graph().parse(GRAPH_V0)


# ── 룰 테이블 자체의 무결성 ────────────────────────────────────────────
def test_every_concept_iri_exists_in_sdkb(baseline: Graph):
    """룰이 가리키는 IRI 가 SDKB 에 실제로 없으면, 그 특허는 SHACL 게이트에서 죽는다."""
    for pairs in load_code_mapping().values():
        for iri, axis in pairs:
            actual = set(baseline.objects(URIRef(iri), RDF.type))
            assert actual & AXIS_TYPES[axis], f"{iri}: axis={axis} 인데 실제 타입은 {actual}"


def test_no_duplicate_prefixes():
    """같은 접두어가 두 줄에 있으면 매핑이 조용히 다중 개념을 뱉는다."""
    df = pd.read_csv(CODE_MAPPING)
    dupes = df[df.duplicated("code_prefix", keep=False)]["code_prefix"].unique()
    assert not len(dupes), f"중복 접두어: {list(dupes)}"


def test_level_column_matches_actual_type(baseline: Graph):
    """CSV 의 level 컬럼이 SDKB 실제 타입과 어긋나면 커버리지 층위 집계가 틀어진다."""
    expected_type = {
        "process": ONT.Process,
        "subprocess": ONT.SubProcess,
        "device": ONT.Device,
    }
    df = pd.read_csv(CODE_MAPPING)
    for _, row in df.iterrows():
        types = set(baseline.objects(URIRef(row["concept_iri"]), RDF.type))
        assert expected_type[row["level"]] in types, (
            f"{row['code_prefix']}: level={row['level']} 인데 실제 타입은 {types}"
        )


def test_device_codes_never_map_to_process():
    """소자 분류(H10B·H10D·G11C)를 공정에 매핑하면 그것은 룰이 아니라 날조다."""
    table = load_code_mapping()
    for code in ("H10B69", "H10D8", "G11C16"):
        assert not map_codes_to_concepts([code], table)["process"]
        assert map_codes_to_concepts([code], table)["device"]


# ── 접두어 매칭 ────────────────────────────────────────────────────────
def test_longest_prefix_wins():
    """H10P50/20(플라즈마 식각)은 H10P50(식각 일반)을 이겨야 한다 — 아니면 하위 공정이 사라진다."""
    assert map_codes_to_concepts(["H10P50/20"], load_code_mapping())["process"] == [PLASMA_ETCH]


def test_fallback_to_shorter_prefix():
    assert map_codes_to_concepts(["H10P50/99"], load_code_mapping())["process"] == [ETCH]


def test_kipris_spacing_is_normalized():
    """KIPRIS 는 'H10P  50/20' 처럼 공백을 넣어 준다."""
    assert map_codes_to_concepts(["H10P  50/20"], load_code_mapping())["process"] == [PLASMA_ETCH]


def test_both_axes_from_one_patent():
    """한 특허가 공정 코드와 소자 코드를 함께 갖는 것이 정상이다 — 두 축이 같이 나와야 한다."""
    hits = map_codes_to_concepts(["H10P50/20", "H10B12"], load_code_mapping())
    assert hits["process"] == [PLASMA_ETCH]
    assert hits["device"] == [DRAM]


def test_retired_ipc_code_still_maps():
    """KIPRIS 는 구형 특허에 폐지 코드(H01L21/8247)를 그대로 달아 둔다."""
    assert map_codes_to_concepts(["H01L21/8247"], load_code_mapping())["device"] == [EPROM]


def test_back_end_process_is_reachable():
    """후공정(다이싱)은 SemiKong Table 7 복원 전에는 매핑 자체가 불가능했다."""
    assert map_codes_to_concepts(["H10P58/00"], load_code_mapping())["process"] == [DICING]


def test_unmapped_code_returns_empty():
    """미매핑은 버그가 아니라 관측값 — 두 축 모두 비어야 하고, 그 특허는 게이트에서 걸린다."""
    assert map_codes_to_concepts(["B60W30/00"], load_code_mapping()) == {
        "process": [],
        "device": [],
    }


def test_wafer_handling_stays_unmapped():
    """H10P72(웨이퍼 핸들링)는 SemiKong 의 공정 모듈이 아니다 — 커버리지를 위해 억지 매핑하지 않는다."""
    hits = map_codes_to_concepts(["H10P72/70"], load_code_mapping())
    assert hits == {"process": [], "device": []}


# ── 텍스트 매칭 경로 ───────────────────────────────────────────────────
def test_euv_is_unreachable_by_ipc_but_reachable_by_text(baseline: Graph):
    """EUV/DUV 를 가르는 IPC 그룹은 공식 스킴에 없다 — 별칭 텍스트로만 갈린다."""
    assert EUV not in {i for pairs in load_code_mapping().values() for i, _ in pairs}

    terms = load_term_table(baseline)
    hits = map_text_to_concepts("EUV 노광용 마스크 결함 검사 방법", terms)
    assert EUV in hits


def test_text_matching_respects_word_boundary(baseline: Graph):
    """ASCII 약어는 단어경계를 지켜야 한다 — 'ALD' 가 'WALDO' 에 걸리면 안 된다."""
    terms = load_term_table(baseline)
    assert "https://w3id.org/sdkb/data/subprocess/ald" not in map_text_to_concepts("WALDO 장치", terms)


# ── 룰 커버리지 진단 ───────────────────────────────────────────────────
def test_rule_coverage_spans_both_axes(baseline: Graph):
    """커버리지 리포트는 개념 축 전체(Process ∪ Device)를 봐야 한다 — 한 축만 보면 사각지대가 숨는다."""
    df = rule_coverage(baseline)
    assert set(df.index.get_level_values("level")) == {"process", "subprocess", "device"}
    assert len(df) == 83  # Process 11 + SubProcess 38 + Device 34


def test_rule_coverage_flags_euv_duv_gap(baseline: Graph):
    """룰 없는 단계를 리포트가 실제로 드러내는지 — 사각지대를 조용히 넘기면 안 된다."""
    df = rule_coverage(baseline)
    gaps = set(df[~df["has_rule"]].index.get_level_values("label"))
    assert {"EUV Lithography", "DUV Lithography"} <= gaps
