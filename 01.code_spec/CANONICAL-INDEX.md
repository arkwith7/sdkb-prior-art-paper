# 정본 인덱스 (CANONICAL INDEX) — v0.9

> **이 문서의 목적.** "지금 무엇이 정본인가"를 v0.9 기조(선행기술 검색 주 태스크 + T-gate)로 확정한다.
> 숫자가 문서마다 다를 때는 **§1 서명표가 최종 판정**이다. 라벨(RQ·H·C·S)이 문서마다 다를 때는
> **§0.1 라벨 규약**이 판정한다. v0.5 구본 인덱스는 [archive/CANONICAL-INDEX-v05.md](archive/CANONICAL-INDEX-v05.md)
> (인용 금지).
>
> *작성 근거: 정본 원고 [paper/논문_v0_9_SDKB_통합초안.md] · [RECONCILIATION-v09.md](RECONCILIATION-v09.md) ·
> [specs/SPEC-006](specs/SPEC-006-g0-asbuilt-inventory.md)(G₀ as-built)·[SPEC-007](specs/SPEC-007-ir-corpus-asbuilt.md)(IR 코퍼스 as-built) ·
> 메모리 `pivot-v09-retrieval-primary-task`·`spike-retrieval-feasibility-passed`. §1 서명은 온디스크 실측(MANIFEST §3).*

---

## 0. 한눈에 — 지금 무엇이 정본인가

| 축 | 정본 (FINAL) | 위치 |
|---|---|---|
| **논문** | `논문_v0_9_SDKB_통합초안.md` (§1.4=H1–H5·§1.5=기여 3 동결) | `paper/` |
| **작업 규약** | `CLAUDE.md` (v0.9 기조 · C1/C2/C3·T-gate) | 루트 |
| **정합 원장(전파 추적)** | `RECONCILIATION-v09.md` (라벨 사전·SoT 델타·배치 B0–B8) | `01.code_spec/` |
| **baseline 그래프 G₀** | `graph_v0.ttl` (105,588 트리플) | `data/processed/` (gitignore — MANIFEST §3 이 서명) |
| **보강 그래프 G₁** | `graph_v1.ttl` (924,814) | `data/processed/` |
| **소부장 그래프 G₂** | `graph_v2.ttl` (490,529) | `data/processed/` |
| **얼린 상류 스냅샷** | `data/external/sdkb/` (SDKB `d578bf3`) | git-tracked · sha256 in `PROVENANCE.json` |
| **IR 벤치마크 코퍼스** | 질의(거절특허 1,000)·후보 코퍼스(G1/G2 ~40k)·qrel 정답 2,321 — as-built [SPEC-007](specs/SPEC-007-ir-corpus-asbuilt.md) | `data/` (원문 gitignore) |
| **검증 게이트 (L0–L3)** | `queries/cq/*.rq` **28개** · `queries/shapes/graph/` 5 + `shapes/delta/` 1 | 전부 LIVE · 고아 0 |
| **T-gate (T1·T2·T3)** | 계약 명세 = [SPEC-001](specs/SPEC-001-validation-gate.md) §T-gate — **미구현** | (예정) `validate/t{1,2,3}_*.py` |
| **계약(SPEC)** | `SPEC-001~007` — §0.2 목록 | `01.code_spec/specs/` (숫자는 §1 우선) |
| **진행 현황** | `STATUS.md` (v0.9) | `01.code_spec/` (서명 숫자는 §1 우선) |
| **논문 그림·표** | **C2 전량 산출 완료(2026-07-28)** — 표 `paper/tables/ir_{performance,subgroup,increment,crosslingual}_{dev,test}.md` · 그림 2–5 `paper/figures/ir_{increment,metrics,ablation,subgroup}.svg` (`make tables && make figures`). **§6.2f 교차언어 진단표 추가(2026-07-28 · PLAN-019 W1 · `make crosslingual`).** **C3(§6.5·§6.6)은 미산출.** 구 S-시리즈는 `paper/archive/`(인용 금지) | `viz/figures.py` · `analysis/{results_table,subgroup,increment,ablation,lang_recall}.py` |

