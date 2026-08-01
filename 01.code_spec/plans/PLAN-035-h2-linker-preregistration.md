# PLAN-035 — 사전등록: H2 최초 실검정 (개념 적용기 경유 · O → O′)

> **상태: 동결 — 이 커밋이 사전등록의 증거다.** [CLAUDE.md §2.1](../../CLAUDE.md)이 규정한
> **유일한 정지 게이트**이며, 이후 §6 실행은 중간 승인 없이 끝까지 돌린다.
> **여기 적힌 동결 항목은 결과를 본 뒤 바꾸지 않는다.**
>
> **선행:** [PLAN-034](PLAN-034-concept-linker-requirements.md) 5단계까지 완료(코드 동결).
> **전 회차:** [PLAN-030](PLAN-030-a-layer-h2-preregistration.md) — 자격 있는 델타가 있었으나
> 하류에 적용기가 없어 코퍼스 서명이 불변이었고, H2 는 **미검정**으로 끝났다(D-19).
> 이 사전등록이 다른 점은 하나뿐이다 — **자원이 파이프라인에 도달할 통로가 생겼다.**

---

## 0. 한 문장

**교정 전 스냅샷 O(d578bf3)와 교정 후 스냅샷 O′(2839afb + `concept_mapping.json`)를 완전히 동일한
코드·완전히 동일한 검색 설정에 넣어 T1·T2·T3 를 적용하고, 지금까지 "미검정"이던 H2(갱신 승인
안전성)를 이 연구 최초로 실제로 검정한다.**

---

## 1. 두 팔의 정의

| 팔 | 스냅샷 | 사전 | 코드 |
|---|---|---|---|
| **O** | 상류 `d578bf3` — 이 저장소 git `83fd494:data/external/sdkb/` 에서 복원 | **없음**(CR-007 이전) → 적용기 무작동 | 사전등록 커밋 |
| **O′** | 상류 `2839afb` — `make vendor` | `mappings/concept_mapping.json`(patent-text · 표면형 636) | **같은 커밋** |

- 두 스냅샷의 차이는 **4파일**: `sdkb-core.ttl` · `sdkb-core-data.ttl` · `semiconductor_v0_3.json` ·
  `schema_report.json`. **license_restricted 2파일(`sdkb-abox-patents.ttl`·`sdkb-abox-prior-art.ttl`)은
  양쪽에서 바이트 동일**하므로 문서집합(③A-Box 델타)은 섞이지 않는다.
- 상류 저장소를 체크아웃하지 않는다(§0.1 — 상류를 건드리지 않는다). O 팔은 우리 git 이력에서 복원한다.

### 1.1 델타 자격 (실행 전 확정 · 투영 심사 통과)

| 항목 | 값 |
|---|---|
| 스냅샷 서명 | O `6cfb743d3d88` → O′ `b98ad787d1fe`(+ `concept_mapping.json` 편입 후 재계산) |
| T-Box 이동 | `owl:ObjectProperty` **97 → 98**(`skos:broader` 선언) · 클래스 103 불변 · DatatypeProperty 81 불변 |
| 델타 유형 | **① T-Box + ② 개념층** → `classify_delta` = `tbox` ∈ `H2_ELIGIBLE_DELTA_TYPES` |
| ③ A-Box 오염 | **없음**(abox-patents·abox-prior-art sha256 불변) |

---

## 2. 동결 항목 — 결과를 본 뒤 바꾸지 않는다

