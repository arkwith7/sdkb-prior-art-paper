# 정본 인덱스 (CANONICAL INDEX)

> **이 문서의 목적.** 개선 과정에서 쌓인 중간 산출물·계획 문서·초기 현황 데이터가 최종 데이터와
> 섞여, "지금 무엇이 정본인가"가 흐려졌다. 이 문서는 네 디렉토리(`01.code_spec/`·`data/`·`paper/`·
> `queries/`)의 실측 인벤토리를 바탕으로 **정본(FINAL) / 중간(INTERMEDIATE) / 계획(PLAN) / 초기
> 스냅샷(HISTORICAL)** 을 확정한다. 숫자가 문서마다 다를 때는 **이 문서의 §1 표가 최종 판정**이다.
>
> *작성 근거: 2026-07-18 · 온디스크 실측(rdflib) · `data/MANIFEST.md §3` · `PROVENANCE.json`
> (SDKB `edb8ae4`) · 논문 v0.3 초안 실측. STATUS.md 는 진행 정본이나, 아래 §2 의 서명 숫자는
> 이 문서가 STATUS 보다 한 세대 앞선다(STATUS 서명표가 갱신 대기).*

---

## 0. 한눈에 — 지금 무엇이 정본인가

| 축 | 정본 (FINAL) | 위치 |
|---|---|---|
| **논문** | `논문_v0.5_SDKB.md` | `paper/` |
| **baseline 그래프 G₀** | `graph_v0.ttl` (49,307 트리플) | `data/processed/` (gitignore — MANIFEST §3 이 서명) |
| **보강 그래프 G₁** | `graph_v1.ttl` (868,669) | `data/processed/` |
| **소부장 그래프 G₂ (RQ3)** | `graph_v2.ttl` (434,342) | `data/processed/` |
| **얼린 상류 스냅샷** | `data/external/sdkb/` 13파일 (SDKB `d578bf3` — 청구항-feature·거절판단 TBox 반영) | git-tracked · sha256 in `PROVENANCE.json` |
| **검증 게이트 (CQ·SHACL)** | `queries/cq/*.rq` 27개 · `queries/shapes/{graph,delta}/` 5개(+expert_shape) | 전부 LIVE · 고아 0 |
| **데이터셋 정의서 (G₀·G₁·G₂ 정체성)** | `DATASET-CARD.md` (6축: 정의·출처·서명·게이트·배제·상호관계 · 서명은 §1 종속) | `data/` |
| **계약(SPEC)** | `SPEC-001~004` | `01.code_spec/specs/` (숫자는 §1 우선) |
| **진행 현황** | `STATUS.md` | `01.code_spec/` (서명 숫자는 §1·§2 우선) |
| **논문 그림 9장 · 표 11개** | `paper/figures/*.svg` · `paper/tables/*.md` (전량 코드 생성) | `viz/figures.py` 산출 |

---

## 1. 권위 있는 서명 숫자 — SINGLE SOURCE OF TRUTH

**이 표가 최종이다.** 온디스크 실측 = MANIFEST §3 = 논문 v0.3 초안, 세 곳이 일치하는 값이다.

| 항목 | G₀ | G₁ | G₂ (소부장) |
|---|---:|---:|---:|
| **트리플 (정본)** | **49,307** | **868,669** | **434,342** |
| 커버된 공정 / 49 | 20 | **26** | **26** |
| 특허 (병합) | 1,000 (SIRP 거절) | +24,179 델타 (총 25,179) | +12,339 델타 (총 13,339) |
| Process 11 / SubProcess 38 · Device 34 | ✓ | | |
| IPCSymbol | 810 | 2,924 | 2,914 |
| FailureMode (문제층) | 25 | **55** | 25 |
| 청구항 축 (Phase A) | — | claimText 371,267 · abstractText 24,179 · claimCount 24,178 | claimText 161,184(청구항 그래프) |
| 문제층 (Phase C) | — | exhibitsFailureMode 2,816 · relatedToTopic 3,236 | — |
| 출원인(Organization) / 벤더 | 351 / 340 | | 188사(장비 93·재료 50·부분품 45) |
| 게이트 | L1(완화)·L2 consistent·L3 CQ **27/28**(측정) | L1·L2·L3 CQ **28/28** | L1·L2 consistent·L3 CQ **28/28** |
| 그래프 커밋(상류) | SDKB `d578bf3` | 〃 위 델타 | 〃 위 델타 |

