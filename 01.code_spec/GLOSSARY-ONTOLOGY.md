# 온톨로지 개념과 용어 정의

이 문서는 교과서가 아니다. **이 프로젝트에서 실제로 사고를 낸 개념들**을 정리한 것이다.
2026-07 에 터진 결함은 예외 없이 아래 용어들의 혼동에서 나왔다 — TBox 와 ABox 를 구분하지
못해서, `xsd:date` 가 어디까지 통하는지 몰라서, "SHACL 통과"를 "논리적으로 옳음"으로 읽어서.

각 용어에 **SDKB 실물 예시**와 **여기서 실제로 무엇이 깨졌는지**를 붙였다.

짝 문서: [GLOSSARY-SEMICONDUCTOR.md](GLOSSARY-SEMICONDUCTOR.md)(반도체 도메인) · [GLOSSARY-STATISTICS.md](GLOSSARY-STATISTICS.md)(통계). 이 문서가 *지식을 어떻게 표현하는가*라면, 그 둘은 *무엇을 표현하는가*(반도체)와 *어떻게 검정하는가*(통계)다.

---

## 1. 기본 골격 — 트리플, IRI, 그래프

**트리플(triple)** — 지식의 최소 단위. `(주어, 술어, 목적어)`.

```turtle
pat:kr_1020210184131   ont:filingDate   "2021-12-21"^^xsd:date .
#     주어(IRI)          술어(IRI)          목적어(리터럴)
```

**IRI (Internationalized Resource Identifier)** — 사물의 **전역 고유 이름**. URI(Uniform Resource
Identifier)를 확장해 ASCII 를 넘어 **유니코드**(한글·한자 등)까지 식별자에 쓸 수 있게 한 것(RFC 3987).
URL 처럼 생겼지만 **웹 주소일 필요는 없다** — 가리키는 것은 실체(특허·공정·회사)이지 문서가 아니다.
그래프의 모든 자원(주어·술어, 그리고 IRI 인 목적어)은 IRI 로 식별된다. **같은 실체는 같은 IRI 여야
하고, 다른 IRI 는 다른 실체다** — 이 등식이 깨지면 질의가 조용히 어긋난다(아래 사고 참조).
**리터럴(literal)** — 값 그 자체(문자열·날짜·수). IRI 가 아니다. **리터럴은 다른 트리플의 주어가 될 수 없다.**

**네임스페이스 / 접두어(prefix)** — 긴 IRI 를 줄여 쓰는 별칭. 이 프로젝트의 3분리(`config.py`):

| 접두어 | IRI | 무엇이 사는가 |
|---|---|---|
| `ont:` | `https://w3id.org/sdkb/ont/` | **TBox** — 클래스·술어(어휘) |
| `data:` | `https://w3id.org/sdkb/data/` | **ABox** — 인스턴스 |
| `pat:` | `https://w3id.org/sdkb/data/patent/` | 특허 인스턴스 서브트리 |
| `gov:` | `https://w3id.org/sdkb/gov/` | 거버넌스 모듈(이 논문 미사용) |

**그래프(graph) / 지식 그래프** — 트리플의 집합. 우리의 `graph_v0.ttl`(G₀) 은 49,307 트리플이다
(보강 후 G₁ 868,669 · G₂ 434,342 — 정본은 [CANONICAL-INDEX §1](CANONICAL-INDEX.md)).

**Turtle(`.ttl`)** — 트리플을 사람이 읽을 수 있게 적는 직렬화 형식. **RDF/XML**·**N-Triples** 는 다른 형식.
→ ⚠ **owlready2 는 Turtle 을 못 읽는다.** 그래서 L2 리즈너 게이트가 오래 죽어 있었다(§6).

### ⚠ 실제 사고 0 — 역할을 IRI 에 인코딩해 회사 하나가 11쌍으로 갈라졌다

