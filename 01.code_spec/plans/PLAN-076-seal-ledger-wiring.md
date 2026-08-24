# PLAN-076 — 봉인 열람 원장 배선 교정 (O-6 · PLAN-068 트랙 C)

> **1단계 요구정의 · 🛑 승인 대기.** CLAUDE.md §2 정지 게이트 4개를 그대로 탄다
> (요구정의 🛑 → 분석 🛑 → 설계 🛑 → 구현 → 검증 🛑).
> **순서 근거:** OPEN-ITEMS O-6 의 해소 주석 — PLAN-075 §3 선택지 ⓒ 로 순서 제약이 풀렸고,
> 다음 사전등록(λ 선택 · **PLAN-077 로 번호가 밀린다**)이 동결되면 창이 닫힌다.
> **판정·수치는 이 작업으로 하나도 바뀌지 않는다** — 남은 것은 배선뿐이다(O-6 실측).

---

## 1. 목적 — 어느 주장을 지지하는가

**C0·C2·C2′ 의 감사 가능성.** 이 작업은 새 증거를 만들지 않는다. 원고가 Methods 에서
주장하는 정직성 장치(사전등록 순서 · 봉인 · 열람 원장)가 **실제 배선으로 뒷받침되는가**를
맞춘다. CLAUDE.md §0.8 봉인 개봉 행은 2026-08-22 에 이미 **층 한정**을 넣어 교정됐고
(*"판독 B 봉인에 대한 모든 접근"*), 이 계획은 그 한정을 **배선으로도 참으로** 만든다.

**논문 자리.** 파생본 Methods 의 절차 1문단(§8.1) + supplementary 의 원장 전문. 본문 문장은
바뀌지 않는다 — 바뀌면 그것은 이 계획이 아니라 §2.2 다.

---

## 2. 대상 셋 (PLAN-068 트랙 C 원문)

### C-1 · A층 `test` 분할이 봉인 통로를 거치지 않는다 — **본체**

**실측 (2026-08-24).**

| 자리 | 현 상태 |
|---|---|
| `analysis/metrics.py:53` | `qrel_path_for_split()` 이 `test_b` 에만 `B_QREL_SEALED` 를 주고, `test` 는 `QREL_EXAMINER`(전량 qrel)를 직접 읽는다 |
| `open_sealed()` 통과 여부 | `test_b` 만 통과 · `test` 는 미통과 |
| 원장 실측 | 25행 · **전량 `qrel_b_sealed.parquet`** · A층 행 **0** |
| A층 봉인 사본 `qrel_test_sealed.parquet` | 소비자는 있다 — `rag/context.py:153` · `rag/score.py:207` · `rag/t4.py:57` · `analysis/effort.py:67` 이 **`load_qrel()` 로 직접** 읽는다(전부 `open_sealed()` 우회) |

**즉 결함은 둘이다.** ① `metrics` 의 `test` 경로가 봉인 사본이 아니라 전량 qrel 을 가리킨다.
② 봉인 사본을 읽는 네 소비자가 통로를 우회한다. **PLAN-068 이 적은 "소비 경로가 없는 사본"은
정확히는 "통로 밖 소비 경로가 넷 있는 사본"이다** — 실측으로 정정한다.

### C-2 · 원장이 버전관리 밖이다

`seal_access.jsonl` 이 `.gitignore:9`(`data/processed/*`)로 무시되어 커밋 이력 0건이다.
추가전용 파일의 무결성을 커밋으로 증명할 수 없다. **파일 내용은 시각·커밋·호출자·경로·
sha256·사유뿐이라 원문이 0열이며, §1-5 가 막는 대상이 아니다.**

### C-3 · `verdicts.yaml` 키 함정

허용 문구 키는 `allowed` 가 아니라 `composite_allowed` 이고(`scripts/check_verdicts.py:126`),
오타로 적으면 검사기가 **조용히 무시한다**(EP5 에서 실제 발생). 회귀 테스트로 고정한다.

---

## 3. 입력 · 출력

