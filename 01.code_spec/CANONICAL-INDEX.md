# 정본 인덱스 (CANONICAL INDEX) — v0.9

> **이 문서의 목적.** "지금 무엇이 정본인가"를 v0.9 기조(선행기술 검색 주 태스크 + T-gate)로 확정한다.
> 숫자가 문서마다 다를 때는 **§1 서명표가 최종 판정**이다. 라벨(RQ·H·C·S)이 문서마다 다를 때는
> **§0.1 라벨 규약**이 판정한다. v0.5 구본 인덱스는 [archive/CANONICAL-INDEX-v05.md](archive/CANONICAL-INDEX-v05.md)
> (인용 금지).
>
> **개정 (2026-07-31 · 정본 회귀 반영).** v1.0(영문 투고본)·v1.1(국문 정본)은 **`paper/archive/`로
> 내려갔고 인용 금지**이며, 작업 정본은 다시 [v0.9 통합초안](../paper/논문_v0_9_SDKB_통합초안.md)이다
> (CLAUDE.md 머리말 · [PLAN-029](archive/PLAN-029-post-remediation-reexperiment.md)). 이 개정으로
> 바로잡은 것: ① **T-gate·C3 산출물은 "미구현/미산출"이 아니라 구현·산출 완료** ② **기여는 3개가
> 아니라 4개** ③ **C0(상류 환류) 축 신설** — `upstream/` 대장·CR 7건이 정본 인덱스에 없었다
> ④ **G₁·G₂는 "세대"가 아니라 후보 모집단**(D-12 실측) ⑤ C2/H5 판정 문구를 CLAUDE.md §0에 정렬.
>
> *작성 근거: 정본 원고 [paper/논문_v0_9_SDKB_통합초안.md] · [RECONCILIATION-v09.md](RECONCILIATION-v09.md) ·
> [specs/SPEC-006](specs/SPEC-006-g0-asbuilt-inventory.md)(G₀ as-built)·[SPEC-007](specs/SPEC-007-ir-corpus-asbuilt.md)(IR 코퍼스 as-built) ·
> [upstream/DEFECT-LEDGER.md](../upstream/DEFECT-LEDGER.md) · 메모리 `pivot-v09-retrieval-primary-task`.
> §1 서명은 온디스크 실측(MANIFEST §3).*

---

## 0. 한눈에 — 지금 무엇이 정본인가

| 축 | 정본 (FINAL) | 위치 |
|---|---|---|
| **논문** | `논문_v0_9_SDKB_통합초안.md` — **v2.0 재구성 1단계 반영(2026-08-01 · PLAN-033)**: §1.4 = **확증가설 H3·H5 두 개** · 기여 **2개** · H1·H2·H4 는 판정 불변·지위 강등 · §7 흡수로 장 번호 8–11 → 7–10 | `paper/` |
| **작업 규약** | `CLAUDE.md` (v0.9 기조 · C0/C1/C2/C3·T-gate) | 루트 |
| **상류 환류 (C0)** | `DEFECT-LEDGER.md`(결함 D-01~D-30) · **살아 있는 CR 6건**(CR-001A·002·003·005·006·009) · `archive/`(종료 6건 — CR-004R·007·008·**011**·**012**·013 · 재송부 금지) · `HANDOFF-QUEUE.md`(송부 순서 · **상류 대기 0**) | `upstream/` |
| **정합 원장(전파 추적)** | `RECONCILIATION-v09.md` (라벨 사전·SoT 델타·배치 B0–B8 완료) | `01.code_spec/` |
| **baseline 그래프 G₀** | `graph_v0.ttl` (**115,095** 트리플 · 구 105,713 · 105,588) — 게이트 대상 | `data/processed/` (gitignore — MANIFEST §3 이 서명) |
| **후보 모집단 G₁** | `graph_v1.ttl` (924,814) — **세대가 아니라 방해문서 풀**(D-12) · ⚠ 구 G₀ 위 조립 | `data/processed/` |
| **후보 모집단 G₂** | `graph_v2.ttl` (490,529) — 〃 · ⚠ 구 G₀ 위 조립 | `data/processed/` |
| **얼린 상류 스냅샷** | `data/external/sdkb/` (SDKB `2839afb` · 스냅샷 서명 `b98ad787d1fe`) | git-tracked · sha256 in `PROVENANCE.json` |
| **IR 벤치마크 코퍼스** | 질의(거절특허 1,000)·후보 코퍼스(G1/G2 ~40k)·qrel 정답 2,321 — as-built [SPEC-007](specs/SPEC-007-ir-corpus-asbuilt.md) | `data/processed/ir/` (원문 gitignore) |
| **검증 게이트 (L0–L3)** | `queries/cq/*.rq` **28개** · `queries/shapes/graph/` 5 + `shapes/delta/` 1 | 전부 LIVE · 고아 0 |
| **T-gate (T1·T2·T3)** | 계약 = [SPEC-001](specs/SPEC-001-validation-gate.md) §T-gate · 구현 = `validate/{t1_noninferiority,t2_subgroup,t3_cross_task_cq,t_gate,leakage_check}.py` | **LIVE** (`make leakage`·`cq-freeze`·`tgate` · dev·확증분할 실행 완료) |
| **계약(SPEC)** | `SPEC-001·002·004~008` — §0.2 목록 | `01.code_spec/specs/` (숫자는 §1 우선) |
| **진행 현황** | `STATUS.md` (v0.9) | `01.code_spec/` (서명 숫자는 §1 우선) |
| **논문 그림·표** | **C2·C3 전량 산출 완료(2026-07-28)** — C2 표 `paper/tables/ir_{performance,subgroup,increment,crosslingual}_{dev,test}.md` · 그림 2–5 `paper/figures/ir_{increment,metrics,ablation,subgroup}.svg` · **C3 표 `fault_matrix{,_v2,_v3,_v4}.md`·`cq_generations.md`** (`make tables && make figures && make faults`). 구 S-시리즈는 `paper/archive/`(인용 금지) | `viz/figures.py` · `analysis/{results_table,subgroup,increment,ablation,lang_recall}.py` · `validate/fault_inject.py` |

