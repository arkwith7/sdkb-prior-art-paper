# PLAN-017 — v0.9 선행기술 검색 벤치마크 데이터셋: 정의 및 보완

> **📦 아카이브 (2026-08-01) — 실행 완료.** 이 계획이 정의한 IR 벤치마크는 M1에서 조립됐고,
> **as-built 정본은 [SPEC-007](../specs/SPEC-007-ir-corpus-asbuilt.md)** (코퍼스 40,552 · qrel 2,321)이다.
> 새 작업의 근거로 인용하지 않는다 — 코퍼스의 현재 상태는 SPEC-007·`data/profiles/ir_corpus_v09.md`가
> 정본이고, 이 문서는 **조립 전의 설계 의도**를 보존할 뿐이다.
> 아래 상태 배너는 아카이브 시점의 원문이다.
>
> **상태(원문): 초안 (2026-07-25) · 승인 대기 🛑**
> 정본 초안 [paper/논문_v0_9_SDKB_통합초안.md] 기조 전환의 첫 실행 계획.
> 이 PLAN은 데이터셋(B)만 다룬다. 거버넌스 재작성(A)·검색 시스템·T-gate는 후속 PLAN.
> 관련 결정: 메모리 `pivot-v09-retrieval-primary-task` · `spike-retrieval-feasibility-passed`.
> **이 문서의 모든 수치는 실측(2026-07-25, `graph_v0.ttl` 105,588 + 벤더 스냅샷)이다.**

---

## 0. 목적과 한 줄 요약

v0.9의 주 검증 태스크(선행기술 검색)를 **사다리 검증(키워드·의미·KG)으로 평가 가능한 IR 벤치마크
데이터셋**으로 정의하고, 관찰로 드러난 8개 보완 항목을 채운다. 지지하는 논문 축: **RQ2(하이브리드 검색)·
RQ3(계층 기여)·T1·T2**의 입력 전부.

**한 줄 요약:** 정답·질의·후보가 텍스트·시점·개념링크째로 대부분 존재한다(질의밀도 97.6%). 데이터는
"큐레이션 KG" 모양이라 "문서중심 IR 코퍼스" 모양으로 **재조립 + 8개 축 보완**하면 벤치마크가 선다.
**단, 이 벤치마크는 본질적으로 다국어다(§1.6) — 이것이 유일한 핵심 설계 결정이며 온톨로지 기여의
강점이기도 하다.**

---

## 1. 데이터셋 정의 (관찰된 현 상태)

### 1.1 질의 집합 (Queries)
| 속성 | 값 | 출처 |
|---|---|---|
| 규모 | 거절특허 1,000건 (전량 KR) | `graph_v0.ttl` `ont:RejectedPatent` |
| filingDate | 1,000/1,000 (100%) | 실측 |
| abstractText | 1,000/1,000 (100%) | 실측 |
| **claimText (인라인)** | **0/1,000** → sidecar 조인 필요 | 실측 (B1) |
| 심사관 인용 ≥1 | 1,000/1,000 | 실측 |

질의 단위(v0.9 §4.2): 주 분석 = 독립 청구항(Claim-only), 보조 = Claim+Abstract / Fielded.

### 1.2 정답 집합 (qrel — 양성 전용 약한 정답)
| 속성 | 값 | 비고 |
|---|---|---|
| 심사관 인용 엣지 | 2,534 (`hasPriorArtExaminer`) | 분모 혼용 금지 |
| 고유 정답 노드 | 2,321 | 〃 |
| CitedPatent 노드 총계 | 3,034 | 출원인 인용 포함분 |
| 정답 텍스트 보유 | 93.3% (abstract/claim) | **영어 정규화** |
| 정답 filingDate | 95.3% | 시점유효성 |
| 정답 개념링크(KG 팔) | 70.5% (realizesProcess 등) | 사다리 최약칸 |
| **관할 분포** | KR 1,720 · JP 721 · US 471 · WO 81 · CN 20 · EP 12 | source = BigQuery Google Patents |

**등급(v0.9 §3.5):** 등급2 = `PriorArtJudgment` 청구항수준 연결(sidecar 635) · 등급1 = 특허수준
`hasPriorArtExaminer` · 출원인 인용(`hasPriorArtApplicant`)은 분리 보존.

### 1.6 언어 지형 (실측 — 다국어 벤치마크)
**중요 정정(2026-07-25):** 텍스트는 영어 정규화가 아니라 **각 특허의 원어**다. 실측 결과:

