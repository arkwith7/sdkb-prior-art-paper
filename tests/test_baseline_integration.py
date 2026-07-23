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
import json
import os
import shutil
import subprocess

import pytest
from rdflib import RDF, URIRef

from sdkb_paper.config import EXTERNAL_SDKB, ONT, QUERIES_CQ
from sdkb_paper.ontology.baseline import build_baseline, summarize
from sdkb_paper.ontology.vendor import verify_freshness, verify_snapshot
from sdkb_paper.validate.cq_runner import run_cqs
from sdkb_paper.validate.shacl_gate import validate_graph
from sdkb_paper.validate.vocab_coverage import measure

# 얼린 스냅샷이 만들어내는 G₀ 의 서명.
# 스냅샷을 의도적으로 갱신하면 이 숫자들이 바뀐다 — 그때는 data/MANIFEST.md 의 표와
# 논문 §2.4 표 2 를 함께 고쳐야 한다. 그 강제가 이 상수의 존재 이유다.
EXPECTED_TRIPLES = 49210    # 2026-07-21 전문가 상세 경력 A-Box 적재(SDKB): +4,906 — 경력 datatype
                            # 22종 · EquipmentModel 29 · ExpertCase 163(사례 reification) · 큐레이션
                            # ontology_alignment 기반 역량 링크. **특허↔공정 엣지는 한 건도 안 움직였다**
                            # (realizesProcess 1565 · concernsDevice 181 · assignedTo 1053 불변) —
                            # C₀ 20/49 불변 · H1 네 표본집합 p 전부 불변(4.77e-07·3.05e-05·1.95e-03·
                            # 2.44e-04) · RQ3 세 층 불변. docs/deidentification_protocol.md §1.5. 구 44,221.
                            # 그 전: 2026-07-20 SubProcess 한국어 별칭 승격(SDKB da745ef): skos:altLabel@ko
                            # +19 — 원자층증착=ALD·화학기상증착=CVD·물리기상증착/스퍼터링=PVD·
                            # 건식(플라즈마) 식각·습식 식각. 라벨만 늘고 특허↔공정 엣지 불변이라
                            # C₀ 20/49 · H1 네 표본집합 p값 전부 불변(실측). 구 44,202.
                            # 그 전: 2026-07-15 청구항 어휘(C-2 RQ3): ont:claimText·claimCount TBox 선언
                            # +10 (술어 2개 × 5 트리플) — 구 44,192. G₀ 의 SIRP 특허는 청구항1만
                            # 있어 claimText 사용 0, ABox·엣지 불변(C₀ 20/49 불변 · H1 p 4자리 불변).
                            # 그 전: 2026-07-15 규제 축(PLAN-015): governance TBox+인스턴스 +378 — 구 43,814
                            # +2: hardConstraint·softConstraint 의 skos:prefLabel. Expert·Problem·특허
                            # +100: rdfs:label → skos:prefLabel 는 술어 교체라 净 0 이고,
                            # 전문가의 EN 표기 100개가 skos:altLabel 로 **새로 들어왔다**.
                            # 특허 엣지·개념 링크는 한 건도 안 움직인다 (C₀ 20/49 불변 · H1 p 불변).
                            # −33: 역할별로 갈라져 있던 회사 노드 11쌍이 organization/ 하나로
                            # 접혔다 (data:org/samsung_electronics 등은 assignedTo in-edge 가
                            # 0 이었으므로 **특허 엣지는 한 건도 움직이지 않았다** — C₀ 불변).
EXPECTED_PROCESS = 11       # SemiKong Table 7 의 L1 그룹 10개 (Patterning 이 리소/식각 둘로 갈림)
EXPECTED_SUBPROCESS = 38    # Table 7 의 L2 모듈 + SDKB 고유 유닛
EXPECTED_DEVICE = 34        # H2 의 개념 축은 Process ∪ Device (HBM·GAA 는 Device 다)
EXPECTED_PATENTS = 1000     # SIRP 거절특허 — G₀ 는 "현행 SDKB" 다 (특허 0건이 아니다)
                            # 인용문헌 3,763건은 ont:Patent 로 타입하지 않는다 (서지가 없다)

