# PLAN-064-prereg — EP5(제2 도메인 이식 시연) 사전등록

> **지위: 발효(동결).** 이 문서를 커밋한 뒤에 EP5 를 실행한다. 근거 규약은 CLAUDE.md **§2.1**
> (자원 버전이 바뀌면 정지 게이트 1개)과 **§1-3**(사전등록을 사후에 고치지 않는다)이다.
> **이 문서는 SDKB 실험의 판정·수치를 하나도 바꾸지 않는다** — EP5 는 새 자원 위의 **새 실험**이며,
> 기존 판정은 소급 수정되지 않는다.
>
> **발효일 2026-08-22.** 상위 설계는 [PLAN-064 §2](PLAN-064-second-domain-portability-and-aei-reframe.md)이고,
> 후보 적격 확인(A-0)은 같은 문서 §1.3 이다. 이 문서는 A-0 이후 **실측으로 확정된 값**만 담는다.
>
> **A-0 이후 설계가 바뀐 자리 셋을 먼저 밝힌다** — 전부 결과 확인 이전의 변경이며 근거는 실측이다.
> ① 태스크 뷰 셋 → **둘**(에너지 계량 제외 · §2) ② 교차 결함 4종 → **3종**(계량 뷰와 함께 X1 제외 · §4)
> ③ CQ 20 → **15**(스위트 셋 × 5 · §3). 개수를 줄인 이유는 전부 *"A-Box 가 받쳐 주지 않는다"* 하나다.

---

## 0. 결론 먼저 — 무엇을 주장할 수 있고 무엇을 주장하면 안 되는가

EP5 가 이식하는 것은 **절차**(L0–L3 + T3 + 결함주입)이고 이식하지 않는 것은 **태스크 벤치마크**
(T1·T2)와 **자원 규모**다. 따라서 결과가 어느 쪽으로 나오든 승격 후보가 되는 설계원리는
**DP3(교차 태스크 감시)** 하나이며, **DP1·DP2·DP4·DP5·DP6 의 등급은 EP5 로 바뀌지 않는다.**

**허용 문구.** *"형식 층과 교차 태스크 층에 한정하여 제2 도메인에서 동일 절차로 판정하였다"*
(영문: *"cross-domain evaluation of the formal and cross-task layers"*).

**금지 문구 여섯 — 결과를 보기 전에 박는다.**

| # | 주장하지 않는다 | 이유 |
|---|---|---|
| ① | T-gate **전체**의 도메인 독립성 | T1·T2 를 이식하지 않는다 |
| ② | 제2 도메인의 **태스크 성능 비열등성** | 정답·후보풀이 없다 |
| ③ | 제2 도메인의 **하위집단 비회귀** | T2 를 이식하지 않는다 |
| ④ | DP1·DP2·DP4 의 **2도메인 실증** | EP5 는 이 셋의 근거를 늘리지 않는다 |
| ⑤ | 승인된 변경의 **사후 안전성** | H2 미검정 상태는 EP5 로 변하지 않는다 |
| ⑥ | 제2 도메인의 **A-Box 규모가 SDKB 와 비교 가능하다** | 최대 공개 모델 3,774 트리플 ↔ SDKB G₀ 105,713 트리플 (A-0 K4 경고) |

**판정은 어느 쪽이든 싣는다.** T3 가 제2 도메인에서 교차 결함을 단독 검출하지 못하면 그 결과를
그대로 적고 DP3 의 도전 조건이 부분 성립했음을 밝힌다. **표를 채우려고 결함 강도·CQ·τ 를 사후에
조정하지 않는다.**

---

## 1. 대상 자원 — 파일별 sha256 (동결)

정본 기록은 [`data/external/brick/PROVENANCE.json`](../../data/external/brick/PROVENANCE.json)이다.
TTL 자체는 공개 릴리스에서 재생성 가능하므로 커밋하지 않는다(`.gitignore`).
취득 명령은 `uv run python scripts/probe_brick_candidate.py data/external/brick --download` 이며,
A-Box 예제는 **`v1.4.4` 태그의 `examples/` 경로에 고정**했다.

### 1.1 T-Box 계보 — v1.3.0 이후로 한정한다

