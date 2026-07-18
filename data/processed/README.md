# data/processed/ — 파일별 정본/중간 판정

> 이 폴더는 **gitignore** 다(전부 `make` 로 재생성). 여러 세대의 그래프·델타·분할본이 한 폴더에
> 섞여 "무엇이 최종인지" 헷갈리므로, 아래 표가 파일별로 판정한다. **물리적으로 옮기지 않고**
> 라벨로 구분한다 — 파일명이 `config.py`·`Makefile`·논문에 배선돼 있어 이동은 코드 변경을 동반한다.
> 서명 수치는 [`../MANIFEST.md` §3](../MANIFEST.md), 갱신 규율은 [`../README.md`](../README.md).

## ✅ 최종 (FINAL) — 이것이 결과다

| 파일 | 무엇 | 재생성 |
|---|---|---|
| `graph_v0.ttl` | **G₀** baseline (H1 before) | `make baseline` |
| `graph_v1.ttl` | **G₁** 삼성·SK하이닉스 보강 (H1 after) | `make merge` |
| `graph_v2.ttl` | **G₂** 소부장 188사 (RQ3) | `make merge CORPUS=ksia-equipment` |
| `graph_v2_equipment.ttl` · `graph_v2_material.ttl` · `graph_v2_component.ttl` | G₂ 층별 (논문 표 5b) | `make ksia-strata` |
| `h1_coverage.csv` · `h1_coverage_ksia.csv` | H1 공정별 커버리지 | `make h1` |
| `h1_residual_gaps.md` · `h1_strata_ksia.md` · `h1_threshold_sensitivity.md` | H1 잔여공백·층별·민감도 | `make h1` |
| `h2a_census.csv` · `h2_leadtime.csv` · `h2_timeseries.csv` · `h2_dart_reference.csv` · `h2_plan009_matrix.csv` · `h2prime_matrix.csv` · `h2_predecessor_codes.csv` · `h2_report.md` | H2 검정 산출 | `make h2` |
| `robustness_applicant.md` · `robustness_family.md` | §4.5 강건성 (출원인별·패밀리 dedup) | `make by-applicant` · `make robustness` |

## ⚠ 중간·강건성 (INTERMEDIATE) — 최종이 아니다

| 파일 | 무엇 | 왜 최종 아님 |
|---|---|---|
| `delta_v1.ttl` · `delta_v2.ttl` | 병합 **전** 델타 트리플 | `graph_v1/v2` 로 병합되는 *입력*. 독립 산출물 아님 |
| `delta_v2_{equipment,material,component}.ttl` | 층별 델타 | 위와 같음 |
| `graph_v1_famdedup.ttl` · `delta_v1_famdedup.ttl` | 패밀리 dedup 변형 G₁ | §4.5 강건성 *변형본*, 헤드라인 G₁ 아님 |
| `graph_v1_samsung.ttl` · `graph_v1_hynix.ttl` · `delta_v1_{samsung,hynix}.ttl` | 출원인 분할 G₁ | §4.5.2 분할 *부분집합*, 헤드라인 G₁ 아님 (mtime 이 최신이라 오인 주의) |
| `candidates_report.md` | 신기술 후보 탐색 목록(2026-07-13) | 현행 동결 이전 작업 산출 — 최종 매핑 규칙 아님 |

> **`delta_*` 은 절대 `graph_*` 의 대체가 아니다.** 큰 용량(`delta_v2` ≈ 대형)이라도 병합 전 입력이다.
> **`graph_v1_*` 접미사 붙은 것은 전부 분할/변형본**이고, 헤드라인 G₁ 은 접미사 없는 `graph_v1.ttl` 하나다.
