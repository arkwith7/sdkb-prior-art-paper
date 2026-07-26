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


def test_load_run_parses_rank_order(tmp_path):
    p = tmp_path / "run.txt"
    p.write_text("q1 Q0 d2 2 0.5 tag\nq1 Q0 d1 1 0.9 tag\n", encoding="utf-8")
    run = metrics.load_run(p)
    assert run["q1"] == ["d1", "d2"]    # rank 순 정렬
