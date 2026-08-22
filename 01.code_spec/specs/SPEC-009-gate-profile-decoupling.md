# SPEC-009 · 게이트의 자원 비의존화 (프로파일 분리 · PLAN-064 A-1)

| | |
|---|---|
| 지지하는 것 | **C3 진화안전**(게이트가 자원에 의존하지 않음의 코드 증거) · **C4 설계지식**(DP3 이전 가능성의 선행조건) |
| 상위 계획 | [PLAN-064 §3](../plans/PLAN-064-second-domain-portability-and-aei-reframe.md) C1–C9 (+ 본 문서가 신설하는 C10·C11) |
| 동결 문서 | [PLAN-064-prereg](../plans/PLAN-064-prereg.md) — **이 문서는 사전등록을 해석하지 않고 전사한다** |
| 대상 | `src/sdkb_paper/config.py` · `validate/{cq_runner,t3_cross_task_cq,fault_inject,shacl_gate,t_gate,quarantine}.py` · `analysis/faults.py` · `Makefile` · `tests/` · `paper/verdicts.yaml` |
| 단계 | §2 정지 게이트 — **1 요구정의 ✔승인(2026-08-22) · 2 분석 ✔ · 3 설계 = 이 문서 · 4 구현 · 5 검증** |

> **이 문서는 SDKB 실험의 판정·수치를 하나도 바꾸지 않는다.** A-1 의 성공 조건 자체가
> *"SDKB 프로파일에서 출력이 바이트 동일"* 이므로, 이 작업이 기존 수치를 움직이면 그것은
> 성공이 아니라 실패다. EP5 실행(A-4)·원고 반영(A-5)은 이 문서의 범위가 아니다.

---

## 0. 결론 먼저

게이트 코드에 박힌 SDKB 전제는 **상수 몇 개가 아니라 네 층**이다 — ① 어휘(네임스페이스) ②
스위트 이름과 층 귀속 ③ 결함의 조작 술어와 결정성 규칙 ④ 승인식의 형태(T1·T2 가 있다는 전제).
①–③ 은 값의 외부화로 풀리지만 ④ 는 **판정 구조의 문제**라 값으로 풀리지 않는다. 그래서 설계의
중심은 프로파일 파일이 아니라 **`accept` 를 `null` 로 둘 수 있게 만드는 것**이다(§3.7).

가장 위험한 자리는 C2 다. `suite_predicates()` 의 교집합 검사는 Brick 에서 **실패하지 않고
공허하게 통과한다** — 술어를 하나도 세지 못하기 때문이다(§2 ③). 검사기가 눈이 먼 채 초록불을
내는 것은 검사가 없는 것보다 나쁘다.

---

## 1. 요구정의 (2026-08-22 승인)

**목적.** C3·C4 — 게이트가 자원 비의존적이라는 주장의 코드 증거를 만든다. EP5 판정의 선행조건이다.

**입력.** `profiles/sdkb.yaml`(현 상수의 전사) · `profiles/brick.yaml`(사전등록 §2–§5 의 전사) ·
`queries/brick/**` · `data/external/brick/PROVENANCE.json` · `data/external/brick/ep5_cq_calibration.json`.

**출력.** 프로파일 로더 · 프로파일화된 L1/L3/T3/결함주입/T-gate · `make gate-profile PROFILE=brick` ·
EP5 판정 JSON 스키마(`accept: null` + `Accept_partial`).

**성공기준.**

