"""축1 3단 증분표: B0(BM25) → B2(Dense) → B3(RRF) → P1(온톨로지) · family R@100.

모든 시스템을 같은 조건(F10 CandidateMask · POOL_K 절단 · family fold)에서 비교한다.
기존 동결 산출물(run 파일 · qrel · split · family map)만 읽는다. 새 검색 없음.

사용: python increment_table.py [dev|test]
"""
from __future__ import annotations

import sys

import pandas as pd

from sdkb_paper import config
from sdkb_paper.analysis.bootstrap import paired_bootstrap
from sdkb_paper.analysis.metrics import evaluate, load_qrel, load_run
from sdkb_paper.analysis.ontology_eval import (
    component_cache_p1,
    rerank_p1,
)
from sdkb_paper.collect.bq_family_ir import load_family_map
from sdkb_paper.retrieval import systems as S
from sdkb_paper.retrieval.bm25 import RUN_B0
from sdkb_paper.retrieval.candidate import CandidateMask
from sdkb_paper.retrieval.dense import RUN_B2
from sdkb_paper.retrieval.hybrid import RUN_B3
from sdkb_paper.retrieval.ontology_rerank import OntologyFeatures

SPLIT = sys.argv[1] if len(sys.argv) > 1 else "test"
K = 100
P1_TAU, P1_ALPHA, P1_W4 = 0.7, 0.75, (0.25, 0.0, 0.25, 0.5)

fam = load_family_map()
qrel = load_qrel()
sp = pd.read_parquet(config.IR_SPLIT)
keep = set(sp.loc[sp["split"] == SPLIT, "doc_id"])
qrel = {q: p for q, p in qrel.items() if q in keep}
qids = [q for q, p in qrel.items() if p]
print(f"[{SPLIT}] 정답≥1 질의 {len(qids)}")

mask = CandidateMask()


def masked(run_path):
    """run → 질의별 마스킹 후 POOL_K 절단(재랭크 팔과 동일한 후보 조건)."""
    r = load_run(run_path)
    return {q: [d for d in r.get(q, []) if mask.is_allowed(q, d)][: S.POOL_K] for q in qids}


runs = {
    "B0_bm25": masked(RUN_B0),
    "B2_dense": masked(RUN_B2),
    "B3_rrf": masked(RUN_B3),
}

# P1 = B3 풀 위 온톨로지 재랭크 (τ=0.7 · α=0.75 · w=(0.25,0,0.25,0.5))
feats = OntologyFeatures()
b3_raw = load_run(RUN_B3)
from sdkb_paper.retrieval.feature_coverage import FeatureCoverageIndex  # noqa: E402

pool_docs = set(qids)
for q in qids:
    pool_docs.update(runs["B3_rrf"][q])
fc = FeatureCoverageIndex(restrict_docs=pool_docs)
cache = component_cache_p1(feats, mask, b3_raw, qids, fc)
ti = list((0.5, 0.6, 0.7, 0.8)).index(P1_TAU)
runs["P1_onto"] = rerank_p1(cache, ti, P1_ALPHA, P1_W4, k=1000)

print(f"\n[{SPLIT} · family Recall@{K} · {len(qids)}질의]")
r100 = {}
for name, run in runs.items():
    r = evaluate(run, qrel, ks=(K,), family=fam)
    r100[name] = r["recall"][K]
    print(f"  {name:10} R@{K}={r100[name]:.4f}")

PAIRS = [
    ("B2_dense", "B0_bm25", "Dense 단독 vs BM25"),
    ("B3_rrf", "B0_bm25", "① 의미검색 추가 (B0→B3)"),
    ("B3_rrf", "B2_dense", "B3 vs Dense"),
    ("P1_onto", "B3_rrf", "② 온톨로지 추가 (B3→P1)"),
    ("P1_onto", "B0_bm25", "누적 (B0→P1)"),
]
print("\n  ─ 페어드 부트스트랩 10k (family R@100) ─")
for a, b, label in PAIRS:
    r = paired_bootstrap(runs[a], runs[b], qrel, k=K, family=fam)
    print(
        f"  {label:28} Δ={r['delta']:+.4f} CI[{r['lb95']:+.4f},{r['ub95']:+.4f}]"
        f" p={r['p_two_sided']:.3f} 승/패/동 {r['win']}/{r['loss']}/{r['tie']}"
    )
