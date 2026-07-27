"""§6.2f 교차언어 진단 단위 테스트 (PLAN-019 W1).

외부 의존(코퍼스 parquet·run 파일) 없이 순수 함수만 검증한다 — 언어별 마이크로 집계·family 해상도·
경계(빈 정답·미상 언어)·렌더 계약.
"""
from __future__ import annotations

from sdkb_paper.analysis import lang_recall as LR


def test_gold_lang_recall_counts_documents_not_queries():
    """정답 단위 마이크로 집계 — 질의 평균이 아니라 정답 문서마다 1건씩 센다."""
    run = {"q1": ["ko1", "en1", "x"], "q2": ["ko2"]}
    qrel = {"q1": {"ko1", "en1", "en2"}, "q2": {"ko2"}}
    lang = {"ko1": "ko", "ko2": "ko", "en1": "en", "en2": "en"}
    r = LR.gold_lang_recall(run, qrel, lang, fam=None, k=10)
    assert r["ko"] == {"n": 2, "hit_doc": 2, "hit_fam": 0,
                       "recall_doc": 1.0, "recall_fam": 0.0}
    assert r["en"]["n"] == 2 and r["en"]["hit_doc"] == 1
    assert r["en"]["recall_doc"] == 0.5


def test_family_resolution_rescues_sibling_publication():
    """정답 문서 자체는 못 찾아도 같은 패밀리의 형제 공개를 찾으면 recall_fam 은 회수로 센다."""
    run = {"q1": ["ko_sib"]}
    qrel = {"q1": {"en_gold"}}
    lang = {"en_gold": "en", "ko_sib": "ko"}
    fam = {"en_gold": "F1", "ko_sib": "F1"}
    r = LR.gold_lang_recall(run, qrel, lang, fam=fam, k=10)
    assert r["en"]["recall_doc"] == 0.0
    assert r["en"]["recall_fam"] == 1.0


def test_cutoff_k_is_applied():
    run = {"q1": ["a", "b", "c"]}
    qrel = {"q1": {"c"}}
    lang = {"c": "ko"}
    assert LR.gold_lang_recall(run, qrel, lang, fam=None, k=2)["ko"]["recall_doc"] == 0.0
    assert LR.gold_lang_recall(run, qrel, lang, fam=None, k=3)["ko"]["recall_doc"] == 1.0


def test_unknown_language_and_empty_positives():
    """언어 지도에 없는 문서는 'und' 로 떨어지고, 정답 0인 질의는 분모에 들어가지 않는다."""
    run = {"q1": ["z"], "q2": []}
    qrel = {"q1": {"z"}, "q2": set()}
    r = LR.gold_lang_recall(run, qrel, {}, fam=None, k=10)
    assert set(r) == {"und"} and r["und"]["n"] == 1


def test_missing_query_in_run_counts_as_miss():
    r = LR.gold_lang_recall({}, {"q1": {"d"}}, {"d": "en"}, fam=None, k=10)
    assert r["en"]["n"] == 1 and r["en"]["recall_doc"] == 0.0


def test_render_is_deterministic_and_reports_foreign_share():
    recalls = {"B0_bm25": {"ko": {"n": 2, "hit_doc": 1, "hit_fam": 1,
                                  "recall_doc": 0.5, "recall_fam": 0.5},
                           "en": {"n": 2, "hit_doc": 0, "hit_fam": 0,
                                  "recall_doc": 0.0, "recall_fam": 0.0}}}
    cov = [{"scope": "후보 문서(질의 제외)", "lang": "en", "n": 10, "concept_cov": 0.7,
            "concept_mean": 1.5, "ipc_cov": 1.0, "text_cov": 0.99, "text_median": 1100.0}]
    pool = [{"lang": "en", "n_docs": 10, "n_positive": 7, "positive_share": 0.7}]
    md = LR.render("test", recalls, cov, pool, n_q=2)
    assert md == LR.render("test", recalls, cov, pool, n_q=2)     # 결정적
    assert "비한국어 2건 = 50.0%" in md
    assert "0.000 / 0.000" in md                                   # 영어 회수 0 그대로 노출
