"""서술문 앵커링 — 실무자가 문장으로 물을 때 그래프 어휘를 옳게 집어내는가.

이 층은 논문 산출물이 아니라 시연 도구다. 그래도 계약은 세 가지로 고정한다:
어휘를 발명하지 않을 것, 결정적일 것, 사용자 문자열이 쿼리에 보간되지 않을 것.
"""
from __future__ import annotations

import pytest

from sdkb_paper.config import GRAPH_V0, GRAPH_V1
from sdkb_paper.explore import anchor, store

SENTENCE = (
    "We need to optimize our etching process to achieve better uniformity. "
    "Current performance: 78%. Target specification: 93%. "
    "Key constraints include equipment compatibility. "
    "Previous optimization attempts using DOE showed inconclusive."
)

pytestmark = pytest.mark.skipif(
    not GRAPH_V0.exists(), reason="graph_v0 없음 — make baseline 후 실행"
)


@pytest.fixture(scope="module")
def result() -> dict:
    return anchor.interpret(SENTENCE, "v0")


def test_normalize_is_symmetric() -> None:
    # 어법상 틀린 어간이어도 무방하다 — 문장과 라벨이 같은 규칙을 지나면 된다.
    assert anchor.normalize("Processes") == anchor.normalize("process")
    assert anchor.normalize("Etching") == anchor.normalize("etch")


def test_lexicon_excludes_patent_titles() -> None:
    lex = anchor.build_lexicon("v0")
    assert lex, "사전이 비어 있다"
    assert not [e for e in lex if e.cls in ("Patent", "RejectedPatent", "Organization")]
    assert {e.cls for e in lex} <= set(anchor.ANCHOR_CLASSES)


@pytest.mark.parametrize("graph_key", ["v0", "v1", "v2"])
def test_lexicon_is_complete_not_truncated(graph_key: str) -> None:
    """사전은 그래프의 개념을 **전부** 실어야 한다.

    클래스를 파이썬에서 거르던 판본은 특허가 많은 G₁·G₂ 에서 store.MAX_ROWS 에 걸려
    조용히 잘렸고, Device 34개 중 21개만 실려 HBM 이 사라졌다 —
    잘린 사전은 '그 개념이 그래프에 없다'와 구별되지 않는다.
    """
    from sdkb_paper.config import GRAPH_V1, GRAPH_V2

    if not {"v0": GRAPH_V0, "v1": GRAPH_V1, "v2": GRAPH_V2}[graph_key].exists():
        pytest.skip(f"{graph_key} 없음")
    lex = anchor.build_lexicon(graph_key)
    devices = {e.iri for e in lex if e.cls == "Device"}
    expected = store.scalar(
        graph_key,
        "PREFIX ont: <https://w3id.org/sdkb/ont/>"
        "SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s a ont:Device }",
    )
    assert len(devices) == expected


def test_anchors_the_example_sentence(result: dict) -> None:
    labels = {a["label"] for a in result["anchors"]}
    assert "Etch" in labels  # Process — 'etching' 의 접미사 정규화 경로
    assert any("Etch" in x and x != "Etch" for x in labels)  # Plasma/Wet/Hardmask Etch
    assert any(a["matched"] == ["doe"] for a in result["anchors"])  # altLabel 경유


def test_doe_comes_from_ontology_alias(result: dict) -> None:
    """동의어를 코드가 발명하지 않는다 — DOE 는 온톨로지 altLabel 이 공급한다."""
    doe = [a for a in result["anchors"] if a["matched"] == ["doe"]]
    assert doe and doe[0]["via_alt"] and doe[0]["cls"] == "Skill"


def test_off_topic_narrative_labels_are_rejected(result: dict) -> None:
    """문장에 없는 주제어(CMP·deposition)를 담은 실무문제는 앵커가 아니다."""
    for a in result["anchors"]:
        if a["cls"] in anchor._NARRATIVE:
            assert "CMP" not in a["label"] and "deposition" not in a["label"]


def test_head_noun_alone_is_not_an_anchor(result: dict) -> None:
    """'process' 는 머리명사다 — 이것만으로 'Back-End Processes' 가 잡히면 안 된다."""
    assert "Back-End Processes" not in {a["label"] for a in result["anchors"]}


def test_unmodelled_spans_are_reported_not_queried(result: dict) -> None:
    """성능 수치·제약조건에는 대응 술어가 없다 — 있는 척하지 않고 남긴다."""
    unused = {u.lower() for u in result["unused"]}
    assert {"78", "93", "compatibility"} <= unused


