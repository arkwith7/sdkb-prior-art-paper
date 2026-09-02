"""예시 델타 서사의 회귀 테스트 (PLAN-087 §8 ②).

원고 §3.4·§4.4·§5.4 의 관통 예시는 "예시 델타 A(동의어 오병합)는 형식·주 태스크 층을 통과하고
공정 계층 질의(CQ21)에서만 걸린다" · "예시 델타 B(사례 재배치)는 CQ28 에서만 걸린다" 는 서사에
기대고 있다. 픽스처(mini_graph.ttl)나 CQ 파일이 바뀌어 이 서사가 깨지면 원고가 조용히 거짓이
되므로, 여기서 회귀 CQ 집합을 그대로 단언한다.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "example_delta_demo.py"


def _load():
    spec = importlib.util.spec_from_file_location("example_delta_demo", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def demo():
    return _load()


@pytest.mark.parametrize("delta", ["merge_etch_into_plasma", "relocate_case_failuremode"])
def test_regressed_cq_set_matches_manuscript_narrative(demo, delta):
    r = demo.evaluate(delta)
    assert r["regressed"] == demo.EXPECTED_REGRESSED[delta], (
        f"예시 델타 {delta} 의 회귀 CQ 집합이 서사와 다르다: {sorted(r['regressed'])}"
    )
    assert r["l3_pass"], "예시 델타는 주 태스크(pa) 스위트를 통과해야 한다 — T3 단독 검출 서사의 전제"
    assert not r["t3_pass"], "예시 델타는 T3 에서 걸려야 한다"


def test_delta_a_preserves_or_grows_prior_art_answers(demo):
    """서사의 둘째 절반 — 동의어 오병합은 선행기술조사 쪽에서는 '개선'으로 보인다."""
    r = demo.evaluate("merge_etch_into_plasma")
    pa = {row[0]: (row[4], row[5]) for row in r["rows"] if row[1] == "pa" and row[0] not in demo.SIDECAR}
    assert all(after >= before for before, after in pa.values()), pa


def test_delta_b_changes_exactly_one_triple(demo):
    r = demo.evaluate("relocate_case_failuremode")
    assert r["changed"] == 1 and r["n0"] == r["n1"], "간선 수 보존 결함(F14 축소판)이어야 한다"
