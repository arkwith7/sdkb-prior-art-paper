# PLAN-043 — 사전등록: CR-013(원소 기호 별칭 정밀도) 반영 스냅샷의 전량 재측정

> **상태: 조건·서명 동시 동결 · 실행 전 🛑**
> 근거 절차: [CLAUDE.md §2.1](../../CLAUDE.md) "자원 버전이 바뀌면 — 정지 게이트 1개로 전량 재측정".
> **이 커밋이 그 유일한 정지점이고, 이후 §5 는 중간 승인 없이 관통한다.**
>
> **선행:** 하류 CR [CR-013](../../upstream/CR-013-element-symbol-alias-precision.md)(2026-08-07 송부) ·
> 상류 회신 `~/Dev/sdkb/docs/project/reply_cr013_element_symbol_alias_precision.md`(커밋 `4f3dbfb`) ·
> [PLAN-042](PLAN-042-cr011-central-axis-reprep.md)(중심축 CR-011 반영 · 판독 B 개봉 보류) ·
> [PLAN-035](../archive/PLAN-035-h2-linker-preregistration.md)(O/O′ 두 팔 프로토콜).
>
> **이 사전등록이 새로 고르는 것은 하나도 없다.** ε·δ·주지표·분할 경계·판정식·봉인 해시는
> 전부 PLAN-031/035/040 에서 동결됐고 그대로 승계한다. 새로 적는 것은 **서명 표(§1)** 와
> **재산출된 예측값(§3)** 둘뿐이며, 후자는 **결과를 보기 전에** 산출됐다.

---

## 0. 한 문장

**상류가 CR-013 의 두 줄(단독 `hf` 제거 · `high k` → `material:dielectric` 재지정)을 구현해
스냅샷 서명 4건이 바뀌었으므로, 코드를 한 줄도 바꾸지 않은 채 자원만 교체해 전량 재측정하고,
검증기준 ①–⑦ 을 판정한다.**

---

## 1. §2.1 발동 근거 — 서명이 바뀐 것은 **네 파일**이다

발동 조건은 "T-Box 변경"이 아니라 **스냅샷 서명 변경**이다. 실측(2026-08-08 · `sha256sum` ·
상류 워킹트리 `4f3dbfb` · `git status --porcelain` = 0행):

| 자산 | 현 스냅샷 sha256 | **상류 워킹트리 sha256** | 회신 §5 와 | 판정 |
|---|---|---|---|---|
| `mappings/concept_mapping.json` | `b2da08e7c261465e4d50b0228f05fdcc2edc6b30b26643c90e1cffa2ab9cf09a` | `cdf5fa5dc1dcc2b41eec61cae2c470b8c866d838eadb20ba38f93d4a4d4698f4` | 일치 | **변경** |
| `mappings/abox_term_aliases.json` | `f54ff7ea434612ccb91a3c33f1e4480de0be4d0a04cb30e3a9fa682e990ed179` | `9c8bbeb2067beab4a0f592e54e6103906c2d95a47b6f14f0825d6b954d17030b` | 일치 | **변경** |
| `ontology/sdkb-abox-patents.ttl` | `3c16ad2597ba31db20407da0b3d3c9497cd1662f94575d471b3551f9b9583089` | `974899fa414f7444f64e578399056b4b1d014b2cfdcfe120685cbb8af458fcf5` | 일치 | **변경** |
| `ontology/sdkb-abox-prior-art.ttl` | `1abbf5e54f66c8dc49e203244b5c3925369839524a5fd22768abf3aae137c3fd` | `e96d987358206f75f2fe2b444753c33dfd4e972ee006d18bea3af9068d5ff76b` | 일치 | **변경** |
| `ontology/sdkb-core.ttl` · `sdkb-core-data.ttl` | `256346fc…` · `f366a764…` | 동일 | 일치 | **불변**(T-Box 델타 0) |
| 나머지 vendor 대상 12파일 | — | 바이트 불변 | — | **불변** |

**상류 A-Box TTL 두 개는 gitignore 된 빌드 산출물이라 커밋 `4f3dbfb` 에 들어 있지 않다.**
그래서 위 대조는 **재빌드된 상류 워킹트리**에서 떴고, 네 값이 회신 §5 와 **전부 일치**한다.
(어긋났다면 "상류가 다른 것도 바꿨다"가 아니라 재빌드 문제였다.)

### 1.1 `make vendor` 는 **필요하다** — 네 파일 전부 `VENDOR_FILES` 다

