# SPEC-006 · G₀ 데이터셋 온톨로지 as-built 인벤토리 (측정 기반)

| | |
|---|---|
| 지지하는 것 | **C1 자원**(공유 T-Box가 세 태스크를 표현) · 반복 조사 종식 / 논문 §3·§6.1 |
| 정본(측정 대상) | `data/processed/graph_v0.ttl` (105,588) · `data/processed/central_axis.oxstore` (11,606,318) |
| 원천 | 벤더 스냅샷 `data/external/sdkb/*.ttl` (SDKB 커밋 `d578bf3` · 미반영분 반영 `3429d66`) |
| 재측정 | §9 스크립트 (rdflib + pyoxigraph) |

> **이 문서는 "무엇이 실제로 적재되어 있는가"의 정본 기록이다.** 이전 인스턴스 구축의 정의·적재
> 내역이 남지 않아 매번 재조사하던 문제를 끝내기 위해, **실측값**으로 G₀와 claim-feature sidecar의
> as-built 상태를 고정한다. **모든 수치는 2026-07-26 측정값**이며 TTL/oxstore가 정본이다(문서와
> 어긋나면 실물이 옳다 · CLAUDE.md §1.1·§1.5). 값이 바뀌면 §9로 재측정해 이 문서를 갱신한다.
>
> 구 `SPEC-002`(baseline G₀ 동결·H1)는 커버리지 패러다임 문서로 **역사 참조**다 — 동결 거버넌스는
> v0.9 전환으로 폐지(`CLAUDE.md` v0.9 · [archive/CLAUDE-v05.md]). 자원 정의의 정본은 이 SPEC-006이다.

---

## 1. 서명

| 자원 | 트리플 | 파일 |
|---|---:|---|
| **G₀ 분석 그래프** | **105,588** | `data/processed/graph_v0.ttl` |
| **Claim-feature sidecar** | **11,606,318** | `data/processed/central_axis.oxstore` (pyoxigraph 온디스크) |

- sidecar는 rdflib 금지(11.6M) — **pyoxigraph로만** 조회(메모리 `central-axis-use-oxigraph-ondisk`).
- 특허 전문(abstract/claim/feature)은 `license_restricted`(KIPRIS 학술이용·비재배포) → gitignore,
  `make vendor`로 로컬 재생성. 커밋되는 것은 집계·식별자·해시뿐.

---

## 2. G₀ 클래스 인스턴스 인벤토리 (rdf:type 실측)

### 2.1 도메인 인스턴스 (태스크 뷰별)

| 뷰 | 클래스 | 인스턴스 |
|---|---|---:|
| **선행기술조사** | CitedPatent | 3,034 |
| | Patent | 1,000 (전량 RejectedPatent 겸함) |
| | RejectedPatent | 1,000 |
| | CPCSymbol / IPCSymbol | 3,504 / 2,655 |
| | RejectionType | 5 |
| **공유 코어** | Organization / Vendor | 351 / 340 |
| | SubProcess / Process | 38 / 11 |
| | Device | 34 |
| | Equipment / EquipmentModel / EquipmentClass | 41 / 29 / 11 |
| | Material | 20 |
| **전문가 매칭** | Problem | 226 |
| | ExpertCase / Expert | 163 / 110 |
| | FailureMode / RootCause / Mitigation | 25 / 20 / 20 |
| | Skill | 12 |
| **기술예측** | TechnologyReadinessLevel | 9 |
| | STEEPVEDimension | 7 |
| | OptionType | 5 |
| | TechnologyNode | 3 |
| | Metrology / Parameter | 3 / 5 |
| **규제·수출통제** | KRIndustrialTechRule | 14 |
| | EARRule | 9 |
| | NationalCoreTechnology / NCTField | 6 / 3 |

### 2.2 TBox 메타 (스키마 선언 — 인스턴스 아님)
Class 103 · ObjectProperty 97 · DatatypeProperty 81 · TransitiveProperty 2 · Ontology 7 · Concept 6 ·
Semiconductor 1 · Activity 1. (총 42 rdf:type 값 중 위 8종은 스키마 선언이다.)

---

