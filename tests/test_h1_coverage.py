"""S1(구 커버리지 H1) 검정의 계약 — 집계 · Wilcoxon · 표본 집합 · viz 경계.

이 파일이 지키는 것 (CLAUDE.md §5):
  ontology(graph) → analysis.s1_coverage     : 고유 특허 수 · 0건 단계도 행으로 남는다
  analysis.s1_coverage → s1_coverage_cli      : 검정의 사전 확정값(단측 · 동점 제외 · 표본 단위)
  analysis → viz                      : 컬럼 계약 (label/before/after/delta)

검정 자체는 결과를 본 뒤 바꿀 수 없다 — 여기 고정된 것이 그 약속이다.
"""
from __future__ import annotations

import pandas as pd
import pytest
from rdflib import RDF, Graph, Literal, URIRef

from sdkb_paper.analysis.s1_coverage import (
    compare_coverage,
    coverage_by_process_step,
    legacy_scope_iris,
    restrict,
    wilcoxon_h1,
)
from sdkb_paper.config import ONT, SDKB_DATA
from sdkb_paper.viz.figures import fig_h1_coverage

SKOS_PREF = URIRef("http://www.w3.org/2004/02/skos/core#prefLabel")

# 복원 이전 집합의 서명. 20 이 아니면 동결 CSV 가 손상됐거나 손으로 편집된 것이다.
LEGACY_N = 20


def _graph(steps: dict[str, int], out) -> "object":
    """공정 단계 s 마다 특허 n 건을 realizesProcess 로 매단 최소 그래프."""
    g = Graph()
    for step, n in steps.items():
        s = SDKB_DATA[f"process/{step}"]
        g.add((s, RDF.type, ONT["Process"]))
        g.add((s, SKOS_PREF, Literal(step)))
        for i in range(n):
            p = SDKB_DATA[f"patent/{step}-{i}"]
            g.add((p, RDF.type, ONT["Patent"]))
            g.add((p, ONT["realizesProcess"], s))
    g.serialize(out, format="turtle")
    return out


# --- 집계 계약 ---------------------------------------------------------------

def test_uncovered_step_stays_as_a_row(tmp_path):
    """특허 0건인 단계도 행으로 남는다 — 그 공백이 H1 의 관측 대상이다."""
    df = coverage_by_process_step(_graph({"etch": 2, "clean": 0}, tmp_path / "g.ttl"))
    assert len(df) == 2
    assert df.loc[("process", str(SDKB_DATA["process/clean"])), "patents"] == 0


def test_patent_counted_once_per_step(tmp_path):
    """C(s) 는 고유 특허 수다. 한 특허가 같은 단계를 두 번 가리켜도 1 이다."""
    g = Graph()
    step = SDKB_DATA["process/etch"]
    g.add((step, RDF.type, ONT["Process"]))
    g.add((step, SKOS_PREF, Literal("Etch")))
    pat = SDKB_DATA["patent/1"]
    g.add((pat, RDF.type, ONT["Patent"]))
    g.add((pat, ONT["realizesProcess"], step))
    g.add((pat, ONT["realizesProcess"], step))  # 중복 트리플은 RDF 에서 하나지만…
    g.add((pat, ONT["hasIPC"], Literal("H01L21/302")))  # …JOIN 이 곱해지는 경로를 만든다
    out = tmp_path / "dup.ttl"
    g.serialize(out, format="turtle")

    df = coverage_by_process_step(out)
    assert df["patents"].iloc[0] == 1


def test_compare_coverage_columns_and_delta(tmp_path):
    """analysis → viz 컬럼 계약. 어긋나면 그림이 빈 채로 그려진다."""
    before = _graph({"etch": 1, "clean": 0, "cmp": 3}, tmp_path / "b.ttl")
    after = _graph({"etch": 5, "clean": 2, "cmp": 3}, tmp_path / "a.ttl")

    df = compare_coverage(before, after)
    assert list(df.columns) == ["label", "before", "after", "delta"]
    assert df["delta"].tolist() == sorted(df["delta"].tolist(), reverse=True)
    delta = df.droplevel("level")["delta"]
    assert delta[str(SDKB_DATA["process/etch"])] == 4
    assert delta[str(SDKB_DATA["process/cmp"])] == 0


