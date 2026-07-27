"""M4 온톨로지팔 단위·경계 테스트 (PLAN-018 §7.3) — Bedrock·대용량 데이터 무관 순수 로직.

검증: ConceptOverlap·PathSim(Wu-Palmer)·IpcSim · F10 후보 마스크(시점·family·self) ·
축 필터(ablation) · P0★ 재랭크 결정성 · 격자(simplex) · Holm · 누출/경계 계약.
"""
from __future__ import annotations

import numpy as np
import pytest

from sdkb_paper.retrieval import systems as S
from sdkb_paper.retrieval.candidate import CandidateMask, _to_int
from sdkb_paper.retrieval.ontology_rerank import OntologyFeatures


# --- 가짜 피처 객체(디스크 미접근) -------------------------------------------
def _fake_feats() -> OntologyFeatures:
    f = object.__new__(OntologyFeatures)
    f.doc_ids = ["q", "d1", "d2", "d3"]
    f.row = {d: i for i, d in enumerate(f.doc_ids)}
    f.concepts = [frozenset({"etch", "plasma_etch"}), frozenset({"etch"}),
                  frozenset({"cmos"}), frozenset()]
    f.ipc = [frozenset({"H01L21-02"}), frozenset({"H01L21-311"}),
             frozenset({"G03F7-20"}), frozenset()]
    f.cpc = [frozenset(), frozenset(), frozenset(), frozenset()]
    # etch·plasma_etch = SubProcess(자식 Process), cmos = Device
    f.axis = {"etch": "SubProcess", "plasma_etch": "SubProcess", "cmos": "Device"}
    f.depth = {"Process": 1, "SubProcess": 2, "Device": 1}
    f._parent = {"SubProcess": ["Process"]}
    f._ancestors.cache_clear() if hasattr(f._ancestors, "cache_clear") else None
    f.inv_concept, f.inv_ipc = {}, {}
    for i, cs in enumerate(f.concepts):
        for c in cs:
            f.inv_concept.setdefault(c, set()).add(i)
    for i, cs in enumerate(f.ipc):
        for c in cs:
            for p in f._ipc_prefixes(c):
                if len(p) >= 4:
                    f.inv_ipc.setdefault(p, set()).add(i)
    return f


# --- ConceptOverlap -----------------------------------------------------------
def test_concept_overlap_jaccard():
    a, b = frozenset({"etch", "plasma_etch"}), frozenset({"etch"})
    assert OntologyFeatures.concept_overlap(a, b) == pytest.approx(1 / 2)  # |∩|1/|∪|2
    assert OntologyFeatures.concept_overlap(a, a) == 1.0
    assert OntologyFeatures.concept_overlap(a, frozenset()) == 0.0
    assert OntologyFeatures.concept_overlap(a, frozenset({"cmos"})) == 0.0


# --- PathSim (Wu-Palmer) ------------------------------------------------------
def test_pathsim_same_concept_is_one():
    f = _fake_feats()
    assert f.path_sim(frozenset({"etch"}), frozenset({"etch"})) == 1.0


def test_pathsim_same_axis_class_high_diff_axis_zero():
    f = _fake_feats()
    # etch vs plasma_etch: 같은 SubProcess 클래스 → WP=2·2/(2+2)=1
    assert f.path_sim(frozenset({"etch"}), frozenset({"plasma_etch"})) == pytest.approx(1.0)
    # etch(SubProcess) vs cmos(Device): 공통조상 없음 → 0
    assert f.path_sim(frozenset({"etch"}), frozenset({"cmos"})) == 0.0


def test_pathsim_empty_is_zero():
    f = _fake_feats()
    assert f.path_sim(frozenset(), frozenset({"etch"})) == 0.0


# --- IpcSim (접두 계층) -------------------------------------------------------
def test_ipc_prefixes_hierarchy():
    p = OntologyFeatures._ipc_prefixes("H01L21-02")
    assert {"H", "H01", "H01L", "H01L21", "H01L21-02"} <= p


def test_ipc_sim_shared_subclass():
    f = _fake_feats()
    # H01L21-02 vs H01L21-311: 섹션·클래스·서브클래스·메인그룹 공유(H,H01,H01L,H01L21)
    s = f.ipc_sim(frozenset({"H01L21-02"}), frozenset({"H01L21-311"}))
    assert 0.0 < s < 1.0
    # 다른 섹션(H vs G)은 훨씬 낮다
    s2 = f.ipc_sim(frozenset({"H01L21-02"}), frozenset({"G03F7-20"}))
    assert s2 < s
    assert f.ipc_sim(frozenset(), frozenset({"H01L21-02"})) == 0.0


# --- F10 후보 마스크 ----------------------------------------------------------
def _fake_mask() -> CandidateMask:
    m = object.__new__(CandidateMask)
    m.doc_ids = ["q", "d_past", "d_future", "d_samefam", "d_nodate"]
    m.row = {d: i for i, d in enumerate(m.doc_ids)}
    m.pub_int = np.array([0, 20100101, 20990101, 20100101, 0], dtype=np.int64)
    m.family = np.array(["fq", "f1", "f2", "fq", "f3"], dtype=object)
    m.n_pub_missing = 2
    m.q_filing = {"q": 20150101}
    m.q_family = {"q": "fq"}
    return m


