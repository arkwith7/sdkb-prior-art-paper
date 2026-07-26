# 진행 실적 (v0.9)

*최종 갱신: 2026-07-26 · 기조: 선행기술 검색 주 태스크 + T-gate (CLAUDE.md v0.9)*

> **서명 수치의 정본은 [CANONICAL-INDEX.md](CANONICAL-INDEX.md) §1.** 현재값: **G₀ 105,588 · G₁ 924,814 ·
> G₂ 490,529 트리플**. 라벨(RQ·H·C·S)의 정본은 [RECONCILIATION-v09.md](RECONCILIATION-v09.md) §1.
> v0.5 구 패러다임의 상세 진행 서사(커버리지·시계열·이식성 = S1/S2/S3)는
> [archive/STATUS-v05.md](archive/STATUS-v05.md)에 보존한다 — **인용은 "S1(구 H1)" 형식으로만**.

새 세션은 이 문서부터 읽는다. 온톨로지·반도체·통계 용어는 `GLOSSARY-*.md`, 소부장 IP-R&D 실무는
[REF-001](REF-001-ip-rnd-domain-framework.md), 무엇이 정본인지는 [CANONICAL-INDEX.md](CANONICAL-INDEX.md)를 본다.

---

## 0. 세 주장의 현재 상태 (CLAUDE.md §0)

| 주장 | 내용 | 증거 | 상태 |
|---|---|---|---|
| **C1 · 자원** | 공유 T-Box가 세 태스크를 표현 | 도달성 사다리·CQ 28·SHACL·어휘 커버리지 | **지지** (관측) |
| **C3 · 진화안전** | 다중 태스크 작동성 — T-gate(T1·T2·T3) | 결함주입·McNemar·음성대조군 | **미측정** (T-gate 미구현) |
| **C2 · 핵심증명** | 선행기술 검색 온톨로지 보강 효과 | Recall@100·nDCG·ablation·부트스트랩 | **미측정** (IR 하네스 미구축) |

확증 가설 **H1–H5** (RQ1 검증게이트→H1·H2=C3 · RQ2 검색유용성→H3=C2 · RQ3 계층기여·특이성→H4·H5=C2).
탐색적 강등: 운용 효율·법적 맥락·의미 도달성.

---

## 1. 완료 (v0.9)

**데이터 자원 (C1 · C2 입력)**
- [x] **G₀/G₁/G₂ 전면 재빌드** — 미반영 SDKB 온톨로지 전량 반영(선행기술 ABox·상용화·RBV). §1 서명
      105,588·924,814·490,529 동결. 선행기술조사 정답지 도달성 0%→95.3%(노드) → 검색 벤치마크 성립.
- [x] **검색 벤치마크 스파이크 통과** — 질의당 회수가능 정답 97.6% · 정답 텍스트 93.3% · 개념링크 70.5%
      (메모리 `spike-retrieval-feasibility-passed`).
- [x] **M1 IR 코퍼스·심사관 qrel 조립** — 질의(거절특허 1,000)·후보 코퍼스(G1/G2 ~40k)·qrel 정답 2,321.
      as-built 정본 = [SPEC-007](specs/SPEC-007-ir-corpus-asbuilt.md) (커밋 `8abd209`).
- [x] **G₀ as-built 인벤토리** = [SPEC-006](specs/SPEC-006-g0-asbuilt-inventory.md) — "무엇이 어디에" 데이터 딕셔너리.
- [x] **종속항 분해 Tier 1/2/3** — 거절특허(10,562)·인용 선행기술(30,438)·G₂ 소부장(116,774) 종속항 실체화,
      회수율 1.0 · SHACL 통과 (메모리 `tier1/2/3-...done`).

**온톨로지 자산 (C1 · 재사용, 논문이 변경하지 않음)**
- [x] T-Box 설계서 [SPEC-005](specs/SPEC-005-tbox-ontology-design.md) — 태스크 3종 어휘 근거.
- [x] CQ 배터리 28개(스위트 pa·em·tf·core) · 어휘 검증 커버리지(측정 운용, 게이트 아님).
- [x] L0–L3 게이트 LIVE ([SPEC-001](specs/SPEC-001-validation-gate.md)).

