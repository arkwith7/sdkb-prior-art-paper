"""개념·공리 계기판의 계약 (2026-08-23 · CLAUDE.md §0 표현의 세 층).

이 테스트가 지키는 것 셋.
  ① **어휘 선언을 공리로 세지 않는다** — `subClassOf`·`domain`·`range` 를 세면 계기판이
     늘 녹색이 되고, 그것이 지금까지의 착시였다.
  ② 계기판은 **읽기만 한다** — 코퍼스·qrel·게이트 산출물을 쓰지 않는다.
  ③ 델타 표기가 직전 실행과의 차이를 정확히 낸다 — 틀리면 "진척"이 거짓이 된다.
"""
from __future__ import annotations

import json

import pytest

from sdkb_paper import config
from sdkb_paper.analysis import concept_status as cs

MD = config.ROOT / "data" / "reports" / "concept_status.md"
JSON = config.ROOT / "data" / "reports" / "concept_status.json"


def test_inferential_set_excludes_vocabulary_declarations():
    """RDFS 어휘 선언은 추론 공리 목록에 없다."""
    keys = set(cs.INFERENTIAL)
    for vocab in ("rdfs:subClassOf", "rdfs:domain", "rdfs:range", "rdfs:subPropertyOf"):
        assert vocab not in keys


def test_delta_renders_only_on_change():
    assert cs._delta(3, 3) == ""
    assert cs._delta(3, None) == ""
    assert cs._delta(5, 3) == " (+2)"
    assert cs._delta(0.5, 1.5) == " (-1)"


def test_report_matches_stored_json():
    """커밋된 산출물이 생성기와 어긋나면(손편집) 계기판이 거짓말을 한다."""
    if not JSON.exists():
        pytest.skip("계기판 미생성 — make concept-status")
    stored = json.loads(JSON.read_text(encoding="utf-8"))
    text = MD.read_text(encoding="utf-8")
    d = stored["declared"]
    assert f"**{d['inferential_total']}" in text
    assert (f"{d['prior_art_axis_with_axioms']} / {len(d['prior_art_axis'])}") in text


def test_prior_art_axis_axioms_are_reported_not_assumed():
    """중심축 항목은 전량 열거된다 — 빠뜨리면 '없음'이 보이지 않는다."""
    if not JSON.exists():
        pytest.skip("계기판 미생성")
    axis = json.loads(JSON.read_text(encoding="utf-8"))["declared"]["prior_art_axis"]
    assert set(axis) == set(cs.AXIS_TERMS)
    for name, v in axis.items():
        assert isinstance(v["inferential_axioms"], list), name


def test_status_never_touches_sealed_artifacts():
    """봉인 qrel·분할을 읽지 않는다.

    **주석이 아니라 코드를 본다** — 모듈 docstring 은 그것을 읽지 않는다고 *설명*하므로,
    문자열 검사만 하면 설명이 위반으로 잡힌다. 그래서 docstring 을 떼고 검사한다.
    """
    import ast

    path = config.ROOT / "src" / "sdkb_paper" / "analysis" / "concept_status.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            node.body = [n for n in node.body
                         if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
                                 and isinstance(n.value.value, str))]
    code = ast.unparse(tree)
    for forbidden in ("QREL", "qrel", "test_b", "SPLIT", "split.parquet"):
        assert forbidden not in code, f"계기판이 {forbidden} 를 만진다"
