"""IR 평가 지표 (PLAN-018 §6 · 원고 §5.1).

run(순위) × qrel(정답) → Recall@K·Success@K·MRR@K. 여기서는 **문서수준**(family 집계 이전).
family-level Recall@100(F1 주지표)은 family 그룹핑(B2 · PLAN-017 계층 A) 완료 후 M3 에서 얹는다.

- **경계(PLAN-018 §2):** analysis 는 순위를 만들지 않는다 — run 파일을 읽어 평가만 한다. qrel 열람 허용.
- 매크로 평균: 정답 ≥1 인 질의에 대해서만 평균(질의밀도 반영). 분모를 명시 보고한다(혼용 금지).

CLI: `python -m sdkb_paper.analysis.metrics [--run PATH] [--k 50 100 500]`.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from .. import config


def load_run(path: Path) -> dict[str, list[str]]:
    """TREC run → {qid: [doc_id, ...]} (rank 순)."""
    run: dict[str, list[str]] = {}
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if len(parts) < 4:
                continue
            qid, _, docid, rank = parts[0], parts[1], parts[2], int(parts[3])
            run.setdefault(qid, []).append((rank, docid))
    return {q: [d for _, d in sorted(v)] for q, v in run.items()}


def load_qrel(path: Path | None = None) -> dict[str, set[str]]:
    """qrel parquet(query_id·doc_id·relevance) → {qid: {positive doc_id}} (relevance>0)."""
    import pandas as pd

    q = pd.read_parquet(path or config.QREL_EXAMINER)
    qrel: dict[str, set[str]] = {}
    for r in q.itertuples(index=False):
        if getattr(r, "relevance", 1) > 0:
            qrel.setdefault(r.query_id, set()).add(r.doc_id)
    return qrel


def evaluate(
    run: dict[str, list[str]], qrel: dict[str, set[str]], ks: tuple[int, ...] = (50, 100, 500)
) -> dict:
    """문서수준 Recall@K·Success@K·MRR@K (매크로, 정답≥1 질의만)."""
    eval_qids = [q for q, pos in qrel.items() if pos]   # 정답 보유 질의만
    n = len(eval_qids)
    out: dict = {"n_queries_evaluated": n, "n_queries_in_run": len(run)}
    recall = {k: 0.0 for k in ks}
    success = {k: 0 for k in ks}
    mrr = 0.0
    for qid in eval_qids:
        pos = qrel[qid]
        ranked = run.get(qid, [])
        # MRR: 첫 정답의 역수 순위 (상한 max(ks) 내)
        for i, d in enumerate(ranked[: max(ks)], start=1):
            if d in pos:
                mrr += 1.0 / i
                break
        for k in ks:
            topk = set(ranked[:k])
            hit = len(topk & pos)
            recall[k] += hit / len(pos)
            if hit > 0:
                success[k] += 1
    out["recall"] = {k: (recall[k] / n if n else 0.0) for k in ks}
    out["success"] = {k: (success[k] / n if n else 0.0) for k in ks}
    out["mrr"] = mrr / n if n else 0.0
    return out


def _fmt(res: dict) -> str:
    lines = [
        f"평가 질의(정답≥1): {res['n_queries_evaluated']}  ·  run 질의: {res['n_queries_in_run']}",
        "─" * 48,
    ]
    for k in sorted(res["recall"]):
        lines.append(
            f"  Recall@{k:<4} {res['recall'][k]:.4f}   "
            f"Success@{k:<4} {res['success'][k]:.4f}"
        )
    lines.append(f"  MRR         {res['mrr']:.4f}")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=Path, default=None, help="TREC run 파일(기본 B0)")
    ap.add_argument("--qrel", type=Path, default=None, help="qrel parquet(기본 examiner)")
    ap.add_argument("--k", type=int, nargs="+", default=[50, 100, 500])
    args = ap.parse_args()

    from ..retrieval.bm25 import RUN_B0

    run = load_run(args.run or RUN_B0)
    qrel = load_qrel(args.qrel)
    res = evaluate(run, qrel, tuple(sorted(args.k)))
    print(_fmt(res))


if __name__ == "__main__":
    main()