**입력 (읽기 전용 · 어느 것도 바꾸지 않는다).**
`src/sdkb_paper/analysis/metrics.py` · `validate/seal_audit.py` · `rag/{context,score,t4}.py` ·
`analysis/effort.py` · `config.py` · `.gitignore` · `paper/verdicts.yaml` ·
`scripts/check_verdicts.py` · `data/processed/ir/seal_access.jsonl`(25행 · **추가만**).

**출력.**
1. `src/` 배선 변경(범위는 3단계 설계에서 확정) + 회귀 테스트.
2. `.gitignore` 예외 1줄 + 원장 최초 커밋.
3. `tests/` 에 검사기 키 회귀 테스트.
4. 이 문서에 2·3·5단계 기록.

---

## 4. 성공기준 (검정가능)

| | 기준 | 검증 방법 |
|---|---|---|
| **S1** | A층 `test` qrel 적재가 `open_sealed()` 를 지나고 원장에 1행을 남긴다 | 원장 행수 증분 · `caller` 필드가 호출자를 지목 |
| **S2** | **수치 불변** — 교정 전후 A층 `test` 평가 지표가 **비트 단위로 동일**하다 | 동일 run 파일로 `make eval` 2회 · 산출 md/csv sha256 대조 |
| **S3** | 봉인 사본 소비자 넷이 전부 통로를 지난다 | `grep` 로 `load_qrel(config.IR_QREL_TEST_SEALED)` **0건** |
| **S4** | B층 배선은 **무변경** — `test_b` 의 거부 기본값과 사유 요구가 그대로다 | 기존 `tests/test_b_layer_readout.py` 통과 |
| **S5** | 원장 기존 25행 **불변**(추가만) | 앞 25행 sha256 대조 |
| **S6** | 검사기 키 오타가 실패로 드러난다 | 회귀 테스트: `allowed` 키를 쓴 합성 스펙에 대해 검사기가 경고/실패 |
| **S7** | `make lint && make test` · `make verdicts` · `make sig-check` 통과 | 명령 출력 |

**S2 가 이 계획의 안전 조건이다.** A층 경로가 전량 qrel → 봉인 사본으로 바뀌면 **내용이
같은지**가 판정 불변의 전제이며, 2단계에서 두 파일을 실제로 대조한 뒤에야 설계로 넘어간다.
같지 않으면 **거기서 멈추고 보고한다** — 그때는 배선이 아니라 판정 문제다.

---

## 5. 비목표 (하지 않는 것)

- **판정·수치·문구 변경 0.** 원고·`verdicts.yaml` record·§0.8 표는 손대지 않는다.
- **새 실험 0 · 새 사전등록 0 · 봉인 개봉 0**(A층 원장 기록은 개봉이 아니라 **기록의 신설**이다).
- **A층에 `--unseal` 강제를 도입할지는 3단계 결정 사항**이며, 이 문서는 결정하지 않는다.
  A층은 이미 1회 공표 개봉됐으므로 거부 기본값을 넣으면 기존 재현 경로가 전부 막힌다 —
  **선택지 두 개(ⓐ 기록만 · ⓑ 기록 + 명시 허가)를 3단계에 올린다.**
- 리팩터·추상화·"나중에 쓸" 유틸 금지(§1-10).
- `data/external/**` · 봉인 qrel 파일 자체 · 동결 run 파일 무변경.

---

## 6. 다음 단계

**2단계 분석 (승인 후 착수).** ① `qrel_examiner`∩test 와 `qrel_test_sealed` 의 **엣지 집합
동일성 실측**(S2 의 전제) ② 봉인 사본 소비자 넷의 호출 문맥과 사유 문자열 후보
③ 원장 스키마에 `layer` 필드가 필요한가(A/B 구분) ④ 영향 받는 `make` 타깃 목록.

---

## 7. 2단계 분석 — 실측 (2026-08-24 · 🛑 승인 대기)