**거버넌스·정합 (원고·라벨 전파)**
- [x] **정본 원고 v0.9 §1.4/§1.5 동결** — H1–H5·기여 3 (커밋 `3355838`).
- [x] **구 원고·그림·표 아카이브** — v0.5/v0.7 → `paper/archive/`, 커버리지/시계열/이식성 그림·표
      → `paper/archive/{figures,tables}/` (S-시리즈·인용 금지, 커밋 `0d87075`).
- [x] **정합 전파 B0·B1·B2·B4·B5** — 라벨 사전 확정 · CLAUDE.md §0 갱신 · 구 SPEC/PLAN/AUDIT 배너·
      S-재라벨 · SPEC-001 T-gate 절 신설 · CANONICAL-INDEX/STATUS v0.9 재생(구본 archive). 원장 =
      [RECONCILIATION-v09.md](RECONCILIATION-v09.md).

---

## 2. 진행 중 · 다음

- [ ] **B6** — `scripts/check_signatures.py` TARGETS에 v0.9 원고 추가(현재 `[warn] 검사할 원고 없음`) ·
      GLOSSARY·README·REF-001 용어 S-시리즈/v0.9 정합.
- [ ] **B7** — 코드 S-시리즈 재라벨(`analysis/h1_cli→s1_*`·`h2_cli→s2_*` · Makefile 타깃 · 산출 파일명 · 테스트 동반).
- [ ] **B8** — 전체 sig-check + 최종 표류 0 감사.
- [ ] **PLAN-017 승인 후 IR 하네스 구축** — Pyserini(BM25 nori)·FAISS flat Dense·RRF·ontology_rerank ·
      Titan Embed v2 · Haiku 4.5 질의번역. → **C2 산출물**(Recall@100·nDCG·ablation·하위집단·부트스트랩).
- [ ] **T-gate 구현** ([SPEC-001](specs/SPEC-001-validation-gate.md) §T-gate) — `validate/t{1,2,3}_*.py` ·
      `make gate` 확장 · 결함주입 매트릭스. → **C3 산출물**.
- [ ] **G₁ 청구항 축 마감** (Phase D · 결정 `next-review-g1-claims-then-tier3`) — 엣지 중립(H1 불변).

---

## 3. S-시리즈 — 구 패러다임 결과 (C1 2차 재사용 · 인용 규약 준수)

구 커버리지(S1)·시계열(S2)·이식성(S3) 검정은 **자원 형성 타당성의 방증**이자 **T-gate T3의 회귀 감시
대상**(em·tf·core 스위트)으로 보존된다. 성능은 주장하지 않는다(전문가매칭·기술예측은 별도 논문 AFCP-EM).

| 구 라벨 | 결과 (구본) | v0.9 위치 |
|---|---|---|
| **S1** (구 커버리지 H1) | 지지 — C₀ 20/49 · 네 표본집합 p 유의 · 소부장 세 층 지지 | `archive/STATUS-v05.md` · `paper/archive/tables/h1_*.md` |
| **S2** (구 시계열 H2/RQ2) | 조합 개념 능력 존재 증명(유의성 아님) · 작은 n은 현상 | `archive/STATUS-v05.md` · `paper/archive/tables/h2_*.md` |
| **S3** (구 이식성 RQ3) | 소부장 G₂ 폭 26/49 포화 · 깊이 갈림 | `archive/STATUS-v05.md` · `paper/archive/tables/h1_ksia*.md` |

> 상세 서사·검정 수치·재동결 이력은 전부 [archive/STATUS-v05.md](archive/STATUS-v05.md)에 있다.
> **v0.9 산출물의 근거로 직접 인용하지 않는다** — 인용은 C1의 2차 재사용 맥락에서 "S1(구 H1)" 형식으로만.