| | 기준 | 검증 방법 |
|---|---|---|
| S1 | SDKB 프로파일 출력이 **바이트 동일** | `make gate-graph` diff 0 · `cq_g0.json` 재생성 동일 · 기존 seed 결함본 sha256 동일 |
| S2 | Brick CQ 15개가 파싱·실행되고 개발 행 수가 `ep5_cq_calibration.json` 과 일치 | 신규 테스트(개발 A-Box 만 사용) |
| S3 | `suite_predicates()` 가 **단일 파서로** 사전등록 §4.1 표를 재현하고, `fdd ∩ space = ∅` 가 **공허한 통과가 아님**이 강제된다 | 각 스위트 술어 수 > 0 을 함께 단언 |
| S4 | 프로파일 값이 사전등록과 어긋나면 **로드 시점에 실패** | sha256 대조 (§3.1.3) |
| S5 | 620 + 신규 테스트 전량 통과 · CI 녹색 | `make lint && make test` |

**비목표.** EP5 실행(A-4) · 원고 반영(A-5) · 승인식 개정(T4 편입) · SDKB 수치 재산출 ·
홀드아웃 A-Box(`ex-soda_brick.ttl`) 열람.

---

## 2. 분석 — 실측 (2026-08-22)

**① 프로파일화 대상의 실제 사용 범위.** `CQ_SUITES`·`T3_SUITES`·`L3_SUITES`·`CQ_TARGETS`·
`CQ_GATE_TARGET`·`QUERIES_CQ`·`SHAPES_GRAPH`·`SHAPES_DELTA`·`CQ_TAU` 계열이 **src 8개 파일 ·
tests 6개 파일**에서 참조된다. PLAN-064 C-표가 든 다섯 파일보다 넓으며, `validate/vocab_coverage.py`
와 `analysis/faults.py` 가 목록 밖이다.

**② `_parse_meta` 가 Brick CQ 15개 전량을 거부한다** (실행 확인).
`ValueError: CQ 스위트 라벨이 없거나 잘못됐다: 'fdd' (허용 ('pa','em','tf','core'))`.
추가로 사전등록 §3.1 이 규율로 못박은 `# shared: true`(core 5건)는 **파서에 항목이 없어**
읽히지 않는다.

**③ `suite_predicates()` 의 거짓 통과 — 이 작업에서 가장 중요한 자리.**
`cq_runner.py:151` 의 정규식은 `ont:` 와 `skos:` 만 센다. Brick CQ 는 전량 `brick:` 접두어이므로
**모든 스위트가 빈 집합**이 되고, `fdd ∩ space = ∅` 는 참이 되지만 아무것도 검증하지 않는다.
사전등록 §4.1 의 술어 표는 이 함수가 아니라 `scripts/ep5_cq_calibrate.py:28` 의 **별도 정규식**에서
나왔다 — 판정 코드와 사전등록 근거가 서로 다른 파서를 쓰고 있다.

**④ 사전등록과 코드 상수의 충돌 둘.** 사전등록이 동결이므로 코드가 따른다.

| | 코드 | 사전등록 §4.2 |
|---|---|---|
| 강도 격자 | `STRENGTHS = (0.01, 0.05, 0.10)` | **5 % · 10 % · 20 %** |
| seed 규칙 | `sha256(key\|rate\|rep)` | **`20260822 + 100·결함번호 + 반복번호`** |

**⑤ T-gate 에 T1·T2 부재 모드가 없다.** `accept()` 는 네 조건의 곱이고 `--mode` 는
`system|resource` 둘뿐이다. `resource_visibility` 는 SDKB 파이프라인 서명을 읽으므로 Brick 에서
의미가 없다.

**⑥ 세대 아티팩트가 프로파일 간에 충돌한다.** `generation_path()` 는
`data/cq_generations/cq_<label>.json` 평면 경로이고, `render_generations()` 는 표 헤더에
`pa/em/tf/core` 를 하드코딩한다.

**⑦ 실행 경로 둘이 C-표 밖에 있다.** EP5 결함주입을 실제로 도는 것은 `analysis/faults.py`
`run_instance` 이며 `config.GRAPH_V0`·`load_generation("g0")`·누출 감사·T1/T2 재랭크가 박혀 있다.
`quarantine.protected_paths()` 의 봉인 목록은 SDKB 정본 전용이다. → **C10·C11 로 신설**(승인됨).

