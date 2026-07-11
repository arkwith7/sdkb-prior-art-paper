"""특허 -> SDKB 공정(ont:Process / ont:SubProcess) 매핑.

두 경로를 쓴다:

1. **IPC/CPC 룰 테이블** (`mappings/ipc_to_process.csv`) — 결정적·재현가능. 1차 경로.
2. **용어 매칭** (SDKB 의 skos:prefLabel / altLabel) — IPC 로 분해되지 않는 단계용 보완 경로.
   EUV/DUV 리소그래피가 대표적이다: 둘 다 G03F7/70 아래라 IPC 접두어로는 구분이 **불가능**하고,
   SDKB 가 가진 별칭("EUV", "ArF", "KrF")으로 명세 텍스트를 봐야만 갈린다.

미매핑 코드는 버그가 아니라 **관측값**이다 — 커버리지 공백 분석의 입력이자, SHACL 게이트가
공정 링크 없는 특허를 막는 근거다(그런 특허는 graph 에 들어가지 않는다).
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from rdflib import RDF, SKOS, Graph, URIRef

from sdkb_paper.config import IPC_MAPPING, ONT


# ── 1. IPC/CPC 룰 경로 ──────────────────────────────────────────────────
def load_code_mapping(csv_path: Path = IPC_MAPPING) -> dict[str, list[str]]:
    """ipc_to_process.csv -> {code_prefix: [concept_iri, ...]}

    code_prefix / concept_iri 외의 컬럼(근거·신뢰도·출처)은 사람이 읽고 검수하기 위한 것이며
    매칭에는 쓰이지 않는다.
    """
    df = pd.read_csv(csv_path)
    table: dict[str, list[str]] = {}
    for _, row in df.iterrows():
        table.setdefault(_norm_code(row["code_prefix"]), []).append(str(row["concept_iri"]).strip())
    return table


def _norm_code(code: object) -> str:
    """KIPRIS 는 'H01L  21/3065' 처럼 공백을 넣어 준다 — 공백 제거 후 대문자."""
    return re.sub(r"\s+", "", str(code)).upper()


def map_codes_to_concepts(codes: list[str], table: dict[str, list[str]]) -> list[str]:
    """가장 긴 prefix 우선 매칭. 미매핑 코드는 커버리지 공백 분석의 입력이 된다.

    긴 접두어 우선이 핵심이다 — H01L21/3065(플라즈마 식각)는 H01L21/306(식각 일반)보다
    먼저 잡혀야 하위 공정으로 내려간다.
    """
    concepts: list[str] = []
    prefixes = sorted(table, key=len, reverse=True)
    for code in codes:
        code = _norm_code(code)
        for p in prefixes:
            if code.startswith(p):
                concepts.extend(table[p])
                break
    return sorted(set(concepts))


# ── 2. 용어 매칭 경로 (IPC 로 안 갈리는 단계) ───────────────────────────
def load_term_table(graph: Graph) -> dict[str, list[str]]:
    """SDKB 그래프에서 {공정 IRI: [prefLabel, altLabel...]} 를 뽑는다.

    한국어 altLabel("식각", "평탄화")과 영문 약어("EUV", "ArF")가 섞여 있다 — KIPRIS 국문
    명세에 그대로 걸리는 것이 이 경로의 존재 이유다.
    """
    table: dict[str, list[str]] = {}
    for cls in (ONT.Process, ONT.SubProcess):
        for step in graph.subjects(RDF.type, cls):
            terms = [str(t) for t in graph.objects(step, SKOS.prefLabel)]
            terms += [str(t) for t in graph.objects(step, SKOS.altLabel)]
            if terms:
                table[str(step)] = terms
    return table


def map_text_to_concepts(text: str, terms: dict[str, list[str]]) -> list[str]:
    """명세 텍스트에서 공정 용어를 찾아 IRI 로 되돌린다 (결정적 단어경계 매칭).

    보조 경로일 뿐이다 — 이 결과만으로 그래프에 넣지 않는다. IPC 룰이 상위 공정까지만
    찍어줄 때 하위 공정으로 내리는 근거로 쓰고, 사람이 검수한다.
    """
    hay = text.lower()
    hits = []
    for iri, labels in terms.items():
        for label in labels:
            # 한글은 단어경계(\b)가 동작하지 않으므로 ASCII 용어일 때만 경계를 강제한다.
            pattern = rf"\b{re.escape(label.lower())}\b" if label.isascii() else re.escape(label)
            if re.search(pattern, hay):
                hits.append(iri)
                break
    return sorted(set(hits))


# ── 3. 룰 커버리지 진단 ─────────────────────────────────────────────────
def rule_coverage(graph: Graph, table: dict[str, list[str]] | None = None) -> pd.DataFrame:
    """SDKB 공정 20개 중 IPC 룰이 하나도 없는 단계를 드러낸다.

    특허를 한 건도 수집하기 전에 매핑의 사각지대를 알 수 있다 — 룰이 없는 단계는
    H1 에서 영원히 공백으로 남을 수밖에 없고, 그건 데이터가 아니라 룰의 한계다.
    """
    table = table if table is not None else load_code_mapping()
    mapped = {iri for iris in table.values() for iri in iris}
    rows = []
    for cls in ("Process", "SubProcess"):
        for step in graph.subjects(RDF.type, ONT[cls]):
            iri = str(step)
            rows.append({
                "level": cls.lower(),
                "label": str(graph.value(URIRef(iri), SKOS.prefLabel)),
                "step": iri,
                "n_rules": sum(iri in iris for iris in table.values()),
            })
    df = pd.DataFrame(rows).sort_values(["level", "n_rules", "label"])
    df["has_rule"] = df["step"].isin(mapped)
    return df.set_index(["level", "label"])[["n_rules", "has_rule", "step"]]


def main() -> None:
    """CLI: baseline 대비 IPC 룰 커버리지를 보고한다."""
    from sdkb_paper.config import GRAPH_V0

    g = Graph().parse(GRAPH_V0)
    df = rule_coverage(g)
    print(df[["n_rules", "has_rule"]].to_string())
    gaps = df[~df["has_rule"]]
    print(f"\n[mapping] IPC 룰 있는 단계: {df['has_rule'].sum()}/{len(df)}")
    if len(gaps):
        print(f"[mapping] 룰 없는 단계 {len(gaps)}개 — 텍스트 매칭 경로가 필요하다:")
        for (level, label) in gaps.index:
            print(f"           - {level}/{label}")


if __name__ == "__main__":
    main()
