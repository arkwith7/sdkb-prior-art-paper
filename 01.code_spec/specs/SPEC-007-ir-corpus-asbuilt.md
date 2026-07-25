# SPEC-007 · IR 코퍼스 as-built 인벤토리 (검색 데이터셋 · 측정 기반)

| | |
|---|---|
| 지지하는 것 | **C2 핵심증명**(선행기술 검색에서 데이터셋 실효) / 논문 §5–6(RQ2·RQ3·T1·T2) |
| 정본(측정 대상) | `data/processed/ir/ir_corpus_v09.parquet` (40,552행) · `data/processed/ir/qrel_examiner.parquet` (2,416엣지) |
| 원천 | `graph_v0/v1/v2.ttl` + `central_axis.oxstore`(sidecar 청구항) — 조립기 `corpus/assemble.py` |
| 입력 명세 | [SPEC-006](SPEC-006-g0-asbuilt-inventory.md) (G₀ 원천이 어디 있는가) · 계획 [PLAN-017](../plans/PLAN-017-v09-ir-benchmark-dataset.md) |
| 재측정 | §8 스크립트 (pandas) |

> **이 문서는 "조립된 검색 데이터셋이 실제로 무엇인가"의 정본 기록이다.** SPEC-006이 *입력*(원천에
> 질의·정답이 어디 있는가)을 고정했다면, 이 SPEC-007은 그 입력을 재조립한 *출력*(문서중심 IR
> 코퍼스와 qrel의 스키마·서명·규율)을 고정한다. 매 세션 재조사를 끝내기 위함이다(SPEC-006과 같은 규율).
>
> **모든 수치는 2026-07-26 측정값**(`ir_corpus_v09.parquet` 서명 `ec5ea51b626d3ff9`)이며 **parquet이
> 정본**이다(문서와 어긋나면 실물이 옳다 · CLAUDE.md §1.1). 값이 바뀌면 §8로 재측정해 이 문서를 갱신한다.
>
> 특허 전문(abstract/claim)을 담으므로 parquet은 `license_restricted`(KIPRIS 학술이용·비재배포) →
> gitignore, `make corpus`로 로컬 재생성한다. 커밋되는 것은 이 SPEC·프로파일·MANIFEST의 집계·서명뿐.

---

## 1. 서명

| 자원 | 값 | 파일 | sha256(앞16) |
|---|---:|---|---|
| **IR 코퍼스** | **40,552 행 · 29 컬럼** | `data/processed/ir/ir_corpus_v09.parquet` | `ec5ea51b626d3ff9` |
| **심사관 qrel** | **2,416 엣지** | `data/processed/ir/qrel_examiner.parquet` | `10ab67f21cc1328d` |
| 원천 G₀ | 105,588 트리플 | `data/processed/graph_v0.ttl` | `a79a8a27db593a77` |
| 원천 G₁ | — | `data/processed/graph_v1.ttl` | `41094e9f053d6b4c` |
| 원천 G₂ | — | `data/processed/graph_v2.ttl` | `16b4f3223e049762` |
| sidecar | 11,606,318 트리플 | `data/processed/central_axis.oxstore` | (PROVENANCE.json) |

재생성: `make corpus` → 프로파일 [data/profiles/ir_corpus_v09.md] + MANIFEST append.

---

## 2. 문서 인벤토리 (역할·원천별)

### 2.1 source 분포 (역할 우선순위 라벨)
| source | 문서 | 역할 | 텍스트(초록/청구항전체) |
|---|---:|---|---|
| **g0_rej** | 1,000 | **질의**(거절특허 · 전량 KR) | 100% / 100% |
| **g0_cited** | 3,034 | **정답 후보**(심사관·출원인 인용) | 98.0% / 72.4% |
| **g1** | 24,179 | 후보·hard negative(삼성·SK하이닉스) | 100% / 100% |
| **g2** | 12,339 | 후보·이식성(KSIA 소부장 188사) | 100% / 100% |
| **합계** | **40,552** | | 초록 99.8% · 청구항전체 97.9% |

- **`source` = 역할 우선순위 라벨**(rej > cited > g1 > g2). 한 특허가 여러 그래프에 있어도 최상위 역할로 라벨.
- 심사관 정답 노드(`is_examiner_positive`=true) = **2,211**(코퍼스 존재분). 원 2,321 중 텍스트 0인
  비특허 110개(`other_*`) 제외 — §4 참조.
- 청구항 중앙값: 질의 12·독립항 2 / g1 12·3 / g2 12·2 / cited 10·2.

### 2.2 in_gX 플래그 ≠ source (혼동 금지)
| 플래그 | 값 | 뜻 |
|---|---:|---|
| in_g0 | 4,034 | **graph_v0.ttl 파일에 존재**(=rej 1,000+cited 3,034) |
| in_g1 | 28,213 | graph_v1.ttl에 존재(G₁=G₀+델타 → g0 노드 포함) |
| in_g2 | 16,373 | graph_v2.ttl에 존재(G₂=G₀+델타 → g0 노드 포함) |
| 다중그래프 문서 | 4,034 | g0 노드는 g1/g2 파일에도 실린다(포함관계) |

