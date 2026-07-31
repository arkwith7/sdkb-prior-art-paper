# data/processed/ — 파일별 정본/중간 판정 (v0.9)

> 이 폴더는 **gitignore** 다(전부 `make` 로 재생성). 여러 세대의 그래프·델타·분할본·두 패러다임의
> 산출물이 한 폴더에 섞여 "무엇이 최종인지" 헷갈리므로, 아래 표가 파일별로 판정한다.
> **물리적으로 옮기지 않고** 라벨로 구분한다 — 파일명이 `config.py`·`Makefile`·논문에 배선돼 있어
> 이동은 코드 변경을 동반한다.
> 서명 수치는 [`../MANIFEST.md` §3](../MANIFEST.md), 갱신 규율은 [`../README.md`](../README.md),
> 전 저장소 정본 판정은 [`../../01.code_spec/CANONICAL-INDEX.md`](../../01.code_spec/CANONICAL-INDEX.md).
>
> **⚠ 2026-07-31 개정 — 이 파일은 구 패러다임 상태로 낡아 있었다.** 이전 판은 `h1_*`·`h2_*`·
> `robustness_*`(=커버리지·시계열 검정 = **S1/S2**)를 "✅ 최종 — 이것이 결과다"로 등재하고,
> **v0.9의 실제 결과인 `ir/` 전체를 한 줄도 적지 않았다.** v0.9 정본 기조(선행기술 검색 주 태스크 +
> T-gate)에서 **결과는 `ir/`와 `fault_matrix*`·`tgate_report*`이고, 구 산출은 S-시리즈다.**

---

## ✅ 최종 (FINAL) — v0.9의 결과는 여기다

### C2 · 선행기술 검색 (`ir/`) — 핵심증명의 산출물

