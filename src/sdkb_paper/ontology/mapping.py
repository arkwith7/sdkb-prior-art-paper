"""특허 -> SDKB 개념 매핑.

1차: CPC/IPC 코드 -> 개념 룰 테이블 (mapping.csv)
2차(선택): 텍스트 임베딩 유사도 기반 후보 추천 -> 사람 검수 후 룰 테이블에 반영
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_code_mapping(csv_path: Path) -> dict[str, list[str]]:
    """mapping.csv (columns: code_prefix, concept_iri) -> {prefix: [iri, ...]}"""
    df = pd.read_csv(csv_path)
    table: dict[str, list[str]] = {}
    for _, row in df.iterrows():
        table.setdefault(str(row["code_prefix"]).strip(), []).append(str(row["concept_iri"]).strip())
    return table


def map_codes_to_concepts(codes: list[str], table: dict[str, list[str]]) -> list[str]:
    """가장 긴 prefix 우선 매칭. 미매핑 코드는 커버리지 공백 분석의 입력이 된다."""
    concepts: list[str] = []
    prefixes = sorted(table, key=len, reverse=True)
    for code in codes:
        code = code.replace(" ", "")
        for p in prefixes:
            if code.startswith(p):
                concepts.extend(table[p])
                break
    return sorted(set(concepts))