**`in_gX` 는 "그 그래프 파일에 존재하는가"(포함관계)이고 `source` 는 "역할이 무엇인가"이다.** G₁/G₂는
G₀ 위에 델타를 병합한 상위집합이라 g0 노드가 in_g1/in_g2 로도 잡힌다 — 이중집계가 아니라 파일
멤버십이다. 후보 코퍼스 규모(≈40k)는 `source` 로 세고, 그래프 소속은 `in_gX` 로 본다.

---

## 3. 스키마 (컬럼 딕셔너리 — 29종, 전량 사용)

| 컬럼 | dtype | 정의 | 쓰임(논문 자리) |
|---|---|---|---|
| `doc_id` | str | IRI 지역명(§5) — 유일키 | 모든 색인·qrel 조인 |
| `iri` | str | 전체 IRI `…/data/patent/<doc_id>` | 그래프 역추적 |
| `source` | str | g0_rej·g0_cited·g1·g2 (역할 라벨) | 후보군 정의·하위집단 |
| `is_query` | bool | RejectedPatent 여부(=질의 1,000) | 질의 집합 선택 |
| `is_examiner_positive` | bool | 심사관 인용 정답 노드(2,211) | 정답 문서 표시 |
| `in_g0`·`in_g1`·`in_g2` | bool | 그래프 파일 멤버십(§2.2) | 원천 추적 |
| `lang` | str | 스크립트 감지 ko/ja/en/und (§6) | KR vs 외국 하위집단 T2 |
| `title` | str | prefLabel(제목) | 질의표현 q_repr_title_* |
| `abstract` | str | abstractText(정제) | 초록 팔·text_main |
| `first_claim_original` | str | G₀ firstClaimText(원문 claim1, 질의만) | 청구항 재구성 병기·감사 |
| `claims_independent` | str | **sidecar 재구성 독립항**(정본) | 독립항 질의단위(강건성) |
| `claims_full` | str | **sidecar 재구성 전체 청구항**(정본) | 주 청구항 텍스트 |
| **`text_main`** | str | **초록 + 청구항전체**(질의·후보 대칭) | **주 색인 텍스트**(BM25·Dense) |
| `n_claims`·`n_independent` | int64 | 청구항·독립항 수 | 통계·필터 |
| `filing_date`·`publication_date` | str | 출원일·공개일(ISO) | 시점유효 분할(B8)·누출통제 |
| `publication_number`·`application_number` | str | 서지 번호 | 식별·중복확인 |
| `patent_office` | str | 관할(KR/US/…) | 관할 하위집단 |
| `ipc` | list[str] | IPC 코드(100% 보유) | 분류 팔·hard negative |
| `cpc` | list[str] | CPC 코드(2.4% — 희소) | CPC 팔(희소성 한계 명시) |
| `concepts` | list[str] | 개념링크(98% — realizesProcess 등) | **온톨로지 재랭크 팔**(언어중립) |
| `q_repr_abstract` | str | 질의 표현: 초록 | 질의표현 강건성 |
| `q_repr_claims` | str | 질의 표현: 청구항전체 | 〃 |
| `q_repr_abstract_claims` | str | 질의 표현: 초록+청구항(=text_main) | **주 질의 표현** |
| `q_repr_title_abstract_claims` | str | 질의 표현: 제목+초록+청구항 | 질의표현 강건성 |

- `q_repr_*` 4종은 **질의(is_query=true) 에만** 채워진다 — 후보는 null(PLAN-017 §7 M1).
- **미사용 컬럼 없음.** 대응이 깨지면 결함(CLAUDE.md §7).
- 청구항 본문 정본 = **sidecar `featureText` 재구성**(claimNumber·featureSeq 순 이어붙임, HTML 정제).
  `first_claim_original` 은 G₀ 원문 claim1 을 병기해 재구성 감사에 쓴다(SPEC-006 §8).

---

## 4. qrel 분모 규율 (혼용 금지 — 핵심)

| 항목 | 값 | 뜻 |
|---|---:|---|
| 원 인용 엣지 | **2,534** | G₀ `hasPriorArtExaminer` 전량 |
| 원 고유 정답 노드 | **2,321** | 인용된 고유 CitedPatent |
| **코퍼스한정 qrel 엣지** | **2,416** | 정답이 검색가능 문서인 엣지 |
| 코퍼스한정 고유 정답 | **2,211** | = `is_examiner_positive` |
| 고유 질의(정답 ≥1) | **981** | 질의밀도 981/1,000 = **98.1%** |
| 제외 정답 노드 | **110** | 텍스트 0인 비특허 선행기술(`other_*`) |
| 제외 엣지 | **118** | 위 110 노드로 향하는 인용 |

