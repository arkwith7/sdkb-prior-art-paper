# 상류 대기열 — CR 송부 순서와 상태 (2026-07-30)

> **받는 곳:** `~/Dev/sdkb` · **보내는 곳:** `~/Dev/SKKU/sdkb-prior-art-paper`
> 하류 §0.1 규약상 **CR의 정본은 하류에 있다.** 상류는 이 저장소의 파일을 **읽고** 구현하며
> 복사본을 만들지 않는다. 상류는 자신의 CLAUDE.md §2 게이트를 따로 갖는다 —
> TBox·IRI 변경은 상류에서 다시 승인받는다.

## 대기열

| 순서 | CR | 결함 | 하류 단계 | 상류 상태 | 비고 |
|---|---|---|---|---|---|
| 1 | [CR-004R](CR-004-rejection-basis-structure.md) | D-06 | 1·2·3 완료·승인 | **4단계 착수 가능** | 이관 내용 §1.1 · 입력 데이터 수집 완료 |
| 2 | [CR-007](CR-007-concept-linking-rules.md) | D-14·D-15·**D-16** | 1·2 완료 · **3단계 결정 4건 대기 🛑** | 대기 | **임계경로 선두** — CR-001의 선행 조건 |
| 3 | [CR-005](CR-005-tbox-logical-axioms.md) | D-03·D-09 | 1 완료 | **송부 가능(대기열)** | 아래 §2 |
| 4 | [CR-006](CR-006-tbox-module-boundaries.md) | D-13 | 1 완료 | **송부 가능(대기열)** | 아래 §2 |
| 5 | [CR-001](CR-001-concept-resolution.md) | D-01·D-04 | 1·2 완료 · 3단계 결정 2건 대기 🛑 | **보류** | CR-007 확정 후 개봉 |
| 6 | CR-002 · CR-003 | D-02·D-05 | 1 완료 | 보류 | CR-001과 함께 |

## 1.1 CR-004R 이관 내용 (1·2·3단계 완료·승인 — 상류는 4단계부터)

의견제출통지서 998건을 새로 수집해 거절근거 무라벨이 **600 → 1**이 됐다. 이 라벨을
`ont:RejectionReason`·`ont:PriorArtJudgment` 인스턴스로 실체화한다. **두 클래스는 T-Box에 이미
선언돼 있고 A-Box 인스턴스가 0건**이므로, 새 구조를 만드는 것이 아니라 **선언된 빈 구조를
채우는 것**이다. 새 어휘는 조항 개체 7개와 술어 5개뿐.

**하류에서 확정된 결정 — 뒤집지 말 것.** ⓐ 조항 개체는 **항(項) 단위**로 발행, 호(號)는 문자열
속성에 보존(가역성 — 뭉쳤다 쪼개면 기존 IRI 의미가 바뀐다) · ⓑ **기존 개체 5개의 IRI·의미·notation
불변**(`Rejection_ClarityScope` 포함) · ⓒ **회차를 PriorArtJudgment IRI에 넣지 않는다**(넣으면 기존
635 IRI가 전부 바뀜 — 회차는 RejectionReason 층에만) · ⓓ 표 파싱 우선, LLM은 62문서 폴백으로 강등.

**작업 목록.** ① `sdkb-patent.ttl` 조항 개체 7개 · ② 같은 파일 술어 5개
(`reasonGround`·`groundClause`·`noticeRound`·`noticeType`·`noticeDate` · 전부 domain =
`ont:RejectionReason`) · ③ `reextract_claim_judgments.py` — 통지서 txt union · 표 헤더
`거절이유가 있는 부분과 관련 법조항` 추가 · `_G29` → 전 조항 파서 · **시행령/시행규칙 배제 필터** ·
④ `build_abox_claim_features.py` — RejectionReason 인스턴스 발행(현행 0건)·ground 매핑 확장·
회차/문서출처 속성 · ⑤ SHACL(RejectionReason: `reasonGround` 1 · `groundClause` 1 ·
`noticeRound` ≥1 · `noticeType` ∈ {의견제출통지서, 거절결정서}) · ⑥ 손실 리포트(파싱 실패 55·
표 없음 7을 **건별로**) · ⑦ CHANGELOG 마이너 bump·하류 통보.

**목표 수치(2단계 실측 위 · 이하면 회귀).** 청구항×조항 연결 **≥95 %**(실측 95.5 % · 분모 999) ·
PriorArtJudgment 조립 **≥70 %**(실측 71.7 % · 분모는 **제29조 근거 보유 921건**, 999 아님) ·
RejectionReason 커버 출원 **≥950/999** · 조항 2종 이상 출원의 인스턴스 **≥2**(접힘 해소의 직접 증거) ·
**기존 PriorArtJudgment IRI 635개 전부 존속** · 교차태스크 CQ(em·tf·core) 통과율 하락 **0**(T3).

**입력 데이터 (이미 수집됨 · 재수집 불필요).**
`~/Dev/paper_data/data/processed/opinion_notices/` — `_index.json`(출원 1,000키 · 문서 999 ·
`docs[].sendNumber` = 회차 판별 키) · `txt/` 1,155건(텍스트층 존재 · 본문 평균 7,000자) · `pdf/` 1,155건.
기존 `rejection_decisions/structured/` 979건.

**함정 셋.** ① `sdkb-abox-claim-features.ttl`은 **하류 스냅샷에 없다** — 상류가 채워도 하류가
vendor 하지 않으면 G0는 계속 0건(§4 하류 작업 · 상류는 기다리지 않아도 된다) · ② **조항을 본문
어디서든 잡으면 안 된다** — 제63조·제47조 안내문구·제2조가 오검출된다. `[심사결과]` 표의
`관련 법조항` 칸에서만 읽는다(본문 전체 기준 제47조 645건 → 표 칸 기준 3건) · ③ `특허법 시행령
제6조제2호`는 항상 제45조에 부수한다 — 법령명 필터가 없으면 "제6조 50건" 유령 조항이 생긴다.