| 항목 | 동결값 | 근거 |
|---|---|---|
| ε (성능이 떨어지지 않았다고 볼 한계 · 비열등 마진) | **0.02** | CLAUDE.md §5 기존 동결값 유지 |
| δ (하위집단 국소 회귀 한계) | **0.05** | 동상 |
| 주지표 | **family-level Recall@100** | 동상 |
| 비교 시스템 | **P1** (`--system P1`) · 분할 **test** | O_pre_linker 와 동일 |
| 하위집단 축 | 거절근거 · 공정군 · 언어(KR/외국) | CLAUDE.md §5 T2 |
| CQ 스위트 | pa · em · tf · core (분할 불변) | CLAUDE.md §5 T3 |
| 신뢰구간 | 부트스트랩 95% · 질의 단위 재표집 · 시드 고정 | 기존 `analysis/bootstrap` 그대로 |
| 봉인 qrel | `qrel_test_sealed.parquet` = `984f8ef3dfd3befc1745bddf8928ce09dcdea03957e984150dd71e35dfbfda2c` | 변경 없음 |
| qrel(examiner) | `10ab67f21cc1328dadafe3d94c1bbfd64462ac34268f7bafd1574b26b923d541` — **두 팔에서 동일해야 한다**(E3) | 개념 링크는 qrel 을 만들지 않는다 |
| 시점/패밀리 분할 | `split.parquet` = `c25775b346fa395c6c4e0b2e0d4b633ef0bf35bf547d3651e96c0ce9e6fc0bb7` · 재계산하지 않음 | O 시점 그대로 |
| 후보 모집단 | `graph_v1.ttl` `41094e9f…` · `graph_v2.ttl` `16b4f322…` — **재조립하지 않는다** | PLAN-034 §5 비목표 3 |
| 파이프라인 | **완전 동결** — 검색 설정 · 가중치(**w_h 포함**) · 토큰화 · Dense 모델 · RRF · P1 격자(τ=0.7·α=0.75·w=(0.25,0,0.25,0.5)) · 후보 마스킹 | 바뀌는 것은 **자원 하나뿐** |
| 적용기 규칙 | BOUND 경계 · 표면형 독립 판정 · 역할 무관 · confidence 무가중 · Q4 합집합(slug 키) | PLAN-034 §3.5 |

### 2.1 판정식 (사전등록된 승인 규칙의 적용)

```
Accept(O→O′) =  (L0 = L1 = L2 = L3 = pass)
              ∧ (LB₉₅(ΔR₁₀₀) > −ε)              # T1 · ε = 0.02
              ∧ (max_s drop_s < δ)               # T2 · δ = 0.05
              ∧ (∀f ∈ {em, tf, core}: pass_f(O′) ≥ pass_f(O))   # T3
```

- **T1 은 누출 감사 통과를 전제로만 유효하다.** `make leakage` 위반이 0 이 아니면 T1 판정을
  산출하지 않고 실패로 보고한다(§1-4).
- **T3 는 통계 검정이 아니라 결정론적 통과율 비교다.** 하락 시 즉시 실패, 예외는 waiver 토큰뿐.
- **적격심사(E1–E7) 실패는 불통과가 아니라 미검정이다**(종료코드 2) — T1·T2 를 돌리지 않는다.

### 2.2 E4(동일 코드)의 범위를 좁힌 것 — 실행 전에 밝힌다

`runset.code_signature()` 의 dirty 판정을 **코드 경로**(`src`·`tests`·`Makefile`·`pyproject.toml`·
`uv.lock`)로 한정했다(2026-08-01 · 사용자 승인 · **결과를 보기 전** · 단위 테스트 3건 동반).
이유는 구조적이다 — O 팔의 정의 자체가 git 추적 파일인 `data/external/sdkb/` 를 구 스냅샷으로
되돌린 상태이므로, 트리 전체를 보면 O 팔은 동결 시점에 **반드시 dirty** 이고 E4 가 영구히 실격을
내 자원 델타 측정이 원리적으로 불가능해진다. E4 가 묻는 것은 "두 팔이 같은 코드로 돌았는가"이고,
자원 교체는 팔의 정의 그 자체다. **`src/` 가 더러우면 여전히 실격**이다(테스트로 고정).

---

## 3. 실행 전에 통과해야 하는 사전 검사 (실패하면 그 자리에서 보고·중단)

| # | 검사 | 통과 기준 | 상태 |
|---|---|---|---|
| **P-1** | 무작동 동치성 — 사전이 없으면 적용기는 아무것도 하지 않는다 | O 팔 `ir_corpus_v09.parquet` sha256 = `ec5ea51b626d3ff92f62fd1279a5cbae5abcc4cdd0a07e6d0311f35af8db2b43` | 2026-08-01 **선검증 통과**(현 스냅샷·무사전 재조립이 바이트 동일). O 팔에서 재확인 |
| **P-2** | 축 지도 동치성 | O 팔 `concept_axis.parquet` = `5caac56ec3bfdd9d3809c1a204e016e84afcbe8882d4626380e8a06e73991f81` | 동상 |
| **P-3** | O 팔 run 재현 | O 팔 7개 run 이 `O_pre_linker` 의 run 과 **바이트 동일** (`sys_P1_test.txt` = `a1f72f92e437d402…`) | 실행 시 판정. **불일치는 실패로 보고**하고 재사용으로 대체하지 않는다 |
| **P-4** | S2 서명 변화 | O′ 팔 코퍼스 sha256 ≠ `ec5ea51b…` | 격리 예측값 `9fec15c6c325413e9192f43e872f0226c721c977d6ebd89bdf7d464ccfa7ced4` — **일치하면 결정성의 추가 증거**, 불일치해도 S2 자체는 충족 |
| **P-5** | 문서집합 불변 | 두 팔 모두 코퍼스 40,552 행 · qrel `10ab67f2…` 동일 | ③A-Box 오염 배제 |
| **P-6** | 누출 0 | 두 팔 모두 `make leakage` PASS(L-1·L-2·**L-2b 사전**·L-3·L-4) | O′ 팔에서 L-2b 가 실사전을 검사한다 |