**부수.** 테스트는 계획서의 619 가 아니라 **620건 수집**이다.

---

## 3. 설계

### 3.1 프로파일 객체와 로더 (신규 `src/sdkb_paper/profile.py`)

#### 3.1.1 왜 전역 스위치가 아니라 명시 인자인가

환경변수 하나로 `config` 의 모듈 상수를 갈아 끼우면 호출부는 안 고쳐도 되지만, **한 프로세스
안에서 SDKB 경로와 Brick 경로가 섞일 때 조용히 틀린다** — `analysis/faults.py` 가
`config.GRAPH_V0` 를 읽는 동안 스위트만 Brick 인 상태가 만들어진다. 그래서 프로파일은
**함수 인자로 흐르고**, 기본값은 호출 시점에 `active()` 로 푼다(import 시점이 아니다).

#### 3.1.2 스키마

```python
@dataclass(frozen=True)
class Profile:
    name: str                        # "sdkb" | "brick"
    namespaces: dict[str, str]       # 술어 추출·어휘 측정이 보는 접두어 (sdkb: ont·skos / brick: brick)
    cq_dir: Path
    shapes_graph: Path               # 디렉터리 또는 단일 TTL (Brick 은 배포 TTL 내장 SHACL)
    shapes_delta: Path
    cq_suites: tuple[str, ...]
    l3_suites: tuple[str, ...]
    t3_suites: tuple[str, ...]
    cq_targets: tuple[str, ...]
    cq_gate_target: str
    cq_extra_headers: tuple[str, ...]  # brick: ("shared",)
    cq_tau: float
    cq_tau_grid: tuple[float, ...]
    generation_dir: Path             # 세대 아티팩트 (프로파일별로 가른다 · §2 ⑥)
    graph_default: Path | None       # sdkb: graph_v0 / brick: 없음(D0…D5 를 인자로 받는다)
    faults: dict[str, FaultProfile]  # 결함 키 → 조작 술어·강도·seed 번호
    seed_rule: str                   # "sha256" | "linear"
    seed_base: int | None            # linear 전용
    protected_paths: tuple[str, ...] # quarantine 봉인 대상 (config 속성명)
    has_t1_t2: bool                  # False 면 t_gate 는 accept=null 경로로 간다
    prereg: PreregPins | None        # §3.1.3
```

`load(name)` 는 `profiles/<name>.yaml` 을 읽고, `active()` 는 `SDKB_PROFILE`(기본 `"sdkb"`)를 푼다.

#### 3.1.3 이중 정본을 만들지 않는 두 장치

프로파일 파일이 생기면 **같은 값이 두 곳에 존재**하게 되고, 그것이 표류의 씨앗이다. 둘로 막는다.

1. **전사 검증 테스트.** `profiles/sdkb.yaml` 의 각 값이 현행 `config` 리터럴과 **동일함을**
   테스트가 단언한다. yaml 오타는 게이트 결과가 아니라 테스트에서 죽는다.
2. **사전등록 핀.** `profiles/brick.yaml` 의 `prereg` 블록은 CQ 15개 전문 sha256 ·
   `delta.ttl` sha256 · T-Box 6판 sha256 을 담고, 로더가 **디스크 실물과 대조**한다.
   불일치는 경고가 아니라 `PreregMismatch` 예외다 — 동결된 자원이 아닌 것 위에서 판정이
   돌기 시작하면 사전등록은 그 순간 무효다. sha256 의 원천은 손으로 옮겨 적지 않고
   `PROVENANCE.json` 과 CQ 파일에서 **생성 스크립트가 뽑는다**(§1-1·§1-7).

### 3.2 C1 · `config.py`

- 프로파일 대상 상수는 **삭제하지 않는다.** `config.CQ_SUITES` 등은 `profile.load("sdkb")` 에서
  파생된 값으로 남는다 — 620개 테스트와 호출부가 그대로 도는 것이 S1·S5 의 조건이다.
