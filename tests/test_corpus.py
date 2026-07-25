"""IR 코퍼스 조립의 계약 — 청구항 재구성·정제·언어·결정성·산출물 불변식.

단위(순수 함수)는 외부 데이터 없이 돈다. 산출물 불변식은 parquet 이 있을 때만 검증한다
(없으면 skip — CI 는 `make corpus` 후 돌린다). CLAUDE.md §5(a)(b).
"""
from __future__ import annotations

import pandas as pd
import pytest

from sdkb_paper import config
from sdkb_paper.corpus import assemble, claim_join
from sdkb_paper.corpus import text as textmod


# --- 텍스트 정제 -------------------------------------------------------------

def test_clean_strips_html_and_normalizes_ws():
    assert textmod.clean("</P><P>플라즈마  식각</P>") == "플라즈마 식각"
    assert textmod.clean("A&amp;B") == "A&B"
    assert textmod.clean("  ") == ""
    assert textmod.clean(None) == ""


def test_detect_lang_by_script():
    assert textmod.detect_lang("반도체 식각") == "ko"        # 한글
    assert textmod.detect_lang("プラズマエッチング") == "ja"   # 가나
    assert textmod.detect_lang("plasma etching method") == "en"
    assert textmod.detect_lang("半導体装置") == "en"          # 한자단독 → 비한국어(en)
    assert textmod.detect_lang("") == "und"


# --- 청구항 재구성 -----------------------------------------------------------

def test_reconstruct_orders_and_splits_independent():
    # 청구항 2(종속·seq 뒤섞임)와 청구항 1(독립)을 넣어 번호·seq 정렬과 독립항 분리 검증
    claims = [
        (2, False, "제1항에 있어서 상기 막은 산화막"),
        (1, True, "기판 위에 막을 형성하는 단계"),
    ]
    r = claim_join._reconstruct(claims)
    assert r.n_claims == 2 and r.n_independent == 1
    # claims_full 은 번호순(1→2)
    assert r.claims_full.startswith("기판 위에")
    assert r.claims_independent == "기판 위에 막을 형성하는 단계"
    assert r.first_independent == "기판 위에 막을 형성하는 단계"


def test_reconstruct_first_independent_picks_min_number():
    claims = [
        (5, True, "독립항 5"),
        (1, False, "종속항 1"),
        (3, True, "독립항 3"),
    ]
    r = claim_join._reconstruct(claims)
    assert r.first_independent == "독립항 3"  # 최소 번호 독립항


def test_reconstruct_no_independent_falls_back_to_first_claim():
    claims = [(2, False, "b"), (1, False, "a")]
    r = claim_join._reconstruct(claims)
    assert r.n_independent == 0
    assert r.first_independent == "a"  # 독립항 없으면 최소 번호 청구항


def test_to_int_handles_nonnumeric():
    assert claim_join._to_int("7") == 7
    assert claim_join._to_int("1a") == 10**9  # 비정수는 뒤로 밀림(안정)


# --- 결정성 ------------------------------------------------------------------

def test_reconstruct_is_deterministic():
    claims = [(3, True, "c"), (1, True, "a"), (2, False, "b")]
    assert claim_join._reconstruct(list(claims)).claims_full == \
        claim_join._reconstruct(list(claims)).claims_full


def test_local_iri():
    assert assemble._local("https://w3id.org/sdkb/data/patent/kr_10203") == "kr_10203"


# --- 누출 통제 (구조적) ------------------------------------------------------

def test_forbidden_predicates_never_queried_as_features():
    # 개념링크 목록에 금지 술어가 섞이지 않았는지 (누출 방지 · CLAUDE.md §1.4)
    assert not (set(assemble.CONCEPT_PROPS) & set(assemble.FORBIDDEN))


# --- 산출물 불변식 (parquet 존재 시) -----------------------------------------

@pytest.fixture(scope="module")
def corpus():
    if not config.IR_CORPUS.exists():
        pytest.skip("ir_corpus_v09.parquet 없음 — `make corpus` 후 실행")
    return pd.read_parquet(config.IR_CORPUS)


@pytest.fixture(scope="module")
def qrel():
    if not config.QREL_EXAMINER.exists():
        pytest.skip("qrel_examiner.parquet 없음 — `make corpus` 후 실행")
    return pd.read_parquet(config.QREL_EXAMINER)


def test_queries_have_claims_and_dates(corpus):
    q = corpus[corpus.is_query]
    assert len(q) == 1000
    assert (q.claims_full.str.len() > 0).all()
    assert q.filing_date.notna().all()


def test_query_density_ge_97(corpus, qrel):
    q = corpus[corpus.is_query]
    density = qrel.query_id.nunique() / len(q)
    assert density >= 0.97, f"질의밀도 {density:.1%} < 97%"


def test_qrel_targets_all_in_corpus(corpus, qrel):
    corp_ids = set(corpus.doc_id)
    assert qrel.doc_id.isin(corp_ids).all()


def test_no_leakage_columns(corpus):
    leak = [c for c in corpus.columns
            if any(f.lower() in c.lower() for f in assemble.FORBIDDEN)]
    assert not leak, f"누출 컬럼: {leak}"


def test_candidate_reprs_are_null(corpus):
    # 질의 4종 표현은 질의에만 채워진다(후보는 null)
    cand = corpus[~corpus.is_query]
    assert cand.q_repr_abstract.isna().all()


def test_doc_id_unique(corpus):
    assert corpus.doc_id.is_unique
