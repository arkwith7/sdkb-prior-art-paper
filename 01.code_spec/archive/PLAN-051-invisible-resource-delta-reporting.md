# PLAN-051 — D-43 해소 · "게이트로는 보이지 않는 델타"를 리포트가 스스로 말하게 한다

> ## ✅ 종료 (2026-08-15 · 구현·검증 완료 · 2026-08-17 아카이브)
>
> 실행 커밋 `04df94c`. 산출은 [`validate/runset.py`](../../src/sdkb_paper/validate/runset.py)
> `resource_visibility()` · [`validate/t_gate.py`](../../src/sdkb_paper/validate/t_gate.py) 기록·출력 ·
> 테스트 9건 추가(35 passed) · CLAUDE.md §2.1 **절차 2′** · D-43 **해소**.
>
> **아래 본문의 "🛑 승인 대기"는 낡았다 — 승인·구현·검증이 모두 끝났다.** 다음 세션이 이 표기를
> 근거로 재승인을 요구하지 않는다.
>
> **승계되는 규칙 하나.** `resource_visibility.note` 가 `invisible` 인 실행의 결과는
> **"게이트로는 보이지 않았다"** 로 적는다. `no_evidence` 는 *비가시라는 증거가 없다*이지
> *델타가 보였다*가 아니며, `unknown` 은 근거 없음이지 통과가 아니다. 이 필드는
> **승인식에 들어가지 않는다** — 판정은 그대로 두고 판정의 뜻만 지킨다.

> **단계: 1 요구정의 (§2) — 🛑 승인 대기.**
> 작성 2026-08-15 · 대상 결함 [D-43](../../upstream/DEFECT-LEDGER.md) · 주장 **C3**(진화안전) · **C4**(DP2)

---

## 1. 목적 — 어느 주장을 지지하는가

**C3.** T-gate 가 "승인했다"고 적은 산출물이 실제로는 **그 델타를 본 적이 없는** 경우가 있고,
지금 리포트는 그 둘을 구분하지 않는다. 구분되지 않는 승인은 승인의 증거가 아니다.

부수적으로 **C4 · DP2**("한 층 아래 승인")를 지킨다 — 다음 층이 델타를 읽지 못했는데 승인이
나면 DP2 는 문장으로만 남고 장치로는 작동하지 않는다.

## 2. 무엇이 문제인가 — 실측

PLAN-050 실행에서 관측된 상태가 **지금 이 트리에 그대로 살아 있다**:

| | 값 |
|---|---|
| 스냅샷 서명 | `665c27d1c774` (상류 `0a7ff153` · 22파일) |
| 파이프라인 서명 | `9745a7d932c9` |
| 같은 파이프라인 서명을 가진 동결 runset | `B_layer_readout` — **스냅샷 서명은 `9b7f79ef06a6`** |

스냅샷은 움직였고 파이프라인 구성요소 셋(`ir_corpus 83eef760…`·`concept_axis 197adc10…`·
`graph_v1 41094e9f…`)은 **전부 불변**이다. 즉 ΔR₁₀₀ 은 측정된 0 이 아니라 **구성상 0** 이다.

**같은 상태가 과거에도 있었다**(D-19): `O_pre_linker`(snap `b98ad787d1fe`)와
`O_d578bf3_linkercode`(snap `6cfb743d3d88`)가 파이프라인 서명 `156c0ccd36f5` 를 공유한다.
즉 이 조건은 한 번 있었던 사고가 아니라 **재발하는 상태**다.

