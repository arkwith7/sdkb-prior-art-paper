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
import sys

import pytest
from rdflib import RDF, URIRef

from sdkb_paper.config import EXTERNAL_SDKB, ONT, QUERIES_CQ
from sdkb_paper.ontology.baseline import build_baseline, summarize
from sdkb_paper.ontology.vendor import (
    license_restricted_absences,
    verify_freshness,
    verify_snapshot,
)
from sdkb_paper.validate.cq_runner import run_cqs
from sdkb_paper.validate.shacl_gate import validate_graph
from sdkb_paper.validate.vocab_coverage import measure

# 얼린 스냅샷이 만들어내는 G₀ 의 서명.
# 스냅샷을 의도적으로 갱신하면 이 숫자들이 바뀐다 — 그때는 data/MANIFEST.md 의 표와
# 논문 §2.4 표 2 를 함께 고쳐야 한다. 그 강제가 이 상수의 존재 이유다.
#
# --- 스냅샷 세대별 관측 (2026-08-01 · CLAUDE.md §1-3 · §2.1) ------------------
# **구 값을 덮어쓰지 않고 세대별로 남긴다.** 새 스냅샷 위의 측정은 새 실험이고(§2.1),
# 구 판정은 소급 수정하지 않는다(§1-3) — v0.9 §6 과 v1.0/v1.1 이 인용하는 것은 "교정 전
# 자원에서의 관측"이므로 그 값이 인용 가능한 채로 남아야 한다.
#
# 상류 2839afb 스냅샷(CR-007 반영)에서 움직인 것:
#   트리플 105,588 → 105,713 (+125 · skos:broader T-Box 선언 등)
#   Process 11 → 12 — 신규 `data:process/plasma_processing`. **특허가 0건**이라
#   공정 단계 49 → 50 이고 공백도 29 → 30 이다. **커버 20 은 불변** — S1 의 분자는
#   움직이지 않았고 분모만 늘었다. IPC/CPC 매핑 규칙도 83 → 84 로 함께 늘었다.
#
# 이 성장이 D-19 의 반증이 아니라 **확증**이다: 개념층은 실제로 자랐는데
# `ir_corpus_v09.parquet` 의 sha256 은 바이트 단위로 동일했다(ec5ea51b626d3ff9).
# 자원은 움직였고 검색 파이프라인만 그것을 읽지 않았다.
#
# 상류 39855bb 스냅샷(CR-008·CR-009 + CR-004R `84ea514`)에서 움직인 것:
#   트리플 105,713 → 115,095 (+9,382). 내역은 파일 단위로 전부 설명된다 —
#   `sdkb-abox-prior-art.ttl` +9,378(B층 `CitedPatent` 3,034 → 3,513 · CR-008) ·
#   `sdkb-patent.ttl` +60(**T-Box 술어 5개** `reasonGround`·`groundClause`·`noticeDate`·
#   `noticeRound`·`noticeType` + `RejectionType` 개체 7 · CR-004R) ·
#   **중복 흡수 −56**(B층 문헌이 A층과 같은 IPC 심볼 28개를 다시 선언한다 · 무해).
#   Process·SubProcess·Device·covered·uncovered·mapping_rules 는 **전부 불변**이다 —
#   이번 델타는 특허 문서층과 거절근거 어휘층이고 공정 개념축을 건드리지 않았다.
#
#   `sdkb-abox-prior-art.ttl` 의 **파일 단위 순감은 0** 이다 — CR-008 성공기준 ③
#   ("사라진 트리플 0")을 하류가 독립적으로 확인했다. 병합 그래프의 집합 차분이 순감을
#   보고한다면 그것은 `owl:unionOf` 리스트의 **공백노드 재라벨**이지 삭제가 아니다.
SNAPSHOT_OBSERVATIONS = {
    # 구 스냅샷(≤ 83fd494) — 보존용. 테스트가 검사하지 않는다.
    "pre_remediation": {"triples": 105588, "process": 11, "subprocess": 38, "device": 34,
                        "steps": 49, "covered": 20, "uncovered": 29, "mapping_rules": 83},
    # 상류 2839afb(CR-007 반영 · 스냅샷 서명 b98ad787d1fe) — 보존용. PLAN-035 두 팔의 O′ 팔이다.
    "post_cr007": {"triples": 105713, "process": 12, "subprocess": 38, "device": 34,
                   "steps": 50, "covered": 20, "uncovered": 30, "mapping_rules": 84},
    # 상류 39855bb(CR-008 반영 · PLAN-040) — 보존용.
    "post_cr008": {"triples": 115095, "process": 12, "subprocess": 38, "device": 34,
                   "steps": 50, "covered": 20, "uncovered": 30, "mapping_rules": 84},
    # 상류 4f3dbfb(CR-013 반영 · PLAN-043) — 보존용.
    # 트리플이 19 줄어든 것은 상류가 `involvesMaterial → hf_acid` 오링크 34 → 15 로 정리한
    # 결과다(회신 §3 · patents −6 · prior-art −13). 어휘·T-Box·클래스는 불변이므로
    # process·subprocess·device·steps·covered 는 그대로다.
    "post_cr013": {"triples": 115076, "process": 12, "subprocess": 38, "device": 34,
                   "steps": 50, "covered": 20, "uncovered": 30, "mapping_rules": 84},
    # 현행 스냅샷(상류 7347410 · CR-012 반영 · PLAN-045) — 아래 EXPECTED_* 의 원천.
    # +3,732 는 B층 확증분할 질의 200 의 A-Box 다(TTL 4,204 트리플 중 IPC 심볼 등 472 는
    # 기존 노드와 겹쳐 흡수됐다). **T-Box 는 건드리지 않았으므로** process·subprocess·
    # device·steps·covered·mapping_rules 는 전부 불변이다 — 그 불변이 "층을 파일로 갈랐다"의 증거다.
    "current": {"triples": 118808, "process": 12, "subprocess": 38, "device": 34,
                "steps": 50, "covered": 20, "uncovered": 30, "mapping_rules": 84},
}
_CURRENT = SNAPSHOT_OBSERVATIONS["current"]

