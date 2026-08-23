# PLAN-074 Phase 0′ 계수 결과

**PLAN-074 §12 의 동결 설계로 실행한 계수다.** 범위는 dev 200질의뿐이며 qrel 을 읽지 않는다(D2).
개념 쌍은 개념 식별자로만 싣는다(§5-3).

## 판정

- **P_uniq = 3044** (문턱 400) · **Q_cov = 56.5%** (문턱 0.50) · **C_conf = 1249** (문턱 100)
- P_raw = 8,535 · 판단 단위 409
- **부차(D1 폴백 · 판정 비사용)**: P_uniq = 3,492 · Q_cov = 64.0% · P_raw = 10,990
- **판정(Prec 제외) = 통과** — `Prec` 은 사람 코딩 전이므로 미산출이며, §13 대로 그때까지 최종 판정은 *부분* 이다

## 유형별

| 유형 | P_uniq | 문턱 |
|---|---|---|
| 결합 | 1,157 | 250 |
| 설계변경 | 833 | 60 |
| 임계적 의의 | 576 | — |
| 치환 | 217 | — |
| 주지관용 | 261 | — |

## 단위 생성 계수

| 항목 | 수 |
|---|---|
| 유형 문단 | 459 |
| 두 지시 보유 | 326 |
| 지시 불충분 | 133 |
| 인용문헌 미해소 | 93 |
| 단위 폐기: 인용문헌 | 29 |
| 단위 폐기: 청구항 번호 | 1 |
| 쌍 폐기 · 인용 청구항 실물 없음 | 232 |
| 쌍 폐기 · 인용 개념 0 | 49 |
| 쌍 폐기 · 본원 개념 0 | 79 |
| 식별자 중복으로 버린 코퍼스 행 | 18 |

## Q_cov 차단 단계 (쌍이 0인 질의의 첫 차단점)

| 단계 | 질의 |
|---|---|
| 원천 없음 | 0 |
| 유형 문단 0 | 21 |
| 두 지시 문단 0 | 17 |
| 인용발명 정의줄 없음 | 9 |
| 식별자가 코퍼스에 없음 | 1 |
| 청구항 번호 범위 밖 | 0 |
| 인용 청구항 실물 없음(D1) | 19 |
| 인용 개념 0 | 2 |
| 본원 개념 0 | 18 |
| 차단 없음(쌍 있음) | 113 |
| (참고) 폴백을 허용하면 회복되는 질의 | 15 |

## 빈출 개념 쌍 상위 10

| 본원 개념 | 인용 개념 | 단위 빈도 |
|---|---|---|
| process:deposition | process:deposition | 78 |
| process:deposition | material:aluminum | 77 |
| process:deposition | material:tungsten | 61 |
| process:deposition | material:cobalt | 60 |
| process:deposition | equipment_class:process_chamber | 56 |
| process:deposition | material:sin | 54 |
| process:deposition | material:tin | 49 |
| process:deposition | material:process_gas | 48 |
| process:deposition | process:etch | 46 |
| process:deposition | process:diffusion | 46 |

정밀도 표본 100건은 `data/interim/plan074_precision_sample.tsv` 에 있다(원문을 담으므로 gitignore 경로다).
층 부족분 보충: 없음 · seed = 20260823.