**v1.2.1 → v1.3.0 은 변경이 아니라 재설계이므로 계보에서 뺀다**(`owl:Class` 2,413 → 1,438 ·
`sh:NodeShape` 30 → 1,452 · A-0 K1 경고 ⓐ). v1.2.1 파일은 후보 적격 확인용으로만 내려받았다.

| 태그 | 발행일 | 트리플 | sha256 |
|---|---|---|---|
| v1.3.0 | 2022-10-12 | 52,113 | `a88a716d6ff90748e4847d99cae5e581f8dd9efd2c85e3f207110e59fbb44882` |
| v1.4.0 | 2024-04-15 | 54,631 | `d336095f4cc24bbdee63ba414bb12f46dd6450f718cbe8a4b3c9be23fc26f620` |
| v1.4.1 | 2024-08-23 | 53,646 | `20d5ed752d7e3eb6c4941e6e7ba6bd05f1f95c7656662f66cdd450dc24f0c359` |
| v1.4.2 | 2024-09-20 | 55,055 | `c4a9a35355da6be158123f5dced3a7ad0714d3a2cab51c6a80c4720c3c8d28f0` |
| v1.4.3 | 2025-03-20 | 55,308 | `bff317821868628601d1d0780eab78f58fd66c28d545eb50fd28419fb25ef456` |
| v1.4.4 | 2025-05-02 | 53,960 | `b65720b7b9b64c646745c689777e6138c0d59ce0088df0aeb78fbd444d04d8e7` |

`D0…D5` 는 이 여섯 T-Box 각각에 **홀드아웃 A-Box** 를 얹은 그래프이며, 인접 쌍 **5건**에 대해
L0–L3 + T3 를 1회씩 적용한다.

### 1.2 A-Box 분할 — 개발과 홀드아웃을 파일 단위로 가른다

| 역할 | 파일 | 트리플 | sha256 | 용도 |
|---|---|---|---|---|
| 개발 | `ex-rice_brick.ttl` | 1,665 | `33c3bb0c1a748b28178eb1a689c73bcbbfc293c9a0ee2e73b8a92565d68cc8f0` | CQ 작성·expect-min 확정 |
| 개발 | `ex-g36-combined-ahu-vav.ttl` | 93 | `c2cf22b2d8bcb0f351732504aea7271689de8d312e09c05077a43c427aa14490` | 같음 (FDD 어휘 보강) |
| **홀드아웃** | `ex-soda_brick.ttl` | 3,774 | `09c2ca37b628e6eea88c0b0791a3c028c3c22083c6302055aa85b609a9d17254` | **결함주입·릴리스 계보 판정 전용** |
| 제외 | `ex-building_meter.ttl` · `ex-main-and-submeter.ttl` · `ex-solar_array.ttl` | 55·54·139 | PROVENANCE.json | 계량 뷰 제외와 함께 제외 (§2) |

**홀드아웃은 판정 실행 전까지 열지 않는다.** CQ 보정 스크립트
[`scripts/ep5_cq_calibrate.py`](../../scripts/ep5_cq_calibrate.py)는 개발 두 파일만 읽는다.
A-0(후보 적격 확인)이 홀드아웃의 **타입 단언 계수**를 이미 관측했다는 사실은 여기 밝혀 둔다 —
관측된 것은 규모이지 CQ 결과가 아니며, CQ 는 그 계수를 보고 고르지 않았다.

---

## 2. 태스크 뷰 둘 — 고장탐지·진단 + 공간·구역 점유

| 층 | 뷰 | 스위트 | CQ |
|---|---|---|---|
| **L3**(주 태스크) | 고장탐지·진단(FDD) | `fdd` | 5 |
| **T3**(타 태스크) | 공간·구역 점유 | `space` | 5 |
| **T3**(공유 어휘) | Equipment–Location–Point 연결 | `core` (`# shared: true`) | 5 |

**에너지 계량 뷰를 뺀 이유는 실측이다.** 공개 예제 가운데 큰 모델 둘의 계량 인스턴스가
`soda_brick` **1건** · `rice_brick` **0건**이고, 계량 예제 파일은 54–139 트리플의 장난감이다
(A-0 K3). 0 행 위에서 도는 CQ 는 vacuous 하므로 뷰 자체를 제외한다. **이 결정은 결과 확인
이전이며 사유는 위 계수다.**

`L3 ∩ T3 = ∅` 는 스위트 배정으로 유지하고, 술어 수준의 관계는 §4.1 에 실측으로 적는다.

