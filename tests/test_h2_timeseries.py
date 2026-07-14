"""H2 시계열의 계약 (PLAN-006).

이 파일이 지키는 것:
  신호 규칙(θ · n_min · 창 · 탐색 시작)  : 동결된 규칙이 코드와 어긋나지 않는다
  판정 규칙(동률 · 미탐지)               : 부호검정이 무엇을 세고 무엇을 버리는지
  analysis ↔ ontology 경계               : 개념 시계열 = G₁ 그래프의 SPARQL 결과

**규칙은 시계열을 보기 전에 동결됐다.** 아래 상수가 바뀌면 사전등록이 깨진 것이다.
"""
from __future__ import annotations

import pandas as pd
import pytest
from rdflib import URIRef

from sdkb_paper.analysis.timeseries import (
    N_MIN,
    SEARCH_START,
    THETA,
    WINDOW_END,
    WINDOW_START,
    annual_counts,
    assign_concepts,
    code_series,
    concept_series,
    detect_year,
    lead_times,
    prepare,
    sign_test,
)
from sdkb_paper.config import ONT
from sdkb_paper.ontology.delta import build_delta

FINFET = "https://w3id.org/sdkb/data/device/finfet"
TSV = "https://w3id.org/sdkb/data/device/tsv"


def series(**years: int) -> pd.Series:
    """관측창 전체를 0 으로 채운 시계열. 키는 'y2013' 형태다."""
    data = {y: 0 for y in range(WINDOW_START, WINDOW_END + 1)}
    data.update({int(k[1:]): v for k, v in years.items()})
    return pd.Series(data).sort_index()


# --- 동결된 신호 규칙 --------------------------------------------------------

def test_signal_rule_is_frozen():
    assert (THETA, N_MIN, SEARCH_START, WINDOW_START, WINDOW_END) == (2.0, 3, 2013, 2010, 2023)


def test_truncated_years_are_outside_the_window():
    """2024–2025 는 18개월 비공개 절단이다 — 창에 넣으면 모든 개념이 최근에 급락한다."""
    counts = annual_counts(pd.Series([2015, 2024, 2025, 2025]))
    assert list(counts.index) == list(range(WINDOW_START, WINDOW_END + 1))
    assert counts.sum() == 1


# --- detect_year 의 경계 -----------------------------------------------------

def test_detects_emergence_from_nothing():
    """직전 3년 평균이 0이면(무에서 출현) y >= n_min 만으로 충족한다."""
    assert detect_year(series(y2016=3)) == 2016


def test_below_n_min_is_not_a_signal():
    """n_min 미만은 무에서 나와도 신호가 아니다 — 잡음과 구별되지 않는다."""
    assert detect_year(series(y2016=2, y2017=2)) is None


def test_growth_must_beat_theta_times_prior_mean():
    """직전 3년 평균 10 → θ=2.0 이면 20 이상이라야 탐지된다."""
    # 기저를 2010 년부터 깔아야 θ 규칙을 때린다 — 안 그러면 첫 해가 '무에서 출현'으로 먼저 걸린다.
    base = series(y2010=10, y2011=10, y2012=10, y2013=10, y2014=10, y2015=10)
    slow = base.copy()
    slow[2016] = 19
    assert detect_year(slow) is None
    fast = base.copy()
    fast[2016] = 20
    assert detect_year(fast) == 2016


def test_search_starts_at_2013():
    """2010–2012 는 직전 3년 후행창을 확보할 수 없다 — 탐지 후보가 아니다."""
    assert detect_year(series(y2011=50)) is None
    assert detect_year(series(y2011=50, y2014=200)) == 2014


def test_undetected_is_none_not_a_big_number():
    """미탐지를 임의의 큰 값으로 대체하지 않는다 (PLAN-006 의 사전 약속)."""
    assert detect_year(series()) is None


# --- 판정 규칙과 부호검정 -----------------------------------------------------

def outcomes(*rows: str) -> pd.DataFrame:
    return pd.DataFrame({"outcome": list(rows)})


def test_sign_test_excludes_ties_and_undetected_pairs():
    """동률·양쪽미탐지는 정보 없는 쌍이다 — 분모에서 뺀다 (H1 의 동점 처리와 같은 규약)."""
    r = sign_test(outcomes("concept_first", "concept_first", "tie", "both_undetected", "code_first"))
    assert (r.n_pairs, r.n_concept_first, r.n_code_first, r.n_excluded) == (3, 2, 1, 2)


def test_sign_test_is_one_sided():
    """3/3 개념 우선이면 p = 0.125 — 사례 3건으로는 α=0.05 에 도달할 수 없다(PLAN-006 의 출발점)."""
    assert sign_test(outcomes(*["concept_first"] * 3)).p_value == pytest.approx(0.125)
    assert sign_test(outcomes(*["concept_first"] * 7)).p_value == pytest.approx(0.0078125)


# --- analysis ↔ ontology 경계 -------------------------------------------------

