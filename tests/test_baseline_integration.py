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

from sdkb_paper.config import EXTERNAL_SDKB, ONT, QUERIES_CQ
from sdkb_paper.ontology.baseline import build_baseline, summarize
from sdkb_paper.ontology.vendor import verify_snapshot
from sdkb_paper.validate.cq_runner import run_cqs
from sdkb_paper.validate.shacl_gate import validate_graph

# 얼린 스냅샷이 만들어내는 G₀ 의 서명.
# 스냅샷을 의도적으로 갱신하면 이 숫자들이 바뀐다 — 그때는 data/MANIFEST.md 의 표와
# 논문 §2.4 표 2 를 함께 고쳐야 한다. 그 강제가 이 상수의 존재 이유다.
EXPECTED_TRIPLES = 26973
EXPECTED_PROCESS = 11       # SemiKong Table 7 의 L1 그룹 10개 (Patterning 이 리소/식각 둘로 갈림)
EXPECTED_SUBPROCESS = 38    # Table 7 의 L2 모듈 + SDKB 고유 유닛
EXPECTED_DEVICE = 34        # H2 의 개념 축은 Process ∪ Device (HBM·GAA 는 Device 다)
EXPECTED_PATENTS = 1000     # SIRP 거절특허 — G₀ 는 "현행 SDKB" 다 (특허 0건이 아니다)

# H1 의 before: 49개 공정 단계 중 16개가 커버되어 있고 33개가 공백이다.
#
# 공백이 4 → 33 으로 뛴 것은 상류 SDKB 가 SemiKong Table 7 의 그룹 1·9·10(기판준비·어드밴스드
# 모듈·**후공정**)을 통째로 빠뜨리고 있었기 때문이다. 복원 후 그 단계들은 G₀ 에서 전부 비어 있다 —
# SDKB 가 그 어휘로 특허를 매핑한 적이 없으므로 당연하다.
#
# 이것은 H1 에 **구조적으로 유리한 조건**이다: 새로 복원된 단계는 C₀(s)=0 이라 G₁ 이 채우기만 하면
# 이긴다. 그래서 논문은 H1 을 **두 집합으로 보고한다** — 확장 집합(49)과 기존 집합(20). 독자가
# "새로 추가한 단계 덕분에 산 결과인가"를 직접 판별할 수 있어야 한다 (§4.5).
EXPECTED_COVERED_STEPS = 16
EXPECTED_UNCOVERED_STEPS = 33

# G₀ 의 CQ 서명 — 논문 §4.2 의 before 열.
#
# 8개 CQ 가 **모두 응답한다**. 그래서 §3.4.2 가 쓰려던 이진 지표("G₀ 응답 불가 → G₁ 응답 가능
# 비율")는 분모가 0 이라 정의되지 않는다. 보강 효과는 **응답 완전성**(결과 행 수)으로 잰다:
# CQ06 의 커버리지 공백 29개가 G₁ 에서 줄어드는가, CQ01 의 커버 공정 16개가 늘어나는가.
CQ_MUST_ANSWER = {
    "CQ01_patents_per_process_step",
    "CQ02_recent_patents_by_step",
    "CQ03_uncovered_process_steps",
    "CQ04_concept_annual_series",
    "CQ05_concept_vs_ipc_series",
    "CQ06_concepts_without_recent_patents",
    "CQ07_device_process_crosswalk",
    "CQ08_applicant_process_portfolio",
}

# 완전성 지표의 before 값. G₁ 과 비교되는 수치이므로 여기서 고정한다.
EXPECTED_CONCEPTS_WITHOUT_RECENT = 61   # CQ06 — 개념 83개 중 2021년 이후 출원 전무
EXPECTED_PATENTS_WITH_APPLICANT = 1000  # 출원인 없는 특허는 포트폴리오 분석에 쓸 수 없다


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
    """H1 의 관측 단위(공정 20)와 H2 의 개념 축(Device 31)이 스냅샷과 코드 사이에서 유지된다."""
    g, _ = graph_v0
    counts = summarize(g)
    assert counts["Process"] == EXPECTED_PROCESS
    assert counts["SubProcess"] == EXPECTED_SUBPROCESS
    assert counts["Device"] == EXPECTED_DEVICE
    assert len(g) == EXPECTED_TRIPLES


def test_baseline_carries_sirp_patents(graph_v0):
    """G₀ 는 '현행 SDKB' 다 — SIRP 거절특허가 들어 있어야 H1 의 before 가 정직하다."""
    g, _ = graph_v0
    assert summarize(g)["Patent"] == EXPECTED_PATENTS