---

## 0.1 라벨 규약 — RQ·H·C·S (v0.9)

> **전체 사전은 [RECONCILIATION-v09.md](RECONCILIATION-v09.md) §1. 이 절은 요약이다.**

| 라벨 | v0.9 의미 | 주장 | 상태 |
|---|---|---|---|
| **C0 · 상류 환류** | 실험이 식별한 SDKB 결함 → 검증기준을 갖춘 상류 변경 요구 | 논문 밖 (제품 목적) | **상시** — D-01~D-16 등재 · CR 7건 작성 |
| **C1 · 자원** | 공유 T-Box가 세 태스크를 표현 (정합성·완전성 검증 데이터셋) | 기여 | 지지 (관측) |
| **C3 · 진화안전** | **다중 태스크 작동성** — T-gate로 세 태스크가 상호 간섭 없이 작동 | 기여 | **부분 지지** — H1‴ 홀드아웃 범위 내 지지 · **H2 미검정**(구조적 · CLAUDE.md §0 경계표) |
| **C2 · 핵심증명** | 선행기술 검색에서 온톨로지 보강이 텍스트 기준선을 (조건부) 개선 | 기여 | **부분 지지 — 깊은 회수 한정** (원고 반영 완료) |
| **RQ1 / H1·H2** | 검증 게이트 (H1 게이트 판별력 · H2 승인 안전성) | C3 | **H1‴ 지지**(홀드아웃 72 · T3 단독검출 12/45 · p=.0001 · 위양성 0/27) · **H2 미검정** |
| **RQ2 / H3** | 검색 유용성 (하이브리드 효과 · 조건부 통합) | C2 | **부분 지지** (부차 P1 R@100 +0.0534 유의 · **주 구성 P0★ 비유의** p0.181 · nDCG 미개선 · 조건부 절 반증) |
| **RQ3 / H4·H5** | 계층 기여(H4) · 특이성 음성대조군(H5) | C2 | **H4 기각 · H5 기각 → 경험적 교차 태스크 의존성**(인과 표현 아님) |
| **RQ4 / 계층 독립성** | 태스크 전용 계층이 T-Box 공유 시 실제로 독립 행동하는가 | C2·C3 경계 | H5의 음성 대조군 실패가 답한다 |
| **S1 / S2 / S3** | 구 커버리지 H1 / 구 시계열 H2·RQ2 / 구 이식성 RQ3 → **C1의 2차 재사용 증거** | C1 (2차) | 지지 (구본) |

- **확증 가설은 H1–H5 다섯 개**다. 탐색적 강등: 운용 효율·법적 맥락·의미 도달성·**교차언어 진단**.
- **H2를 "지지"로 쓰지 않는다.** P1 대 B3는 시스템 델타 비교이고 H2는 동일 파이프라인 O 대 O′를
  요구한다. **G0·G1·G2의 T-Box는 완전히 동일**(D-12)하므로 자격 있는 델타가 **존재한 적이 없다**.