- `SDKB_PROFILE` 은 `config` 를 바꾸지 않는다. 프로파일 전환은 **CLI 의 `--profile` 인자**로만
  일어나고, 그 값이 게이트 함수로 흐른다.
- Brick 자원 경로 상수를 추가한다: `EXTERNAL_BRICK`·`BRICK_PROVENANCE`·`BRICK_CALIBRATION`.

### 3.3 C2·C6′ · `cq_runner.py`

| 변경 | 내용 |
|---|---|
| `_parse_meta(text, profile=None)` | 스위트·극성·대상 검증을 프로파일 값으로. `cq_extra_headers` 에 선언된 헤더(`# shared:`)를 **읽어서 반환한다** — 선언만 하고 버리지 않는다 |
| `suite_predicates(cq_dir=None, profile=None)` | 정규식을 **프로파일 네임스페이스 접두어에서 생성**한다. 반환 형태 불변 |
| `assert_disjoint(a, b, profile)` **신설** | 두 스위트의 교집합이 공집합이고 **각 집합이 비어 있지 않음**을 함께 단언. §2 ③ 의 거짓 통과를 구조로 막는다 |
| `result_digest` (C6′) | `run_cqs(..., with_digest=False)` 로 **기본 꺼짐**. 켜면 정렬된 binding 의 sha256 을 `CQResult` 에 붙인다. `judge()` 에는 연결하지 않는다 — 사전등록 §6.4 가 탐색적으로 못박았다 |

**`scripts/ep5_cq_calibrate.py` 의 지역 정규식은 제거하고 `suite_predicates()` 를 호출한다.**
같은 값을 두 파서가 내는 상태를 남기지 않는다. 교체 후 `ep5_cq_calibration.json` 이 **바이트
동일**하게 재생성되는지가 이 변경의 검증이다(사전등록 §4.1 표의 근거가 바뀌지 않았음의 증거).

### 3.4 C3 · `t3_cross_task_cq.py`

- `compare_rates`·`t3_gate`·`freeze_generation` 이 `profile` 을 받는다. 기본은 `active()`.
- `generation_path(label, profile)` → `profile.generation_dir / f"cq_{label}.json"`.
  SDKB 는 `data/cq_generations/` 그대로, Brick 은 `data/cq_generations/brick/`.
- `render_generations()` 의 열 이름을 `profile.cq_suites` 에서 생성한다. **원고 표 6.6 의 출력은
  SDKB 프로파일에서 문자 단위로 불변**이어야 한다(S1).

### 3.5 C4 · `fault_inject.py` — 사전등록 §4.2 의 전사

`ont()`/`skos()` 는 프로파일 네임스페이스를 받는 `ns(prefix, name)` 로 일반화한다.
`CROSS_FAULT_PREDICATES` 는 프로파일의 `faults` 블록에서 주입한다.

| 결함 | 기존 함수와의 관계 | 조작 | 강도 |
|---|---|---|---|
| **X2** 공간 포함관계 역전 | `f12_hierarchy_inversion` 의 **술어 매개변수화** | `brick:hasPart` 방향 역전 · 후보를 Building–Floor · Floor–Room 타입쌍으로 한정 | rate (0.05·0.10·0.20) |
| **X4** 위치 재배선 | `_rewire` 의 **주어 판 신설** | `brick:isLocationOf` 의 **주어**를 같은 타입 서명의 다른 Location 으로 치환 | rate (0.05·0.10·0.20) |
| **X3** 공유 관계 동치 오선언 | **신규** | `owl:equivalentProperty` 삽입 · 단계 1 `feeds≡hasPart` · 2 `+isFedBy≡isPartOf` · 3 `+hasPoint≡hasPart` | tier (1·2·3) |

**두 가지를 사전등록 그대로 옮긴다.**

