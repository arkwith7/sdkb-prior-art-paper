# data/ — 데이터 자산 지도와 갱신 규율 (v0.9)

> **이 디렉토리를 열었을 때 가장 먼저 읽는 문서.** "지금 무엇이 정본 데이터인가"와 "보강·교정하면
> 무엇을 어떻게 갱신하는가"를 한 곳에 고정한다. **숫자는 여기에 다시 적지 않는다** — 숫자를 여러
> 곳에 복사한 것이 혼선의 원인이었다. 서명 수치의 정본은 아래 두 곳뿐이다.
>
> | 무엇 | 정본 위치 |
> |---|---|
> | **현재 그래프 서명(트리플·커버·게이트)** | [`MANIFEST.md` §3](MANIFEST.md) — `make baseline`·`make merge` 출력의 기록 |
> | **전 저장소 정본/중간/계획 판정** | [`../01.code_spec/CANONICAL-INDEX.md`](../01.code_spec/CANONICAL-INDEX.md) §1 |
>
> **⚠ 2026-07-31 개정.** 이전 판은 구 커버리지 패러다임(v0.5) 기준으로 쓰여 있었다 — G₀를 "H1 의
> before", G₂를 "이식성(RQ3) 그래프"로 부르고, **v0.9의 핵심 자산인 IR 벤치마크 코퍼스를 한 줄도
> 언급하지 않았다.** v0.9 기조(선행기술 검색 주 태스크 + T-gate)에 맞춰 다시 썼다.

---

## 0. 이 저장소의 데이터는 세 층이다

```
① 얼린 상류 스냅샷        data/external/sdkb/      ← 정본의 원천 (git tracked · sha256)
       │  make baseline / make merge
② 분석 그래프             data/processed/graph_v*.ttl   ← 결정적 재생성물 (gitignore)
       │  make corpus / index / retrieve / eval
③ IR 벤치마크·실험 산출    data/processed/ir/ · fault_matrix* · tgate_report*   ← v0.9 결과
```

**정본은 "얼린 스냅샷 + 코드"이고, ②③은 거기서 결정적으로 재생성되는 산출물이다.** 그래서 `.ttl`·
parquet 은 gitignore 다 — 잃어버려도 `make` 로 똑같이 되살아난다. 최종의 *원천*만 커밋한다.

| 계층 | 최종 산출물 | 위치 | git | 재생성 |
|---|---|---|---|---|
| **원천 (동결·보존)** | 상류 SDKB 스냅샷 13파일 + `PROVENANCE.json`(sha256) | `external/sdkb/` | ✅ tracked | `make vendor` |
| **G₀ (baseline · 게이트 대상)** | `graph_v0.ttl` | `processed/` | ⛔ ignore | `make baseline` |
| **G₁·G₂ (후보 모집단 · 방해문서 풀)** | `graph_v1.ttl` · `graph_v2.ttl` (+ 층별 `graph_v2_*`) | `processed/` | ⛔ ignore | `make merge [CORPUS=…]` · `make ksia-strata` |
| **IR 벤치마크 (C2 결과의 원천)** | `ir/{ir_corpus_v09,qrel_examiner,qrel_test_sealed,split,concept_axis}.parquet` · `ir/runs/` · `ir/ir_*.csv` | `processed/ir/` | ⛔ ignore | `make corpus`→`index`→`retrieve`→`eval` |
| **T-gate·결함주입 (C3 결과)** | `tgate_report*.json` · `fault_matrix*.json` | `processed/` | ⛔ ignore | `make tgate` · `make faults` |
| **수집 프로파일** | `kipris_*.md` · `family_dedup.md` · `ir_*.md` | `profiles/` | ✅ tracked | `make profile` · 각 수집기 |
| **게이트 픽스처** | `mini_graph.ttl` | `samples/` | ✅ tracked | 손유지(합성 3특허) |
| **S-시리즈 (구 패러다임)** | `h1_*` · `h2_*` · `robustness_*` | `processed/` | ⛔ ignore | `make s1`·`s2`·`robustness`·`by-applicant` |

> **G₁·G₂를 "세대"라고 부르지 않는다 (2026-07-29 · D-12).** 셋의 T-Box는 완전히 동일하다
> (클래스 103·ObjectProperty 97·DatatypeProperty 81 · 술어 델타 0). G₁/G₂가 더하는 것은 특허
> A-Box뿐이고, **정답 2,211건은 전부 G₀ 안에 있다**(G1/G2 전용 정답 0건). 그래도 빼지 않는 이유는
> 빼면 후보가 40,552 → 4,034로 줄어 **건초더미가 사라지기** 때문이다 — 데이터는 유지하고
> **역할 이름만** 고쳤다: 세대 → **후보 모집단**.
>
> `processed/` 안에서 **무엇이 최종이고 무엇이 병합 전 입력·분할본·구 패러다임 산출인지**는
> [`processed/README.md`](processed/README.md) 가 파일별로 판정한다.

