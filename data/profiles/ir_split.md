# 데이터 프로파일 — 시점 분할 (B8 · F9 사전등록)

> 생성: `python -m sdkb_paper.corpus.split` (2026-07-27) · 입력 코퍼스 sha `ec5ea51b626d…` ·
> family 지도 `collect/bq_family_ir`. 산출: `data/processed/ir/split.parquet`(raw·비커밋).
> **F9 동결값은 `config.py`(F9_BOUNDARY_*·F9_SPLIT_FRACTIONS)** — 커밋이 사전등록 증거.

## 사용 목적
질의(거절특허 1,000)를 train/dev/test 로 나눈다. train/dev = 가중치 학습(F18)·민감도(F11)·시스템
개발. **test 200질의는 최종 비교까지 봉인**(F9·CLAUDE 규칙 #3·#4). 후보 코퍼스는 나누지 않는다 —
질의별 F10 시점컷으로 마스킹(`retrieval/candidate`). 소비처: `analysis/metrics --split`, T-gate T2.

## 규칙 (동결)
filingDate 순 **60/20/20**, 단 **family 단위**(family-disjoint). family 대표일 = 그 family 질의들의
최소 출원일. family 를 (대표일, family_id) 로 정렬 후 누적 질의수 60%/80% 지점 절단. 경계일은 데이터
감사 결과이며 config 에 동결 — `build_split` 이 매 실행 절단결과와 대조해 표류 시 즉시 실패(체크섬).

- **train/dev 경계 = 2016-11-21 · dev/test 경계 = 2021-07-21** (F9 동결)

## 형태·통계
| split | 질의 | 비율 | 출원일 범위 | 고유 family |
|---|---:|---:|---|---:|
| train | 600 | 60.0% | 1997-12-31 ~ 2017-12-29 | 568 |
| dev | 200 | 20.0% | 2016-11-21 ~ 2023-06-29 | 193 |
| **test(봉인)** | 200 | 20.0% | 2021-07-21 ~ 2025-04-22 | 198 |

- 출원일 범위가 블록 간 겹친다(예: train 이 2017-12 까지, dev 가 2016-11 부터) — **family 단위 배정의
  당연한 결과**다. family-disjoint 는 유지되나(같은 발명은 한 블록), 개별 질의의 출원일은 대표일과
  달라 경계 부근에서 교차할 수 있다. 이것이 시간 누출을 만들지 않는다: 후보 마스킹은 F10(질의별
  출원일 컷)이 따로 강제하며, 분할은 '어느 질의로 개발/평가하나'만 가른다.
- test qrel 봉인: **479 엣지 / 198 질의** → `qrel_test_sealed.parquet`. 개발용 visible = 1,937 엣지.

## F1 주지표 — split별 B0(BM25-Claim) family-level Recall@100
| split | Recall@100 | Success@100 | 평가질의(정답≥1) |
|---|---:|---:|---:|
| train | 0.2548 | 0.4266 | — |
| **dev** | **0.2942** | 0.5076 | 197 |
| all | 0.2905 | 0.4801 | 981 |
| test | 봉인 | — | 198 |

dev 가 개발 기준선. test 는 Dense·Hybrid·온톨로지팔까지 확정한 뒤 최종 1회만 개봉.