> **청구항-feature·거절판단 TBox 반영 (2026-07-23) — G₀ 49,210 → 49,307 (+97).** 상류 SDKB 가
> `d583b0c`(전문가 적재) 이후 `sdkb-patent.ttl` 에 선언한 **순수 TBox** 를 재벤더로 반영했다:
> 신규 클래스 4(`ont:Claim`·`ont:ClaimFeature`·`ont:PriorArtJudgment`·`ont:CitedPatent`) +
> `featureConcept` range 의 익명 unionOf 클래스 1 → owl:Class 82→87 · ObjectProperty 75→85
> (hasClaim·dependsOnClaim·hasFeature·dependsOnFeature·featureConcept·hasJudgment·aboutClaim·
> overPriorArt·onGround·overlappingFeature) · DatatypeProperty 69→74(claimNumber·isIndependent·
> featureSeq·featureText·decompositionMethod). **ABox·엣지는 한 트리플도 안 움직였다** —
> Patent 1000 · realizesProcess 1565 · concernsDevice 181 · assignedTo 1053 · hasIPC 3804 불변 →
> **C₀ 20/49 · H1 네 표본집합 p 전부 불변**(4.77e-07·3.05e-05·1.95e-03·2.44e-04) · 4층 게이트 통과.
> 청구항 분해 ABox(Tier 1/2/3 · 11.6M 트리플)는 **벤더 안 되는 별도 중심축 데이터셋**이라 G₀ 무관.
> 상류 커밋 `d583b0c → d578bf3`. 구 44,221·49,210.
>
> **전문가 상세 경력 적재 (2026-07-21) — G₀ 44,221 → 49,210 (+4,906).** 상류 SDKB 가
> `curated_profiles_kr.json` 의 경력 datatype 22종 · EquipmentModel 29 · ExpertCase 163(사례
> reification) · 큐레이션 `ontology_alignment` 기반 역량 링크를 A-Box 로 실체화했다. G₁·G₂ 도
> 같은 +4,906(공유 G₀ 기반). **특허↔공정 엣지는 한 건도 안 움직였다** (realizesProcess 1565 ·
> concernsDevice 181 · assignedTo 1053 불변) → **C₀ 20/49 · H1 네 표본집합 p 전부 불변**
> (4.77e-07·3.05e-05·1.95e-03·2.44e-04) · **RQ3 세 층 불변**(장비 4.77e-07·재료 4.42e-05·부분품
> 6.57e-05). 값은 전부 비식별 변조/생성값(SDKB `docs/deidentification_protocol.md` §1.5). 구 44,221.
>
> **특허 건수는 "매핑 ≠ 병합 ≠ 분석 말뭉치"로 세 값이 공존한다** — 모순이 아니다. 논문은 병합
> 기준(G₁ 24,179 델타, 초록 서술상 25,179 병합 특허 노드)·분석 말뭉치(H2′ 63,936)를 문맥별로
> 쓴다. 상세 정합은 메모리 `paper-corpus-counts-mapped-vs-merged` 및 논문 §3.2 참조. **트리플
> 수만큼은 위 표가 유일 정본이다.**