# --- 검정 계약 (사전 확정 — 결과를 본 뒤 바꾸지 않는다) ------------------------

def _df(deltas: list[int]) -> pd.DataFrame:
    idx = pd.MultiIndex.from_tuples(
        [("process", f"s{i}") for i in range(len(deltas))], names=["level", "step"]
    )
    return pd.DataFrame({"before": 0, "after": deltas, "delta": deltas}, index=idx)


def test_wilcoxon_is_one_sided_greater():
    """단측(greater). 증가만 유의하다 — 감소는 H1 을 지지하지 않는다."""
    up = wilcoxon_h1(_df([1, 2, 3, 4, 5, 6, 7]), "up")
    down = wilcoxon_h1(_df([-1, -2, -3, -4, -5, -6, -7]), "down")

    assert up.rejects_null
    assert not down.rejects_null
    assert up.share_increased == pytest.approx(1.0)
    assert down.share_increased == 0.0


def test_tied_pairs_are_excluded_but_reported():
    """동점 쌍은 검정에서 빠지되 표본 크기에는 남는다 — 숨기면 표본이 커 보인다.

    동점이 과반이면 전 단계 중앙값은 0 인데도 검정은 기각한다. 두 수치가 함께 나와야
    "중앙값 0 인데 유의하다"가 모순이 아니라 동점 제외의 귀결로 읽힌다.
    """
    r = wilcoxon_h1(_df([0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6]), "tied")
    assert r.n == 13
    assert r.n_tied == 7
    assert r.n_positive == 6
    assert r.median_delta == 0.0          # 동점이 과반 → 리터럴 중앙값은 0
    assert r.median_delta_positive == 3.5  # 증가한 단계만 보면 3.5
    assert r.share_increased == pytest.approx(6 / 13)
    assert r.rejects_null                  # 그럼에도 기각된다 — 이것이 확장 49 에서 벌어진 일이다


def test_all_tied_yields_no_test_not_a_crash():
    """전 단계가 동점이면 검정할 것이 없다. 조용히 0 을 반환하지도, 죽지도 않는다."""
    r = wilcoxon_h1(_df([0, 0, 0]), "flat")
    assert r.p_value is None
    assert r.statistic is None
    assert not r.rejects_null


def test_empty_scope_is_handled():
    r = wilcoxon_h1(_df([]), "empty")
    assert r.n == 0
    assert r.p_value is None


def test_wilcoxon_is_deterministic():
    d = _df([0, 1, -2, 3, 4, 5, -1, 8])
    a, b = wilcoxon_h1(d, "x"), wilcoxon_h1(d, "x")
    assert a == b


# --- 표본 집합 (복원 편향의 병기 보고) ----------------------------------------

def test_legacy_scope_is_frozen_at_20():
    """복원 이전 집합은 20개다. 손으로 늘리거나 줄이면 H1 의 병기 보고가 무의미해진다."""
    iris = legacy_scope_iris()
    assert len(iris) == LEGACY_N
    assert all(i.startswith("https://w3id.org/sdkb/data/") for i in iris)


def test_restrict_selects_by_iri(tmp_path):
    before = _graph({"etch": 1, "packaging": 0}, tmp_path / "b.ttl")
    after = _graph({"etch": 5, "packaging": 9}, tmp_path / "a.ttl")
    df = compare_coverage(before, after)

    sub = restrict(df, {str(SDKB_DATA["process/etch"])})
    assert len(sub) == 1
    assert sub["delta"].iloc[0] == 4


# --- viz 경계 ----------------------------------------------------------------

def test_figure_renders_from_compare_output(tmp_path):
    """analysis 산출 프레임이 그대로 그림이 된다 (컬럼명·단위가 어긋나면 여기서 깨진다)."""
    before = _graph({"etch": 1, "clean": 0}, tmp_path / "b.ttl")
    after = _graph({"etch": 5, "clean": 2}, tmp_path / "a.ttl")
    df = compare_coverage(before, after)
    df["in_legacy20"] = True

    out = fig_h1_coverage(df, out=tmp_path / "fig.png")
    assert out.exists() and out.stat().st_size > 0