---

## 0.1 라벨 규약 — RQ·H·C·S (v0.9)

> **전체 사전은 [RECONCILIATION-v09.md](RECONCILIATION-v09.md) §1. 이 절은 요약이다.**

| 라벨 | v0.9 의미 | 주장 | 상태 |
|---|---|---|---|
| **C1 · 자원** | 공유 T-Box가 세 태스크를 표현 (정합성·완전성 검증 데이터셋) | 기여 1 | 지지 (관측) |
| **C3 · 진화안전** | **다중 태스크 작동성** — T-gate로 세 태스크가 상호 간섭 없이 작동 | 기여 2 | 미측정 |
| **C2 · 핵심증명** | 선행기술 검색에서 온톨로지 보강이 텍스트 기준선을 (조건부) 개선 | 기여 3 | **부분 지지 — 주 지표 한정** (원고 반영 완료) |
| **RQ1 / H1·H2** | 검증 게이트 (H1 게이트 판별력 · H2 승인 안전성) | C3 | 미측정 |
| **RQ2 / H3** | 검색 유용성 (하이브리드 효과 · 조건부 통합) | C2 | **부분 지지** (R@100 유의 · nDCG 미개선 · 조건부 절 반증) |
| **RQ3 / H4·H5** | 계층 기여(H4) · 특이성 음성대조군(H5) | C2 | **H4 기각 · H5 기각 → 태스크 결합 발견** |
| **S1 / S2 / S3** | 구 커버리지 H1 / 구 시계열 H2·RQ2 / 구 이식성 RQ3 → **C1의 2차 재사용 증거** | C1 (2차) | 지지 (구본) |

- **확증 가설은 H1–H5 다섯 개**다. 탐색적 강등: 운용 효율·법적 맥락·의미 도달성.
- **"H1"은 문맥 없이 쓰지 않는다.** v0.9 H1(게이트 판별력)과 구 H1(커버리지→S1)이 충돌한다 — 구 라벨은
  `S1(구 H1)` 형식으로 쓴다. 코드·문서에 남은 구 라벨은 배치 B4에서 S-시리즈로 재라벨됐다.

## 0.2 SPEC 인벤토리 (계약)

| SPEC | 책임 | v0.9 상태 |
|---|---|---|
| [SPEC-001](specs/SPEC-001-validation-gate.md) | 검증 게이트 L0–L3 **+ T-gate**(T1·T2·T3) | L0–L3 LIVE · T-gate 명세(미구현) |
| [SPEC-002](specs/SPEC-002-baseline-g0.md) | baseline G₀ | 유효 · SPEC-006이 as-built 대체 |
| [SPEC-003](specs/SPEC-003-competency-questions.md) | 역량질문(CQ) — K=8 설계 근거 | 역사 · 현행 28개는 SPEC-004/§1 |
| [SPEC-004](specs/SPEC-004-cq-derivation-protocol.md) | CQ 도출 프로토콜·어휘 검증 (**측정 운용**) | 유효 (게이트 아님) |
| [SPEC-005](specs/SPEC-005-tbox-ontology-design.md) | T-Box 설계서 (태스크 3종) | 유효 (v0.9 어휘 근거) |
| [SPEC-006](specs/SPEC-006-g0-asbuilt-inventory.md) | G₀ as-built 데이터 딕셔너리 | **정본** (v0.9 신규) |
| [SPEC-007](specs/SPEC-007-ir-corpus-asbuilt.md) | IR 코퍼스 as-built | **정본** (v0.9 신규 · C2 입력) |

---

## 1. 권위 있는 서명 숫자 — SINGLE SOURCE OF TRUTH

