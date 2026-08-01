# B층 파일럿 수집 프로파일 (PLAN-032 §5.6 · 자동 생성)

> 이 파일은 `sdkb_paper.collect.b_layer` 가 생성한다. 수기 수정 금지(CLAUDE §1-7).
> **봉인 규율:** 정답(심사관 인용) 식별자·언어분포는 여기에 없다 — 봉인 파일을 열지 않았다.

## 1. 구조

| 산출물 | 키 | 원천 |
|---|---|---|
| 스크리닝 원장 (JSONL) | `application_number` | KIPRIS `getAdvancedSearch` 응답 |
| 채택 레코드 (parquet) | `application_number` | + `getBibliographyDetailInfoSearch` |
| 봉인 qrel (parquet) | `application_number` × 인용 | 서지상세 `priorArtDocumentsInfo` |

## 2. 형태

- 스크리닝 후보 2,623행 · 채택 200건
- 고유 출원번호 2,573
- 출원일 범위 2018 ~ 2018 (채택분)

## 3. 기술통계

### 3.1 비율 (Wilson 95 % CI · 결정 B)

| 지표 | 값 [95 % CI] (분자/분모) |
|---|---|
| `r_free` | 0.0816 [0.0717, 0.0928] (210/2573) |
| `r_family` | 1.0000 [0.9820, 1.0000] (210/210) |
| `r` | 0.9524 [0.9146, 0.9739] (200/210) |

### 3.2 사유 코드 분포 (동결 12종)

| 코드 | 건수 |
|---|---:|
| `dup_application_a_layer` | 5 |
| `ipc_not_frozen` | 696 |
| `no_examiner_citation` | 9 |
| `npl_only_citation` | 1 |
| `ok` | 200 |
| `status_not_rejected` | 1,712 |

### 3.3 채택분 분포와 A층 대조 (PLAN-031 §4 보고 의무)

| 출원연도 | B층 | A층 |
|---|---:|---:|
| 2018 | 200 | 27 |

| 주분류 IPC | B층 |
|---|---:|
| H10P | 58 |
| B23K | 21 |
| H10K | 20 |
| C23C | 18 |
| H10W | 13 |
| G02F | 10 |
| G03F | 9 |
| C07F | 7 |
| H10F | 7 |
| B22F | 6 |

> A층 주분류 IPC 분포는 이 표에 없다 — 상류 원본에만 있고 런타임 상류 접근을 하지 않기 때문이다(CLAUDE §0.1). 대조는 vendor 된 값이 생긴 뒤 별도로 붙인다.

> 분포가 다르므로 **기존 test 결과와 직접 비교하지 않는다** — B층은 자체 완결적 확증이다.

## 4. 호출 회계 (4계정 분리 · §1 동결)

```json
{
  "audit": 50,
  "detail": 210,
  "max_audit": 50,
  "max_detail": 500,
  "max_search": 300,
  "quota_hit": false,
  "search": 22
}
```

## 5. 사용 목적

- 채택 레코드 → B층 질의 (H3·H4·H5 재확증 · PLAN-031 §4)
- 봉인 qrel → 최종 1회 개봉 시의 정답 (그 전까지 읽지 않는다)
- `r` → 본수집 예산 확정 (§8.1 `총콜 ≈ 200/r + 200`)
- 감사 위음성률 → 무료 배제 가정의 검증 (결정 E · 규칙은 바꾸지 않는다)