# H1 의 before: 49개 공정 단계 중 **20개**가 커버되어 있고 29개가 공백이다.
#
# ⚠ 이 값은 16 이었다. 16 은 **틀린 값이었다** (2026-07-14 발견).
#
# `sdkb-abox-patents.ttl` 은 상류에서 gitignore 되는 빌드 산출물인데, `make vendor` 가 재빌드를
# 강제하지 않고 디스크에 있던 파일을 그대로 복사했다. 그 파일은 공정 어휘 복원(SDKB `ad7fe3d`,
# 공정 20 → 49) **이전에** 빌드된 것이라, 복원된 어휘로는 텍스트 추출이 한 번도 돌지 않았다.
# 그래서 annealing·metallization·oxidation·passivation 네 단계는 **실제로 특허가 있는데도**
# C₀(s)=0 으로 기록됐다. PROVENANCE 의 sha256 은 이것을 못 잡는다 — 해시는 파일이 바뀌지
# 않았음만 보장하지 옳게 빌드됐음을 보장하지 않는다.
#
# 재빌드하니 realizesProcess 1,557 → 1,565 · concernsDevice 162 → 181 (잃은 링크 0).
# 즉 **H1 의 before 가 낮게 잡혀 검정이 실제보다 쉬웠다.** 재발 방지는 vendor 의
# _reject_stale_artifacts() 와 Makefile 의 상류 재빌드 의존이다.
#
# 복원된 단계가 G₀ 에서 비어 있다는 구조적 편향은 여전하다 — 그래서 논문은 H1 을 **두 집합으로
# 보고한다**: 확장 집합(49)과 기존 집합(20). 독자가 "새로 추가한 단계 덕분에 산 결과인가"를
# 직접 판별할 수 있어야 한다 (§4.5).
EXPECTED_COVERED_STEPS = 20
EXPECTED_UNCOVERED_STEPS = 29

# G₀ 의 CQ 서명 — 논문 §4.2 의 before 열.
#
# 8개 CQ 가 **모두 응답한다**. 그래서 §3.4.2 가 쓰려던 이진 지표("G₀ 응답 불가 → G₁ 응답 가능
# 비율")는 분모가 0 이라 정의되지 않는다. 보강 효과는 **응답 완전성**(결과 행 수)으로 잰다:
# CQ06 의 커버리지 공백이 G₁ 에서 줄어드는가, CQ01 의 커버 공정 20개가 늘어나는가.
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
# SPEC-004 단계 3·4 의 IP-R&D CQ 는 EXPECTED_IPRD_ROWS 아래에 정의하고 여기에 합친다
# (행 수까지 고정하므로 목록을 두 벌 유지하지 않는다). 22개 **모두 G₀ 에서 응답해야 정상이다** —
# 응답하지 못하면 온톨로지 결함이지 "G₁ 이 고칠 CQ" 가 아니다 (SPEC-004 §6).

# 완전성 지표의 before 값. G₁ 과 비교되는 수치이므로 여기서 고정한다.
EXPECTED_CONCEPTS_WITHOUT_RECENT = 58   # CQ06 — 개념 83개 중 2021년 이후 출원 전무 (구 61)
EXPECTED_PATENTS_WITH_APPLICANT = 1000  # 출원인 없는 특허는 포트폴리오 분석에 쓸 수 없다

# G₀ 의 **어휘 검증 커버리지** 서명 (논문 §3.4.2 지표 ii · §4.2 · SPEC-004).
# 이 숫자가 논문 본문에 인쇄된다 — 조용히 움직이면 논문이 틀린다. 그래서 여기서 얼린다.
#
# CQ 8개(손으로 고른 것) 시절: 술어 5/53 = 9.4% · 클래스 4/25 = 16.0% — 특허 축 하나의 100%.
# CQ 22개(태스크에서 도출 · SPEC-004 P1–P5): 아래. 올린 방법은 임계값이 아니라 태스크다.
EXPECTED_VOCAB_PREDICATES = (38, 83)  # CQ 검증 45.8% — 2026-07-22 CQ28(특허↔문제↔전문가) 추가로
                                      # caseFailureMode·hasCaseExperience 2개 신규 검증(36→38). 문제층
                                      # (§G1 Phase C)이 전문가 매칭 축을 실제로 심문한다는 증거다(§5.2).