**결론 먼저.** ① **S2 의 전제는 충족됐다** — 현행 A층 `test` 경로가 읽는 것과 봉인 사본은
**같은 집합**이다(198질의·479엣지·완전 일치). 배선 교체로 수치가 바뀔 여지가 없다.
② 그러나 **결함의 크기가 O-6 기술보다 크다** — 봉인 사본은 파생물이고 **원본
`qrel_examiner.parquet` 안에 A층 test 정답 479엣지가 그대로 들어 있으며**, 그 원본을
`load_qrel()` 로 **맨손으로 읽는 자리가 열 곳**이다. `qrel_path_for_split()` 한 줄만 고치면
**원장은 통로 하나만 기록하고 나머지 열 곳은 그대로 샌다.**

### 7.1 집합 동일성 — S2 의 전제 (통과)

| 대상 | 질의 | 엣지 |
|---|---:|---:|
| 현행 `test` 경로 (`qrel_examiner` ∩ split=test) | 198 | 479 |
| 봉인 사본 `qrel_test_sealed.parquet` | 198 | 479 |
| 봉인 사본 ∩ split=test | 198 | 479 |

**세 집합이 (질의, 문서) 쌍 단위로 완전히 같다**(`==` 판정 True). 봉인 사본 sha256 =
`984f8ef3dfd3befc1745bddf8928ce09dcdea03957e984150dd71e35dfbfda2c`.

### 7.2 원본 qrel 의 구성 — 왜 사본만으로는 부족한가

`qrel_examiner.parquet` 2,416 엣지의 분할 분포(실측):

| 분할 | 엣지 | 질의 |
|---|---:|---:|
| train | 1,418 | 586 |
| dev | 519 | 197 |
| **test (= A층 봉인 대상)** | **479** | **198** |

**B층 질의가 examiner 에 존재하는 건수는 0 이다** — B층 봉인(`qrel_b_sealed.parquet` ·
538행 · `application_number`/`examiner_citations`)은 완전히 별도 파일이다. **따라서 A층
배선을 고쳐도 B층 원장 25행과 그 판정에는 어떤 경로로도 닿지 않는다**(S4·S5 안전).

### 7.3 접근 경로 3분류 — 교정 대상의 전량

| 분류 | 자리 | test 접근 시 원장 |
|---|---|---|
| **(A) 통로 경유** | `metrics.load_qrel_for_split()` — `test_b` 만 `open_sealed()` 통과 | B층만 기록 · **test 는 미기록** |
| **(B) 맨 `load_qrel()` + 수동 분할 필터** — 같은 6줄이 복제돼 있다 | `results_table.py:54`(`_split_qrel`) · `ablation.py:69` · `subgroup.py:245` · `bootstrap.py:128` · `lang_recall.py:62` · `ontology_eval.py:276,345` · `pathsim_diag.py:33` · `overlap.py:87` · `ir_panel.py:66`(dev 고정) | **전량 미기록** |
| **(C) 봉인 사본 직독** | `rag/context.py:153` · `rag/score.py:207` · `rag/t4.py:57` · `analysis/effort.py:67` · `scripts/rerank_ceiling.py:42` | **전량 미기록** |

`increment.py:49` 와 `judgment_robustness.py:248` 은 각각 (B)의 `_split_qrel` 과 (A)를
재사용하므로 **자체 접근점이 아니다.** `bootstrap.py:131` 에는 이미
*"⚠️ test 개봉 — 최종 비교 전이면 사전등록 위반"* 경고가 있으나 **원장에는 남지 않는다** —
사람이 읽는 경고와 기계가 남기는 기록의 차이가 이 계획의 대상 그 자체다.

### 7.4 영향 받는 `make` 타깃

| 타깃 | 기본 분할 | 접근 분류 |
|---|---|---|
| `tables` (results_table · subgroup · increment · ablation · lang_recall · overlap) | **`SPLIT ?= test`** | (B) ×5 |
| `effort` | test 고정 | (C) |
| `rag` · `ragcount` · `rageval` | test 고정 | (C) |
| `crosslingual` | `SPLIT ?= test` | (B) |
| `eval` (`analysis.metrics` CLI) | `--split` 인자 | (A) |
| `tables-b` · `t4` · `retrieve-b` | test_b | (A · 이미 통로 경유) |

