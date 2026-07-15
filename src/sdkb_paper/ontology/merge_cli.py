"""`make merge` 의 진입점 — 델타를 게이트에 통과시켜 graph_v1(G₁) 을 만든다.

게이트가 실패하면 그래프는 저장되지 않고 종료코드 1 이다. 우회로는 없다 (CLAUDE.md §5).
"""
from __future__ import annotations

import argparse
import sys

from sdkb_paper.config import GRAPH_V0
from sdkb_paper.ontology.delta import DELTA_TTL, DELTA_V2_TTL, GRAPH_V1, GRAPH_V2
from sdkb_paper.ontology.merge import GateFailure, merge_with_gate


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", choices=["samsung-hynix", "ksia-equipment"], default="samsung-hynix",
                    help="samsung-hynix=G₁(PLAN-002) · ksia-equipment=G₂ 소부장(RQ3 · PLAN-014 C-2)")
    args = ap.parse_args()

    # G₂ 도 G₀ 위에 병합한다(G₁ 이 아니다) — G₂ 는 소부장 코퍼스만의 델타이고, 삼성/하이닉스
    # 델타와 섞지 않는다. 두 코퍼스의 before 는 똑같이 G₀ 다(H1 은 코퍼스만 다르다).
    delta_ttl, out, tag = ((DELTA_V2_TTL, GRAPH_V2, "graph_v2 (G₂)")
                           if args.corpus == "ksia-equipment"
                           else (DELTA_TTL, GRAPH_V1, "graph_v1 (G₁)"))
    try:
        g = merge_with_gate(GRAPH_V0, delta_ttl, out)
    except GateFailure as e:
        print(f"❌ 게이트 실패 — 그래프를 저장하지 않았다.\n{e}", file=sys.stderr)
        return 1
    print(f"✓ L1 통과 · {tag} 트리플 {len(g):,} → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
