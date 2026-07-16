"""A — 기술개념 전수 인구조사 (PLAN-016).

**이것은 유의성 검정이 아니라 음성·진단 증거다.** 소자 몇 개만 보면 "왜 4~7개뿐이냐"는
체리피킹 의심을 못 지운다. 그래서 온톨로지의 **기술개념 전수**(소자·공정·소재·장비)에
개념-vs-명칭 조기탐지를 걸어, **소박한 모집단 검정이 왜 무효 유의를 내는지**를 실증한다.

발견 (측정 결과 · PLAN-016 Stage 2):
  · 소자만        : 개념 12 vs 명칭 7  (p≈0.18)
  · 소자+공정      : 개념 26 vs 명칭 10 (p≈0.006) — **유의하나 무효다**
  · 전 개념        : 개념 26 vs 명칭 18 (p≈0.15)
왜 무효인가 — 두 인공물:
  (1) **성숙개념 우편향 절단**: etch·metallization 같은 flat-high 성숙 공정은 명칭팔이
      상대성장 규칙에서 발화 자체를 못 해 개념팔이 **자동 승리**한다. 조기탐지가 아니다.
  (2) **소급코드 편향**: 개념(코드)팔 매핑의 절반이 H10 소급코드라 §4.4 의 시간무효성을 탄다.
스코프를 골라 유의성을 취하지 않는다 — **세 스코프를 나란히** 싣고, 우편향 절단·성숙개념을
플래그해 유의성이 인공물임을 독자가 직접 판별하게 한다 (CLAUDE.md §1.2).

개념팔이 **구조적으로 발화 불가**한 축(소재·장비: code_to_concept 매핑 0)은 개념-vs-명칭
비교가 퇴화하므로 별도 표기한다 — 유리해서가 아니라 개념팔이 침묵하기 때문이다.
"""
from __future__ import annotations

import pandas as pd
from rdflib import Graph
from scipy.stats import binomtest

from sdkb_paper.analysis.timeseries import (
    N_MIN, WINDOWS, annual_counts, assign_concepts, concept_series, detect_year,
)
from sdkb_paper.config import GRAPH_V0
from sdkb_paper.ontology.emerging import _term_in

WINDOW = WINDOWS["extended"]  # 2005–2023 · 좌측절단 교정창 (C 와 동일)

# 기술개념 축. Material·Equipment 는 code_to_concept 매핑이 없어 개념팔이 침묵한다.
TECH_CLASSES = ("Device", "Process", "SubProcess", "Material", "Equipment", "EquipmentClass")
MAPPED_AXES = ("Device", "Process", "SubProcess")  # 개념팔 발화 가능한 축

_LABEL_SPARQL = """
PREFIX ont:  <https://w3id.org/sdkb/ont/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?c ?cls ?label WHERE {
  VALUES ?cls { %s }
  ?c a ?cls .
  { ?c skos:prefLabel ?label } UNION { ?c skos:altLabel ?label }
}
""" % " ".join(f"ont:{c}" for c in TECH_CLASSES)


def load_tech_concepts(graph_path=GRAPH_V0) -> dict[str, tuple[str, list[str]]]:
    """{개념 IRI: (클래스, [명칭 용어...])}. 명칭 팔의 어휘는 그래프 라벨 그대로다 (신규수집 0)."""
    g = Graph().parse(graph_path)
    out: dict[str, tuple[str, set[str]]] = {}
    for c, cls, label in g.query(_LABEL_SPARQL):
        iri = str(c)
        term = str(label).strip()
        if len(term) < 2:
            continue
        cls_name = str(cls).split("/")[-1]
        out.setdefault(iri, (cls_name, set()))[1].add(term)
    return {iri: (cls, sorted(terms)) for iri, (cls, terms) in out.items()}


def _name_year(df: pd.DataFrame, terms: list[str]) -> int | None:
    """명칭 팔 탐지연도 — 라벨 용어가 명세에 등장한 특허의 조기탐지."""
    years = [
        row.application_date.year
        for row in df.itertuples()
        if any(_term_in(t, f"{row.invention_title or ''} {row.abstract or ''}".lower())
               for t in terms)
    ]
    return detect_year(annual_counts(pd.Series(years, dtype="int64"), WINDOW), window=WINDOW)


def _judge(cy: int | None, ny: int | None) -> str:
    if cy is None and ny is None:
        return "both_undetected"
    if ny is None:
        return "concept_first"   # 명칭 미탐지 → 개념 승 (우편향 절단)
    if cy is None:
        return "name_first"
    if cy < ny:
        return "concept_first"
    if cy > ny:
        return "name_first"
    return "tie"


def census(df: pd.DataFrame, graph_path=GRAPH_V0) -> pd.DataFrame:
    """전 기술개념 × (개념 코드팔 · 명칭팔) 탐지연도와 판정. df 는 codes 컬럼 보유(prepare 후)."""
    concepts = load_tech_concepts(graph_path)
    assigned = assign_concepts(df, definition="legacy")  # 개념(코드) 팔
    rows = []
    for iri, (cls, terms) in concepts.items():
        cs = concept_series(df, iri, assigned, WINDOW)
        cy = detect_year(cs, window=WINDOW)
        ny = _name_year(df, terms)
        # 좌측절단(성숙) 플래그: 창 첫해에 이미 ≥ n_min 이면 상대성장 규칙이 볼 수 없다.
        mature = int(cs.get(WINDOW[0], 0)) >= N_MIN
        outcome = _judge(cy, ny)
        rows.append({
            "cls": cls, "concept": iri.split("/")[-1],
            "concept_year": cy, "name_year": ny,
            "concept_n": int(cs.sum()),
            "outcome": outcome,
            "one_sided": outcome == "concept_first" and ny is None,  # 명칭 미발화 승
            "mature": mature,                                        # 좌측절단 성숙개념
        })
    return pd.DataFrame(rows).sort_values(["cls", "concept"]).reset_index(drop=True)


def scope_test(cen: pd.DataFrame, classes: tuple[str, ...]) -> dict:
    """한 스코프의 단측 부호검정. 동점·양쪽미탐지 제외 (C 와 같은 규약)."""
    sub = cen[cen["cls"].isin(classes)]
    valid = sub[sub["outcome"].isin(["concept_first", "name_first"])]
    c = int((valid["outcome"] == "concept_first").sum())
    n = len(valid)
    p = binomtest(c, n, 0.5, alternative="greater").pvalue if n else 1.0
    return {
        "scope": "+".join(classes),
        "n_concepts": len(sub),
        "n_pairs": n,
        "concept_first": c,
        "name_first": n - c,
        "one_sided_wins": int(valid["one_sided"].sum()),   # 우편향 절단으로 인한 개념 승
        "mature_concept_wins": int(valid[(valid["outcome"] == "concept_first")]["mature"].sum()),
        "p": float(p),
    }


def scopes_summary(cen: pd.DataFrame) -> pd.DataFrame:
    """세 스코프를 나란히 — 유의성이 스코프 선택과 인공물의 산물임을 드러낸다."""
    rows = [
        scope_test(cen, ("Device",)),
        scope_test(cen, ("Device", "Process", "SubProcess")),
        scope_test(cen, TECH_CLASSES),
    ]
    return pd.DataFrame(rows)
