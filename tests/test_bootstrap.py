"""페어드 부트스트랩 단위 테스트 (analysis/bootstrap · F4)."""
from __future__ import annotations

from sdkb_paper.analysis import bootstrap as B


def test_per_query_recall():
    run = {"q1": ["a", "x", "b"], "q2": ["y", "c"]}
    qrel = {"q1": {"a", "b"}, "q2": {"c"}}
    r = B.per_query_recall(run, qrel, k=2)
    assert r["q1"] == 0.5      # top2 {a,x} ∩ {a,b} = {a}
    assert r["q2"] == 1.0      # top2 {y,c} ∋ c → 1.0
    r1 = B.per_query_recall(run, qrel, k=1)
    assert r1["q2"] == 0.0     # top1 {y} → c 없음


def test_paired_bootstrap_deterministic():
    # A 가 B 보다 모든 질의에서 우월 → Δ>0, CI 하한>0.
    run_a = {f"q{i}": ["a"] for i in range(20)}
    run_b = {f"q{i}": ["z"] for i in range(20)}
    qrel = {f"q{i}": {"a"} for i in range(20)}
    r1 = B.paired_bootstrap(run_a, run_b, qrel, k=1, n=1000, seed=42)
    r2 = B.paired_bootstrap(run_a, run_b, qrel, k=1, n=1000, seed=42)
    assert r1 == r2                        # 시드 고정 → 결정적
    assert r1["delta"] == 1.0 and r1["lb95"] == 1.0
    assert r1["win"] == 20 and r1["loss"] == 0


def test_paired_bootstrap_no_difference():
    run = {f"q{i}": ["a"] for i in range(10)}
    qrel = {f"q{i}": {"a"} for i in range(10)}
    r = B.paired_bootstrap(run, run, qrel, k=1, n=500, seed=1)
    assert r["delta"] == 0.0 and r["lb95"] == 0.0 and r["ub95"] == 0.0


# ── 보조지표 페어드 부트스트랩(N7) — 주지표와 같은 절차를 쓰는지 ─────────────
def test_per_query_metric_dispatch():
    from sdkb_paper.analysis.bootstrap import per_query_metric

    run = {"q1": ["a", "x", "b"], "q2": ["y", "c"]}
    qrel = {"q1": {"a", "b"}, "q2": {"c"}}
    rec = per_query_metric(run, qrel, "recall", k=3)
    ndcg = per_query_metric(run, qrel, "ndcg", k=3)
    mrr = per_query_metric(run, qrel, "mrr", k=3)
    bp = per_query_metric(run, qrel, "bpref", k=3)
    assert rec["q1"] == 1.0 and abs(mrr["q1"] - 1.0) < 1e-12
    assert abs(mrr["q2"] - 0.5) < 1e-12
    assert 0.0 < ndcg["q1"] <= 1.0 and 0.0 < bp["q1"] <= 1.0


def test_per_query_metric_rejects_unknown():
    import pytest

    from sdkb_paper.analysis.bootstrap import per_query_metric
    with pytest.raises(ValueError):
        per_query_metric({"q": ["a"]}, {"q": {"a"}}, "nosuch")


def test_paired_bootstrap_metric_is_deterministic():
    """같은 run·qrel·지표 → 같은 CI (시드 고정 F16)."""
    from sdkb_paper.analysis.bootstrap import paired_bootstrap

    a = {"q1": ["a", "b"], "q2": ["c", "x"]}
    b = {"q1": ["x", "a"], "q2": ["x", "c"]}
    qrel = {"q1": {"a"}, "q2": {"c"}}
    r1 = paired_bootstrap(a, b, qrel, k=2, metric="ndcg", n=200)
    r2 = paired_bootstrap(a, b, qrel, k=2, metric="ndcg", n=200)
    assert r1 == r2
    assert r1["delta"] > 0        # a 가 정답을 더 위에 둔다
