# CR-005 · T-Box 논리 공리와 방향성 SHACL 형상 (D-03 · D-09)

> 제출처: `~/Dev/sdkb` · 양식: 상류 CLAUDE.md §2 **1단계 요구정의**
> 근거: `upstream/DEFECT-LEDGER.md` §1.4 · 논문 v0.9 §6.5(F12 0/9 · 2회)·v1.1 §5.1·§7
> 우선순위: **P1**

```
목적      : "논리적으로 검증된 온톨로지"라는 주장의 근거를 만든다.
            현재 동결 스냅샷 전체(data/external/sdkb/*.ttl)의 공리 계수는 다음과 같다 —
              owl:disjointWith 0 · owl:AllDisjointClasses 0
              owl:FunctionalProperty 0 · owl:InverseFunctionalProperty 0
              owl:AsymmetricProperty 0 · owl:IrreflexiveProperty 0
              owl:inverseOf 0 · owl:cardinality/min/max 0
              owl:someValuesFrom 0 · owl:allValuesFrom 0 · owl:propertyDisjointWith 0
              owl:TransitiveProperty 2 · rdfs:domain 75 · rdfs:range 89
            **위반할 공리가 없으므로 어떤 그래프도 일관적이다** — L2(HermiT)는 공허하다.
            실증: 결함주입에서 서브공정 방향 역전(F12)이 두 차례 모두 0/9 로 미검출됐다.
            그래프를 거꾸로 뒤집어도 형식 검증이 통과한다는 뜻이다.
            하류(§0) 전원 — 특히 릴리스 게이트를 신뢰하는 모든 소비자.

입력      : ontology/ 생성기(scripts/build_owl.py) 와 그 원천 data/**
            validation/ 의 현행 SHACL shapes
            현재 클래스 41개(최대 깊이 4) · 술어 domain 75 / range 89

출력      : (1) TBox 공리 (build_owl.py 생성) —
                · 축 간 owl:disjointWith (Process ⊥ Device ⊥ Material ⊥ Equipment ⊥ FailureMode …)
                · 방향 술어에 owl:AsymmetricProperty + owl:IrreflexiveProperty
                  (hasSubprocess · valueChainStage 계열 · isDueTo · mitigatedBy)
                · 1:1 서지 속성에 owl:FunctionalProperty (filingDate · publicationDate ·
                  applicationNumber · publicationNumber · patentOffice)
                · 역관계 쌍에 owl:inverseOf (hasSubprocess ↔ subprocessOf 등)
                · 필수 관계에 카디널리티 제약
            (2) SHACL shapes (validation/) — 순환 금지 · 방향 위반 금지 · 필수 카디널리티.
                **shape 는 그것이 겨냥하는 실제 그래프에 걸어 실행한다**(상류 §4).
            (3) 공리 도입 시 드러나는 기존 위반 목록 — 이것이 이 CR 의 진짜 산출물이다.
            바뀌는 것: TBox + shapes

성공 기준 : 게이트 통과 형태로 —
            ① 방향 역전 델타(하류 F12 형)를 주입하면 make validate 가 **실패**한다
               (현재는 통과 — "실패해야 할 입력이 실패하는가", 상류 §2 5단계(b))
            ② 타입 모순(예: 한 인스턴스가 Process 이자 Device)을 주입하면
               HermiT 가 **비일관을 검출**한다 (현재는 검출 불가)
            ③ 정상 그래프에 대한 위양성 0 — 공리 도입 후 현행 릴리스가 그대로 통과하거나,
               통과하지 못하면 **그 위반이 진짜 결함이므로 원천을 고친다**
               (shape 를 느슨하게 만들지 않는다 — 상류 §1.6)
            ④ 하류 재검정에서 F12 형 결함 검출 0/9 → ≥ 7/9

비목표    : 표현력을 위한 표현력 — 검증에 쓰이지 않는 공리는 넣지 않는다.
            추론 기반 신규 관계 생성(entailment materialization)은 이번 범위 밖.
            OWL 프로파일 상향(EL→DL 등)이 필요하면 3단계에서 별도 승인.

파급      : TBox 변경 = 하류 전원 영향. 다만 기존 IRI·술어 의미는 보존되고
            제약만 추가되므로 **의미 변경이 아니라 의미 명시화**다.
            단, ③에서 기존 데이터 위반이 나오면 그것은 **데이터 결함의 발견**이며
            수정 규모에 따라 별도 CR 로 분리한다. CHANGELOG · 버전 · 하류 통보.
```

## 예상되는 저항과 답

**"공리를 넣으면 기존 그래프가 검증에 실패할 것이다."** — 그것이 이 CR의 목적이다. 지금 통과하는
이유는 그래프가 옳아서가 아니라 **검사할 것이 없어서**다. 실패는 진단의 시작이지 변경이 무가치하다는
뜻이 아니다(논문 v1.1 §6.5의 릴리스 정책 ⑧과 같은 원칙).

## 하류가 되돌려줄 측정

`make faults` — 결함주입 × 게이트 검출 매트릭스를 다시 만들어 회신한다. 특히 **F12(방향 역전)의
0/9가 깨지는지**가 합격선이다. 하류의 T3가 아니라 **상류의 L1·L2가 이 결함을 잡는 것이 정상**이며,
그렇게 되면 하류 게이트의 부담이 줄고 논문의 "L2 과소명세" 한계도 해소된다.
