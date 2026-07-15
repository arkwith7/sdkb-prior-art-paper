"""어휘 검증 커버리지 지표의 계약 (논문 §3.4.2 지표 ii · SPEC-004).

이 지표의 존재 이유는 "CQ 8/8 · 100%" 가 공허한 게이트임을 드러내는 것이다. 따라서
**부풀릴 수 없어야** 한다 — 그 방어선을 여기서 고정한다:

  · OPTIONAL 안에 술어를 넣어 커버리지를 올릴 수 없다
  · 0 행을 응답하는 CQ 는 어휘를 검증하지 못한다
  · 같은 입력에 같은 출력이다 (그래야 논문의 수치가 재현된다)
"""
from __future__ import annotations

from rdflib import Graph

from sdkb_paper.config import ONT, SAMPLES
from sdkb_paper.validate.vocab_coverage import cq_vocabulary, graph_vocabulary, measure

PREFIXES = """
PREFIX ont:  <https://w3id.org/sdkb/ont/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
"""


def _iri(local: str) -> str:
    return str(ONT[local])


def test_required_pattern_is_counted():
    v = cq_vocabulary(PREFIXES + "SELECT ?p WHERE { ?p a ont:Patent ; ont:realizesProcess ?s . }")
    assert _iri("Patent") in v.required
    assert _iri("realizesProcess") in v.required


def test_optional_pattern_does_not_inflate_coverage():
    """커버리지를 부풀리는 가장 쉬운 방법 — OPTIONAL 로 술어를 나열하기 — 이 막히는가."""
    v = cq_vocabulary(
        PREFIXES
        + """SELECT ?p WHERE {
                 ?p a ont:Patent .
                 OPTIONAL { ?p ont:hasPriorArtExaminer ?a . }
                 OPTIONAL { ?p ont:companyType ?c . }
               }"""
    )
    assert _iri("Patent") in v.required
    assert _iri("hasPriorArtExaminer") not in v.required
    assert _iri("companyType") not in v.required
    assert {_iri("hasPriorArtExaminer"), _iri("companyType")} <= set(v.optional)


def test_not_exists_is_required():
    """FILTER NOT EXISTS 안의 술어는 필수다 — 질의의 답이 실제로 그 술어에 의존한다 (CQ03)."""
    v = cq_vocabulary(
        PREFIXES
        + """SELECT ?s WHERE {
                 ?s a ont:Process .
                 FILTER NOT EXISTS { ?p ont:realizesProcess ?s . }
               }"""
    )
    assert _iri("realizesProcess") in v.required


def test_values_clause_terms_are_counted():
    """CQ01 이 VALUES 로 여는 클래스도 잡아야 한다 — 정규식이 아니라 대수를 파싱하는 이유."""
    v = cq_vocabulary(
        PREFIXES
        + """SELECT ?s WHERE {
                 VALUES ?t { ont:Process ont:SubProcess }
                 ?s a ?t .
               }"""
    )
    assert {_iri("Process"), _iri("SubProcess")} <= set(v.required)


def test_denominator_is_vocabulary_actually_used():
    """분모는 TBox 선언이 아니라 그래프에 **쓰인** 어휘다."""
    g = Graph().parse(SAMPLES / "mini_graph.ttl")
    predicates, classes = graph_vocabulary(g)
    assert _iri("realizesProcess") in predicates
    assert _iri("Patent") in classes
    assert all(v > 0 for v in predicates.values())


def test_zero_row_cq_verifies_nothing(tmp_path):
    """술어가 그래프에 없어도 0 행은 나온다 — 0 행 응답은 어휘를 검증하지 못한다."""
    cq_dir = tmp_path / "cq"
    cq_dir.mkdir()
    (cq_dir / "CQ99_empty.rq").write_text(
        PREFIXES + "SELECT ?p WHERE { ?p a ont:Patent ; ont:concernsTechnologyNode ?n . "
        "FILTER(?n = ont:nonexistent_node) }",
        encoding="utf-8",
    )
    # SHACL 을 격리해 CQ 검증 행위만 잰다 (shapes_dir 을 빈 디렉터리로).
    empty_shapes = tmp_path / "shapes"
    empty_shapes.mkdir()
    cov = measure(SAMPLES / "mini_graph.ttl", cq_dir, empty_shapes)
    rows, hit = cov.per_cq["CQ99_empty"]
    assert rows == 0
    assert not hit
    assert cov.predicate_rate == 0.0  # CQ 검증률 (SHACL 격리)


def test_deterministic():
    a, b = measure(SAMPLES / "mini_graph.ttl"), measure(SAMPLES / "mini_graph.ttl")
    assert a.verified_predicates == b.verified_predicates
    assert a.predicates_used == b.predicates_used
