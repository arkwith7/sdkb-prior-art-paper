# PLAN-013 · 온톨로지 품질검증 — T-Box · A-Box · SHACL · 기능적 CQ 확장

> **부분 유효 (v0.9).** 이 문서의 SHACL·CQ 품질검증 설계는 v0.9에서도 유효하다. 다만 본문의 "H1/H2"
> 언급은 구 커버리지/시계열 패러다임 라벨이며 **S1/S2**로 읽는다(v0.9 확증 가설 H1–H5와 다름).
> 기준: [../RECONCILIATION-v09.md](../RECONCILIATION-v09.md) §1.

*상태: **설계 승인 대기** · 지지 대상: RQ2 (태스크 지원 · 품질검증부는 v0.9 유효) / 논문 §2.2 · §4.2*

> 현재 이 저장소의 검증은 **특허 노드에만** 걸려 있다. SHACL shape 2개가 둘 다
> `sh:targetClass ont:Patent` 이고, CQ 8개가 전부 `특허 × (공정∪디바이스) × 시간` 축이다.
> H1/H2 를 검정하기에는 충분하지만, **"이것이 제대로 된 도메인 온톨로지인가"** 를 묻는
> §2.2(구조적·기능적 품질 평가)의 결과 자리(§4.2)를 채우기에는 부족하다.

## 0. 무엇이 상위인가 — **온톨로지가 논문보다 위다** (2026-07-14 사용자 재정의)

> **SDKB 는 이 논문 하나의 입력이 아니라 여러 연구가 딛고 선 baseline 이다.**
> 그것이 깨져 있으면 이 논문의 결과뿐 아니라 그 위의 다른 연구들도 함께 무너진다.
> 그러므로 이 프로젝트의 품질검증은 **논문을 지키기 위한 절차가 아니라, 최상의 반도체 도메인
> 온톨로지를 확보하기 위한 절차다.**

**따라서 결정 규칙은 단순하다:**

> **온톨로지에 결함이 발견되면 상류(`~/Dev/sdkb`)에서 고친다.
> 그 결과 G₀ 가 움직이면 이 논문은 처음부터 다시 시작한다.**
> 재vendor → G₀ 재동결 → 수집 재적용 → **H1·H2 전면 재실행.**