@pytest.fixture(scope="module")
def corpus() -> pd.DataFrame:
    """고정 픽스처. FinFET 은 코드로, TSV 는 이름으로만 잡힌다 — 두 경로를 모두 때린다.

    prepare(use_cpc=False) = 사전등록 경로(KIPRIS IPC 만). 분석은 `codes` 컬럼만 본다.
    """
    df = pd.DataFrame(
        [
            {
                "application_number": "1020150000001",
                "applicant_name": "삼성전자주식회사",
                "application_date": pd.Timestamp("2015-03-01"),
                "invention_title": "핀 전계효과 트랜지스터",
                "abstract": "게이트 구조",
                "ipc_codes": ["H10D30/62"],
                "open_date": "20160901",
            },
            {
                "application_number": "1020160000002",
                "applicant_name": "에스케이하이닉스 주식회사",
                "application_date": pd.Timestamp("2016-05-02"),
                "invention_title": "적층 반도체 장치",
                "abstract": "실리콘 관통 전극을 이용한 적층 구조",  # 1층 별칭 경로 (코드 없음)
                "ipc_codes": ["H01L23/48"],
                "open_date": "20171101",
            },
            {
                "application_number": "1020160000003",
                "applicant_name": "삼성전자주식회사",
                "application_date": pd.Timestamp("2016-06-03"),
                "invention_title": "반도체 소자",
                "abstract": "무관한 내용",
                "ipc_codes": ["H10D30/62"],
                "open_date": "20171201",
            },
        ]
    )
    return prepare(df, use_cpc=False)


def test_concept_series_matches_the_graph(corpus):
    """개념 시계열 = G₁ SPARQL 결과. 어긋나면 논문의 그림과 그래프가 다른 말을 한다.

    개념이 1개 이상 붙은 특허는 정의상 전부 병합되므로(L1 델타 shape), 말뭉치 전체에서
    센 개념 시계열과 그래프에서 센 것은 같아야 한다 — 코드 시계열만 미매핑분을 더 본다.
    """
    g = build_delta(corpus)
    assigned = assign_concepts(corpus)
    for concept in (FINFET, TSV):
        from_graph = pd.Series(
            [
                int(str(g.value(p, ONT.filingDate))[:4])
                for p in g.subjects(ONT.concernsDevice, URIRef(concept))
            ],
            dtype="int64",
        )
        assert concept_series(corpus, concept, assigned).tolist() == annual_counts(
            from_graph
        ).tolist(), concept


def test_text_only_concept_is_invisible_to_the_code_arm(corpus):
    """TSV 특허는 이름으로만 잡힌다 — 대조 코드(H10W20/211)에는 0건이다.

    이것이 H2 의 논지이자, H2 의 대조군이 무엇을 놓치는지에 대한 관측이다.
    """
    assigned = assign_concepts(corpus)
    assert concept_series(corpus, TSV, assigned).sum() == 1
    assert code_series(corpus, "H10W20/211").sum() == 0


def test_code_series_matches_prefix_including_subgroups(corpus):
    assert code_series(corpus, "H10D30/62").sum() == 2
    assert code_series(corpus, "H10D30").sum() == 2


def test_lead_times_marks_lower_bound_when_code_never_detects(corpus):
    """코드가 끝내 탐지되지 않으면 시차는 **하한**이다 — 우편향 절단을 그렇게 표기한다."""
    cases = pd.DataFrame(
        [
            {
                "case_id": "tsv",
                "concept_iri": TSV,
                "control_code": "H10W20/211",
                "subset_flag": True,
            }
        ]
    )
    # n_min=1 이라야 픽스처의 1건이 신호가 된다 (주 분석의 n_min=3 은 실데이터용이다).
    row = lead_times(corpus, cases, n_min=1).iloc[0]
    assert row["concept_year"] == 2016
    assert row["code_year"] is None
    assert row["outcome"] == "concept_first"
    assert row["lead_is_lower_bound"]
    assert row["lead"] == WINDOW_END - 2016


# --- 당시(vintage) 분류 — 관측 시점 ≠ 출원연도 (PLAN-007) ----------------------

def test_vintage_reports_observation_year_not_filing_year(corpus):
    """탐지 연도는 **관측자가 알 수 있었던 해**다 (출원연도가 아니다).

    첫 구현이 둘을 섞어 측정이 무너졌다: T 의 관측자는 t=T 의 출원을 볼 수 없는데(18개월
    비공개) 신호 규칙을 y(T) 에 걸어, 늦은 해는 언제나 0 이고 이른 해는 미래 정보를 받았다.
    이 테스트가 그 회귀를 막는다.
    """
    from sdkb_paper.analysis.timeseries import OBS_START, vintage_detect_year

    # 픽스처 3건이 2017-10 스냅샷에 보이고, 전부 FinFET 코드를 달고 있었다고 두자.
    snap = {row.application_number: ["H01L29/785"] for row in corpus.itertuples()}
    vintage = {201710: snap, 201903: snap, 202004: snap, 202101: snap, 202204: snap, 202304: snap}

    year = vintage_detect_year(
        corpus, lambda codes, _row: any(c.startswith("H01L29/785") for c in codes), vintage, n_min=1
    )
    assert year is not None
    assert year >= OBS_START, "관측 시점은 스냅샷이 존재하는 2017년 이후여야 한다"


def test_vintage_cannot_see_patents_absent_from_the_snapshot(corpus):
    """스냅샷에 없는 특허 = 그때 미공개. 결측이 아니라 관측값이므로 세지 않는다."""
    from sdkb_paper.analysis.timeseries import vintage_detect_year

    empty = {s: {} for s in (201710, 201903, 202004, 202101, 202204, 202304)}
    assert vintage_detect_year(corpus, lambda codes, _row: True, empty, n_min=1) is None