| 구성요소 | 규모 | 언어 |
|---|---|---|
| 질의 (거절특허) | 1,000 | **한국어 100%** |
| 후보 코퍼스 G1/G2 | ~40k | **한국어 ~100%** |
| qrel 정답 | 2,321 | **한국어 57% (1,719 kr)** · **영어 39%**(US 470·WO 79·CN 20·EP 12·JP영문MT 597) · **일본어 2% (67 jp원문)** · 기타 9 |

- `dcterms:source "BigQuery Google Patents"`는 "영어"를 뜻하지 않는다 — Google Patents는 KR 특허를
  한국어 원문으로, 다수 외국 특허를 영문 MT로 저장한다. 다중 언어 병기 노드는 **0건**(각 노드 1언어).
- **함의:** 한국어 질의로 영어/일본어 정답(43%)을 어휘검색으로 회수할 수 없다. 한국어 전용 → 회수율
  상한 ~57%. 영어 전용 → 한국어 다수(질의·코퍼스·정답 57%)를 전량 번역해야 함.
- **이것은 결함이 아니라 실제 KIPO 심사 태스크의 본질이며, 언어중립 개념 IRI를 쓰는 온톨로지 팔이
  어휘검색이 구조적으로 실패하는 지점(교차언어=저어휘중첩의 극단, H2b)에서 가치를 증명할 무대다.**

### 1.3 후보 코퍼스 (Candidate pool D_q)
| 원천 | 규모(특허) | 텍스트 | 역할 |
|---|---|---|---|
| G0 | 1,000 거절 + 2,321 정답 | 有 | 앵커·질의 |
| G1 | ~24,179 (삼성·SK하이닉스) | claimText 有 | 후보·hard negative |
| G2 | ~12,339 (KSIA 188사) | claimText 有 | 후보·이식성 |
| **합계** | **≈ 4만+ 시점유효 전문 문서** | | CLEF-IP 부분집합급 |

### 1.4 메타데이터 축
filingDate(시점) · **DOCDB family_id(부재 → 보완 B2)** · IPC/CPC(有, CPC 팔 B4용) · 개념링크(KG 팔).

### 1.5 릴리스 분리 (누출 방지 · v0.9 §3.7)
`g:core` / `g:qrels-dev` / `g:qrels-test-sealed`(해시 고정·접근로그) / `g:derived-features` / `g:provenance`.

---

## 2. 보완 항목 (Gap → 조달/작업 → 근거)

| # | Gap | 현 상태(실측) | 보완 방법 | 근거·비고 |
|---|---|---|---|---|
| **B1** | 질의 청구항 텍스트 | 거절특허 claimText 0/1000 | `central_axis.oxstore`(1.2GB sidecar)에서 `Patent→hasClaim→Claim→claimText` 조인 + 독립항 식별 | 주 질의단위(§4.2)의 전제 |
| **B2** | DOCDB family_id | 사실상 부재 | `collect/bq_family.py`로 BigQuery 조달, 질의·정답·후보 전량에 family 부여 | family-disjoint 분할(§4.3) |
| **B3** | 단일 문서 코퍼스 미조립 | G0/G1/G2 TTL 분산 | 통합 문서 인덱스 조립: {docID, text, filingDate, family, IPC/CPC, 개념링크} | IR 하네스 입력 |
| **B4** | Hard negative 미정의 | — | 동일 CPC/공정 · 시점유효 · 비인용 문헌 표집(후보군이 정답 주변으로 축소 방지) | §4.4 |
| **B5** | graded qrel(등급2) | PriorArtJudgment 635 (sidecar) | `aboutClaim`/`overPriorArt`로 (질의,독립항,정답) 등급2 부분집합 구성 | §3.5 · nDCG용 |
| **B6** | 누출원 목록 미확정 | — | `leakage_check`: 질의 `hasPriorArtExaminer/hasPriorArt/overPriorArt` 엣지·`NoveltyScore`·qrel파생 개념링크 마스킹 목록 동결 | §4.5 |
| **B7** | **다국어 (핵심 결정)** | 질의·코퍼스=한국어, 정답=한57/영39/일2 (§1.6) | **권고: 원어 유지 다국어 코퍼스 + 교차언어 이중팔.** 어휘팔=질의 LLM 영역/일역 후 언어별 색인 RRF 병합(번역은 질의 1,000건 + JP 67건만, 코퍼스 4만건 번역 불필요); 밀집팔=다국어 인코더; **온톨로지팔=언어중립 개념IRI(헤드라인)**. 언어별 하위집단(KR vs 외국) T2로 보고 | 관찰 — 사용자 승인 대기 |
| **B8** | 시점분할 경계 | 미확정 | filingDate 정렬 60/20/20 + family-disjoint, **테스트 개봉 전 경계 동결** | §4.3 |