상류가 같은 회사를 **역할별로 다른 IRI 접두사**에 넣고 있었다 — 공급사면 `vendor:samsung`,
출원인이면 `org:samsung`. 그러나 **회사는 하나의 실체**다. 역할은 `rdf:type` 이 말해야지 IRI 이름이
말하면 안 된다. 결과: 삼성이 **두 노드**로 갈라졌고(전체 11쌍), "이 공정의 장비 공급사와 그 회사의
특허 포트폴리오"(CQ13)는 두 IRI 를 조인하지 못해 **에러 없이 0행**을 냈다. 다른 IRI = 다른 실체이므로
그래프는 아무 모순도 없이 "그런 회사 없음"이라고 답한 것이다 — 가장 잡기 어려운 종류의 결함이다.

해결: 회사 노드를 `data:organization/` **한 스킴**에만 두고 역할은 타입으로 표현
(SDKB `mappings/org_identity_crosswalk.csv` 근거로 병합). IRI 만 합쳐서는 부족했다 — **prefLabel 도
회사당·언어당 하나**여야 CQ 가 회사를 다시 쪼개지 않는다(§4).

> **규칙: 회사 하나 = IRI 하나. 역할은 IRI 접두사가 아니라 `rdf:type` 이 말한다.** (CLAUDE.md §0 · 논문 §6.2)

---

## 2. TBox vs ABox — 이 프로젝트에서 가장 비싼 구분

| | **TBox** (Terminological Box) | **ABox** (Assertional Box) |
|---|---|---|
| 담는 것 | **어휘·스키마.** 어떤 클래스가 있고 어떤 술어가 허용되는가 | **사실·인스턴스.** 개별 특허·공정·기업 |
| 예 | `ont:Patent a owl:Class`<br>`ont:filingDate a owl:DatatypeProperty ; rdfs:range xsd:date` | `pat:kr_1020210184131 a ont:Patent ;`<br>`  ont:filingDate "2021-12-21"^^xsd:date` |
| SDKB 파일 | `sdkb-core.ttl` · `sdkb-patent.ttl` · `sdkb-foresight.ttl` (806 트리플) | `sdkb-core-data.ttl` · `sdkb-abox-patents.ttl` |
| 비유 | 데이터베이스의 **스키마** | 데이터베이스의 **행(row)** |

**클래스(Class)** — 개체의 종류. `ont:Process`, `ont:Patent`, `ont:Device`.
**인스턴스(instance) / 개체(individual)** — 클래스에 속하는 구체적 사물.
`data:process/etch`(식각 공정), `pat:kr_1020210184131`(특허 1건).
**타입 선언** — `rdf:type`(Turtle 에서 `a`). `pat:… a ont:Patent` = "이 특허는 Patent 클래스의 인스턴스다".

### ⚠ 실제 사고 1 — ABox 가 어휘를 발명했다

SDKB 의 특허 ABox 는 `ont:concernsProcess` 라는 술어를 **ABox 파일 안에서 인라인 선언**해 쓰고 있었다.
TBox(`sdkb-patent.ttl`)에는 그 술어가 **없었다.** 정작 TBox 는 같은 뜻의 `ont:realizesProcess` 를
정의해 두고 있었다.

결과: TBox 만 읽는 소비자에게 `concernsProcess` 는 **존재하지 않는 술어**였고, SHACL·추론기가
검증할 수 없었다. 1,558개 링크가 그렇게 떠 있었다.

> **규칙: 선언은 TBox 에서만 한다. ABox 는 사실만 적는다.** (CLAUDE.md §1.4 "어휘를 발명하지 않는다")

---

## 3. 술어(Property)의 두 종류 — 이걸 틀리면 range 위반이 난다

| | **ObjectProperty** | **DatatypeProperty** |
|---|---|---|
| 목적어 | **IRI** (다른 개체) | **리터럴** (값) |
| 예 | `ont:realizesProcess` → `ont:Process` | `ont:filingDate` → `xsd:date` |

**domain / range** — 술어의 정의역·치역. `ont:realizesProcess` 는 `rdfs:domain ont:Patent`,
`rdfs:range ont:Process` 다. 즉 **특허가 아닌 것에 붙이거나, 공정이 아닌 것을 가리키면 위반**이다.