- **강도의 의미가 결함마다 다르다.** X2·X4 는 비율, X3 은 누적 단계다. 프로파일은 결함마다
  `kind: rate|tier` 를 선언하고, `_n(rate, N) = max(1, round(rate·N))` 하한 규칙은 그대로 둔다.
- **seed 는 강도를 타지 않는다.** 사전등록 식 `20260822 + 100·결함번호 + 반복번호` 에는 강도가
  없으므로, **같은 (결함·반복)의 세 강도는 같은 seed 를 공유한다.** 이는 결정성을 해치지 않으며
  (같은 입력 → 같은 출력) 판정에도 관여하지 않는다. **식을 "고쳐서" 강도를 넣지 않는다** — 동결
  이후의 개선은 개선이 아니라 사후 조정이다(§1-3). 이 사실은 결과 표에 그대로 적는다.
  반복 번호는 X2·X4 가 `{1,2,3}`, X3 이 `{1}` 이다(사전등록 §4.2 의 반복 수를 1-기점으로 전개).

SDKB 프로파일의 `seed_rule: sha256` 과 `STRENGTHS = (0.01,0.05,0.10)` 은 **한 글자도 바뀌지
않는다** — 기존 결함본 재생성 sha256 동일이 S1 이다.

### 3.6 C5 · `shacl_gate.py`

`resolve_shapes(spec, profile)` 가 프로파일의 shapes 경로를 푼다. `load_shapes()` 는 **디렉터리와
단일 TTL 을 모두 받는다** — Brick 의 graph shape 은 배포 TTL 에 내장돼 있어 디렉터리가 아니다.
빈 shapes 를 조용히 통과시키지 않는 현행 규율(`SystemExit`)은 유지한다.

### 3.7 C6 · `t_gate.py` — `accept` 를 `null` 로 둘 수 있게 만든다

```python
def accept(l0_l3, t1, t2, t3) -> bool          # 불변 — SDKB 승인식은 손대지 않는다
def accept_partial(l0_l3, t3) -> bool          # 신설 — 이름이 부분임을 말한다
```

- `--mode t3only` 신설. 이 모드에서 JSON 은 **`"accept": null`** 과
  **`"Accept_partial": 0|1`** 을 **서로 다른 키로** 갖는다. 사전등록 §6.2 의
  *"부분 승인식을 승인식이라 부르지 않는다"* 를 스키마가 집행한다.
- 종료코드: `0` 부분 통과 · `1` 부분 불통과. **`2`(미검정)는 쓰지 않는다** — T1·T2 는
  "재보지 못한 것"이 아니라 **설계상 부재**이며, 두 상태를 같은 코드로 적으면 결과가 흐려진다.
- `resource_visibility` 는 `has_t1_t2=False` 프로파일에서 **`null` 로 기록**한다(SDKB 파이프라인
  서명을 읽는 필드이므로 Brick 에서 값을 만들면 그것이 허구다).
- **운용 비용 계측**(사전등록 §7 · 탐색적): 층별 wall-clock 과 `ru_maxrss` 를
  `"cost": {"L0":…, "L1":…, "L2":…, "L3":…, "T3":…}` 로 기록한다. 판정에 관여하지 않는다.
- `report_path` 에 `t3only__<profile>__<delta>` 형을 더한다 — 덮어쓰기 사고의 재발 방지(PLAN-060 §10).

### 3.8 C7 · `Makefile`

```
gate-profile PROFILE=brick GRAPH=<D_n>     # l0? · L1 · L2 · L3 · T3 (프로파일 경로)
faults-profile PROFILE=brick               # X2·X4·X3 + 정상 델타
ep5                                        # A-4 전량 (사전등록 §6 판정까지)
```
`ep5` 타깃은 **이 작업에서 배선만 하고 실행하지 않는다**(A-4 는 별도 단계다).

### 3.9 C8 · `tests/`