**즉 A층 주판독 경로(`make tables`)가 통째로 (B)에 있다.**

### 7.5 원장 스키마 — `layer` 필드가 필요하다

현 원장 25행은 **전량 B층**이고, 필드는 `opened_at·commit·caller·file·sha256·reason` 이다.
A층 행이 섞이면 CLAUDE.md §0.8 이 요구하는 **층 한정 진술**을 사람이 파일명으로 역추론하게
된다. `layer`(`A`/`B`)와 `split` 을 명시 필드로 넣기를 제안한다 — **기존 25행은 손대지
않는다**(추가전용 · S5). 구 행은 `layer` 부재로 식별되며, 판독 코드가 `file` 로 보정한다.

### 7.6 3단계로 넘기는 결정 — 두 개

**결정 1 · 범위.** (A)만 고칠 것인가, (B)·(C)까지 고칠 것인가.

| 안 | 범위 | 얻는 것 | 비용·위험 |
|---|---|---|---|
| **ⓐ 최소** | (A) 한 줄 | 원장에 A층 행이 생긴다 | **주판독 `make tables` 는 그대로 샌다** — 원고가 쓸 수 있는 문구가 *"`eval` 경로의 접근만 기록"* 으로 좁아진다 |
| **ⓑ 전량** (권고) | (A)+(B)+(C) 15자리 | *"A층 test qrel 에 대한 모든 접근이 원장에 남는다"* 가 참이 된다 | (B) 열 자리의 중복 6줄을 `load_qrel_for_split()` 호출로 치환 — **§1-10 이 금지하는 자발적 리팩터가 아니라 성공기준 S1·S3 의 요구**이나, 손대는 파일이 늘어 S2 대조 부담이 커진다 |
| ⓒ 중간 | (A)+(C) | 봉인 사본 소비자는 닫힌다 | (B)가 원본을 직독하므로 **사본을 닫아도 원본이 열려 있다** — 절반의 배선 |

**권고는 ⓑ 다.** ⓐ·ⓒ 는 배선을 고치고도 §0.8 의 진술을 A층으로 넓히지 못하므로, 이 계획의
목적(§1)을 달성하지 못한다. 다만 ⓑ 는 **S2 를 자리마다 확인**해야 하며, 그 대조는
`make tables` 산출물 sha256 전량 대조로 한다.

**결정 2 · A층에 명시 허가를 요구할 것인가.**

| 안 | 동작 | 귀결 |
|---|---|---|
| **ⓐ 기록만** (권고) | `test` 는 열리되 원장에 1행 남는다 | 기존 재현 경로 전부 유지 · 원장이 **실행마다** 자란다(현 25행 → 실행당 +1) |
| ⓑ 기록 + 명시 허가 | `test` 도 `--unseal` 필요 | `make tables`·`effort`·`rag` 계열이 전부 인자를 요구 — **A층은 이미 1회 공표 개봉됐으므로 얻는 것이 없다** |

**권고는 ⓐ 다.** A층 봉인의 목적(최종 비교 전 미열람)은 이미 소진됐고, 지금 필요한 것은
**금지가 아니라 기록**이다. 원장이 자라는 것은 결함이 아니라 이 장치의 정상 동작이며,
§0.8 이 요구하는 것도 *"1회 개봉"* 이 아니라 *"모든 접근의 기록"* 이다.

**두 결정 모두 3단계 설계 게이트에 올린다 — 이 문서는 결정하지 않는다.**

---

## 8. 3단계 설계 (2026-08-24 · 🛑 승인 대기)

**두 결정은 §7.6 의 권고대로 확정됐다(2026-08-24 사용자 승인).**
**범위 = ⓑ 전량**(A+B+C 15자리) · **A층 = ⓐ 기록만**(명시 허가 요구 없음).

