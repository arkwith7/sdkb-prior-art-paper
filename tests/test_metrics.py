"""IR 평가 지표 단위 테스트 (PLAN-018 §6 · analysis/metrics).

토이 run/qrel 로 Recall@K·Success@K·MRR·분모(정답≥1 질의만) 를 결정적으로 검증한다.
"""
from __future__ import annotations

from sdkb_paper.analysis import metrics


def test_evaluate_basic():
    # q1: 정답 {a,b}, 순위 [a, x, b, y] → R@2=0.5(a만) R@4=1.0 · MRR=1(1위 a)
    # q2: 정답 {c},   순위 [x, y, c]    → R@2=0(top2 무), R@4=1.0 · MRR=1/3
    # q3: 정답 없음 → 평가 분모에서 제외
    run = {"q1": ["a", "x", "b", "y"], "q2": ["x", "y", "c"], "q3": ["z"]}
    qrel = {"q1": {"a", "b"}, "q2": {"c"}, "q3": set()}
    res = metrics.evaluate(run, qrel, ks=(2, 4))
    assert res["n_queries_evaluated"] == 2          # q3 제외
    assert res["recall"][2] == (0.5 + 0.0) / 2
    assert res["recall"][4] == (1.0 + 1.0) / 2
    assert res["success"][2] == (1 + 0) / 2
    assert res["success"][4] == 1.0
    assert abs(res["mrr"] - (1.0 + 1 / 3) / 2) < 1e-9


def test_evaluate_missing_query_in_run():
    # 정답은 있으나 run 에 없는 질의 → recall 0 으로 집계(분모엔 포함)
    run = {"q1": ["a"]}
    qrel = {"q1": {"a"}, "q2": {"b"}}
    res = metrics.evaluate(run, qrel, ks=(1,))
    assert res["n_queries_evaluated"] == 2
    assert res["recall"][1] == (1.0 + 0.0) / 2


def test_family_fold_then_cut():
    # a,b 는 같은 family F1; c 는 F2; 정답 {a, c}.
    # 순위 [a, b, x, c]: family 로 접으면 [F1, x, F2] (b 는 F1 중복 → 제거).
    # family top-2 = {F1, x} → 정답 family {F1, F2} 중 F1 만 → R@2 = 0.5.
    fam = {"a": "F1", "b": "F1", "c": "F2"}
    run = {"q1": ["a", "b", "x", "c"]}
    qrel = {"q1": {"a", "c"}}
    res = metrics.evaluate(run, qrel, ks=(2, 3), family=fam)
    assert res["level"] == "family"
    # 정답 family = {F1, F2} (a,c 접힘 · 서로 다름) → 분모 2
    assert res["recall"][2] == 0.5          # top-2 family {F1,x} ∩ {F1,F2} = {F1}
    assert res["recall"][3] == 1.0          # top-3 family {F1,x,F2} ⊇ {F1,F2}


def test_family_merges_positives_into_one():
    # 정답 두 문서가 같은 family → 분모 1, 한 번 회수로 R=1.
    fam = {"a": "F1", "b": "F1"}
    run = {"q1": ["a", "z"]}
    qrel = {"q1": {"a", "b"}}
    res = metrics.evaluate(run, qrel, ks=(1,), family=fam)
    assert res["recall"][1] == 1.0          # family 분모 1, a 로 F1 회수


def test_fold_dedups_first_occurrence():
    fam = {"a": "F", "b": "F", "c": "G"}
    assert metrics._fold(["a", "b", "c", "a"], fam) == ["F", "G"]
    # 지도에 없는 doc 은 자기자신 family
    assert metrics._fold(["a", "q"], fam) == ["F", "q"]


def test_load_run_parses_rank_order(tmp_path):
    p = tmp_path / "run.txt"
    p.write_text("q1 Q0 d2 2 0.5 tag\nq1 Q0 d1 1 0.9 tag\n", encoding="utf-8")
    run = metrics.load_run(p)
    assert run["q1"] == ["d1", "d2"]    # rank 순 정렬


# ── nDCG@20(이진 이득) · bpref(retrieved-as-judged) — N7 보조지표 ──────────────
def test_ndcg_perfect_and_empty():
    """정답이 전부 최상위면 1.0 · 회수 0이면 0.0."""
    assert abs(metrics.ndcg_at_k(["a", "b", "x"], {"a", "b"}, k=20) - 1.0) < 1e-12
    assert metrics.ndcg_at_k(["x", "y"], {"a"}, k=20) == 0.0


def test_ndcg_discounts_lower_ranks():
    """같은 회수라도 순위가 낮으면 값이 작아야 한다 — 상위 정밀도 지표의 요건."""
    hi = metrics.ndcg_at_k(["a", "x", "y"], {"a"}, k=20)
    lo = metrics.ndcg_at_k(["x", "y", "a"], {"a"}, k=20)
    assert hi > lo > 0.0
    assert abs(hi - 1.0) < 1e-12                      # 1위 = 이상 DCG


def test_ndcg_ideal_capped_at_k():
    """정답이 k 보다 많으면 이상 DCG 는 k 개로 자른다(1.0 을 넘지 않는다)."""
    ranked = [str(i) for i in range(5)]
    v = metrics.ndcg_at_k(ranked, set(ranked), k=3)
    assert abs(v - 1.0) < 1e-12


def test_bpref_penalizes_nonrelevant_above():
    """양성 위에 비양성이 많이 낄수록 감점 — 양성 전용 qrel 관례."""
    clean = metrics.bpref(["a", "b", "x", "y"], {"a", "b"})
    dirty = metrics.bpref(["x", "y", "a", "b"], {"a", "b"})
    assert abs(clean - 1.0) < 1e-12
    assert 0.0 <= dirty < clean


def test_bpref_unretrieved_positive_contributes_zero():
    """회수되지 않은 양성은 0 기여 — 분모는 정답 수 그대로."""
    assert abs(metrics.bpref(["a"], {"a", "b"}) - 0.5) < 1e-12
    assert metrics.bpref([], {"a"}) == 0.0
    assert metrics.bpref(["x"], set()) == 0.0


def test_evaluate_exposes_aux_metrics():
    """evaluate() 가 nDCG·bpref 를 함께 낸다(§6.2 표의 열)."""
    run = {"q1": ["a", "x"], "q2": ["y", "c"]}
    qrel = {"q1": {"a"}, "q2": {"c"}}
    res = metrics.evaluate(run, qrel, ks=(2,))
    assert f"ndcg@{metrics.NDCG_K}" in res and "bpref" in res
    assert 0.0 < res[f"ndcg@{metrics.NDCG_K}"] <= 1.0
    assert 0.0 < res["bpref"] <= 1.0
