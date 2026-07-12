"""통합 테스트 — 얼린 스냅샷 ↔ 코드 ↔ 게이트의 정합성.

단위 테스트가 전부 통과해도 모듈 경계에서 조용히 깨지는 것들을 여기서 잡는다
(CLAUDE.md §5(b)). 지키는 계약:

  external/sdkb (스냅샷) → ontology.baseline : PROVENANCE 무결성, 관측 단위 수, 결정성
  ontology.baseline      → validate.shacl    : graph_v0 이 L1 을 통과한다
  ontology.baseline      → validate.cq       : graph_v0 의 "특허 0건 서명" (H1 의 before)

graph_v0 은 gitignore 대상이라 CI 러너에 존재하지 않는다 — 커밋된 스냅샷에서 매번
재조립해서 검증한다. 그게 요점이다: 재조립이 깨지면 H1 의 before 가 사라진다.
"""
from __future__ import annotations

import hashlib
import shutil
import subprocess

import pytest
from rdflib import RDF

from sdkb_paper.config import EXTERNAL_SDKB, QUERIES_CQ
from sdkb_paper.ontology.baseline import build_baseline, summarize
from sdkb_paper.ontology.vendor import verify_snapshot
from sdkb_paper.validate.cq_runner import run_cqs
from sdkb_paper.validate.shacl_gate import validate_graph

# 얼린 스냅샷(SDKB e64f90cc74ec)이 만들어내는 baseline 의 서명.
# 스냅샷을 의도적으로 갱신하면 이 숫자들이 바뀐다 — 그때는 data/MANIFEST.md 의 표와
# 논문 §2.4 표 2 를 함께 고쳐야 한다. 그 강제가 이 상수의 존재 이유다.
EXPECTED_TRIPLES = 3201
EXPECTED_PROCESS = 8
EXPECTED_SUBPROCESS = 12

# graph_v0 은 보강 전 그래프다: 특허가 0건이므로 특허를 요구하는 CQ 는 응답 불가여야 하고,
# 커버리지 공백을 찾는 CQ 는 응답 가능해야 한다. 이 서명이 깨지면 SIRP 특허가 섞였거나
# 질의가 망가진 것이다.
CQ_MUST_ANSWER = {"CQ03_uncovered_process_steps"}
CQ_MUST_NOT_ANSWER = {"CQ01_patents_per_process_step", "CQ02_recent_patents_by_step"}


@pytest.fixture(scope="module")
def graph_v0(tmp_path_factory):
    """커밋된 스냅샷에서 baseline 을 재조립한다 (원본 data/processed 를 건드리지 않는다)."""
    out = tmp_path_factory.mktemp("baseline") / "graph_v0.ttl"
    return build_baseline(snapshot=EXTERNAL_SDKB, out=out), out


# --- 스냅샷 → baseline 경계 -------------------------------------------------

def test_snapshot_matches_provenance():
    """커밋된 스냅샷이 PROVENANCE 의 sha256 과 일치한다. 어긋나면 baseline 의 출처가 거짓이다."""
    assert verify_snapshot(EXTERNAL_SDKB) == []


def test_baseline_observation_units(graph_v0):
    """H1 의 관측 단위(공정 계층)가 스냅샷과 코드 사이에서 유지된다."""
    g, _ = graph_v0
    counts = summarize(g)
    assert counts["Process"] == EXPECTED_PROCESS
    assert counts["SubProcess"] == EXPECTED_SUBPROCESS
    assert len(g) == EXPECTED_TRIPLES


def test_baseline_has_no_patents(graph_v0):
    """보강 전 그래프에 특허가 있으면 H1(보강 효과)이 성립하지 않는다."""
    g, _ = graph_v0
    assert summarize(g)["Patent"] == 0


def test_baseline_is_deterministic(tmp_path):
    """같은 스냅샷 → 같은 그래프. G₀ 가 흔들리면 보강 전후 비교가 재현되지 않는다."""
    a, b = tmp_path / "a.ttl", tmp_path / "b.ttl"
    build_baseline(snapshot=EXTERNAL_SDKB, out=a)
    build_baseline(snapshot=EXTERNAL_SDKB, out=b)
    assert hashlib.sha256(a.read_bytes()).hexdigest() == hashlib.sha256(b.read_bytes()).hexdigest()


# --- baseline → 게이트 경계 -------------------------------------------------