---

## 4. 가설과 방향 — 결과를 보기 전에 적는다

**H2 (갱신 승인 안전성).** 게이트를 통과한 자원 갱신은 선행기술 검색 성능을 떨어뜨리지 않고,
하위집단에서도 국소 회귀를 일으키지 않으며, 다른 태스크의 CQ 를 뒷걸음치게 하지 않는다.

- **지지** = `Accept = true` · **기각** = `Accept = false`, 이때 **어느 조건에서 깨졌는지(T1/T2/T3)가
  곧 결과**다.
- **비열등성 검정이지 우월성 검정이 아니다.** O′ 가 O 보다 좋다는 것을 주장하지 않는다. 성능 상승이
  관측되어도 그것은 **확증이 아니다** — test 분할은 이미 개봉됐다(§2.1 안전장치 · PLAN-029 A층).

### 4.1 사전에 선언하는 기대 — 방향은 **음수 쪽**으로 본다

문서당 개념이 1.545 → 3.779 로 2.4배가 되면 P1 의 ConceptOverlap(Jaccard) 분모가 커진다. 개념이
늘어난 만큼 **변별력이 아니라 잡음이 늘 수 있고**, 그러면 ΔR₁₀₀ 은 0 이거나 **음수**로 나온다.

- **ΔR₁₀₀ 이 음수여도 그것은 실패가 아니라 H2 검정의 결과다.** ε=0.02 는 동결돼 있고 결과를 본 뒤
  손대지 않는다. LB₉₅ ≤ −0.02 면 **T1 실패 = H2 기각**으로 그대로 보고한다.
- **nDCG@20 의 회복은 기대하지 않는다.** D-01(개념 해상도)은 이 규모로 해결되지 않는다.
- **일본어(문서 117건)는 개선되지 않는다** — 사전의 `lang: ja` 표면형이 0개다(위험 A 확증 · D-21).
  T2 의 언어 축에서 외국어군이 움직이지 않는 것은 **예상된 결과**이지 사후 해명이 아니다.
- **`skos:broader` 11 → 18 은 T1·T2 에 비가시다** — P1 점수식의 `w_h = 0`(D-02). 사전 자인.
- 이 문단은 **결과를 보기 전에 작성됐다**(커밋 해시가 증거).

---

## 5. 확증과 탐색의 구분 — 섞지 않는다

| 산출 | 지위 |
|---|---|
| T1 · T2 · T3 판정과 `Accept` (system=P1 · split=test) | **확증** — H2 의 결과. 원고 §8.1 의 "미검정" 항목을 대체한다 |
| 개념 링크 밀도 · 어휘 규모 · 축 분포 · 발화/무발화 표면형 | **진단** — CR 회신용(C0) |
| nDCG@20 · MRR · bpref · 다른 시스템(B0–B5·P0★)의 Δ | **탐색적** — "확증"으로 인용하지 않는다 |
| D-20(`hf` 오링크 1,234문서) 규모 재측정 | **진단** — 상류 CR 재료 |
| H3 · H4 · H5 | **판정하지 않는다.** 개봉된 분할이므로 재확증 불가 — B층(PLAN-031)의 몫 |

---

## 6. 실행 절차 — 동결 커밋 이후 중간 승인 없이 완주

```
[O 팔]  git checkout 83fd494 -- data/external/sdkb/     # 구 스냅샷 복원(16파일)
        make snapshot            # 무결성 — PROVENANCE sha256 대조
        make baseline            # graph_v0 재조립
        make corpus              # ← P-1 판정(ec5ea51b…)
        python -m sdkb_paper.ontology.concept_axis      # ← P-2 판정(5caac56e…)
        make index / dense / hybrid / tables SPLIT=test # run 재산출 ← P-3 판정
        make leakage SPLIT=test  # ← P-6
        make freeze-runset LABEL=O_d578bf3_linkercode SPLIT=test

[O′ 팔] make vendor              # 2839afb + mappings/concept_mapping.json
        make snapshot
        make baseline
        make corpus              # ← P-4 판정(서명 변화)
        python -m sdkb_paper.ontology.concept_axis
        make index / dense / hybrid / tables SPLIT=test
        make leakage SPLIT=test  # ← L-2b 가 실사전을 검사
        make freeze-runset LABEL=Oprime_2839afb SPLIT=test

[판정]  make tgate-resource OLD=O_d578bf3_linkercode NEW=Oprime_2839afb SYSTEM=P1 SPLIT=test
        make eval / figures
```

