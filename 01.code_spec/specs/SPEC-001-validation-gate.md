# SPEC-001 · 검증 게이트 (4층 L0–L3 + T-gate)

> **v0.9 확장 (2026-07-26).** 이 문서의 L0–L3는 **구조·논리·기능 정합**을 검증한다. v0.9 정본 기조에서
> 이 위에 **T-gate**(T1 검색 비열등 · T2 하위집단 안전성 · T3 교차 태스크 CQ 비회귀)가 얹혀 **진화
> 안전성(C3 · 다중 태스크 작동성)**을 검증한다 — L0–L3만으로는 놓치는 회귀를 잡는다(§T-gate 절 신설,
> 원고 §4·§6 · CLAUDE.md §5). v0.9 RQ1 = **검증 게이트**(H1 게이트 판별력·H2 승인 안전성).
> 아래 본문의 "H1 before"·"H2 시계열"은 구 커버리지/시계열 라벨(**S1·S2**)이다 —
> [../RECONCILIATION-v09.md](../RECONCILIATION-v09.md) §1.

> **2026-07-18 갱신 — 3층 → 4층.** 이 문서는 "3층 + 스냅샷 무결성"으로 쓰여 있었고, 그때 L0 는
> `make vendor` 안에서만 도는 반쪽이었다(`_reject_stale_artifacts()` 가 살아있는 SDKB 워킹트리를
> 요구 → 심사자가 저장소만 받아 돌리면 sha256 검사뿐). **이제 L0 는 독립 층이다** — `verify_freshness()`
> 신설 · CLI `--verify-freshness` · `make l0` · `gate: l0 validate reason cq vocab`. 논문 v0.5 가
> 초록·§4.3·§6.6·§7.2·§8 에서 주장하는 4층과 코드가 일치한다.

| | |
|---|---|
| 지지하는 것 | RQ1 (검증 게이트 — L0–L3 구조·논리·기능 + T-gate) / 논문 §3.3 · §4 · §6 |
| 구현 | `src/sdkb_paper/validate/{shacl_gate,reasoner_gate,cq_runner}.py`, `src/sdkb_paper/ontology/{vendor,merge}.py`, `queries/shapes/`, `queries/cq/` |
| 검증 | `make gate` · `tests/test_shacl_gate.py` · `tests/test_merge_gate.py` · `tests/test_baseline_integration.py` |

논문 §3.3 은 "게이트를 통과하지 못한 델타는 그래프에 병합되지 않는다"를 **방법론적 기여**로 주장한다.
이 SPEC 은 그 주장이 실제로 참이 되게 하는 계약이다.

---

## 보장하는 것

**L0-a 스냅샷 무결성.** 커밋된 `data/external/sdkb/` 의 모든 파일이 `PROVENANCE.json` 의 sha256 과
일치한다. PROVENANCE 가 모르는 TTL 이 섞이면 실패한다.
→ `vendor.verify_snapshot()` · `make snapshot` · `test_verify_snapshot_detects_tampering`,
`test_verify_snapshot_detects_stray_ttl`

**L0-b 신선도.** 그 스냅샷이 **옳게 재빌드된 최신본**인가. sha256 은 "바뀌지 않았음"만 보장하고
"옳게 빌드되었음"은 보장하지 않는다 — 2026-07-14 사고가 정확히 그 틈으로 났다. 해시는 내내 맞았고
L1–L3 는 내내 통과했는데, 공정 어휘 복원 **이전에** 빌드된 특허 ABox 가 얼려져 H1 의 before 가
실제보다 낮았다(C₀ 16 → 정정 20). 그래서 신선도는 별도 층이다(논문 §7.2).

상류 워킹트리는 심사자·CI 에 없으므로 **오프라인에서 검사 가능한 두 가지**를 본다:
(a) **이행 증명** — vendor 가 `_reject_stale_artifacts()` 를 실제로 돌린 흔적(PROVENANCE 의
`freshness` 블록)이 존재하고 대상 산출물 전부를 덮는가. 블록이 없으면 그 스냅샷은 신선도 검사를
거치지 않고 얼려진 것이고, **그것이 사고 당시의 상태다.**
(b) **파생 산출물 신선도** — `graph_v0` 가 스냅샷보다 새로운가. 스냅샷만 갱신하고 `make baseline` 을
잊으면 분석이 옛 그래프를 읽는다.
→ `vendor.verify_freshness()` (`vendor.py:86`) · `make l0` · 회귀 테스트 4개(통과 1 + 거부 3)

> **왜 이행 증명인가.** 상류 mtime 대조는 살아있는 SDKB 를 요구하므로 저장소만 받은 사람은 돌릴 수
> 없다. 그래서 강한 검사는 `make vendor` 시점에 하고(`_reject_stale_artifacts()`), L0 는 **그 검사가
> 남긴 서명을 검증**한다. 심사자가 재현할 수 있는 게이트가 4층이 되는 것은 이 분리 덕분이다.