## 3. G₀ 속성 사용 인벤토리 (실측 상위, 119종 중)

| 그룹 | 속성 (사용 수) |
|---|---|
| 분류 | `hasIPC` 13,857 · `hasCPC` 9,204 · `notation` 6,200 |
| 라벨 | `prefLabel` 5,526 · `altLabel` 1,022 · `label` 272 · `definition` 261 |
| 출처 | `license` 4,999 · `source` 4,992 · `wasGeneratedBy` 1,000 · `bibliographicCitation` 284 |
| **특허 본문** | `abstractText` 3,973 · `claimText` 2,197 · **`firstClaimText` 1,000** |
| **특허 서지** | `filingDate` 4,034 · `publicationDate` 1,000 · `publicationNumber` 1,000 · `applicationNumber` 1,000 · `patentOffice` 1,000 · `examinationStatus` 1,000 |
| **선행기술(qrel)** | `hasPriorArt` 3,485 · **`hasPriorArtExaminer` 2,534** · `rejectedFor` 414 |
| **개념링크** | `realizesProcess` 4,174 · `involvesMaterial` 2,068 · `concernsSkill` 1,994 · `involvesProcess` 432 · `concernsDevice` 430 · `exhibitsFailureMode` 86 |
| 전문가 | `hasEquipmentExperience` 903 · `hasSkill` 183 · `requiresSkill` 170 · 경력 datatype 22종(각 110) |
| 규제 | `complianceSensitivity` 226 · `complianceFlag` 110 · `hasNCT` 110 · `subjectToControl` 37 |
| foresight | `trlLevel` 9 · `concernsTechnologyNode` 1 |

전량 목록·수치는 §9 재측정으로 재현.

---

## 4. 질의·정답·후보의 실체화 위치 (반복 조사 종식 — 핵심)

**이 절이 이 문서의 존재 이유다.** 각 데이터가 *어디에* 있는지 명시한다.

### 4.1 질의 = 거절특허 1,000건 (전량 KR)
| 요소 | 술어·위치 | 커버리지 |
|---|---|---:|
| 제목 | `prefLabel` (G₀) | 1,000 |
| 초록 | `abstractText` (G₀) | 1,000 |
| 청구항 1 원문 | `firstClaimText` (G₀ 인라인) | 1,000 |
| **청구항 전체(독립+종속)** | **sidecar** `Claim(rej_*)`→`hasFeature`→`featureText` | 1,000 (13,679 청구항) |
| 서지·분류 | `filingDate`·`publicationDate`·`hasIPC`·`hasCPC` | 1,000 |
| 개념링크 | `realizesProcess`·`concernsDevice`·`involvesMaterial`·`concernsSkill` | 부분 |
| 거절근거 | `rejectedFor` → `RejectionType` | 414 엣지 |
| 정답 엣지 | `hasPriorArtExaminer`(2,534)·`hasPriorArt`(3,485) | — |

- **rej_ 청구항 13,679개 · 독립항 3,117개**(`isIndependent`=true) · feature 29,395개(전량 `featureText`).

### 4.2 정답(qrel) = 심사관 인용 선행기술
| 항목 | 값 | 위치 |
|---|---|---|
| 인용 엣지 | 2,534 (`hasPriorArtExaminer`) | G₀ |
| 고유 정답 노드 | 2,321 | G₀ `CitedPatent` |
| CitedPatent 총계 | 3,034 (출원인 인용 포함) | G₀ |
| 텍스트 | abstractText 93.3% · claimText 2,197 | G₀ 인라인 |
| 청구항 전체 | `Claim(cited_*)` 40,437 (특허 2,197) | sidecar |
| 등급2 판단 | `PriorArtJudgment` 635 (`aboutClaim`·`overPriorArt`·`onGround`) | sidecar |
| 출원인 인용 | `hasPriorArtApplicant` (분리 보존) | G₀ |

### 4.3 후보 코퍼스 = G1/G2 (전량 KR · ~40k 특허)
`Claim` 접두 분포(sidecar): **g1_ 371,267 · g2_ 161,184 · cited_ 40,437 · rej_ 13,679 = 586,567.**
후보 본문은 `graph_v1.ttl`(246MB)·`graph_v2.ttl`(116MB)의 `abstractText`·`claimText` + sidecar 청구항.