def test_candidate_mask_time_family_self():
    m = _fake_mask()
    assert m.is_allowed("q", "d_past")        # 공개<출원·타family
    assert not m.is_allowed("q", "d_future")  # 미래 공개 → 배제
    assert not m.is_allowed("q", "d_samefam") # 같은 family → 배제
    assert not m.is_allowed("q", "q")         # 자기 → 배제
    assert m.is_allowed("q", "d_nodate")      # 공개일 결측 → 시점유효로 포함(보수적)


def test_candidate_allowed_array_matches_scalar():
    m = _fake_mask()
    arr = m.allowed_array("q")
    for i, d in enumerate(m.doc_ids):
        assert bool(arr[i]) == m.is_allowed("q", d)


def test_to_int_parsing():
    assert _to_int("2015-01-01") == 20150101
    assert _to_int(None) == 0
    assert _to_int("") == 0
    assert _to_int(float("nan")) == 0


# --- 축 필터(ablation) --------------------------------------------------------
def test_filter_concepts_by_axis():
    f = _fake_feats()
    cs = frozenset({"etch", "cmos"})   # SubProcess + Device
    kept = S._filter_concepts(f, cs, S.ALL_AXES - S.AXES_PROCESS_DEVICE)
    assert kept == frozenset()         # 둘 다 process/device 축 → 전부 제거
    kept2 = S._filter_concepts(f, cs, S.ALL_AXES - S.AXES_MATERIAL_EQUIP_FAILURE)
    assert kept2 == cs                 # 재료·고장 축 아님 → 유지


def test_onto_score_toggles():
    f = _fake_feats()
    cfg_full = S.OntoConfig(alpha=0.5, w_c=0.5, w_h=0.5, w_i=0.0)
    s_full = S._onto_score(f, 0, 1, cfg_full)          # q vs d1
    assert s_full > 0
    cfg_nopath = S.OntoConfig(alpha=0.5, w_c=0.5, w_h=0.5, w_i=0.0, use_path=False)
    assert S._onto_score(f, 0, 1, cfg_nopath) < s_full  # 경로항 제거 → 감소


# --- P0★ 재랭크 결정성 + 경계 -------------------------------------------------
def _fake_mask_all_allowed(doc_ids) -> CandidateMask:
    m = object.__new__(CandidateMask)
    m.doc_ids = list(doc_ids)
    m.row = {d: i for i, d in enumerate(m.doc_ids)}
    m.pub_int = np.zeros(len(doc_ids), dtype=np.int64)
    m.family = np.array([f"f{i}" for i in range(len(doc_ids))], dtype=object)
    m.q_filing, m.q_family = {"q": 0}, {"q": "fq"}
    return m


def test_rerank_promotes_concept_match_and_is_deterministic(monkeypatch):
    f = _fake_feats()
    m = _fake_mask_all_allowed(f.doc_ids)
    monkeypatch.setattr(S, "_query_features", lambda feats: {"q": 0})
    base = {"q": ["d3", "d2", "d1"]}   # d1(개념일치)이 꼴찌
    cfg = S.OntoConfig(alpha=1.0, w_c=1.0, w_h=0.0, w_i=0.0)  # 순수 개념
    r = S.rerank_p0(base, f, m, cfg, pool_k=10, k=10)
    assert r["q"][0] == "d1"           # 개념 겹치는 d1 이 1위로 승격
    assert S.rerank_p0(base, f, m, cfg, pool_k=10, k=10) == r  # 결정적


# --- 격자·Holm ----------------------------------------------------------------
def test_simplex_grid_sums_to_one():
    from sdkb_paper.analysis.ontology_eval import simplex_grid
    g = simplex_grid(0.25)
    assert all(abs(sum(w) - 1.0) < 1e-9 for w in g)
    assert (1.0, 0.0, 0.0) in g and (0.0, 0.0, 1.0) in g
    assert len(g) == 15


def test_grid_configs_folds_alpha_zero():
    from sdkb_paper.analysis.ontology_eval import grid_configs
    cfgs = grid_configs()
    zeros = [c for c in cfgs if c[0] == 0.0]
    assert len(zeros) == 1              # α=0 은 1개로 접힘
    assert len(cfgs) == 1 + 4 * 15      # α=0 1개 + (0.25,.5,.75,1)×15


def test_holm_ordering():
    from sdkb_paper.analysis.ablation import holm
    rej = holm([("a", 0.001), ("b", 0.04), ("c", 0.9)], alpha=0.05)
    assert rej["a"] is True            # 0.001 < 0.05/3
    assert rej["c"] is False


# --- 누출/경계 계약 -----------------------------------------------------------
def test_concept_props_not_leakage():
    from sdkb_paper.corpus.assemble import CONCEPT_PROPS, FORBIDDEN
    assert set(CONCEPT_PROPS).isdisjoint(set(FORBIDDEN))


def test_features_load_no_forbidden_columns():
    """OntologyFeatures 가 읽는 컬럼에 정답 파생·금지 간선이 없다(경계 계약)."""
    import inspect
    src = inspect.getsource(OntologyFeatures.__init__)
    for bad in ("qrel", "relevance", "is_examiner_positive", "hasPriorArt", "NoveltyScore"):
        assert bad not in src