**이 표가 최종이다.** 온디스크 실측(rdflib) = MANIFEST §3 값이다. (v0.5 구본과 **동일한 동결 사실** —
패러다임 전환은 라벨·서술을 바꿨을 뿐 그래프 서명은 바꾸지 않았다.)

| 항목 | G₀ | G₁ | G₂ (소부장) |
|---|---:|---:|---:|
| **트리플 (정본)** | **105,588** | **924,814** | **490,529** |
| 커버된 공정 / 49 | 20 | 26 | 26 |
| 특허 (병합) | 1,000 (SIRP 거절) | +24,179 델타 (총 25,179) | +12,339 델타 (총 13,339) |
| 선행기술 정답지 (`ont:CitedPatent`) | 3,034 (심사관 인용 + 개념링크) | 상속 | 상속 |
| Process 11 / SubProcess 38 · Device 34 | ✓ | | |
| IPCSymbol | 810 | 2,924 | 2,914 |
| FailureMode (문제층) | 25 | 55 | 25 |
| 청구항 축 | — | claimText 371,267 · abstractText 24,179 · claimCount 24,178 | claimText 161,184 |
| 문제층 | — | exhibitsFailureMode 2,816 · relatedToTopic 3,236 | — |
| 출원인(Organization) / 벤더 | 351 / 340 | | 188사(장비 93·재료 50·부분품 45) |
| 게이트 | L1(완화)·L2 consistent·L3 CQ 27/28 | L1·L2·L3 CQ 28/28 | L1·L2 consistent·L3 CQ 28/28 |
| 그래프 커밋(상류) | SDKB `d578bf3` | 〃 위 델타 | 〃 위 델타 |

> **동결 규율.** §1 서명은 CLAUDE.md §0 "동결된 사실"이며 예고 없이 바뀌면 회귀 테스트가 차단한다.
> `scripts/check_signatures.py`가 이 표의 `**트리플 (정본)**` 행을 파싱해 TARGETS 문서의 표류를 잡는다.

> **재산출 이력 (2026-07-23, 커밋 `3429d66`) <!-- sig-history -->.** 미반영 SDKB 온톨로지 전량 반영으로
> 세 그래프를 재조립했다 — 선행기술 ABox(`ont:CitedPatent` 3,034)·상용화·RBV 편입. 구 49,307·868,669·
> 434,342 → 현재 값. **C₀ 20/49 불변** (선행기술은 명시 타입이 `ont:Patent`가 아니라 CQ01이 안 셈)·
> 델타특허 24,179/12,339 불변. **선행기술조사 정답지 도달성 0%→95.3%(노드)** — 이 재빌드가 v0.9
> 검색 벤치마크를 비공허하게 만든 전제다(메모리 `spike-retrieval-feasibility-passed`). 상세 서사는
> [archive/CANONICAL-INDEX-v05.md](archive/CANONICAL-INDEX-v05.md) §1.

> **분모 규율 (CLAUDE.md §0).** 2,534(인용 엣지) ≠ **2,321(고유 정답)** ≠ 2,211(노드도달) ≠ 584(판단연결).
> 혼용 금지. 질의밀도(회수가능 정답 ≥1) = 97.6%. IR 질의/qrel 상세는 [SPEC-007](specs/SPEC-007-ir-corpus-asbuilt.md).

> **grep으로 트리플을 세지 말 것.** `grep -c ' \.$'` 프록시는 Turtle 축약 때문에 약 13배 과소계상한다.
> 트리플 수는 MANIFEST §3 또는 rdflib 파싱으로만 인용한다.

---

## 2. 태스크와 증거 지도 — C1/C2/C3가 무엇으로 지지되는가

