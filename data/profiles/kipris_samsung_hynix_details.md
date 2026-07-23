# 프로파일 — KIPRIS 삼성·SK하이닉스 상세 (초록+전체청구항 · §G1 Phase A · G₁ 선행기술 feature 축)
> 이 파일은 `python -m sdkb_paper.preprocess.profile --corpus samsung-hynix --details` 이 생성한다. 손으로 고치지 않는다.

## 1. 구조 (structure)

| 컬럼 | 의미 | dtype | 원천 |
|---|---|---|---|
| application_number | 출원번호 (하이픈 제거, 키) | str | KIPRIS applicationNumber |
| abstract | 초록 전문 → ont:abstractText | str | KIPRIS astrtCont |
| claims | 청구항 전문 리스트 (번호순, 선두번호 보존) | object(list[str]) | KIPRIS claim — 청구항당 1원소 |
| claim_count | KIPRIS 신고 청구항 수 (>len(claims)면 미적재) | int64 | KIPRIS claimCount |

키: `application_number` (병합 24,179건 = build_delta 병합필터와 동일 집합). **초록·청구항 원문은 그래프(gitignore·로컬 전용)에만 실체화되고 재배포하지 않는다 (§1.3).**

## 2. 형태 (shape)

| 항목 | 값 | 설명 |
|---|---|---|
| 상세 수집 특허 | 24,179 | 병합 특허 전량 (룰 OR 인식층 · 사용자 결정 2026-07-22) |
| 고유 출원번호 | 24,179 | 키 — 중복 0 |
| 청구항 보유 | 24,179 (100.0%) | FTO 자기완결성 |
| 초록 보유 | 24,179 (100.0%) | 선행기술 텍스트 대비 입력 |
| **claimText 트리플(예상)** | **371,267** | 청구항당 1트리플 (번호 보존) |
| claim_count 미적재 특허 | 52 | KIPRIS claimCount > 실제 청구항 수 (정직 계상) |

## 3. 기술통계 (descriptive)

### 특허당 청구항 수 (실제 적재 기준)

| 통계 | 값 |
|---|---|
| count | 24,179 |
| mean | 15.4 |
| std | 7.0 |
| min | 1 |
| median | 12 |
| max | 86 |

### KIPRIS 신고 claim_count

| 통계 | 값 |
|---|---|
| count | 24,179 |
| mean | 14.2 |
| median | 10 |
| max | 86 |
| 합계 | 343,742 |

## 4. 사용 목적 (purpose)

| 컬럼 | 논문에서 쓰이는 곳 |
|---|---|
| `claims` | `ont:claimText`(청구항당 1)·`ont:firstClaimText` → **claim-feature 분해**의 원천 (RQ2 선행기술조사 feature 대비 · §G1 Phase C `src_g1`) |
| `abstract` | `ont:abstractText` — 선행기술 텍스트 대비·설명 |
| `claim_count` | `ont:claimCount` — FTO 자기완결성 지표 (신고 대비 적재율) |
| `application_number` | 특허 IRI 키 (`data:patent/kr_…`) — G₀→G₁ 주 대비축 |

> **엣지 중립**: 이 데이터는 datatype 속성만 더한다 — `realizesProcess`·`concernsDevice` 엣지와 병합 특허 집합을 건드리지 않으므로 **H1 커버리지는 원리적으로 불변**이다 (회귀 테스트 `test_delta_details_are_edge_neutral`).
