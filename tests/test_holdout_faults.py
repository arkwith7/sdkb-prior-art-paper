"""W9 홀드아웃 결함·H1‴ 판정의 계약 (PLAN-025 §5-1 · 사전등록 동결 `a474126`).

여기서 지키는 명제는 넷이다.

1. **홀드아웃이 진짜 홀드아웃인가** — 새 rep 이 1차(rep 0–2)와 같은 결함 그래프를 내면 "아직
   판정한 적 없는 인스턴스"라는 전제가 거짓이 된다.
2. **교차성이 결과가 아니라 구성인가** — 신규 결함군의 조작 술어가 주 태스크(pa) CQ 가 읽는
   술어와 겹치면, T3 단독검출은 발견이 아니라 설계 실패다. 목록은 문서가 아니라 `.rq` 에서 뽑는다.
3. **결함이 설계대로 무증상인가** — 간선 수 보존·range 클래스 보존이 깨지면 L1(SHACL)이 먼저
   잡아버려 T3 를 잴 무대 자체가 사라진다.
4. **판정식이 조용히 관대해지지 않는가** — 위양성 임계·단측 방향·정지 규칙의 경계.
"""
from __future__ import annotations

import re

import pytest
from pyoxigraph import NamedNode, Quad, Store

from sdkb_paper import config
from sdkb_paper.analysis import faults as FA
from sdkb_paper.validate import cq_runner as CQ
from sdkb_paper.validate import fault_inject as FI

ONT = FI.ONT
RDFT = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
HOLDOUT_REPS = tuple(range(config.FAULT_HOLDOUT_REP_OFFSET,
                           config.FAULT_HOLDOUT_REP_OFFSET + config.FAULT_HOLDOUT_REPS))


def _expert_toy() -> Store:
    """전문가 3 · 공정 3(같은 타입) · 사례 3 · 결함모드 3 · 장비 2 · 벤더 2 의 최소 그래프."""
    s = Store()

    def q(a, b, c):
        s.add(Quad(NamedNode(ONT + a), NamedNode(b if b.startswith("http") else ONT + b),
                   NamedNode(ONT + c)))

    for i in (1, 2, 3):
        q(f"e{i}", RDFT, "Expert")
        q(f"p{i}", RDFT, "Process")
        q(f"e{i}", "hasProcessExpertise", f"p{i}")
        q(f"c{i}", RDFT, "ExpertCase")
        q(f"fm{i}", RDFT, "FailureMode")
        q(f"c{i}", "caseFailureMode", f"fm{i}")
    for i in (1, 2):
        q(f"eq{i}", RDFT, "Equipment")
        q(f"v{i}", RDFT, "Vendor")
        q(f"eq{i}", "providedBy", f"v{i}")
    return s


def _pred_pairs(store: Store, pred: str) -> set[tuple[str, str]]:
    return {(str(x.subject), str(x.object))
            for x in store.quads_for_pattern(None, NamedNode(ONT + pred), None, None)}


# --- (b) 홀드아웃 rep 이 1차와 겹치지 않는다 ----------------------------------
def test_holdout_reps_do_not_overlap_first_round():
    """rep 이 겹치면 `seed_for` 가 같은 시드를 내고, 홀드아웃은 4회차 재판정이 된다."""
    assert HOLDOUT_REPS == (3, 4, 5)
    first = {FI.seed_for(k, s, r)
             for k in FA.HOLDOUT_KEYS for s in FI.STRENGTHS for r in (0, 1, 2)}
    held = {FI.seed_for(k, s, r)
            for k in FA.HOLDOUT_KEYS for s in FI.STRENGTHS for r in HOLDOUT_REPS}
    assert first.isdisjoint(held)
    assert len(held) == len(FA.HOLDOUT_KEYS) * len(FI.STRENGTHS) * len(HOLDOUT_REPS)


def test_holdout_job_grid_is_72_instances():
    """축 A 18 + 축 B 27 + 정상 델타 27 = 72 (PLAN-025 §3.3)."""
    cross = [k for k in FA.HOLDOUT_KEYS if FI.BY_KEY[k].cross_task]
    normal = [k for k in FA.HOLDOUT_KEYS if k in FA.NORMAL_KEYS]
    assert len(cross) == 5 and len(normal) == 3
    assert len(cross) * 3 * 3 == 45 and len(FA.HOLDOUT_KEYS) * 3 * 3 == 72


def test_new_faults_are_registered_as_cross_task():
    """교차 라벨이 빠지면 H1‴ 판정 분모(45)에서 조용히 빠진다."""
    for k in FA.HOLDOUT_NEW_KEYS:
        assert FI.BY_KEY[k].cross_task, k
        assert FI.BY_KEY[k].expected.startswith("T3")