### 8.1 통로 단일화 — 무엇이 유일한 문이 되는가

`analysis.metrics.load_qrel_for_split(split, *, unseal, reason)` 를 **모든 분할의 유일한
적재 통로**로 삼는다. 맨 `load_qrel()` 는 남기되 **경로 인자를 반드시 받는 저수준 판독기**로
지위를 낮춘다(인자 없는 호출은 회귀 테스트가 금지한다 · §8.5 T5).

```
qrel_path_for_split(split) -> Path
    "test_b" → B_QREL_SEALED          (불변)
    "test"   → IR_QREL_TEST_SEALED    (신설 — 현행은 QREL_EXAMINER)
    그 외     → QREL_EXAMINER          (불변)
```

**`test` 의 경로를 사본으로 바꾸는 근거는 §7.1 의 집합 동일성**이다(198질의·479엣지 완전
일치). 사본을 정본으로 삼아야 *"봉인 파일을 열었다"* 는 기록이 파일명과 sha256 으로
자기증명된다 — 원본을 가리키면 원장의 `sha256` 이 train·dev 를 포함한 전량의 해시가 되어
무엇을 열었는지 지목하지 못한다.

### 8.2 기록 대상 규칙 — 무엇을 열면 원장에 남는가

| split | 읽는 파일 | 원장 | 허가 |
|---|---|---|---|
| `test_b` | `qrel_b_sealed.parquet` | 1행 (`layer="B"`) | **`unseal=True` 필요**(불변) |
| `test` | `qrel_test_sealed.parquet` | 1행 (`layer="A"`) | 불필요 — 기록만 |
| `all` | `qrel_examiner.parquet` | 1행 (`layer="A"` · `split="all"`) | 불필요 — 기록만 |
| `dev` · `train` | `qrel_examiner.parquet` | **없음** | — |

**`all` 을 기록 대상에 넣는 이유.** `all` 은 필터를 걸지 않으므로 **test 479엣지가 결과에
들어온다**(§7.2). 기록하지 않으면 `--split all` 이 배선을 우회하는 뒷문이 된다.
**`dev`·`train` 은 봉인 대상이 아니므로 기록하지 않는다** — 개발 실행마다 원장이 자라면
원장의 신호가 잡음에 묻힌다.

### 8.3 `open_sealed()` 시그니처 확장

```python
def open_sealed(path, *, reason: str, allow: bool,
                layer: str = "B", split: str | None = None) -> Path
```

- 기록 필드에 `layer`·`split` 을 **추가**한다. 기존 여섯 필드(`opened_at`·`commit`·
  `caller`·`file`·`sha256`·`reason`)는 이름·의미 **불변**.
- **기존 25행은 손대지 않는다**(추가전용 · S5). 구 행은 `layer` 부재로 식별되며,
  `access_log()` 판독기가 `file` 로 `layer="B"` 를 보정해 돌려준다.
- `allow=False` 거부와 빈 사유 거부는 **그대로**다(B층 동작 불변 · S4).
- A층 호출은 `allow=True` 로 고정하되 **사유는 여전히 필수**다 — 호출자마다 기본 사유
  문자열을 준다(예: `"A층 재판독(split=test · analysis.results_table)"`).

### 8.4 자리별 변경 명세 — 15자리

**(B) 맨 `load_qrel()` + 복제된 분할 필터 → `load_qrel_for_split()` 호출 (10자리)**

| 파일 | 줄 | 비고 |
|---|---|---|
| `analysis/results_table.py` | 54 (`_split_qrel`) | 이 함수 자체가 통로의 중복 구현 — 본문을 위임으로 교체 |
| `analysis/ablation.py` | 69 | |
| `analysis/subgroup.py` | 245 | |
| `analysis/bootstrap.py` | 128 | 기존 `⚠️ test 개봉` 경고는 **남긴다**(사람용 · 원장과 목적이 다르다) |
| `analysis/lang_recall.py` | 62 | |
| `analysis/ontology_eval.py` | 276 · 345 | 2자리 |
| `analysis/pathsim_diag.py` | 33 | |
| `analysis/overlap.py` | 87 | `split=None` → `"all"` 로 정규화 |
| `explore/ir_panel.py` | 66 | dev 고정 — 기록 없음 · 호출 형태만 통일 |