EXPECTED_TRIPLES = _CURRENT["triples"]
                            # 2026-07-23 미반영 SDKB 온톨로지 전량 반영(사용자 결정): 선행기술 ABox
                            # (CitedPatent 3,034 + 개념링크 realizesProcess/concernsDevice/involvesMaterial)
                            # · 상용화(TRL) · 자원기반관점(RBV)을 G₀ 에 편입. 49,307 → 105,588.
                            # **선행기술조사 정답지 도달성 0%→95.3%(노드)**. 개념링크는 정의별 곡선 —
                            # Process∪Device 54.6%/+material 63.4%/+전의미 70.5%/+분류 95.3%(재측정 확정). 단 CitedPatent
                            # 는 명시 타입이 ont:CitedPatent 라 CQ01(?patent a ont:Patent)이 안 세므로
                            # C₀ 20/49·H1 네 표본집합 불변(19/21 통합테스트 통과로 실측). 선행기술을 커버로
                            # 세면 26/49(+6). 구 이력(청구항 TBox +97 → 49,307)은 git 참조.
EXPECTED_TRIPLES_LEGACY = 49307  # 2026-07-23 청구항-feature·거절판단 순수 TBox 반영(SDKB d578bf3): +97 —
                            # 신규 클래스 4(Claim·ClaimFeature·PriorArtJudgment·CitedPatent) + 익명
                            # unionOf 1 · ObjectProperty +10 · DatatypeProperty +5. G₀ 에 이 어휘의
                            # 인스턴스가 0이라(청구항 분해 ABox 는 보강 코퍼스 G₁·G₂ 전용) ABox·엣지 불변 —
                            # realizesProcess 1565·concernsDevice 181·assignedTo 1053·Patent 1000 불변 →
                            # C₀ 20/49·H1 네 표본집합 p 불변·4층 게이트 통과. 구 49,210.
                            # 2026-07-21 전문가 상세 경력 A-Box 적재(SDKB): +4,906 — 경력 datatype
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
EXPECTED_PROCESS = _CURRENT["process"]      # 구 11 (SemiKong Table 7 의 L1 그룹 10개 · Patterning
                            # 이 리소/식각 둘로 갈림) + plasma_processing 1 = 12
