# 아카이브 색인 — 무엇이 여기 있고 왜 여기 있는가

> **이 파일의 존재 이유.** `archive/` 는 89개 문서를 갖고 있으나 목록이 없었다. **PLAN 은
> 지워지지 않으므로**([README](../README.md)) 이 디렉터리는 계속 늘어나고, 목록이 없으면
> "이미 결정된 것"을 다음 세션이 다시 결정한다.
>
> **여기 있는 것은 전부 인용 가능한 기록이되 현행 정본이 아니다.** 현행 정본은
> [CANONICAL-INDEX](../CANONICAL-INDEX.md) 가 판정하고, 살아 있는 계획은
> [plans/](../plans/) 와 [OPEN-ITEMS](../plans/OPEN-ITEMS.md) 에 있다.
> **`v0.5`·`v0.9` 구본 표시가 붙은 문서는 인용 금지다.**
>
> **아래 표는 기계로 추출했다** — 제목은 각 문서의 첫 표제, 상태는 그 문서가 머리말에서
> 스스로 밝힌 문구다. **요약을 사람이 새로 쓰지 않았다**(CLAUDE.md §1-1 과 같은 이유 —
> 손으로 쓴 요약은 원문과 조용히 어긋난다). 빈 칸은 그 문서가 머리말에 상태를 적지 않았다는
> 뜻이며, 완료 여부는 원문에서 확인한다.
>
> *생성: 2026-08-30 (PLAN-071 · PLAN-079-prereg 2행 추가 · 같은 추출 규칙) · 재생성은 이 파일 말미의 명령으로 한다.*