> **G₁ 418,738 → 868,669 재동결 (2026-07-22~23, 커밋 `dfdb9dd`).** 두 층이 얹혔다 —
> **(A) 주 대비축 청구항 축**(§G1 Phase A/B): G₁ 병합 특허 24,179건 전량의 초록·전체 청구항을
> `claimText`(371,267 트리플)·`abstractText`(24,179)·`claimCount`(24,178, claim_count=0 인 1건 제외)로
> 실체화. RQ2 선행기술조사의 feature 대비축(상류 SDKB `src_g1` 이 읽어 all-elements feature 실체화)이다.
> **(B) 특허 문제층**(§G1 Phase C): 초록 → 문제원자 추출로 `exhibitsFailureMode`(2,816)·`relatedToTopic`
> (3,236)를 연결하고 FailureMode 개념을 **25 → 55**(신규 30, 사용자 채택·frozen)로 넓혔다. CQ28
> (특허↔문제↔전문가) 비공허 11,794행. **어휘 발명 0**(두 술어 모두 기존 SDKB TBox). 세부 로그는
> `MANIFEST §2`(2026-07-22 두 행) — 온디스크 실측(rdflib)과 정확히 일치한다.
>
> **두 층 모두 H1 엣지를 한 건도 안 건드렸다** — realizesProcess 11,647 · concernsDevice 23,342 ·
> Patent 25,179 불변 → **C₀ 20/49 · C₁ 커버 26 · H1 p 전부 원리적 불변**(datatype·문제층은 커버리지
> 엣지가 아니다). G₂(434,342)는 이 커밋의 대상이 아니므로 불변이다.
>
> **CQ 재측정 완료 (2026-07-23 · `make cq` = cq_runner 전 그래프).** 청구항 축 적재로 **G₁ 이 이제
> CQ27 을 통과한다**(2행). 배터리도 CQ28 추가로 **28개**다. 실측 응답률: **G₀ 27/28 · G₁ 28/28 ·
> G₂ 28/28 · mini_graph 28/28.** 지는 것은 **G₀ 의 CQ27** 하나뿐 — baseline 은 SIRP 특허의 청구항1만
> 있어 FTO 청구항 전문이 없다. **CQ27 은 이제 baseline(G₀)만 떨어뜨리고 특허 보강 두 코퍼스(G₁·G₂)를
> 모두 통과시킨다** — 배터리가 코퍼스를 판별한다는 증거가 더 깔끔해졌다. CQ28(특허↔문제↔전문가)은
> 전 그래프 응답(G₀ 40·G₁ 11,794·G₂ 40·mini 1).

> **커버된 공정 정정 (2026-07-18, AUDIT §5).** 이 표는 G₁ 커버를 **24** 로 적고 있었다 —
> 실측(`data/processed/h1_coverage.csv`: `after>0` 인 단계 수)은 **26** 이다. 중재자를 자처하는
> 문서가 틀린 값을 들고 있었으므로 정정한다. **G₁ 26 = G₂ 26 이 RQ3 의 "폭 포화" 근거**이고
> (`h1_coverage_ksia.csv` 도 26), 24 를 믿으면 그 주장이 거짓으로 보인다.
>
> **L3 응답률 (2026-07-23 재측정으로 갱신).** 실측 **G₀ 27/28 · G₁ 28/28 · G₂ 28/28**. 지는 것은
> `CQ27_fto_claim_readiness` 이고 이제 **G₀ 하나뿐**이다 — 청구항 전문은 특허 보강 코퍼스(G₁·G₂)에
> 실체화돼 있고 baseline 에는 없다. 결함이 아니라 **배터리가 코퍼스를 판별한다는 증거**다.
> (구 값 G₀·G₁ 26/27·G₂ 27/27 은 CQ28 추가·G₁ 청구항 축 적재 이전 · AUDIT-2026-07-18 §S1.)

> **grep 으로 트리플을 세지 말 것.** `grep -c ' \.$'` 프록시는 Turtle 의 `;`·`,` 축약 때문에
> 약 13배 과소계상한다(G₀ 프록시 3,291 vs 실제 49,210). 트리플 수는 **MANIFEST §3 또는 rdflib
> 파싱**으로만 인용한다.

---

## 2. 어긋난 숫자 지도 — 어디의 무엇이 낡았는가 (읽을 때 주의)

개선 과정에서 갱신이 문서를 다 따라가지 못해, 아래 위치는 **옛 세대 숫자**를 들고 있다.
데이터가 틀린 게 아니라 **문서 메타가 낡은 것**이다. 정합화(§5) 전까지는 §1 을 믿는다.

| 위치 | 낡은 값 | 정본 값 (§1) | 낡은 이유 |
|---|---:|---:|---|
| `STATUS.md` G₀ 서명표 | 44,192 | **44,202** | PLAN-015 이후 +10(TBox 선언 2개) 재동결을 서명표에 미반영 |
| `STATUS.md` G₁ 서명표 | 413,340 | **413,730** | 재병합 이후 서명표 미갱신 |
| `STATUS.md` G₁ 서명표 CQ01/03 before | 16 / 33 | 20 / 29 | 낡은 스냅샷 교정(C₀ 16→20) 이전 값 |
| `SPEC-002-baseline-g0.md` | 43,812 (`23d07a1`) | **44,202** (`edb8ae4`) | 두 세대 뒤 (재동결 2회 미반영) |
| `SPEC-003-competency-questions.md` | CQ06 61 또는 29 | 58 | C₀ 16→20 교정 이전 |
| `SPEC-004` CQ 개수 | 22/22 · 43,814 | 27/27 · 44,202 | PLAN-015 의 CQ23–26·규제 재동결 미반영 |
| `data/MANIFEST.md §1` 마지막 행 | 43,812 (`23d07a140cec`) | 44,202 (`edb8ae4`) | §1 이력표가 재동결에 미갱신 (단 **§3 은 44,202 로 정확**) |
| `plans/PLAN-006·007·013·014·016` 헤더 | "승인 대기 / 설계 대기" | STATUS 완료가 정답 | PLAN 헤더는 완료 시 갱신 안 함(설계상). **상태는 STATUS 의 완료/대기 절이 판정**한다 |