> **B7이 유일한 핵심 설계 결정이다(§1.6·§7).** 한국어 전용은 정답 43%(외국)를 구조적으로 놓쳐
> 회수율 상한 ~57%로 벤치마크를 망가뜨린다. 영어 전용은 한국어 다수(질의·코퍼스·정답 57%)를 전량
> MT해야 해 대규모 번역 비용 + "MT 코퍼스로 평가했다"는 타당성 위협을 낳고, 무엇보다 **온톨로지의
> 교차언어 가교라는 가장 강력한 증명 무대를 지워버린다.** 권고안(원어 유지 + 질의만 번역하는
> 교차언어 이중팔)은 번역을 질의 1,000 + JP 67로 한정하고, 언어중립 온톨로지 팔을 C2의 헤드라인으로
> 세운다. 사용자 제안(한국어 우선 → LLM 영역 → 병합)과 정합한다. **최종 채택 전 사용자 승인 필요.**

---

## 3. 산출물

- **[../specs/SPEC-007-ir-corpus-asbuilt.md] — 조립된 IR 코퍼스·qrel의 as-built 정본(스키마·서명·
  분모 규율). M1 완료분(2026-07-26). SPEC-006(입력)과 대칭.** ✅
- `data/processed/ir/ir_corpus_v09.parquet` (40,552행·29컬럼) · `qrel_examiner.parquet` (2,416엣지) —
  M1 산출(gitignore·`make corpus` 재생성). ✅
- `data/profiles/ir_corpus_v09.md` — §4 프로파일 의무 이행(구조·형태·기술통계·목적). ✅
- `data/DATASET-CARD-v09.md` — 검색 벤치마크 데이터 카드(6축 정의·분모 규율·라이선스·관할·분할) [TODO]
- 코드(`corpus/`): `claim_join`(B1 ✅) · `assemble`(B3 ✅ · qrel ✅) · `fetch_family`(B2) ·
  `build_splits`(B8) · `sample_hard_negatives`(B4) · `build_graded_qrels`(B5) · `leakage_check`(B6)
- 동결 산출: `qrels/dev/` · `qrels/test-sealed/`(해시) · `splits/family_time/` · 코퍼스 문서 인덱스 [후속]

## 4. 실행 순서 (fail-fast)

```
B7 언어정책 결정(선행) → B1 질의청구항 → B3 코퍼스 조립 → B2 family → B8 분할
   → B5 graded qrel → B4 hard negative → B6 누출차단
   → ▶ 진입 임계치: 누출 없는 BM25 Recall@100 산출 (이 수치 전 초록·기여 확정 금지)
```

## 5. 성공 기준 (검정 가능)
1. 통합 코퍼스에 질의 1,000 전량이 독립항 텍스트 + filingDate + family 보유.
2. 각 질의의 정답이 코퍼스 내 검색가능 문서로 존재(질의밀도 재확인 ≥97%).
3. `leakage_check` 통과: 마스킹 후 금지 간선 0.
4. family-disjoint·시점유효 분할이 두 번 실행에 동일(결정성).
5. 진입 임계치 BM25 Recall@100 산출(값 자체는 성패 아님 — 비공허 확인).

## 6. 비목표 (스코프 방어선)
- 검색 시스템(Dense/Hybrid/Ontology reranking)·T-gate·결함주입·ablation — 후속 **[PLAN-018](PLAN-018-v09-retrieval-tgate-harness.md)**(계층 B · 2026-07-26 신설·승인대기).
- 새 CLAUDE.md 거버넌스 — 산출물 A(별도).
- G0/G1/G2 그래프 자체의 온톨로지 변경 — 하지 않음(코퍼스는 파생 뷰).
- 라이선스 제한 원문 커밋 — 하지 않음(식별자·해시·재구축 절차만).

## 7. 미해결·결정 필요
- **B7 언어 정책** — **확정(2026-07-25): 원어 유지 다국어 + 교차언어 이중팔.**
- **검색 스택** — **확정(2026-07-25): Pyserini(BM25 nori + FAISS flat Dense + RRF hybrid) · parquet/pandas
  (메타데이터·후보필터). Postgres+pgvector 제거**(§8.3).
- **M1 코퍼스 설계 — 확정(2026-07-26):** (1) 청구항 텍스트 = sidecar `featureText` 재구성(claimNumber·
  featureSeq 순)을 정본, `firstClaimText`(원문 claim1) 병기. (2) 질의 표현 4종 필드 저장{초록 · 청구항전체 ·
  초록+청구항전체 · 제목+초록+청구항}, **주 분석 = 초록+청구항전체**(독립항만은 강건성). (3) 후보도 초록+
  청구항전체 재구성 색인(정답과 대칭). G₀ as-built 정본 = **[../specs/SPEC-006-g0-asbuilt-inventory.md]**.

