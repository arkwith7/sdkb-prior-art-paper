# 어휘 검증 커버리지 — `data/samples/mini_graph.ttl`

분모 = 그래프에 실제로 쓰인 `ont:` 어휘. 어휘는 **기능(CQ)** 또는 **구조(SHACL)** 중
최소 한 층이 봐야 한다. **목표는 커버리지 90% 가 아니라 '아무도 안 보는 어휘 = 0' 이다.**

| 축 | CQ 검증 | SHACL 검사 | **게이트(합집합)** | 사용됨 | **아무도 안 봄** |
|---|---:|---:|---:|---:|---:|
| 술어 | 36 (80.0%) | 10 | **45 (100.0%)** | 45 | **0** |
| 클래스 | 18 (90.0%) | 12 | **20 (100.0%)** | 20 | **0** |

## CQ 별 검증 어휘

| CQ | 결과행 | 검증한 어휘 |
|---|---:|---|
| CQ01_patents_per_process_step | 3 | `Patent` · `Process` · `SubProcess` · `realizesProcess` |
| CQ02_recent_patents_by_step | 2 | `Patent` · `filingDate` · `realizesProcess` |
| CQ03_uncovered_process_steps | 1 | `Patent` · `Process` · `SubProcess` · `realizesProcess` |
| CQ04_concept_annual_series | 6 | `Device` · `Patent` · `Process` · `SubProcess` · `concernsDevice` · `filingDate` · `realizesProcess` |
| CQ05_concept_vs_ipc_series | 5 | `Patent` · `filingDate` · `hasIPC` |
| CQ06_concepts_without_recent_patents | 2 | `Device` · `Patent` · `Process` · `SubProcess` · `concernsDevice` · `filingDate` · `realizesProcess` |
| CQ07_device_process_crosswalk | 1 | `Patent` · `concernsDevice` · `realizesProcess` |
| CQ08_applicant_process_portfolio | 2 | `Patent` · `assignedTo` · `realizesProcess` |
| CQ09_rejection_prior_art | 1 | `RejectedPatent` · `hasPriorArt` · `hasPriorArtExaminer` · `rejectedFor` |
| CQ10_prior_art_candidates_by_concept | 1 | `Patent` · `filingDate` · `realizesProcess` |
| CQ11_experts_for_process_skill | 1 | `Expert` · `Process` · `SubProcess` · `hasSkill` · `requiresSkill` |
| CQ12_problem_process_equipment_expert | 1 | `Expert` · `Problem` · `hasProcessExpertise` · `involvesEquipment` · `involvesProcess` |
| CQ13_value_chain_vendor_portfolio | 1 | `EquipmentClass` · `Patent` · `Vendor` · `assignedTo` · `isInstanceOf` · `madeBy` · `providedBy` · `usesEquipmentClass` |
| CQ14_value_chain_role_distribution | 1 | `companyType` |
| CQ15_failure_causal_chain | 1 | `FailureMode` · `Mitigation` · `Problem` · `RootCause` · `Skill` · `exhibitsFailureMode` · `isDueTo` · `mitigatedBy` · `mitigationProvidesSkill` · `occursAtProcessStep` |
| CQ16_material_incompatibility | 1 | `Material` · `incompatibleWith` · `usesMaterial` |
| CQ17_material_problem_expert | 1 | `Expert` · `Problem` · `hasMaterialExpertise` · `involvesMaterial` |
| CQ18_patents_by_skill | 1 | `Patent` · `concernsSkill` |
| CQ19_process_control_and_metrology | 2 | `Metrology` · `Parameter` · `hasParameter` · `measuredBy` |
| CQ20_experts_by_equipment | 2 | `Equipment` · `EquipmentClass` · `Expert` · `hasEquipmentExperience` |
| CQ21_process_hierarchy_portfolio | 2 | `hasSubprocess` |
| CQ22_patent_equipment_and_technode | 2 | `EquipmentClass` · `Patent` · `RootCause` · `TechnologyNode` · `concernsTechnologyNode` · `realizesEquipmentClass` |
| CQ23_concept_export_control | 4 | — |
| CQ24_national_core_technology | 2 | — |
| CQ25_critical_control_concepts | 2 | — |
| CQ26_patent_export_control_exposure | 3 | `Patent` · `concernsDevice` · `realizesProcess` |
| CQ27_fto_claim_readiness | 1 | `Patent` · `assignedTo` · `claimCount` · `claimText` |

## 아무도 보지 않는 어휘 (CQ 도 SHACL 도) — **0 이어야 한다**

없음. 모든 어휘가 CQ(기능) 또는 SHACL(구조) 중 최소 한 층의 검증을 받는다.

## CQ 가 검증하지 않는 어휘 (SHACL 이 보는 것 포함)

| 술어 | 사용 | | 클래스 | 사용 |
|---|---:|---|---|---:|
| `applicationNumber` | 5 | | `IPCSymbol` | 2 |
| `patentOffice` | 5 | | `Organization` | 2 |
| `abstractText` | 2 | |  |  |
| `firstClaimText` | 2 | |  |  |
| `examinationStatus` | 1 | |  |  |
| `problemCategory` | 1 | |  |  |
| `processFamily` | 1 | |  |  |
| `publicationNumber` | 1 | |  |  |
| `valueChainStage` | 1 | |  |  |
