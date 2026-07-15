# PLAN-015 · 규제·컴플라이언스 축 — 수출통제 인스턴스 적재 (B 최소 실증)

*상태: **설계 대기** (사용자 지시 · 2026-07-15) · 지지 대상: **RQ3(소부장 IP-R&D)** · 논문 §4.6 · §5.3*
*선행: [PLAN-014](PLAN-014-ipr-d-framework-and-portability.md) §4 단계 3·4 완료 (CQ 게이트 커버리지 100%)*

> **사용자 결정 (2026-07-15)**: 규제 축을 **한계로 남기지 않고 최소 실증한다.**
> 근거 데이터는 실재한다 — `~/Dev/kukkukpool/ExpDataSet/us_compliance_standards_v1.json`
> (미국 EAR/CCL 수출통제 마스터 정의). 이것을 **온톨로지 인스턴스로 생성**하고, 그 위에서
> "이 기술을 이 나라에 이전하려면 규제가 걸리는가"를 질의 가능하게 만든다. RQ3 의 소부장
> 기업이 해외 협력할 때 **수출통제 심사가 실무의 핵심**이기 때문이다.

---

## 0. 왜 이 계획이 필요한가 — 측정된 공백 (2026-07-15 실측)

규제 어휘는 온톨로지에 **반쯤** 실려 있다. 세 층으로 잰 결과:

| 층 | 상태 | 실측 |
|---|---|---|
| **TBox (선언)** | ✅ 풍부하다 | `gov:` 모듈 두 파일. `EARRule`·`RegulatedItem`·`StandardReference`·`NCTField`·`NationalCoreTechnology` 클래스, `designatedAsNCT`·`hasJurisdiction`·`requiresGovApproval`·`standardRef` 속성. 규칙 앵커(`Rule_BIS_744_23`·`Rule_KR_ITPA_Art11`)까지 |
| **ABox (인스턴스)** | ⚠ **비어 있다** | `designatedAsNCT` 링크 **0** · `RegulatedItem` **0** · `StandardReference` **0**. 즉 **어느 공정·소자·특허도 규제에 연결돼 있지 않다** |
| **SHACL (제약)** | ⚠ **죽어 있다** | `gov:Shape_NCTLeakage`(정교한 SPARQL 누출 shape)가 있으나 걸릴 데이터가 0이라 **vacuous**, 게다가 `make validate`(상류)·`make gate`(논문)가 이 파일을 **돌리지 않는다** |

**핵심**: "이 기술은 국가핵심기술/수출통제 대상인가? 이 특허를 해외 기업에 이전하려면 승인이
필요한가?" 를 물으면 규칙은 있는데 **에러 없이 0행**이 나온다 — PLAN-014 가 반복해서 잡은
바로 그 패턴(CQ 도 데이터 흐름도 심문하지 않으면 축이 빈 채로 있다)의 규제 버전이다.

또한 이 축은 **논문 G₀ 에 아예 들어오지 않는다** — `sdkb-governance*.ttl` 이 vendor 스냅샷
(`data/external/sdkb/`)에 **없다**. `ont:complianceFlag`(110)·`complianceSensitivity`(336)만
Expert/Problem 을 통해 새어 들어와 있고, 그것은 규제 규칙 체계와 **연결되지 않은 별개 플래그**다.

---

## 1. 근거 데이터 — `us_compliance_standards_v1.json` (관찰 완료 · 2026-07-15)

`~/Dev/kukkukpool/ExpDataSet/us_compliance_standards_v1.json` (11.6 KB · `jurisdiction: US_EAR`).
**마스터 정의**이며, `extensibility.db_seed_mapping` 이 `data/compliance/…` → DB 시딩 흐름을 명시한다.

### 1.1 구조 (실측)

| 최상위 키 | 내용 | 온톨로지 대응 |
|---|---|---|
| `legal_framework` | EAR/ECRA/Wassenaar/ECCN/Entity List · 벌칙(§764) · 라이선스 유형(NLR/예외/개별) | `gov:EARRule` 앵커 · `dcterms:bibliographicCitation` |
| `jurisdiction_trigger_rules` | 적용 조건 · `country_group_map`(A_ALLIES/D1/E1/E2) | `gov:hasJurisdiction` · **국가군은 신규 어휘 판단 필요** |
| `deemed_export_rule` | EAR §734.13 — 외국국적자 국내 기술제공 = 수출 간주 | **신규 어휘 판단 필요** (전문가 국적 축) |
| `technology_controls` | **8건** — 기술↔ECCN↔통제수준↔수출제한 | **이 계획의 본체** (아래) |
| `country_authorization_by_jurisdiction` | 국가군 요약 | 참조 |
| `extensibility` | 계획된 관할(JP/EU/NL/TW) · 시드 매핑 | RQ3 재현성의 근거 |