---

## 3. CQ 스위트 — 전문 15개의 sha256 과 expect-min (동결)

전문은 [`queries/brick/cq/`](../../queries/brick/cq/)에 있다. **`expect-min` 은 전량 1 로 고정했고,
그 값은 실행 이전에 정했다** — 개발 건물의 행 수를 보고 문턱을 올리면 그것이 정확히 사후 조정이다.
판정은 존재검사(v1)가 아니라 **행 수 회귀(v2 · τ)** 가 지므로 문턱을 낮게 두어도 검출력은 τ 가 진다.

| CQ | 스위트 | expect-min | 개발 행 수 | sha256 |
|---|---|---|---|---|
| `FDD01_ahu_discharge_air_temperature.rq` | fdd | 1 | 4 | `e52dbe60b2b98bfe63e8b27caabb0c6a4558cb5ff074baf1f766f3525b7d5602` |
| `FDD02_vav_airflow_points.rq` | fdd | 1 | 120 | `9e7e5a8b83cb05931a326ff5f3f268d169fc1dd2ce86a2e82ba3165dcb545525` |
| `FDD03_equipment_status_points.rq` | fdd | 1 | 2 | `2b9befe8ba0824574bfe35034adf6d0336822a6b4de57e4eb8d71aad9694aa9b` |
| `FDD04_equipment_command_points.rq` | fdd | 1 | 9 | `516ece9ba272db38b6850edc3ced4f1f3ff81f6efcdf70933d1ef1ceae993cf4` |
| `FDD05_air_supply_chain_sensors.rq` | fdd | 1 | 8 | `7bd859933ff6461dad79d2115be9b32152b0407aa0c8bb1dd4ea7a5b8e5433e3` |
| `SPA01_building_floor_room_hierarchy.rq` | space | 1 | 90 | `dd0d69a8c72bef712d24fd8ddd59aa001dfa70298da5b7bbf83bab1289b6751f` |
| `SPA02_points_located_in_rooms.rq` | space | 1 | 168 | `c730eca375e390243794fa924441c2f2ce0c26780404282c72744d29065ba892` |
| `SPA03_rooms_with_occupancy_sensing.rq` | space | 1 | 4 | `ad751b993f14510e18ae680f32bf3c2cc8d2eea42714a0506d47756aa8fe4710` |
| `SPA04_hvac_zone_membership.rq` | space | 1 | 108 | `036fed237b20c02786db6a053f961e34a88a0aac2bb75b3aa23f42ed242f7a61` |
| `SPA05_room_count_per_floor.rq` | space | 1 | 5 | `15e54da273b89019638f728c94a6fae6fc8e28caf175fd70f5a0cd5d82cb0e3d` |
| `CORE02_sensor_count_per_location.rq` | core | 1 | 90 | `e27ee858e1891158d4a5c47fca5c1eadfd4f970bdbbf6bbab490fd98486e4d78` |
| `CORE04_zone_room_point_path.rq` | core | 1 | 221 | `1ddfdb7f17030ca2ae5f6847afc5fbd1c4020690b81f5cb0895795a87cae62f6` |
| `CORE05_equipment_parts_with_points.rq` | core | 1 | 14 | `8704199679df804a73a31d68eac1e14cc5fa217fc98ddb9cd004f497286d5e6c` |
| `CORE06_equipment_points_in_rooms.rq` | core | 1 | 134 | `e15d4f9ab0dbb46e68cdd696e64361753c99ba4d688898ccde22276bb66c7b0e` |
| `CORE07_floor_room_sensor_path.rq` | core | 1 | 167 | `c12b7df68afae0812b90731b3326c43d31b1f37e899653a18ab1a9f5045c2373` |

개발 행 수의 산출 조건: **D0 = Brick v1.3.0 + 개발 A-Box 2개 = 53,871 트리플**, 기록은
[`data/external/brick/ep5_cq_calibration.json`](../../data/external/brick/ep5_cq_calibration.json).

