"""F11 어휘중첩·거절근거 하위집단 라벨 단위 테스트 (원고 §5.3·§6.4).

데이터 파일을 요구하지 않는 순수 함수와, 벤더 스냅샷이 있을 때만 도는 계약 검사를 나눈다.
"""
from __future__ import annotations

import pytest

from sdkb_paper import config
from sdkb_paper.analysis import overlap


def test_normalize_strips_stopwords_and_punctuation():
    t = overlap.normalize("청구항 1. 상기 플라즈마 식각(etching) 방법!!")
    assert "청구항" not in t and "상기" not in t
    assert "플라즈마" in t and "etching" in t
    assert "!" not in t and "(" not in t


def test_char_ngrams_size_and_short_text():
    assert overlap.char_ngrams("가나다라", n=3) == {"가나다", "나다라"}
    assert overlap.char_ngrams("가", n=3) == set()      # 길이 미달 → 공집합


def test_jaccard_bounds():
    a, b = {"x", "y"}, {"y", "z"}
    assert overlap.jaccard(a, a) == 1.0
    assert abs(overlap.jaccard(a, b) - 1 / 3) < 1e-12
    assert overlap.jaccard(a, set()) == 0.0            # 빈 집합은 0(0 나눗셈 금지)


def test_overlap_is_deterministic():
    """같은 입력 → 같은 점수. 층화 라벨이 실행마다 흔들리면 §6.4 표가 재현되지 않는다."""
    t1, t2 = "플라즈마 식각 공정", "플라즈마 건식 식각"
    g1, g2 = overlap.char_ngrams(t1), overlap.char_ngrams(t2)
    assert overlap.jaccard(g1, g2) == overlap.jaccard(overlap.char_ngrams(t1),
                                                      overlap.char_ngrams(t2))


@pytest.mark.skipif(not config.IR_OVERLAP_THRESHOLD.exists(),
                    reason="F11 임계 미동결(analysis.overlap --freeze 선행)")
def test_frozen_threshold_contract():
    """동결 파일은 dev 에서 산출된 Q1 이어야 한다 — test 분포로 다시 잡지 않았음의 증거."""
    import json
    rec = json.loads(config.IR_OVERLAP_THRESHOLD.read_text(encoding="utf-8"))
    assert rec["source_split"] == "dev"
    assert rec["metric"].startswith("char_") and rec["agg"] == "mean"
    assert rec["min"] <= rec["q1_threshold"] <= rec["median"] <= rec["q3"] <= rec["max"]


@pytest.mark.skipif(not config.REJECTION_BASIS.exists(),
                    reason="거절근거 스냅샷 미벤더(vendor --derive-rejection 선행)")
def test_rejection_labels_have_no_fulltext_and_known_values():
    """라벨 CSV 는 식별자+법조만 담는다(원문 커밋 금지 §1-5) · 값 집합은 넷뿐."""
    import csv

    from sdkb_paper.analysis.subgroup import rejection_labels
    with config.REJECTION_BASIS.open(encoding="utf-8") as f:
        cols = set(next(csv.reader(f)))
    assert not (cols & {"title", "abstract", "claim1", "claims_full"})

    labs = rejection_labels()
    assert set(labs.values()) <= {"inventiveness", "novelty+inventiveness",
                                  "novelty_only", "unlabeled"}
    # 자원 사실(2026-07-27 실측): 신규성 단독 거절은 존재하지 않는다.
    # 이 단정이 깨지면 §6.4 의 "검정 불가" 서술을 갱신해야 한다 — 조용히 통과시키지 않는다.
    assert sum(v == "novelty_only" for v in labs.values()) == 0
