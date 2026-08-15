# IR 코퍼스 프로파일 — ir_corpus_v09 (PLAN-017 M1)

> 코드 생성물. 재생성: `make corpus`. 원천 TTL 서명은 §서명. 특허 전문은 license_restricted(gitignore) — 이 프로파일의 집계만 커밋된다(CLAUDE.md §1.4·§4).

- 생성(UTC): 2026-08-15T11:49:19.603140+00:00
- 지지 주장: **C2 핵심증명**(선행기술 검색)의 입력 · 논문 §5–6(RQ2·RQ3·T1·T2)

## 1. 서명 (원천·산출)
| 자원 | 값 | sha256(앞16) |
|---|---:|---|
| ir_corpus_v09.parquet | 41,223 행 | `83eef760ed0a8be2` |
| qrel_examiner.parquet | 2,416 엣지 | `10ab67f21cc1328d` |
| graph_v0.ttl | — | `6b3f3c5b973dd629` |
| graph_v1.ttl | — | `41094e9f053d6b4c` |
| graph_v2.ttl | — | `16b4f3223e049762` |

## 2. 구조 (컬럼·dtype·목적)
| 컬럼 | 목적 |
|---|---|
| doc_id·iri | 문서 식별자(IRI 지역명) |
| source | g0_rej(질의)·g0_cited(정답)·g1·g2(후보) |
| is_query·is_examiner_positive·in_g0/1/2 | 역할·원천 플래그 |
| query_layer | 질의의 층: A(주분석 1,000) · B(제2 확증분할 200) · null(후보) |
| is_candidate | 색인·후보 풀 포함 자격 — B층 신규 문서만 False |
| lang | 스크립트 감지(ko/ja/en) — 다국어 하위집단 T2 |
| title·abstract·first_claim_original | 서지·초록·G₀ 원문 청구항1 |
| claims_independent·claims_full | sidecar 재구성 청구항(정본) |
| **text_main** | 초록+청구항전체 — 주 색인 텍스트(질의·후보 대칭) |
| q_repr_* | 질의 4종 표현(초록/청구항/초록+청구항/제목+초록+청구항) |
| filing/publication_date·publication/application_number·patent_office | 시점·서지 |
| ipc·cpc·concepts | 분류·개념링크(CPC팔·온톨로지팔 입력) |
| n_claims·n_independent | 청구항 통계 |

## 3. 형태·기술통계
- 총 문서: **41,223**
- source 분포: g0_cited=3,513 · g0_rej=1,200 · g1=24,173 · g2=12,337
- 언어 분포(전체): en=1,412 · ja=140 · ko=39,671
- 질의(is_query): 1,200 = **A층 1,000 + B층 200** (B층 = CR-012 · 판독 B 용 · A층 주분석에 섞이지 않는다) · 심사관 정답 노드(is_examiner_positive): 2,211
- 후보 자격(is_candidate): 41,031 — B층 질의가 새로 데려온 문서는 후보에서 제외한다(PLAN-045 D2 · 질의는 후보가 아니다). A층 문서집합 불변의 근거.
- 정답 노드 언어: en=862 · ja=83 · ko=1,266
- 텍스트 커버리지: 초록=99.8% · 청구항전체=97.5% · text_main=99.8%
- 청구항 보유 문서: 40,187 · 독립항 보유: 40,185

## 4. qrel (심사관 인용 · 등급1)
- 원엣지(hasPriorArtExaminer): 2,534 · 원 고유정답 노드: 2,321
- 코퍼스한정 qrel: **2,416 엣지** · 고유 질의 981 · 고유 정답 2,211
- 제외: 텍스트 0인 비특허 선행기술 110 노드(학술논문 등 `other_*` — 검색 불가라 qrel 표준 관행상 제외).
- 질의밀도(코퍼스 내 정답 ≥1 / 원질의 1,000): **98.1%** (성공기준 ≥97%)
- 분모 규율(SPEC-006 §7): 2,534 인용엣지 ≠ 2,321 고유정답 ≠ 코퍼스한정. 혼용 금지.

## 5. 사용 목적
- **text_main** → BM25(nori)·Dense(Titan) 색인의 주 문서/질의 텍스트(RQ2).
- q_repr_* → 질의 표현 강건성(주=초록+청구항, 보조 3종).
- ipc/cpc → CPC 어휘팔·hard negative 표집(B4). concepts → 온톨로지 재랭크팔(언어중립).
- lang → KR vs 외국 하위집단 안전성 T2. filing_date → 시점유효 분할(B8)·누출통제.
- **미사용 컬럼 없음** — 전부 색인/필터/분할/평가에 대응(대응 깨지면 결함).

## 6. 누출 통제 (건설적)
- 문서 피처에서 배제: `hasPriorArt` · `hasPriorArtExaminer` · `hasPriorArtApplicant` · `overPriorArt` · `NoveltyScore`.
- qrel(hasPriorArtExaminer)은 별도 파일로만 추출 — 코퍼스 문서에 포함되지 않음.
- concepts 는 질의/문서 자체 기술이지 정답 파생이 아니다(realizesProcess 등).