**중간·원문(커밋 안 함, 재배포 금지):** `raw/`(KIPRIS·BigQuery·DART 원문·캐시) · `interim/`(*.parquet) ·
특허 전문(claim/abstract) — 전부 gitignore. KIPRIS 학술 이용·비재배포 조건(CLAUDE.md §1-5).

---

## 1. 갱신 규율 — "새 사본을 만들지 말고 최종을 다시 굳힌다"

보강·교정이 생기면 **아래 순서를 지키고, 새 그래프 이름을 만들지 않는다.** G₀/G₁/G₂ 는 *같은
파일명*으로 재생성되고, 서명은 *같은 표*(MANIFEST §3)에서 갱신된다. 새 `graph_v3`·`graph_v1_new`
같은 이름이 생기는 순간 혼선이 재발한다.

```
① 상류 SDKB 에서 고친다 — 이 저장소는 상류를 직접 수정하지 않는다.
   결함은 upstream/DEFECT-LEDGER.md 에 등재하고 upstream/CR-NNN 으로 제출한다(C0).
   여기서 우회 패치하면 스냅샷 출처가 거짓이 된다.
② make vendor        # external/sdkb/ 재동결 + PROVENANCE.json sha256 재작성
③ make baseline      # graph_v0(G₀) 재생성
④ make merge [CORPUS=…]   # graph_v1 / graph_v2 재생성
⑤ make gate          # L0→L1→L2→L3 + T1·T2·T3, 통과 확인
⑥ make baseline 두 번 재실행해 graph_v0 바이트 동일 확인 (결정성 = 재현성)
⑦ 코퍼스가 바뀌면 make corpus → index → retrieve → eval 을 다시 태운다
⑧ 서명 갱신을 한 커밋으로: MANIFEST §1 이력표에 새 줄 + §3 서명 수정
                        + CANONICAL-INDEX.md §1 수정 + 이 파일 지도가 바뀌면 반영
```

> **G₀ 는 동결이 기본이다.** ③④ 로 G₀ 가 움직이면 게이트 기준선과 검색 결과가 함께 움직인다.
> G₀ 를 바꾸는 보강은 **사람 승인**이 있어야 하고(CLAUDE.md §0.1·§1-8), 바꾼 뒤에는 게이트를
> 전면 재실행해 판정의 불변(또는 변화)을 보고한다.
>
> **상류 교정 후의 재평가는 새 사전등록 아래 새 검정이다** (CLAUDE.md §1-2·§1-3 · [PLAN-029](../01.code_spec/plans/PLAN-029-post-remediation-reexperiment.md)).
> 스냅샷이 바뀌었다고 기존 원고의 판정을 소급 수정하지 않는다.

> **왜 그래프를 커밋하지 않는가.** `.ttl` 을 커밋하면 "디스크의 파일"과 "코드가 만드는 그래프"가
> 갈라져 또 하나의 정본 후보가 생긴다. 원천(스냅샷)만 커밋하고 그래프는 재생성함으로써
> **정본이 언제나 하나**가 되게 한다.

---

## 2. 이 디렉토리의 문서 지도

| 문서 | 역할 |
|---|---|
| `README.md` (이 파일) | 데이터 자산 지도 + 갱신 규율 |
| [`MANIFEST.md`](MANIFEST.md) | 수집·스냅샷·파생 그래프·IR 코퍼스의 **이력과 서명** — 서명 수치의 정본 |
| [`DATASET-CARD.md`](DATASET-CARD.md) | 데이터셋 **정체성**(정의·출처·의도적 배제·상호관계) — *Datasheets for Datasets* 형식 |
| [`processed/README.md`](processed/README.md) | `processed/` 파일별 정본/S-시리즈/중간 판정 |
| [`profiles/*.md`](profiles/) | 수집·조립 산출물의 기술통계 — **코드 생성물**(손으로 고치지 않는다 · CLAUDE.md §4) |

> **S-시리즈 산출물의 출력 경로 (2026-07-31 교정).** `make s1`·`s2`·`robustness`·`by-applicant`·
> `ksia-strata` 와 `make figures` 의 구 패러다임 그림은 **`paper/archive/regenerated/`** 로 나간다
> (gitignore). v0.9 정본 표·그림(`paper/tables`·`paper/figures`)과 섞이지 않고, 인용 대상인 동결본
> (`paper/archive/{tables,figures}`)도 덮지 않는다 — 경로 상수는 `config.ARCHIVE_TABLES`·`ARCHIVE_FIGURES`.