### 1.2 `technology_controls` 8건 — 개념 연결 가능성

| tech_keyword | category | control_level | ECCN | **G₀ 개념 연결** |
|---|---|---|---|---|
| `CCL_3A001` | Semiconductor | CRITICAL | 3A001.a.1 | GAA·FinFET·nanosheet (device/gaa_fet · finfet) · ≤16nm |
| `CCL_3B001` | Semiconductor | HIGH | 3B001.a | EUV·DUV·ALE·ALD 장비 (equipment_class) |
| `EUV_Process` | Semiconductor | HIGH | 3B001.a.2 | subprocess/euv_lithography · EUV pellicle/resist (material) |
| `Advanced_Metrology` | Semiconductor | HIGH | 3B001.f | CD-SEM·OCD (metrology/cd_sem) |
| `CCL_3E001…Tech` | Semiconductor | HIGH | 3E001 | DRAM·NAND·Foundry **기술 자체**(know-how) — 개념 축 |
| `Legacy_CCL_Low` | Semiconductor | LOW | EAR99 | ≥28nm — 통제 대상 아님(음성 사례) |
| `EAR_Deemed_Export_CN` | Compliance_Rule | HIGH | N/A | 규칙(기술 아님) — 전문가 국적 축 |
| `BIS_Entity_List` | Compliance_Rule | CRITICAL | N/A | 규칙 — Huawei·SMIC·CXMT·YMTC |

**6건이 G₀ 의 개념(공정·소자·장비·계측·재료)에 직접 연결된다.** 2건은 규칙(개념이 아니라 절차)이다.

> **연결 근거가 이미 그래프에 있다.** GAA·FinFET·EUV·CD-SEM 는 PLAN-004 의 신기술 인식 레이어와
> 계측 축이 G₀ 에 실체화해 둔 개념이다 — 억지 매핑이 아니라 **ECCN 조건(아키텍처·해상도·nm)이
> 우리 개념 정의와 겹친다.** 겹치지 않는 것은 연결하지 않는다 (§1.2 날조 금지).

---

## 2. 🛑 결과 전에 결정해야 할 것 (설계 게이트)

### 2.1 어휘 — 발명하지 않는다 vs 상류 확장

`gov:` TBox 로 **대부분 표현된다**: ECCN 항목 → `gov:RegulatedItem`, EAR 규칙 → `gov:EARRule`,
관할 → `gov:hasJurisdiction`, 국가핵심기술 → `gov:designatedAsNCT`. 그러나 **미대응 개념 4개**:

| 데이터 개념 | gov: 대응 | 판단 |
|---|---|---|
| `control_level` (CRITICAL/HIGH/LOW) | 없음 | 상류에 `gov:controlLevel` 신설? **사람 승인** (CLAUDE.md §1.4) |
| `country_group_map` (A/D1/E1/E2) | 없음 | 국가군을 노드로? 아니면 규칙 속성 문자열로? |
| Deemed Export (전문가 국적) | 없음 | Expert 에 국적 축이 없다 — 범위 밖일 수 있다 |
| Entity List 기업 | `gov:` 없음 · `Organization` 있음 | 기존 회사 노드에 `gov:` 플래그? |

> **🛑 이것이 다음 세션의 첫 정지선이다.** 어휘를 발명하지 않는다는 규약(CLAUDE.md §1.4)과,
> 상류 SDKB 를 고쳐야 결함을 우회하지 않는다는 규약(§0.1)이 여기서 만난다. **G₀ 는 동결돼
> 있으므로** 규제 인스턴스를 G₀ 에 넣으면 H1 의 before 가 움직이는지부터 확인해야 한다
> (규제는 특허↔공정 링크를 건드리지 않으므로 **C₀ 불변일 것으로 예상**하나, 결과 전에 선언한다).

### 2.2 어느 그래프에 넣는가 — G₀ vs G₂ vs 별도 레이어

규제 인스턴스는 **개념(공정·소자)에 붙는다**. 개념은 G₀ 에 있다. 그러나:
- G₀ 에 넣으면 재동결 필요 · H1 불변 확인 필요 (트리플 증가는 라벨 교정처럼 净 링크 0 예상)
- **대안**: 규제를 RQ3 의 **G₂(소부장) 레이어**에 얹는다 — 소부장 IP-R&D 가 실사용처이므로.

> **사용자 지시가 "RQ3 에서 활용"이므로 G₂ 트랙이 자연스럽다.** 단 규제↔개념 링크는 G₀ 의
> 개념을 참조하므로, G₀ 를 건드리지 않고 **델타로 얹는 것**이 동결을 지킨다. 이 배치를 2단계에서 확정.

### 2.3 라이선스·재배포

