# SPEC-002 · baseline G₀ (H1 의 "보강 전 그래프")

| | |
|---|---|
| 지지하는 것 | H1 (공정 커버리지) / 논문 §3.1 · §4.3 |
| 구현 | `src/sdkb_paper/ontology/{vendor,baseline}.py`, `data/external/sdkb/` |
| 검증 | `make baseline` · `tests/test_baseline_integration.py` |

**G₀ 가 움직이면 H1 이 무효가 된다.** 이 SPEC 의 존재 이유는 그것을 막는 것이다.

---

## 보장하는 것

**G₀ = 현행 SDKB.** SIRP 거절특허 1,000건을 **포함한다**.
→ `baseline.EXPECTED_PATENTS = 1000`, `test_baseline_carries_sirp_patents`

**의존 방향은 한 방향뿐이다.**

```
SDKB 원본(~/Dev/sdkb) ──(사람이 make vendor)──> data/external/sdkb/ (얼린 스냅샷 + sha256)
                                                        └──> make baseline ──> graph_v0 = G₀
```
이 저장소의 **어떤 코드도 `~/Dev/sdkb` 를 런타임에 읽지 않는다.** 오직 `ontology/vendor.py` 만,
그것도 사람이 명시적으로 실행할 때만.

**결정적이다.** 같은 스냅샷 → 같은 그래프(바이트 단위 동일).
→ `test_baseline_is_deterministic` (두 번 조립해 sha256 비교)

**서명 (`make baseline` 출력, SDKB 커밋 `c49dea0`)**

| 항목 | 값 | 이것이 깨지면 |
|---|---:|---|
| 트리플 | 26,676 | 스냅샷이나 조립이 바뀌었다 |
| Process / SubProcess | 8 / 12 | **H1 의 관측 단위(n=20)가 바뀐다** |
| Device | 31 | H2 의 개념 축이 바뀐다 |
| Patent | 1,000 | SIRP 가 빠졌거나 상류가 바뀌었다 |
| 출원일 보유 | 1,000 (100%) | H2 시계열의 전제가 깨진다 |
| 출원인(Organization) | 351 | CQ08(포트폴리오)이 무너진다 |
| **커버된 공정 / 공백** | **16 / 4** | **H1 의 before 가 움직인다** |

→ `test_baseline_observation_units`, `test_baseline_patents_have_filing_dates`,
`test_baseline_patents_have_applicants`, `test_baseline_coverage_is_not_vacuous`

**커버리지가 자명하지 않다.** `0 < C₀ < 전체` 를 테스트가 강제한다. C₀=0 이면 어떤 보강도
유의해져 H1 이 검정이 아니게 된다.

---

## 보장하지 않는 것

- **매핑의 옳음.** SIRP 의 특허↔공정 링크는 상류 SDKB 가 만든 것이다(구조화 필드 브리지 +
  한국어 자유텍스트 추출). 이 논문은 그것을 **주어진 것으로 받는다.**
- **G₀ 와 G₁ 의 매핑 방법 동일성.** G₀ 의 링크는 SDKB 의 방법으로, G₁ 의 삼성 특허는 이 논문의
  IPC 룰로 매핑된다. **이 비대칭은 논문 §5.3 한계에 명시하고 §4.5 강건성으로 점검해야 한다.**
- **출원인 명칭의 완전한 정규화.** `_org_slug()` 는 법인격 접미어·구두점만 흡수한다. 동일 기업의
  표기 변형이 남을 수 있다(예: 삼성 계열 5개가 별도 IRI). 프로파일로 드러내고 §5.3 에 적는다.

---

## 왜 이렇게 했는가

**특허 0건 baseline 을 폐기했다.** 이전 설계는 SIRP 를 의도적으로 제외해 G₀ 를 특허 0건으로
두었다. 그러면 모든 공정 단계에서 **C₀(s) = 0** 이므로 `C₁(s) − C₀(s) ≥ 0` 이 항상 성립하고,
삼성 특허가 몇 건만 매핑돼도 Wilcoxon(n=20, 단측)이 최소 p값과 효과크기 1.0 을 뱉는다.
**기각될 수 없는 가설은 가설이 아니다.** 논문 v0.2 §2.4 가 SDKB 2단계의 특허 보강을 명시하면서
이 모순이 표면화됐다.

**상류의 결함은 상류에서 고쳤다** (SDKB `4fca29c`, `c49dea0`). 이 저장소에서 우회 패치를 하면
스냅샷의 출처가 거짓이 된다. 고친 것:
- **출원일이 실은 공개일이었다** — raw JSONL 의 `target_patent.date` 가 `biblio.unex_pub_date` 와
  동일(99%). KIPRIS 권위 조회로 1,000건 전량 재수집. 이 정정 없이 H2 를 돌렸으면 모든 시계열이
  1~2년 밀렸다.
- **ABox 가 TBox 를 무시하고 평행 어휘를 발명하고 있었다** — `concernsProcess`(TBox 미정의) →
  `realizesProcess`, `primaryIpc`(리터럴) → `hasIPC`+IPCSymbol 노드.
- **출원인이 전무했다** — TBox 는 `ont:assignedTo` 를 정의해 두었는데 ABox 가 비워둠.

**개념 축은 Process ∪ Device.** 논문 §3.4.4 의 H2 사례(HBM, GAA)가 공정이 아니라 **디바이스**다.
Device 없이는 H2 가 자기 검증 사례를 온톨로지에 매핑조차 할 수 없다.
다만 **H1 의 관측 단위는 공정 20개를 유지한다**(§3.4.3) — 가설을 결과를 본 뒤 바꾸지 않는다.
개념 51개 기준 커버리지는 §4.5 강건성으로 병기한다.
