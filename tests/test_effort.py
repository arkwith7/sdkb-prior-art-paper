"""운용 효율 지표의 계약 검증 (PLAN-036 §10.3).

네 가지를 강제한다 — ① 절단 2×2 교차표의 네 칸 합 = 평가 질의 수 ② K=100 회수 = `make eval`
family Recall@100 ③ 절단 대입 경계(도달 K=D 와 미도달 D+1 의 구분) ④ 결정성(2회 실행 동일).
데이터 의존 테스트는 동결 팔이 없는 클론에서 skip 한다(gitignore 산출물).
"""
from __future__ import annotations

import pytest

from sdkb_paper.analysis import effort as E
from sdkb_paper.analysis.metrics import evaluate

_HAS_ARM = (E.ARM_DIR / f"sys_P1_{E.SPLIT}.txt").exists()
requires_arm = pytest.mark.skipif(not _HAS_ARM, reason=f"동결 팔 없음: {E.ARM_DIR}")


# ── ③ 절단 대입 경계 (합성 데이터 · 데이터 비의존) ──────────────────────────────
def test_k_at_recall_boundary_and_censoring():
    ranked = ["a", "x", "b", "y", "c"]
    pos = {"a", "b", "c"}
    assert E.k_at_recall(ranked, pos, "first", cap=5) == 1
    assert E.k_at_recall(ranked, pos, 0.5, cap=5) == 3      # ⌈0.5·3⌉=2건 → 3위
    assert E.k_at_recall(ranked, pos, 1.0, cap=5) == 5
    # 상한이 도달 지점과 같으면 도달, 하나 모자라면 절단
    assert E.k_at_recall(ranked, pos, 1.0, cap=4) is None
    assert E.k_at_recall(ranked, pos, 1.0, cap=5) == 5
    assert E.k_at_recall(ranked, pos, "first", cap=0) is None


def test_need_at_rounds_up():
    assert E.need_at(1, 0.5) == 1        # |Rel|=1 이면 R=0.5 와 R=1.0 이 같다
    assert E.need_at(2, 0.5) == 1
    assert E.need_at(3, 0.5) == 2
    assert E.need_at(5, 0.8) == 4
    assert E.need_at(4, 0.8) == 4        # ⌈3.2⌉=4 = 전량 → R=1.0 과 동일
    assert E.need_at(9, "first") == 1


def test_median_is_suppressed_when_censoring_reaches_half():
    """절단율 ≥50% 면 중앙값은 대입값이 결정한다 → 숫자를 내지 않는다(§9.4-2)."""
    qids = ["q1", "q2", "q3", "q4"]
    qrel = {q: {"g"} for q in qids}
    runs = {"S": {"q1": ["g"], "q2": ["g"], "q3": ["x"], "q4": ["x"]}}   # 절단 2/4 = 50%
    r = E.effort_at_recall(runs, qrel, qids, "S", "first", cap=1)
    assert r["censored"] == 2
    assert r["median"] is None
    assert r["reach_rate"] == 0.5


# ── ① 2×2 교차표 · ② 회수 일치 · ④ 결정성 (동결 팔 필요) ───────────────────────
@pytest.fixture(scope="module")
def arm():
    return E.load_arm()


@requires_arm
def test_censoring_crosstab_sums_to_n(arm):
    runs, qrel, qids, _ = arm
    for target in E.R_MEDIAN:
        c = E.candidate_reduction(runs, qrel, qids, target)
        assert c["n_both"] + c["only_proposed"] + c["only_baseline"] + c["neither"] == len(qids)
        assert c["wins"] + c["ties"] + c["losses"] == c["n_both"]


@requires_arm
def test_recall_at_100_matches_metrics_module(arm):
    """K=100 열은 `make eval` 의 family Recall@100 과 같아야 한다(§5 성공기준 6)."""
    runs, qrel, qids, _ = arm
    for s in E.MAIN_SYSTEMS:
        ref = evaluate({q: runs[s][q] for q in qids},
                       {q: qrel[q] for q in qids}, ks=(100,))["recall"][100]
        assert E.recall_at_k(runs, qrel, qids, s, 100) == pytest.approx(ref, abs=1e-12)


@requires_arm
def test_p1_reproduces_manuscript_r100(arm):
    """팔이 바뀌면 즉시 실패시킨다 — `runs/`(O′ 팔)는 0.4556 이라 여기서 걸린다(§9.1)."""
    runs, qrel, qids, _ = arm
    assert E.recall_at_k(runs, qrel, qids, "P1", 100) == pytest.approx(0.4849, abs=5e-5)
    assert E.recall_at_k(runs, qrel, qids, "B3_rrf", 100) == pytest.approx(0.4315, abs=5e-5)


@requires_arm
def test_render_is_deterministic(arm):
    runs, qrel, qids, sha = arm
    assert E.render(runs, qrel, qids, sha) == E.render(runs, qrel, qids, sha)


@requires_arm
def test_extra_found_is_censoring_free(arm):
    """추가 발견 건수는 상한과 무관하다 — 정의에 절단이 없음을 계약으로 못박는다."""
    runs, qrel, qids, _ = arm
    e = E.extra_found(runs, qrel, qids, 100)
    assert e["total"] == pytest.approx(e["mean"] * len(qids))
    assert e["gain_queries"] + e["loss_queries"] <= len(qids)
    # 상한 D 는 이 지표의 정의에 등장하지 않는다 — K 만이 인자다
    assert E.extra_found(runs, qrel, qids, 20) != E.extra_found(runs, qrel, qids, 500)