**0 행 CQ 2건을 제거했고 대체 2건을 작성했다 — 개수를 보고한다(§2.2 규율).**
제거: `CORE01_equipment_location_point.rq`(장비에 직접 부여된 위치 링크가 개발 모델에 없다) ·
`CORE03_feeds_pairs_with_locations.rq`(같은 이유로 공급 쌍의 위치를 얻지 못한다).
대체: `CORE06`·`CORE07` — 개발 모델이 실제로 쓰는 공유 경로(Equipment–Point–Room ·
Floor–Room–Sensor)로 다시 썼다. **제거·대체는 전부 개발 건물에서, 판정 실행 이전에 이루어졌다.**
**홀드아웃에서 0 행인 CQ 는 제거하지 않고 "홀드아웃 미충족"으로 보고한다.**

### 3.1 CQ 헤더 규율

모든 CQ 는 `# desc / # suite / # monotone / # expect-min` 을 갖고, `core` 는 `# shared: true` 를
추가로 갖는다(공유 어휘를 **의도적으로** 참조함을 표기). 파서는 기존 `cq_runner._parse_meta` 를
프로파일화하여 재사용한다(PLAN-064 §3 C1·C2 — 코드 변경은 A-1 이며 이 문서의 동결 대상이 아니다).

### 3.2 L1 델타 shape — 3규칙 (동결)

[`queries/brick/shapes/delta.ttl`](../../queries/brick/shapes/delta.ttl) ·
sha256 `fde91ac47c43d9e7a7f9bae580cd397ddd26e82a10ebdf72a5a27f8ed9c85358`.
**S-D1** 델타가 도입한 클래스는 `rdfs:label` 을 갖는다 · **S-D2** `owl:deprecated true` 항목은
`brick:deprecationMitigationMessage` 또는 `…Rule` 을 갖는다 · **S-D3** 델타가 도입한
`owl:ObjectProperty` 는 `rdfs:domain`·`rdfs:range` 를 갖는다. 세 규칙이 참조하는 술어는 전부
Brick v1.4.4 가 실제로 쓰는 것이다(실측 — `deprecatedInVersion` 250 · `deprecationMitigationMessage`
249 · `deprecationMitigationRule` 6). Brick 배포 TTL 내장 SHACL 은 **graph shape** 으로 별도 실행한다.

---

## 4. 교차 결함 3종 · 강도 · seed · τ 격자 (동결)

### 4.1 스위트별 참조 술어 — (M) 묶음의 전제를 실측으로 고정한다

| 스위트 | 참조 술어 |
|---|---|
| `fdd` | `feeds` · `isFedBy` · `hasPoint` · `isPointOf` |
| `space` | `hasPart` · `isPartOf` · `hasLocation` · `isLocationOf` |
| `core` | `hasPart` · `isPartOf` · `hasPoint` · `isPointOf` · `hasLocation` · `isLocationOf` |

**`fdd ∩ space = ∅`**(실측) · `core ∩ fdd = {hasPoint, isPointOf}` · `core ∩ space =
{hasPart, isPartOf, hasLocation, isLocationOf}`. 즉 `core` 는 설계대로 두 뷰에 걸쳐 있다.

### 4.2 결함 3종

| 묶음 | 결함 | 조작 | 왜 L1–L3(fdd)를 통과하는가 | 기대 검출 | 인스턴스 |
|---|---|---|---|---|---|
| **(M)** | **X2 · 공간 포함관계 역전** | 홀드아웃의 `brick:hasPart`(Building–Floor · Floor–Room) 중 강도 비율만큼 방향 역전 | 역관계 제약 부재 → L2 통과 · fdd 는 `hasPart` 를 참조하지 않는다(§4.1) | `space`·`core` — 행 수 감소 | 3 강도 × 3 반복 = **9** |
| **(M)** | **X4 · 위치 재배선** | `brick:isLocationOf` 의 주어를 **같은 클래스의 다른 Location** 으로 치환 | `sh:class` 통과 · fdd 비참조 | `space`·`core` — **행 수 불변 가능** | 3 강도 × 3 반복 = **9** |
| **(S)** | **X3 · 공유 관계 동치 오선언** | `owl:equivalentProperty` 선언 삽입. 강도 1 = `feeds ≡ hasPart` · 강도 2 = +`isFedBy ≡ isPartOf` · 강도 3 = +`hasPoint ≡ hasPart` (`owl:sameAs` 는 쓰지 않는다 — 속성에 쓰면 OWL DL 밖이라 L2 가 다른 이유로 잡는다) | 경로 후보가 늘어 fdd CQ 는 통과하거나 행 수가 **증가**한다 | `core`·`space` 복수 스위트 | 3 강도 × **1**(결정적) = **3** |

