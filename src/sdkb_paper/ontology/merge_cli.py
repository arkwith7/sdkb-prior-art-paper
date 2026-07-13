"""`make merge` 의 진입점 — 델타를 게이트에 통과시켜 graph_v1(G₁) 을 만든다.

게이트가 실패하면 그래프는 저장되지 않고 종료코드 1 이다. 우회로는 없다 (CLAUDE.md §5).
"""
from __future__ import annotations

import sys

from sdkb_paper.config import GRAPH_V0
from sdkb_paper.ontology.delta import DELTA_TTL, GRAPH_V1
from sdkb_paper.ontology.merge import GateFailure, merge_with_gate


def main() -> int:
    try:
        g = merge_with_gate(GRAPH_V0, DELTA_TTL, GRAPH_V1)
    except GateFailure as e:
        print(f"❌ 게이트 실패 — 그래프를 저장하지 않았다.\n{e}", file=sys.stderr)
        return 1
    print(f"✓ L1 통과 · graph_v1 트리플 {len(g):,} → {GRAPH_V1}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