EXPECTED_VOCAB_CLASSES = (18, 27)     # CQ 검증 66.7% — 클래스 사용 25→27(+EquipmentModel·ExpertCase)

# **게이트 커버리지 = CQ ∪ SHACL.** 목표는 커버리지 90% 가 아니라 "아무도 안 보는 어휘 = 0" 이다.
# 신규 어휘 29종은 expert_shape.ttl(SHACL)이 본다 → 게이트 커버리지는 100% 유지.
EXPECTED_GATE_PREDICATES = (83, 83)   # 100% — 전문가 경력 술어를 expert_shape 이 게이트
EXPECTED_GATE_CLASSES = (27, 27)      # 100% — 아무도 안 보는 클래스 0 (EquipmentModel·ExpertCase 포함)

# G₀ 의 IP-R&D CQ before 값 (§4.2 의 G₀ 열). G₁ 과 비교되는 수치이므로 여기서 고정한다.
EXPECTED_IPRD_ROWS = {
    "CQ09_rejection_prior_art": 414,             # 거절 근거가 기록된 특허
    "CQ10_prior_art_candidates_by_concept": 8,   # plasma_etch · 2015 이전 출원
    "CQ11_experts_for_process_skill": 66,
    "CQ12_problem_process_equipment_expert": 3134,  # 2026-07-21 전문가 링크를 큐레이션
                                                    # ontology_alignment ID 로 전환(텍스트 재매칭 폐기).
                                                    # 정렬 공정 링크가 더 정밀해 problem→process→expert
                                                    # 조인이 4967→3134 로 줄었다(정직한 변화 · 여전히 응답).
    "CQ13_value_chain_vendor_portfolio": 21,     # 정체성 통합 이전에는 **0 행**이었다
    "CQ14_value_chain_role_distribution": 18,
    # SPEC-004 단계 4 — 불량 인과·재료·계측 축 (2026-07-15). 여섯도 G₀ 에서 응답해야 정상이다.
    "CQ15_failure_causal_chain": 6,
    "CQ16_material_incompatibility": 3,
    "CQ17_material_problem_expert": 35,
    "CQ18_patents_by_skill": 10,
    "CQ19_process_control_and_metrology": 6,
    "CQ20_experts_by_equipment": 395,  # 2026-07-21 정렬 기반 링크 + EquipmentModel 노드로
                                       # 전문가↔장비 경험이 대폭 풍부해졌다(15→395 · vendor·
                                       # equipment_class·equipment_model 세 축).
    "CQ21_process_hierarchy_portfolio": 38,
    "CQ22_patent_equipment_and_technode": 9,
    # PLAN-015 · 규제·수출통제 축 (2026-07-15). RQ3 IP-R&D 산출물 4(라이선싱·기술이전 심사).
    # gov: 축이라 어휘 커버리지 측정(ont: 한정) 밖이지만, CQ 로 기능 검증한다.
    "CQ23_concept_export_control": 37,           # 개념↔통제 링크 전량
    "CQ24_national_core_technology": 12,         # 국가핵심기술(NCT) 지정 개념
    "CQ25_critical_control_concepts": 7,         # CRITICAL 수준 통제 개념
    "CQ26_patent_export_control_exposure": 1249, # 수출통제 대상 공정·소자를 구현하는 거절특허
}
CQ_MUST_ANSWER |= set(EXPECTED_IPRD_ROWS)


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