| 주장 | 논문 | 증거 산출물 | 상태 |
|---|---|---|---|
| **C1 자원** | §3·§6.1 | 도달성 사다리·CQ 28(측정)·SHACL(L1)·어휘 검증 커버리지 | **지지** (관측 사실) |
| **C3 진화안전** | §4·§6 (RQ1·H1·H2) | 결함주입 검출 매트릭스·McNemar·음성대조군·T-gate 통과 | **미측정** (T-gate 미구현) |
| **C2 핵심증명** | §5–6 (RQ2·H3 · RQ3·H4·H5) | Recall@100·nDCG@20(이진)·MRR·bpref·ablation A1–A8·부트스트랩·하위집단 4축 | **부분 지지 — 주 지표 한정** (2026-07-28 산출·원고 반영). H3 R@100 유의·**nDCG 미개선** · H4 기각 · H5 기각→결합 발견 |

- **S-시리즈(C1 2차 재사용).** 구 커버리지(S1)·시계열(S2)·이식성(S3) 산출물은 자원 형성 타당성의
  방증이며 T-gate T3의 회귀 감시 대상(em·tf·core 스위트)이다. 그림·표는 `paper/archive/`, 상세 서사는
  `archive/STATUS-v05.md`. **인용은 "S1(구 H1)" 형식**으로만.
- **C2 는 채워졌고 C3 는 아직 비어 있다.** IR 하네스(Pyserini BM25 nori + FAISS flat Dense + RRF ·
  Titan Embed v2)는 구축·확증 완료다. **단 질의 번역은 구현되지 않았다** — CLAUDE.md 동결 사실의
  "Haiku 4.5 질의 번역"은 아직 코드에 없으며, 교차언어 하위집단 해석의 교란으로 원고 §9.1 에 명시했다.
  C3(§6.5 결함주입·§6.6 CQ 추이)는 M5 T-gate 구현 후 채워진다 — 지금 비어 있는 것이 정상이다.
- **C2 산출물 재생성:** `make tables SPLIT=test && make figures`. 새 검색 없이 동결 run·설정을
  재평가한다. 사전등록 동결값: ε=0.02 · δ=0.05 · **F11 low-overlap 임계 = dev Q1 0.0079**
  (`data/processed/ir/overlap_threshold.json`) · P0★ α=0.75·w=(0.5,0,0.5) · P1 τ=0.7·w=(0.25,0,0.25,0.5).

---

## 3. 디렉토리별 분류 요약

### `paper/`
| 분류 | 파일 |
|---|---|
| **FINAL** | `논문_v0_9_SDKB_통합초안.md` (정본 · 유일) |
| **ARCHIVED (인용 금지)** | `archive/논문_v0.7_SDKB.md` · `archive/논문_v0.5_SDKB.md` · `archive/논문초안_v0.2·v0.3` |
| **GENERATED — LIVE** | `figures/{cq_report,vocab_coverage}_*.md` (CQ·어휘 측정 리포트) |
| **ARCHIVED 그림·표 (S-시리즈)** | `archive/figures/*.svg`(fig1·4·6·7·8·10·11 등) · `archive/tables/*.md`(h1·h2·robustness) — 구 커버리지/시계열/이식성, **인용 금지** |
| **v0.9 그림·표** | **미산출** — C2/C3 검색결과·결함매트릭스는 IR 하네스 후 생성 |
| **빈 디렉토리 (함정)** | `manuscript/`(.gitkeep 뿐 — 진짜 원고는 `paper/논문_v0_9…md`) · `tables/`(현재 빔) |

