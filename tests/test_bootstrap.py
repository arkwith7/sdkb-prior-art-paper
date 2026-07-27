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