- **"H1"은 문맥 없이 쓰지 않는다.** v0.9 H1(게이트 판별력)과 구 H1(커버리지→S1)이 충돌한다 — 구 라벨은
  `S1(구 H1)` 형식으로 쓴다. 코드·문서에 남은 구 라벨은 배치 B4에서 S-시리즈로 재라벨됐다.

## 0.2 SPEC 인벤토리 (계약)

| SPEC | 책임 | v0.9 상태 |
|---|---|---|
| [SPEC-001](specs/SPEC-001-validation-gate.md) | 검증 게이트 L0–L3 **+ T-gate**(T1·T2·T3) | **전부 LIVE** (T-gate 구현·실행 완료) |
| [SPEC-002](specs/SPEC-002-baseline-g0.md) | baseline G₀ | 유효 · SPEC-006이 as-built 대체 |
| ~~SPEC-003~~ | 역량질문(CQ) — K=8 설계 근거 | **아카이브됨** → [archive/SPEC-003](archive/SPEC-003-competency-questions.md) (구 라벨·2세대 낡은 수치 · 인용 금지). 현행 28개는 SPEC-004/§1 |
| [SPEC-004](specs/SPEC-004-cq-derivation-protocol.md) | CQ 도출 프로토콜·어휘 검증 (**측정 운용**) | 유효 (게이트 아님) |
| [SPEC-005](specs/SPEC-005-tbox-ontology-design.md) | T-Box 설계서 (태스크 3종) | 유효 (v0.9 어휘 근거) |
| [SPEC-006](specs/SPEC-006-g0-asbuilt-inventory.md) | G₀ as-built 데이터 딕셔너리 | **정본** (v0.9 신규) |
| [SPEC-007](specs/SPEC-007-ir-corpus-asbuilt.md) | IR 코퍼스 as-built | **정본** (v0.9 신규 · C2 입력) |
| [SPEC-008](specs/SPEC-008-nori-userdict-inventory.md) | nori 사용자사전 as-built (BM25 토큰화) | **정본** (v0.9 신규 · C2 전제) |

---

## 1. 권위 있는 서명 숫자 — SINGLE SOURCE OF TRUTH

**이 표가 최종이다.** 온디스크 실측(rdflib) = MANIFEST §3 값이다. (v0.5 구본과 **동일한 동결 사실** —
패러다임 전환은 라벨·서술을 바꿨을 뿐 그래프 서명은 바꾸지 않았다.)

> **⚠ 세대가 갈렸다 (2026-08-01 · 2026-08-05 갱신).** G₀ 는 상류 `39855bb` 스냅샷 위에서 **다시
> 재조립됐고**(105,713 → **115,095**), G₁·G₂ 는 **여전히 재조립하지 않았다** — 디스크의
> `graph_v1/v2.ttl` 은 2026-07-23 산출물이라 **두 세대 전의 G₀(105,588) 위에 얹혀 있다.** 아래
> G₁·G₂ 열은 그래서 *구 세대의 실측*이고, 새 세대의 값이 아니다. 재조립 전까지 G₁·G₂ 수치를
> "현행"으로 인용하지 않는다. 두 열에 델타를 더해 추정하는 것도 **금지**(§1-1 — 실행되지 않은 수치다).

| 항목 | G₀ | G₁ | G₂ (소부장) |
|---|---:|---:|---:|
| **세대** | 상류 `39855bb` (현행 · 구 `2839afb`) | 상류 `d578bf3` (**구**·미재조립) | 〃 |
| **트리플 (정본)** | **115,095** | **924,814** | **490,529** |
| 커버된 공정 | 20 / **50** | 26 / 49 (구) | 26 / 49 (구) |
| 특허 (병합) | 1,000 (SIRP 거절) | +24,179 델타 (총 25,179) | +12,339 델타 (총 13,339) |
| 선행기술 정답지 (`ont:CitedPatent`) | **3,513** (구 3,034 · CR-008 B층 +479) | 상속 | 상속 |
| Process **12** / SubProcess 38 · Device 34 | ✓ (구 Process 11 — 신규 `data:process/plasma_processing`) | | |
| IPCSymbol | **3,273** (구 810 · B층 문헌의 IPC 유입) | 2,924 | 2,914 |
| FailureMode (문제층) | 25 | 55 | 25 |
| 청구항 축 | — | claimText 371,267 · abstractText 24,179 · claimCount 24,178 | claimText 161,184 |
| 문제층 | — | exhibitsFailureMode 2,816 · relatedToTopic 3,236 | — |
| 출원인(Organization) / 벤더 | 351 / 340 | | 188사(장비 93·재료 50·부분품 45) |
| 게이트 | L1(완화)·L2 consistent·L3 CQ 27/28 | L1·L2·L3 CQ 28/28 | L1·L2 consistent·L3 CQ 28/28 |
| 그래프 커밋(상류) | SDKB **`39855bb`** (구 `2839afb`·`d578bf3`) | `d578bf3` 위 델타 (구) | 〃 (구) |

