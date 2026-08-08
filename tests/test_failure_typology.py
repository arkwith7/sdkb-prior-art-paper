"""실패 유형 분류 (PLAN-048 §10) — 동결 상수·분해 항등식·κ·가림 누출.

**이 테스트가 지키는 것.** 동결된 것은 값이지 코드가 아니므로, 값이 바뀌면 테스트가 깨져야
한다(§1-3). 그래서 임계·표본·시드·유형 목록을 **테스트가 함께 고정**한다 — C2′ T4 마진을
테스트가 고정한 것과 같은 방식이다.
"""
from __future__ import annotations

import json

import pytest

from sdkb_paper.analysis import failure_typology as ft


# --- 동결 상수 ---------------------------------------------------------------
def test_frozen_constants():
    assert ft.SEV_RANK_DROP == 20
    assert ft.N_COMPETITORS == 3
    assert ft.HUMAN_SAMPLE == 40
    assert ft.SEED == 20260809
    assert list(ft.TYPES) == ["F1", "F2", "F3", "F4", "F5", "F6", "F7"]


def test_frozen_scoring_weights_match_p1():
    """분해는 P1 이 실제로 쓴 가중치를 써야 한다 — 다른 값을 쓰면 분해가 거짓이 된다."""
    from sdkb_paper.analysis.results_table import P1_ALPHA, P1_TAU, P1_W4

    assert (P1_TAU, P1_ALPHA, P1_W4) == (0.7, 0.75, (0.25, 0.0, 0.25, 0.5))
    assert (ft._WC, ft._WH, ft._WI, ft._WF) == P1_W4


# --- 분해 --------------------------------------------------------------------
ROW_A = (0.90, 0.20, 0.10, 0.30, 0.40)      # (text_norm, concept, path, ipc, fc)
ROW_B = (0.80, 0.50, 0.10, 0.30, 0.40)


def test_score_terms_sum_equals_p1_score():
    """항별 기여의 합 = P1 점수. 이 항등식이 깨지면 분해는 설명이 아니라 창작이다."""
    from sdkb_paper.analysis.results_table import P1_ALPHA, P1_W4

    tn, c, p, ic, f = ROW_A
    wc, wh, wi, wf = P1_W4
    expected = (1 - P1_ALPHA) * tn + P1_ALPHA * (wc * c + wh * p + wi * ic + wf * f)
    assert ft.score_terms(ROW_A)["text"] + sum(
        v for k, v in ft.score_terms(ROW_A).items() if k != "text") == pytest.approx(expected)


def test_path_term_is_structurally_zero():
    """w_h = 0 이므로 계층 항은 어떤 입력에서도 0 이다 — 원고가 사전 자인한 구조적 0."""
    assert ft.score_terms((0.1, 0.1, 1.0, 0.1, 0.1))["path"] == 0.0


def test_decompose_driver_and_share():
    d = ft.decompose(ROW_A, ROW_B)
    assert d["driver"] == "concept"
    assert 0.0 <= d["driver_share"] <= 1.0
    assert d["gap"] == pytest.approx(sum(d["delta"].values()))


def test_driver_share_bounded_when_terms_cancel():
    """상쇄가 있어도 비율이 1 을 넘지 않는다 — 순 격차를 분모로 쓰면 넘었다(실측 19.58)."""
    lost = (0.95, 0.30, 0.0, 0.10, 0.0)
    comp = (0.80, 0.28, 0.0, 0.40, 0.10)    # text·concept 는 손해, ipc·feature 로 뒤집는 형태
    d = ft.decompose(lost, comp)
    assert d["gap"] > 0
    assert d["driver"] == "ipc"
    assert d["driver_share"] == pytest.approx(0.6)   # 순 격차를 분모로 쓰면 1.07 이 된다


# --- κ ------------------------------------------------------------------------
def test_kappa_perfect_and_chance():
    a = ["F1", "F2", "F3", "F1"]
    assert ft.cohen_kappa(a, a) == pytest.approx(1.0)
    assert ft.agreement(a, a) == 1.0
    # 완전 불일치 · 주변분포가 겹치지 않으면 κ 는 음수
    assert ft.cohen_kappa(["F1", "F1"], ["F2", "F2"]) <= 0.0