| 문서 | 제목 | 문서가 밝힌 상태 |
|---|---|---|
| [AUDIT-2026-07-18.md](AUDIT-2026-07-18.md) | 원고 v0.5 ↔ 저장소 정합 감사 (2026-07-18) |  |
| [CANONICAL-INDEX-v05.md](CANONICAL-INDEX-v05.md) | 정본 인덱스 (CANONICAL INDEX) — v0.5 구본 (ARCHIVED · 인용 금지) |  |
| [CR-004-full-analysis-2026-07-30.md](CR-004-full-analysis-2026-07-30.md) | CR-004 · 거절근거의 조항 단위 구조화 (D-06) |  |
| [GLOSSARY-STATISTICS.md](GLOSSARY-STATISTICS.md) | 통계 개념과 용어 정의 — 이 논문을 위한 최소한 |  |
| [PLAN-001-h10-mapping-rules.md](PLAN-001-h10-mapping-rules.md) | IPC/CPC → 개념 룰의 H10 계열 보강 | 완료 |
| [PLAN-002-samsung-collection.md](PLAN-002-samsung-collection.md) | 삼성전자·SK하이닉스 특허 수집과 G₁ 구축 | 완료 |
| [PLAN-003-device-market-layer.md](PLAN-003-device-market-layer.md) | Device→Process 브리지와 DART 제품/시장 레이어 |  |
| [PLAN-004-emerging-tech-recognition.md](PLAN-004-emerging-tech-recognition.md) | 신기술 인식 레이어 (별칭 · 조합 정의 · 후보 발굴) |  |
| [PLAN-005-h1-coverage-test.md](PLAN-005-h1-coverage-test.md) | H1 검정 (공정 단계별 개념 커버리지) | 완료 |
| [PLAN-006-h2-case-preregistration.md](PLAN-006-h2-case-preregistration.md) | H2 검정 — 사례 사전등록과 조기탐지 시차 |  |
| [PLAN-007-h2-vintage-classification.md](PLAN-007-h2-vintage-classification.md) | H2 재검정 — 당시(vintage) 분류로 |  |
| [PLAN-008-scheme-independent-concepts.md](PLAN-008-scheme-independent-concepts.md) | 분류체계 독립 개념과 DART 외부 준거로 H2 재검정 |  |
| [PLAN-009-left-truncation-and-scheme-independent-retest.md](PLAN-009-left-truncation-and-scheme-independent-retest.md) | 좌측절단 교정 + 분류체계 독립 개념으로 H2 재검정 | 완료 (2026-07-13) |
| [PLAN-010-h2prime-name-baseline.md](PLAN-010-h2prime-name-baseline.md) | H2′ — 시점 유효한 대조군(명칭)으로 다시 세운 조기탐지 검정 | 완료 (2026-07-14) |
| [PLAN-011-family-dedup-robustness.md](PLAN-011-family-dedup-robustness.md) | DOCDB 패밀리 중복 제거 (§4.5 강건성) | 완료 (2026-07-14) |
| [PLAN-012-per-applicant-retest.md](PLAN-012-per-applicant-retest.md) | 출원인별 분리 재검정 (§4.5.2 강건성) | 완료 (2026-07-14) |
| [PLAN-013-ontology-quality-validation.md](PLAN-013-ontology-quality-validation.md) | 온톨로지 품질검증 — T-Box · A-Box · SHACL · 기능적 CQ 확장 |  |
| [PLAN-014-ipr-d-framework-and-portability.md](PLAN-014-ipr-d-framework-and-portability.md) | 품질검증 프레임워크의 재현성 — CQ 도출 프로토콜 · 소부장 IP-R&D 재적용 |  |
| [PLAN-015-compliance-regulatory-layer.md](PLAN-015-compliance-regulatory-layer.md) | 규제·컴플라이언스 축 — 수출통제 인스턴스 적재 (B 최소 실증) | 완료 요약 (2026-07-15 · SDKB `f65d4cd` · G₀ 44,192) |
| [PLAN-016-rq2-population-leadtime.md](PLAN-016-rq2-population-leadtime.md) | RQ2(H2) 재설계 — 소자 모집단 리드타임 검정 (A-both) + DART 외부 준거 확장 |  |
| [PLAN-017-v09-ir-benchmark-dataset.md](PLAN-017-v09-ir-benchmark-dataset.md) | v0.9 선행기술 검색 벤치마크 데이터셋: 정의 및 보완 | 상태(원문): 초안 (2026-07-25) · 승인 대기 🛑 |
| [PLAN-018-v09-retrieval-tgate-harness.md](PLAN-018-v09-retrieval-tgate-harness.md) | v0.9 검색 시스템·T-gate·Ablation 하네스 (계층 B 설계·사전등록) | 상태: 승인 (2026-07-26 사용자) 🟢 · M2 착수 가능 |
| [PLAN-019-v09-completeness-crosslingual.md](PLAN-019-v09-completeness-crosslingual.md) | v0.9 원고 완성도 개선 계획 (진보성·신규성 입증) · 교차언어 축 신설 | 상태(원문): 진행 중 (2026-07-28 착수) |
| [PLAN-020-w4-fault-injection.md](PLAN-020-w4-fault-injection.md) | W4 결함주입 설계 동결 · 오염 격리 규율 (H1 · 원고 §4.10·§6.5) | 상태: 실행 중 (2026-07-28 착수 · 사용자 승인 "권고안대로 진행") |
| [PLAN-021-w4b-cq-refinement.md](PLAN-021-w4b-cq-refinement.md) | W4b CQ 판정 세분화 사전등록 동결 (H1′ · 원고 §6.5·§6.6·부록 D-0·F) | 상태: 동결 (2026-07-28 · 사용자 승인 "네 진행해 주세요") |
| [PLAN-022-n5c-layer-separation.md](PLAN-022-n5c-layer-separation.md) | N5c · L3–T3 검출 표면 분리 사전등록 (H1″ · 원고 §4.9·§6.5.3·부록 D-0·F) | 상태: 완료 (2026-07-28 · 사용자 승인 "네") |
| [PLAN-023-n5d-claim-level-pa-cq.md](PLAN-023-n5d-claim-level-pa-cq.md) | N5d · 선행기술 CQ 청구항 수준 확장 사전등록 (C1 표현범위 · 원고 §3.1.6·§6.6·§9.7) | 상태: 완료 (2026-07-28 · 사용자 승인 "네") |
| [PLAN-024-h2-test-tgate-and-claim-matrix.md](PLAN-024-h2-test-tgate-and-claim-matrix.md) | N12·H2 · 확증 분할 T-gate 판정 + 부록 B 주장–증거 매트릭스 정합 사전등록 (C3 · 원고 §6.3·부록 B) | 상태: 동결 (2026-07-28 · 사용자 승인 "네") |
| [PLAN-025-w9-h1ppp-confirmatory.md](PLAN-025-w9-h1ppp-confirmatory.md) | W9 · H1‴ 확증 재사전등록 (홀드아웃 결함 · 원고 §6.5.4·§7.2·표 7.1) | 상태(원문): 🔒 동결 (2026-07-28 · v2) |
| [PLAN-027-strong-dense-baseline.md](PLAN-027-strong-dense-baseline.md) | 강한 밀집 기준선 추가 (B2′) · 확증분할 재개봉 사전등록 (C2 · RQ2/H3) | 상태: 초안 · 승인대기 🛑 (2026-07-28 작성) |
| [PLAN-028-manuscript-artifact-consistency.md](PLAN-028-manuscript-artifact-consistency.md) | 원고 산출물 계약 정비 · 투고 준비 (C1·C2·C3 공통 · 새 실험 0) | 상태: 초안 · 승인대기 🛑 (2026-07-28 작성) |
| [PLAN-029-post-remediation-reexperiment.md](PLAN-029-post-remediation-reexperiment.md) | 상류 교정 후 재실험 로드맵 (C0 → C2·C3 · 3층 구조) | 상태: 초안 · 승인대기 🛑 (2026-07-29 작성) |
| [PLAN-030-a-layer-h2-preregistration.md](PLAN-030-a-layer-h2-preregistration.md) | A층 사전등록: H2 최초 실검정 (스냅샷 O → O′) | 종결 (2026-08-06 `plans/` → `archive/` 이동) — 실행됐고 H2 는 미검정으로 끝났다(D-19) |
| [PLAN-031-b-layer-second-confirmation-split.md](PLAN-031-b-layer-second-confirmation-split.md) | B층 제2 확증분할 수집 사전등록 (C2 · H3·H4·H5 재확증) | 상태: 🔒 동결 (2026-07-31 승인 · 2026-07-29 작성 · 2026-07-30·31 갱신) |
| [PLAN-032-b-layer-pilot-collection.md](PLAN-032-b-layer-pilot-collection.md) | B층 수집 드라이버 · 파일럿 500콜 **3단계 설계** | 종결 (2026-08-06 `plans/` → `archive/` 이동) — 5단계 완주 · 200건 채택 · 봉인 미개봉 |
| [PLAN-033-v2-manuscript-restructure.md](PLAN-033-v2-manuscript-restructure.md) | v2.0 투고본 재구성 · **1단계(재실험 무관분) 실행 계획** | 상태: 축 확정(사용자 승인 2026-08-01) · 1단계 착수 |
| [PLAN-034-concept-linker-requirements.md](PLAN-034-concept-linker-requirements.md) | 개념 적용기(linker) — **§2 1단계 요구정의** 🛑 | 종결 (2026-08-06 `plans/` → `archive/` 이동) — 5단계까지 완료 · 코드 동결 |
| [PLAN-035-h2-linker-preregistration.md](PLAN-035-h2-linker-preregistration.md) | 사전등록: H2 최초 실검정 (개념 적용기 경유 · O → O′) | 종결 (2026-08-06 `plans/` → `archive/` 이동) — 실행·판정 완료: H2 최초 실검정 · 기각 |
| [PLAN-036-effort-at-recall-requirements.md](PLAN-036-effort-at-recall-requirements.md) | 1단계 요구정의: Effort@Recall · Candidate Reduction (운용 효율) | 상태: ✅ 5단계까지 완료 · 종결 (2026-08-06 `plans/` → `archive/` 이동 · 머리말 정정) |
| [PLAN-037-i1-promotion-precheck.md](PLAN-037-i1-promotion-precheck.md) | §2.2 사전 점검: I1(층 사이의 어긋남)을 한계에서 본론으로 | 종결 (2026-08-06 `plans/` → `archive/` 이동) — 편집 완료 |
| [PLAN-038-c2prime-transfer-requirements.md](PLAN-038-c2prime-transfer-requirements.md) | 1단계 요구정의: C2′ 전달 실험 (RQ5 · 검색 층 → 생성 층) |  |
| [PLAN-039-v2-thesis-restructure.md](PLAN-039-v2-thesis-restructure.md) | §2.2 사전 점검: v2.0 논지로의 원고 재구조화 (제목·초록·§1·§2.6·§4.9·§6.7·§7.3·§10) | 종결 (2026-08-06 `plans/` → `archive/` 이동) — 편집 완료 |
| [PLAN-040-post-remediation-tgate-and-b-layer.md](PLAN-040-post-remediation-tgate-and-b-layer.md) | 사전등록: 상류 교정 4건 반영 스냅샷의 T-gate 재적용 + B층 확증분할 H3 재확증 | 상태: 조건 동결 (§2·§3·§5·§6) · 서명 미기입 (§4.2) |
| [PLAN-041-dsr-reframing.md](PLAN-041-dsr-reframing.md) | 연구방법 전환: 통계적 가설검정 중심 → 설계과학연구(DSR) 중심 | 상태: ✅ 종료 (2026-08-08) — §9 네 단계 전부 집행 완료. 아래 §18 이 종료 기록이다 |
| [PLAN-042-cr011-central-axis-reprep.md](PLAN-042-cr011-central-axis-reprep.md) | 사전등록: CR-011 반영 중심축 스냅샷의 B층 청구항 도달 재측정 + 판독 B 개봉 조건 재판정 | 상태: 조건·서명 동시 동결 · 실행 전 🛑 |
| [PLAN-043-cr013-hf-precision-remeasure.md](PLAN-043-cr013-hf-precision-remeasure.md) | 사전등록: CR-013(원소 기호 별칭 정밀도) 반영 스냅샷의 전량 재측정 | 상태: 관통 완료 (2026-08-08) · 결과는 §8 |
| [PLAN-045-b-layer-query-ingestion-downstream.md](PLAN-045-b-layer-query-ingestion-downstream.md) | B층 질의 200을 하류가 소비한다 (D-27 검증기준 ① · 판독 B 개봉 선결) | 상태: ✅ 1–5단계 완주(2026-08-08). S1–S7 전부 통과 — 그러나 계획은 아직 닫히지 않았다 |
| [PLAN-046-d33-corpus-rebuild-preregistration.md](PLAN-046-d33-corpus-rebuild-preregistration.md) | D-33 코퍼스 재조립 사전등록 (§2.1 정지 게이트 1개) |  |
| [PLAN-047-readout-b-unsealing-preregistration.md](PLAN-047-readout-b-unsealing-preregistration.md) | 판독 B 개봉 사전등록 (C2 재확증 · C2′ 확증 · T4 마진 동결) | 상태: 🔒 동결 (2026-08-08 · 커밋 `67568c8`) |
| [PLAN-048-failure-typology-requirements.md](PLAN-048-failure-typology-requirements.md) | 실패 유형 분류표 — 1단계 요구정의 (트랙 C) |  |
| [PLAN-048-submission-retarget.md](PLAN-048-submission-retarget.md) | 투고 재조준·재구성 마스터 계획 (v0.9 → 투고본) | 완료 기준(DoD)의 수치는 정본이 아니다 |
| [PLAN-048-부속A-CLAUDE_md-개정안.md](PLAN-048-부속A-CLAUDE_md-개정안.md) | PLAN-048 부속 A — CLAUDE.md 개정·재구조화 방안 |  |
| [PLAN-048-부속B-제목초록기여-시안.md](PLAN-048-부속B-제목초록기여-시안.md) | PLAN-048 부속 B — 제목·초록·기여 재조준 시안 (승인 후 3단계에서 적용) |  |
| [PLAN-050-vendor-annotation-delta-preregistration.md](PLAN-050-vendor-annotation-delta-preregistration.md) | 사전등록 — 주석 델타 스냅샷 교체와 CR-017 투영 편입 | 상태: 🔒 동결 대상 |
| [PLAN-051-invisible-resource-delta-reporting.md](PLAN-051-invisible-resource-delta-reporting.md) | D-43 해소 · "게이트로는 보이지 않는 델타"를 리포트가 스스로 말하게 한다 |  |
| [PLAN-052-intro-background-restructure.md](PLAN-052-intro-background-restructure.md) | 투고 파생본 §1·§2 재구성 (기조 변경 게이트 기록) |  |
| [PLAN-053-manuscript-focus-restructure.md](PLAN-053-manuscript-focus-restructure.md) | 투고 파생본 집중도 재구성 (§2.2 정지 게이트 · 요건 5종) | 상태: ✅ 적용 완료 (2026-08-17 · 사용자 승인 후 실행) |
| [PLAN-054-multilingual-baseline-preregistration.md](PLAN-054-multilingual-baseline-preregistration.md) | 다국어 텍스트 기준선 사전등록 (B6–B9 · B★ · P1′ · 강건성 점검) | 상태: 3단계(설계) 승인 완료 (2026-08-17 사용자) → 4단계(구현) 진행 가능 |
| [PLAN-055-incomplete-judgment-robustness.md](PLAN-055-incomplete-judgment-robustness.md) | 불완전 정답 아래의 비교 강건성 (전문가 판정 필요의 제거 · §2 1단계 요구정의) |  |
| [PLAN-056-practitioner-mirrored-experiment-exposition.md](PLAN-056-practitioner-mirrored-experiment-exposition.md) | 실무 모사 관점의 실험 구조 재서술 (구성도 · 구성요소 표 · 전제 승격 · 재순위화 천장) | 상태: ✅ 승인 · 적용 (2026-08-17 · 사용자 승인) |
| [PLAN-057-family-citation-merge.md](PLAN-057-family-citation-merge.md) | 가족 인용 병합으로 정답지 결손 줄이기 (§2 1단계 요구정의) |  |
| [PLAN-058-single-repo-benchmark-release.md](PLAN-058-single-repo-benchmark-release.md) | 평가 하네스의 단일 리포 공개 (1단계 산출물: 허용목록 초안 · 라이선스 표) | 상태: 완료 (2026-08-20 · 커밋 `b04fdda`) · 종결 기록은 §11 |
| [PLAN-059-findings-forward-ch5-ch6.md](PLAN-059-findings-forward-ch5-ch6.md) | 결과·논의 장의 발견 우선 재서술 (§2.2 기조 변경 게이트) |  |
| [PLAN-060-external-review-response.md](PLAN-060-external-review-response.md) | 외부 검토 반영 · 단일변인성 · 임계 안정성 · DSR 명시화 (§2.2 기조 변경 게이트) |  |
| [PLAN-061-additional-delta-eligibility-screening.md](PLAN-061-additional-delta-eligibility-screening.md) | 추가 델타 T-gate 적용의 자격 심사 (PLAN-060 단계 C · §2.1 경로) |  |
| [PLAN-062-external-review-round2.md](PLAN-062-external-review-round2.md) | 외부 검토 2차 반영 · 정의 정밀화와 주장 단위 정렬 (§2.3 파생본 절차) |  |
| [PLAN-063-external-review-3-submission-consistency.md](PLAN-063-external-review-3-submission-consistency.md) | 외부 검토 3차 반영 · 투고 정합 마감 | 아카이빙 2026-08-23 — 본체 완주 |
| [PLAN-064-prereg.md](PLAN-064-prereg.md) | EP5(제2 도메인 이식 시연) 사전등록 | 지위: 발효(동결) |
| [PLAN-064-second-domain-portability-and-aei-reframe.md](PLAN-064-second-domain-portability-and-aei-reframe.md) | PLAN-064 (v2) — 제2 공학 온톨로지 이식 시연(EP5)과 AEI 투고 프레이밍 재구성 | 아카이빙 2026-08-25 — 본체 완주 · 잔여는 이월 |
| [PLAN-065-readability-restructure.md](PLAN-065-readability-restructure.md) | 투고 파생본 산문의 논술 구조 개선 (가독성 · 논리 정합) |  |
| [PLAN-066-terminology-first-mention.md](PLAN-066-terminology-first-mention.md) | 용어 첫 등장 규율과 B 단계 편입 (V1·V2 기계화) | 아카이빙 2026-08-23 — 본체 완주 |
| [PLAN-067-ep5-reframe-port-anatomy.md](PLAN-067-ep5-reframe-port-anatomy.md) | EP5 재프레이밍: 일반화 시험에서 **이식 해부**로 |  |
| [PLAN-068-defensive-prose-reduction-and-cause-separation.md](PLAN-068-defensive-prose-reduction-and-cause-separation.md) | 방어 서술의 감량과 논거의 실험적 보강 | 아카이빙 2026-08-23 — 트랙 A 완주 |
| [PLAN-069-axiomatization-reframe.md](PLAN-069-axiomatization-reframe.md) | 기조 전환: 선언된 중심축을 **작동하는 공리**로 | 아카이빙 2026-08-25 — 트랙 A 완주 |
| [PLAN-071-followup-paper-axiomatized-resource-redesign.md](PLAN-071-followup-paper-axiomatized-resource-redesign.md) | 이관 기록: 후속 논문(논문 B) 설계는 상류로 갔다 (2026-08-30) | 지위: 이관 기록 · 아카이브 |
| [PLAN-072-prereg.md](PLAN-072-prereg.md) | 사전등록: CR-001B ⑤ · CR-020 ⑥ 하류 지표 (스냅샷 `0a7ff153` → `48971f8`) | 아카이빙 2026-08-23 — 실행 완주 |
| [PLAN-073-claim-feature-projection-wiring.md](PLAN-073-claim-feature-projection-wiring.md) | 요구정의: 한정요소 개념 투영을 순위 함수에 배선한다 (하류 §2 1단계 🛑) | 아카이빙 2026-08-23 — 2단계 관찰까지 완주 후 승계 |
| [PLAN-074-part1-redesign-extraction-unit.md](PLAN-074-part1-redesign-extraction-unit.md) | 이관 기록: 판단 쌍 추출 단위 재설계는 상류로 갔다 (2026-08-29) |  |
| [PLAN-075-operative-channel-path-term-and-projection-wiring.md](PLAN-075-operative-channel-path-term-and-projection-wiring.md) | 요구정의: 작동 층의 **통로**를 연다 (경로 점수 항 + 한정요소 투영 배선 · 하류 §2 1단계 🛑) | 지위: 요구정의 · 1단계 승인 완료 (2026-08-24 · §11 다섯 항 전부) |
| [PLAN-076-seal-ledger-wiring.md](PLAN-076-seal-ledger-wiring.md) | 봉인 열람 원장 배선 교정 (O-6 · PLAN-068 트랙 C) |  |
| [PLAN-078-prereg-snapshot-013854b.md](PLAN-078-prereg-snapshot-013854b.md) | 사전등록: 스냅샷 `48971f8` → `013854b` 반영 (B층 인용문헌 복원) | 아카이빙 2026-08-25 — 실행 완주 |
| [PLAN-079-prereg-measurement-013854b.md](PLAN-079-prereg-measurement-013854b.md) | 사전등록: CR-001B ⑤ · CR-020 ⑥ 하류 판정과 T3 (스냅샷 `013854b` · D-53) | 지위: 미실행 종결 · 아카이브 (2026-08-30 · 사용자 지시) |
| [PLAN-081-reframe-existence-proof.md](PLAN-081-reframe-existence-proof.md) | 투고처 재조준과 주장 크기 재정렬 (§2.2 요건 다섯 · 정지 게이트 1개) | 아카이빙 (2026-08-29 · 사용자 지시) |
| [PLAN-082-figure-en.md](PLAN-082-figure-en.md) | 본문 그림 7종의 영문판 (§2 완주 · 2026-08-26 종결) | 아카이빙 (2026-08-29 · 사용자 지시) |
| [PLAN-083-condense-body-tables-figures.md](PLAN-083-condense-body-tables-figures.md) | 본문 축약(§2·§4·§5·§6) · 표 간결화 · 그림 라벨 감량 (2026-08-27) | 아카이빙 (2026-08-29 · 사용자 지시) |
| [PLAN-084-supplementary-reader-facing.md](PLAN-084-supplementary-reader-facing.md) | supplementary 를 편집 이력이 아니라 독자용 부록으로 재조직 | 아카이빙 (2026-08-29 · 사용자 지시) |
| [PLAN-085-restructure-findings-first.md](PLAN-085-restructure-findings-first.md) | 발견 중심 재구성과 작업 정본 층의 복원 | 아카이빙 (2026-08-29 · 사용자 지시) |
| [README-PLAN-066-files.md](README-PLAN-066-files.md) | PLAN-066 산출물 — 리포 반영 안내 | 아카이빙 2026-08-23 |
| [SPEC-003-competency-questions.md](SPEC-003-competency-questions.md) | SPEC-003 · 역량질문(CQ)과 §4.2 의 측정 지표 |  |
| [STATUS-v05.md](STATUS-v05.md) | 진행 실적 — v0.5 구본 (ARCHIVED · 인용 금지) |  |
| [PLAN-040-oprime-snapshot-signatures.json](PLAN-040-oprime-snapshot-signatures.json) | (데이터 파일 — 스냅샷 서명) |  |

---

## 재생성

이 표는 손으로 갱신하지 않는다. 파일이 늘거나 머리말이 바뀌면 다시 뽑는다 — 추출 규칙은
**첫 표제 = 제목**, **머리말 40행 안의 굵은 글씨 `아카이빙|상태|지위|종결|완료` = 상태**다.