> **결번 해소 (2026-07-18).** STATUS 가 완료로 인용하던 `PLAN-011`(패밀리 dedup)·`PLAN-012`(출원인별
> 재검정)의 문서가 부재했다 → **완료 기록형 스텁으로 작성**해 plans/ 를 001–016 연속으로 복원했다.
> 결과물(`robustness_family.md`·`robustness_applicant.md`·표 9/10)은 원래부터 실재한다.

---

## 3. 디렉토리별 분류 요약

### `data/`
| 분류 | 파일 |
|---|---|
| **FINAL — 그래프** | `graph_v0.ttl`(G₀) · `graph_v1.ttl`(G₁) · `graph_v2.ttl`(G₂) |
| **FINAL — 층·강건성 산출** | `graph_v2_{equipment,material,component}.ttl`(표 5b) · `h1_coverage*.csv` · `h1_*.md` · `h2*.csv` · `h2_report.md` · `robustness_{applicant,family}.md` |
| **FINAL — 얼린 스냅샷** | `data/external/sdkb/` 13파일 (sha256 in PROVENANCE) · `data/profiles/*.md`(표 4, 4개 전부 현행) · `data/samples/mini_graph.ttl`(게이트 픽스처) |
| **INTERMEDIATE — 병합 전 입력** | `delta_v1*.ttl` · `delta_v2*.ttl` (모두 그래프의 *입력*, 독립 산출물 아님) |
| **INTERMEDIATE — 변형/분할본** | `graph_v1_famdedup.ttl` · `graph_v1_{samsung,hynix}.ttl` (G₁ 아님 — 강건성 분할본) · `candidates_report.md`(2026-07-13, 현행 동결 이전 작업 목록) |
| **HISTORICAL — raw (gitignore)** | `data/raw/{kipris,bigquery,dart}/…` · `data/interim/*.parquet` (원문·캐시, 재배포 금지) |

### `01.code_spec/`
| 분류 | 파일 |
|---|---|
| **PROGRESS (정본)** | `STATUS.md` — 진행/완료/대기의 판정자 (단 서명 숫자는 §1) |
| **CANONICAL (계약)** | `specs/SPEC-001`(게이트) · `SPEC-002`(G₀) · `SPEC-003`(CQ) · `SPEC-004`(CQ 도출) |
| **REFERENCE** | `README.md` · `GLOSSARY-{ONTOLOGY,SEMICONDUCTOR,STATISTICS}.md` · `REF-001`(IP-R&D) |
| **PLAN — 완료(역사 기록)** | PLAN-001·002·004·005·006·007·009·010·013(부분)·014·015 |
| **PLAN — 폐기/대체** | PLAN-008 (→ PLAN-009 가 대체) |
| **PLAN — 대기(살아있는 의도)** | PLAN-003 (Device→Process·DART 시장층, 보류) · PLAN-016 (RQ2 재설계, STATUS 상 사실상 완료 전이 중) |

### `paper/`
| 분류 | 파일 |
|---|---|
| **FINAL** | `논문_v0.5_SDKB.md` (정본, 유일) |
| **INTERMEDIATE** | `archive/논문초안_v0.2_…md`(3층 모델·삼성 only) · `archive/논문초안_v0.3_…md`(RQ3 이전 번호체계) — 둘 다 폐기, 인용 금지 |
| **GENERATED (코드 산출)** | `figures/*.svg` **9개** — 본문 9장과 1:1 (2026-07-18 통합 반영: 구 fig3+fig4 → `fig3_research_model.svg`, 구 fig1+fig11 → `fig11_summary.svg`; `fig1_gap_map.svg`·`fig4_pipeline.svg` 는 **생성 중단·삭제**). 파일명 번호는 v0.3 명칭 유지 — 본문 `[그림 n]` 과 불일치하는 것이 정상이고 정렬은 조판 시. 부록/진단 전용: `fig8b_…preregistered.svg`(사전등록 코드 팔) · `fig8c_h2_code_arm_d1.svg`(진단 D1) — **본문 그림 번호 없음** · `figures/vocab_coverage_graph_v0.md` · `tables/*.md` |
| **빈 디렉토리 (함정)** | `manuscript/`(.gitkeep 뿐 — 진짜 원고는 `paper/논문_v0.5_SDKB.md`) |