CR-011 때는 바뀐 파일이 `VENDOR_FILES` 에 0개여서 vendor 가 답이 아니었다(PLAN-042 §1.1).
이번은 반대다 — 바뀐 4개가 **전부** `VENDOR_FILES` 에 있다(`vendor.py:42·45·54·59`).

**다만 상류 `make` 재빌드는 돌리지 않는다.** `make vendor` 의 첫 줄은
`$(MAKE) -C $(SDKB_HOME) owl convert abox …` 로 **상류 저장소를 쓴다**. 상류는 이미
CR-013 구현 후 재빌드했고 그 산출물의 sha256 이 회신 §5 와 위 표대로 일치하므로, 지금
재빌드는 얻는 것 없이 **하류가 상류를 수정하는 일**이 된다(§0.1 — 이 저장소는 상류를 직접
수정하지 않는다). 그래서 vendor 의 **복사·검증 단계만** 돌린다:

```
uv run python -m sdkb_paper.ontology.vendor --sdkb-home ~/Dev/sdkb
```

신선도(L0)는 이 단계가 독립적으로 강제한다 — `_reject_stale_artifacts()` 가 산출물 mtime 을
빌드 스크립트 mtime 과 대조하고, 낡으면 `SystemExit` 로 멈춘다(`vendor.py:319–338`).
**vendor 후 네 파일의 sha256 이 회신 §5 와 다르면 그 자리에서 멈춘다.**

### 1.2 중심축은 이번 범위가 아니다

`CENTRAL_AXIS_SRC`(`sdkb-abox-claim-features.ttl`)는 **바이트 불변**이다. CR-013 은 청구항
사이드카를 건드리지 않았으므로 `central_axis build` 를 돌리지 않는다.

---

## 2. 승계 — 조건은 하나도 재선택하지 않는다

| 항목 | 값 | 출처 |
|---|---|---|
| 주지표 | **family-level Recall@100** | 동결 |
| ε · δ | **0.02 · 0.05** | 동결 |
| 승인식 | `Accept = (L0..L3) ∧ (LB₉₅(ΔR₁₀₀) > −ε) ∧ (max_s drop_s < δ) ∧ (∀f∈{em,tf,core}: pass_f(new) ≥ pass_f(old))` | CLAUDE §5 |
| 분할 경계 | 시점·family-disjoint 60/20/20 · `split.parquet` 불변 | 동결 |
| 봉인 qrel (A층 test) | `qrel_test_sealed.parquet` = `984f8ef3dfd3befc…` | 불변 |
| 봉인 qrel (B층 · **열지 않는다**) | `qrel_b_sealed.parquet` = `127a138f1c165167…` | **불변 · 개봉 금지** |
| 검색 설정·가중치·토큰화·Dense 모델 | **전부 동결** — 코드 변경 0 | §2.1 안전장치 |
| 두 팔 프로토콜 | 재vendor **전에** O 팔 run 을 얼린다 | Makefile `freeze-runset` 주석 · PLAN-035 |

**판독 B(B층 확증)는 이 사전등록의 범위가 아니다.** CR-012 회신 대기 중이고, D-27(질의 노드
부재)이 해소되지 않았다. 봉인은 열지 않는다.

---

## 3. 검증기준 — CR-013 §6 의 일곱, 그중 ⑤ 는 재산출됐다

| # | 기준 | 합격선/예측 | 성격 | 판정자 |
|---|---|---|---|---|
| ① | 사전 `patent-text` entries 에 단독 `hf` 표면형 | **0건** | 자원 | 하류 재확인 |
| ② | `high k` 가 `material:hfO2` 를 가리킴 | **0건** | 자원 | 하류 재확인 |
| ③ | 재조립 후 `material:hf_acid` 문서 | **1,522 → 412** | 하류 | `concept_links.parquet` |
| ④ | 재조립 후 `material:hfO2` 문서 | **391 → 298** | 하류 | 〃 |
| ⑤ | 고유 (doc,concept) 쌍 | **106,496 → 105,347** (−1,149) | 하류 | 〃 |
| ⑤-b | 코퍼스 union (doc,concept) 쌍 | **154,264 → 153,133** (−1,131) | 하류 | `ir_corpus_v09.parquet` |
| ⑥ | 교차 태스크 CQ(em·tf·core) 통과율 하락 | **0** (T3) | 상류→**하류** | `make gate` |
| ⑦ | P1 family Recall@100 (ΔR₁₀₀) | **합격선 없음 — 보고만 한다** | 태스크 | `results_table`·`tgate-resource` |