**L1 구조 제약 (SHACL) — 두 겹이다.**

| shapes | 대상 | 요구 |
|---|---|---|
| `queries/shapes/graph/` | 그래프 전체 (G₀·G₁·G₂) | 출원번호 1개, 출원일 1개(`xsd:date`), prefLabel 규약 |
| `queries/shapes/delta/` | **병합되는 특허만** | 위 + **개념 매핑 ≥1 (Process ∪ Device)** |

두 겹인 이유: 게이트의 의미는 "이 데이터를 넣어도 되는가"이지 상류가 남긴 레거시의 소급 처벌이
아니다. SIRP 118건에 공정 링크가 없는 것은 **사실**이다 — IPC 가 `G11C`(기억장치 회로)·
`H10B`/`H10D`(소자) 같은 소자 분류다. 공정으로 억지 매핑하는 것은 날조다(CLAUDE.md §1.2).
→ `test_graph_gate_allows_patent_with_no_concept_link`, `test_delta_gate_rejects_patent_with_no_concept_link`

**L2 논리 일관성 (HermiT).** 그래프가 기술논리적으로 일관된다.
→ `make reason` · `test_baseline_is_logically_consistent`

**L3 기능 검증 (CQ).** 현행 배터리는 **28개**(`queries/cq/CQ01~CQ28.rq`) — 도출 프로토콜 P1–P5 는
[SPEC-004](SPEC-004-cq-derivation-protocol.md), 초기 K=8 설계 근거는 [archive/SPEC-003](../archive/SPEC-003-competency-questions.md)(아카이브 · 인용 금지).
실측 응답률 (2026-07-23 재측정): **G₀ 27/28 · G₁ 28/28 · G₂ 28/28 · mini_graph 28/28**. 지는 것은
**G₀ 의 CQ27(FTO 청구항)** 하나뿐 — 청구항 전문은 특허 보강 코퍼스(G₁·G₂)에 실체화돼 있고 baseline
에는 없다(2026-07-22 G₁ 청구항 축 적재로 G₁ 도 통과) — **결함이 아니라 배터리가 코퍼스를 판별한다는 증거**다.
응답률 단독은 게이트가 되지 않으므로 어휘 검증 커버리지를 반드시 병기한다(`make vocab`).

**게이트 실패 시 그래프는 불변이다.** `merge_with_gate()` 가 실패하면 출력 파일이 생기지 않는다.
→ `test_gate_rejects_bad_delta_and_leaves_graph_untouched`

**거부 경로가 살아 있다.** 통과만 확인하는 게이트는 게이트가 아니다. 스냅샷 변조, stray TTL,
TBox range 위반, 출원일 누락, 개념 매핑 누락 — 각각이 실제로 거부되는지 테스트가 고정한다.

---

## T-gate (v0.9 확장 · C3 진화 안전성) — **LIVE** ✅

L0–L3는 그래프의 **구조·논리·기능** 정합을 본다. v0.9는 그 위에 **태스크 회귀**를 잡는 세 층을 얹는다.
델타는 L0–L3와 T1–T3를 **모두** 통과해야 병합된다(CLAUDE.md §5 승인 규칙).

| 층 | 검증 | 실패 조건 | 방법 |
|---|---|---|---|
| **T1** | 검색 비열등성 | `LB₉₅(ΔRecall@100) ≤ −ε` (ε=0.02) | 부트스트랩 신뢰구간 · 누출 감사 통과 전제 |
| **T2** | 하위집단 안전성 | `max_s drop_s ≥ δ` (δ=0.05) — 거절근거·공정군·**언어(KR/외국)**별 국소 회귀 | 하위집단 Recall 비교 |
| **T3** | 교차 태스크 CQ 비회귀 | `∃f∈{em,tf,core}: pass_f(new) < pass_f(old)` | 결정론적 CQ 통과율 비교(통계검정 아님) |

- **승인 규칙**: `Accept = (L0=L1=L2=L3=pass) ∧ (LB₉₅(ΔR₁₀₀)>−ε) ∧ (max_s drop_s<δ) ∧ (∀f: pass_f(new)≥pass_f(old))`.
- ε·δ는 **테스트 qrel 개봉 전 동결**(CLAUDE.md §1.3). T3 하락 시 즉시 실패, 예외는 waiver 토큰만(횟수 보고).
- **T3는 통계가 아니라 명세 비교다** — em(전문가매칭)·tf(기술예측)·core 스위트가 선행기술 검색 보강으로
  훼손되지 않음을 보증(= 다중 태스크 작동성). 이 세 스위트가 **S1/S2의 T3 회귀 감시 대상**이다.