> **서명 이력 (G₀ · 최근 세대만).** 105,588(상류 `d578bf3` · 2026-07-23 재조립 · v0.9 §6 의 모든 결과가
> 이 세대 위에서 측정됐다) → 구 105,713(상류 `2839afb` · 2026-08-01 · CR-007 반영 · +125 ·
> **PLAN-035 두 팔의 O′ 팔**) → **115,095**(상류 `39855bb` · 2026-08-05 · CR-008 B층 +9,378 ·
> CR-004R T-Box 술어 +60 · IPC 심볼 중복 흡수 −56 · PLAN-040).
> 구 세대 값은 `scripts/check_signatures.py` 의 `HISTORICAL_SIGNATURES` 로 내렸다 — 문서에 '현재
> 값'으로 다시 나타나면 `make sig-check` 가 실패한다. 전체 이력은 `data/DATASET-CARD.md` §③.

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
| **C0 상류 환류** | 논문 밖 (제품 목적) | [DEFECT-LEDGER](../upstream/DEFECT-LEDGER.md) D-01~D-30 · CR 12건(종료 6 · 살아 있음 6) · HANDOFF-QUEUE | **상시** — **상류 대기 0(2026-08-08)** · 막는 것은 하류 코드(D-27 ① · PLAN-045) |
| **C1 자원** | §3·§6.1 | 도달성 사다리·CQ 28(측정)·SHACL(L1)·어휘 검증 커버리지 | **지지** (관측 사실) |
| **C3 진화안전** | §4·§6 (RQ1·H1·H2) | 결함주입 검출 매트릭스(`fault_matrix*.md`)·McNemar·음성대조군·T-gate 판정 | **부분 지지** — H1‴ 홀드아웃 72 확증(§6.5.4) · **H2 미검정**(자격 델타 부재 = D-12) |
| **C2 핵심증명** | §5–6 (RQ2·H3 · RQ3·H4·H5) | Recall@100·nDCG@20(이진)·MRR·bpref·ablation A1–A8·부트스트랩·하위집단 4축 | **부분 지지 — 깊은 회수 한정** (2026-07-28 산출·원고 반영). 부차 P1 R@100 +0.0534 유의 · **주 구성 비유의** · **nDCG 미개선** · H4 기각 · H5 기각 |

- **S-시리즈(C1 2차 재사용).** 구 커버리지(S1)·시계열(S2)·이식성(S3) 산출물은 자원 형성 타당성의
  방증이며 T-gate T3의 회귀 감시 대상(em·tf·core 스위트)이다. 그림·표는 `paper/archive/`, 상세 서사는
  `archive/STATUS-v05.md`. **인용은 "S1(구 H1)" 형식**으로만.
- **C2·C3 모두 산출은 끝났고, 남은 것은 자원 교정 후 재실험이다.** IR 하네스(Pyserini BM25 nori +
  FAISS flat Dense + RRF · Titan Embed v2)와 T-gate·결함주입은 구축·확증 완료다. **단 질의 번역은
  구현되지 않았다** — CLAUDE.md 동결 사실대로 `src/`에 번역 모듈이 없으며, 교차언어 실패의 세 원인
  중 하나로 원고 §6.2f·§9.1에 명시했다. 도입은 [PLAN-029](archive/PLAN-029-post-remediation-reexperiment.md) §3.2.
- **기각·무효과의 다수는 방법이 아니라 자원의 결함이다**(C0). `w_h=0`은 계층이 11트리플이라 생긴
  구조적 0(D-02), nDCG 악화는 개념 어휘 143개·문서당 1.55개라는 해상도의 귀결(D-01)이다.
  재평가는 상류 교정 후 **새 사전등록 아래 새로 검정**한다 — 기존 판정은 소급 수정하지 않는다.