### SDKB 특허 모듈의 실물 어휘 (`sdkb-patent.ttl`)

**DatatypeProperty** (값이 리터럴):

| 술어 | range | 비고 |
|---|---|---|
| `ont:applicationNumber` | `xsd:string` | 출원번호 |
| **`ont:filingDate`** | **`xsd:date`** | **출원일 — H2 시계열의 전제** |
| `ont:publicationDate` | `xsd:date` | 공개일 (≠ 출원일!) |
| `ont:patentOffice` | `xsd:string` | KR/US/… |
| `ont:examinationStatus` · `ont:publicationNumber` · `ont:processFamily` · `ont:valueChainStage` | `xsd:string` | |

**ObjectProperty** (값이 IRI):

| 술어 | range | 이 논문에서의 쓰임 |
|---|---|---|
| **`ont:realizesProcess`** | `ont:Process` | **H1 커버리지의 근거** |
| **`ont:concernsDevice`** | `ont:Device` | **H2 개념 축의 두 번째 축** |
| `ont:hasIPC` / `hasCPC` | `ont:IPCSymbol` / `CPCSymbol` | **H2 의 대조군**(코드 단위 시계열) |
| `ont:assignedTo` | `ont:Organization` | 출원인 — CQ08 |
| `ont:involvesMaterial` · `realizesEquipmentClass` · `concernsSkill` · `exhibitsFailureMode` · `concernsTechnologyNode` | 각 도메인 클래스 | 부가 링크 |
| `ont:hasPriorArtExaminer` · `hasPriorArt` · `cites` | `ont:Patent` | 선행기술(2단계 자산) |

### ⚠ 실제 사고 2 — 리터럴 vs IRI

ABox 가 IPC 를 `ont:primaryIpc "H01L 21/3065"` 처럼 **리터럴**로 적고 있었다. TBox 의 `ont:hasIPC` 는
**range 가 `ont:IPCSymbol`(IRI)** 인 ObjectProperty 다. 두 세계가 따로 놀았다.
→ IPC 를 `data:ipc/H01L21-3065` 라는 **인스턴스 노드**로 승격하고 `skos:notation` 으로 코드 문자열을 달았다.

---

## 4. 레이블 — `rdfs:label` 이 아니라 `skos:prefLabel`

SDKB 는 SKOS 어휘를 쓴다. **여기서 `rdfs:label` 을 쓰면 질의가 조용히 0행을 반환한다.**

| 술어 | 뜻 | 예 |
|---|---|---|
| `skos:prefLabel` | **대표 명칭** | `"Plasma Etch"@en` |
| `skos:altLabel` | 이명·번역 | `"플라즈마 식각"@ko` |
| `skos:notation` | 코드값 | `"H01L 21/3065"` (IPCSymbol) |

`"..."@en` 의 `@en` 은 **언어 태그**다. 언어 태그가 다르면 다른 리터럴이다.

---

## 5. 계층과 추론 — `SubProcess ⊑ Process`

**`rdfs:subClassOf`** — 클래스 포함 관계. SDKB 에는 `ont:SubProcess rdfs:subClassOf ont:Process` 가 있다.

**RDFS 추론(inference)** — 명시되지 않은 사실을 규칙으로 도출하는 것.
위 공리가 있으면, `plasma_etch a ont:SubProcess` 로부터 **`plasma_etch a ont:Process`** 가 자동으로 따라온다.

이것이 중요한 이유: `ont:realizesProcess` 의 range 는 `ont:Process` 인데, 특허가 **SubProcess** 를
가리켜도 위반이 아니다 — 추론 하에서 SubProcess 는 Process 이기 때문이다.
우리 `shacl_gate` 는 `inference="rdfs"` 로 검증한다.

> ⚠ 단, **SPARQL 은 추론하지 않는다.** `cq_runner` 는 추론 없이 질의하므로, CQ 는 두 층위를
> `VALUES (?stepType) { ont:Process ont:SubProcess }` 처럼 **명시적으로 열어야** 한다.