def test_baseline_patents_have_filing_dates(graph_v0):
    """모든 특허가 출원일을 갖는다. 상류의 filing_date 는 한때 **공개일**이었다 —
    그 값이 되돌아오면 H2 의 시계열이 1~2년 밀린다."""
    from rdflib import XSD

    g, _ = graph_v0
    pats = set(g.subjects(RDF.type, ONT["Patent"]))
    dated = {p for p in pats if (p, ONT["filingDate"], None) in g}
    assert dated == pats, f"출원일 없는 특허 {len(pats - dated)}건"

    for _, o in g.subject_objects(ONT["filingDate"]):
        assert o.datatype == XSD.date, f"filingDate 가 xsd:date 가 아니다: {o!r}"


def test_baseline_coverage_is_not_vacuous(graph_v0):
    """H1 의 before 가 자명하지 않은가. C₀(s)=0 이면 어떤 보강도 유의해져 H1 이 검정이 아니게 된다."""
    g, _ = graph_v0
    steps = set(g.subjects(RDF.type, ONT["Process"])) | set(g.subjects(RDF.type, ONT["SubProcess"]))
    covered = {
        o for p in g.subjects(RDF.type, ONT["Patent"])
        for o in g.objects(p, ONT["realizesProcess"])
    } & steps

    assert len(covered) == EXPECTED_COVERED_STEPS
    assert len(steps) - len(covered) == EXPECTED_UNCOVERED_STEPS
    assert 0 < len(covered) < len(steps), "before 가 전무하거나 이미 만점이면 H1 이 검정이 아니다"


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
    """L3: G₀ 의 CQ 서명 — 논문 §4.2 의 before 열.

    CQ01 이 응답 불가가 되면 특허가 사라진 것이고, CQ03 이 20(=전 공정)을 반환하면
    특허↔공정 링크가 끊어진 것이다. 둘 다 H1 을 조용히 무효화한다.
    """
    _, path = graph_v0
    results = {r.name: r for r in run_cqs(path, QUERIES_CQ)}

    missing = CQ_MUST_ANSWER - results.keys()
    assert not missing, f"CQ 파일이 사라졌다: {missing}"

    for name in CQ_MUST_ANSWER:
        assert results[name].passed, f"{name} 이 G₀ 에서 응답하지 못한다"

    assert results["CQ01_patents_per_process_step"].rows == EXPECTED_COVERED_STEPS
    assert results["CQ03_uncovered_process_steps"].rows == EXPECTED_UNCOVERED_STEPS
    assert results["CQ06_concepts_without_recent_patents"].rows == EXPECTED_CONCEPTS_WITHOUT_RECENT


def test_baseline_patents_have_applicants(graph_v0):
    """모든 특허가 출원인을 갖는다 — CQ08(전 공정 포트폴리오 보유, §1.1)의 전제.

    TBox 는 ont:assignedTo 를 처음부터 정의했지만 ABox 가 비워두고 있었다. 그 상태로는
    "삼성전자가 전 공정 포트폴리오를 보유한다"는 논문의 출발점을 그래프에 물어볼 수 없다.
    """
    g, _ = graph_v0
    pats = set(g.subjects(RDF.type, ONT["Patent"]))
    with_org = {s for s, _ in g.subject_objects(ONT["assignedTo"])}

    assert len(with_org & pats) == EXPECTED_PATENTS_WITH_APPLICANT
    for _, o in g.subject_objects(ONT["assignedTo"]):
        assert (o, RDF.type, ONT["Organization"]) in g, f"assignedTo 의 객체가 Organization 이 아니다: {o}"


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
    """PROVENANCE 가 모르는 TTL 이 스냅샷에 섞이면 잡는다 — baseline 이 조용히 오염된다."""
    fake = tmp_path / "sdkb"
    shutil.copytree(EXTERNAL_SDKB, fake)
    (fake / "sdkb-abox-experts.ttl").write_text("# PROVENANCE 가 모르는 ABox\n", encoding="utf-8")

    problems = verify_snapshot(fake)
    assert any("sdkb-abox-experts.ttl" in p for p in problems), problems


# --- CLI 계약 (Makefile/CI 가 부르는 경로) ------------------------------------

def test_vendor_verify_cli_exits_zero():
    """`make snapshot` 이 부르는 CLI. SDKB 원본 없이 동작해야 CI 에서 돈다."""
    r = subprocess.run(
        ["python", "-m", "sdkb_paper.ontology.vendor", "--verify"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