- **C2 산출물 재생성:** `make tables SPLIT=test && make figures`. 새 검색 없이 동결 run·설정을
  재평가한다. 사전등록 동결값: ε=0.02 · δ=0.05 · **F11 low-overlap 임계 = dev Q1 0.0079**
  (`data/processed/ir/overlap_threshold.json`) · P0★ α=0.75·w=(0.5,0,0.5) · P1 τ=0.7·w=(0.25,0,0.25,0.5).

---

## 3. 디렉토리별 분류 요약

### `paper/`
| 분류 | 파일 |
|---|---|
| **FINAL** | `논문_v0_9_SDKB_통합초안.md` (정본 · 유일 · v2.0 재구성 1단계) |
| **SUPPLEMENTARY (공개 예정 · 인용 가능)** | `supplementary/S1-appendices-v09.md`(잘라낸 부록 A·C–H 전문) · `supplementary/S2-fault-injection-v09.md`(결함주입 4회차 재판정 §6.5–6.6 + 구 §6.3 가설 판정표 전문) |
| **ARCHIVED (인용 금지)** | `archive/논문_v1_1_SDKB_국문정본.md` · `archive/논문_v1_0_SDKB_AEI_투고초안.md` (**2026-07-29 강등** — "교정 전 상태"의 정직한 기록으로 보존) · `archive/논문_v0.7_SDKB.md` · `archive/논문_v0.5_SDKB.md` · `archive/논문초안_v0.2·v0.3` |
| **GENERATED — LIVE** | `figures/{cq_report,vocab_coverage}_*.md` (CQ·어휘 측정 리포트) |
| **ARCHIVED 그림·표 (S-시리즈)** | `archive/figures/*.svg`(fig1·4·6·7·8·10·11 등) · `archive/tables/*.md`(h1·h2·robustness) — 구 커버리지/시계열/이식성, **인용 금지** |
| **v0.9 그림·표 — 산출 완료** | `tables/ir_{performance,subgroup,increment,crosslingual}_{dev,test}.md`(C2 · 9건) · `tables/fault_matrix{,_v2,_v3,_v4}.md`·`tables/cq_generations.md`(C3 · 5건) · `figures/ir_{increment,metrics,ablation,subgroup}.svg`(**원고 그림 1–4** — v2.0 에서 mermaid 그림 1 제거로 한 칸씩 당겨졌다) |
| **빈 디렉토리 (함정)** | `manuscript/`(.gitkeep 뿐 — 진짜 원고는 `paper/논문_v0_9…md`) |

### `01.code_spec/`
| 분류 | 파일 |
|---|---|
| **PROGRESS (정본)** | `STATUS.md`(v0.9) · `RECONCILIATION-v09.md`(전파 원장 · B0–B8 완료) |
| **CANONICAL (계약)** | `specs/SPEC-001·002·004~008` (§0.2) |
| **REFERENCE** | `README.md` · `GLOSSARY-{ONTOLOGY,SEMICONDUCTOR,STATISTICS}.md` · `REF-001`(IP-R&D) · `TOOLING.md` |
| **REPORT (실험 기록)** | `reports/M4-{실험결과-1차,실험파이프라인-설명,검색유용성-서술전략,확증결과-원고반영}.md` — **v0.9 §6 산출의 근거 기록**. "원고 반영"은 v0.9 §6 반영을 뜻한다 |
| **PLAN — 살아 있는 계획 (5건 · 2026-08-08 2차 갱신)** | **`PLAN-045`(B층 질의 하류 소비 · **§1·§2 완료 · 🛑 3단계 설계** — 나머지 넷의 선결)** · `PLAN-031`(B층 수집 사전등록 **🔒 동결** · 봉인 미개봉) · `PLAN-033`(원고 재구성 — §6.2–6.4 재작성 미완) · `PLAN-038`(C2′ 전달 · 🛑 4단계 승인 대기) · `PLAN-040`(+ `PLAN-040-oprime-snapshot-signatures.json` · 판독 B 미개봉).<br>**2026-08-08 `archive/` 이동: `PLAN-018`**(실행 완료 — **F1–F18 동결은 여전히 현행 코드의 계약이다 · 인용은 `archive/` 경로로**) · **`PLAN-029`**(미승인 로드맵 · 실질을 PLAN-030/031/035/040/041/045 가 나눠 가짐 · **§3.2 질의 번역 · §3.3 질의 표현 비교는 아직 미승계**) |
| **ARCHIVED (인용 금지)** | `archive/CANONICAL-INDEX-v05.md` · `archive/STATUS-v05.md` · `archive/AUDIT-2026-07-18.md`(구 v0.5 원고 감사 · 2026-07-31 이동) · `archive/SPEC-003-competency-questions.md`(2026-07-31 이동) · `archive/CR-004-full-analysis-2026-07-30.md` · **종결 PLAN 33건 → 아래 §3.1** |

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