---

## 5. Claim-feature sidecar as-built (`central_axis.oxstore`)

| 항목 | 값 |
|---|---:|
| 총 트리플 | 11,606,318 |
| Claim | 586,567 |
| ClaimFeature | 1,289,300 |
| PriorArtJudgment | 635 |
| hasFeature / **featureText** | 1,289,300 / **1,289,300** (모든 feature에 텍스트) |
| isIndependent | 586,567 (독립/종속 명시) |
| dependsOnClaim / dependsOnFeature | 483,390 / 507,346 |
| aboutClaim / overPriorArt / onGround | 5,917 / 635 / 635 |

- **청구항 텍스트는 `claimText`가 아니라 `ClaimFeature.featureText`에 분해 저장**(`decompositionMethod`=rule,
  `featureSeq` 순서). 청구항 전체 텍스트 = 해당 Claim의 feature를 (claimNumber, featureSeq)로 이어붙여 재구성.
- Claim 노드 속성: `claimNumber` · `isIndependent` · `dependsOnClaim` · `hasFeature`. (원문 단일 문자열 없음)
- 이력: Tier1(rej 종속항)·Tier2(cited 종속항)·Tier3(g2 종속항)·G1 청구항축
  (메모리 `tier1/2/3-*`·`next-review-g1-claims-then-tier3`).

---

## 6. 언어 지형 (실측 — 다국어)
질의 1,000 = **한국어**. 후보 G1/G2 = **한국어 ~100%**. qrel 정답 2,321 = **한국어 57%(1,719 kr) ·
영어 39%(US 470·WO 79·CN 20·EP 12·JP영문MT 597) · 일본어 2%(67 jp원문)**. 다중언어 병기 노드 0건.
`dcterms:source "BigQuery Google Patents"` ≠ 영어(원어 저장). 상세 [PLAN-017 §1.6].

## 7. 분모 규율 (혼용 금지)
**2,534**(인용 엣지) ≠ **2,321**(고유 정답 노드) ≠ **2,211**(노드 도달) ≠ **584**(판단연결 표본).
도달성 사다리: 노드 95.3% · 의미(Process∪Device) 54.6% · +Material 63.4% · +전체의미 70.5% · +CPC/IPC 95.3%.

## 8. 텍스트·청구항 접근 레시피 (재조사 대신 이걸 보라)
- **질의 제목/초록**: G₀ `prefLabel`/`abstractText`.
- **질의 청구항1 원문**: G₀ `firstClaimText`.
- **질의/정답 청구항 전체**: sidecar `?p hasClaim ?c . ?c isIndependent ?i ; claimNumber ?n ; hasFeature ?f .
  ?f featureText ?t ; featureSeq ?q` → (n, q) 정렬 후 `?t` 이어붙이기. 독립항 = `?i=true`.
- **정답 등급2**: sidecar `PriorArtJudgment`(`aboutClaim`·`overPriorArt`·`onGround`).
- **후보 본문**: `graph_v{1,2}.ttl` `abstractText`/`claimText` + sidecar 청구항(g1_/g2_).

## 9. 재측정 (이 문서의 모든 수치)
```python
# G₀ 클래스·속성 census (rdflib, graph_v0.ttl 105,588 — 소규모)
import rdflib; from rdflib import RDF; from collections import Counter
g=rdflib.Graph(); g.parse("data/processed/graph_v0.ttl","turtle")
Counter(str(o).split('/')[-1] for o in g.objects(None,RDF.type))      # 클래스
Counter(str(p).split('/')[-1] for s,p,o in g if p!=RDF.type)          # 속성

# sidecar (pyoxigraph 온디스크 — rdflib 금지)
from pyoxigraph import Store
s=Store.read_only("data/processed/central_axis.oxstore")
s.query('SELECT (COUNT(?x) AS ?n) WHERE { ?x a <https://w3id.org/sdkb/ont/ClaimFeature> }')
```
값이 바뀌면 이 SPEC를 같은 커밋에서 갱신한다(§CLAUDE 데이터 프로파일 의무).