def test_no_user_text_interpolated_into_sparql(result: dict) -> None:
    """앵커는 IRI 다 — 리터럴 인젝션 경로가 없다."""
    for q in result["queries"].values():
        assert "optimize" not in q.lower()
        assert "78" not in q


def test_quote_in_sentence_does_not_break_queries() -> None:
    r = anchor.interpret('etching "process" with \\ backslash', "v0")
    for q in r["queries"].values():
        store.run_query("v0", q)  # 파싱 예외가 나면 실패


def test_deterministic() -> None:
    a = anchor.interpret(SENTENCE, "v0")
    b = anchor.interpret(SENTENCE, "v0")
    assert a == b


def test_generated_queries_execute(result: dict) -> None:
    assert set(result["queries"]) == {"expert", "priorart", "fto"}
    assert store.run_query("v0", result["queries"]["expert"]).rows
    assert store.run_query("v0", result["queries"]["priorart"]).rows


@pytest.mark.skipif(not GRAPH_V1.exists(), reason="graph_v1 없음 — make merge 후 실행")
def test_emerging_aliases_are_anchorable_in_g1() -> None:
    """신기술 약칭·한국어는 G₀ 에 없고 G₁ 병합이 altLabel 로 실체화한다(delta.py).

    G₀ 에서 'HBM' 이 안 잡히는 것은 결함이 아니라 **보강 전이라는 사실**이다 —
    이 테스트가 그 경계를 고정한다.
    """
    text = "HBM 적층에서 TSV 식각 후 보이드. GAA 소자도 검토 중."
    g0 = {a["label"] for a in anchor.interpret(text, "v0")["anchors"]}
    g1 = {a["label"] for a in anchor.interpret(text, "v1")["anchors"]}
    assert {"HBM", "GAA"} <= g1
    assert not {"HBM", "GAA"} & g0
    assert "식각" in g1  # 한국어 altLabel 경유 — 룰이 아니라 온톨로지가 공급한다


def test_same_label_nodes_fold_into_one_anchor() -> None:
    """동일 prefLabel 을 쓰는 형제 노드는 한 앵커로 접되 질의는 전부를 대상으로 한다.

    실무문제 226개 중 19개 라벨이 최대 28개 노드에 공유된다 — 접지 않으면 클래스당
    상한 5개가 같은 라벨 하나로 다 차서 다른 개념이 밀려난다.
    """
    r = anchor.interpret(
        "We need to optimize our deposition process to achieve lower defects.", "v0"
    )
    problems = [a for a in r["anchors"] if a["cls"] == "Problem"]
    assert len({(a["cls"], a["label"]) for a in problems}) == len(problems)  # 중복 행 없음
    multi = [a for a in problems if a["nodes"] > 1]
    assert multi, "형제 노드를 가진 실무문제가 하나도 없다 — 픽스처 전제가 깨졌다"
    # 접힌 형제의 IRI 가 실제로 질의에 실렸는가
    q = r["queries"].get("expert", "")
    for a in multi:
        assert q.count("problem/") >= a["nodes"] or "?prob" not in q


def test_korean_particles_do_not_hide_concepts() -> None:
    """조사가 붙어도 개념을 놓치지 않는다.

    '식각을 개선하고 증착이 불안정합니다' 는 두 개념이 모두 사전에 있는데도
    조사 때문에 앵커가 **0개**였다 — 한국어 입력 전체가 조용히 실패하는 결함이었다.
    """
    r = anchor.interpret("식각을 개선하고 증착이 불안정합니다", "v0")
    assert {a["label"] for a in r["anchors"]} >= {"식각", "증착"}
    # 앵커가 된 말이 '미사용'에도 남으면 화면이 스스로와 모순된다.
    assert not [u for u in r["unused"] if u.startswith(("식각", "증착"))]


def test_josa_stripping_requires_a_real_stem() -> None:
    """어간이 사전에 없으면 자르지 않는다 — 자르면 형태소 분석이 아니라 추측이다."""
    known = anchor.korean_tokens(anchor.build_lexicon("v0"))
    assert anchor.strip_josa("식각을", known) == "식각"
    assert anchor.strip_josa("현상이", known) is None  # '현상' 은 사전에 없다
    assert anchor.strip_josa("etching", known) is None  # 한국어가 아니면 대상 아님


def test_no_anchor_yields_no_queries() -> None:
    r = anchor.interpret("the quick brown fox jumps over the lazy dog", "v0")
    assert r["anchors"] == []
    assert r["queries"] == {}