`us_compliance_standards_v1.json` 은 `~/Dev/kukkukpool` 소유다. **공개 법령(EAR·CFR)에서 파생된
공지 사실**이라 집계·인스턴스화는 가능해 보이나, 원본 재배포 조건을 `data/MANIFEST.md` 절차대로
확인한다 (CLAUDE.md §1.3). 커밋되는 것은 **인스턴스 트리플**이지 원본 JSON 이 아니다.

---

## 3. 작업 순서 (다음 세션 · 5단계 게이트 준수)

| | 단계 | 산출물 | 정지선 |
|---|---|---|---|
| **1** | **어휘 결정** (§2.1) — gov: 로 표현되는 것 / 상류 확장이 필요한 것 (control_level·country_group·deemed_export·entity_list) 을 표로 확정하고 **사람 승인** | 어휘 매핑표 | 🛑 신규 술어는 승인 없이 안 쓴다 |
| **2** | **배치 결정** (§2.2) — G₀ 델타 vs G₂ 레이어. G₀ 를 참조하되 동결을 깨지 않는 방식 | 데이터 흐름 설계 | 🛑 G₀ 재동결이면 H1 불변 사전선언 |
| **3** | **로더 구현** — `collect/compliance.py`(원천 읽기) + `ontology/compliance.py`(인스턴스 빌더). 6개 Semiconductor 항목을 G₀ 개념에 연결 · 2개 규칙을 `gov:EARRule` 앵커로 | 인스턴스 TTL + 데이터 프로파일 (§4 의무) | — |
| **4** | **CQ 도출** (프로토콜 P1–P5) — "이 기술을 이 나라에 이전하려면 규제가 걸리는가" · "이 특허는 수출통제 대상인가" · "이 전문가(국적)가 이 기술을 자문할 수 있는가(Deemed Export)". **G₀ 에서 응답 확인** (역설계 금지) | CQ23–2x | 사전선언: G₀=규제레이어 전후 |
| **5** | **SHACL 살리기** — `gov:Shape_NCTLeakage` 를 걸릴 데이터가 있는 살아있는 게이트로. `make validate`/`make gate` 에 배선 (지금 세 번째 vacuous shape 파일이다) | 게이트 배선 + 역방향 테스트 | 🛑 검사되지 않는 shape 은 shape 이 아니다 |
| **6** | **논문 반영** — §4.6(RQ3)에 규제 지원 · §5.3 에 "규제 축을 TBox→ABox→살아있는 게이트로 완성" · 어휘 검증 커버리지에 gov: 축 추가 | 논문 + vocab 리포트 | — |

## 4. 사전등록 — 결과 전에 고정

> **규제 인스턴스는 특허↔공정 링크를 더하지 않는다 → C₀ 불변 · H1 p 불변 예상.**
> 라벨 교정·정체성 통합과 같은 부류다(개념 축에 속성만 더한다). **움직이면 그 자체가 결과**이므로
> 재동결 시 H1 네 표본집합을 재실행해 병기한다.
>
> **규제↔개념 연결은 ECCN 조건과 개념 정의가 겹칠 때만 한다.** GAA(≤16nm·GAA 아키텍처)처럼 근거가
> 명확한 것만 연결하고, 애매한 것은 **연결하지 않는다** — "규제받는 기술이 많아 보이게" 만드는 것은
> §1.2 위반이다. 6개 Semiconductor 항목 중 실제 연결 수는 결과로 보고한다.

## 5. 얻는 것 (RQ3 와의 접점)

- **RQ3 의 실무 완성도**: 소부장 기업이 "우리 EUV 공정 특허를 중국 기업에 라이선스해도 되나"를
  물으면 온톨로지가 **ECCN 3B001·D:1 그룹·개별허가 필요**를 답한다. IP-R&D 의 수출통제 심사.
- **프레임워크 재현성의 두 번째 증거**: `extensibility.planned_jurisdictions`(JP/EU/NL/TW)가
  같은 스키마로 확장된다 — CQ 도출 프로토콜이 **또 다른 코퍼스(규제)에서 재현**됨을 보인다.
- **vacuous gate 서사의 완결**: CQ(기능)·SHACL(구조)에 이어 **규제 게이트**까지 살리면,
  "선언은 있으나 검증되지 않던 축"을 세 종류 모두 실증으로 닫는다.

## 6. 비목표

- **전 세계 관할 구현 안 함** — US_EAR 하나로 최소 실증. JP/EU 등은 재현성 근거로 **언급만**.
- **Deemed Export 의 전문가 국적 축**은 Expert 에 국적 데이터가 없으면 **범위 밖**으로 명시.
- **규제를 H1/H2 에 끌어들이지 않음** — 규제는 RQ3 태스크 지원이지 커버리지·시계열 가설이 아니다.
- **어휘 발명 금지** — control_level 등 신규 술어는 1단계에서 승인받고, 못 받으면 문자열 속성으로.
