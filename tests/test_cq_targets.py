"""CQ 조회 대상 분리의 불변량 (PLAN-023 · N5d).

핵심은 하나다 — **사이드카 CQ 를 늘려도 게이트 분모가 움직이지 않는다**(희석 금지, §1).
사이드카 CQ 는 시험 대상 그래프에 무반응인 상수항이라 L3 분모에 들어가면 실패를 희석하고,
그것은 PLAN-022 §0.1 의 검출력 불변량을 정면으로 깬다. 아래 테스트가 그 성질을 강제한다.
"""
from __future__ import annotations

import pytest

from sdkb_paper import config
from sdkb_paper.validate.cq_runner import (
    CQResult,
    _parse_meta,
    layer_pass_counts,
    suite_pass_rates,
    target_measurements,
)

QUERIES = sorted(config.QUERIES_CQ.glob("*.rq"))


def _mk(name, suite, rows, target="graph", expect_min=1, mono="up"):
    return CQResult(name, "", expect_min, rows, suite, mono, target)


# --- 희석 금지 (사전등록 핵심) ------------------------------------------------

def test_sidecar_cqs_do_not_enter_gate_denominators():
    """사이드카 CQ 를 3개 더해도 pa 분모는 그대로 1 이다."""
    base = [_mk("CQa", "pa", 5), _mk("CQb", "em", 3)]
    with_side = base + [_mk(f"CQs{i}", "pa", 100, target="sidecar") for i in range(3)]
    assert suite_pass_rates(base)["pa"] == suite_pass_rates(with_side)["pa"]
    assert layer_pass_counts(base)["L3"] == layer_pass_counts(with_side)["L3"]


def test_sidecar_cannot_dilute_a_failure():
    """실패가 희석되지 않는다 — 이것이 규칙 A 가 막으려던 바로 그 시나리오다.

    pa 1개 실패 + 항상 통과하는 사이드카 3개를 한 분모에 넣으면 0.250 → 0.625 로 통과율이
    올라간다(게이트 완화). 분리돼 있으면 0.250 그대로여야 한다.
    """
    res = [_mk("CQfail", "pa", 0)] + [_mk(f"CQs{i}", "pa", 9, target="sidecar") for i in range(3)]
    assert suite_pass_rates(res)["pa"]["rate"] == 0.0
    assert suite_pass_rates(res)["pa"]["n_total"] == 1


def test_measurements_report_sidecar_separately():
    """게이트에서 뺐다고 사라지면 안 된다 — 보이지 않는 검사는 없는 검사다."""
    res = [_mk("CQa", "pa", 5), _mk("CQs", "pa", 0, target="sidecar")]
    m = target_measurements(res)
    assert m["graph"]["n_pass"] == 1 and m["sidecar"]["n_pass"] == 0
    assert m["sidecar"]["cqs"][0]["cq"] == "CQs"


# --- 라벨 계약 ---------------------------------------------------------------

def test_unknown_target_label_is_an_error():
    q = "# desc: x\n# suite: pa\n# monotone: up\n# target: 사이드카\nSELECT * WHERE {}"
    with pytest.raises(ValueError, match="조회 대상 라벨"):
        _parse_meta(q)


def test_missing_target_defaults_to_gate_side():
    """기본값은 **게이트에 드는 쪽**이어야 한다 — 라벨 누락이 감시를 약화시키면 안 된다."""
    q = "# desc: x\n# suite: pa\n# monotone: up\nSELECT * WHERE {}"
    assert _parse_meta(q)[4] == config.CQ_GATE_TARGET


@pytest.mark.parametrize("rq", QUERIES, ids=lambda p: p.stem)
def test_every_cq_declares_a_valid_target(rq):
    assert _parse_meta(rq.read_text(encoding="utf-8"))[4] in config.CQ_TARGETS


def test_gate_target_count_is_frozen_at_28():
    """게이트 대상 CQ 는 28개다 — 표 6.5 계열(결함주입)이 이 체제로 동결돼 있다.

    사이드카 CQ 를 더해도 이 수는 움직이지 않는다. 움직였다면 동결된 결함 실험의 분모가
    소리 없이 바뀐 것이고, 표 6.5 는 더 이상 재현되지 않는다.
    """
    targets = [_parse_meta(p.read_text(encoding="utf-8"))[4] for p in QUERIES]
    assert targets.count(config.CQ_GATE_TARGET) == 28
