"""개념 쌍 관계 유사도 표 (PLAN-075 §12.2 · §12.5 · 순위 함수의 `w_r` 항 입력).

**왜 이 모듈이 있는가.** 기존 경로 항 `path_sim`(`retrieval/ontology_rerank.py`)은 개념이 아니라
개념의 **축 클래스**로 Wu-Palmer 를 계산한다. 실측(PLAN-075 §9.1.3)에서 축 쌍 105 가운데 비영은
1 이었고, 그래서 그 항은 관계 유사도가 아니라 *"축이 같은가"* 의 지시자로 퇴화해 있다. 관계
자체는 벤더 스냅샷의 개념 그래프에 **엣지 310**(고유)으로 존재하는데 검색이 그것을 읽는 코드가
없었다 — 이 모듈이 그 통로다.

정의(설계 §12.2 · 사용자 승인 2026-08-24):

    s(a,b) = 0                    (a == b)
    s(a,b) = γ^(hop(a,b) − 1)     (1 ≤ hop ≤ H · 무향 최단 홉)
    s(a,b) = 0                    (그 밖)

`a == b` 에서 0 을 주는 것이 이 항의 존재 이유다 — 정확 일치는 `ConceptOverlap` 이 이미 세므로,
여기서 또 세면 새 항의 이득과 이중 계상이 구분되지 않는다.

제외 둘(§12.3) — **음수 가중 술어**(`INCOMPATIBLE_WITH`·`NOT_ALLOWED_WITH`)는 "닮았다"가 아니라
"함께 있을 수 없다"이므로 유사도 경로가 아니다. **전문가 축 술어**(`REQUIRES_SKILL`·`PROVIDED_BY`·
`MADE_BY`)는 A8 음성 대조군(`Skill` 축)이 쓰는 길이라, 경로 항이 그것을 타면 A8 제거가 경로 항을
함께 흔들어 H5 의 판정 논리가 무너진다.

원천은 벤더 스냅샷 `semiconductor_v0_3.json` 이다(§0.1 계약 — 런타임에 상류를 읽지 않는다).
`sdkb-core-data.ttl` 로 310/310 전부 승격돼 있어 둘은 동치이나, JSON 이 술어명과 가중을 그대로
갖는다(PLAN-075 §9.1.1).

CLI: `python -m sdkb_paper.ontology.concept_relations [--gamma 0.5] [--max-hop 2]`
"""
from __future__ import annotations

import json
from collections import defaultdict, deque
from pathlib import Path

from .. import config

SOURCE_JSON = "semiconductor_v0_3.json"

# 유사도 경로로 세지 않는 술어 — 근거는 모듈 독스트링·PLAN-075 §12.3.
NEGATIVE_PREDICATES = frozenset({"INCOMPATIBLE_WITH", "NOT_ALLOWED_WITH"})
EXPERT_PREDICATES = frozenset({"REQUIRES_SKILL", "PROVIDED_BY", "MADE_BY"})

# 동결값(§12.3 · 결과 보기 전에 박는다). 민감도 격자는 γ∈{0.3,0.5,0.7}×H∈{2,3}.
GAMMA = 0.5
MAX_HOP = 2
ROUND_NDIGITS = 6


def _slug(node_id: str) -> str:
    """`process:etch` → `etch`. 코퍼스 `concepts` 열은 축 접두 없는 지역명이다."""
    return node_id.split(":", 1)[1] if ":" in node_id else node_id


def _adjacency(edges: list[dict], *, drop_expert: bool, drop_negative: bool,
               use_weight: bool) -> dict[str, dict[str, float]]:
    """무향 인접. `use_weight` 는 기본 꺼짐 — JSON 의 0.5–1.0 은 출처 매핑 신뢰도이지
    의미 거리가 아니므로, 두 미검증 선택을 한 델타에 섞지 않는다(§12.3)."""
    adj: dict[str, dict[str, float]] = defaultdict(dict)
    for e in edges:
        pred = e["predicate"]
        if drop_negative and pred in NEGATIVE_PREDICATES:
            continue
        if drop_expert and pred in EXPERT_PREDICATES:
            continue
        w = abs(float(e.get("weight", 1.0))) if use_weight else 1.0
        a, b = _slug(e["src"]), _slug(e["dst"])
        if a == b:
            continue
        adj[a][b] = max(adj[a].get(b, 0.0), w)
        adj[b][a] = max(adj[b].get(a, 0.0), w)
    return adj


def _hops(adj: dict[str, dict[str, float]], src: str, max_hop: int) -> dict[str, int]:
    """src → {node: 최단 홉}. 자기 자신은 넣지 않는다(s(a,a)=0)."""
    seen: dict[str, int] = {src: 0}
    q: deque[str] = deque([src])
    while q:
        u = q.popleft()
        h = seen[u]
        if h >= max_hop:
            continue
        for v in adj.get(u, ()):
            if v not in seen:
                seen[v] = h + 1
                q.append(v)
    del seen[src]
    return seen


def build(gamma: float = GAMMA, max_hop: int = MAX_HOP, *, use_weight: bool = False,
          drop_expert: bool = True, drop_negative: bool = True,
          out: Path | None = None) -> Path:
    """개념 쌍 표를 산출한다. 무작위성 없음 · 정렬과 반올림 고정 → 두 번 돌리면 바이트 동일."""
    import pandas as pd

    src = config.EXTERNAL_SDKB / SOURCE_JSON
    graph = json.loads(src.read_text(encoding="utf-8"))
    adj = _adjacency(graph["edges"], drop_expert=drop_expert,
                     drop_negative=drop_negative, use_weight=use_weight)

    rows: list[tuple[str, str, int, float]] = []
    for a in sorted(adj):
        for b, hop in _hops(adj, a, max_hop).items():
            if a < b:                                  # 무향 → 상삼각만 보관
                sim = round(gamma ** (hop - 1), ROUND_NDIGITS)
                rows.append((a, b, hop, sim))
    rows.sort()

    df = pd.DataFrame(rows, columns=["a", "b", "hop", "sim"])
    path = Path(out) if out else config.IR_CONCEPT_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    return path


def load_rel(path: Path | None = None) -> dict[tuple[str, str], float]:
    """`(a,b) → sim` (a<b 정렬 키). 표가 없으면 빈 사전 — 항은 무작동이 된다."""
    import pandas as pd

    p = Path(path) if path else config.IR_CONCEPT_REL
    if not p.exists():
        return {}
    df = pd.read_parquet(p)
    return {(a, b): float(s) for a, b, s in zip(df["a"], df["b"], df["sim"], strict=True)}


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="개념 쌍 관계 유사도 표 (PLAN-075 §12.5)")
    ap.add_argument("--gamma", type=float, default=GAMMA)
    ap.add_argument("--max-hop", type=int, default=MAX_HOP)
    ap.add_argument("--use-weight", action="store_true", help="JSON weight 사용(민감도 격자)")
    ap.add_argument("--keep-expert", action="store_true", help="전문가 축 술어 포함(A8 오염 주의)")
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    path = build(a.gamma, a.max_hop, use_weight=a.use_weight,
                 drop_expert=not a.keep_expert, out=a.out)
    import pandas as pd

    df = pd.read_parquet(path)
    print(f"[concept_rel] {path} · 쌍 {len(df):,} · γ={a.gamma} H={a.max_hop} "
          f"· 개념 {len(set(df['a']) | set(df['b'])):,}")
    print(df.groupby("hop").size().to_string())


if __name__ == "__main__":
    main()