def test_baseline_iprd_cq_signature(graph_v0):
    """§4.2 의 G₀ 열 — 태스크에서 도출한 IP-R&D CQ 의 before 값.

    CQ13 이 0 을 반환하면 회사 정체성이 다시 쪼개진 것이다(공급 역할과 출원인 역할이 다른
    IRI 로 갈라지면 이 조인은 **에러 없이 0행**을 낸다 — 그것이 이 지표의 존재 이유다).
    """
    _, path = graph_v0
    results = {r.name: r.rows for r in run_cqs(path, QUERIES_CQ)}
    for name, expected in EXPECTED_IPRD_ROWS.items():
        assert results[name] == expected, f"{name}: {results[name]} != {expected}"


def test_baseline_vocab_coverage_signature(graph_v0):
    """어휘 검증 커버리지를 수치로 고정한다 (논문 §3.4.2 · §4.2).

    CQ 를 늘리면 이 상수를 함께 고쳐야 하고, 그때 논문의 표도 같이 움직인다.
    그 강제가 이 테스트의 존재 이유다.
    """
    _, path = graph_v0
    cov = measure(path, QUERIES_CQ)

    assert (len(cov.verified_predicates), len(cov.predicates_used)) == EXPECTED_VOCAB_PREDICATES
    assert (len(cov.verified_classes), len(cov.classes_used)) == EXPECTED_VOCAB_CLASSES

    # **게이트 커버리지(CQ ∪ SHACL) = 100% · 아무도 안 보는 어휘 0.** 이것이 이 사이클의 핵심
    # 결과다 — 목표는 커버리지 90% 가 아니라 "검증되지 않는 어휘가 없다" 이다.
    assert (len(cov.gated_predicates), len(cov.predicates_used)) == EXPECTED_GATE_PREDICATES
    assert (len(cov.gated_classes), len(cov.classes_used)) == EXPECTED_GATE_CLASSES
    assert not cov.ungated_predicates(), f"아무도 안 보는 술어: {cov.ungated_predicates()}"
    assert not cov.ungated_classes(), f"아무도 안 보는 클래스: {cov.ungated_classes()}"

    # 태스크에서 도출한 CQ 가 실제로 그 축들을 심문하는가 (SPEC-004 단계 3·4 의 성과)
    verified = cov.verified_predicates
    for local in ("hasPriorArtExaminer", "rejectedFor", "hasProcessExpertise", "hasSkill",
                  "requiresSkill", "involvesProcess", "involvesEquipment", "companyType",
                  "providedBy", "madeBy", "usesEquipmentClass",
                  "exhibitsFailureMode", "isDueTo", "mitigatedBy", "involvesMaterial",
                  "concernsSkill", "hasEquipmentExperience", "hasSubprocess"):
        assert str(ONT[local]) in verified, f"{local} 이 미검증이다 — CQ 가 깨졌다"

    # 서지·프로비넌스는 CQ 가 아니라 **SHACL** 이 본다 (기능이 아니라 제약이므로).
    assert str(ONT["abstractText"]) not in cov.verified_predicates      # CQ 는 안 본다
    assert str(ONT["abstractText"]) in cov.shacl_predicates             # SHACL 이 본다


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