**(C) 봉인 사본 직독 → 통로 경유 (5자리)**

| 파일 | 줄 | 교체 |
|---|---|---|
| `rag/context.py` | 153 | `load_qrel(config.IR_QREL_TEST_SEALED)` → `load_qrel_for_split(split, reason=…)` |
| `rag/score.py` | 207 | 〃 |
| `rag/t4.py` | 57 | 〃 |
| `analysis/effort.py` | 67 | 〃 |
| `scripts/rerank_ceiling.py` | 42 | 〃 (모듈 경로 상수 `QREL` 제거) |

**세 파일의 `if split == SPLIT_B: … else: …` 분기는 사라진다** — 통로가 분할을 보고 스스로
경로를 고르므로 호출부에 분기가 필요 없다. **분기 제거는 리팩터가 아니라 이 계획의 목적
자체**다(우회 경로를 남기지 않는다).

**바꾸지 않는 것.** `metrics.load_qrel(path)` 저수준 판독기 · `corpus/split.py` 의 봉인
산출 · `validate/{leakage_check,runset}.py` 의 **경로 참조**(파일을 sha256 대상으로만 쓰고
qrel 내용을 읽지 않는다) · `corpus/qrel_family_merge.py`(이미 통로 경유).

### 8.5 회귀 테스트 명세 — `tests/test_seal_wiring.py` (신설)

| | 이름 | 검사 |
|---|---|---|
| **T1** | 경로 배선 | `qrel_path_for_split` 이 test→사본 · test_b→B봉인 · dev/train→examiner |
| **T2** | **S2 동일성** | `load_qrel_for_split("test")` == `load_qrel(QREL_EXAMINER)` 를 split=test 로 거른 것 — **§7.1 을 코드로 고정한다** |
| **T3** | A층 기록 | 임시 원장으로 `test` 적재 → 1행 증가 · `layer=="A"` · `split=="test"` · `caller` 가 호출자 지목 |
| **T4** | dev 무기록 | `dev` 적재 → 행 증가 **0** |
| **T5** | 우회 금지 (소스 스캔) | `src/`·`scripts/` 에 인자 없는 `load_qrel()` 와 `load_qrel(config.IR_QREL_TEST_SEALED)` **0건** |
| **T6** | B층 불변 | `load_qrel_for_split("test_b", unseal=False)` 가 `SealedAccessError`(기존 `test_b_layer_readout.py` 와 중복 아님 — 저쪽은 경로, 이쪽은 거부) |
| **T7** | 검사기 키 함정 | `check_verdicts` 가 **미지 키**를 담은 스펙에 rc 2 로 실패 |

**T7 의 구현.** `scripts/check_verdicts.py` 에 **엄격 키 검사**를 넣는다 — 허용 키는
verdict 항목 `{forbidden, composite_allowed, exempt_line, scan_raw, record}` · meta
`{plan, frozen_date, scan_targets, exempt_tables_with_header}` (현 yaml 실측 전량 · 10라벨).
그 밖의 키가 나오면 **조용히 무시하지 않고 rc 2 로 멈춘다.** `paper/verdicts.yaml` 자체는
**한 글자도 고치지 않는다**(§1-2 동급 규율).

### 8.6 S2 검증 절차 — 수치 불변을 무엇으로 보이는가

1. **정적 동일성** — T2 가 상시 강제한다. 이것이 1차 증거다.
2. **산출물 sha256 대조** — `make effort`(결정적 · 시각·경로 미포함 실측)와
   `make eval` 산출을 교정 전후로 대조한다.