# --- (e) pa 술어 ∩ 신규 조작 술어 = ∅ (문서가 아니라 `.rq` 가 원천) ------------
def test_new_fault_predicates_are_disjoint_from_pa_suite():
    """교차성은 결과가 아니라 **구성**이다 — 주 태스크 CQ 가 읽는 술어를 건드리면 안 된다."""
    pa = CQ.suite_predicates()["pa"]
    assert len(pa) == 20, "pa 스위트 술어 집합이 동결(20개)에서 벗어났다 — 사전등록 재확인"
    for key, preds in FI.CROSS_FAULT_PREDICATES.items():
        assert set(preds).isdisjoint(pa), f"{key} 가 pa 술어를 건드린다: {set(preds) & pa}"


def test_new_fault_predicates_hit_their_target_suite():
    """무해한 술어만 골라 '아무 데도 안 걸리는 결함'을 만들면 판별력 검정이 공허해진다."""
    by_suite = CQ.suite_predicates()
    assert set(FI.CROSS_FAULT_PREDICATES["F13"]) <= by_suite["em"]
    assert set(FI.CROSS_FAULT_PREDICATES["F14"]) <= by_suite["em"]
    assert set(FI.CROSS_FAULT_PREDICATES["F15"]) <= by_suite["core"]


# --- (f) 조작 술어가 상류 스냅샷에 실재한다 (어휘 발명 재발 차단) --------------
def test_manipulated_predicates_exist_upstream():
    """v1 의 `involvesProblem` 은 존재하지 않는 어휘였다(PLAN-025 §0-1) — 두 번은 없다."""
    ttl = "\n".join(p.read_text(encoding="utf-8")
                    for p in sorted(config.EXTERNAL_SDKB.glob("*.ttl")))
    for key, preds in FI.CROSS_FAULT_PREDICATES.items():
        for p in preds:
            assert re.search(rf"ont:{p}\s+a\s+owl:ObjectProperty", ttl), \
                f"{key} 의 조작 술어 {p} 가 상류 스냅샷에 없다 (CLAUDE.md §1-6)"


# --- (c) 간선 수 보존 · (g) range 클래스 보존 ---------------------------------
@pytest.mark.parametrize("key,pred", [("F13", "hasProcessExpertise"),
                                      ("F14", "caseFailureMode"),
                                      ("F15", "providedBy")])
def test_new_faults_preserve_edge_count(key, pred):
    """링크 **수**가 변하면 결함이 '분포 왜곡'이 아니라 '삭제'가 되어 표적 층이 달라진다."""
    s = _expert_toy()
    before = _pred_pairs(s, pred)
    stats = FI.BY_KEY[key].inject(s, 1.0, 11)
    after = _pred_pairs(s, pred)
    assert len(before) == len(after), f"{key} 가 간선 수를 바꿨다"
    assert after != before, f"{key} 가 아무것도 바꾸지 않았다 — 결함 없는 결함 주입"
    assert stats["n_affected"] > 0


def test_f15_flips_direction():
    s = _expert_toy()
    before = _pred_pairs(s, "providedBy")
    FI.BY_KEY["F15"].inject(s, 1.0, 11)
    assert _pred_pairs(s, "providedBy") == {(o, sub) for sub, o in before}


@pytest.mark.parametrize("key,pred", [("F13", "hasProcessExpertise"),
                                      ("F14", "caseFailureMode")])
def test_rewire_preserves_object_class(key, pred):
    """range 가 깨지면 L1(SHACL)이 먼저 잡아 T3 를 잴 무대가 사라진다 — 그건 교차결함이 아니다."""
    s = _expert_toy()
    types_before = {str(q.subject): FI._type_sig(s, q.subject)
                    for q in s.quads_for_pattern(None, NamedNode(RDFT), None, None)}
    FI.BY_KEY[key].inject(s, 1.0, 11)
    for _, o in _pred_pairs(s, pred):
        assert types_before.get(o), f"{key} 가 타입 없는 개체로 재배선했다: {o}"
    objs = {o for _, o in _pred_pairs(s, pred)}
    assert len({types_before[o] for o in objs}) == 1     # 같은 타입 서명 안에서만 움직였다


def test_f13_concentrates_on_hubs():
    """허브 집중화는 **서로 다른 객체 수**를 줄인다 — 그게 조인 분포 붕괴의 정의다."""
    s = _expert_toy()
    before = len({o for _, o in _pred_pairs(s, "hasProcessExpertise")})
    FI.BY_KEY["F13"].inject(s, 1.0, 11)
    after = len({o for _, o in _pred_pairs(s, "hasProcessExpertise")})
    assert after < before and after <= FI.HUB_K


def test_new_faults_are_deterministic():
    """같은 (결함·강도·시드)는 언제 돌려도 같은 그래프 — 매트릭스 재현의 전제."""
    for key in FA.HOLDOUT_NEW_KEYS:
        def run():
            s = _expert_toy()
            FI.BY_KEY[key].inject(s, 0.5, FI.seed_for(key, 0.05, 3))
            return sorted(f"{q.subject} {q.predicate} {q.object}" for q in s)
        assert run() == run(), key