신규 7건. **전량 개발 A-Box(`ex-rice_brick.ttl`·`ex-g36-combined-ahu-vav.ttl`)만 읽는다 —
홀드아웃은 A-1 에서 열지 않는다.**

| | 테스트 | 무엇을 막는가 |
|---|---|---|
| T-1 | `profiles/sdkb.yaml` 전사 == 현행 `config` 리터럴 | 이중 정본 표류 |
| T-2 | Brick 프로파일 로드가 사전등록 sha256 과 대조되고 불일치 시 예외 | 동결 밖 자원 위의 판정 |
| T-3 | Brick CQ 15개 파싱 · `# shared` 5건 인식 | §2 ② |
| T-4 | `suite_predicates(brick)` == 사전등록 §4.1 표 **∧ 각 집합 비어 있지 않음** | §2 ③ 거짓 통과 |
| T-5 | Brick 개발 행 수 == `ep5_cq_calibration.json` | 보정 기록과 코드의 어긋남 |
| T-6 | 결함 seed 결정성: 같은 (결함·강도·반복) → 같은 그래프 sha256 (양 프로파일) | F16 결정성 |
| T-7 | `t3only` JSON 이 `accept is None` **∧** `Accept_partial ∈ {0,1}` | 부분 승인을 승인으로 읽는 것 |

### 3.10 C9 · `paper/verdicts.yaml` — EP5 키 (제안 전문)

> **`verdicts.yaml` 수정은 §1-2 와 동급이다.** 아래 문안을 이 설계 승인에 포함해 함께 승인받고,
> 승인 없이는 넣지 않는다. **판정을 적지 않는다** — EP5 는 아직 돌지 않았고, 여기 들어가는 것은
> 사전등록 §0 이 결과 보기 전에 박은 **금지 문구 여섯**뿐이다.

```yaml
  EP5:
    record:
      - { registration: PLAN-064-prereg, verdict: 미실행(사전등록 발효 2026-08-22) }
    forbidden:
      - 'T-gate\s*(전체|전반)[의가]?\s*도메인\s*(독립|비의존)'
      - '제2\s*도메인.*(비열등|성능\s*우위)'
      - '제2\s*도메인.*하위집단.*(비회귀|안전)'
      - 'DP[124].*(2도메인|두\s*도메인)\s*실증'
      - '승인된\s*변경.*사후\s*안전성[이은는]?\s*(확인|보장)'
      - '(A-Box|자원)\s*규모가\s*(SDKB|반도체).*비교\s*가능'
    allowed:
      - '형식\s*층과\s*교차\s*태스크\s*층에\s*한정'
```

### 3.11 C10 · `analysis/faults.py` (신설 · 승인됨)

`run_instance(..., profile=None)`. 프로파일이 결정하는 것은 넷이다 — **주입 대상 그래프**
(`profile.graph_default` 또는 인자) · **기준 세대 라벨** · **누출 감사 실행 여부**
(`has_t1_t2=False` 이면 `None` 으로 기록하고 돌리지 않는다 · 사전등록에 누출 축이 없다) ·
**T1·T2 실행 여부**(기존 `skip_t12` 를 프로파일에서 유도). `summarize`·`render_table_*` 의
스위트 열은 `profile.cq_suites` 에서 생성한다.

**SDKB 경로의 기본값은 전부 현행과 같다** — 인자를 주지 않으면 지금과 한 글자도 다르지 않게 돈다.

### 3.12 C11 · `quarantine.py` (신설 · 승인됨)

`protected_paths(profile=None)` 가 프로파일의 `protected_paths` 를 푼다. Brick 의 봉인 대상은
**T-Box 6판 · A-Box 3종 · CQ 15개 · `delta.ttl`** 이며, 홀드아웃 파일은 **해시만 대조하고 내용을
읽지 않는다**(sha256 은 이미 `PROVENANCE.json` 에 있다). 봉인 없이 도는 경로는 만들지 않는다 —
결함주입이 정본을 오염시키는 사고를 막는 유일한 장치다.