- **제외 근거**: 텍스트가 전무한 비특허 선행기술(학술논문 등)은 어떤 검색기(BM25/Dense/온톨로지)로도
  회수 불가하다. qrel에 남기면 모든 시스템의 recall 상한을 동일하게 깎아 벤치마크를 오도한다 — TREC 관행상
  판정 가능한(검색가능) 문서로 한정한다. **원엣지 2,534·제외 118은 프로파일에 투명 보고**(사후 조정 아님).
- **혼용 금지(SPEC-006 §7 연장)**: 2,534(인용엣지) ≠ 2,321(원 고유정답) ≠ 2,416(코퍼스한정 엣지) ≠
  2,211(코퍼스한정 정답). 논문에서 각 수치의 분모를 명시한다.
- qrel 스키마: `query_id`(질의 doc_id) · `doc_id`(정답 doc_id) · `relevance`(1 — 등급1 이진).
  등급2(`PriorArtJudgment` 청구항수준 635)는 후속 B5에서 별도 파일로 조립.

---

## 5. docID 규약 (IRI 지역명)

`doc_id` = IRI의 마지막 `/` 뒤 지역명. 관할 접두어가 붙는다.

| 예 | 역할 |
|---|---|
| `kr_1019970082313` | 질의(거절특허, KR 출원번호) |
| `cn_CN106917072A` · `us_US5308414` · `jp_…` · `wo_…` · `ep_…` | 정답·후보(관할별) |
| `other_LinYang…2021` | 비특허 선행기술(텍스트 0 → qrel 제외 대상) |

- **함정(실측)**: 심사관 정답 노드는 `ont:Patent` 이 아니라 **`ont:CitedPatent`** 로만 타입된다
  (Patent 타입 0건). 문서 노드 선택은 `Patent ∪ CitedPatent ∪ RejectedPatent` 여야 정답을 놓치지 않는다.
- sidecar 특허 IRI(`…/patent/kr_1019970082313`)와 G₀ 특허 IRI가 **동일** → 청구항 조인이 성립.
  sidecar 청구항 IRI 접두(`rej_`·`cited_`·`g1_`·`g2_`)는 수집 회차 표식이지 doc_id 가 아니다.

---

## 6. 언어 지형 (실측 — 다국어)

| 집합 | 규모 | 언어 |
|---|---:|---|
| 질의(g0_rej) | 1,000 | **ko 100%** |
| 후보 g1/g2 | 36,518 | **ko ~100%** |
| 전체 코퍼스 | 40,552 | ko 39,246 · en 1,189 · ja 117 |
| **심사관 정답(2,211)** | | **ko 1,266(57%) · en 862(39%) · ja 83(4%)** |

- 정답 언어비 ko57·en39·ja4 는 PLAN-017 §1.6 실측(57/39/2)과 정합 — 코드 언어감지기의 독립 검증이다.
- `lang` 은 텍스트 스크립트로 결정한다: 한글→ko, (한글없고)가나→ja, 그 외→en. 한자단독(중국어/JP영문MT)은
  en. **다국어 코퍼스는 결함이 아니라 KIPO 심사 태스크의 본질**이며, 언어중립 개념 IRI를 쓰는 온톨로지
  팔이 교차언어(=저어휘중첩 극단)에서 가치를 증명할 무대다(H2b).

---

## 7. 누출 통제 (건설적 — CLAUDE.md §1.4 · PLAN-017 B6)

- **문서 피처에서 배제**: `hasPriorArt` · `hasPriorArtExaminer` · `hasPriorArtApplicant` ·
  `overPriorArt` · `NoveltyScore`. 코퍼스 어느 컬럼에도 이들 파생값이 없다(성공기준3 통과).
- qrel(`hasPriorArtExaminer`)은 **별도 파일로만** 추출 — 코퍼스 문서에 포함되지 않는다.
- `concepts`(realizesProcess 등)는 **질의/문서 자체의 기술**이지 정답 파생이 아니다 → 피처로 허용.
- 시점유효성·family-disjoint 분할은 후속(B8) — `filing_date` 가 그 입력이다.

---

## 8. 재측정 (이 문서의 모든 수치)

```python
import pandas as pd, hashlib
from sdkb_paper import config
c = pd.read_parquet(config.IR_CORPUS); q = pd.read_parquet(config.QREL_EXAMINER)
hashlib.sha256(config.IR_CORPUS.read_bytes()).hexdigest()[:16]        # 서명
c.source.value_counts()                                              # §2.1
[int(c.in_g0.sum()), int(c.in_g1.sum()), int(c.in_g2.sum())]         # §2.2
c[c.is_examiner_positive].lang.value_counts()                        # §6 정답 언어
[len(q), q.query_id.nunique(), q.doc_id.nunique()]                   # §4 qrel
# 성공기준 자체검증:
#   make corpus-check   (python -m sdkb_paper.corpus.assemble --check)
```
값이 바뀌면 이 SPEC를 같은 커밋에서 갱신한다(CLAUDE.md 데이터 프로파일 의무). 성공기준(PLAN-017 §5)은
`make corpus-check` 가 강제: 질의 1,000 청구항+filingDate · 질의밀도 ≥97% · 누출컬럼 0 · qrel 정답 전량 존재.
