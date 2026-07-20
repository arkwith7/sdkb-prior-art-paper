"""온톨로지 뷰어 — 점진 확장이 계약을 지키는가.

G₁·G₂ 는 41만 트리플이다. 뷰어의 존재 이유는 **전량을 그리지 않는 것**이므로,
계약은 셋이다: 초기 화면이 작을 것, 상한에 걸리면 말할 것, 없는 링크를 그리지 않을 것.
"""
from __future__ import annotations

import pytest

from sdkb_paper.config import GRAPH_V0, GRAPH_V1
from sdkb_paper.explore import viewer

PLASMA_ETCH = "https://w3id.org/sdkb/data/subprocess/plasma_etch"

pytestmark = pytest.mark.skipif(
    not GRAPH_V0.exists(), reason="graph_v0 없음 — make baseline 후 실행"
)


def test_domain_map_is_small_enough_to_render() -> None:
    """초기 화면은 노드 100개 미만이어야 한다 — 41만 트리플을 그릴 수는 없다."""
    d = viewer.domain_map("v0")
    assert d["mode"] == "domain"
    assert 0 < len(d["nodes"]) < 100
    assert {n["cls"] for n in d["nodes"]} == {"Process", "SubProcess", "Device"}


def test_domain_map_covers_every_step() -> None:
    """H1 의 관측 단위 49개가 하나도 빠지지 않아야 한다 — 빠지면 지도가 거짓말을 한다."""
    d = viewer.domain_map("v0")
    steps = [n for n in d["nodes"] if n["cls"] in ("Process", "SubProcess")]
    assert len(steps) == 49
    assert len([n for n in d["nodes"] if n["cls"] == "Device"]) == 34


def test_domain_edges_are_only_real_links() -> None:
    """소자↔공정 직접 엣지는 그래프에 없다 — 보기 좋으라고 만들어 넣지 않는다."""
    d = viewer.domain_map("v0")
    cls = {n["id"]: n["cls"] for n in d["nodes"]}
    for e in d["edges"]:
        assert e["pred"] == "hasSubprocess"
        assert cls[e["src"]] == "Process" and cls[e["dst"]] == "SubProcess"
    assert "특허가 매개한다" in d["note"]


def test_patent_counts_are_measured_not_guessed() -> None:
    d = viewer.domain_map("v0")
    by_label = {n["label"]: n for n in d["nodes"]}
    assert by_label["Plasma Etch"]["patents"] > 0
    # G₀ 는 공백 29단계를 갖는다(§6.3) — 0 인 단계가 실제로 있어야 지도가 현실을 그린 것이다.
    assert [n for n in d["nodes"] if n["cls"] in ("Process", "SubProcess") and n["patents"] == 0]


def test_definitions_are_present_not_fabricated() -> None:
    """툴팁 설명은 그래프의 skos:definition 이다. 없으면 None 이지 지어내지 않는다."""
    d = viewer.domain_map("v0")
    plasma = next(n for n in d["nodes"] if n["label"] == "Plasma Etch")
    assert plasma["definition"] and "plasma" in plasma["definition"].lower()
    assert all(n["definition"] is None or isinstance(n["definition"], str) for n in d["nodes"])


def test_expand_reports_truncation() -> None:
    """상한에 걸리면 말한다 — 조용히 자르면 '이게 전부'로 읽힌다."""
    small = viewer.expand("v0", PLASMA_ETCH, limit=3)
    assert len(small["nodes"]) <= 3
    assert small["truncated"] is True
    for e in small["edges"]:
        assert PLASMA_ETCH in (e["src"], e["dst"])


def test_detail_exposes_labels_and_props() -> None:
    d = viewer.detail("v0", PLASMA_ETCH)
    assert d["label"] == "Plasma Etch"
    assert d["axis_ko"] == "하위 공정"
    assert d["definition"]
    assert not [p for p in d["props"] if p["pred"] in ("prefLabel", "altLabel", "type")]


@pytest.mark.skipif(not GRAPH_V1.exists(), reason="graph_v1 없음")
def test_promoted_korean_aliases_are_visible() -> None:
    """승격한 한국어 별칭이 뷰어 상세에 실제로 보이는가(SDKB da745ef)."""
    d = viewer.detail("v1", PLASMA_ETCH)
    assert {"플라즈마 식각", "건식식각"} <= set(d["alt_labels"])


@pytest.mark.skipif(not GRAPH_V1.exists(), reason="graph_v1 없음")
def test_domain_map_is_cached() -> None:
    """상주 그래프는 불변이므로 두 번째 호출은 같은 객체여야 한다(G₂ 첫 호출 ~1s)."""
    assert viewer.domain_map("v1") is viewer.domain_map("v1")


# ── 인력·문제 축 ────────────────────────────────────────────────────
def test_people_map_is_bridged_by_skill() -> None:
    """전문가와 실무문제는 역량을 통해 붙는다 — 역량이 이 지도의 다리다."""
    d = viewer.people_map("v0")
    assert d["mode"] == "people"
    skills = [n for n in d["nodes"] if n["cls"] == "Skill"]
    assert len(skills) == 12
    assert all("experts" in n and "problems" in n for n in skills)
    assert {e["pred"] for e in d["edges"]} == {"requiresSkill"}


def test_people_map_shows_the_staffing_gap() -> None:
    """지도의 쓸모는 불균형이 그대로 보이는 것이다 — 채우거나 감추지 않는다."""
    d = viewer.people_map("v0")
    skills = {n["label"]: n for n in d["nodes"] if n["cls"] == "Skill"}
    assert skills["Defect Analysis"]["problems"] > skills["Defect Analysis"]["experts"]
    assert [n for n in skills.values() if n["experts"] == 0]  # 전문가 0인 역량이 실재한다


def test_category_nodes_are_marked_as_derived() -> None:
    """문제 범주는 problemCategory 집계지 그래프의 개체가 아니다 — 구분해 표시한다."""
    d = viewer.people_map("v0")
    cats = [n for n in d["nodes"] if n["cls"] == "ProblemCategory"]
    assert cats and all(n["derived"] and n["id"].startswith(viewer.CATEGORY_PREFIX) for n in cats)
    assert "집계 노드" in d["note"]


def test_expand_category_returns_its_problems() -> None:
    d = viewer.expand_category("v0", "yield_improvement")
    assert d["nodes"] and all(n["cls"] == "Problem" for n in d["nodes"])
    assert all(e["src"] == viewer.CATEGORY_PREFIX + "yield_improvement" for e in d["edges"])


def test_expand_category_quotes_cannot_break_the_query() -> None:
    """범주 값은 리터럴로 들어간다 — 따옴표가 섞여도 질의가 깨지지 않아야 한다."""
    assert viewer.expand_category("v0", 'no"such\\category')["nodes"] == []