## 8. 기술 스택 (2026-07-25 검토·확정)

환경에 Bedrock 기존 배선 확인: `.env`에 `AWS_BEDROCK_MODEL_HAIKU`·`BEDROCK_EMBED_MODEL`·`AWS_REGION`
등 존재, 기존 claim 분해가 Bedrock 사용. 접근은 `config.get_secret()` 경유(§CLAUDE 1.8).

### 8.1 밀집 인코더 — Amazon Titan Embed Text v2 (`amazon.titan-embed-text-v2:0`) · 채택
- **근거:** 다국어(KR/JP/EN 원어) 지원 → 원어유지 설계 정합. 특허특화 인코더(PaECTER/PatentSBERTa)는
  **영어전용**이라 다국어 코퍼스에 부적합. Titan v2가 그 공백을 메움.
- 차원 1024 · 결정적 · `BEDROCK_EMBED_MODEL` 키 사용 · 입력 토큰 한도 내 독립항+초록(확정은 구현 시).
- **재현성:** Bedrock 모델버전 `:0` 고정, 임베딩 캐시 해시. Bedrock 호스팅 의존은 한계로 명시(§9.5).
- **논문 대비:** 보조 영어-피벗 PaECTER 팔(질의→EN 번역, 영어 정답 부분집합)을 강건성으로 추가 가능.

### 8.2 질의 번역 LLM — Claude Haiku 4.5 (`global.anthropic.claude-haiku-4-5-20251001-v1:0`) · 채택
- **근거:** 기존 검증 인프라(claim 분해 16-way), `AWS_BEDROCK_MODEL_HAIKU` 기존재. KR→EN·KR→JP 질의 번역.
- **규율:** temperature=0 · 번역결과를 **동결·해시·커밋(파생 산출물)** → 재현성. **누출 경계 안**(질의만
  번역, qrel 미접촉). 대상 = 질의 1,000 + JP 정답 67(선택). 코퍼스 4만건 번역 안 함.

### 8.3 검색 — Pyserini(BM25 + FAISS Dense + RRF) · 확정 (Postgres+pgvector 제거)
**ablation 적합성이 결정 근거.** pgvector 기본 HNSW는 근사 검색이라 ablation Recall 델타에 인덱스
근사오차가 섞인다. **FAISS flat(브루트포스)은 정확·결정적**이라 델타가 순수 계층 효과. 4만 문서×1024차원
(~160MB)은 flat 정확검색이 밀리초 — 근사 인덱스는 수백만 건부터나 필요.

- **BM25:** Pyserini(Lucene/Anserini) · IR표준·재현성·**한국어 nori**. 교차언어 어휘팔 = 한국어 질의→
  nori색인(한국어 문서) + 영역 질의→standard색인(영어 문서) + 일역 질의→(일본어 문서) 각 BM25 후 RRF.
- **Dense:** Pyserini `FaissSearcher`(flat·정확), Titan v2 1024차원 임베딩(parquet 캐시 로드).
- **Hybrid:** Pyserini `HybridSearcher`(RRF) 내장.
- **메타데이터·후보필터:** parquet + **pandas 불린 마스크**(공개일<cutoff · family≠질의 · CPC). 4만 건
  규모라 DB 서버 불필요 — Postgres+pgvector 통째로 제거해 스택이 Pyserini 단일 생태계로 단순화.
- **ablation 워크플로:** Titan 임베딩 1회 계산·parquet 캐시 → 설정마다 캐시 벡터 로드/flat 검색만.
  재인덱싱 즉시·결정적, HNSW 튜닝 파라미터(M·ef) 없어 비교 오염 없음.
- 대안(초단순): NumPy matmul 코사인(신규 의존성 0). 4만 건엔 충분하나 hybrid·인용편의는 Pyserini가 우위.

### 8.4 신규 의존성 (승인 대상)
`boto3`(Bedrock Titan·Haiku) · `pyserini`(+JVM · BM25 nori + FAISS Dense) · `faiss-cpu` ·
자체 RRF/부트스트랩(또는 `ranx`). **psycopg·pgvector 불필요.** 확정 스택:
**Pyserini(BM25+FAISS Dense+RRF) · parquet/pandas(메타·필터) · Titan v2(임베딩) · Haiku 4.5(질의 번역)**.
- 어휘팔 교차언어 처리 = 질의 LLM 번역(KR→EN, KR→JP) 1,000+67건. 코퍼스 전량 번역은 하지 않음.
- sidecar 독립항 식별 규칙(청구항1 vs 종속관계 파싱) — B1 착수 시 확정.
