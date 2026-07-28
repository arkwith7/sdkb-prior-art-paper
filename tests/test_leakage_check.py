"""누출 감사 단위 테스트 (PLAN-019 W3 · 원고 §4.5·§5.6).

파일을 열지 않는 순수 함수만 검증한다 — 이름 검사(대소문자·구분자 무시)·개념값 검사·
run 마스크 잔여. 누출 검사는 **거짓 초록불이 가장 위험한** 코드라 통과 조건보다 검출 조건을
더 많이 때린다.
"""
from __future__ import annotations

from sdkb_paper.validate.leakage_check import (
    check_concept_values,
    check_names,
    check_qrel_derived,
    check_run_mask,
)


def test_forbidden_column_detected_regardless_of_style():
    """`hasPriorArtExaminer` 가 어떤 표기로 들어와도 잡는다."""
    cols = ["doc_id", "has_prior_art_examiner", "abstract"]
    assert check_names(cols) == ["has_prior_art_examiner"]
    assert check_names(["HasPriorArt"]) == ["HasPriorArt"]
    assert check_names(["novelty_score"]) == ["novelty_score"]


def test_clean_columns_pass():
    assert check_names(["doc_id", "title", "abstract", "concepts", "ipc", "lang"]) == []


def test_qrel_derived_columns_detected():
    """정답 라벨 자체가 피처 자원에 섞이는 것도 누출이다."""
    assert check_qrel_derived(["doc_id", "relevance"]) == ["relevance"]
    assert check_qrel_derived(["is_positive"]) == ["is_positive"]
    assert check_qrel_derived(["doc_id", "concepts"]) == []


def test_concept_values_scanned_entirely():
    vals = ["https://w3id.org/sdkb/data/subprocess/plasma_etch",
            "https://w3id.org/sdkb/ont/hasPriorArtExaminer"]
    assert check_concept_values(vals) == ["https://w3id.org/sdkb/ont/hasPriorArtExaminer"]
    assert check_concept_values([]) == []


def test_run_mask_violations_reported_with_rank():
    """F10 위반(자기 자신·동일 패밀리·미래 문서)이 상위 K 에 남아 있으면 전부 보고."""
    run = {"q1": ["ok1", "q1", "future1"], "q2": ["ok2"]}

    def is_allowed(qid, doc):
        return doc not in {qid, "future1"}

    viol = check_run_mask(run, is_allowed, k=10)
    assert [v["doc_id"] for v in viol] == ["q1", "future1"]
    assert viol[0]["rank"] == 2 and viol[0]["query_id"] == "q1"


def test_run_mask_respects_cutoff_k():
    """K 밖의 위반은 주지표에 영향이 없으므로 세지 않는다(검토 깊이 = K)."""
    run = {"q1": ["ok", "ok2", "bad"]}
    assert check_run_mask(run, lambda q, d: d != "bad", k=2) == []
    assert len(check_run_mask(run, lambda q, d: d != "bad", k=3)) == 1


def test_clean_run_passes():
    assert check_run_mask({"q1": ["a", "b"]}, lambda q, d: True, k=100) == []