---

## 6. 검증의 세 층 — 각각 **다른 것**을 본다

이 셋을 뭉뚱그리는 것이 가장 흔한 오해다. **하나가 통과해도 다른 하나는 실패할 수 있다.**

| | **L1 · SHACL** | **L2 · 추론기(HermiT)** | **L3 · SPARQL/CQ** |
|---|---|---|---|
| 묻는 것 | "**필수 속성이 있는가**" | "**논리적으로 모순이 없는가**" | "**태스크 질문에 답할 수 있는가**" |
| 세계 가정 | **닫힌 세계**(없으면 위반) | **열린 세계**(없으면 그냥 모를 뿐) | — |
| 예 | 출원일이 없다 → **위반** | 출원일이 없다 → 문제 없음 | 시계열 질의가 0행 |
| 통과의 뜻 | 구조가 갖춰졌다 | 모순이 없다 | 질문에 답이 나온다 |

**SHACL(Shapes Constraint Language)** — 데이터가 지켜야 할 **모양(shape)** 을 선언하는 언어.

- `sh:NodeShape` — 하나의 제약 묶음
- `sh:targetClass ont:Patent` — 이 shape 를 **어떤 노드에 적용할지**
- `sh:minCount 1` / `sh:maxCount 1` — 개수 제약
- `sh:datatype xsd:date` — 리터럴의 타입
- `sh:class ont:Process` — 목적어가 그 클래스여야 함
- `sh:or ( … )` — 둘 중 하나면 통과 (우리 델타 shape 의 "공정 **또는** 디바이스")

**열린 세계 가정(OWA)** — OWL/추론기의 전제. "적혀 있지 않다"는 "거짓"이 아니라 **"모른다"** 이다.
그래서 **필수 속성 검사는 추론기가 아니라 SHACL 의 일**이다.

### ⚠ 실제 사고 3 — 리즈너가 처음부터 죽어 있었다

`reasoner_gate` 는 한 번도 동작한 적이 없었다. 세 가지가 겹쳐 있었다.

1. **owlready2 는 Turtle 을 파싱하지 못한다** (RDF/XML·N-Triples 만).
2. **HermiT 는 `xsd:date` 를 지원하지 않는다.** OWL 2 datatype map 에 `xsd:dateTime` 은 있지만
   `xsd:date` 는 **없다** → `UnsupportedDatatypeException`.
3. **`owl:imports`** 때문에 리즈너가 import IRI 를 HTTP 로 가져오려다 404 로 죽었다.

해결: **추론 전용 뷰**(RDF/XML 변환 · `owl:imports` 제거 · `xsd:date`→`xsd:dateTime` 승격)를 만들어
넘긴다. **원본의 `xsd:date` 는 손대지 않는다** — H2 시계열의 전제이고 L1 이 검사한다.

---

## 7. 역량질문(CQ)과 SPARQL

**역량질문(Competency Question)** — "이 온톨로지가 답할 수 있어야 하는 질문"(Grüninger & Fox, 1995).
온톨로지 평가의 **기능적(task-based)** 축이다. 초기 8개에서 태스크 도출(P1–P5)로 넓혀 현재
`queries/cq/*.rq` 에 **28개**를 SPARQL 로 정식화했다(CQ01–27 + CQ28 특허↔문제↔전문가).

**SPARQL** — 그래프 질의 언어. `SELECT … WHERE { ?s ?p ?o }`.

> **CQ 를 "G₀ 가 실패하도록" 만들면 안 된다.** CQ 는 **태스크 요구**에서 도출한다. G₀ 가 전부
> 답한다면 그것은 **발견**이지 설계 실패가 아니다. (실측 응답률 2026-07-23 재측정: G₀ **27/28** ·
> G₁ **28/28** · G₂ **28/28** · mini 28/28 — 지는 것은 G₀ 의 CQ27 FTO 청구항 하나뿐. 청구항 전문이
> 특허 보강 코퍼스에만 있어 baseline 만 떨어진다 → SPEC-003)