**2026-08-01 추가 이동 4건 — 실행이 끝났거나 대체된 계획**

| PLAN | 한 줄 결론 |
|---|---|
| 017 v0.9 IR 벤치마크 데이터셋 | **실행 완료** — M1 조립됨. as-built 정본은 [SPEC-007](specs/SPEC-007-ir-corpus-asbuilt.md)(코퍼스 40,552·qrel 2,321)이며 이 문서는 조립 전 설계 의도만 보존 |
| 019 v0.9 완성도·교차언어 원장 | **W-시리즈 종결** — W1·W3·W4·W4b·W4c·W5b·W6·W7·W9 완료 · W8 폐기 · W5 구조적 미성립(D-12) · **W2는 [PLAN-029](archive/PLAN-029-post-remediation-reexperiment.md) §3.2로 이월**. 현행 원장은 STATUS §2.0 |
| 025 W9 H1‴ 홀드아웃 확증 사전등록 | **판정 완료 — H1‴ 지지**(T3 단독검출 12/45·p=.0001·위양성 0/27). 사전등록 증거라 내용 불변 · C층이 판정 규칙 문면을 재사용(새 문서로 복사·출처 표기) |
| 027 강한 밀집 기준선 B2′ | **대체됨** — [PLAN-031](plans/PLAN-031-b-layer-second-confirmation-split.md) §5가 흡수하고 **B2′=`BAAI/bge-m3`** 로 동결(2026-07-31). test 198 재개봉 방식은 폐기라 이 문서는 실행되지 않는다 |

**2026-08-06 추가 이동 7건 — 실행이 끝난 계획**

> **이 일곱은 "인용 금지"가 아니다.** 030·035 는 사전등록 증거이고 037·039 는 §2.2 정지 게이트
> 기록이라, **판정의 출처로 인용해야 한다.** 금지되는 것은 **다시 실행하는 것**이다.

| PLAN | 한 줄 결론 |
|---|---|
| 030 A층 H2 사전등록 (스냅샷 O → O′) | **실행 종료 · H2 미검정** — 자격 있는 델타는 있었으나 하류에 적용기가 없어 코퍼스 서명이 바이트 단위로 불변이었다(D-19 · ΔR₁₀₀ 이 정의상 0). [PLAN-035](archive/PLAN-035-h2-linker-preregistration.md)가 대체 |
| 032 B층 파일럿 수집 드라이버 | **5단계 완주(2026-08-02)** — 200건 채택 · `r_family` 1.0000 · **봉인 미개봉**. 채택분이 전부 2005-01~02 출원이라 **A층 test 와 직접 비교하지 않는다**(§8.4) |
| 034 개념 적용기(linker) 요구정의 | **5단계 완료 · 코드 동결** — `corpus/concept_link.py` 신설로 **D-19 해소**. 부작용 하나를 등재해 두었다: 결함주입은 오염 그래프에서 개념 뷰를 다시 만들어 사전 링크가 빠진다(§4.4 · 다음 결함주입 전 선결) |
| 035 H2 사전등록 (적용기 경유 · O → O′) | **판정 완료 — H2 최초 실검정 · 기각.** 문서당 개념 1.545 → 3.779(2.4배)인데 **P1 ΔR₁₀₀ = −0.0293** [−0.0542, −0.0053] → **T1 실패 · Accept = 0**. 온톨로지 단독(B5)은 +0.0482 개선. 원인 미구분(D-23) · 원고 §8.1.2 · **I1(진보성의 본체)의 실측 근거** |
| 036 Effort@Recall · Candidate Reduction | **5단계 완료** — `make effort` · `analysis/effort.py` · `paper/tables/ir_effort_test.md`. 탐색적 기술통계로만 보고. **§12.3 경고는 아직 살아 있다 → 아래 §4 함정 9** |
| 037 §2.2 사전 점검 — I1 을 한계에서 본론으로 | **편집 완료** — 원고 **§7.5 신설**(층마다 지표가 어긋난 세 관측) · 구 §7.5 → §7.6. 판정·수치 불변, 삭제 줄 4 |
| 039 §2.2 사전 점검 — v2.0 논지 재구조화 | **편집 완료** — 제목·초록·§1·§2.6·§4.9(T4 설계)·**§6.7 신설**·§7.3·§10. §6.2–6.4 diff 0줄 · 판정 5건 불변 |

