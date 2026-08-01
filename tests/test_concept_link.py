"""개념 적용기의 계약 — 정규화·경계·결정성·무작동·역할 대칭·축 확장·누출 (PLAN-034 §3.8).

여기의 단위 테스트는 **외부 데이터 없이** 돈다. 실제 사전·코퍼스가 필요한 것은
통합 테스트(파일이 있을 때만)로 표시하고 없으면 skip 한다 — CI 는 `make corpus` 후 돈다.
"""
from __future__ import annotations

import json
import random

import pandas as pd
import pytest

from sdkb_paper import config
from sdkb_paper.corpus import concept_link as CL
from sdkb_paper.ontology import concept_axis as CA
from sdkb_paper.ontology import concept_dict as CD

DATA_NS = str(config.SDKB_DATA)


# --- 사전 픽스처 --------------------------------------------------------------

def _dict_doc(entries: list[dict]) -> dict:
    return {"schema_version": "1.0", "profiles": {CD.PROFILE: {"entries": entries, "blocked": []}}}


def _write_dict(tmp_path, entries: list[dict]):
    p = tmp_path / "concept_mapping.json"
    p.write_text(json.dumps(_dict_doc(entries), ensure_ascii=False), encoding="utf-8")
    return p


def _entry(surface, concept_id, lang="ko", ctype="Material", conf=1.0, ambiguous=False):
    return {"surface": surface, "lang": lang, "concept_id": concept_id, "concept_type": ctype,
            "rule_id": "T1-CANONICAL", "confidence": conf, "ambiguous": ambiguous}


# --- R1 정규화 ----------------------------------------------------------------

def test_normalize_follows_r1():
    assert CD.normalize("Plasma-Etch (Dry)") == "plasma etch dry"
    assert CD.normalize("A/B_C.D") == "a b c d"
    assert CD.normalize("  식각   공정 ") == "식각 공정"
    assert CD.normalize("") == "" and CD.normalize(None) == ""


def test_needs_boundary_only_for_latin_or_digit():
    assert CD.needs_boundary("al") and CD.needs_boundary("3d nand")
    assert not CD.needs_boundary("식각")


# --- BOUND 경계 규칙 (2단계 실측이 채택 근거) ----------------------------------

def test_bound_surface_rejects_substring_hit():
    """`al` 이 *metal*·*chemical* 안에서 걸리면 위양성이다(NAIVE 가 기각된 이유)."""
    al = CD.Surface("al", True, ())
    assert not CL._fires("a metal layer", al)
    assert not CL._fires("chemical vapor", al)
    assert CL._fires("an al film", al)          # 단독
    assert CL._fires("al", al)                  # 문자열 전체
    assert CL._fires("al film", al)             # 시작 경계
    assert CL._fires("thin al", al)             # 끝 경계
    assert CL._fires("layer/al/film", CD.Surface("al", True, ()))  # 정규화된 구분자


def test_hangul_surface_matches_as_substring():
    """한국어는 교착어라 경계가 공백으로 서지 않는다 — 부분문자열이 정본 규칙이다."""
    s = CD.Surface("식각", False, ())
    assert CL._fires("건식식각을 수행하고", s)


def test_empty_text_or_surface_never_fires():
    assert not CL._fires("", CD.Surface("al", True, ()))
    assert not CL._fires("무언가", CD.Surface("", False, ()))


# --- 사전 적재 ----------------------------------------------------------------

def test_load_missing_file_returns_empty_dict():
    """사전이 없는 상태(CR-007 이전 스냅샷 · O 팔)에서 적용기는 무작동이어야 한다."""
    assert CD.load(config.DATA / "__no_such_dict__.json") == ()


def test_load_unknown_profile_fails_loudly(tmp_path):
    p = tmp_path / "d.json"
    p.write_text(json.dumps({"profiles": {"expert-tag": {"entries": []}}}), encoding="utf-8")
    with pytest.raises(SystemExit):
        CD.load(p)


def test_load_is_sorted_and_groups_surfaces(tmp_path):
    p = _write_dict(tmp_path, [
        _entry("증착", "process:deposition", ctype="Process"),
        _entry("산화막", "material:sio2"),
        _entry("산화막", "material:oxide"),
    ])
    surfaces = CD.load(p)
    assert [s.text for s in surfaces] == ["산화막", "증착"]          # 표면형 사전순
    assert [e.concept_id for e in surfaces[0].entries] == ["material:oxide", "material:sio2"]


def test_entry_slug_and_segment():
    e = CD.Entry("equipment_class:cd_sem", "EquipmentClass", "T1", 1.0, False)
    assert e.slug == "cd_sem" and e.segment == "equipment_class"


def test_concept_universe_builds_data_iri(tmp_path):
    surfaces = CD.load(_write_dict(tmp_path, [_entry("아르곤", "material:argon")]))
    assert CD.concept_universe(surfaces) == {"material:argon": f"{DATA_NS}material/argon"}
    assert CD.concept_types(surfaces) == {f"{DATA_NS}material/argon": "Material"}