### `01.code_spec/`
| 분류 | 파일 |
|---|---|
| **PROGRESS (정본)** | `STATUS.md`(v0.9) · `RECONCILIATION-v09.md`(전파 원장) |
| **CANONICAL (계약)** | `specs/SPEC-001~007` (§0.2) |
| **REFERENCE** | `README.md` · `GLOSSARY-{ONTOLOGY,SEMICONDUCTOR,STATISTICS}.md` · `REF-001`(IP-R&D) · `TOOLING.md` |
| **PLAN — 살아 있는 계획 (7건)** | `plans/PLAN-017`(IR 벤치마크 데이터셋) · `PLAN-018`(검색·T-gate 하네스 사전등록 🟢) · `PLAN-019`(v0.9 완성도 원장) · `PLAN-025`(H1‴ 확증 사전등록 🔒 — C층이 문면 재사용) · `PLAN-027`(강한 밀집 기준선 — PLAN-029 B층에 흡수) · `PLAN-029`(재실험 로드맵 🛑) · `PLAN-031`(B층 수집 사전등록 🛑) |
| **ARCHIVED (인용 금지)** | `archive/CANONICAL-INDEX-v05.md` · `archive/STATUS-v05.md` · `AUDIT-2026-07-18.md`(구 패러다임 감사 배너) · **종결 PLAN 22건 → 아래 §3.1** |

#### 3.1 종결 PLAN — 한 줄 요약 (2026-07-30 `plans/` → `archive/` 이동)

원문은 `01.code_spec/archive/`에 그대로 있다(사전등록 증거·커밋 해시 불변). **인용 금지 — 결론만 여기서 읽는다.**

**구 패러다임(v0.5/v0.7) · S-시리즈로 재라벨됨 — C1 자원 형성의 2차 증거**

| PLAN | 한 줄 결론 |
|---|---|
| 001 IPC/CPC→개념 룰 H10 보강 | 매핑 룰 확장. 구 H10 계열 자원 형성 |
| 002 삼성·SK 특허 수집 | G₁ 후보 모집단의 원천 수집 절차 |
| 003 Device→Process 브리지·DART 시장층 | 소자/시장 축 신설 — 현 Device 축의 기원 |
| 004 신기술 인식 레이어 | 별칭·조합 정의. 단일 계층으로 GAA·HBM을 못 담음을 실증 |
| 005 S1(구 H1) 커버리지 검정 | 공정단계별 개념 커버리지 — 커버리지 패러다임의 주검정 |
| 006·007 S2(구 H2) 사례 사전등록·vintage 분류 | 조기탐지 시차 검정 설계·당시분류 재검정 |
| 008·009 분류체계 독립 개념·좌측절단 교정 | 좌측절단 보정 후 S2 재검정 |
| 010 S2′ 명칭 기준선 | 시점 유효 대조군 재설정 |
| 011 패밀리 중복 제거 | KR 패밀리당 평균 1.00 — 중복 영향 없음 |
| 012 출원인별 분리 재검정 | §4.5.2 강건성 |
| 013 온톨로지 품질검증 | T-Box·A-Box·SHACL·CQ 확장 — 현 L0–L3 게이트의 기원 |
| 014 CQ 도출 프로토콜·이식성 | SPEC-004의 근거. S3(구 RQ3) |
| 015 규제·컴플라이언스 축 | 수출통제 인스턴스 적재(B 최소 실증) |
| 016 S2 재설계 — 소자 모집단 리드타임 | A-both 설계 + DART 외부 준거 |

**v0.9 W-시리즈 · PLAN-019 §5가 상위 원장, PLAN-025가 최종 확증으로 대체**

| PLAN | 한 줄 결론 |
|---|---|
| 020 W4 결함주입 설계 동결 | **H1 기각** — 게이트 판별력 미달 |
| 021 W4b CQ 판정 세분화 | **H1′ 기각 · 원인 규명**(CQ 28개 중 26개가 존재검사 → D-08). 부수: G₀에 완전중복 `Problem` 실재 |
| 022 N5c L3–T3 검출 표면 분리 | **H1″ 탐색적 지지** · 동결 `44f8022`. `L3=pa ⊥ T3={em,tf,core}` 정의는 PLAN-025가 그대로 승계 |
| 023 N5d 선행기술 CQ 청구항 수준 확장 | 완료 · 동결 `8b55611`. C1 표현범위 확장 |
| 024 N12 확증분할 T-gate 판정·부록 B 매트릭스 | 완료 · **부록 B는 §6.3 수치의 복사본을 두지 않는다**(단일 원천 규율) |
| 028 원고–산출물 정합 | 완료(2026-07-28 이전 아카이브) |