- **`leakage` 와 `gate` 를 주변 검증으로 빼지 않는다**(§2.1). 누출이 0 이 아니면 Recall 전체가 무효고,
  T1·T2 출력은 부수 확인이 아니라 **H2 의 증거 그 자체**다.
- **C0(결함 등재·CR 작성)는 실행이 끝난 뒤 배치로 처리한다.** 임계경로에 올리지 않는다.
- 각 팔이 재생성하는 `data/profiles/*.md`·`data/MANIFEST.md` 는 팔별로 scratchpad 에 보존하고,
  최종 보고와 함께 커밋한다. **코드 경로가 아니므로 E4 에 영향을 주지 않는다**(§2.2).

### 6.1 보고 형식

결론 먼저 — `Accept` 값과 깨진 조건. 이어서 적격심사 E1–E7 · T1(ΔR₁₀₀ 점추정·95% CI 하한) ·
T2(축별 최대 하락) · T3(스위트별 통과율 O vs O′) · 누출 감사 · P-1~P-6 판정. 그 다음 탐색적 수치.
**기각·무효과·건너뛴 단계는 먼저 알린다.**

---

## 7. 이 사전등록이 §1-2·§1-3 을 위반하지 않는 이유

§1-3 이 금지하는 것은 **결과를 본 뒤 같은 실험의 조건을 바꾸는 것**이다. 이것은 새 자원(적용기가
개설한 도달 경로) 위의 **새 실험**이고, 구 판정(PLAN-030 의 "미검정")은 소급 수정하지 않는다.
E4 범위 변경(§2.2)도 **결과를 보기 전**의 변경이며, 그 변경으로 통과가 쉬워진 것은 자원 교체
상황뿐이고 코드 오염은 여전히 실격이다.

---

## 부록 A — 동결 서명 (사전등록 시점 실측)

| 대상 | sha256 |
|---|---|
| O 스냅샷 서명(16+2파일 · `83fd494` PROVENANCE) | `6cfb743d3d88…` (상류 `d578bf3074edbab4cdd39c21917cb44684dc8400`) |
| O′ 스냅샷 서명(현행 17파일 · 사전 편입 전) | `b98ad787d1fe…` (상류 `2839afb87825874eb4f299e02c30d6d801d49c6a`) |
| `concept_mapping.json` | `dc73bae2cc5e161860b0bfebf13df97aa3c210df5c1c40380bb70a468678528c` |
| `ir_corpus_v09.parquet` (무사전) | `ec5ea51b626d3ff92f62fd1279a5cbae5abcc4cdd0a07e6d0311f35af8db2b43` |
| `concept_axis.parquet` (무사전) | `5caac56ec3bfdd9d3809c1a204e016e84afcbe8882d4626380e8a06e73991f81` |
| `qrel_examiner.parquet` | `10ab67f21cc1328dadafe3d94c1bbfd64462ac34268f7bafd1574b26b923d541` |
| `qrel_test_sealed.parquet` | `984f8ef3dfd3befc1745bddf8928ce09dcdea03957e984150dd71e35dfbfda2c` |
| `split.parquet` | `c25775b346fa395c6c4e0b2e0d4b633ef0bf35bf547d3651e96c0ce9e6fc0bb7` |
| `graph_v1.ttl` | `41094e9f053d6b4c0504bc6de0abcc391ae9c14370425c57950a2c7786164869` |
| `graph_v2.ttl` | `16b4f3223e049762dbc33ef820002ecf1fb34c0bbd305a7b3f8f64506d8a0763` |
| O 팔 기대 run (`O_pre_linker`) | B0 `889bebb7…` · B2 `02854720…` · B3 `29cdd11b…` · B4 `e058a207…` · B5 `8f894d33…` · P0★ `77d1413c…` · **P1 `a1f72f92…`** |

## 부록 B — 실행 결과 (실행 후 기계적으로 채운다)

`[실험 후 기입]`