def test_kappa_degenerate_inputs():
    assert ft.cohen_kappa([], []) == 0.0
    assert ft.cohen_kappa(["F1"], ["F1", "F2"]) == 0.0
    # 두 코더가 전 항목을 같은 한 범주로 찍으면 우연 일치가 1 이라 κ 는 정의되지 않는다 → 0
    assert ft.cohen_kappa(["F1", "F1"], ["F1", "F1"]) == 0.0


# --- 파서 ---------------------------------------------------------------------
def test_parse_label_accepts_fenced_and_trailing_prose():
    """C2′ §17.2 와 같은 고장(펜스 뒤 산문)을 같은 파서로 흡수한다."""
    assert ft.parse_label('{"primary": "F4"}')["primary"] == "F4"
    assert ft.parse_label('```json\n{"primary": "F4"}\n```')["primary"] == "F4"


def test_parse_label_rejects_unknown_type():
    assert ft.parse_label('{"primary": "F9"}') is None
    assert ft.parse_label("설명만 있고 JSON 이 없다") is None


# --- 가림 --------------------------------------------------------------------
def test_sheet_is_blinded(tmp_path, monkeypatch):
    """시트에 팔 이름·순위·정답 여부가 새어 나가지 않는다."""
    sheet = ft.TYPOLOGY_DIR / "sheet_test.jsonl"
    if not sheet.exists():
        pytest.skip("시트 미생성 — `make typology-sheet` 후 검사")
    text = sheet.read_text(encoding="utf-8")
    for leak in ("B3_rrf", "rank_b3", "rank_p1", "r100_loss", "lost_doc", "positive"):
        assert leak not in text, f"가림 누출: {leak}"
    # 팔 이름은 부분문자열 검사가 안 된다 — IPC 코드 `B23P11-00` 이 "P1" 을 품는다(실측).
    # JSON 의 키·값 토큰으로만 찾는다.
    import re

    for arm in ("P1", "P0star", "B3"):
        assert not re.search(rf'"[^"]*\b{arm}\b[^"]*"', text), f"가림 누출: {arm}"
    row = json.loads(text.splitlines()[0])
    assert row["focus_slot"].startswith("문서 ")
    assert all(d["slot"].startswith("문서 ") for d in row["documents"])
    assert "doc_id" not in row["documents"][0]


def test_key_file_holds_what_sheet_hides():
    """가린 정보는 버리는 것이 아니라 열쇠 파일에 남는다 — 사후 대조가 가능해야 한다."""
    key = ft.TYPOLOGY_DIR / "key_test.jsonl"
    if not key.exists():
        pytest.skip("열쇠 미생성")
    row = json.loads(key.read_text(encoding="utf-8").splitlines()[0])
    assert {"unit_id", "qid", "lost_doc", "rank_b3", "rank_p1", "drop"} <= set(row)


def test_human_sample_is_deterministic():
    key = ft.TYPOLOGY_DIR / "key_test.jsonl"
    if not key.exists():
        pytest.skip("열쇠 미생성")
    a = json.loads(ft.human_sample().read_text(encoding="utf-8"))
    b = json.loads(ft.human_sample().read_text(encoding="utf-8"))
    assert a == b and len(a) <= ft.HUMAN_SAMPLE


def test_human_sample_spans_both_layers():
    """표본은 층별 40 이 아니라 **두 층 합쳐 40** 이다 — 층이 갈리면 사람 부담이 두 배가 된다."""
    if not (ft.TYPOLOGY_DIR / "key_test_b.jsonl").exists():
        pytest.skip("B층 열쇠 미생성")
    ids = json.loads(ft.human_sample().read_text(encoding="utf-8"))
    assert len(ids) == ft.HUMAN_SAMPLE
    assert {i.split(":")[0] for i in ids} == {"test", "test_b"}