### `queries/`
| 분류 | 파일 |
|---|---|
| **LIVE (전부)** | `cq/CQ01~CQ27.rq`(27개, 연속·중복 0) · `shapes/graph/*.ttl`(완화 3개) · `shapes/delta/patent_delta_shape.ttl`(엄격 1개) |
| **고아/중복** | **없음.** 게이트가 디렉토리 glob 으로 로드하므로 폴더에 있으면 곧 LIVE |

---

## 4. 혼동 유발 파일 Top — "최종으로 착각하기 쉬운 것"

1. **`graph_v1_{famdedup,samsung,hynix}.ttl`** — G₁ 이 **아니다**. 강건성/분할본. 특히
   samsung/hynix 는 트리에서 mtime 이 가장 최신(07-17)이라 "가장 최신=정본"으로 오인하기 쉽다.
   **정본 G₁ 은 `graph_v1.ttl`.**
2. **`delta_v*.ttl`** — 전부 병합 *전* 입력. 독립 산출물 아님. 큰 용량에 속지 말 것.
3. **`archive/논문초안_v0.2_…md` · `archive/논문초안_v0.3_…md`** — v0.5 이전 폐기본.
   v0.2 는 4층 게이트 이전, v0.3 은 RQ3·절 번호 재편 이전이라 **절·표·그림 번호가 정본과 다르다.**
   **인용 금지.**
4. **`STATUS.md`·`SPEC-002`·`MANIFEST §1` 의 트리플 숫자** — 낡은 세대(§2 참조). 숫자는 §1 표.
5. **`candidates_report.md`** — 현행 동결 이전(07-13)의 탐색 목록. 최종 매핑 규칙 아님.
6. **grep 트리플 프록시** — 실제의 약 1/13. rdflib/MANIFEST §3 로만 셀 것.
7. **H2 전용 미병합 코퍼스** (`interim/patents_2005_2009.parquet`) — H1 의 after 를 움직이는
   함정. 어떤 그래프에도 병합하지 않는다(MANIFEST §2 경고).

---

## 5. 미해결 — 승인 필요한 후속 정합화 (이 문서는 아직 손대지 않음)

아래는 **데이터가 아니라 문서 메타의 정합화**다. G₀/G₁/G₂ 그래프·H1·H2 결론은 불변이다.

**2026-07-18 완료분** (문서 메타만 수정 · 그래프·통계 불변):
- [x] `STATUS.md` G₀/G₁ 서명표를 44,202 / 413,730 으로, CQ01/03 before 를 20/29 로 갱신 + 상단 배너
- [x] `SPEC-002` 서명(43,812·`23d07a1`) → 44,202·`edb8ae4` 로 갱신 + 배너
- [x] `SPEC-003` 배너 (CQ06 58·C₀ 20 정본 링크; 본문 옛값은 역사 기록으로 보존)
- [x] `SPEC-004` 배너 (CQ 22 → 27·재동결 44,202)
- [x] `MANIFEST.md §1` 이력표에 `edb8ae4`·44,202 재동결 행 추가 + 역사 서명 배너
- [x] `PLAN-011`·`PLAN-012` 완료 기록형 스텁 작성 (plans/ 001–016 연속 복원)
- [x] `data/README.md`·`data/processed/README.md` 신설 (최종 지도 + 갱신 규율 + 파일별 판정)

**대기 (별도 승인 필요):**
- [ ] `data/processed/` 의 INTERMEDIATE 파일을 하위 디렉토리로 **물리 분리** — **파일명이
      `config.py`·`delta.py`·`Makefile`·논문에 배선돼 있어 코드 경로 수정 + 파이프라인 재생성
      검증을 동반한다.** 설계안은 이 세션의 보고 참조.