- **상태: 구현·실행 완료 (2026-07-28 · W3/N4).** 구현부 =
  `src/sdkb_paper/validate/{leakage_check,t1_noninferiority,t2_subgroup,t3_cross_task_cq,t_gate}.py` ·
  진입점 `make leakage`·`make cq-freeze`·`make tgate` 이고 `make gate` 에 편입됐다.
  **실측(dev):** 누출 0 · T1 LB₉₅ **+0.0129** · T2 max drop **−0.0222** · T3 하락 0 → **Accept=1**.
  **확증분할(주 델타 P1 vs B3):** T1 LB₉₅ **+0.0145** · T2 max drop **−0.0140** · T3 하락 0 → Accept=1.
  산출 = `data/processed/tgate_report{,_test,_test_p0star}.json`.
- **게이트의 판별력은 별도로 검정됐다.** "Accept=1"은 게이트가 *통과시켰다*는 사실일 뿐 게이트가
  *결함을 잡는다*는 증거가 아니다. 판별력은 결함주입으로 검정했고(H1 기각 → H1′ 기각 → 층 분리 후
  H1″ 탐색적 지지 → **H1‴ 홀드아웃 72 확증**: T3 단독검출 12/45 · p=.0001 · 위양성 0/27),
  잔여 한계는 τ=0.10 기각·특이성 미검정이다. 매트릭스 = `data/processed/fault_matrix*.json`.
- **⚠ 이 절의 T-gate 실행을 H2(갱신 승인 안전성)의 증거로 인용하지 않는다.** 위 판정은 **P1 대 B3
  = 시스템 델타** 비교이고, H2는 **동일 파이프라인에 O와 O′를 넣은 버전 델타** 비교를 요구한다.
  실측 D-12에 따르면 G0·G1·G2의 T-Box가 완전히 동일해 **자격 있는 델타가 존재한 적이 없다** —
  H2는 미검정이며, 그 해소는 상류 릴리스 정책 변경에 달려 있다(CLAUDE.md §0 경계표 ·
  [upstream/DEFECT-LEDGER.md](../../upstream/DEFECT-LEDGER.md) D-10·D-12).

---

## 보장하지 않는 것

- **의미의 정확성.** SHACL 은 "특허가 공정에 매핑되었는가"만 보고 "**옳은** 공정에 매핑되었는가"는
  보지 않는다. 매핑 품질은 룰 테이블의 책임이며, 논문 §4.5 강건성 점검의 대상이다.
- **레거시 특허의 개념 매핑.** 그래프 shapes 는 공정 링크 없는 특허를 통과시킨다(위 참조).
- **CQ 의 응답 품질.** L3 는 응답 행 수만 센다. 응답이 **옳은지**는 검사하지 않는다.

---

## 왜 이렇게 했는가

**L2 는 원본 그래프를 그대로 리즈너에 넘기지 않는다.** owlready2 는 Turtle 을 파싱하지 못하고
(RDF/XML·NTriples 만), HermiT 는 `xsd:date` 를 지원하지 않는다(OWL 2 datatype map 밖 →
`UnsupportedDatatypeException`). 게다가 `owl:imports` 때문에 리즈너가 네트워크를 타고 404 로 죽었다.
그래서 `reasoner_gate.reasoning_view()` 가 **추론 전용 뷰**를 만든다: RDF/XML 변환 ·
`owl:imports` 제거(네트워크 의존 차단) · `xsd:date` → `xsd:dateTime` 승격.

**원본의 `xsd:date` 는 손대지 않는다** — H2 시계열의 전제이고 L1 이 검사한다. range 공리와
리터럴을 **함께** 승격하므로 타입 위반 탐지력은 보존된다.
→ `test_reasoner_rejects_range_violation` 이 이 보존을 고정한다(승격이 검사를 무력화하면 L2 는
항상 통과하는 가짜 게이트가 된다).

**기각한 대안: Pellet.** owlready2 번들 JAR 이 깨져 있다(`UnsupportedClassVersionError`,
class file 69 vs 65).

**게이트 대상이 두 그래프인 이유.** `graph_v0` 하나로는 병합 델타의 계약(개념 매핑 ≥1)이 한 번도
exercise 되지 않는다. 합성 특허 3건이 든 `data/samples/mini_graph.ttl` 이 엄격 shape 와 CQ **27개**를
전부 때린다. 지금 게이트 대상은 **세 그래프**다(`graph_v0`·`graph_v1`/`graph_v2`·`mini_graph`) —
하나로는 게이트가 vacuous 해진다.

**델타를 단독으로 검증하지 않는다.** 델타에는 TBox 도, 델타가 가리키는 공정 인스턴스도 없어
`sh:class ont:Process` 가 성립하지 않는다. 그래서 `shacl_gate.target_only()` 가 **그래프는 합치되
shape 의 대상만 델타의 특허로 좁힌다.**
