# 어휘 검증 커버리지 — `data/processed/graph_v0.ttl`

분모 = 그래프에 실제로 쓰인 `ont:` 어휘. 어휘는 **기능(CQ)** 또는 **구조(SHACL)** 중
최소 한 층이 봐야 한다. **목표는 커버리지 90% 가 아니라 '아무도 안 보는 어휘 = 0' 이다.**

| 축 | CQ 검증 | SHACL 검사 | **게이트(합집합)** | 사용됨 | **아무도 안 봄** |
|---|---:|---:|---:|---:|---:|
| 술어 | 36 (66.7%) | 19 | **54 (100.0%)** | 54 | **0** |
| 클래스 | 18 (72.0%) | 11 | **25 (100.0%)** | 25 | **0** |

## CQ 별 검증 어휘

| CQ | 결과행 | 검증한 어휘 |
|---|---:|---|
| CQ01_patents_per_process_step | 20 | `Patent` · `Process` · `SubProcess` · `realizesProcess` |
| CQ02_recent_patents_by_step | 365 | `Patent` · `filingDate` · `realizesProcess` |
| CQ03_uncovered_process_steps | 29 | `Patent` · `Process` · `SubProcess` · `realizesProcess` |
| CQ04_concept_annual_series | 304 | `Device` · `Patent` · `Process` · `SubProcess` · `concernsDevice` · `filingDate` · `realizesProcess` |
| CQ05_concept_vs_ipc_series | 1959 | `Patent` · `filingDate` · `hasIPC` |
| CQ06_concepts_without_recent_patents | 58 | `Device` · `Patent` · `Process` · `SubProcess` · `concernsDevice` · `filingDate` · `realizesProcess` |
| CQ07_device_process_crosswalk | 55 | `Patent` · `concernsDevice` · `realizesProcess` |
| CQ08_applicant_process_portfolio | 316 | `Patent` · `assignedTo` · `realizesProcess` |
| CQ09_rejection_prior_art | 414 | `RejectedPatent` · `hasPriorArt` · `hasPriorArtExaminer` · `rejectedFor` |
| CQ10_prior_art_candidates_by_concept | 8 | `Patent` · `filingDate` · `realizesProcess` |
| CQ11_experts_for_process_skill | 66 | `Expert` · `Process` · `SubProcess` · `hasSkill` · `requiresSkill` |
| CQ12_problem_process_equipment_expert | 4967 | `Expert` · `Problem` · `hasProcessExpertise` · `involvesEquipment` · `involvesProcess` |
| CQ13_value_chain_vendor_portfolio | 21 | `EquipmentClass` · `Patent` · `Vendor` · `assignedTo` · `isInstanceOf` · `madeBy` · `providedBy` · `usesEquipmentClass` |
| CQ14_value_chain_role_distribution | 18 | `companyType` |
| CQ15_failure_causal_chain | 6 | `FailureMode` · `Mitigation` · `Problem` · `RootCause` · `Skill` · `exhibitsFailureMode` · `isDueTo` · `mitigatedBy` · `mitigationProvidesSkill` · `occursAtProcessStep` |
| CQ16_material_incompatibility | 3 | `Material` · `incompatibleWith` · `notAllowedWith` · `usesMaterial` |
| CQ17_material_problem_expert | 35 | `Expert` · `Problem` · `hasMaterialExpertise` · `involvesMaterial` |
| CQ18_patents_by_skill | 10 | `Patent` · `concernsSkill` |
| CQ19_process_control_and_metrology | 6 | `Metrology` · `Parameter` · `hasParameter` · `measuredBy` |
| CQ20_experts_by_equipment | 15 | `Equipment` · `EquipmentClass` · `Expert` · `hasEquipmentExperience` |
| CQ21_process_hierarchy_portfolio | 38 | `hasSubprocess` |
| CQ22_patent_equipment_and_technode | 9 | `EquipmentClass` · `Patent` · `RootCause` · `TechnologyNode` · `concernsTechnologyNode` · `realizesEquipmentClass` · `relatedToTopic` |
| CQ23_concept_export_control | 37 | — |
| CQ24_national_core_technology | 12 | — |
| CQ25_critical_control_concepts | 7 | — |
| CQ26_patent_export_control_exposure | 1249 | `Patent` · `concernsDevice` · `realizesProcess` |
| CQ27_fto_claim_readiness | 0 | — |

## 아무도 보지 않는 어휘 (CQ 도 SHACL 도) — **0 이어야 한다**

없음. 모든 어휘가 CQ(기능) 또는 SHACL(구조) 중 최소 한 층의 검증을 받는다.

## CQ 가 검증하지 않는 어휘 (SHACL 이 보는 것 포함)

| 술어 | 사용 | | 클래스 | 사용 |
|---|---:|---|---|---:|
| `abstractText` | 1000 | | `IPCSymbol` | 810 |
| `applicationNumber` | 1000 | | `Organization` | 351 |
| `examinationStatus` | 1000 | | `STEEPVEDimension` | 7 |
| `firstClaimText` | 1000 | | `OptionType` | 5 |
| `patentOffice` | 1000 | | `RejectionType` | 5 |
| `processFamily` | 1000 | | `ConstraintType` | 2 |
| `publicationDate` | 1000 | | `Semiconductor` | 1 |
| `publicationNumber` | 1000 | |  |  |
| `valueChainStage` | 1000 | |  |  |
| `interpretationType` | 914 | |  |  |
| `region` | 336 | |  |  |
| `clientCountry` | 226 | |  |  |
| `complianceSensitivity` | 226 | |  |  |
| `problemCategory` | 226 | |  |  |
| `confidence` | 149 | |  |  |
| `complianceFlag` | 110 | |  |  |
| `validationRequired` | 108 | |  |  |
| `securityLevel` | 1 | |  |  |