---

## 4. 결정성·바이트 동일 계약 (S1 의 집행)

구현 중 **매 커밋** 아래 넷이 초록이어야 한다. 하나라도 붉으면 그 커밋은 되돌린다.

1. `make gate-graph` 출력 diff 0
2. `cq_g0.json` 재생성 바이트 동일
3. 기존 seed 로 SDKB 결함본 5종 재생성 → **공백노드 불변 정준 해시** 동일

> **③ 의 측정 방식을 구현 중에 정정했다(2026-08-22 · 실측).** 설계는 *"결함본 sha256 동일"*
> 이라고 적었으나 **그 형태로는 어떤 코드도 통과할 수 없다** — 직렬화 바이트도, 트리플 집합도
> 실행마다 다르다(같은 코드·같은 시드로 두 번 돌려 확인). 원인은 적재가 공백노드에 매번 새
> 라벨을 주기 때문이며, 트리플 수는 119,220 으로 동일했다. 그래서 공백노드를 담은 트리플
> (161건)은 개수만 세고 나머지를 정렬해 해시한다. 결함 조작이 바꾸는 것은 전부 명명 노드
> 사이의 간선이므로 이 형태는 조작에 민감하다. **기준선은 HEAD 워크트리에서 같은 스크립트를
> 돌려 떴다** — 변경 전후를 같은 자로 잰다. 이것은 기준을 낮춘 것이 아니라 **잴 수 없던 것을
> 잴 수 있게** 바꾼 것이며, 판정·수치는 이 정정으로 하나도 움직이지 않는다.
4. `paper/tables/cq_generations.md` 재생성 문자 동일

---

## 5. 신규 의존성

**`pyyaml` 을 `pyproject.toml` 에 명시한다.** 현재 `pyshacl` 경유로 설치돼 있어 `import yaml` 이
동작하지만(실측 6.0.3), **전이 의존에 기대는 것은 상류가 끊으면 게이트가 죽는다는 뜻**이다.
프로파일은 게이트의 입력이므로 명시 선언이 옳다. 이 외 신규 의존성은 없다.

---

## 6. 하지 않는 것

- 홀드아웃 A-Box 열람 · EP5 판정 실행
- 승인식 개정(T1·T2 를 부분 승인식에 넣거나 T4 를 편입하는 일)
- `vocab_coverage.py` 의 프로파일화 — **게이트가 아니라 측정**이며 EP5 판정에 들어가지 않는다.
  하려면 근거가 필요하고, 지금은 없다(§1-10).
- SDKB 상수의 값 변경 · 기존 결함 인스턴스 재주입

---

## 7. 구현 순서 (4단계)

`profile.py` + `profiles/sdkb.yaml` + T-1 → `config` 파생 전환(§4 계약 확인) → `cq_runner`(C2·C6′) →
`shacl_gate`(C5) → `t3`(C3) → `fault_inject`(C4) → `t_gate`(C6) → `faults.py`(C10) →
`quarantine`(C11) → `profiles/brick.yaml` + T-2–T-7 → `Makefile`(C7) → `verdicts.yaml`(C9).

각 단계마다 §4 의 넷을 돌린다 — 마지막에 몰아서 확인하면 어느 변경이 깼는지 가릴 수 없다.


---

## 8. 구현 기록 (4단계 · 2026-08-22)

### 8.1 설계와 다르게 간 자리 넷 — 전부 실측이 사유다