# --- 결정성(S1) ---------------------------------------------------------------

def test_match_is_independent_of_dictionary_order(tmp_path):
    """사전 순서가 결과를 바꾸면 S1 위반이다 — 표면형은 서로 독립으로 판정한다."""
    surfaces = CD.load(_write_dict(tmp_path, [
        _entry("식각", "process:etch", ctype="Process"),
        _entry("건식 식각", "subprocess:dry_etch", ctype="SubProcess"),
        _entry("막", "material:film"),
    ]))
    text = "건식 식각으로 막을 제거한다"
    got = CL.concept_ids(CL.match(text, surfaces))
    shuffled = tuple(random.Random(7).sample(list(surfaces), len(surfaces)))
    assert CL.concept_ids(CL.match(text, shuffled)) == got
    # 겹치는 표면형이 서로를 소비하지 않는다 (교체 정규식이라면 하나만 남는다)
    assert got == {"process:etch", "subprocess:dry_etch", "material:film"}


def test_sidecar_rows_are_deterministically_ordered(tmp_path):
    surfaces = CD.load(_write_dict(tmp_path, [
        _entry("막", "material:film"), _entry("식각", "process:etch", ctype="Process")]))
    _, side = CL.link_corpus(["막을 식각한다", "식각"], ["b_doc", "a_doc"], surfaces)
    assert list(side["doc_id"]) == sorted(side["doc_id"])
    assert side.columns.tolist() == ["doc_id", "concept_id", "slug", "axis", "surface",
                                     "rule_id", "confidence", "ambiguous"]


# --- 무작동(O 팔) · 합집합(Q4) ------------------------------------------------

def test_empty_dictionary_is_a_no_op():
    """사전이 비면 `concepts` 열을 **건드리지 않는다** — O 팔 코퍼스가 바이트로 재현돼야 한다."""
    corpus = pd.DataFrame({"doc_id": ["d1"], "text_main": ["식각 공정"],
                           "concepts": [["etch"]]})
    before = corpus["concepts"].tolist()
    side = CL.apply_to_corpus(corpus, ())
    assert side.empty and corpus["concepts"].tolist() == before


def test_apply_unions_graph_links_and_linker_links(tmp_path):
    surfaces = CD.load(_write_dict(tmp_path, [_entry("산화막", "material:oxide")]))
    corpus = pd.DataFrame({"doc_id": ["d1"], "text_main": ["산화막을 형성한다"],
                           "concepts": [["etch"]]})
    CL.apply_to_corpus(corpus, surfaces)
    assert corpus["concepts"].iloc[0] == ["etch", "oxide"]    # 합집합·정렬


def test_apply_handles_numpy_cells():
    """parquet 왕복 후 셀은 numpy 배열이다 — `or` 로 다루면 터진다(실제로 터졌다)."""
    import numpy as np
    corpus = pd.DataFrame({"doc_id": ["d1"], "text_main": ["x"],
                           "concepts": [np.array(["etch"], dtype=object)]})
    assert CL._as_set(corpus["concepts"].iloc[0]) == {"etch"}
    assert CL._as_set(None) == set()


def test_ambiguous_surface_keeps_all_candidates(tmp_path):
    """Q3(승인) — 상류가 정렬해 넘긴 후보를 하류에서 자르지 않는다."""
    surfaces = CD.load(_write_dict(tmp_path, [
        _entry("산화막", "material:oxide", conf=1.0, ambiguous=True),
        _entry("산화막", "material:sio2", conf=0.7, ambiguous=True)]))
    assert CL.concept_ids(CL.match("산화막", surfaces)) == {"material:oxide", "material:sio2"}


# --- 역할 대칭(결정 D) ---------------------------------------------------------

def test_match_has_no_role_argument():
    """질의·후보 비대칭은 T1 을 오염시킨다 — 구조로 막는다(시그니처 계약)."""
    import inspect

    params = set(inspect.signature(CL.match).parameters)
    assert not (params & {"is_query", "role", "query", "is_candidate"})
    src = inspect.getsource(CL)
    assert "is_query" not in src


# --- 축 지도 확장(A′) ----------------------------------------------------------

def _axis_store():
    from pyoxigraph import NamedNode, Quad, Store

    s = Store()
    rdft = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
    g = NamedNode("urn:g0")

    def q(a, b, c):
        s.add(Quad(NamedNode(a), NamedNode(b), NamedNode(c), g))

    ont = "https://w3id.org/sdkb/ont/"
    # 그래프 링크 보유 개념(기존) — 지역명 `etch`
    q(f"{DATA_NS}process/etch", rdft, f"{ont}Process")
    q(f"{DATA_NS}patent/doc1", f"{ont}realizesProcess", f"{DATA_NS}process/etch")
    # 사전에만 있는 개념 — 그래프 타입은 있다
    q(f"{DATA_NS}material/argon", rdft, f"{ont}Material")
    return s


