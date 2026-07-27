# 데이터 프로파일 — IR 코퍼스 DOCDB family 지도 (PLAN-018 B2 · F1 주지표)

> 생성: `python -m sdkb_paper.collect.bq_family_ir` (2026-07-27) · 원천: BigQuery
> `patents-public-data.patents.publications` · 조인 방식 공개번호+출원번호 정규화.
> 산출: `data/raw/bigquery/ir_family_map.parquet` (raw·비커밋) · 입력 코퍼스 sha256 `ec5ea51b626d…`.

## 왜 만드는가 (사용 목적)
주 지표 **family-level Recall@100**(F1 · 원고 §5.1·§4.5)의 전제. 같은 발명의 국내외 중복 공개를
한 패밀리로 접어야 회수를 정직하게 센다. 조립된 IR 코퍼스에는 family_id 열이 없었고, qrel 정답
(심사관 인용 선행기술)은 **공개번호**로만 식별돼 시계열용 `bq_family.py`(KR 출원번호 키)로는 한 건도
조인되지 않았다 — 그래서 IR 전용 수집기(`collect/bq_family_ir`)를 신설했다. 소비처:
`analysis/metrics.evaluate(..., family=...)`, 이후 T2 언어 하위집단·B8 family-disjoint 분할.

## (1) 구조
| 컬럼 | dtype | 의미 |
|---|---|---|
| `doc_id` | str | 코퍼스 문서 ID (조인 키) |
| `family_id` | str | DOCDB family_id, 또는 fallback `self:<doc_id>` |
| `method` | str | `docdb-pub`(공개번호 조인)·`docdb-app`(출원번호 조인)·`fallback-self`(미조인) |

## (2) 형태
- 행 40,552 = 코퍼스 전 문서 1:1 (결측 0 · 모든 문서가 family_id 보유, 미조인은 fallback).
- 고유 family 39,899 (문서 40,552 → 653 문서가 기존 패밀리에 흡수 = 동일발명 중복).

## (3) 기술통계 — 조인 방식 분해
| method | 건수 | 비율 |
|---|---:|---:|
| docdb-app (출원번호) | 36,181 | 89.2% |
| docdb-pub (공개번호) | 2,666 | 6.6% |
| fallback-self (미조인) | 1,705 | 4.2% |
| **DOCDB 소계** | **38,847** | **95.8%** |

source별 DOCDB 커버리지: g0_rej(질의) 99.8% · g1 96.2% · g2 96.6% · **g0_cited(정답) 87.9%**.

### 주지표 관점 — qrel 정답(2,211)의 family
- 정답 DOCDB 커버리지 **88.1%**(1,947/2,211). fallback 264 = US 출원공개 252(연도 시리얼에
  코퍼스가 0 하나 더 부여 — BQ `US-2001000632` vs 코퍼스 `US20010000632`) + 구 KR/기타 12.
- **family 집계 효과는 미미:** 정답 문서 2,211 → 고유 정답 family 2,193(−18). 정답을 병합하는
  질의는 **5/981** 뿐. 심사관 인용은 대개 서로 다른 발명이라 이 데이터셋에서 **family 수준 ≈
  문서 수준**이다(정직 보고). 그럼에도 주 결론은 F1(family 수준)에 둔다(원고 §5.1).

## 정규화 규칙 (재현 계약)
- 키 = `country_code` + 앞0 제거 숫자부. kind code(A·B1…)는 같은 출원의 다른 공보 → 무시.
- **KR 특례:** KIPRIS 공개/등록번호의 타입접두(특허 `10`·실용 `20`)를 제거한 변형을 후보에 추가
  (`KR100146263B1`=10+0146263 → BQ `KR-0146263-B1`). `bq_family.py` 출원번호 규칙과 동형.
- 미조인 = fallback `self:<doc_id>`(1개 패밀리). 조용한 무효과 방지 · 비율을 여기 보고(원고 §4.5).

## 알려진 한계 (정직 보고)
- US 출원공개 252건·구 KR 공개 등은 번호포맷 차이/BQ 부재로 fallback. family 집계 효과가 미미해
  주지표 영향은 무시가능. 번호 정규화 과적합(위양성 매칭) 위험을 피해 88%에서 멈춤.
- family_id 는 DOCDB 스냅샷 시점 의존. BQ 커밋이 아니라 결과 재현은 코퍼스 sha + 이 프로파일로 고정.