**출처:** `data/profiles/plan043_prediction.md`(생성기 `scripts/plan043_predict.py` ·
이 커밋에 포함). 수치는 손으로 옮겨 적지 않았다(§1-7).

### 3.1 ⑤ 가 재산출된 이유 — 상류가 **제거가 아니라 재지정**을 골랐다

CR-013 §6 의 ⑤(106,496 → 105,293)는 ⓑ 를 **순수 제거**로 가정한 값이다. 상류는 CR §3.4 의
문언대로 `material:dielectric` 으로 **재지정**했고(회신 §2 · CR-007 이 같은 용도로 만든 상위
부류 노드 · 어휘 신설 0), 그래서 `high k` 문서 중 아직 `dielectric` 이 없던 문서만큼 쌍이
되돌아온다. **동결 전에 다시 계산했고 그 결과가 위 표의 105,347 이다.**

분해는 셋이고 그게 전부다 — 단독 `hf` 로만 `hf_acid` 를 얻던 문서 **−1,110** · `high k` 로만
`hfO2` 를 얻던 문서 **−93** · `high k` 로 `dielectric` 을 새로 얻는 문서 **+54**.

**방법이 아니라 상류의 선택이 바뀌었다는 증거:** 같은 스크립트로 순수 제거판을 계산하면
**105,293** 이 그대로 재현된다(예측 파일 §1.2). 즉 구 예측의 산술은 옳았고 전제가 달라졌다.

### 3.2 ⑤-b 를 새로 세는 이유 — 잣대가 둘이다

코퍼스의 `concepts` 열은 **A-Box 그래프 링크 ∪ 적용기 링크**다
(`concept_link.apply_to_corpus:132`). ⑤ 는 적용기 산출물만 세므로 상류의 A-Box 정리
(회신 §3 · `hf_acid` 링크 34 → 15)가 잡히지 않는다. 그 정리는 ⑤-b 에만 나타난다.
**두 수가 다른 것은 오류가 아니다** — 어느 쪽인지 밝히지 않고 "개념 링크 수"라고 쓰는 것이
오류다.

### 3.3 ⑥ 은 하류가 자기 스위트로 잰다

상류에 `em`·`tf`·`core` 스위트가 없다(회신 §1.1 — 지어내지 않고 산출 불가로 회신했다).
스위트 분할은 하류 자산(`queries/cq/*.rq`)이므로 **⑥ 의 판정자는 하류의 `make gate`(T3)** 다.
T3 는 통계검정이 아니라 결정론적 통과율 비교이며, 하락하면 그 자리에서 실패다.

### 3.4 ⑦ 에 합격선을 걸지 않는다 — 그리고 **확증으로 쓰지 않는다**

CR-013 §6 이 결과 전에 정한 그대로다. 덧붙여 A층 test 는 **이미 1회 개봉된 표본**이므로,
§2.1 안전장치상 허용되는 것은 사전등록된 승인 규칙의 적용과 **탐색적 재측정**뿐이다.
**이 값으로 H3 를 재확증하지 않는다.**

---

## 4. 미리 자인하는 것 — 이 재측정이 **하지 못하는** 것

**ⓐ T1·T2 는 E7(델타 유형 자격)에서 미검정이 나올 것으로 예상한다.** CR-013 은 A-Box 파일
둘의 서명을 바꾸고, `classify_delta()` 는 파일명 표지(`abox-patents`·`abox-prior-art`)를 보고
델타를 **`abox`** 로 분류한다(`runset.py:159–184`). `H2_ELIGIBLE_DELTA_TYPES = ("tbox",
"concept")` 이므로 E7 은 실격을 내고, 그것은 **불통과가 아니라 미검정**이다(종료코드 2).
**실질은 ②개념층 델타에 가깝다** — 문서집합은 한 건도 늘지 않았고 바뀐 것은 개념 **링크**
19건이다. 그러나 **분류기를 고치지 않는다**: 코드를 손대는 순간 §2.1 이 아니라 §2 전체가
적용되고, 결과를 본 뒤 자격 규칙을 고치는 모양이 된다(§1-2·§1-3). 미검정은 미검정으로
보고하고, 필요하면 **다음 사전등록에서 분류기 개정을 별건으로** 다룬다.

