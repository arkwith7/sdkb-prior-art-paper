#!/usr/bin/env python3
"""scripts/rerank_ceiling.py — 재순위화 상한의 정량화 (PLAN-056 §6.4).

용법:  uv run python scripts/rerank_ceiling.py
산출:  data/processed/ir/rerank_ceiling_test.json

**무엇을 세는가.** 제안 구성은 텍스트 기준선(B3)의 상위 1,000건을 재정렬할 뿐 후보 집합을
확대하지 않는다(`retrieval/systems.py:30` POOL_K). 따라서 재순위화 계열 전체가 원리적으로
넘을 수 없는 상한이 존재한다 — **정답이 그 풀 안에 있는가**이다. 이 스크립트는 동결된 run
파일과 봉인 해제된 test qrel 위에서 그 상한을 결정적 집합 연산으로 센다.

**세 값 (PLAN-056 §6.4).**
1. 후보 풀 상한 — B3 상위 1,000 안에 있는 정답의 비율
2. 풀 밖 정답 — 개념 단독 구성(B5)이 회수하였으나 풀에 없는 정답의 건수
3. 합집합 상한 — 풀과 개념 단독 회수의 합집합 기준 상한

**지위는 탐색적 기술통계다(PLAN-056 §6.4.1).** 가설의 지지·기각을 진술하지 않는다.
- 동결된 run 위의 결정적 집합 연산이다 — 검색 설정·분할·임계·정답을 건드리지 않는다.
- 추가 개봉 0회 — 이미 개봉된 test 만 쓴다. B층(test_b)은 이 스크립트의 범위가 아니다.
- **문서 단위**이며 주 지표(family-level Recall@100)를 대체하지 않는다. 두 값을 나란히
  놓지 않는다(분모 규율).
- 분모는 확증 분할의 **479 엣지 / 198 질의**이며 그렇게 밝힌다.

새 검색을 돌리지 않는다 — 읽는 것은 이미 산출된 run 파일뿐이다.
"""
from __future__ import annotations

import json

from sdkb_paper import config
from sdkb_paper.analysis.metrics import load_qrel, load_run
from sdkb_paper.retrieval.systems import POOL_K

RUNS = config.PROCESSED / "ir" / "runs"
B3 = RUNS / "sys_B3_rrf_test.txt"
B5 = RUNS / "sys_B5_concept_test.txt"
QREL = config.PROCESSED / "ir" / "qrel_test_sealed.parquet"
OUT = config.PROCESSED / "ir" / "rerank_ceiling_test.json"


def main() -> None:
    qrel = load_qrel(QREL)
    b3 = load_run(B3)
    b5 = load_run(B5)

    n_edges = sum(len(v) for v in qrel.values())
    n_queries = len(qrel)

    in_pool = out_pool_in_b5 = in_union = 0
    for qid, golds in qrel.items():
        pool = set(b3.get(qid, [])[:POOL_K])
        concept = set(b5.get(qid, []))
        in_pool += len(golds & pool)
        out_pool_in_b5 += len(golds & concept - pool)
        in_union += len(golds & (pool | concept))

    payload = {
        "note": (
            "재순위화 상한의 정량화 (PLAN-056 §6.4). 탐색적 기술통계이며 "
            "**문서 단위**다 — 주 지표 family-level Recall@100 을 대체하지 않는다. "
            "추가 개봉 0회 · 새 검색 실행 0."
        ),
        "split": "test (첫 확증 분할)",
        "denominator": {"edges": n_edges, "queries": n_queries},
        "pool_depth": POOL_K,
        "sources": {
            "pool_run": str(B3.relative_to(config.ROOT)),
            "concept_run": str(B5.relative_to(config.ROOT)),
            "qrel": str(QREL.relative_to(config.ROOT)),
        },
        "values": {
            "pool_ceiling": {
                "hits": in_pool,
                "ratio": in_pool / n_edges,
                "how": "B3 상위 1,000 안에 있는 정답 엣지 / 전체 정답 엣지",
            },
            "outside_pool_recovered_by_concept": {
                "hits": out_pool_in_b5,
                "how": "개념 단독 구성이 회수하였으나 풀에 없는 정답 엣지",
            },
            "union_ceiling": {
                "hits": in_union,
                "ratio": in_union / n_edges,
                "how": "풀 ∪ 개념 단독 회수 기준 상한",
            },
        },
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"✓ {OUT.relative_to(config.ROOT)} — 분모 {n_edges} 엣지 / {n_queries} 질의")
    for key, val in payload["values"].items():
        ratio = f" ({val['ratio']:.4f})" if "ratio" in val else ""
        print(f"  {key:38s} = {val['hits']}{ratio}")


if __name__ == "__main__":
    main()