### `data/`
| 분류 | 파일 |
|---|---|
| **FINAL — 그래프** | `graph_v0.ttl`(G₀ · 게이트 대상) · `graph_v1.ttl`·`graph_v2.ttl`(**후보 모집단** — D-12) |
| **FINAL — IR 코퍼스 (v0.9 결과의 원천)** | `processed/ir/{ir_corpus_v09,qrel_examiner,qrel_test_sealed,concept_axis,feature_sidecar}.parquet` · `ir/runs/*.txt`(동결 run 19) · `ir/ir_{performance,subgroup,increment,crosslingual,ablation}_{dev,test}.csv` · `ir/overlap_threshold.json`(F11 동결) · as-built [SPEC-007](specs/SPEC-007-ir-corpus-asbuilt.md)·[SPEC-008](specs/SPEC-008-nori-userdict-inventory.md) |
| **FINAL — 얼린 스냅샷** | `data/external/sdkb/` (sha256 in PROVENANCE) · `data/samples/mini_graph.ttl`(게이트 픽스처) |
| **정의서** | `DATASET-CARD.md`(G₀·G₁·G₂ 정체성 · 서명은 §1 종속) · `MANIFEST.md`(이력·서명) · `README.md`(지도·갱신 규율) |
| **S-시리즈 (구 패러다임 · 인용 시 재라벨)** | `processed/{s1_*,h1_*,h2_*,robustness_*}` — `make s1`·`s2`·`robustness`·`by-applicant`로 재생성. **v0.9 결과가 아니다** |
| **HISTORICAL — raw (gitignore)** | `data/raw/…` · `data/interim/*.parquet` · 특허 전문(claim/abstract) — 재배포 금지 |

### `queries/`
| 분류 | 파일 |
|---|---|
| **LIVE (전부)** | `cq/CQ01~CQ28.rq`(**28개** · 스위트 pa·em·tf·core) · `shapes/graph/*.ttl`(완화 5) · `shapes/delta/patent_delta_shape.ttl`(엄격 1) |
| **고아/중복** | 없음 (게이트가 디렉토리 glob 으로 로드) |

---

## 4. 혼동 유발 파일 Top — "정본으로 착각하기 쉬운 것"

0. **`paper/archive/논문_v1_0`·`논문_v1_1`** — **가장 헷갈리는 함정.** 버전 번호가 v0.9보다 높아
   최신처럼 보이지만 2026-07-29에 강등됐다. 작업 정본은 **v0.9**다. v1.0/v1.1은 "상류 교정 **전**
   상태"의 기록으로만 인용한다(재실험 서사가 "결함을 찾아 고치고 다시 쟀다"이므로 고치기 전
   상태를 인용할 수 있어야 한다).
1. **`paper/archive/논문_v0.5·v0.7`** — 구 정본. 절·표·그림 번호·RQ/H 라벨이 v0.9와 다르다. **인용 금지.**
2. **`paper/archive/figures/*.svg`·`archive/tables/*.md`** — 구 커버리지/시계열/이식성 그림·표(S-시리즈).
   v0.9 본문 그림이 아니다.
3. **`archive/CANONICAL-INDEX-v05.md`·`archive/STATUS-v05.md`** — 구 중재자. 서명(§1)만 승계됐고 서술은 폐기.
4. **`graph_v1_{famdedup,samsung,hynix}.ttl`** — G₁이 아니다. 강건성/분할본(S1/S2 근거). 정본 G₁은 `graph_v1.ttl`.
5. **`delta_v*.ttl`** — 병합 *전* 입력. 독립 산출물 아님.
6. **구 라벨 "H1"·"H2"** — 코드·구 PLAN에 남은 것은 **S1·S2**(구 커버리지·시계열)다. v0.9 H1–H5와 다르다.
7. **grep 트리플 프록시** — 실제의 약 1/13. rdflib/MANIFEST §3 로만 셀 것.
8. **`paper/archive/regenerated/` 는 인용 대상이 아니다.** S-시리즈 타깃(`make s1`·`s2`·
   `robustness`·`by-applicant`·`ksia-strata`)과 `make figures` 의 구 패러다임 그림은 여기로 나간다
   (gitignore). **인용 대상은 동결본 `paper/archive/{tables,figures}/`** 이며, 둘은 값이 다를 수
   있다(실측: `robustness_family_dedup.md`·`h2_census.md`·fig7/8/8b/8c). 재생성물이 동결본과 다르면
   **그것이 정보**다 — 덮어쓰지 말고 차이를 보고한다.
   *(2026-07-31 교정 이전에는 이 타깃들이 v0.9 정본 `paper/{tables,figures}` 에 직접 써서 실제로
   S-시리즈 표 10건·그림 4건을 되살렸다. `config.ARCHIVE_TABLES`/`ARCHIVE_FIGURES` 신설로 차단.)*