def test_baseline_company_identity_is_unified(graph_v0):
    """회사 하나 = IRI 하나 — IP-R&D 질의(RQ3)의 선결 조건.

    상류는 같은 회사에 **역할에 따라 다른 IRI** 를 줬었다: 큐레이션 기업 `data:org/`,
    장비 공급사 `data:vendor/`, 특허 출원인 `data:organization/`. 역할은 이미
    rdf:type(ont:Organization·ont:Vendor)이 말하는데 IRI 접두사가 그것을 중복하면서
    정체성만 깼다.

    갈라진 채로 두면 "이 회사가 공급하는 장비와 이 회사의 특허 포트폴리오"라는 질의가
    **에러 없이 0행**을 낸다 — data:vendor/lam_research 는 장비를 공급하고
    data:organization/lam_research 는 특허 19건을 갖는 다른 노드였다.
    상류가 이 상태로 되돌아가면 이 테스트가 잡는다 (SDKB 581360a · org_identity_crosswalk.csv).
    """
    g, _ = graph_v0
    data = str(ONT).replace("/ont/", "/data/")
    companies = set(g.subjects(RDF.type, ONT["Organization"])) | set(
        g.subjects(RDF.type, ONT["Vendor"])
    )
    # 유일한 예외는 "미상 공급사" 자리표시자다 — 실재 회사가 아니므로 정체성을 주지 않는다.
    placeholder = {f"{data}vendor/generic"}
    strays = {str(s) for s in companies if not str(s).startswith(f"{data}organization/")}
    assert strays == placeholder, f"organization/ 밖의 회사 노드: {sorted(strays)}"

    # 병합의 요점: 공급 역할과 특허 포트폴리오가 같은 노드에 붙는다.
    lam = URIRef(f"{data}organization/lam_research")
    assert (lam, RDF.type, ONT["Vendor"]) in g, "lam_research 에 공급 역할이 없다"
    assert (lam, RDF.type, ONT["Organization"]) in g, "lam_research 에 출원인 역할이 없다"
    assert list(g.subjects(ONT["providedBy"], lam)), "lam_research 가 장비를 공급하지 않는다"
    assert list(g.subjects(ONT["assignedTo"], lam)), "lam_research 가 특허를 갖지 않는다"


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


# --- L0 신선도 (해시가 잡지 못하는 실패 양식) ---------------------------------

def test_verify_freshness_passes_on_current_snapshot():
    """현행 스냅샷은 L0 를 통과한다 — 통과 경로의 회귀 고정."""
    assert verify_freshness(EXTERNAL_SDKB) == []


def test_verify_freshness_rejects_missing_attestation(tmp_path):
    """이행 증명 없는 스냅샷은 거부한다.

    2026-07-14 사고 당시의 상태가 정확히 이것이다 — sha256 은 내내 맞았고 L1–L3 도 내내
    통과했으나 산출물이 입력보다 낡아 H1 의 before 가 낮게 잡혔다.
    """
    fake = tmp_path / "sdkb"
    shutil.copytree(EXTERNAL_SDKB, fake)
    prov = json.loads((fake / "PROVENANCE.json").read_text(encoding="utf-8"))
    del prov["freshness"]
    (fake / "PROVENANCE.json").write_text(json.dumps(prov, ensure_ascii=False), encoding="utf-8")

    problems = verify_freshness(fake)
    assert any("freshness" in p for p in problems), problems


def test_verify_freshness_rejects_partial_attestation(tmp_path):
    """일부 산출물만 덮은 증명은 증명이 아니다."""
    fake = tmp_path / "sdkb"
    shutil.copytree(EXTERNAL_SDKB, fake)
    prov = json.loads((fake / "PROVENANCE.json").read_text(encoding="utf-8"))
    prov["freshness"]["artifacts"].pop("ontology/sdkb-abox-patents.ttl", None)
    (fake / "PROVENANCE.json").write_text(json.dumps(prov, ensure_ascii=False), encoding="utf-8")

    problems = verify_freshness(fake)
    assert any("sdkb-abox-patents.ttl" in p for p in problems), problems


def test_verify_freshness_rejects_stale_derived_graph(tmp_path):
    """스냅샷보다 낡은 baseline 을 거부한다 — 갱신 후 재조립을 잊으면 분석이 옛 그래프를 읽는다."""
    fake = tmp_path / "sdkb"
    shutil.copytree(EXTERNAL_SDKB, fake)
    stale = tmp_path / "graph_v0.ttl"
    stale.write_text("# 스냅샷보다 낡은 파생 산출물\n", encoding="utf-8")
    os.utime(stale, (0, 0))

    problems = verify_freshness(fake, derived=stale)
    assert any("낡았다" in p for p in problems), problems


# --- CLI 계약 (Makefile/CI 가 부르는 경로) ------------------------------------

def test_vendor_verify_cli_exits_zero():
    """`make snapshot` 이 부르는 CLI. SDKB 원본 없이 동작해야 CI 에서 돈다."""
    r = subprocess.run(
        ["python", "-m", "sdkb_paper.ontology.vendor", "--verify"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