### `data/`
| 분류 | 파일 |
|---|---|
| **FINAL — 그래프** | `graph_v0.ttl`(G₀) · `graph_v1.ttl`(G₁) · `graph_v2.ttl`(G₂) |
| **FINAL — IR 코퍼스** | 질의·후보 코퍼스·qrel (as-built [SPEC-007](specs/SPEC-007-ir-corpus-asbuilt.md)) · 임베딩(Titan) |
| **FINAL — 얼린 스냅샷** | `data/external/sdkb/` (sha256 in PROVENANCE) · `data/samples/mini_graph.ttl`(게이트 픽스처) |
| **정의서** | `DATASET-CARD.md`(G₀·G₁·G₂ 정체성 · 서명은 §1 종속) |
| **HISTORICAL — raw (gitignore)** | `data/raw/…` · `data/interim/*.parquet` · 특허 전문(claim/abstract) — 재배포 금지 |

### `queries/`
| 분류 | 파일 |
|---|---|
| **LIVE (전부)** | `cq/CQ01~CQ28.rq`(**28개** · 스위트 pa·em·tf·core) · `shapes/graph/*.ttl`(완화 5) · `shapes/delta/patent_delta_shape.ttl`(엄격 1) |
| **고아/중복** | 없음 (게이트가 디렉토리 glob 으로 로드) |

---

## 4. 혼동 유발 파일 Top — "정본으로 착각하기 쉬운 것"

1. **`paper/archive/논문_v0.5·v0.7`** — 구 정본. 절·표·그림 번호·RQ/H 라벨이 v0.9와 다르다. **인용 금지.**
2. **`paper/archive/figures/*.svg`·`archive/tables/*.md`** — 구 커버리지/시계열/이식성 그림·표(S-시리즈).
   v0.9 본문 그림이 아니다.
3. **`archive/CANONICAL-INDEX-v05.md`·`archive/STATUS-v05.md`** — 구 중재자. 서명(§1)만 승계됐고 서술은 폐기.
4. **`graph_v1_{famdedup,samsung,hynix}.ttl`** — G₁이 아니다. 강건성/분할본(S1/S2 근거). 정본 G₁은 `graph_v1.ttl`.
5. **`delta_v*.ttl`** — 병합 *전* 입력. 독립 산출물 아님.
6. **구 라벨 "H1"·"H2"** — 코드·구 PLAN에 남은 것은 **S1·S2**(구 커버리지·시계열)다. v0.9 H1–H5와 다르다.
7. **grep 트리플 프록시** — 실제의 약 1/13. rdflib/MANIFEST §3 로만 셀 것.

---

## 5. 미해결 · 후속 정합화 (배치 추적 = RECONCILIATION-v09 §3)

전파 배치 진행: **B0·B1·B2·B4 완료** · **B5 = 이 문서·STATUS 재생(진행 중)** · B6(GLOSSARY·README·
check_signatures TARGETS) · B7(코드 S-시리즈 재라벨) · B8(전체 sig-check).

- [ ] **B6**: `scripts/check_signatures.py` TARGETS에 v0.9 정본 원고 추가 (현재 `[warn] 검사할 원고 없음` —
      구 원고 아카이브 후 목록 미갱신 · §1 서명 보호 복원). GLOSSARY·README·REF-001 용어 정합.
- [ ] **B7**: 코드 모듈·Makefile 타깃·산출 파일명 S-시리즈 재라벨 (`h1_cli→s1_*` 등 · 테스트 동반).
- [ ] **IR 하네스 구축** (PLAN-017 후속): C2/C3 산출물 생성 — 이 인덱스 §0·§3의 "미산출" 해소.
