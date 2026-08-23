# PLAN-074 Phase 0′ 계수 결과

**PLAN-074 §12 의 동결 설계로 실행한 계수다.** 범위는 dev 200질의뿐이며 qrel 을 읽지 않는다(D2).
개념 쌍은 개념 식별자로만 싣는다(§5-3).

## 판정

- **P_uniq = 2149** (문턱 400) · **Q_cov = 48.5%** (문턱 0.50) · **C_conf = 803** (문턱 100)
- P_raw = 5,253 · 판단 단위 363
- **부차(D1 폴백 · 판정 비사용)**: P_uniq = 2,845 · Q_cov = 59.0% · P_raw = 7,976
- **판정(Prec 제외) = 부분** — `Prec` 은 사람 코딩 전이므로 미산출이며, §13 대로 그때까지 최종 판정은 *부분* 이다

## 유형별

| 유형 | P_uniq | 문턱 |
|---|---|---|
| 결합 | 783 | 250 |
| 설계변경 | 570 | 60 |
| 임계적 의의 | 422 | — |
| 치환 | 168 | — |
| 주지관용 | 206 | — |

## 단위 생성 계수

| 항목 | 수 |
|---|---|
| 유형 문단 | 459 |
| 두 지시 보유 | 326 |
| 인용문헌 미해소 | 284 |
| 지시 불충분 | 133 |
| 단위 폐기: 인용문헌 | 69 |
| 쌍 폐기 · 인용 청구항 실물 없음 | 178 |
| 쌍 폐기 · 인용 개념 0 | 55 |
| 쌍 폐기 · 본원 개념 0 | 66 |
| 식별자 중복으로 버린 코퍼스 행 | 19 |

## Q_cov 차단 단계 (쌍이 0인 질의의 첫 차단점)

| 단계 | 질의 |
|---|---|
| 원천 없음 | 0 |
| 유형 문단 0 | 21 |
| 두 지시 문단 0 | 17 |
| 인용발명 정의줄 없음 | 9 |
| 식별자가 코퍼스에 없음 | 17 |
| 청구항 번호 범위 밖 | 0 |
| 인용 청구항 실물 없음(D1) | 26 |
| 인용 개념 0 | 4 |
| 본원 개념 0 | 9 |
| 차단 없음(쌍 있음) | 97 |
| (참고) 폴백을 허용하면 회복되는 질의 | 21 |

## 빈출 개념 쌍 상위 10

| 본원 개념 | 인용 개념 | 단위 빈도 |
|---|---|---|
| process:deposition | process:deposition | 61 |
| process:deposition | material:aluminum | 47 |
| process:deposition | equipment_class:process_chamber | 41 |
| process:deposition | process:etch | 41 |
| process:deposition | material:process_gas | 40 |
| equipment_class:process_chamber | equipment_class:process_chamber | 36 |
| material:dielectric | process:deposition | 35 |
| equipment_class:process_chamber | process:deposition | 34 |
| material:dielectric | material:dielectric | 33 |
| process:plasma_processing | process:deposition | 33 |

정밀도 표본 100건은 `data/interim/plan074_precision_sample.tsv` 에 있다(원문을 담으므로 gitignore 경로다).
층 부족분 보충: 없음 · seed = 20260823.
