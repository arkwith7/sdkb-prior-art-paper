"""결정 안정성 표 생성기의 계약 (PLAN-060 B3).

이 표가 지켜야 하는 것은 하나다 — **동결 임계에서 내린 판정과 전환점의 거리만 보고하고,
임계 자체는 움직이지 않는다.** 그래서 검사도 셋뿐이다.
  ① 수치를 만들어내지 않는다 — 표의 모든 값이 입력 산출물에 실재한다.
  ② 전환점은 관측된 하한·최대 하락에서 코드가 계산한다.
  ③ 디스크의 표가 산출물과 어긋나면 --check 가 실패한다(파생본 조립이 이것을 먼저 탄다).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from sdkb_paper.analysis import decision_stability as ds

CONCEPT = Path("paper/figures/data/concept_values.json")
FAULTS = Path("data/processed/fault_matrix_v4.json")

pytestmark = pytest.mark.skipif(
    not (CONCEPT.exists() and FAULTS.exists() and ds.T4_VERDICT.exists()),
    reason="입력 산출물이 없는 환경 — 생성기는 산출물에서만 읽는다",
)


@pytest.fixture(scope="module")
def table() -> str:
    return ds.build()


def test_frozen_thresholds_are_reported_unchanged(table: str) -> None:
    """§3.5 에서 동결한 임계가 그대로 실린다 — 표는 임계를 조정하지 않는다."""
    assert "ε = 0.02" in table
    assert "δ = 0.05" in table
    assert "ε_T4 = 0.02" in table


def test_observed_values_come_from_artifacts(table: str) -> None:
    """관측값은 전부 입력 산출물에 실재한다(§1-1 — 손으로 적지 않는다)."""
    values = json.loads(CONCEPT.read_text(encoding="utf-8"))["values"]
    faults = json.loads(FAULTS.read_text(encoding="utf-8"))["holdout"]["by_tau"]

    assert f"{abs(values['ep3.p1.ci_lo']['value']):.4f}" in table
    assert f"{values['ep3.t2_max_drop']['value']:.4f}" in table
    for key, block in faults.items():
        main = block["main"]
        assert f"{main['n_t3_only']}/{main['n_cross']}" in table
        assert f"τ = {float(key):.2f}" in table


def test_flip_points_are_derived_not_typed(table: str) -> None:
    """전환점은 하한의 절댓값이다 — 별도의 새 수치가 아니다."""
    values = json.loads(CONCEPT.read_text(encoding="utf-8"))["values"]
    t1_lb = abs(values["ep3.p1.ci_lo"]["value"])
    t4_lb = abs(values["t4.citation_precision.lb95"]["value"])
    assert f"ε > {t1_lb:.4f}" in table
    assert f"ε_T4 > {t4_lb:.4f}" in table


def test_no_stray_numbers(table: str) -> None:
    """표에 등장하는 수치는 임계·관측·전환점·분모뿐이다 — 출처 없는 값이 섞이지 않는다."""
    values = json.loads(CONCEPT.read_text(encoding="utf-8"))["values"]
    faults = json.loads(FAULTS.read_text(encoding="utf-8"))["holdout"]["by_tau"]

    allowed = {"0.02", "0.05", "95", "100", "3.5", "0.10", "0.00", "0", "1"}
    for key, block in faults.items():
        main = block["main"]
        allowed |= {str(main["n_t3_only"]), str(main["n_cross"]), f"{float(key):.2f}"}
        p = main["mcnemar"]["p"]
        allowed.add(f"{p:.4f}".lstrip("0") if p >= 0.0001 else ".0001")
    for key in ("ep3.p1.delta", "ep3.p1.ci_lo", "ep3.t2_max_drop", "t4.citation_precision.lb95"):
        val = values[key]["value"]
        allowed |= {f"{val:.4f}", f"{abs(val):.4f}"}

    # 표 본문의 수치 토큰이 전부 허용 목록 안에 있어야 한다.
    # 게이트 이름(T1–T4)과 지표 이름(ΔR@100·LB₉₅)의 숫자는 측정값이 아니므로 먼저 뺀다.
    body = "\n".join(ln for ln in table.split("\n") if ln.startswith("|"))
    body = re.sub(r"ε_T4|T[1-4]|ΔR@100|LB₉₅", "", body).replace("−", "-")
    normalized = {a.lstrip("-.") for a in allowed} | {a.lstrip("-") for a in allowed} | allowed
    for token in re.findall(r"\d+(?:\.\d+)*", body):
        assert token in normalized, token


def test_check_mode_matches_disk() -> None:
    """디스크의 표가 산출물과 정합한다 — 어긋나면 파생본 조립이 막힌다."""
    assert ds.OUT.exists(), "make tables-stability 로 먼저 생성한다"
    assert ds.OUT.read_text(encoding="utf-8") == ds.build()