---

## 8. 이 프로젝트 고유의 용어

| 용어 | 뜻 |
|---|---|
| **G₀ (graph_v0)** | **보강 전 그래프** = 현행 SDKB(SIRP 특허 1,000건 포함). H1 의 "before" |
| **G₁ (graph_v1)** | 삼성 특허를 병합한 뒤의 그래프. H1 의 "after" |
| **SIRP** | Semiconductor Industry Rejected Patents — SDKB 2단계가 적재한 거절특허 1,000건 |
| **델타(delta)** | 그래프에 **넣으려는** 트리플 뭉치. 게이트는 델타를 검증한다 |
| **게이트(gate)** | 통과하지 못한 델타는 병합되지 않는 검문소. `merge_with_gate()` |
| **vendoring / 스냅샷** | 상류 SDKB 를 특정 커밋에서 **얼려서** 복사해 오는 것. `data/external/sdkb/` |
| **PROVENANCE** | 스냅샷의 출처(커밋 SHA)와 무결성(파일별 sha256) 기록. 이게 없으면 baseline 의 출처가 거짓이 된다 |
| **개념 축** | H2 의 집계 단위 = **Process(49) ∪ Device(34)**. HBM·GAA 는 공정이 아니라 디바이스다 |
| **관측 단위** | H1 의 표본 단위 = **공정 49개**(Process 11 + SubProcess 38). 복원 이전 20개 집합으로도 병기 검정한다 |
| **커버리지 C(s)** | 공정 단계 s 에 매핑된 특허의 존재/수. G₀ 는 49개 중 **20개 커버, 29개 공백**(C₀ 20/49) |
| **PROV-O** | 출처 표준 어휘. `prov:wasGeneratedBy`(어느 활동이 만들었나), `dcterms:source` / `dcterms:license` |

---

## 9. 자주 혼동되는 것 (사고 기록)

| 혼동 | 사실 | 대가 |
|---|---|---|
| IRI 접두사가 역할을 말한다(`vendor:`·`org:`) | **아니다.** 역할은 `rdf:type`, 회사 하나 = IRI 하나 | 삼성이 11쌍으로 갈라져 CQ13 이 0행 |
| ABox 에서 술어 선언 = 어휘 정의 | **아니다.** TBox 가 정의해야 검증 가능 | `concernsProcess` 1,558 링크가 검증 밖에 |
| `rdfs:label` | SDKB 는 **`skos:prefLabel`** | 질의가 조용히 0행 |
| `xsd:date` 는 어디서나 통한다 | **HermiT 는 못 다룬다** (OWL 2 map 밖) | L2 게이트가 죽어 있었음 |
| SHACL 통과 = 논리적으로 옳음 | **다른 검사다** (닫힌 세계 vs 열린 세계) | 3층이 필요한 이유 |
| 컬럼 이름이 곧 의미 | **아니다.** `filing_date` 에 **공개일**이 들어 있었다 | 시계열이 1~2년 밀릴 뻔 |
| Device = Product | **아니다.** HBM(기술 아키텍처) ≠ 삼성 HBM3E(상용 제품) | 시장 데이터와 기술 데이터가 섞임 |
| 특허가 공정에 안 걸리면 결함 | **아니다.** IPC 가 소자(G11C·H10B)를 지시하면 그게 사실 | 억지 매핑 = 날조 |

---

## 10. 약어

**TBox** Terminological Box · **ABox** Assertional Box · **IRI** Internationalized Resource Identifier ·
**RDF** Resource Description Framework · **RDFS** RDF Schema · **OWL** Web Ontology Language ·
**SHACL** Shapes Constraint Language · **SKOS** Simple Knowledge Organization System ·
**SPARQL** SPARQL Protocol and RDF Query Language · **PROV-O** Provenance Ontology ·
**CQ** Competency Question · **OWA** Open World Assumption ·
**IPC/CPC** International / Cooperative Patent Classification