9. **`make tables` 는 지금 돌리면 원고 §6.2 확증 표를 갈아 끼운다** (2026-08-06 승격 —
   출처 [archive/PLAN-036](archive/PLAN-036-effort-at-recall-requirements.md) §12.3 · 메모리
   `disk-resource-is-oprime-manuscript-is-o-arm`). **디스크의 자원은 O′ 이고 원고 §6.2 는 O 팔의
   판정 기록이다.** 재생성 전에 어느 팔인지 확인한다. 선택지는 둘뿐 — ⓐ `make vendor` 로 O 를
   복원한 뒤에만 재생성(**권고**) · ⓑ 원고를 O′ 로 이전(= 재측정이 아니라 **새 실험** · §2.1 전체).
10. **`data/processed/tgate_report.json` 의 `accept: true` 를 인용하지 않는다** (2026-08-06 승격 —
   출처 STATUS 서두 함정 ①). `mode: system`(P1 대 B3) · `h2_eligible: false` 이고 run 은
   2026-08-01 자 구 코퍼스 산출이다. **승인 판정은 사전등록 문서의 판정표에서 읽는다.**

---

## 5. 미해결 · 후속 (배치 추적 = RECONCILIATION-v09 §3)

**전파 배치 B0–B8은 전부 완료됐다**(2026-07-28 확인 · `check_signatures.py` 서명 정합 ✓ · CLI가
`s1_coverage_cli`·`s2_timeseries_cli`로 재라벨되고 `h1`·`h2`는 호환 별칭으로만 남음).
**IR 하네스·T-gate·결함주입도 구축·실행 완료다.** 남은 것은 실험이 아니라 **자원 교정과 재실험**이다.

- [x] **상류 교정 (C0) — 임계경로에서 내려왔다 (2026-08-08 갱신 · 아래 구 순서를 대체한다).**
      **상류 대기열은 0이다.** 종료 여섯은 `upstream/archive/` 에 있다 — CR-004R·CR-007·CR-008·
      **CR-011**·**CR-012**·CR-013([종료 기록](../upstream/archive/README.md)). 살아 있는 여섯은
      전부 **임계경로 밖**이다 — CR-001A(송부 보류 · 하류 한계효과 ≈ 0) · CR-002 · CR-003 ·
      CR-005 · CR-006(송부 가능) · **CR-009**(상류 발행 완료 · 하류 미소비).
      **막는 것은 이제 상류가 아니라 하류 코드다** — CR-012 검증기준 ①(`is_query` 1,000 → 1,200)이
      열려 있고 그 일이 [PLAN-045](plans/PLAN-045-b-layer-query-ingestion-downstream.md) 다.
      송부 순서 정본은 [upstream/HANDOFF-QUEUE.md](../upstream/HANDOFF-QUEUE.md).
      *(구 순서 ①CR-004R ②CR-007 ③CR-005 ④CR-006 ⑤CR-001A ⑥CR-002·003 은 2026-07-31 기록이다.)*
- [ ] **재실험 (PLAN-029).** 상류 P0 3건(CR-001·002·003) 교정 → `make vendor` 새 스냅샷 →
      **새 사전등록 아래 H3·H4·H5 재확증**. 제2 확증분할 200건 신규 수집 = [PLAN-031](plans/PLAN-031-b-layer-second-confirmation-split.md)(**🔒 동결 2026-07-31** · IPC 21종·B2′=bge-m3·파일럿 500콜).
- [ ] **H2 최초 검정의 전제.** D-12가 해소되어 **문서집합 불변·링크만 바뀐 델타 릴리스**가 나오기
      전까지 H2는 원리적으로 검정 불가다. 자격 없는 델타로 "지지"를 만들지 않는다(CLAUDE.md §1-2).
- [ ] **B7 후속(잔여).** 산출 파일명·figures 출력 경로의 S-시리즈 재라벨 (`h1_*.md` → `s1_*.md` 등) —
      figure/IR 하네스 재빌드 시 동반.
- [ ] **투고본 v2.0.** 재실험 후 새로 쓴다. v1.0/v1.1은 교정 전 상태의 기록으로만 인용한다.