**ⓑ 두 팔의 O 쪽 run 을 새로 산출한다 — 디스크의 run 이 낡았기 때문이다.** 현 `sys_*` run 은
2026-08-01(PLAN-035) 산출이고, 그 뒤 PLAN-042 가 코퍼스를 재조립했다(청구항 본문 충전 ·
sha `1a108009…`). 낡은 run 을 O 팔로 쓰면 ΔR₁₀₀ 이 **CR-011 본문 충전 + CR-013 사전 변경**을
합친 값이 되어 D-23 의 "미구분"이 재발한다. 그래서 **vendor 전에** 현 자원 위에서 run 을
재산출해 얼린다. 이것은 조건 변경이 아니라 **같은 파이프라인의 재실행**이다.

**ⓒ CR-012 와 묶지 않는다.** CR-012 회신이 이 관통 도중 도착해도 **같은 스냅샷에 함께 싣지
않는다.** 묶으면 변인이 둘이 되어 원인을 가르지 못한다(D-23 · DP4).

**ⓓ D-28 은 이 재측정으로 해소되지 않는다.** 적용기의 `.lower()` 정규화가 대소문자 판별자를
지우는 문제는 하류 소관 코드 변경이라 §2 전체를 타는 별건이다. CR-013 은 그것을 **요구하지
않았고**, 그래서 하프늄 666 문서·불산 370 문서의 신호가 함께 사라지는 손실이 남는다.

**ⓔ 판독 B 는 열지 않는다.** 봉인 `127a138f…` 불변.

**ⓕ `make tables` 를 돌리지 않는다.** 원고 §6.2 확증 표는 **O 팔** 산출이고 디스크 자원은
그 뒤 세대다. run 산출은 `results_table --split test`(**`--write` 없이**)로만 한다 —
`build_runs()` 가 run 을 쓰고 `--write` 는 원고 표를 덮는다(`results_table.py:67·300`).

---

## 5. 실행 순서 — 중간 승인 없이 관통한다

```
(1) 이 사전등록 커밋                                          ← 유일한 정지점 🛑
(2) [O 팔] results_table --split test (write 없음) → make leakage SPLIT=test
        → make freeze-runset LABEL=O_pre_CR013 SPLIT=test     ← 재vendor 전에 얼린다
(3) vendor 복사·검증 (§1.1) → 네 파일 sha256 = 회신 §5 대조    ← 어긋나면 정지
(4) make snapshot → make baseline → make corpus               ← ③④⑤⑤-b 판정
(5) python -m sdkb_paper.ontology.concept_axis
(6) make index → make dense → make hybrid
        → results_table --split test (write 없음)
(7) make leakage SPLIT=test                                    ← 금지 간선 0 (T1 의 전제)
(8) make freeze-runset LABEL=O_post_CR013 SPLIT=test
(9) make tgate-resource OLD=O_pre_CR013 NEW=O_post_CR013 SYSTEM=P1 SPLIT=test   ← ⑦ · T1·T2
(10) make gate SPLIT=test                                      ← ⑥(T3) · L0–L3
(11) 결과 보고 → 그 다음에 C0 (D-20 종결 · CR-013 archive · 대기열·STATUS 갱신)
```

**(1) 의 커밋 전에는 (2) 이후를 돌리지 않는다.** 순서를 뒤집으면 사후 사전등록이다(§1-3).
**(3) 에서 sha256 이 어긋나면 (4) 로 가지 않는다.**
**(9)·(10) 사이에 판정 기준을 고치지 않는다.**

---

## 6. 보고 의무 (§4 · §8)

- **코퍼스 증분 프로파일** — 행수 41,031 → `[기입]` · 코퍼스 sha256 전후 · 문서당 개념 전후 ·
  언어분포 · 결측·중복.
- **검증기준 표 ①–⑦ 을 예측 대 실측으로 나란히** 적는다. 어긋난 칸은 **어긋났다고** 적고,
  그 자리에서 원인을 묻는다(CR-013 §6).
- **T1·T2 가 미검정이면 미검정으로** 적는다 — `Accept` 를 산출하지 않는다.
- **⑦ 의 부호가 어느 쪽이든 그대로 적는다.** 나빠지면 나빠진 대로다 — 합격선을 걸지 않은
  이유가 그것이다(D-23).
- 기각·무효과·구조적 0을 적을 때는 **그것이 상류에 요구하는 수정**을 함께 적는다(C0).

---

## 7. 승인 기록

| 항목 | 상태 |
|---|---|
| §1 서명 기입 (sha256 4건 · 상류 `4f3dbfb` · dirty=false) | ✅ 이 커밋 |
| §3 예측값 재산출 (⑤ 105,347 · ⑤-b 153,133) | ✅ 이 커밋 (`data/profiles/plan043_prediction.md`) |
| §5 실행 | 이 커밋 이후 무정지 관통 |