EXPECTED_SUBPROCESS = _CURRENT["subprocess"]  # Table 7 의 L2 모듈 + SDKB 고유 유닛
EXPECTED_DEVICE = _CURRENT["device"]        # H2 의 개념 축은 Process ∪ Device (HBM·GAA 는 Device 다)
EXPECTED_PATENTS = 1200     # A층 SIRP 거절특허 1,000 + B층 확증분할 질의 200(CR-012 · PLAN-045).
                            # **완화가 아니라 승계다** — 둘 중 하나라도 어긋나면 여전히 깨진다.
                            # G₀ 는 "현행 SDKB" 다 (특허 0건이 아니다)
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
EXPECTED_COVERED_STEPS = _CURRENT["covered"]      # 20 — 새 스냅샷에서도 불변
EXPECTED_UNCOVERED_STEPS = _CURRENT["uncovered"]  # 구 29 → 30 (plasma_processing 은 특허 0건)

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
EXPECTED_CONCEPTS_WITHOUT_RECENT = 59   # CQ06 — 개념 84개 중 2021년 이후 출원 전무.
                            # 구 58(개념 83 · 그 전 61). +1 은 신규 plasma_processing 이며
                            # 특허가 0건이라 "최근 출원 없음"에 그대로 들어온다.
EXPECTED_PATENTS_WITH_APPLICANT = 1000  # 출원인 없는 특허는 포트폴리오 분석에 쓸 수 없다

# G₀ 의 **어휘 검증 커버리지** 서명 (논문 §3.4.2 지표 ii · §4.2 · SPEC-004).
# 이 숫자가 논문 본문에 인쇄된다 — 조용히 움직이면 논문이 틀린다. 그래서 여기서 얼린다.
#
# CQ 8개(손으로 고른 것) 시절: 술어 5/53 = 9.4% · 클래스 4/25 = 16.0% — 특허 축 하나의 100%.
# CQ 22개(태스크에서 도출 · SPEC-004 P1–P5): 아래. 올린 방법은 임계값이 아니라 태스크다.
EXPECTED_VOCAB_PREDICATES = (38, 86)  # CQ 검증 44.2% — 2026-07-23 미반영 SDKB 반영으로 술어 사용
                                      # 83→86(선행기술 hasCPC·인용 claimText·상용화 trlLevel). CQ 검증분
                                      # 38 은 불변 — 새 축은 아직 태스크 CQ 가 아니라 SHACL 이 본다(§5.2).
EXPECTED_VOCAB_CLASSES = (18, 30)     # CQ 검증 60.0% — 클래스 사용 27→30(+CitedPatent·CPCSymbol·TRL)

# **게이트 커버리지 = CQ ∪ SHACL.** 목표는 커버리지 90% 가 아니라 "아무도 안 보는 어휘 = 0" 이다.
# 새 축 5종(hasCPC·claimText·trlLevel·CPCSymbol·TechnologyReadinessLevel)은 new_axes_shape.ttl 이
# 본다 → 게이트 커버리지 100% 유지(구 83/83·27/27 → 86/86·30/30).
EXPECTED_GATE_PREDICATES = (86, 86)   # 100% — 새 축 술어를 new_axes_shape 이 게이트
EXPECTED_GATE_CLASSES = (30, 30)      # 100% — 아무도 안 보는 클래스 0 (CitedPatent·CPCSymbol·TRL 포함)