**수집 API 함정(재수집 시).** `IntermediateDocumentOPService`(의견제출통지) ·
`IntermediateDocumentREService`(거절결정) 모두 **검색 `advancedSearchInfo`는 0건**을 반환한다.
출원번호 직접 조회 **`pdfInfoV2`만 작동**한다. 2026-05에 475건이 0으로 나온 원인이 이것이었다.

## 1.2 왜 CR-007이 CR-001보다 앞인가 (2026-07-30 결정)

CR-007 §2단계 실측: 특허 전문 재추출로 커버리지를 2.33배 늘리면 **Skill 축 오링크가 3.2 % →
18.1 %로 5.7배** 커진다. 태스크축 링크의 98.9 %가 Tier-2 별칭 경유이고, Skill 축의 80.3 %를
표면형 5개(`챔버`·`가스`·`플라즈마`·`마스크`·`정렬`)가 만든다. **CR-001을 먼저 보내면 해상도와
오염이 함께 커진다.** 상세는 CR-007 §2단계 G1–G7 · 대장 §1.10.

## 2. CR-005·CR-006 — 임계경로 밖이고 작다 (상류가 CR-004를 하는 동안 병행 가능)

두 건 모두 **어휘를 만들지 않는다.** 서로 독립이며 CR-004와도 파일이 겹치지 않는다.

| | CR-005 (논리 공리) | CR-006 (모듈 경계) |
|---|---|---|
| 성격 | **공리 붙이기** — disjointWith·Asymmetric·Irreflexive·Functional·inverseOf | **파일 나누기** — `sdkb-expert.ttl` 신설, TechnologyNode → foresight |
| 바뀌는 것 | TBox 공리 + SHACL shapes | TBox 파일 구성 + 의존 검사 테스트 |
| **IRI** | 불변 | **불변**(이동만) |
| 진짜 산출물 | 공리 도입 시 드러나는 **기존 위반 목록** | core에 남은 태스크 전용 어휘 0 |
| 하류 합격선 | 결함주입 **F12(방향 역전) 0/9 → ≥7/9** | 기존 CQ 31개 통과 유지 · 릴리스 서명 총계 불변 |
| 주의 | 기존 그래프가 검증에 **실패하는 것이 목적**이다 — shape를 느슨하게 만들지 않는다(상류 §1.6) | 모듈화는 **변경 격리**를 주지 **신호 격리**를 주지 않는다 — "태스크 독립"을 주장하지 않는다 |

**CR-006의 미결 판단:** `FailureMode`를 core에 남길지 expert 모듈로 보낼지는 **상류 2단계에서
사용처를 세고** 정한다(하류 코퍼스에서 FailureMode 링크는 전체 개념 링크의 4.60 %).

## 3. 상류 세션 시작 프롬프트 (그대로 붙여넣기)

**CR-004R (1순위 · 즉시):**

```
하류(sdkb-prior-art-paper)에서 CR-004R 이 승인돼 넘어왔다.
이관 브리프: /home/arkwith/Dev/SKKU/sdkb-prior-art-paper/upstream/HANDOFF-QUEUE.md §1.1
정본 CR:    /home/arkwith/Dev/SKKU/sdkb-prior-art-paper/upstream/CR-004-rejection-basis-structure.md

두 파일을 읽고, 우리 CLAUDE.md §2 절차에 따라 4단계(구현) 착수 전
TBox·IRI 변경에 대한 승인을 나에게 요청하라. 하류에서 확정된 결정 ⓐ~ⓓ 는 뒤집지 않는다.
```

**CR-005 · CR-006 (대기열 · CR-004 이후 또는 병행):**

```
하류(sdkb-prior-art-paper)에서 CR-005·CR-006 이 1단계 요구정의 형태로 넘어왔다.
대기열:  /home/arkwith/Dev/SKKU/sdkb-prior-art-paper/upstream/HANDOFF-QUEUE.md
정본 CR: /home/arkwith/Dev/SKKU/sdkb-prior-art-paper/upstream/CR-005-tbox-logical-axioms.md
         /home/arkwith/Dev/SKKU/sdkb-prior-art-paper/upstream/CR-006-tbox-module-boundaries.md

두 건은 어휘를 만들지 않고 IRI 를 바꾸지 않는다. 우리 CLAUDE.md §2 절차대로
2단계(분석)부터 시작하라 — CR-005 는 공리 도입 시 드러나는 기존 위반 목록을,
CR-006 은 FailureMode 의 실제 사용처 계수를 먼저 산출하고 3단계 설계 승인을 요청하라.
```

## 4. 하류가 상류 완료 후 할 일 (상류는 하지 않는다)

- `vendor.py` VENDOR_FILES 갱신 — **`mappings/abox_term_aliases.json`(D-16)** ·
  `ontology/sdkb-abox-claim-features.ttl`(CR-004R) 추가 → `make vendor`
- CR-004R: D-06 검증치 재측정(A5 제거손실 ≠ 0 · T2 n≥20 집단 ≥ 4) · PLAN-031 §5.1 재산출
- CR-005: `make faults` 재실행 — F12 검출률 회신
- CR-006: `make gate` T3(교차태스크 CQ) 비회귀 확인
- CR-007: 정밀도 표본 200건 판정 · 해상도·축 점유율·검색(A8 부호) 재측정
