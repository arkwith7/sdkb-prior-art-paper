# SPEC-002 · baseline G₀ (H1 의 "보강 전 그래프")

> **⚠️ 구 패러다임 문서 — 인용 시 S-시리즈로 재라벨.** 이 문서는 커버리지 H1 패러다임(v0.5/v0.7)의
> 기록이다. v0.9 정본 기조(선행기술 검색 주 태스크 · paper/논문_v0_9_SDKB_통합초안.md)에서 이 작업은
> **S1(구 커버리지 H1) — 자원 형성 타당성의 2차 재사용 증거**로 강등·보존된다. 본문의 "H1"은
> **S1(구 H1)**을 뜻하며, v0.9 확증 가설 H1–H5와 혼동하지 않는다. 재라벨 기준:
> [../RECONCILIATION-v09.md](../RECONCILIATION-v09.md) §1 라벨 사전.

| | |
|---|---|
| 지지하는 것 | S1 (구 커버리지 H1 · 공정 커버리지) / 논문 §3.1 · §4.3 |
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

**서명 (`make baseline` 출력, SDKB 커밋 `edb8ae4` · 2026-07-15 규제·FTO 어휘 적재 후 최종 재동결)**

> ⚠ **서명 수치의 정본은 [CANONICAL-INDEX.md](../CANONICAL-INDEX.md) §1 이다.** 아래 표는 재동결
> 시점마다 갱신한다 (트리플 이력: 43,712 → 43,745 → 43,812 → 44,192 → **44,202** 현재).
> 트리플·커밋을 제외한 서명(C₀ 20/29·Process 11/SubProcess 38·Device 34·Patent 1,000 등)은 불변이다.

| 항목 | 값 | 이것이 깨지면 |
|---|---:|---|
| 트리플 | 44,202 | 스냅샷이나 조립이 바뀌었다 |
| Expert / Problem 의 `skos:prefLabel` | 110 / 226 (`rdfs:label` 0) | **인력·문제 질의가 IRI 만 돌려준다** |
| Process / SubProcess | 11 / 38 | **H1 의 관측 단위(n=49)가 바뀐다** |
| Device | 34 | H2 의 개념 축이 바뀐다 |
| Patent | 1,000 | SIRP 가 빠졌거나 상류가 바뀌었다 |
| 출원일 보유 | 1,000 (100%) | H2 시계열의 전제가 깨진다 |
| 출원인(Organization) | 351 | CQ08(포트폴리오)이 무너진다 |
| Vendor | 340 | CQ13(공급 벤더)이 무너진다 |
| **커버된 공정 / 공백** | **20 / 29** | **H1 의 before 가 움직인다** |
| **회사 IRI 스킴** | **`data:organization/` 단일** | **IP-R&D 질의가 조용히 절반만 답한다** |

> **회사 하나 = IRI 하나.** 상류는 같은 회사에 **역할에 따라 다른 IRI** 를 줬었다 — 큐레이션
> 기업 `data:org/`, 장비 공급사 `data:vendor/`, 특허 출원인 `data:organization/`. 역할은 이미
> `rdf:type`(`ont:Organization`·`ont:Vendor`)이 말하는데 IRI 접두사가 그것을 중복하면서
> **정체성만 깼다**. 갈라진 채로는 "이 회사가 공급하는 장비와 이 회사의 특허"라는 IP-R&D 의
> 핵심 질의가 **에러 없이 0행**을 낸다. 11쌍을 병합했다(근거: SDKB `mappings/org_identity_crosswalk.csv`).
> 유일한 예외는 `data:vendor/generic` — 실재 회사가 아닌 자리표시자다.
>
> **특허 엣지는 한 건도 움직이지 않았다** (`assignedTo` 1,053 불변) — 갈라져 있던 `org/`·`vendor/`
> 노드는 in-edge 가 0 이었기 때문이다. 그래서 **C₀ 20/49 도 H1 의 p 값도 불변**이다.

→ `test_baseline_observation_units`, `test_baseline_patents_have_filing_dates`,
`test_baseline_patents_have_applicants`, `test_baseline_coverage_is_not_vacuous`,
`test_baseline_company_identity_is_unified`

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

**공정 어휘를 복원했다 (PLAN-001, SDKB `ad7fe3d`).** SDKB 의 공정은 SemiKong Appendix A
Table 7 의 L1 Process Group 을 원천으로 하는데(`provenance.source_id`), 원천의 **10개 그룹 중 7개만**
담고 있었다 — **기판준비 · 어드밴스드 모듈 · 후공정**이 통째로 없었다. 다이싱·패키징·금속화를
표현할 어휘가 없는 baseline 으로는 RQ1("전 공정 커버리지")에 답할 수 없다. Table 7 의 Group·Module
열을 전량 복원해 공정 20 → **49**, 소자 31 → **34** 가 되었다.

**이것이 H1 에 유리한 편향을 만든다.** 복원된 단계는 G₀ 에서 C₀(s)=0 이므로 G₁ 이 채우기만 하면
이긴다. 복원 자체는 특허를 보기 전에 원천만 보고 했지만(따라서 §1.2 의 사후 조정은 아니다),
편향은 남는다. 그래서 **H1 은 두 집합으로 병기 보고한다** — 확장 집합(49)과 복원 이전 집합(20).
두 집합에서 결론이 갈리면 그 사실 자체를 결과로 적는다(논문 §3.4.3 · §5.3(f)).

**여기서 상류는 동결이다.** 삼성 특허를 한 건이라도 본 뒤의 어휘 변경은 사후 조정이 된다.