**공백은 `system` 모드에만 있다.** `resource` 모드에는 이미 **E6(파이프라인 서명 상이)** 가 있고
실패 시 `unreached` 로 미검정 처리하며 종료코드 2 를 낸다([runset.py:310](../../src/sdkb_paper/validate/runset.py#L310)) —
**여기는 고칠 것이 없다.** 그러나 `make gate` 의 기본 경로는 `system` 모드이고, 그 경로는
자원 델타를 **묻지도 않는다**([t_gate.py:70-72](../../src/sdkb_paper/validate/t_gate.py#L70-L72)).
그래서 `Accept = 1` 이 나오고, 리포트에는 그것이 어떤 자원 상태에서 나온 승인인지 적히지 않는다.

## 3. 입력 · 출력 · 비목표

**입력** — 새로 수집하는 데이터는 **없다.** 이미 있는 것만 읽는다:
`data/external/sdkb/PROVENANCE.json`(스냅샷 서명) · `config.IR_CORPUS`·`IR_CONCEPT_AXIS`·
`GRAPH_V1`(파이프라인 서명) · `data/runsets/*.json`(동결 매니페스트 6개).

**출력** — 둘.

1. **`tgate_report.json` 의 신규 필드** (모드 무관하게 항상 기록)
   - `resource_visibility.pipeline_sig` · `.snapshot_sig`
   - `resource_visibility.pipeline_sig_changed` — 같은 파이프라인 서명 · **다른 스냅샷 서명**의
     동결 매니페스트가 있으면 `false`, 없으면 `null`(비교 근거 없음), 있고 서명이 갈리면 `true`
   - `resource_visibility.basis` — 판단 근거가 된 매니페스트 라벨(있을 때)
   - `resource_visibility.note` — `"invisible"` / `"unknown"` / `"visible"`
2. **`format_report()` 의 경고 한 줄** — `invisible` 일 때 `Accept` 줄 **위**에
   *"이 실행의 자원 델타는 이 게이트로는 보이지 않는다"* 를 찍는다.
3. **[CLAUDE.md](../../CLAUDE.md) §2.1 한 줄** — 파이프라인 서명이 불변인 실행의 산출물은
   *"통과했다"* 가 아니라 **"이 게이트로는 비가시"** 로 적는다.

**비목표 — 여기서 하지 않는 것을 명시한다.**

- ❌ **승인식을 바꾸지 않는다.** `accept()` 는 한 글자도 손대지 않는다. `Accept` 값·종료코드·
  T1·T2·T3 판정 로직은 전량 불변이다. **이 변경으로 어떤 수치도 재산출되지 않는다.**
- ❌ 기존 `tgate_report*.json` 3개를 재생성하지 않는다(§1-3 — 과거 판정은 소급 수정하지 않는다).
- ❌ `resource` 모드의 E1–E7 을 건드리지 않는다.
- ❌ 원고를 고치지 않는다. 원고 반영이 필요하면 **별건**이다(§2.2 대상 여부부터 판단).

## 4. 성공기준 — 검정 가능한 형태로

| | 기준 | 확인 방법 |
|---|---|---|
| **S1** | 현 트리에서 `--mode system` 실행 시 리포트가 `note="invisible"` · `basis="B_layer_readout"` 를 낸다 | 단위 테스트(매니페스트 주입) + 실제 1회 실행 |
| **S2** | `O_pre_linker` ↔ `O_d578bf3_linkercode` 쌍이 `invisible` 로 분류된다 | 단위 테스트 — **과거 D-19 상태를 이 검사가 잡는가** |
| **S3** | 파이프라인 서명이 어느 매니페스트와도 안 맞으면 `note="unknown"` · `pipeline_sig_changed=null` | 단위 테스트 — **모르는 것을 안다고 적지 않는다** |
| **S4** | 승인식 불변 — 같은 입력에 `accept`·종료코드·`t1`/`t2`/`t3` 가 변경 전과 **바이트 단위로 동일** | 변경 전 리포트를 사본으로 떠 두고 신규 필드 제외 후 대조 |
| **S5** | `make lint && make test` 통과 · `make verdicts` · `make submission-check` 녹색 유지 | 실행 |

**S4 가 이 계획의 안전장치다.** 실패하면 이것은 리포팅 변경이 아니라 방법 변경이고, §2.1 의
안전장치("코드가 바뀌면 §2 전체")를 넘어 **새 사전등록**이 필요해진다.

## 5. 위험과 경계

- **거짓 안심의 위험.** `pipeline_sig_changed=true` 는 *"델타가 보였다"* 를 뜻할 뿐
  *"델타가 옳게 반영됐다"* 를 뜻하지 않는다. 필드 이름과 note 문구에 그 한계를 담는다.
- **`unknown` 을 `visible` 로 접지 않는다.** 동결 매니페스트가 없으면 판단 근거가 없는 것이고,
  근거 없음은 통과가 아니다(§8 — 불확실은 불확실로).
- **이 조항은 §2.1 을 넓히지 않는다.** D-43 이 이미 적었듯 트리거를 좁히면 자격 있는 델타를
  놓치므로, 넓게 두는 현 설계가 옳다. 바뀌는 것은 **결과를 적는 방식**뿐이다.

## 6. 다음 단계

2 분석 🛑 → 3 설계 🛑 → 4 구현 → 5 검증 🛑. 코퍼스·qrel·통계 결과를 바꾸지 않으므로 §2 의
규모 예외 대상이 아니다 — 다만 **게이트 로직 파일을 만지므로 예외가 없다**(§2 말미).

---

# 2단계 · 분석 (2026-08-15 · 🛑 통과)

## 7. 관찰 사실

1. **매니페스트 6개의 스키마는 균일하다.** 전부 `snapshot.sig`·`pipeline.sig`·`pipeline.parts`
   (구성요소 3개) 보유 · `parts` 에 `None` 없음 · 결측 키 없음. 정리 작업은 필요 없다.
2. **`tgate_report.json` 의 소비자는 0건이다.** [config.py:253](../../src/sdkb_paper/config.py#L253)
   의 정의를 빼면 읽는 코드가 없다. 신규 필드는 아무것도 깨지 않는다 — 동시에 이것이 D-43 이
   조용했던 이유다.
3. **현 `tgate_report.json` 이 문제 사례 그 자체다** — `mode=system` · `accept=true` · 서명 기록
   전무. 구 리포트 둘(`_test`·`_test_p0star`)은 `mode` 키조차 없는 D-19 이전 산출물이며
   **재생성하지 않는다**(§1-3).
4. **배선은 이미 절반 있다.** `arm_label()` 이
   [results_table.py:232](../../src/sdkb_paper/analysis/results_table.py#L232) ·
   [ir_panel.py:219](../../src/sdkb_paper/explore/ir_panel.py#L219) 에서 쓰이고, 표는
   *"미등록(동결 runset 과 불일치)"* 까지 찍는다. **표는 자기 팔을 말하는데 게이트만 말하지 않는다.**
5. **테스트 자리가 있다.** [test_resource_gate.py:76](../../tests/test_resource_gate.py#L76)
   `test_snapshot_changed_but_pipeline_unchanged_is_unreached`(resource 모드) 와 `_mf` 픽스처
   헬퍼를 재사용한다 — **새 픽스처 체계를 만들지 않는다.**
6. **`make tgate` 의 기본 분할은 `dev` 다**([Makefile:310](../../Makefile#L310)). 현 리포트는
   `split=test` 이므로 S4 대조 실행은 `make tgate SPLIT=test` 여야 한다.

## 8. 확정된 결정 둘

**A · `note` 의 세 값은 `invisible` · `no_evidence` · `unknown` 이다.** 요구정의의 `visible` 은
쓰지 않는다 — 실제로 확인 가능한 것은 *"비가시라는 증거가 없다"* 이지 *"델타가 보였다"* 가
아니기 때문이다(§8 · 요구정의 §5 경계).

**B · 필드명은 `resource_visibility.note` 다(B2 채택 · 2026-08-15).** D-43 이 적은
`pipeline_sig_changed` 는 O/O′ 두 팔이 있는 `resource` 모드의 어휘이고, `system` 모드에는
비교할 짝이 없다. 재는 것과 이름이 어긋나면 다음 세션이 오독한다. **대장 D-43 의 수정 제안
문구는 구현 기록으로 정정한다** — 판정이 아니므로 §1-3 대상이 아니다.

---

# 3단계 · 설계 (2026-08-15 · 🛑 승인 대기)

## 9. 모듈·시그니처

### 9.1 `validate/runset.py` — 신규 판정 함수 하나

```python
VIS_INVISIBLE   = "invisible"      # 스냅샷이 움직였는데 파이프라인이 읽지 않았다
VIS_NO_EVIDENCE = "no_evidence"    # 비가시라는 증거가 없다 (≠ 델타가 보였다)
VIS_UNKNOWN     = "unknown"        # 판단 근거가 없다

def resource_visibility(pipeline: dict | None = None,
                        snapshot: dict | None = None) -> dict:
```

**반환** — `{"note", "pipeline_sig", "pipeline_short", "snapshot_sig", "snapshot_short",
"matched", "basis", "detail", "error"}`. `matched` 는 파이프라인 서명이 같은 매니페스트 라벨
(정렬), `basis` 는 그중 **스냅샷 서명이 다른** 것(정렬).

**판정 순서** — 위에서 아래로, 먼저 걸리는 것이 이긴다.

| # | 조건 | `note` |
|---|---|---|
| 1 | 파이프라인 구성요소에 `None` 이 하나라도 있다 | `unknown` |
| 2 | 스냅샷 서명을 구할 수 없다(`PROVENANCE.json` 부재 등) | `unknown` + `error` |
| 3 | `basis` 가 비어 있지 않다 | **`invisible`** |
| 4 | `matched` 는 있고 `basis` 는 비었다 | `no_evidence` |
| 5 | `matched` 가 비었다 | `unknown` |

3 이 4 보다 앞서는 이유는 `classify_delta` 가 A-Box 오염을 우선하는 것과 같다 — **자격 없음·
비가시는 흡수되지 않는다.**

**이 함수는 예외를 올리지 않는다. 그러나 삼키지도 않는다.** 리포팅 경로가 게이트를 죽이면
안 되므로 `FileNotFoundError`·`OSError`·`json.JSONDecodeError` 를 잡되, **사유를 `error` 에
문자열로 남기고 `format_report` 가 그것을 찍는다.** D-42 의 교훈(*"검사기가 눈을 감는 방식은 늘
예외를 삼키는 것이었다"*)을 지키는 방식은 예외를 올리는 것이 아니라 **조용하지 않게 만드는 것**이다.

**결정성** — `sorted(glob)` · 정렬된 라벨 · 시각·절대경로·난수 없음. 같은 트리에서 두 번 호출하면
바이트 단위로 같다(테스트 V8).

### 9.2 `validate/t_gate.py` — 기록 지점 하나, 출력 지점 둘

- `run_tgate()`: `out` 초기화 **직후** `out["resource_visibility"] = RS.resource_visibility()`.
  **적격심사보다 앞에 둔다** — 미검정으로 조기 반환하는 경로(`untested=True`)에서도 *"어느 자원
  상태에서 돌았는가"* 는 남아야 하기 때문이다. 지역 임포트(`from . import runset as RS`)로
  `system` 모드의 기존 임포트 비용 구조를 바꾸지 않는다.
- `format_report()`: `_visibility_lines(res) -> list[str]` 를 만들어 **두 개의 `Accept` 줄 위**에
  각각 삽입한다(조기 반환 경로 L143 · 정상 경로 L152). `invisible` 일 때만 경고 형식으로 찍고,
  `unknown` 은 사유와 함께 한 줄, `no_evidence` 는 한 줄로 조용히 적는다.

**손대지 않는 것** — `accept()` · 종료코드 분기 · `t1`/`t2`/`t3` 호출과 인자 · E1–E7 · CLI 인자.
**신규 의존성 0.**

## 10. 검정·판정 방법

**통계 검정이 없다.** 이 산출물은 서명 대조이며 `t3_cross_task_cq` 와 같은 **결정론적 비교**다.
표본단위·효과크기·유의수준이 등장할 자리가 없고, 등장하면 그것은 설계 오류다.

## 11. 테스트 설계

`tests/test_resource_gate.py` 에 절 하나를 추가한다(`_mf` 재사용 · 새 픽스처 체계 없음).

| | 테스트 | 고정하는 것 | 성공기준 |
|---|---|---|---|
| V1 | 현 트리 형상 — 매니페스트 `B_layer_readout`(snap `9b7f79ef…` · pipe `9745a7d9…`) · 현 상태 snap `665c27d1…` · pipe `9745a7d9…` | **오늘의 실측 상태** | `invisible` · `basis=["B_layer_readout"]` → **S1** |
| V2 | 과거 D-19 쌍 — `O_pre_linker`(snap `b98ad787…`) ↔ `O_d578bf3_linkercode`(snap `6cfb743d…`) · 공유 pipe `156c0ccd…` | **이 검사가 과거 사고를 잡는가** | `invisible` → **S2** |
| V3 | 매치되는 매니페스트 없음 / 매니페스트 디렉터리 자체가 없음 | 모르는 것을 안다고 적지 않는다 | `unknown` → **S3** |
| V4 | 매치 있음 · 전부 같은 스냅샷 서명 | `no_evidence` 가 `invisible` 로 번지지 않는다 | `no_evidence` |
| V5 | 파이프라인 구성요소에 `None` 포함 | 규칙 1 | `unknown` |
| V6 | `PROVENANCE.json` 부재 | 예외를 올리지 않고 **조용하지도 않다** | 반환됨 · `note=unknown` · `error` 비어 있지 않음 |
| V7 | `run_tgate(mode="system")` — `t1`/`t2`/`t3`/누출 monkeypatch | **승인식 불변** | `accept` 가 패치 값 그대로 · `resource_visibility` 존재 |
| V8 | 두 번 호출 | 결정성 | 두 반환이 동일 |

## 12. S4(승인식 불변) 확인 절차 — 5단계에서 실행

1. 변경 **전에** `data/processed/tgate_report.json` 을 스크래치패드로 사본.
2. 구현 후 `make tgate SPLIT=test` **1회** 실행(현 리포트와 같은 인자 · 누출 감사 포함).
3. 두 JSON 에서 `resource_visibility` 키만 제거하고 대조 → **완전 일치여야 한다.**
4. 불일치가 나오면 **덮지 않고 보고한다.** 그것은 이 변경이 리포팅이 아니라 방법 변경이라는
   뜻이거나(→ 새 사전등록 필요), 파이프라인에 비결정성이 있다는 뜻이다(→ 별건 결함 등재).

---

# 4·5단계 · 구현과 검증 (2026-08-15 · 실측)

## 14. 성공기준 판정 — 5/5 충족

| | 기준 | 결과 |
|---|---|---|
| **S1** | 현 트리 실행이 `invisible` · `basis=B_layer_readout` | ✅ `make tgate SPLIT=test` 실측 — `⚠ 자원 델타 가시성 = invisible (pipeline=9745a7d932c9 · snapshot=665c27d1c774)` |
| **S2** | 과거 D-19 쌍이 `invisible` 로 잡힌다 | ✅ `test_visibility_catches_the_historical_d19_pair` |
| **S3** | 대조 근거 없으면 `unknown` | ✅ V3a·V3b·V5·V6 |
| **S4** | **승인식 불변** — 신규 키 제외 시 변경 전후 완전 일치 | ✅ 신규 키 `['resource_visibility']` 하나 · 나머지 **완전 일치** · `accept` 1 → 1 |
| **S5** | `make lint`·`make test`·`make verdicts`·`make submission-check` | ✅ ruff 통과 · **594 passed** · 판정 문구 정합 통과 · 투고 준비 검사 통과 |

**S4 가 부수적으로 증명한 것 하나** — 같은 인자의 재실행이 `t1`·`t2`·`t3`·누출 감사까지
바이트 단위로 재현됐다. 파이프라인 비결정성은 **없다**(설계 §12-4 의 두 번째 분기는 발생하지 않음).

## 15. 실측 판정값 (참고 · 재산출 아님)

`make tgate SPLIT=test` 는 변경 전과 **같은 값**을 냈다 — T1 `Δ +0.0240 · 95%CI [−0.0134, +0.0612]`
LB₉₅ > −ε → PASS · T2 max drop `+0.0193` < δ → PASS · T3 em·tf·core `1.000` 유지 → PASS ·
누출 감사 잔여 0 → `Accept = 1`.

**이 값들은 이 작업으로 재산출된 것이 아니다** — 변경 전 리포트와 동일함이 S4 로 확인됐고,
여기 옮겨 적는 이유는 *"승인이 났지만 그 승인은 자원 델타를 본 적이 없다"* 는 D-43 의 문장이
같은 실행 안에서 함께 읽혀야 하기 때문이다.

## 16. 산출물

- [`src/sdkb_paper/validate/runset.py`](../../src/sdkb_paper/validate/runset.py) — `VIS_*` 상수 3 ·
  `_iter_manifests()` · `resource_visibility()`
- [`src/sdkb_paper/validate/t_gate.py`](../../src/sdkb_paper/validate/t_gate.py) — 기록 1행 ·
  `_visibility_lines()` · 출력 2지점 · 모듈 docstring
- [`tests/test_resource_gate.py`](../../tests/test_resource_gate.py) — 가시성 절 9건 추가(35 passed)
- [`CLAUDE.md`](../../CLAUDE.md) §2.1 절차 **2′**
- [`upstream/DEFECT-LEDGER.md`](../../upstream/DEFECT-LEDGER.md) D-43 → **해소** + 필드명 정정 기록

## 13. 이 설계가 하지 않는 것 (재확인)

수치 재산출 0 · 판정 변경 0 · 원고 수정 0 · qrel/코퍼스/run 접근 0(읽기 전용 sha256) ·
신규 의존성 0 · CLI 계약 변경 0.