3. **`make tables` 는 sha 대조에서 제외한다** — `--latency` 가 `time.perf_counter()` 로
   지연을 측정해 **원리적으로 비결정적**이다(`results_table.py:183,215`). 대신
   **지연 표를 뺀 지표 열만** 대조한다. **이 제외를 숨기지 않는다** — 보고에 명시한다.
4. **원장 앞 25행 sha256 불변** 대조(S5).

### 8.7 원장의 버전관리 편입 (C-2)

`.gitignore` 에 예외 1줄을 추가한다 — `!data/processed/ir/seal_access.jsonl`.
**파일에 원문은 0열**이고(시각·커밋·호출자·경로·sha256·사유·층·분할) §1-5 가 막는 대상이
아니다. 최초 커밋으로 현 25행의 무결성이 이력에 고정된다.

### 8.8 결정성·비목표 재확인

- **새 수치 0 · 새 실험 0 · 봉인 개봉 0.** A층 원장 기록은 개봉이 아니라 **기록의 신설**이다.
- **`data/external/**` · 봉인 qrel 파일 · 동결 run 파일 · `paper/**` 무변경.**
- 신규 의존성 **0** — 표준 라이브러리와 기존 모듈만 쓴다.
- 실행 시각·경로 절대값을 산출물에 넣지 않는다(원장 제외 — 원장은 시각이 존재 이유다).

---

## 9. 4·5단계 구현과 검증 (2026-08-24)

**결론 먼저.** 배선을 15자리 전량 고쳤고, **A층 test qrel 에 대한 모든 접근이 이제 열람
원장에 남는다.** 수치는 하나도 바뀌지 않았다 — `make eval` 세 분할과 `make effort` 산출물이
교정 전후로 동일하다. **선행 결함 8건은 그대로 빨간색이며 이 작업과 무관함을 HEAD 기준선으로
확인했다**(§9.4).

### 9.1 변경한 자리 (18파일)

| 갈래 | 파일 |
|---|---|
| 통로 | `analysis/metrics.py`(경로·기록 규칙) · `validate/seal_audit.py`(`layer`·`split` 필드) |
| (B) 10자리 | `analysis/{results_table,ablation,subgroup,bootstrap,lang_recall,ontology_eval(2),pathsim_diag,overlap}.py` · `explore/ir_panel.py` |
| (C) 5자리 | `rag/{context,score,t4}.py` · `analysis/effort.py` · `scripts/rerank_ceiling.py` |
| 검사기 | `scripts/check_verdicts.py`(엄격 키 검사) |
| 테스트 | `tests/test_seal_wiring.py`(신설 11건) · `tests/conftest.py`(신설) · `tests/test_b_layer_readout.py`(R1·R2 개정 · §9.5) |
| 버전관리 | `.gitignore`(원장 예외 3줄) |

**`paper/**` · `data/external/**` · 봉인 qrel 파일 · 동결 run · `verdicts.yaml` 변경 0.**

### 9.2 수치 불변 (S2)

| 대조 | 결과 |
|---|---|
| `metrics --split {all,dev,test} --family` 출력 | **교정 전후 완전 동일**(세 분할 모두 diff 0) |
| `make effort` 산출 2종 sha256 | `52edfa7c…`(md) · `3c996453…`(csv) — **불변** |
| 집합 동일성 | `load_qrel_for_split("test")` == 전량 qrel 의 test 부분 (198질의·479엣지) — 회귀 테스트로 고정 |
| 분할 필터의 `astype(str)` | 실측상 무해 — `split.doc_id`·`qrel.query_id` 가 이미 전부 `str` |

**`make tables` 는 설계대로 sha 대조에서 제외했다** — `--latency` 가 원리적으로 비결정적이다.
대신 그 다섯 모듈이 쓰는 정답지가 통로 하나로 수렴했고, 그 통로의 반환값 동일성을 T2 가
고정한다. **이 제외를 숨기지 않는다.**

### 9.3 원장 (S1·S5)

