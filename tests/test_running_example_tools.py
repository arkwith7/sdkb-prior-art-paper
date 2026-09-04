"""PLAN-087 running-example generation and skim-path contracts."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_example_excerpt_is_derived_from_measured_graph():
    """PLAN-088 — 예시 1은 합성 픽스처가 아니라 실측 그래프의 거절특허다."""
    mod = _load("gen_example_excerpt")
    text = mod.render()
    assert f"pat:{mod.QID}" in text
    assert mod.CITED in text
    assert mod.SKILL in text            # 전문가 매칭 뷰로 이어지는 경로
    # §1-5 — 원문 리터럴과 제목은 어떤 경로로도 나오지 않는다.
    for pred in mod.FORBIDDEN_PREDICATES:
        assert pred not in text


def test_case_selection_rule_is_deterministic():
    """PLAN-088 §3.1 — 선정 규칙에 자유도가 없다(중앙값 근접 · 동률은 unit_id 오름차순)."""
    card = _load("gen_case_card")
    unit = card.select_unit()
    assert card.select_unit() == unit                       # 재실행해도 같다
    excerpt = _load("gen_example_excerpt")
    assert unit["qid"] == excerpt.QID                       # §3 예시와 §5 추적이 같은 특허다
    assert unit["lost_doc"] == excerpt.CITED


def test_case_card_answer_key_comes_from_the_graph_not_the_seal():
    """PLAN-088 §3.4 — 정답은 봉인 qrel 이 아니라 심사관 인용 간선에서 읽는다(O-18)."""
    card = _load("gen_case_card")
    unit = card.select_unit()
    cited = card.examiner_citations(card.config.GRAPH_V0, unit["qid"])
    assert unit["lost_doc"] in cited
    assert all("," not in c for c in cited)


def test_skim_explicit_figure_reference_pattern():
    mod = _load("skim_outline")
    assert mod.FIG_REF_RE.search("이 절의 관찰 수준은 그림 3을 다시 참조한다.")
    assert not mod.FIG_REF_RE.search("그림을 별도로 두지 않는다.")
