"""IR 시연 패널 — 화면 수치가 실험 수치와 같은가, 그리고 봉인을 지키는가.

이 패널은 새 실험을 하지 않고 M4 산출물을 재구성한다. 따라서 계약은 셋이다:
① 실험과 같은 재랭크 결과를 낼 것(수치 표류 = 결함) ② test 질의를 절대 노출하지 않을 것
③ 재랭크 천장(풀 밖 정답)을 감추지 않을 것.

**①의 기준값은 팔(자원 스냅샷)마다 다르다 — 그래서 상수로 박지 않는다.** 패널은 B3 run 파일만
읽고 온톨로지 재랭크는 **현재 디스크의 자원으로 다시 계산**한다. 그래서 `make vendor` 로 스냅샷이
바뀌면 run 파일이 그대로여도 화면 수치가 움직인다(O→O′ 에서 dev 평균 P0★ 0.4193 → 0.4071).
기준값을 하드코딩하면 자원이 바뀔 때마다 "테스트가 깨졌다"로 나타나고, 실제로 그렇게 깨진 채
방치됐다(PLAN-036 §12). 그래서 기대값은 **파이프라인 서명별로** `tests/fixtures/ir_panel_expected.json`
에 두고, 현재 팔의 항목과 대조한다. 팔이 바뀌면 실패 메시지가 **기록 명령**을 안내한다 —
"수치가 틀렸다"가 아니라 "팔이 바뀌었다"로 읽히게 하는 것이 이 설계의 요점이다.
"""
from __future__ import annotations

import json

import pytest

from sdkb_paper.explore import ir_panel

pytestmark = pytest.mark.skipif(
    not ir_panel.ready(), reason="IR 산출물 없음 — make index·retrieve 후 실행"
)

EXAMPLE = ir_panel.EXAMPLE_QID


@pytest.fixture(scope="module")
def demo():
    return ir_panel.demo()


@pytest.fixture(scope="module")
def expected(demo):
    """현재 팔의 기대값. 없으면 **명시적으로 실패**한다 — 조용히 건너뛰면 계약이 사라진다."""
    path = ir_panel.EXPECTED_PATH
    book = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    prov = demo.provenance()
    key = prov["pipeline_short"]
    if key not in book:
        pytest.fail(
            f"현재 자원 팔의 기대값이 없다 — 팔이 바뀌었다.\n"
            f"  pipeline_sig={key} · arm={prov['arm']} · parts={prov['parts']}\n"
            f"  기록: uv run python -m sdkb_paper.explore.ir_panel --record\n"
            f"  (기존 팔의 기록은 덮이지 않는다. 기록 전에 팔이 의도한 것인지 먼저 확인하라.)"
        )
    return book[key]


def test_selected_weights_are_the_frozen_ones(demo) -> None:
    """가중치는 dev 격자선택 결과여야 한다 — 뷰어가 임의 값으로 유리하게 보이면 안 된다."""
    from sdkb_paper.analysis.ontology_eval import SELECTED_ALPHA, SELECTED_W

    assert demo.alpha == SELECTED_ALPHA
    assert tuple(demo.w) == tuple(SELECTED_W)


def test_only_dev_queries_are_exposed(demo) -> None:
    """test 질의는 봉인이다 — 목록·상세 어느 경로로도 나오면 안 된다."""
    import pandas as pd

    from sdkb_paper import config

    sp = pd.read_parquet(config.IR_SPLIT)
    test_ids = set(sp.loc[sp["split"] == "test", "doc_id"].astype(str))
    listed = {q["qid"] for q in demo.queries()["queries"]}
    assert listed and not (listed & test_ids)
    with pytest.raises(ValueError):
        demo.detail(next(iter(test_ids)))


def test_provenance_names_the_arm(demo) -> None:
    """화면은 자기가 어느 팔인지 말할 수 있어야 한다(§12 · 표류를 팔 문제로 드러낸다)."""
    prov = demo.provenance()
    assert len(prov["pipeline_sig"]) == 64
    assert prov["parts"]["ir_corpus"], "코퍼스 해시가 비었다 — 서명이 공허하다"


def test_mean_recall_matches_experiment(demo, expected) -> None:
    """dev 평균 R@100 은 **이 팔에 기록된** 값과 같아야 한다."""
    q = demo.queries()
    assert q["n_queries"] == expected["n_queries"]
    assert q["mean_b3"] == pytest.approx(expected["mean_b3"], abs=5e-4)
    assert q["mean_p0"] == pytest.approx(expected["mean_p0"], abs=5e-4)


def test_text_baseline_is_arm_independent(expected) -> None:
    """B3 는 텍스트 전용이라 자원 팔이 바뀌어도 움직이지 않는다 — 기록 자체를 계약으로 건다.

    이 값이 팔마다 다르면 온톨로지가 텍스트 기준선에 샜다는 뜻이고, 그때는 비교가 무효다.
    """
    book = json.loads(ir_panel.EXPECTED_PATH.read_text(encoding="utf-8"))
    means = {v["mean_b3"] for v in book.values()}
    assert len(means) == 1, f"팔마다 B3 평균이 다르다 — 누출 의심: {means}"


def test_example_query_reproduces_recorded_rank_movement(demo, expected) -> None:
    """예시 질의의 순위 이동이 이 팔의 기록과 같아야 한다 — 어긋나면 기록이나 코드가 틀렸다."""
    d = demo.detail(EXAMPLE)
    gold = {g["doc_id"]: g for g in d["gold"]}
    exp = expected["example"]
    assert len(gold) == exp["n_gold"]
    for doc_id, e in exp["gold"].items():
        got = gold[doc_id]
        if e["rank_b3"] is not None:
            assert got["rank_b3"] == e["rank_b3"], doc_id
        if e["rank_p0"] is not None:
            assert got["rank_p0"] == e["rank_p0"], doc_id
        if e["n_shared_concepts"] is not None:
            assert len(got["shared_concepts"]) == e["n_shared_concepts"], doc_id


def test_rerank_ceiling_is_reported_honestly(demo) -> None:
    """풀 밖 정답은 풀 밖으로 정직하게 보고된다 — 감추면 재랭크 천장이 안 보인다."""
    d = demo.detail(EXAMPLE)
    gold = {g["doc_id"]: g for g in d["gold"]}
    out_of_pool = gold["jp_JP07091636B2"]
    assert out_of_pool["rank_p0"] is None
    assert out_of_pool["shared_concepts"] == []