# G₀ 의 IP-R&D CQ before 값 (§4.2 의 G₀ 열). G₁ 과 비교되는 수치이므로 여기서 고정한다.
EXPECTED_IPRD_ROWS = {
    # CQ26 은 1,249 → 1,324(+75). B층 질의 200 중 75건이 수출통제 대상 개념에 링크돼
    # 노출 집계에 들어온 것이다(B층 개념링크 보유 117/200 의 부분집합). 자원이 바뀐 것이
    # 아니라 **모집단이 커진 것**이므로 승계한다 — 상류 T-Box·통제 인스턴스는 불변이다.
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
    "CQ26_patent_export_control_exposure": 1324, # 수출통제 대상 공정·소자를 구현하는 거절특허
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


def test_verify_snapshot_tolerates_absent_license_restricted(tmp_path):
    """라이선스 제한 파일(특허 전문)은 gitignore 되어 클론/CI 에 없다 — 그 부재는 실패가 아니다.

    이 관용이 없으면 심사자가 저장소만 받아 돌리는 L0 게이트가 늘 빨간불이 되어,
    논문 §7.2 의 "4층 게이트는 상류 없이 재현 가능" 주장이 깨진다.
    """
    fake = tmp_path / "sdkb"
    shutil.copytree(EXTERNAL_SDKB, fake)
    restricted = fake / "sdkb-abox-prior-art.ttl"
    assert restricted.exists(), "픽스처 전제: 로컬 스냅샷엔 라이선스 제한 파일이 있다"
    restricted.unlink()  # 클론/CI 상태를 흉내낸다

    problems = verify_snapshot(fake)
    assert not any("sdkb-abox-prior-art.ttl" in p for p in problems), problems
    # 부재는 실패가 아니지만 조용하지도 않다 — 별도 창구로 표면화된다.
    assert "sdkb-abox-prior-art.ttl" in license_restricted_absences(fake)


def test_license_restricted_flag_comes_from_code_not_from_hand():
    """플래그는 **코드가** 박아야 한다 — 손으로 넣은 메타데이터는 다음 vendor 에서 사라진다.

    2026-08-01 실측: 04ab68b 가 PROVENANCE.json 에 손으로 넣은 license_restricted 2건이
    다음 `make vendor`(fa16f2f)에서 조용히 지워졌고, 신선한 클론/CI 의 L0 가 다시 깨졌다.
    """
    from pathlib import Path

    from sdkb_paper.ontology.vendor import LICENSE_RESTRICTED, VENDOR_FILES

    vendored = {Path(rel).name for rel, _role in VENDOR_FILES}
    assert LICENSE_RESTRICTED <= vendored, "vendor 대상이 아닌 파일에 플래그를 걸 수 없다"

    prov = json.loads((EXTERNAL_SDKB / "PROVENANCE.json").read_text(encoding="utf-8"))
    flagged = {e["file"] for e in prov["files"] if e.get("license_restricted")}
    assert flagged == set(LICENSE_RESTRICTED), (
        f"스냅샷의 플래그가 코드 상수와 다르다: {flagged} vs {set(LICENSE_RESTRICTED)}")


def test_verify_snapshot_still_catches_tampered_license_restricted(tmp_path):
    """관용은 '부재'에만 적용된다 — 파일이 있으면 변조는 여전히 잡는다."""
    fake = tmp_path / "sdkb"
    shutil.copytree(EXTERNAL_SDKB, fake)
    target = fake / "sdkb-abox-prior-art.ttl"
    target.write_text(target.read_text(encoding="utf-8") + "\n# tampered\n", encoding="utf-8")

    problems = verify_snapshot(fake)
    assert any("sdkb-abox-prior-art.ttl" in p and "sha256" in p for p in problems), problems
    assert license_restricted_absences(fake) == []  # 있으니 부재 목록은 비어야 한다


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
    # `python` 이 PATH 에 없는 환경(venv 활성화 없이 pytest 실행 등)이 실제로 있다.
    # 인터프리터는 지금 이 테스트를 돌리는 것과 같은 것을 쓴다.
    r = subprocess.run(
        [sys.executable, "-m", "sdkb_paper.ontology.vendor", "--verify"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr


# --- 파생: 거절근거 조항 인스턴스 (CR-004R · 888MB TTL 라인 스캔) ----------------

_REASON_TTL_FIXTURE = """\
@prefix ont: <https://w3id.org/sdkb/ontology#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<https://w3id.org/sdkb/data/patent/kr_1020040038467> ont:hasClaim <https://w3id.org/sdkb/data/claim/rej_1020040038467_c1> ;
    ont:rejectionEvidence <https://w3id.org/sdkb/data/rejection/kr_1020040038467__29-2-__r1>,
        <https://w3id.org/sdkb/data/rejection/kr_1020040038467__42-3-__r1> .

<https://w3id.org/sdkb/data/rejection/kr_1020040038467__29-2-__r1> a ont:RejectionReason ;
    ont:groundClause "29-2-"^^xsd:string ;
    ont:noticeDate "2010-10-26"^^xsd:date ;
    ont:noticeRound 1 ;
    ont:noticeType "의견제출통지서"^^xsd:string ;
    ont:reasonGround ont:Rejection_Inventiveness .

<https://w3id.org/sdkb/data/rejection/kr_1020040038467__42-3-__r1> a ont:RejectionReason ;
    ont:groundClause "42-3-"^^xsd:string ;
    ont:noticeDate "2010-10-26"^^xsd:date ;
    ont:noticeRound 1 ;
    ont:noticeType "의견제출통지서"^^xsd:string ;
    ont:reasonGround ont:Rejection_ClaimRequirements .

<https://w3id.org/sdkb/data/rejection/kr_1019990000001__29-1-2__r2> a ont:RejectionReason ;
    ont:groundClause "29-1-2"^^xsd:string ;
    ont:noticeRound 2 ;
    ont:noticeType "거절결정서"^^xsd:string ;
    ont:reasonGround ont:Rejection_Novelty .
"""


def _fake_sdkb_with_reasons(tmp_path, body: str):
    from sdkb_paper.ontology.vendor import REJECTION_REASON_SRC

    src = tmp_path / "sdkb" / REJECTION_REASON_SRC
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text(body, encoding="utf-8")
    return tmp_path / "sdkb"


def test_derive_rejection_reasons_reads_clause_resolution(tmp_path):
    """조항(項)·회차·통지종별을 잃지 않고 옮긴다 — rejection_basis.csv 가 접는 해상도다.

    마지막 인스턴스는 `noticeDate` 가 없고 `rejectionEvidence` 로도 걸려 있지 않다.
    결측은 빈 칸으로 남고, 미연결은 **세어서 보고**한다 — 조용히 지우지 않는다.
    """
    import csv

    from sdkb_paper.ontology.vendor import _derive_rejection_reasons

    dest = tmp_path / "out"
    dest.mkdir()
    entry = _derive_rejection_reasons(_fake_sdkb_with_reasons(tmp_path, _REASON_TTL_FIXTURE), dest)

    assert entry["counts"] == {"reasons": 3, "applications": 2, "unlinked_to_patent": 1}
    rows = list(csv.DictReader((dest / entry["file"]).open(encoding="utf-8")))
    assert [r["doc_id"] for r in rows] == [
        "kr_1019990000001", "kr_1020040038467", "kr_1020040038467"]   # 정렬은 결정적이다
    assert rows[0] == {
        "doc_id": "kr_1019990000001", "clause": "29-1-2", "ground": "Rejection_Novelty",
        "notice_round": "2", "notice_type": "거절결정서", "notice_date": "",
        "reason_id": "kr_1019990000001__29-1-2__r2",
    }
    # 조항 두 종이 한 출원 안에서 갈린다 — 접힘 해소의 직접 증거(CR-004R 검증기준 #4).
    assert {r["clause"] for r in rows if r["doc_id"] == "kr_1020040038467"} == {"29-2-", "42-3-"}
    # 원문 0열 — 청구항·초록 텍스트가 섞이면 커밋할 수 없다(CLAUDE.md §1-5).
    assert set(rows[0]) == {"doc_id", "clause", "ground", "notice_round",
                            "notice_type", "notice_date", "reason_id"}


def test_derive_rejection_reasons_is_deterministic(tmp_path):
    """두 번 돌리면 같은 sha256 — 스냅샷 서명이 실행마다 흔들리면 사전등록이 무의미하다."""
    from sdkb_paper.ontology.vendor import _derive_rejection_reasons

    home = _fake_sdkb_with_reasons(tmp_path, _REASON_TTL_FIXTURE)
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    assert (_derive_rejection_reasons(home, a)["sha256"]
            == _derive_rejection_reasons(home, b)["sha256"])


def test_derive_rejection_reasons_refuses_silent_zero(tmp_path):
    """상류 직렬화가 바뀌어 0건이 나오면 **멈춘다** — 빈 CSV 를 얼리면 하위집단이 조용히 사라진다."""
    from sdkb_paper.ontology.vendor import _derive_rejection_reasons

    dest = tmp_path / "out"
    dest.mkdir()
    home = _fake_sdkb_with_reasons(tmp_path, "@prefix ont: <https://w3id.org/sdkb/ontology#> .\n")
    with pytest.raises(SystemExit, match="RejectionReason"):
        _derive_rejection_reasons(home, dest)


def test_derive_rejection_reasons_absent_source_is_tolerated(tmp_path):
    """상류 원본이 없는 환경(신선한 클론)에서는 None — vendor 전체를 깨뜨리지 않는다."""
    from sdkb_paper.ontology.vendor import _derive_rejection_reasons

    assert _derive_rejection_reasons(tmp_path / "nowhere", tmp_path) is None