| | 설계 | 실제 | 사유 |
|---|---|---|---|
| ① | 계약 ③ = 결함본 sha256 동일 | **공백노드 불변 정준 해시** 동일 | §4 각주 — 그 형태로는 **어떤 코드도** 통과할 수 없다(같은 코드·같은 시드로 두 번 돌려 확인) |
| ② | `Profile.generation_dir` 을 그대로 사용 | sdkb 에서는 `config.CQ_GEN_DIR` 을 읽는 `gen_dir()` 경유 | 세대 디렉터리는 도구·테스트가 오래 써 온 **대체(monkeypatch) 지점**이다. 옮기면 이 작업이 바꾸지 않기로 한 SDKB 동작을 바꾼다. **값이 둘인 것이 아니라 이름이 둘**이며 동일성은 T-1 이 단언한다 |
| ③ | `CQResult.in_gate` 를 프로파일 값으로 | `in_gate` 는 그대로 두고 `gated(profile)` 을 신설 | 두 프로파일 모두 게이트 대상이 `graph` 하나라 동작이 같고, 기존 속성을 바꾸면 호출부 전량이 흔들린다 |
| ④ | 테스트 7건 | **10건** | 부분 승인식·빈 추출·자기모순 로드가 각각 별개의 실패 양식이라 하나로 묶을 수 없었다 |

### 8.2 구현 중 드러난 것 둘 — 보고 대상

**(가) `suite_predicates()` 의 거짓 통과는 실증됐다.** 스위트 라벨은 맞고 어휘만 낯선 CQ 를
넣으면 구 구현의 추출 결과가 `{"pa": set(), "em": set()}` 이고, 그 위의 교집합 검사는 **통과**
한다. `tests/test_profile.py::test_empty_extraction_fails_loudly` 가 이 상황을 그대로 재현한 뒤
예외를 요구한다.

**(나) 파서 이중화는 값을 바꾸지 않은 채 해소됐다.** `scripts/ep5_cq_calibrate.py` 의 지역
정규식을 지우고 `suite_predicates()`·`_parse_meta()` 로 교체한 뒤 `ep5_cq_calibration.json` 이
**바이트 동일**하게 재생성됐다 — 사전등록 §4.1 표의 근거가 바뀌지 않았다는 증거다.

### 8.3 범위 밖으로 남긴 것

- `scripts/rerank_ceiling.py:29` 의 미사용 import — **A-1 이전부터 있던 것**이며(HEAD 확인)
  `make lint` 는 `src tests` 만 보므로 검사에 걸리지 않는다. 고치지 않았다(§1-10).
- `Makefile` 의 `family` 타깃 중복 정의(226행·454행) — 역시 **HEAD 에 이미 있다**(2건 확인).
- `validate/vocab_coverage.py` 의 프로파일화 — 측정이지 게이트가 아니다(§6 그대로).
- **커밋된 표 6.6 과 커밋된 면제 로그의 어긋남** — `paper/tables/cq_generations.md` 는
  *"면제 승인 9건 · 판정 로그 67행"* 이라 적혀 있으나 같은 커밋의
  `data/cq_generations/dedup_exemption_log.jsonl` 은 **76행(18건)** 이다. 둘 다 2026-07-28
  커밋이며 **A-1 이전부터 어긋나 있었다.** 이 작업의 계약 검증은 *생성 출력*의 변경 전후
  동일성을 본 것이라 이 드리프트에 영향을 받지 않는다(재생성 결과는 변경 전후 모두
  `60239f43…`). 재생성본으로 갱신하는 것은 **원고 산출물 변경**이라 A-1 의 범위 밖이므로
  워킹트리를 HEAD 로 되돌려 두었다 — 갱신 여부는 별도 결정 사항이다.

### 8.4 계약 넷의 최종 상태

| 계약 | 결과 |
|---|---|
| ① `cq_runner`(G₀·mini)·`shacl_gate` 출력 | **diff 0** |
| ② `cq_g0.json` | `eb80027231400a71…` — 기준선과 동일 |
| ③ 결함본 5종 정준 해시(F11·F12·F13·F14·F15) | HEAD 워크트리 대비 **전량 동일** |
| ④ `paper/tables/cq_generations.md` | `60239f43baa7dbf2…` — 기준선과 동일 |
