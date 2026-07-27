"""IR 시연 패널 — 화면 수치가 실험 수치와 같은가, 그리고 봉인을 지키는가.

이 패널은 새 실험을 하지 않고 M4 산출물을 재구성한다. 따라서 계약은 셋이다:
① 실험과 같은 재랭크 결과를 낼 것(수치 표류 = 결함) ② test 질의를 절대 노출하지 않을 것
③ 재랭크 천장(풀 밖 정답)을 감추지 않을 것.
"""
from __future__ import annotations

import pytest

from sdkb_paper.explore import ir_panel

pytestmark = pytest.mark.skipif(
    not ir_panel.ready(), reason="IR 산출물 없음 — make index·retrieve 후 실행"
)

# M4 1차 실험(커밋 355144b·dev)에서 관측된 예시 질의. 문서 M4-실험파이프라인-설명.md §2 와 동일.
EXAMPLE = "kr_1020170018545"


@pytest.fixture(scope="module")
def demo():
    return ir_panel.demo()


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


def test_mean_recall_matches_experiment(demo) -> None:
    """dev 평균 R@100 은 마스터표와 같아야 한다(B3_masked 0.377 · P0★ 0.4193)."""
    q = demo.queries()
    assert q["n_queries"] == 197
    assert q["mean_b3"] == pytest.approx(0.377, abs=5e-4)
    assert q["mean_p0"] == pytest.approx(0.4193, abs=5e-4)


def test_example_query_reproduces_documented_rank_movement(demo) -> None:
    """문서 §2 의 148위→4위가 화면에서도 재현돼야 한다 — 어긋나면 문서나 코드가 틀렸다."""
    d = demo.detail(EXAMPLE)
    gold = {g["doc_id"]: g for g in d["gold"]}
    assert len(gold) == 3
    g = gold["kr_KR1020040035486A"]
    assert len(g["shared_concepts"]) == 5
    assert g["rank_b3"] == 148
    assert g["rank_p0"] == 4
    assert gold["kr_KR100208898B1"]["rank_b3"] == 82
    # 재랭크 천장 — 풀 밖 정답은 풀 밖으로 정직하게 보고된다
    assert gold["jp_JP07091636B2"]["rank_p0"] is None
    assert gold["jp_JP07091636B2"]["shared_concepts"] == []


def test_query_string_is_the_korean_claim_text(demo) -> None:
    """질의는 키워드가 아니라 한국어 청구항 원문이다 — 이 화면의 존재 이유."""
    q = demo.detail(EXAMPLE)["query"]
    assert "스퍼터" in q["claims_independent"]
    assert len(q["claims_independent"]) > 200
    assert "pvd" in q["concepts"]        # 개념은 메타데이터로만 동반


def test_missing_publication_date_is_blank_not_nan(demo) -> None:
    """결측 공개일이 'nan' 으로 새면 화면이 날짜를 지어낸 것처럼 보인다."""
    d = demo.detail(EXAMPLE)
    for c in d["top_b3"] + d["top_p0"]:
        assert c["publication_date"] != "nan"