def test_baseline_passes_shacl(graph_v0):
    """L1: 실물 baseline 이 SHACL 제약을 통과한다."""
    _, path = graph_v0
    conforms, report = validate_graph(path)
    assert conforms, report


def test_baseline_cq_signature(graph_v0):
    """L3: 특허 0건 그래프의 CQ 서명. CQ01 이 갑자기 응답하면 특허가 새어든 것이다."""
    _, path = graph_v0
    results = {r.name: r for r in run_cqs(path, QUERIES_CQ)}

    missing = (CQ_MUST_ANSWER | CQ_MUST_NOT_ANSWER) - results.keys()
    assert not missing, f"CQ 파일이 사라졌다: {missing}"

    for name in CQ_MUST_ANSWER:
        assert results[name].passed, f"{name} 은 baseline 에서도 응답 가능해야 한다 (H1 의 핵심 질의)"
    for name in CQ_MUST_NOT_ANSWER:
        assert results[name].rows == 0, (
            f"{name} 이 baseline 에서 {results[name].rows}행을 반환했다 — "
            f"보강 전 그래프에 특허가 섞여 있다."
        )


@pytest.mark.skipif(shutil.which("java") is None, reason="HermiT 는 Java 가 필요하다")
def test_baseline_is_logically_consistent(graph_v0):
    """L2: 실물 baseline 이 논리적으로 일관된다 (Turtle 입력 경로 포함 — owlready2 는 TTL 을 못 읽는다)."""
    from sdkb_paper.validate.reasoner_gate import check_consistency

    _, path = graph_v0
    assert check_consistency(path)


@pytest.mark.skipif(shutil.which("java") is None, reason="HermiT 는 Java 가 필요하다")
def test_reasoner_rejects_range_violation(graph_v0, tmp_path):
    """L2 의 거부 경로. 추론 뷰가 xsd:date 를 xsd:dateTime 으로 승격해도 탐지력이 남아야 한다 —
    승격이 타입 검사를 무력화하면 L2 는 항상 통과하는 가짜 게이트가 된다."""
    from rdflib import XSD, Graph, Literal

    from sdkb_paper.config import ONT, PATENT_NS
    from sdkb_paper.validate.reasoner_gate import check_consistency

    g, _ = graph_v0
    bad = Graph()
    for t in g:
        bad.add(t)
    # filingDate 는 rdfs:range xsd:date 인 DatatypeProperty — 문자열을 넣으면 범위 위반이다.
    bad.add((PATENT_NS["9999999999999"], RDF.type, ONT.Patent))
    bad.add((PATENT_NS["9999999999999"], ONT.filingDate, Literal("not-a-date", datatype=XSD.string)))

    out = tmp_path / "range_violation.ttl"
    bad.serialize(out, format="turtle")
    assert check_consistency(out) is False


# --- 스냅샷 변조 탐지 (게이트의 거부 경로) -----------------------------------

def test_verify_snapshot_detects_tampering(tmp_path):
    """실패해야 할 입력이 실패하는가 — 통과만 확인하는 게이트는 게이트가 아니다."""
    fake = tmp_path / "sdkb"
    shutil.copytree(EXTERNAL_SDKB, fake)
    target = fake / "sdkb-core.ttl"
    target.write_text(target.read_text(encoding="utf-8") + "\n# tampered\n", encoding="utf-8")

    problems = verify_snapshot(fake)
    assert any("sdkb-core.ttl" in p and "sha256" in p for p in problems), problems


def test_verify_snapshot_detects_stray_ttl(tmp_path):
    """PROVENANCE 가 모르는 TTL(예: SIRP 특허 ABox)이 스냅샷에 섞이면 잡는다."""
    fake = tmp_path / "sdkb"
    shutil.copytree(EXTERNAL_SDKB, fake)
    (fake / "sdkb-abox-patents.ttl").write_text("# SIRP 773건\n", encoding="utf-8")

    problems = verify_snapshot(fake)
    assert any("sdkb-abox-patents.ttl" in p for p in problems), problems


# --- CLI 계약 (Makefile/CI 가 부르는 경로) ------------------------------------

def test_vendor_verify_cli_exits_zero():
    """`make snapshot` 이 부르는 CLI. SDKB 원본 없이 동작해야 CI 에서 돈다."""
    r = subprocess.run(
        ["python", "-m", "sdkb_paper.ontology.vendor", "--verify"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