**합계 21 결함.** X3 의 반복을 1 로 두는 이유는 조작에 무작위 요소가 없어 반복이 정보를 더하지
않기 때문이며, 이 사실을 결과 표에 그대로 적는다. **X1(계량 포인트 오배선)은 계량 뷰와 함께
제외했다**(§2).

**강도 정의.** X2·X4 의 강도는 대상 트리플의 **5 % · 10 % · 20 %** 이고, 표본 추출은
`seed = 20260822 + 100·(결함 번호) + (반복 번호)` 로 고정한다. 결함 생성기는 같은 seed 에서
**바이트 동일** 산출을 내야 하며, 이는 SDKB 의 F16 결정성 검사와 같은 요구다.

**X4 는 T3 의 구성 타당도 경계 사례로 사전 지정한다.** 위치 재배선은 트리플 수를 보존하므로
현행 T3(존재 + 행 수)로는 놓칠 수 있다. **검출 실패는 결과의 실패가 아니라 경계의 실측**이며,
보조로 결과 binding 의 정렬 후 sha256(`result_digest`)을 **탐색적 지표**로 병기한다 —
**판정식에는 넣지 않는다.** 단, `CORE02`·`SPA05` 는 위치별 집계이므로 군 수가 바뀌면 행 수로도
잡힐 수 있다. 어느 쪽이 실제인지는 실행이 답한다.

### 4.3 τ 격자

CQ 회귀는 **행 수의 상대 감소 > τ** 로 정의한다. **τ = 0.05 를 주값**으로 하고 격자
**(0, 0.05, 0.10)** 전량을 동시에 보고한다. `monotone: up` 이므로 증가는 회귀가 아니다 —
X3 의 행 수 증가는 회귀로 세지 않으며, 그 사실 자체를 결과에 적는다.

---

## 5. 정상 델타 — 음성 대조군 (동결)

**실제 정상 델타 1건: `v1.4.1 → v1.4.2`.** 클래스·ObjectProperty·DatatypeProperty·NodeShape·
PropertyShape·deprecated 계수가 **전부 동일**하고 트리플만 53,646 → 55,055 로 움직이는 유일한
인접 쌍이다(A-0 실측). 이 쌍은 §6 의 릴리스 계보 판정에도 함께 들어간다.

**합성 정상 델타 30건.** 생성 규칙 넷을 seed `20260822` 로 조합한다 — ① 라벨 보존 재명명
(IRI 변경 + `owl:equivalentClass` 로 구 IRI 유지) ② 공식 deprecation 매핑의 부분 적용
③ `rdfs:comment`·단위 주석 추가 ④ 동치 클래스 alias 추가. **주 태스크·타 태스크 어느 CQ 의
경로도 끊지 않는 변경만** 생성하며, 생성기는 결정적이다.

**위양성 상한은 관측 개수와 함께 적는다.** 관측 위양성이 0/30 이면 95 % 단측 상한은
**9.5 %**(`1 − 0.05^(1/30)`)이므로, *"위양성 ≤ 5 %"* 라고 쓰지 않고
*"관측 위양성 0/30 · 5 % 수준의 정밀 검증은 미달"* 로 쓴다. 일정이 허락하면 60건으로 올리고
그때의 상한은 4.9 % 다 — **개수를 올리는 것은 허용하되, 결과를 본 뒤 올리지 않는다.**

---

## 6. 판정식과 확증·탐색의 구분 (동결)

### 6.1 결함 검출 판정 (확증)

- **T3 단독 검출** = `fdd` 전량 통과 ∧ (`space` ∪ `core`) 중 ≥ 1 실패.
- **확증 조건 셋의 동시 충족**: ① T3 단독 검출 ≥ 1 ② 단측 McNemar *p* < .05 (fdd 검출 대 T3 검출의
  불일치 쌍) ③ 정상 델타 위양성 관측치와 그 95 % 단측 상한 병기.
- **묶음별 분리 보고.** (M) 9+9 와 (S) 3 을 합산해 하나의 검출률로 쓰지 않는다.
- **검정력의 한계를 미리 적는다.** 결함 21건에서 부호검정이 *p* < .05 에 이르려면 불일치 쌍이
  **최소 5건**(0.5⁵ = .031)이다. 그보다 적으면 *"단독 검출은 관측되었으나 유의에 이르지 못했다"* 로
  쓴다.

