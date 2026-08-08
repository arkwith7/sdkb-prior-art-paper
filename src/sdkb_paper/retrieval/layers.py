"""층 표지 소비 헬퍼 (PLAN-045 D1·D2).

검색 모듈 셋이 같은 두 가지를 물어본다 — "이 행이 후보인가" · "이 질의가 내 층인가".
같은 답을 세 곳에 복사하면 한 곳만 고쳐지는 사고가 난다(§2′.3 이 그 유형이다).

**구 코퍼스(층 컬럼 이전)와도 호환된다** — 컬럼이 없으면 질의 전량이 A층이던 시절이므로
`is_candidate` 는 전부 참, `query_layer` 필터는 무작동으로 둔다.
"""
from __future__ import annotations

from .. import config

LAYER_A = "A"
LAYER_B = "B"


def corpus_columns() -> set[str]:
    import pyarrow.parquet as pq

    return set(pq.ParquetFile(config.IR_CORPUS).schema.names)


def with_layer_cols(cols: list[str]) -> list[str]:
    """읽을 컬럼 목록에 층 컬럼이 있으면 더한다(중복 제거)."""
    have = corpus_columns()
    extra = [c for c in ("is_candidate", "query_layer") if c in have and c not in cols]
    return list(dict.fromkeys(cols + extra))


def candidates(df):
    """후보 자격 있는 행만. 없는 코퍼스면 전량."""
    return df[df["is_candidate"]] if "is_candidate" in df.columns else df


def queries_of(df, layer: str = LAYER_A):
    """지정한 층의 질의만. 층 컬럼이 없으면 `is_query` 전량(구 코퍼스)."""
    if "query_layer" in df.columns:
        return df[df["query_layer"] == layer]
    return df[df["is_query"]]