- 앞 **25행 sha256 불변** (`384c1ca4…`) — 추가만 일어났다.
- 검증 실행이 남긴 A층 행 **14행**(`layer="A"` · `split` 은 `test` 13 · `all` 1). 이 행들은
  **지우지 않는다** — 추가전용 원장에서 기록을 되돌리는 것이 더 나쁜 선례다. 무엇의 기록인지는
  `reason` 이 지목한다(`analysis.effort` · `rag.context` · `rag.score` 등).
- **테스트 실행은 더 이상 원장을 건드리지 않는다** — `tests/conftest.py` 가 세션 동안 원장을
  임시 경로로 돌린다(실측: 도입 전 12행 증가 → 도입 후 **증가 0**). 기록 기제 자체는
  `test_seal_wiring.py` 가 자기 임시 원장으로 따로 검증한다.

### 9.4 검사기·테스트

| 명령 | 결과 |
|---|---|
| `make lint` | 통과 |
| `make verdicts` | 통과(6개 파일) |
| `make sig-check` | 서명 정합 ✓ |
| `make style-check` | 통과(2개 파일) |
| `make glossary-check` | 통과 · 경고 20건(기존 · 경고 모드) |
| `tests/test_seal_wiring.py` | **11/11 통과**(T1–T7) |
| `make test` 전량 | **729 통과 · 7 실패 · 3 오류** |

**실패·오류 10건의 귀속.** 그중 **둘은 이 작업이 개정한 계약**이고(§9.5 · 개정 후 통과),
나머지 **여덟은 선행 결함**이다 — `test_baseline_integration` 5건(`graph_v0.ttl` 이 스냅샷보다
낡음 · CQ 서명 불일치) · `test_explore_ir_panel` 3건(기대값 대장 미갱신). **HEAD 를 그대로
돌려 같은 8건이 같은 사유로 실패함을 확인했다** — 이 작업과 무관하며, OPEN-ITEMS 2순위
(회귀 신호 복구)의 대상이다.

### 9.5 개정한 계약 둘 — 숨기지 않고 적는다

`tests/test_b_layer_readout.py` 의 R1·R2 가 이 배선과 정면으로 충돌했다.

| | 구 계약 | 개정 | 왜 정당한가 |
|---|---|---|---|
| **R1** | *"A층 분할의 정답지는 examiner qrel 그대로 — 봉인 통로를 타지 않는다"* | *"A층 정답지는 **B층 봉인이 아니다**"* 로 바꾸고, `test`→A층 봉인 사본을 명시 | R1 이 지키려던 것은 **B층 개봉이 A층 배관을 오염시키지 않는 것**이고 그것은 그대로다. *"통로를 타지 않는다"* 는 O-6 이 결함으로 지목한 바로 그 상태였다 |
| **R2** | `results_table.load_qrel` 을 폭탄으로 치환 | 그 이름이 사라졌으므로 `metrics.load_qrel`·`load_qrel_for_split` 을 폭탄으로 | 검사 의도(판독 B 의 run 산출이 qrel 을 읽으면 깨진다)는 **더 넓어졌다** |

**두 개정은 검사를 약화시키지 않는다** — R1 은 조건을 하나 더 얹었고(A층 경로 ≠ B층 봉인),
R2 는 감시 범위를 통로 자체로 옮겼다.

### 9.6 남은 구멍 하나 — 명시 경로 탈출구

`analysis.metrics` CLI 의 `--qrel <경로>` 는 여전히 통로를 거치지 않는다(`main()` 의
`load_qrel(args.qrel)`). **이것은 저수준 판독기의 의도된 탈출구**이며(설계 §8.4 "바꾸지 않는
것"), 사람이 경로를 손으로 적어야만 열린다. **닫지 않은 채로 적어 둔다** — 닫으려면 CLI 계약을
바꾸는 별건이고, 이 계획의 범위 밖이다.

### 9.7 남은 작업 (사용자 승인 필요)

1. **커밋** — `src/` 18파일 + 원장 최초 커밋(`data/processed/ir/seal_access.jsonl` 39행).
2. **OPEN-ITEMS O-6 종결 표기** — 이 문서를 근거로.
