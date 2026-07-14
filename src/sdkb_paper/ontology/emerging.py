"""신기술 인식 레이어 — 이름으로도 코드로도 잡히지 않는 기술을 개념으로 붙잡는다 (PLAN-004).

왜 필요한가 (실측):
  - GAA 전용 코드(H10D30/6735 · H10D30/501)를 받은 삼성·SK하이닉스 특허는 **0건**이다.
    코드가 존재하는 것과 코드가 부여되는 것은 다른 사건이고, 그 지연이 H2 의 논지다.
  - HBM 은 조합 정의로 209건이 잡히는데 그중 **대다수가 명세에 이름을 쓰지 않는다.**
    별칭 테이블만으로는 이들을 영원히 놓친다.

두 층으로 잡는다 (3층 후보 발굴은 candidates.py):
  1층 별칭  — 이름을 **다르게** 부르는 특허 (MBCFET · 나노시트 · 고대역폭 메모리)
  2층 조합  — 이름도 코드도 없는 특허. **기존 개념의 논리 조합**으로 정의한다
              (HBM ≡ 적층메모리 ∧ TSV). 코드가 신설되기를 기다리지 않고 개념을 표현할 수
              있다는 것이 온톨로지가 코드 리스트보다 나은 이유다.

**새 어휘를 만들지 않는다.** 두 층 모두 SDKB 에 이미 있는 Device 개념(device/hbm ·
device/gaa_fet · device/finfet)에 `ont:concernsDevice` 링크를 더할 뿐이다 (CLAUDE.md §1.4).

**정의는 시계열을 보기 전에 동결됐다.** 대상 기술과 조합식은 우리 데이터 분포가 아니라 외부
원천(JEDEC 표준 · CPC 2026.01 공식 스킴 원문)에서 왔고, 출처가 CSV 의 source 컬럼에 있다.
커밋 해시가 사전등록의 증거다. 변이(strict/base/loose)도 미리 정의해 함께 커밋했다 —
결과를 보고 유리한 정의를 고르는 것을 막기 위해서다 (CLAUDE.md §1.2 · 논문 §4.5).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from sdkb_paper.config import (
    EMERGING_CONCEPTS,
    NAME_BASELINE,
    SI_CONCEPTS,
    TERM_ALIASES,
)
from sdkb_paper.ontology.mapping import _norm_code

# 기본 변이. 민감도 분석은 strict/loose 로 같은 함수를 다시 돌린다 (§4.5).
DEFAULT_VARIANT = "base"
VARIANTS = ("strict", "base", "loose")


# ── 1층 · 별칭 ──────────────────────────────────────────────────────────
def load_aliases(path: Path = TERM_ALIASES, variant: str = DEFAULT_VARIANT) -> dict[str, list[str]]:
    """{개념 IRI: [용어...]}. variant 는 누적이 아니라 포함 관계다 — loose ⊃ base."""
    df = pd.read_csv(path)
    keep = {"base"} if variant in ("strict", "base") else {"base", "loose"}
    df = df[df["variant"].isin(keep)]

    table: dict[str, list[str]] = {}
    for _, row in df.iterrows():
        table.setdefault(str(row["concept_iri"]).strip(), []).append(str(row["term"]).strip())
    return table


def alias_labels(
    path: Path = TERM_ALIASES, variant: str = DEFAULT_VARIANT
) -> list[tuple[str, str, str]]:
    """[(개념 IRI, 용어, 언어코드)] — 그래프에 skos:altLabel 로 넣기 위한 형태.

    SDKB 의 라벨 설계는 **영문이 기준(prefLabel@en), 타 언어는 별칭(altLabel@ko)** 이다
    (실측: prefLabel@en 630 · altLabel@ko 428). 그런데 신기술 개념만 이 체계에서 비어 있다 —
    `device/gaa_fet` 의 altLabel 은 **0개**이고 `device/hbm` 은 영문 하나뿐이다.

    별칭을 CSV 안에만 두면 매칭에는 쓰이지만 **그래프에 "고대역폭 메모리"로 질의할 수 없다** —
    그건 온톨로지가 아니라 사설 룩업 테이블이다. 그래서 별칭을 SDKB 자체 어휘(skos:altLabel)로
    G₁ 에 실체화한다. G₀ 는 건드리지 않으므로 H1 의 before 는 그대로다.

    loose 변이(나노와이어 등)는 민감도 분석 전용이므로 **그래프에 넣지 않는다.**
    """
    df = pd.read_csv(path)
    keep = {"base"} if variant in ("strict", "base") else {"base", "loose"}
    df = df[df["variant"].isin(keep)]
    return [
        (str(r["concept_iri"]).strip(), str(r["term"]).strip(), str(r["lang"]).strip())
        for _, r in df.iterrows()
    ]


def _term_in(term: str, hay: str) -> bool:
    """한글은 단어경계(\\b)가 동작하지 않으므로 ASCII 용어일 때만 경계를 강제한다 —
    mapping.map_text_to_concepts 와 같은 규칙이다."""
    t = term.lower()
    pattern = rf"\b{re.escape(t)}\b" if term.isascii() else re.escape(t)
    return re.search(pattern, hay) is not None


def match_aliases(text: str, aliases: dict[str, list[str]]) -> list[str]:
    """명세 텍스트에서 별칭을 찾아 개념 IRI 로 되돌린다 (결정적 매칭)."""
    hay = text.lower()
    return sorted(
        {iri for iri, terms in aliases.items() if any(_term_in(t, hay) for t in terms)}
    )


# ── 2층 · 조합 정의 ─────────────────────────────────────────────────────
@dataclass(frozen=True)
class Combination:
    """조합 정의 하나. groups 는 **논리곱**, 각 group 안의 접두어는 **논리합**이다.

    HBM(base) = (H10B80 ∨ H10W90) ∧ (H10W20/20 ∨ H10W20/211 ∨ H10W20/023)
    집합 연산이지 추론이 아니다 — 결정적이고 감사 가능하다.
    """

    concept_iri: str
    variant: str
    groups: tuple[tuple[str, ...], ...]

    def matches(self, codes: list[str]) -> bool:
        norm = [_norm_code(c) for c in codes]
        return all(
            any(c.startswith(p) for c in norm for p in group)
            for group in self.groups
        )


def parse_definition(expr: str) -> tuple[tuple[str, ...], ...]:
    """'A|B AND C|D' → (('A','B'), ('C','D'))."""
    return tuple(
        tuple(_norm_code(p) for p in group.split("|") if p.strip())
        for group in expr.split(" AND ")
        if group.strip()
    )


def load_combinations(
    path: Path = EMERGING_CONCEPTS, variant: str = DEFAULT_VARIANT
) -> list[Combination]:
    if variant not in VARIANTS:
        raise ValueError(f"알 수 없는 variant: {variant!r} (허용: {VARIANTS})")
    df = pd.read_csv(path)
    df = df[df["variant"] == variant]
    return [
        Combination(
            concept_iri=str(r["concept_iri"]).strip(),
            variant=variant,
            groups=parse_definition(str(r["definition"])),
        )
        for _, r in df.iterrows()
    ]


def match_combinations(codes: list[str], combos: list[Combination]) -> list[str]:
    return sorted({c.concept_iri for c in combos if c.matches(codes)})


# ── 두 층의 합 ──────────────────────────────────────────────────────────
def emerging_devices(
    codes: list[str],
    text: str,
    aliases: dict[str, list[str]],
    combos: list[Combination],
) -> list[str]:
    """특허 1건이 가리키는 신기술 개념(Device IRI). 두 경로의 합집합이다.

    이름을 쓴 특허는 1층이, 이름도 코드도 없는 특허는 2층이 잡는다. 두 집합은 거의 겹치지
    않는다 — HBM 에서 조합 209건 중 이름을 쓴 것은 4건뿐이다.
    """
    return sorted(set(match_aliases(text, aliases)) | set(match_combinations(codes, combos)))


# ── 분류체계 독립 정의 (PLAN-009) ───────────────────────────────────────
#
# 왜 별도의 층인가. 위의 2층 조합은 **분류코드**로 개념을 정의한다 — 그런데 그 코드(H10*)가
# 전량 2021년 이후 신설이고 과거 특허에 소급 부여된다는 것이 PLAN-007 에서 드러났다.
# 개념이 코드에 기생하면 개념은 코드보다 앞설 수 없고, 그러면 H2 는 검정되기 전에 진다.
#
# 그래서 si 정의는 **분류코드를 일절 보지 않는다.** 개념 팔은 명세 텍스트(구조 어휘)만,
# 코드 팔은 분류체계만 본다 — 두 팔이 서로 다른 증거원을 보게 되어 코드 기생도, 부분집합
# 자명성(개념 ⊇ 코드)도 함께 사라진다. 정의의 근거는 외부 표준(JEDEC · IRDS)이다.
#
# 대가는 정직하게 치른다: 초록이 구조를 말하지 않는 특허는 개념이 놓친다.


@dataclass(frozen=True)
class TextCombination:
    """텍스트 구조식 하나. groups 는 **논리곱**, 각 group 안의 용어는 **논리합**이다.

    HBM(base) = (적층|스택) ∧ (관통전극|TSV|…) ∧ (메모리|DRAM)   ← JEDEC JESD235
    같은 (개념, 변이)에 행이 여러 개면 그 행들끼리는 **논리합**이다 — 구조식 경로와
    이름 경로를 한 정의 안에서 합집합으로 쓰기 위해서다.
    """

    concept_iri: str
    variant: str
    groups: tuple[tuple[str, ...], ...]

    def matches(self, text: str) -> bool:
        hay = text.lower()
        return bool(self.groups) and all(
            any(_term_in(term, hay) for term in group) for group in self.groups
        )


def parse_text_definition(expr: str) -> tuple[tuple[str, ...], ...]:
    """'가|나 AND 다' → (('가','나'), ('다',)). 코드 정규화를 하지 않는다 — 용어이지 코드가 아니다."""
    return tuple(
        tuple(t.strip() for t in group.split("|") if t.strip())
        for group in expr.split(" AND ")
        if group.strip()
    )


def load_si_combinations(
    path: Path = SI_CONCEPTS, variant: str = DEFAULT_VARIANT
) -> list[TextCombination]:
    if variant not in VARIANTS:
        raise ValueError(f"알 수 없는 variant: {variant!r} (허용: {VARIANTS})")
    df = pd.read_csv(path)
    df = df[df["variant"] == variant]
    return [
        TextCombination(
            concept_iri=str(r["concept_iri"]).strip(),
            variant=variant,
            groups=parse_text_definition(str(r["definition"])),
        )
        for _, r in df.iterrows()
    ]


def si_devices(text: str, combos: list[TextCombination]) -> list[str]:
    """특허 1건이 가리키는 신기술 개념 — **텍스트만** 본다 (PLAN-009)."""
    return sorted({c.concept_iri for c in combos if c.matches(text)})


# ── H2′ · 명칭 대조군과 구조 전용 개념 (PLAN-010) ─────────────────────────
#
# 코드 대조군이 시간적으로 무효라(소급 재분류 · 2017 해상도 바닥) H2 를 검정할 수 없었다.
# **명세 텍스트는 소급 재작성되지 않는다** — 2010년 특허의 초록은 지금도 2010년의 초록이다.
# 그래서 시점 유효한 대조군을 하나 더 세운다: 그 기술의 **명칭**으로 검색하기.
# 온톨로지 없는 실무자가 실제로 하는 일이고, 온톨로지가 이겨야 할 대상이다.


def load_name_terms(path: Path = NAME_BASELINE) -> dict[str, list[str]]:
    """{개념 IRI: [명칭 용어...]} — H2′ 의 대조군."""
    df = pd.read_csv(path)
    return {
        str(r["concept_iri"]).strip(): [t.strip() for t in str(r["terms"]).split("|") if t.strip()]
        for _, r in df.iterrows()
    }


def strip_name_terms(
    combos: list[TextCombination], names: dict[str, list[str]]
) -> list[TextCombination]:
    """개념 정의에서 **명칭 용어를 뺀다** — 구조 어휘만 남긴 개념 (H2′ 의 강건성 검정).

    왜 필요한가: si 정의는 구조 ∪ 명칭이라 명칭 대조군을 **포함한다**(개념 ⊇ 이름). 그대로
    비교하면 부분집합 자명성이 다시 들어온다 — PLAN-006 이 코드에서 겪은 그 함정이다.
    명칭을 빼면 두 팔이 **서로소**가 되고, 그때 비교는 진짜 양방향이 된다.

    그리고 그것이 이 논문의 논지 자체다 — **특허는 기술을 이름으로 부르기 전에 구조로 말한다.**
    용어가 전부 빠져 빈 그룹이 생기면 그 조합은 발화할 수 없으므로 **버린다**(명칭 전용 행).
    """
    out = []
    for c in combos:
        drop = {t.lower() for t in names.get(c.concept_iri, [])}
        groups = tuple(
            tuple(t for t in group if t.lower() not in drop) for group in c.groups
        )
        if all(groups) and groups:  # 빈 그룹이 하나라도 있으면 이 조합은 성립하지 않는다
            out.append(TextCombination(c.concept_iri, c.variant, groups))
    return out