이것은 비용이지 손실이 아니다. **H1 이 이미 지지됐다는 사실은 보호 대상이 아니다.**
그 지지를 유지하기 위해 결함을 남겨두거나, 우회 패치를 쓰거나, 한계 각주로 덮는 것은
**목적과 수단을 뒤바꾸는 것**이다 (CLAUDE.md §0.1 "상류에서 고친다", §1.2 "가설에 유리하게
결과를 만들지 않는다"). 결함을 알고도 baseline 을 보존하면 그것이야말로 조작이다.

**결과가 뒤집히면 뒤집힌 대로 보고한다.** H1 이 새 G₀ 에서 기각되면 기각된 대로 쓴다.

### 0.1 심각도 분류 — 조치를 정하기 위한 것이지, 수정을 회피하기 위한 것이 아니다

| 등급 | 정의 | 조치 |
|---|---|---|
| **S1 · 치명** | 온톨로지가 **거짓을 주장**한다: TBox 비일관 / 불만족 클래스 / `range`·`domain` 위반 / 술어 의미 오용(이름과 값의 불일치) / 개념 축(Process·Device) 정의 오류 | **상류 즉시 수정** → G₀ 재동결 → 논문 재실행 |
| **S2 · 중대** | 사실은 맞으나 **태스크에 필요한 정보가 구조적으로 없다**: TBox 가 선언한 술어의 인스턴스 0건, 필수 링크 누락 | **상류 수정** (데이터 수집이 필요하면 별도 계획) |
| **S3 · 경미** | 선택적 속성 결측, 라벨 누락, 커버리지 편중 | 상류 백로그에 등록. **이번 재동결 사이클에 묶어 함께 고친다** |

> **어느 등급도 "G₀ 를 보호하기 위해 고치지 않는다"로 귀결되지 않는다.**
> 고치지 않는 유일한 사유는 **결함이 아니라는 판정**이다.

### 0.2 사전등록 — 진단 결과를 보기 전에 고정한다

수정의 정당성은 **결함 그 자체**여야지 H1 의 결과여서는 안 된다. 그래서 순서를 못 박는다.

1. **수정 목록을 H1/H2 재실행 전에 확정하고 커밋한다.** 재실행 결과를 보고 목록을 바꾸지 않는다.
2. **구 G₀ 의 결과를 지우지 않는다.** 논문에 구 G₀ / 신 G₀ 를 병기하고, 무엇이 왜 바뀌었는지 적는다.
   이는 은폐 방지이자, **온톨로지 품질이 결론을 어떻게 바꾸는가**라는 그 자체로 실린 결과다.
3. H1 의 **검정 방법·표본 단위·단측 여부는 불변**이다 (PLAN-005). 데이터만 갱신된다.

### 0.3 진단(A) 자체는 읽기 전용이다

측정은 그래프를 바꾸지 않는다. 상류 수정은 진단 결과를 함께 본 뒤 승인받아 착수한다.

---

## 1. 관찰된 사실 (설계의 근거 · 2026-07-14 실측)

### 1.1 검증 커버리지의 공백

| 층 | 현재 | 공백 |
|---|---|---|
| T-Box | HermiT **consistency** (`reasoner_gate.check_consistency`) | **불만족 클래스(coherence) 미검사** — TBox 에 모순 정의가 있어도 인스턴스가 없으면 통과 |
| A-Box (SHACL) | `ont:Patent` 만 | Process 11 · SubProcess 38 · Device 34 · Equipment 41 · Skill 12 · Material 20 · Vendor 16 · Organization 353 · IPCSymbol — **shape 0개** |
| CQ | 8개, 전부 특허×공정/디바이스×시간 | **인력 · 소부장 · 선행기술 축 0개** |

### 1.2 상류 SDKB 에 이미 shape 이 있다 (새로 발명할 필요 없음)

`~/Dev/sdkb/validation/shapes.ttl` · `shapes_patent.ttl` 의 `sh:targetClass`:

```
Patent(3) · Process/SubProcess/EquipmentClass(2) · RejectionReason · RejectedPatent
· IPCSymbol · FailureMode · ExtrinsicSemiconductor · Equipment · Dopant
· gov:StandardReference · gov:SCIPRule · gov:EARRule
```

이 저장소가 vendor 할 때 `ontology/*.ttl` 만 가져오고 `validation/` 을 안 가져왔다.
**새 shape 을 쓰는 것은 어휘 발명(CLAUDE.md §1.4)의 위험이 있으나, 상류 shape 을 vendor 하는 것은
없다.** 상류에서 가져온다.

### 1.3 인력·소부장 축은 G₀ 에 **이미 존재한다** — 질의가 없을 뿐

| 축 | G₀ 트리플 |
|---|---|
| 인력 | `ont:concernsSkill` **630** (특허→스킬) · `ont:requiresSkill` **18** (공정→스킬) · Skill 12 |
| 소부장 | `ont:involvesMaterial` **526** (특허→소재) · `ont:providedBy` **41** (장비→벤더) · `ont:usesMaterial` 30 · `ont:usesEquipmentClass` 10 · Equipment 41 · Material 20 · Vendor 16 |

> ⚠ **이 링크들은 G₀ → G₁ 에서 한 건도 늘지 않는다** (630→630, 526→526, 41→41).
> 병합한 특허 24,179건이 `realizesProcess`·`concernsDevice` 만 받기 때문이다.
> **따라서 CQ09/CQ10 은 G₀ = G₁ 로 나온다. 이것은 보강 효과가 아니라 커버리지 증거다.**
> 논문에 그 구분을 명시한다. 결과가 안 나온다고 링크를 만들어내지 않는다 (§1.2).

### 1.4 선행기술조사의 텍스트는 **이미 수집돼 있다** (재수집 불필요)

- `data/interim/patents_delta.parquet` (34,521행) · `patents_2005_2009.parquet` (29,415행) 에
  `abstract` · `invention_title` 컬럼이 **채워져 있다.** KIPRIS 가 `astrtCont` 를 처음부터 준다
  ([kipris_client.py:141](../../src/sdkb_paper/collect/kipris_client.py#L141)).
- [delta.py:80](../../src/sdkb_paper/ontology/delta.py#L80) 이 그 텍스트를 **IPC 매핑에만 쓰고 그래프에 싣지 않는다.**
  그래서 `ont:abstractText` 가 그래프에 0건이다. 데이터가 없어서가 아니다.
- **거절사유·인용문헌은 진짜로 0건이다** (`ont:rejectedFor` · `ont:hasPriorArt` · `ont:rejectionPassage`
  = 0, 상류 SDKB 전체에서도 0). 이것만 재수집 대상이며 **이 계획의 비목표**다 (→ PLAN-014).

---

## 1.5 진단 배터리 — SHACL 만으로는 부족하다

**형식적으로 완벽한데 값이 틀린 결함**이 가장 위험하고, SHACL 은 그것을 원리적으로 잡지 못한다.
전례가 이미 있다: SDKB 의 `filing_date` 가 실은 **공개일(open date)** 이었다. `xsd:date` 로
형식은 완벽했고 SHACL 은 통과했으나, **값의 의미가 이름과 달랐다** — H2 시계열 전체를 오염시키는
S1 급 결함이다. 그래서 진단을 6층으로 쌓는다.

| | 층 | 무엇을 잡는가 | 도구 |
|---|---|---|---|
| **D1** | TBox 일관성 | 모순된 공리 | HermiT (기존) |
| **D2** | TBox 정합성(coherence) | **불만족 클래스** — 인스턴스가 없어 조용히 통과하던 모순 | HermiT + `owl:Nothing` 동치 검사 (**신규**) |
| **D3** | ABox 구조 | 필수 속성·카디널리티·range 위반 | 상류 `validation/shapes.ttl` (**신규 적용**) |
| **D4** | **TBox 약속 이행** | TBox 가 선언했으나 **인스턴스가 0건인 술어·클래스** — "말만 있고 실물이 없는" 어휘 | 술어별 인스턴스 카운트 (**신규**) |
| **D5** | **값의 진실성** | **이름과 값이 불일치하는 술어** (filing_date=공개일 型). SHACL 이 원리적으로 못 잡는다 | 권위 원천(KIPRIS) 표본 대조 (**신규**) |
| **D6** | 기능적 충족 | 태스크 질문에 답하는가 | CQ 8 → 11 (아래 B·C1) |

**D5 가 이 진단의 핵심이다.** D1–D3 만 돌리고 "통과"라고 보고하는 것은 이전에 이미 한 번
실패한 방식이다.

---

## 2. 이 계획이 하는 것

> ⚠ **아래 §2 는 진단 이전의 설계다. §6(진단 결과)이 이를 부분적으로 무효화한다.**
> 특히 B 의 "ExpDataSet 을 그래프에 병합하지 않는다"와 C1 의 "G₀ 불변" 전제는 **폐기됐다** —
> 상류 SDKB 에 이미 인력·문제 A-Box(전문가 110 · 문제 226)와 선행기술 엣지 6,692건이 있고,
> 사용자가 이를 정식 인스턴스로 채택하기로 결정했기 때문이다(2026-07-14).
> **실행 계획은 §6.4 를 따른다.**

### A · 구조 검증 확장 (그래프 불변)

**A1.** 상류 `validation/shapes.ttl` · `shapes_patent.ttl` 을 vendor → `queries/shapes/upstream/`.
- `baseline.py` 는 `BASELINE_PARTS` **명시 리스트**로 5개 TTL 만 읽는다(glob 아님) → 스냅샷에
  파일이 늘어도 **G₀ 트리플 수는 불변**이다. 이것이 안전한 이유다.
- **정지 조건**: vendor 후 기존 5개 TTL 의 sha256 이 하나라도 바뀌면 **중단하고 보고한다.**
  상류 워킹트리가 동결(SDKB `ad7fe3d`) 이후 움직였다는 뜻이고, 그대로 두면 G₀ 가 조용히 이동한다.

**A2.** `reasoner_gate` 에 **coherence 검사** 추가 — 추론 후 `owl:Nothing` 과 동치가 된 클래스
(unsatisfiable class) 목록을 반환. 현재의 consistency 검사와 **분리 보고**한다.

**A3.** 상류 shape 을 G₀ · G₁ 에 걸어 **측정한다.**
> **위반이 나와도 데이터를 고치지 않는다.** 레거시 위반은 SDKB 의 품질 사실이고, G₀ 를 고치면
> H1 의 before 가 움직인다. 위반은 §4.2 표와 §5.3(한계)에 **그대로 싣는다.**
> 어느 shape 을 게이트로 승격할지는 **측정 결과를 보고 별도 승인**받는다.

### B · 기능적 CQ 확장 — 인력 · 소부장 (그래프 불변)

CQ 는 **태스크 요구에서 도출한다**(Grüninger & Fox). 이번 태스크 요구의 출처는
`~/Dev/kukkukpool/ExpDataSet` 의 **소부장 기업 실문제 226건**이다
(`company_type`: materials 133 · equipment 52 · parts 19).

| CQ | 질문 | 쓰는 술어 |
|---|---|---|
| **CQ09** | 특정 공정 단계의 문제를 해결하려면 **어떤 스킬**이 필요하며, 그 스킬을 다루는 **특허와 출원인**은 누구인가 | `requiresSkill` · `concernsSkill` · `realizesProcess` · `assignedTo` |
| **CQ10** | 특정 공정 단계에 쓰이는 **소재·장비**는 무엇이며, 그 **공급 벤더**와 관련 특허는 무엇인가 | `usesMaterial` · `usesEquipmentClass` · `providedBy` · `involvesMaterial` |

> **ExpDataSet 의 데이터는 그래프에 병합하지 않는다.** (a) 226건 중 122건이
> `synthetic_generated` 이고, (b) 어휘가 SDKB 와 달라(`AMAT_Centura` ↔ `ont:Equipment`) 정렬하려면
> 매핑을 발명해야 하며, (c) 그 매칭 실험은 **AFCP_EM 논문의 기여**다. 중복 게재를 만들지 않는다.
> ExpDataSet 은 **CQ 도출의 출처로만 인용**한다.

### C1 · 선행기술조사 CQ (G₁ 만 변경 · G₀ 불변)

**C1-a.** `delta.py` 가 `ont:abstractText` (초록) · `rdfs:label` (발명명칭)을 델타에 싣는다.
- **G₀ 는 손대지 않는다.** 델타(우리가 병합하는 특허)에만 추가된다 → H1 의 before 불변.
- H1(커버리지=`realizesProcess` 링크 수) · H2(시계열=`filingDate`+개념 링크)의 **입력은 불변**이다.
  그러나 **가정하지 않고 `make h1` · `make h2` 를 재실행해 동일 수치를 확인한다.**

**C1-b.** **CQ11 — 선행기술조사.** 아이디어를 (개념 IRI 집합 + 키워드)로 표현하면, 그 개념을
실현하면서 초록에 키워드를 포함하는 특허를 **출원일 오름차순**으로 반환한다.
- 순수 SPARQL(`CONTAINS`). **임베딩·LLM 유사도를 도입하지 않는다** — 결정성이 깨지고 §1.5 의
  재현성 규약을 위반한다.
- **시연 아이디어 3건을 결과를 보기 전에 고정**한다 (p-hacking 방지). 결과가 빈약해도 그대로 싣는다.

---

## 3. 성공 기준 (검정 가능한 형태)

| | 무엇이 나오면 성공인가 |
|---|---|
| A1 | 상류 shape 이 `queries/shapes/upstream/` 에 있고, **기존 5개 TTL 의 sha256 이 불변**이며 `make snapshot` 통과 |
| A2 | `reasoner_gate` 가 불만족 클래스 목록을 반환한다 (0개면 0개라고 보고) |
| A3 | G₀ · G₁ 의 클래스별 SHACL 위반 건수 표가 나온다. **위반이 있어도 성공이다** — 측정이 목적이다 |
| B | CQ09 · CQ10 이 G₀ 에서 **1행 이상** 응답한다. G₀=G₁ 이면 그대로 보고한다 |
| C1-a | `make h1` · `make h2` 재실행 결과가 **기존 수치와 완전히 동일**하다. 다르면 **실패**이며 되돌린다 |
| C1-b | CQ11 이 사전 고정한 아이디어 3건에 대해 선행 특허를 출원일 순으로 반환한다 |

## 4. 비목표 (스코프 방어선)

- **이 계획 안에서 상류를 고치지 않는다.** 진단은 진단으로 끝내고, 수정은 결함 목록을 함께 본 뒤
  **PLAN-014(상류 교정 · G₀ 재동결)** 로 분리한다. 진단과 교정을 한 덩어리로 하면 무엇을 왜
  고쳤는지 추적이 끊긴다.
- **ExpDataSet 을 그래프에 병합하지 않는다.** 매칭 성능(P@k · nDCG)을 측정하지 않는다.
- **거절사유·인용문헌을 수집하지 않는다** (→ PLAN-015 · 별도 승인).
- **임베딩·LLM 검색을 도입하지 않는다** (결정성 · 재현성).
- 새 SHACL shape 을 **작성하지 않는다** (상류 것을 가져다 쓴다 — 어휘 발명 금지).

## 6. 진단 결과 (2026-07-14 · 읽기 전용 실행)

### 6.1 구조는 건강하다 — 논리적 S1 결함 없음

| | 결과 |
|---|---|
| **D1** TBox 일관성 (HermiT) | **통과** |
| **D2** 정합성(coherence) | **불만족 클래스 0개** |
| **D5** 값의 진실성 (날짜) | **통과** — filingDate < publicationDate 1000/1000, 간격 중앙 **556일**(≈18개월). 과거의 `filing_date`=공개일 결함은 **상류에서 이미 교정됐다** |
| **D3** ABox SHACL (상류 shape) | 위반 **702건** — 전부 **Organization 351/353** 의 `dcterms:license`·`interpretationType` 결측 → **S2** (Process 49개는 다 갖고 있다. 출원인 보강 때 SDKB 자신의 provenance 규율을 안 지켰다) |

### 6.2 D4 — TBox 어휘의 **62%가 실물이 없다**

클래스 **50개 중 28개(56%)**, 술어 **93개 중 58개(62%)** 가 인스턴스 0건. 그 안에 모듈 셋이 통째로 있다:
**거절 모듈 · 선행기술 모듈 · foresight 모듈(Scenario·Signal·STEEPVE·RealOption — 전부 0).**
그 밖에 `hasNextStep` **0건**(공정 49개가 **순서 없는 라벨 집합**), `hasSubStep`(0) ↔ `hasSubprocess`(38) **중복 어휘**.

### 6.3 D6 — 사용자가 지목한 두 태스크: **둘 다 미구현. 실패의 성격이 정반대다**

#### 태스크 ① 소부장 문제 ↔ 인력 매칭 — **스키마 자체가 없다 (S1)**

| 검사 | 결과 |
|---|---|
| **사람을 표현할 클래스** | `Person`·`Expert`·`Engineer`·`Role`·`Competency` — **TBox 에 존재하지 않음.** 인스턴스 0 |
| 스킬 보유자 관계 (`hasSkill` 型) | **없음** |
| `ont:Skill` | **12개**: DOE Analysis · Metrology Analysis · Recipe Tuning · Endpoint Detection · Film Stress Control · Slurry Management · Overlay Optimization · Defect Analysis · Mask Engineering · Chamber Conditioning · Gas Chemistry · Plasma Diagnostics |
| 문제(FailureMode) → Skill **직접** 경로 | **끊김 (0)** |
| 문제 → 공정 → Skill **우회** 경로 | 도달 38 |
| Mitigation → Skill | 도달 8 |
| `requiresSkill` 를 가진 공정 | **11 / 49** (78% 공백) |
| 스킬 특허의 출원인 | 186 Organization — **기업이지 인력이 아니다** |

> ⚠ **위 표는 G₀(= vendor 된 TTL 5개)만 본 결과다. 상류를 열어보니 판정이 바뀐다 — §6.5 를 보라.**
>
> **정정**: 상류 SDKB 는 `make abox` 로 `sdkb-abox-experts-problems.ttl` 을 생성한다 —
> **Expert 110 · Problem 226 · 3,597 트리플.** 이 논문의 `vendor.py` 가 TTL 5개만 가져오면서
> **이 파일을 빼먹었다.** 인력 축은 "없는" 것이 아니라 **vendor 되지 않은** 것이다.
>
> **그러나 진짜 S1 결함이 그 안에 있다** — 아래 §6.5.

#### 태스크 ② 선행기술 특허 매칭 — **전 경로 끊김. 그러나 데이터는 원천에 있다 (S1, 그러나 재모델링으로 해결)**

| 경로 | G₀ |
|---|---|
| `Patent →hasPriorArt→ Patent` | **0** |
| `Patent →cites→ Patent` | **0** |
| `Patent →rejectedFor→ RejectionReason` | **0** |
| `Patent →abstractText` | **0** |
| `Patent →firstClaimText` | **0** |
| `Patent →rdfs:label` (명칭) | 1,000 |

**그런데 원천 `~/Dev/sdkb/data/patents/raw/semiconductor_industry_rejected_patents.jsonl` (1,000건) 에는 다 있다:**

| 원천 필드 | 실재 | 적재 |
|---|---:|---|
| **`ground_truth_examiner`** — **심사관이 인용한 선행기술** | **2,551건** (특허당 중앙 2 · 최대 10) | ✗ |
| `abstract` | 1,000 | ✗ |
| `claim1` / `claims_full` | 1,000 / **13,685 청구항** | ✗ |
| `examination_status` | 1,000 (`거절결정(일반)` 678 · `거절결정(재심사)` 304 …) | 문자열로만 |
| `rejection_decision.txt_path` | 430건 **선언** | JSONL 의 경로가 **stale**. 실물은 `data/patents/rejection_decisions/` 에 **441건 존재** |

특허 1,000건이 **전부 `ont:Patent`** 이고 `ont:RejectedPatent` 는 **0건**이다 — 거절특허 데이터셋인데.

---

### 6.5 상류를 열어보니 — **결함의 정체는 "지식이 parquet 에 갇혀 있다"였다**

`~/Dev/sdkb` 실측 (2026-07-14):

| 상류에 실재하는 것 | 규모 | 온톨로지 A-Box |
|---|---:|---|
| `data/patents/prior_art_edges.parquet` | **6,692 엣지** (examiner 2,504 · evidence_v2 656 · all 3,441) · 대상특허 **1,000** · 피인용 **3,822**. IRI 형태로 이미 정규화됨 (`patent:kr_…`) | ✗ **0** |
| `data/patents/rejection_decisions/structured/` | **441건** | ✗ **0** |
| SIRP 초록 / 청구항 | 1,000 / 13,685 | ✗ **0** |
| `ontology/sdkb-abox-experts-problems.ttl` (`make abox` 산출) | **Expert 110 · Problem 226 · 3,597 트리플** | △ **이 논문이 vendor 안 함** |
| `make compliance` (EAR · NCT 거버넌스 시드) | — | △ 미빌드 |
| 기존 파이프라인 | `build_prior_art_pairs.py` · `eval_prior_art_realgt.py` (**Recall@10/50 · MRR**) · 노트북 04·06·07 | 그래프 밖에서 동작 |

> **재수집이 필요 없다. 어휘를 발명할 필요도 없다.**
> SDKB 의 지식이 **parquet·json 에 있고 온톨로지 A-Box 로 올라오지 않았다.**
> `ont:hasPriorArt`·`ont:abstractText`·`ont:RejectedPatent` 는 TBox 가 **선언해 두었는데**
> 빌더(`build_abox_patents.py`)가 그 입력을 받지 않는다.

#### ⚠ 진짜 S1 — 인력·문제 어휘가 **A-Box 안에서 인라인 선언**된다

`sdkb-abox-experts-problems.ttl` 이 `owl:Class` **2개**와 `owl:ObjectProperty` **10개**를 A-Box
파일 안에서 선언한다. TBox(`sdkb-core.ttl`)에는 **0개**다 (실측: `grep -c` → 0):

`ont:Expert` · `ont:Problem` · `ont:hasSkill` · `ont:hasProcessExpertise` ·
`ont:hasEquipmentExperience` · `ont:hasMaterialExpertise` · `ont:involvesProcess` ·
`ont:involvesEquipment` · `ont:mitigationProvidesSkill`

**SDKB 자신의 CLAUDE.md §1.2 가 금지하는 행위다** — *"TBox 를 읽는 소비자에게는 존재하지 않는
술어가 되고, SHACL·추론기가 검증할 수 없다."* 특허 쪽에서 이미 겪고 고친 사고(상류 §8-2)를
인력·문제 쪽이 아직 안고 있다. **§6.3 이 "인력 스키마가 없다"고 판정한 원인이 이것이다 —
있긴 한데 검증 불가능한 자리에 있었다.**

### 6.4 결론 — 무엇을 고칠 것인가 (상류 3건 → G₀ 재동결 → 논문 재실행)

| | 할 일 | 등급 | 새 어휘 | 재수집 |
|---|---|---|---|---|
| **PLAN-014** | `build_abox_patents.py` 가 `prior_art_edges.parquet`(6,692)·초록·청구항1 을 읽어 `hasPriorArt`·`abstractText`·`firstClaimText`·`RejectedPatent`·`rejectedFor` 를 적재 | **S1** | **0** | **0** |
| **PLAN-015** | Expert/Problem 어휘 **12개를 TBox 로 승격** + SHACL shape. A-Box 내용은 불변 — **위치만 교정** | **S1** | 0 (이동) | 0 |
| **PLAN-016** | 이 논문 `vendor.py` 의 FILES 확대 — 인력·문제·거버넌스 A-Box 포함 | **S2** | 0 | 0 |
| 동반 | Organization provenance(351) · `hasNextStep`(0) · `hasSubStep`↔`hasSubprocess` 중복 · CPC 축 | S2·S3 | — | — |
| 별건 | foresight 모듈 0 인스턴스 (Scenario·Signal·STEEPVE·RealOption) | S2 | — | — |

**완료 후**: 재vendor → **G₀ 재동결** → 수집 재적용 → **H1·H2 전면 재실행** (§0 사전등록대로 구/신 G₀ 병기).

**얻는 것**: 선행기술 CQ 가 **시연이 아니라 정량 평가**가 된다 — 청구항 1을 질의로 넣고 반환된
선행기술을 **심사관 인용과 대조해 Recall@k · MRR** 을 잰다. 합성 정답이 아니라 **특허청 심사관의 정답**이다.

---

## 5. 논문 반영 위치

| 산출물 | 논문 위치 |
|---|---|
| T-Box consistency + coherence, A-Box SHACL 위반표 | **§4.2** (구조적 정합성) — 현재는 특허만 다룸 |
| CQ 8 → 11 확장, G₀/G₁ 응답 행수 | **§4.2** (CQ 응답률) · **부록 A** |
| CQ09/CQ10 이 G₀=G₁ 인 사실 | **§4.2** + **§5.3** (한계: 매핑 룰이 공정·디바이스 축만 만든다) |
| CQ11 선행기술 시연 | **§4.2** 또는 **§5.2** (실무적 시사점) |
| 거절사유·인용문헌 부재 | **§5.3** (한계) · **§5.4** (향후 연구) |