def test_extract_adds_dictionary_concepts_to_axis_map():
    store = _axis_store()
    base, _ = CA.extract(store=store)
    assert set(base["slug"]) == {"etch"}
    extra = {f"{DATA_NS}material/argon": "Material",
             f"{DATA_NS}rootcause/etch": "RootCause",     # 지역명 충돌(축 다름)
             f"{DATA_NS}skill/no_type_here": "Skill"}     # 그래프 타입 없음 → 사전 축
    df, _ = CA.extract(store=_axis_store(), extra_iris=extra)
    axis = dict(zip(df["slug"], df["axis_class"]))
    assert axis["argon"] == "Material"                    # ① 그래프 rdf:type
    assert axis["no_type_here"] == "Skill"                # ② 사전 concept_type
    assert axis["etch"] == "Process"                      # 기존 개념의 축은 뒤집히지 않는다
    assert df.columns.tolist() == base.columns.tolist()   # 스키마 불변(무작동 동치성)


def test_extract_ignores_non_sdkb_extra_iris():
    df, _ = CA.extract(store=_axis_store(), extra_iris={"http://example.org/x": "Material"})
    assert set(df["slug"]) == {"etch"}


# --- 누출(§3.6) ---------------------------------------------------------------

def test_check_doc_identifiers_flags_patent_numbers():
    from sdkb_paper.validate import leakage_check as LC

    assert LC.check_doc_identifiers(["kr 1020180123456", "1020180123456"])
    assert LC.check_doc_identifiers(["us 9876543"])
    assert not LC.check_doc_identifiers(["193nm pr", "3d nand", "식각", "300mm"])


def test_audit_concept_dict_passes_clean_and_fails_dirty(tmp_path):
    from sdkb_paper.validate import leakage_check as LC

    (tmp_path / "a").mkdir()
    clean = _write_dict(tmp_path / "a", [_entry("식각", "process:etch", ctype="Process")])
    assert LC.audit_concept_dict(clean)["pass"]

    (tmp_path / "b").mkdir()
    dirty = _write_dict(tmp_path / "b", [_entry("kr 1020180123456", "process:etch")])
    res = LC.audit_concept_dict(dirty)
    assert not res["pass"] and res["bad_doc_identifiers"]

    (tmp_path / "c").mkdir()
    leaky = _write_dict(tmp_path / "c", [_entry("식각", "hasPriorArtExaminer:x")])
    assert not LC.audit_concept_dict(leaky)["pass"]


def test_audit_concept_dict_absent_is_not_a_violation(tmp_path):
    from sdkb_paper.validate import leakage_check as LC

    res = LC.audit_concept_dict(tmp_path / "nope.json")
    assert res["pass"] and res["exists"] is False


# --- 벤더 계약(S6 · D-16) ------------------------------------------------------

def test_concept_mapping_is_vendored():
    from sdkb_paper.ontology.vendor import VENDOR_FILES

    assert any(rel == "mappings/concept_mapping.json" for rel, _ in VENDOR_FILES)
    assert config.SDKB_CONCEPT_MAP.name == "concept_mapping.json"


# --- 통합(산출물이 있을 때만) ---------------------------------------------------

@pytest.mark.skipif(not config.IR_CONCEPT_LINKS.exists(), reason="사이드카 없음 — make corpus 선행")
def test_sidecar_slugs_all_have_an_axis():
    """적용기가 붙인 개념이 축 미상이면 A2·A3·A8 절제가 그것을 통째로 누락한다(A′ 계약)."""
    if not config.IR_CONCEPT_AXIS.exists():
        pytest.skip("축 지도 없음")
    axis = pd.read_parquet(config.IR_CONCEPT_AXIS)
    amap = dict(zip(axis["slug"], axis["axis_class"]))
    side = pd.read_parquet(config.IR_CONCEPT_LINKS)
    missing = sorted({s for s in side["slug"] if not amap.get(s)})
    assert not missing, f"축 미상 개념 {len(missing)}: {missing[:10]}"


@pytest.mark.skipif(not config.IR_CONCEPT_LINKS.exists(), reason="사이드카 없음 — make corpus 선행")
def test_sidecar_concepts_are_in_corpus():
    corpus = pd.read_parquet(config.IR_CORPUS, columns=["doc_id", "concepts"])
    have = {d: set(c if c is not None else []) for d, c in zip(corpus["doc_id"], corpus["concepts"])}
    side = pd.read_parquet(config.IR_CONCEPT_LINKS)
    bad = [(d, s) for d, s in zip(side["doc_id"], side["slug"]) if s not in have.get(d, set())]
    assert not bad, f"사이드카에 있으나 코퍼스에 없는 링크 {len(bad)}건: {bad[:5]}"
