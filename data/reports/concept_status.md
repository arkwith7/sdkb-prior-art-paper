# 개념·공리 계기판 — 선언 · 실체화 · 작동

> 생성: `make concept-status`. **손으로 고치지 않는다**(CLAUDE.md §1-1·§1-7).
> 재는 대상은 **동결 벤더 스냅샷과 하류 코퍼스·점수식** — 즉 논문이 실제로 소비하는
> 것이다. 상류가 앞서 있으면 그 차이가 곧 **미도달**이며, 그것을 드러내는 것이 이 표의
> 목적이다. 괄호 안은 직전 실행 대비 델타다.

스냅샷 `0a7ff1537850` · 벤더 시각 2026-08-15T11:46:44+00:00

## ① 선언 — 어휘는 있는가, **추론 공리**는 있는가

| | 값 |
|---|---:|
| T-Box 트리플 | 1,577 |
| 클래스 | 103 |
| ObjectProperty / DatatypeProperty | 99 / 85 |
| `rdfs:subClassOf` (어휘 선언) | 36 |
| **추론 공리 합계** | **3** |

추론 공리 내역 — `subClassOf`·`domain`·`range` 는 어휘 선언이므로 세지 않는다.

| 공리 | 수 |
|---|---:|
| `owl:Restriction` | 0 |
| `owl:propertyChainAxiom` | 0 |
| `owl:inverseOf` | 0 |
| `owl:disjointWith` | 0 |
| `owl:equivalentClass` | 1 |
| `owl:equivalentProperty` | 0 |
| `owl:hasKey` | 0 |
| `owl:TransitiveProperty` | 2 |
| `owl:SymmetricProperty` | 0 |
| `owl:FunctionalProperty` | 0 |
| `owl:InverseFunctionalProperty` | 0 |
| `owl:intersectionOf` | 0 |
| `owl:complementOf` | 0 |
| `swrl:rule` | 0 |

**선행기술 판단 중심축 16항 가운데 추론 공리를 가진 것: 0 / 16**

| 항목 | 어휘 선언 | 추론 공리 |
|---|:--:|---|
| `ont:Claim` | 있음 | **없음** |
| `ont:ClaimFeature` | 있음 | **없음** |
| `ont:PriorArtJudgment` | 있음 | **없음** |
| `ont:hasClaim` | 있음 | **없음** |
| `ont:hasFeature` | 있음 | **없음** |
| `ont:isIndependent` | 있음 | **없음** |
| `ont:dependsOnClaim` | 있음 | **없음** |
| `ont:dependsOnFeature` | 있음 | **없음** |
| `ont:featureConcept` | 있음 | **없음** |
| `ont:hasJudgment` | 있음 | **없음** |
| `ont:aboutClaim` | 있음 | **없음** |
| `ont:overPriorArt` | 있음 | **없음** |
| `ont:onGround` | 있음 | **없음** |
| `ont:overlappingFeature` | 있음 | **없음** |
| `ont:hasPriorArt` | 있음 | **없음** |
| `ont:hasPriorArtExaminer` | 있음 | **없음** |

## ② 실체화 — 개념은 어디서 왔고, 한정요소에 얼마나 붙었는가

| | 값 |
|---|---:|
| 개념 노드 | 274 |
| **특허·거절 원천에서 유도된 개념** | **0** |
| 동의어 (ko / 전체) | 93 / 203 |

개념 출처 분포 — fmea_framework 60 · semikong 49 · vendor_public 42 · author 40 · wikidata 25 · matkg 20 · bis_ccl 11 · author-defined 11 · irds 8 · jedec 5 · semi_standards 3

| 표면형 사전 (`patent-text`) | 값 |
|---|---:|
| 표면형 | 635 |
| 한글 표면형 / `lang=ko` | 154 / 93 |
| 표면형을 가진 개념 | 274 |
| 차단 | R4-SHORT-KO-TASK 6, R6-SURFACE-SUPPRESS 2 |

| 한정요소 (중심축 투영) | 값 |
|---|---:|
| 한정요소 | 1,306,191 |
| 개념이 붙은 것 | 369,586 |
| **개념 0개 비율** | **71.71 %** |
| 독립항 한정요소 개념 0개 비율 | 73.44 % |
| 등장한 고유 개념 | 109 / 274 |

판단 축 전달 — 사이드카 TTL 벤더 **아니오** · 투영 parquet 도착. 판단 인스턴스(PriorArtJudgment)는 사이드카 TTL 에만 있고 투영 parquet 에는 한정요소만 담긴다 — 하류는 판단을 직접 셀 수 없다.

## ③ 작동 — 검색이 실제로 무엇을 쓰는가

| | 값 |
|---|---:|
| 코퍼스 문서 | 41,223 |
| 문서당 개념 (평균) | 3.726 |
| 개념 0개 문서 | 670 |
| 코퍼스에 등장한 고유 개념 | 199 |

| 순위 함수 항 | 가중 |
|---|---:|
| 개념 Jaccard (온톨로지 고유 · df 무가중) | 0.25 |
| 경로(PathSim) | 0.0 |
| IPC 분류코드 | 0.25 |
| FeatureCoverage (한정요소 원문 임베딩 코사인) | 0.5 |
| **공리에서 유도된 항** | **0** |

FeatureCoverage 는 한정요소 원문의 임베딩 코사인이고 IPC 는 분류코드다. 온톨로지 고유 항은 개념 Jaccard 하나이며 df 무가중이다.

---

**읽는 규칙.** 이 표는 진척을 재는 것이지 판정을 바꾸지 않는다(§1-2·§1-3). 원고의 수치·판정은 이 파일과 무관하게 그대로다. 값이 움직였다면 그것은 **새 자원**의 관측이며, 태스크 효과는 새 사전등록 아래 새로 검정한다(§2.1).
