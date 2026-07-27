"""Hybrid RRF 융합 단위 테스트 (retrieval/hybrid) — Bedrock 무관 순수 로직."""
from __future__ import annotations

from sdkb_paper.retrieval.hybrid import rrf


def test_rrf_combines_two_runs():
    # runA: [a, b] · runB: [b, c] · c=60.
    # a: 1/61 · b: 1/62(A)+1/61(B) · c: 1/62 → 순위 b > a > c.
    runs = [{"q": ["a", "b"]}, {"q": ["b", "c"]}]
    fused = rrf(runs, k=10, c=60)
    assert fused["q"][0] == "b"
    assert fused["q"] == ["b", "a", "c"]


def test_rrf_deterministic_tiebreak():
    # a,b 동점(각 1위 한 번) → doc_id 사전순 a<b.
    runs = [{"q": ["a"]}, {"q": ["b"]}]
    assert rrf(runs, k=10)["q"] == ["a", "b"]


def test_rrf_union_of_queries():
    runs = [{"q1": ["a"]}, {"q2": ["b"]}]
    fused = rrf(runs, k=10)
    assert set(fused) == {"q1", "q2"}
