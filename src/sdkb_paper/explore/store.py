"""읽기 전용 pyoxigraph 스토어 — G₀/G₁/G₂ 를 메모리에 적재하고 SPARQL 을 실행한다.

이 모듈은 얼린 산출물(``data/processed/graph_v{0,1,2}.ttl``)을 **열기만** 한다.
어떤 경로로도 그래프에 쓰지 않는다 — G₀ 서명 불변이 explore 도구의 전제다.
"""
from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field

from pyoxigraph import QueryBoolean, QuerySolutions, QueryTriples, RdfFormat, Store

from sdkb_paper.config import GRAPH_V0, GRAPH_V1, GRAPH_V2

# 그래프 키 → (파일, 표시 라벨). 대시보드·질의 대상 선택의 단일 원천.
GRAPHS = {
    "v0": (GRAPH_V0, "G₀ · baseline (현행 SDKB)"),
    "v1": (GRAPH_V1, "G₁ · 삼성·SK하이닉스 보강"),
    "v2": (GRAPH_V2, "G₂ · KSIA 소부장 188사"),
}

# 결과 폭발을 막는 상한. 진단 도구이므로 넉넉하되 유한하게.
MAX_ROWS = 10_000

_stores: dict[str, Store] = {}


def load(key: str) -> Store:
    """그래프를 메모리에 올려 캐시한다. 첫 호출만 파일을 읽는다."""
    if key not in GRAPHS:
        raise KeyError(f"unknown graph key: {key!r}")
    if key not in _stores:
        path = GRAPHS[key][0]
        if not path.exists():
            raise FileNotFoundError(f"{path} 없음 — make baseline / make merge 로 먼저 조립하라")
        store = Store()
        store.bulk_load(path=str(path), format=RdfFormat.TURTLE)
        _stores[key] = store
    return _stores[key]


def available() -> dict[str, dict]:
    """각 그래프의 존재 여부·라벨·적재 상태를 보고한다."""
    out = {}
    for key, (path, label) in GRAPHS.items():
        out[key] = {
            "key": key,
            "label": label,
            "exists": path.exists(),
            "loaded": key in _stores,
            "path": str(path),
        }
    return out


def _term(t) -> dict | None:
    """pyoxigraph 텀 → JSON 직렬화 딕셔너리. 미바인딩은 None."""
    if t is None:
        return None
    cls = type(t).__name__
    if cls == "NamedNode":
        return {"type": "uri", "value": t.value}
    if cls == "BlankNode":
        return {"type": "bnode", "value": t.value}
    if cls == "Literal":
        d: dict = {"type": "literal", "value": t.value}
        if t.language:
            d["lang"] = t.language
        elif t.datatype is not None:
            d["datatype"] = t.datatype.value
        return d
    return {"type": "unknown", "value": str(t)}


@dataclass
class QueryResult:
    kind: str  # select | ask | construct
    columns: list[str] = field(default_factory=list)
    rows: list[list] = field(default_factory=list)  # select: 행별 셀(dict|None) 리스트
    boolean: bool | None = None  # ask
    triples: list[dict] = field(default_factory=list)  # construct/describe
    elapsed_ms: float = 0.0
    truncated: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def run_query(key: str, query: str) -> QueryResult:
    """SELECT/ASK/CONSTRUCT/DESCRIBE 를 실행해 직렬화 가능한 결과로 반환한다."""
    store = load(key)
    t0 = time.perf_counter()
    res = store.query(query)
    elapsed = lambda: (time.perf_counter() - t0) * 1000  # noqa: E731

    if isinstance(res, QueryBoolean):
        return QueryResult(kind="ask", boolean=bool(res), elapsed_ms=elapsed())

    if isinstance(res, QueryTriples):
        triples, truncated = [], False
        for i, tr in enumerate(res):
            if i >= MAX_ROWS:
                truncated = True
                break
            triples.append(
                {"s": _term(tr.subject), "p": _term(tr.predicate), "o": _term(tr.object)}
            )
        return QueryResult(
            kind="construct",
            columns=["subject", "predicate", "object"],
            triples=triples,
            elapsed_ms=elapsed(),
            truncated=truncated,
        )

    # QuerySolutions (SELECT)
    assert isinstance(res, QuerySolutions)
    columns = [v.value for v in res.variables]
    rows, truncated = [], False
    for i, sol in enumerate(res):
        if i >= MAX_ROWS:
            truncated = True
            break
        rows.append([_term(sol[c]) for c in columns])
    return QueryResult(
        kind="select", columns=columns, rows=rows, elapsed_ms=elapsed(), truncated=truncated
    )


def scalar(key: str, query: str) -> int:
    """단일 COUNT 결과를 정수로 뽑는다. 대시보드 서명 집계용."""
    res = run_query(key, query)
    if res.kind == "select" and res.rows and res.rows[0] and res.rows[0][0]:
        try:
            return int(res.rows[0][0]["value"])
        except (ValueError, KeyError, TypeError):
            return 0
    return 0
