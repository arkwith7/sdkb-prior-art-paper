# SPEC-001 · 검증 게이트 (3층 + 스냅샷 무결성)

| | |
|---|---|
| 지지하는 것 | RQ1 (구조적 정합성) / 논문 §3.3 · §4.2 |
| 구현 | `src/sdkb_paper/validate/{shacl_gate,reasoner_gate,cq_runner}.py`, `src/sdkb_paper/ontology/{vendor,merge}.py`, `queries/shapes/`, `queries/cq/` |
| 검증 | `make gate` · `tests/test_shacl_gate.py` · `tests/test_merge_gate.py` · `tests/test_baseline_integration.py` |

논문 §3.3 은 "게이트를 통과하지 못한 델타는 그래프에 병합되지 않는다"를 **방법론적 기여**로 주장한다.
이 SPEC 은 그 주장이 실제로 참이 되게 하는 계약이다.

---

## 보장하는 것

**스냅샷 무결성.** 커밋된 `data/external/sdkb/` 의 모든 파일이 `PROVENANCE.json` 의 sha256 과
일치한다. PROVENANCE 가 모르는 TTL 이 섞이면 실패한다.
→ `vendor.verify_snapshot()` · `make snapshot` · `test_verify_snapshot_detects_tampering`,
`test_verify_snapshot_detects_stray_ttl`

**L1 구조 제약 (SHACL) — 두 겹이다.**

| shapes | 대상 | 요구 |
|---|---|---|
| `queries/shapes/graph/` | 그래프 전체 (G₀·G₁) | 출원번호 1개, 출원일 1개(`xsd:date`) |
| `queries/shapes/delta/` | **병합되는 특허만** | 위 + **개념 매핑 ≥1 (Process ∪ Device)** |

두 겹인 이유: 게이트의 의미는 "이 데이터를 넣어도 되는가"이지 상류가 남긴 레거시의 소급 처벌이
아니다. SIRP 118건에 공정 링크가 없는 것은 **사실**이다 — IPC 가 `G11C`(기억장치 회로)·
`H10B`/`H10D`(소자) 같은 소자 분류다. 공정으로 억지 매핑하는 것은 날조다(CLAUDE.md §1.2).
→ `test_graph_gate_allows_patent_with_no_concept_link`, `test_delta_gate_rejects_patent_with_no_concept_link`

**L2 논리 일관성 (HermiT).** 그래프가 기술논리적으로 일관된다.
→ `make reason` · `test_baseline_is_logically_consistent`

**L3 기능 검증 (CQ).** → [SPEC-003](SPEC-003-competency-questions.md)

**게이트 실패 시 그래프는 불변이다.** `merge_with_gate()` 가 실패하면 출력 파일이 생기지 않는다.
→ `test_gate_rejects_bad_delta_and_leaves_graph_untouched`

**거부 경로가 살아 있다.** 통과만 확인하는 게이트는 게이트가 아니다. 스냅샷 변조, stray TTL,
TBox range 위반, 출원일 누락, 개념 매핑 누락 — 각각이 실제로 거부되는지 테스트가 고정한다.

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
exercise 되지 않는다. 합성 특허 3건이 든 `data/samples/mini_graph.ttl` 이 엄격 shape 와 CQ 8개를
전부 때린다.

**델타를 단독으로 검증하지 않는다.** 델타에는 TBox 도, 델타가 가리키는 공정 인스턴스도 없어
`sh:class ont:Process` 가 성립하지 않는다. 그래서 `shacl_gate.target_only()` 가 **그래프는 합치되
shape 의 대상만 델타의 특허로 좁힌다.**