# --- (a)(d) 판정식 · 정지 규칙 ------------------------------------------------
def _inst(fault, *, l3=False, t3=False, cross=True, leak=False, rep=3, tau=0.05):
    """재판정 산출물 한 줄의 최소 형태 (`_merged_layers` 가 읽는 모양)."""
    v1 = {L: False for L in FA.LAYERS}
    v1["leak"] = leak
    return {"fault": fault, "label": fault, "expected": "T3", "cross_task": cross,
            "strength": 0.05, "rep": rep, "v1": v1,
            "v2_by_tau": {f"{t:.2f}": {"L3_all": l3 or t3, "L3_pa": l3, "T3": t3,
                                       "cross_regressed_cqs": [], "pa_regressed_cqs": []}
                          for t in config.CQ_TAU_GRID}}


def _res(instances, invariant_holds=True):
    return {"tau_main": config.CQ_TAU, "taus": list(config.CQ_TAU_GRID),
            "instances": instances,
            "invariant": {f"{t:.2f}": {"holds": invariant_holds, "n_violation":
                                       0 if invariant_holds else 1, "n_checked": len(instances)}
                          for t in config.CQ_TAU_GRID}}


def test_t3_only_excludes_leak_detection():
    """누출감사 발화도 '다른 층 검출'이다(§3.4) — 안 세면 T3 단독검출이 부풀려진다."""
    v = FA._holdout_verdict([_inst("F13", t3=True, leak=True),
                             _inst("F14", t3=True)], config.CQ_TAU)
    assert v["n_t3_detected"] == 2 and v["n_t3_only"] == 1


def test_one_sided_mcnemar_rejects_reverse_direction():
    """방향은 사전 지정(T3 우세)이다 — 반대로 나오면 유의해지지 않고 기각된다."""
    fwd = FA.mcnemar_one_sided([(False, True)] * 8 + [(True, False)])
    rev = FA.mcnemar_one_sided([(True, False)] * 8 + [(False, True)])
    assert fwd["direction"] == "T3" and fwd["p"] < 0.05
    assert rev["direction"] == "L3" and rev["p"] > 0.05


def test_holdout_supported_requires_all_three_conditions():
    cross = [_inst("F13", t3=True) for _ in range(9)] + [_inst("F11", l3=True, t3=True)]
    normals = [_inst("N01", cross=False) for _ in range(27)]
    j = FA.judge_holdout(_res(cross + normals))
    assert (j["main"]["c1_t3_only"], j["main"]["c2_mcnemar"], j["c3_false_positive"]) == \
           (True, True, True)
    assert j["supported"] and j["verdict"] == "지지"


def test_false_positive_threshold_boundary_is_5_percent():
    """1/27 = 3.7% 는 통과, 2/27 = 7.4% 는 기각 — 임계는 config 동결값이다."""
    cross = [_inst("F13", t3=True) for _ in range(9)]
    normals = [_inst("N01", cross=False) for _ in range(27)]
    ok = FA.judge_holdout(_res(cross + normals[:26] + [_inst("N01", cross=False, l3=True)]))
    bad = FA.judge_holdout(_res(cross + normals[:25]
                                + [_inst("N01", cross=False, l3=True),
                                   _inst("N02", cross=False, t3=True)]))
    assert ok["c3_false_positive"] and ok["supported"]
    assert not bad["c3_false_positive"] and not bad["supported"]
    assert config.FAULT_FP_MAX_RATE == 0.05


def test_no_t3_only_instance_rejects_even_if_significant():
    """T3 가 잡아도 다른 층이 같이 잡으면 '주 태스크 감시가 놓친 회귀'가 아니다."""
    cross = [_inst("F13", l3=True, t3=True) for _ in range(9)]
    j = FA.judge_holdout(_res(cross + [_inst("N01", cross=False) for _ in range(27)]))
    assert not j["main"]["c1_t3_only"] and not j["supported"]


def test_replicate_and_novel_axes_are_reported_separately():
    """복제 축과 일반화 축이 갈리면 갈린 대로 보고한다(§3.4 보조)."""
    cross = ([_inst("F11", l3=True) for _ in range(9)]
             + [_inst("F13", t3=True) for _ in range(9)])
    j = FA.judge_holdout(_res(cross + [_inst("N01", cross=False) for _ in range(27)]))
    assert j["replicate_only"]["n_t3_only"] == 0
    assert j["novel_only"]["n_t3_only"] == 9


def test_kill_switch_blocks_judgment_on_invariant_violation():
    """검출력 불변량이 깨지면 판정하지 않는다 — 수치를 내면 그게 사후 해석의 재료가 된다."""
    insts = [_inst("F13", t3=True) for _ in range(9)]
    j = FA.holdout_judgment(_res(insts, invariant_holds=False))
    assert not j["kill_switch"]["pass"] and j["main"] is None and j["by_tau"] == {}
    assert FA.holdout_judgment(_res(insts))["main"] is not None


def test_layers_are_disjoint_and_cover_all_cqs():
    """L3∩T3=∅ · L3∪T3 = 스위트 전량. 하나라도 어긋나면 T3 단독검출의 의미가 무너진다."""
    l3, t3 = set(config.L3_SUITES), set(config.T3_SUITES)
    assert l3.isdisjoint(t3)
    assert l3 | t3 == set(config.CQ_SUITES)   # 스위트 정본은 config(=프로파일 파생)다
