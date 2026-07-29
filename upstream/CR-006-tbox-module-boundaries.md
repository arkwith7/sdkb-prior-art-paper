# CR-006 · T-Box 모듈 경계를 태스크 경계와 일치시킨다 (D-13)

> 제출처: `~/Dev/sdkb` · 양식: 상류 CLAUDE.md §2 **1단계 요구정의**
> 근거: `upstream/DEFECT-LEDGER.md` §1.8 · 논문 v0.9 §6.4 A8(전문가 계층 제거 −0.0316 · Holm 유일 유의)
> 우선순위: **P1** (P0 3건 직후)

```
목적      : "새 태스크를 위해 어휘를 추가해도 기존 태스크가 흔들리지 않는다"를
            **주장이 아니라 구조로** 만든다. 현재는 모듈 파일이 나뉘어 있고
            owl:imports 도 단방향으로 걸려 있으나, **경계가 태스크와 어긋나 있다.**

            실측 (동결 스냅샷):
              sdkb-core.ttl         클래스 56 · ObjectProperty 44
                → 도메인 공통 + **전문가매칭 어휘 전량**
                  (Expert · ExpertCase · Skill · Problem · RootCause · Mitigation · FailureMode)
                  + TechnologyNode(기술예측 일부)
              sdkb-patent.ttl       클래스 22 · ObjectProperty 31  (선행기술 — 유일하게 깔끔히 분리)
              sdkb-foresight.ttl    클래스  6 · ObjectProperty  6  (Scenario·STEEPVEFactor·RealOption 뿐)

            즉 **전문가매칭은 모듈이 아니라 코어**이고, patent·foresight 가 core 를
            owl:imports 하므로 모든 태스크가 그것을 무조건 상속한다. 이것이 하류
            음성 대조군 실패(전문가 계층 제거 시 검색 R@100 −0.0316, Holm 보정을
            통과한 유일한 절제)의 구조적 설명이다 — 음성 대조군으로 설계한 계층이
            실은 공유 코어의 일부였다.
            하류(§0) 전원. 특히 "새 태스크 뷰를 붙여도 기존 소비자가 깨지지 않는다"에 의존하는 모두.

입력      : ontology/ 의 모듈 파일과 그것을 만드는 scripts/build_owl.py
            현행 owl:imports 그래프(patent·foresight·rbv·commercialization·governance → core 단방향)

출력      : (1) `sdkb-expert.ttl` 신설 — Expert·ExpertCase·Skill·Problem·RootCause·Mitigation 을
                core 에서 분리 (FailureMode 는 §아래 판단 필요)
            (2) TechnologyNode 를 sdkb-foresight.ttl 로 이관
            (3) core 에는 **진짜 공통 도메인 어휘만** 남긴다 — Process·SubProcess·Device·
                Material·Equipment·EquipmentClass·Vendor 계열
            (4) 의존 규칙의 **자동 검사** — 태스크 모듈 → core 단방향, 태스크 모듈 상호 참조 금지.
                위반 시 make test 실패 (상류 §2 5단계(b) "생성기 → TBox" 경계 계약과 동층)
            바뀌는 것: TBox 파일 구성 + 테스트. **IRI 는 바뀌지 않는다(아래 파급).**

성공 기준 : ① core 클래스 56 → 도메인 공통만 남고, 태스크 전용 어휘가 0개
            ② 세 태스크 모듈이 서로를 참조하지 않음 (자동 검사가 강제)
            ③ **모든 IRI 불변** — 파일이 옮겨져도 `https://w3id.org/sdkb/ont#Expert` 는 그대로.
               릴리스 서명(클래스·술어 수)이 총계에서 변하지 않아야 한다
            ④ 기존 CQ 31개 전부 통과 유지 (모듈 분리는 의미를 바꾸지 않는다)
            ⑤ make validate · make test 통과

비목표    : 새 어휘를 만들지 않는다 — **이동과 선언만** 한다.
            "모듈화했으니 태스크가 독립적이다"라고 주장하지 않는다(아래 경계).
            새 태스크 모듈을 실제로 추가하는 실험은 이번 범위 밖.

파급      : **IRI 를 바꾸면 하류가 전부 깨진다.** 하류는 커밋 SHA + sha256 으로 핀하고
            SPARQL 이 IRI 를 직접 참조하므로, 이 CR 은 **파일 재배치와 선언 위치 변경**에
            한정한다. IRI·네임스페이스·의미는 불변이다. 그래도 owl:imports 그래프가
            바뀌므로 CHANGELOG 에 기록하고 하류 3곳에 통보한다.
```

## 경계 — 무엇을 주장할 수 있고 무엇은 못 하는가

**T-Box 모듈화는 "변경 격리"를 주지만 "신호 격리"를 주지 않는다.**

특허 A-Box 가 이미 전문가 어휘에 링크돼 있다 — 스냅샷 실측: `concernsSkill` 980건 ·
`exhibitsFailureMode` 73건(CitedPatent 3,034건 기준). 모듈을 갈라도 **검색 신호는 계속 섞인다.**
따라서 이 CR 이후에도 주장할 수 있는 것은:

| 주장 | 가능 여부 |
|---|---|
| **비간섭** — 새 태스크 어휘를 더해도 기존 태스크가 **나빠지지 않는다** | 이 CR 이 구조적 근거를 만든다 |
| **독립** — 태스크별 기여가 분리된다 | **주장하지 않는다.** H4·H5 에서 이미 기각됐고, 공유 지식기반의 취지상 목표도 아니다 |

**FailureMode 의 소속은 상류 2단계(분석)에서 판단할 것.** 고장모드는 전문가매칭의 문제 서술
어휘이면서 동시에 공정·소자 도메인의 물리 현상이다(어휘 55개가 전부 공정·소자 물리 결함).
공통으로 남길지 전문가 모듈로 보낼지는 **실제 사용처를 세고 나서** 정한다 — 하류 코퍼스에서
FailureMode 링크는 전체 개념 링크의 4.60%다.