### 6.2 릴리스 계보 판정 (확증)

인접 쌍 5건 × 이행 조건 2종 = **최대 10 판정**을 각 1회 실행하고 전부 싣는다.
승인식은 SDKB 와 다르다 — **T1·T2 가 없으므로 `accept` 는 `null` 로 기록**하고,
`Accept_partial = 1[L0–L3] · 1[T3]` 를 별도 필드로 남긴다. **부분 승인식을 승인식이라 부르지 않는다.**
결과 유형 셋 — (a) 전부 통과 (b) L1/L3 실패(폐기로 주 태스크 경로 소실) (c) **T3 만 실패**
(교차 회귀의 실측 · 가장 강한 결과). **재판정 규칙은 없다.**

### 6.3 이행 조건 R/N

각 델타를 **두 고정 조건**으로 실행하고 둘 다 보고한다. **(R)** 원본 A-Box 를 새 T-Box 에 그대로
얹는다. **(N)** 공식 alias·deprecation 이행 규칙(`brick:deprecationMitigationRule` 등)을 적용한 뒤
얹는다. R 에서 실패하고 N 에서 통과하면 *"공식 이행 규칙이 회귀를 흡수한다"* 는 관측이며,
**어느 한쪽을 취소하지 않는다.** "실패 시 재시도" 형태의 조건부 재량은 두지 않는다.

### 6.4 탐색적 산출 (판정 미편입)

`result_digest`(행 수 불변 오배선 관측) · 층별 실행시간과 최대 메모리 · 뷰별 세부 분해 ·
CQ 개별 행 수 변화. **이 넷은 어떤 판정에도 들어가지 않으며 결과 장에서 "탐색적"으로 표기한다.**

---

## 7. 운용 비용 측정 항목 (탐색적)

그래프 트리플 수 · shape 수 · CQ 수 · L0–L3·T3 층별 wall-clock · 최대 RSS 를 SDKB 와 Brick 나란히
표로 싣는다. **"scalable" 이라고 쓰지 않는다** — 실행 가능성과 비용만 진술한다.

---

## 8. 동결 목록 대조 (PLAN-064 §2.5)

| 요구 항목 | 이 문서의 자리 | 상태 |
|---|---|---|
| 개발/홀드아웃 A-Box 식별자와 sha256 | §1.2 | ✔ |
| 릴리스 계보 T-Box sha256 | §1.1 | ✔ |
| CQ 전문과 expect-min (개발 기준) | §3 (15건 · 전량 1) | ✔ |
| (M) 술어 교집합 검사 결과 | §4.1 (`fdd ∩ space = ∅`) | ✔ |
| 결함 명세와 seed | §4.2 | ✔ (4종 → **3종** · 사유 §2) |
| 정상 델타 개수와 생성 규칙 | §5 (실제 1 + 합성 30) | ✔ |
| 이행 조건 R/N 정의 | §6.3 | ✔ |
| 판정식 | §6.1·§6.2 | ✔ |
| τ 격자 | §4.3 | ✔ |
| DP 승격 규칙 | §0 (DP3 하나만 후보) | ✔ |
| 금지 문구 | §0 (여섯) | ✔ |
| 운용 비용 측정 항목 | §7 | ✔ |
| L1 델타 shape | §3.2 | ✔ (동결 대상에 추가) |

---

## 9. 이 문서가 바꾸지 않는 것

**SDKB 실험의 판정·수치·봉인은 하나도 바뀌지 않는다.** H1–H5·ε·δ·주지표·분할 경계·EP1–EP4 의
모든 값이 그대로이고, 봉인 qrel 은 열지 않는다. EP5 는 **다른 자원 위의 다른 실험**이며, 그
결과는 §0 의 허용 문구 범위 안에서만 원고에 들어간다.

**실행 순서.** 이 문서 커밋 → A-1(게이트 자원 비의존화 · PLAN-064 §3) → A-4(EP5 실행) →
A-5(원고 반영). **A-1 은 코드 변경이므로 §2.1 이 아니라 §2 를 탄다** — 이 사전등록은 자원과
평가 설계를 동결할 뿐 코드 변경의 게이트를 면제하지 않는다.