| 파일 | 무엇 | 재생성 |
|---|---|---|
| `ir/ir_corpus_v09.parquet` | **IR 코퍼스 40,552행** (질의 1,000 + 후보 모집단) — as-built [SPEC-007](../../01.code_spec/specs/SPEC-007-ir-corpus-asbuilt.md) | `make corpus` |
| `ir/qrel_examiner.parquet` | 정답지 (심사관 인용 · 2,416 엣지 → 고유 정답 **2,321**) | `make corpus` |
| `ir/qrel_test_sealed.parquet` | **봉인 test qrel** — 최종 비교 시점까지 개봉 금지 (규칙 #3) | `make corpus` |
| `ir/split.parquet` | 시점 분할 train/dev/test (F9 동결 · 프로파일 [`ir_split.md`](../profiles/ir_split.md)) | `make split` |
| `ir/concept_axis.parquet` · `.tree.json` | 개념 축·계층 — 온톨로지 팔의 입력 | `make corpus` |
| `ir/feature_sidecar.parquet` | claim-feature 사이드카 조인 | `make corpus` |
| `ir/index/{bm25_text_main,pretok_text_main}` · `*_titan_cache.sqlite` | Pyserini BM25(nori) 색인 · Titan 임베딩 캐시 | `make index` · `make dense` |
| `ir/userdict_sdkb.txt` | nori 사용자사전 — as-built [SPEC-008](../../01.code_spec/specs/SPEC-008-nori-userdict-inventory.md) | `make userdict` |
| `ir/runs/sys_*_{dev,test}.txt` (14) | **동결 run** — B0·B2·B3·B4·B5·P0★·P1 | `make retrieve` 계열 |
| `ir/runs/{bm25_b0_claim,dense_b2_claim,hybrid_b3_rrf}.txt` · `onto_*_dev.txt` | M3 기준선 · M4 온톨로지팔 개발 run | 〃 |
| `ir/ir_{performance,subgroup,increment,crosslingual}_{dev,test}.csv` · `ir_ablation_test.csv` | **§6 표의 원천** (성능·하위집단·증분·교차언어·ablation A1–A8) | `make eval` · `make tables` · `make crosslingual` |
| `ir/overlap_threshold.json` | F11 low-overlap 임계 **dev Q1 0.0079** (사전등록 동결값) | `make eval` |

> **동결 규율.** run·설정·임계는 사전등록(PLAN-018 F1–F18)으로 동결됐다. 표·그림 재생성은
> **새 검색 없이** 동결 run을 재평가한다: `make tables SPLIT=test && make figures`.

### C3 · 진화안전 (T-gate·결함주입)

| 파일 | 무엇 | 재생성 |
|---|---|---|
| `tgate_report.json` · `tgate_report_test.json` · `tgate_report_test_p0star.json` | T1·T2·T3 판정 (dev · 확증분할 주델타 · 부수델타) | `make tgate` |
| `fault_matrix.json` → `_v2` → `_v3` → `_v4` · `fault_matrix_holdout.json` | 결함주입 × 검출 매트릭스 4세대 + **H1‴ 홀드아웃 72** | `make faults` 계열 |
| `fault_baseline.json` · `fault_matrix_n03.json` · `fault_matrix_n03adv.json` · `fault_t3_prime.json` | 정상 델타 위양성 대조 · N03 악용 결함 · T3′ 진단 | 〃 |

### 그래프 (C1 자원 · 검색 후보 모집단)

| 파일 | 무엇 | 재생성 |
|---|---|---|
| `graph_v0.ttl` | **G₀** baseline — **게이트 대상** (L0–L3 + T-gate) | `make baseline` |
| `graph_v1.ttl` · `graph_v2.ttl` | **후보 모집단**(방해문서 풀) — **"세대"가 아니다**(D-12: 셋의 T-Box가 완전히 동일) | `make merge` · `make merge CORPUS=ksia-equipment` |
| `central_axis.oxstore/` | 청구항 분해 중심축 사이드카 (11,606,318 트리플) — 분석 그래프에 **병합되지 않는다** | 상류 산출·벤더 |

---

## 🔶 S-시리즈 (구 패러다임 · C1의 2차 재사용 증거)

**v0.9의 결과가 아니다.** 구 커버리지(S1)·시계열(S2)·이식성(S3) 검정의 산출물이며, 자원 형성
타당성의 방증이자 T-gate T3의 회귀 감시 맥락으로만 보존한다. **인용은 "S1(구 H1)" 형식으로만**
하고, v0.9 확증가설 H1–H5와 혼동하지 않는다(라벨 사전 = [RECONCILIATION-v09 §1](../../01.code_spec/RECONCILIATION-v09.md)).

| 파일 | 무엇 | 재생성 |
|---|---|---|
| `h1_coverage.csv` · `h1_coverage_ksia.csv` | S1 공정별 커버리지 | `make s1` (구 별칭 `make h1`) |
| *(md 산출)* `h1_residual_gaps.md` · `h1_threshold_sensitivity.md` | S1 잔여공백·증가폭 임계 민감도 | `make s1` |
| *(md 산출)* `h1_strata_ksia.md` | S3 소부장 층별(장비·재료·부분품) | `make ksia-strata` |
| `h2*_*.csv` · *(md)* `h2_report.md` | S2 시계열 조기탐지 검정 산출 | `make s2` (구 별칭 `make h2`) |
| *(md 산출)* `robustness_applicant.md` · `robustness_family.md` | 구 §4.5 강건성 (출원인별·패밀리 dedup) | `make by-applicant` · `make robustness` |
| *(md 산출)* `candidates_report.md` | 신기술 개념 후보 탐색 목록 (발견 자동·**채택은 사람**) | `make candidates` |

> **`(md 산출)` 표시된 7건은 현재 디스크에 없다 (2026-07-31).** 재생성 가능성을 실제로 검증한 뒤
> 지웠다 — 백업 → 위 명령으로 전량 재생성 → 대조 → 제거. **5건은 바이트 동일**했고, 2건은
> **디스크 사본이 낡아 있었다**: `robustness_family.md`(2026-07-14 · si 4승1패 n=5 → **5승2패 n=7**),
> `candidates_report.md`(2026-07-13 · 신기술 개념 특허 419 → **639**). 즉 **지워서 잃은 정보는 없고,
> 오히려 코드+데이터의 현재 출력과 어긋나는 낡은 사본이 치워졌다.** 필요하면 위 명령으로 되살린다.

> **재오염 경로는 막혔다 (2026-07-31 교정).** 이 타깃들은 예전에 구 패러다임 표·그림을 **v0.9 정본
> `paper/tables/`·`paper/figures/` 에 직접 썼고**, 실제로 재생성 한 번에 S-시리즈 표 10건·그림 4건이
> v0.9 표 옆에 되살아났다. 이제 `config.ARCHIVE_TABLES`·`ARCHIVE_FIGURES` 를 통해
> **`paper/archive/regenerated/{tables,figures}/`** 로만 나간다(gitignore · 검증 완료).
>
> **동결본을 덮지 않는 이유.** 인용 대상인 `paper/archive/{tables,figures}/` 는 v0.5/v0.7 원고가
> 가리키는 **동결 기록**이다. 재계산 값으로 덮으면 "교정 전 상태"를 인용할 수 없게 된다 —
> 실제로 `robustness_family_dedup.md`·`h2_census.md`·fig7/8/8b/8c 는 현행 코드 출력과 값이 다르다.
> **차이는 지울 대상이 아니라 기록할 대상이다.**

> **파일명이 아직 `h1_*`·`h2_*` 인 이유.** 코드 진입점은 `s1_coverage_cli`·`s2_timeseries_cli`로 이미
> 재라벨됐고 `make h1`·`make h2`는 호환 별칭이다. **산출 파일명의 재라벨(B7 후속)은 미완**이며,
> figure/IR 하네스 재빌드 시 동반한다 — 그때까지 이 표가 판정한다.

---

## ⚠ 중간·강건성 (INTERMEDIATE) — 최종이 아니다

| 파일 | 무엇 | 왜 최종 아님 |
|---|---|---|
| `delta_v1.ttl` · `delta_v2.ttl` | 병합 **전** 델타 트리플 | `graph_v1/v2` 로 병합되는 *입력*. 독립 산출물 아님 |
| `delta_v2_{equipment,material,component}.ttl` | 층별 델타 | 위와 같음 |
| `graph_v2_{equipment,material,component}.ttl` | G₂ 층별 | S3 층별 재검정용 분할본 |
| `graph_v1_famdedup.ttl` · `delta_v1_famdedup.ttl` | 패밀리 dedup 변형 G₁ | 구 §4.5 강건성 *변형본*, 헤드라인 G₁ 아님 |
| `graph_v1_samsung.ttl` · `graph_v1_hynix.ttl` · `delta_v1_{samsung,hynix}.ttl` | 출원인 분할 G₁ | 구 §4.5.2 분할 *부분집합* (mtime 이 최신이라 오인 주의) |
| `graph_v{0,1,2}_protege.ttl` | Protégé 조회용 사본 | 도구 편의 산출 — 분석 입력 아님 ([TOOLING.md](../../01.code_spec/TOOLING.md)) |
| `candidates_report.md` | 신기술 후보 탐색 목록(2026-07-13) | 현행 동결 이전 작업 산출 — 최종 매핑 규칙 아님 |
| `catalog-v001.xml` | Protégé 카탈로그 | 도구 부산물 |

> **`delta_*` 은 절대 `graph_*` 의 대체가 아니다.** 큰 용량이라도 병합 전 입력이다.
> **`graph_v1_*` 접미사 붙은 것은 전부 분할/변형본**이고, 헤드라인 G₁ 은 접미사 없는 `graph_v1.ttl` 하나다.
