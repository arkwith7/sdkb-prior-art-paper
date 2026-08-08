# CR-014 — B층 질의 200의 서지 세 속성 (D-31 · L1 게이트 차단)

> 상태: ✅ **종료 (2026-08-08) — 상류 구현 `212fe62` · 하류 반영 · `make gate` 완주**
> 회신 **§7** · 하류 조치와 판정 **§8**. 셋 중 **둘을 채웠고 둘은 원천이 없어 채우지 않았다** —
> 그래서 shape 를 **회신 뒤에** 출처 조건부로 열었다(§8.1). 우선순위 **P0**(해소)
> 결함: [DEFECT-LEDGER.md](DEFECT-LEDGER.md) **D-31**
> 선행: [CR-012](archive/CR-012-b-layer-query-nodes.md)(질의 노드 발행 · 상류 `732b0d9`)의 **직접 후속**
> **차단 대상:** 하류 L1(SHACL) → `make gate` → 판독 B 개봉. 하류 [PLAN-045](../01.code_spec/plans/PLAN-045-b-layer-query-ingestion-downstream.md) 5단계.

---

## 1. 무엇이 문제인가 — 한 문장

**CR-012 가 세운 B층 질의 200 은 하류 SHACL 계약이 `ont:RejectedPatent` 에 요구하는 서지
여섯 중 셋을 갖지 않아, G₀ 가 L1 을 통과하지 못한다.**

## 2. 증거 (실행된 코드의 출력 · 2026-08-08 · PLAN-045 5단계)

`make vendor`(상류 `7347410`) → `make baseline` → SHACL 검증:

```
[baseline] graph_v0.ttl (118,808 triples)   # 115,076 → +3,732
[baseline] Process=12  SubProcess=38  Device=34  Patent=1200
conforms: False | 위반 총계: 600
  ont:processFamily:     200
  ont:publicationNumber: 200
  ont:valueChainStage:   200
고유 focus 노드: 200  (= B층 전량)
```

**A층 대조 (상류 `sdkb-abox-patents.ttl` 실측):** `publicationNumber` **1000** ·
`processFamily` **1000** · `valueChainStage` **1000**.

**즉 이것은 "B층이라 완화되는 요구"가 아니다** — A층은 셋 다 100 % 보유한다.
CR-012 는 *"A층과 같은 생성기·같은 IRI 규칙"* 을 요구했고 청구항 분해는 정확히 그렇게
왔는데, **서지 세 칸이 함께 오지 않았다.**

## 3. 왜 하류에서 고치지 않는가

고칠 수 있는 자리는 하나뿐이다 — `pat:RejectedPatentContentShape` 의 `targetClass` 를
좁히거나 `minCount` 를 낮추는 것. **그것은 결과를 본 뒤 합격선을 고치는 것이다**
(CLAUDE.md §1-2·§1-3). D-30 이 같은 유혹을 이미 한 번 보여줬고, 그때도 규칙을 느슨하게
만들지 않았다.

세 속성이 **채워질 수 없는 것**이라면 그것은 하류가 판단할 사실이 아니라 **상류가 회신에
적을 사실**이다. 그 회신이 오면 그때 shape 를 고치는 것이 정당해진다 — 순서가 반대면
게이트가 게이트가 아니게 된다.

## 4. 요구 — 선호 형태

**A층 발행 규칙을 그대로 B층에 적용한다.** 새 술어·새 클래스는 필요 없다(T-Box 델타 0 유지).

| 속성 | 원천 | 비고 |
|---|---|---|
| `ont:publicationNumber` | KIPRIS 서지 | 거절결정 특허는 공개번호를 갖는다. **`publicationDate` 도 함께 채우면 하류의 시점 필터가 정상 동작한다**(§5 ⓑ) |
| `ont:processFamily` | A층 파생 규칙 | 개념링크가 없는 건은 A층이 쓰는 기본값과 **같은 규칙**으로 |
| `ont:valueChainStage` | A층 파생 규칙 | 〃 |

**비목표(바꾸지 말 것).** ⓐ **인용 간선을 만들지 않는다**(CR-012 비목표 ⓐ 승계 — 만들면
그 간선이 곧 봉인 qrel 의 내용이다) · ⓑ A층 1,000 의 IRI·트리플을 건드리지 않는다 ·
ⓒ T-Box 를 바꾸지 않는다 · ⓓ 파일 분리 구조(`sdkb-abox-b-layer-queries.ttl`)를 유지한다.

## 5. 검증기준 (수정되면 어떤 수치가 어떻게 변해야 하는가)

**①이 하류 지표다**(CLAUDE.md §0.1 — 자원 지표만 걸지 않는다).

1. **하류 `make baseline` 후 SHACL `conforms=True` · 위반 0** ← 지금 600
2. A층 IRI·트리플 변경 **0** (G₀ 델타는 B층 200 노드의 속성 추가분에 한정)
3. 인용 간선 신설 **0** — `make leakage` 금지 간선 0 · 봉인 `127a138f…`·`984f8ef3…` 불변
4. 하류 코퍼스 `is_query` **1,200 유지** · `is_candidate` **41,031 유지**
5. **(선택 · 강하게 권장)** `ont:publicationDate` 200/200 — 채워지면 하류가 B층 문서를
   시점 필터로도 거를 수 있게 된다. **다만 하류는 이것에 의존하지 않는다** —
   `is_candidate` 로 이미 닫았다(PLAN-045 D2 §"왜 상류 보완을 고르지 않았나").

## 6. 이 CR 을 읽는 법

**CR-012 를 되돌리는 것이 아니다.** CR-012 가 만든 것(질의 노드 200 · 인용 간선 0 ·
T-Box 델타 0 · 독립항 1.0000)은 전부 그대로 옳고, 하류는 그것을 **성공적으로 소비했다** —
`is_query` 1,000 → 1,200 이 실제로 섰고 A층 분할 경계도 지켜졌다(PLAN-045 S1–S7 전부 통과).
남은 것은 **서지 세 칸**이며, 그것이 L1 을 막고 있다.

**"상류가 발행했는데 하류가 소비하지 못한다"의 네 번째 사례다**(D-19 · D-26 · D-27 · D-31).
매번 CR 이 겨눈 것보다 한 겹 앞이 막았다. 그래서 이 CR 은 **검증기준 ①을 하류에서 센 수로**
잡는다 — 상류에서 "채웠다"가 아니라 하류에서 "통과했다"로만 닫힌다.

---

## 7. 상류 회신 (2026-08-08 · 상류 `212fe62` · **셋 중 하나만 채웠다**)

> **이 세션이 상류 역할을 맡아 직접 구현했다**(사용자 승인 2026-08-08 · 하류 §0.1 예외).
> 상류 CLAUDE.md §2 의 정지 게이트는 그대로 탔다 — 1단계 요구정의 승인 → 2단계 원천 관찰 →
> 3·4단계 구현 → 5단계 3층 검증.

### 7.1 결론 먼저

| 요구 속성 | 판정 | 실측 |
|---|---|---|
| `ont:publicationNumber` | ✅ **채웠다** | **200/200** |
| `ont:publicationDate` (§4 비고 · §5-5) | ✅ **채웠다** | **200/200** |
| `ont:processFamily` | ❌ **채우지 않는다 — 원천이 없다** | 0/200 |
| `ont:valueChainStage` | ❌ **채우지 않는다 — 원천이 없다** | 0/200 |

`ontology/sdkb-abox-b-layer-queries.ttl` 트리플 **4,204 → 4,604 (+400)**. 400 이지 600 이
아닌 것이 회신의 요지다 — **빈 두 칸은 실수가 아니라 판단이다.**

### 7.2 채운 것 — 값은 `openNumber` 이지 `publicationNumber` 가 아니다

KIPRIS `getBibliographyDetailInfoSearch` 응답에도 `publicationNumber` 필드가 있다. 그것은
**공고번호**이고 거절특허는 등록되지 않아 **200건 전량 `null`** 이다. A층의
`ont:publicationNumber` 는 SIRP `biblio.unex_pub_number` = **공개번호**(`10-2022-0148249`
형식)이므로, 같은 의미를 담는 칸은 `openNumber` 다.

```
1020180000130 → openNumber 10-2019-0083014 · openDate 2019.07.11 | publicationNumber(공고) = None
```

**이름만 보고 골랐으면 칸은 비고 값은 A층과 다른 것을 담았을 것이다**(상류 §1.3).
형식(`10-YYYY-NNNNNNN`)과 **공개일 ≥ 출원일**을 상류 테스트가 고정한다
(`tests/test_b_layer_query_nodes.py::test_publication_number_is_the_open_number`).

### 7.3 채우지 않은 것 — **두 값은 특허의 속성이 아니다**

이것이 이 CR 이 요구한 *"A층 파생 규칙 그대로"* 가 **성립하지 않는 이유**다. A층의 두 값은
파생 규칙의 산물이 아니라 **SIRP 코호트의 수집 출처**다. 원본 실측:

```
meta = {'collection_stage':'etch_core', 'search_strategy':'plasma_H01J37',
        'process_family':'etch', 'value_chain':['process','equipment']}
```

즉 값의 원천은 KIPRIS 가 아니라 **"어느 검색 전략(키워드 게이트 + IPC)이 그 특허를 건졌는가"**
이며(`paper_data/scripts/expand_dataset_via_api.py`), B층 200 은 하류가 **다른 절차**
(IPC 스트림 스크리닝 · `data/processed/ir/b_layer/screening_ledger.jsonl` 의 `stream_ipc`)로
뽑았기 때문에 그 라벨이 **존재하지 않는다.** A층 parquet · SIRP 원본과의 교집합도 **0 건**이라
조인으로 가져올 수도 없다(실측).

**추정으로 채우지 않은 이유는 둘이고, 둘째가 결정적이다.**

- ⓐ IPC·개념링크로 추론하면 **같은 이름의 다른 것**이 된다(상류 §1.3 — CR-012 가 `process_family`
  구조화 브리지를 추정하지 않은 것과 같은 이유).
- ⓑ **하류 T2 하위집단이 "공정군"으로 갈린다.** A층은 검색전략 라벨 · B층은 IPC 추론 라벨이 되면
  T2 는 **서로 다른 규칙으로 만든 층을 같은 축으로 비교**하게 된다. 빌드는 성공하고 하위집단
  분석만 거짓이 된다 — **비어 있는 것보다 나쁘다.**

못 채운 이유는 산출물에 수치와 함께 남는다 —
`data/reports/abox_b_layer_queries_report.json` → `cr014_bibliographic.unfilled_reason`.
**빈 것을 조용히 비워 두지 않는다.**

### 7.4 불변 (검증기준 ②③)

인용 간선 3종 **0**(생성기가 세고 0 이 아니면 중단) · T-Box 델타 **0** · IRI 규칙 **0** ·
A층 1,000 트리플 **0** · 파일 분리 구조 유지 · `RejectedPatent` **200**.
재수집 200/200 후에도 청구항·초록·개념링크 수치는 **한 자리도 바뀌지 않았다**(리포트 diff).

상류 검증: `make validate` 3층 통과(A층·B층 각각) · `pytest` **208 passed, 10 skipped**
(신규 3건 — 서지 충전 · 값 의미 · 추정 금지).

---

## 8. 하류 조치와 종료 판정 (2026-08-08 · 하류 `212fe62` 스냅샷)

### 8.1 shape 를 **회신 뒤에** 고쳤다 — 순서가 정당성이다

§3 이 적어 둔 그대로다: *"세 속성이 채워질 수 없는 것이라면 그것은 하류가 판단할 사실이 아니라
상류가 회신에 적을 사실이다. 그 회신이 오면 그때 shape 를 고치는 것이 정당해진다."*

`pat:RejectedPatentContentShape` 의 **공정군·가치사슬 두 줄만** `sh:or` 로 열었고, 조건은
**출처**다 — `prov:wasGeneratedBy <…/activity/b_layer_query_ingest>` 를 가진 노드만 면제된다.
그 출처는 상류 생성기 하나만 붙일 수 있어 손으로 얻을 수 없다(CR-012 가 인용 `minCount` 에
쓴 패턴 그대로).

**`minCount` 를 낮추지 않았다** — 낮추면 A층 1,000 에 걸린 계약까지 함께 풀린다.
**면제는 두 칸에만 걸린다** — 초록·제1항·심사상태·**공개번호**는 B층도 그대로 요구받는다.
회귀 테스트 셋이 두 방향을 다 고정한다(`tests/test_baseline_integration.py`):

| 테스트 | 무엇을 막는가 |
|---|---|
| `test_process_family_exemption_does_not_leak_to_a_layer` | 출처 없는 거절특허가 공정군 없이 통과 → **거부되어야 한다** |
| `test_b_layer_exemption_does_not_cover_publication_number` | 면제가 서지 전체로 번짐 → **거부되어야 한다** |
| `test_b_layer_node_passes_without_process_family` | 면제가 실제로 작동 → **통과해야 한다** |

### 8.2 검증기준 판정 — **①②③④ 전부 충족 · ⑤ 충족**

| | 기준 | 실측 | 판정 |
|---|---|---|---|
| **①** | 하류 `make baseline` 후 SHACL `conforms=True` · 위반 0 (지금 600) | 서지 충전 후 **600 → 400**(공개번호 200 해소) · shape 개정 후 **conforms=True · 위반 0** | ✅ |
| **②** | A층 IRI·트리플 변경 0 | PROVENANCE 에서 **sha256 이 바뀐 파일은 `sdkb-abox-b-layer-queries.ttl` 하나**(21개 중) · G₀ 118,808 → **119,208**(+400 = 200 × 2 칸) | ✅ |
| **③** | 인용 간선 0 · 봉인 불변 | `make leakage` **PASS**(위반 0 · run 7개) · `qrel_test_sealed` `984f8ef3…` **불변** · `127a138f…` 미개봉 | ✅ |
| **④** | 코퍼스 `is_query` 1,200 · `is_candidate` 41,031 유지 | **1,200 / 41,031** — 코퍼스를 재조립하지 않았으므로 정의상 유지(§8.3 의 단서) | ✅ |
| **⑤** | (선택·권장) `publicationDate` 200/200 | **200/200** | ✅ |

**`make gate` 가 처음으로 완주했다** — L0–L3 ✅ · 누출감사 ✅ · T1 ✅ · T2 ✅ · T3 ✅ →
**Accept(ΔG) = 1**. ⚠ 이 T-gate 는 **기존 run 위의 승인 판정**이고 새 검색 실험이 아니다.
수치를 새 확증으로 인용하지 않는다.

### 8.3 정직하게 남는 것 하나 — **코퍼스는 아직 이 두 칸을 읽지 않았다**

코퍼스를 재조립하지 않았으므로 검증기준 ④는 정의상 유지됐다. 그런데 재조립하면 값이 하나 움직인다:
**B층 질의이면서 A층 후보이기도 한 8건 중 6건의 `publication_date` 가 결측(NaN)에서 실제
공개일로 바뀐다**(실측). 그 6건은 지금 `pub_int = 0` 이라 시점 조건(`pub < 질의 출원일`)을
**항상 통과**하고 있다 — 즉 **공개되기 전 시점의 질의에도 후보로 제시되고 있다.**

**이것은 CR-014 가 만든 문제가 아니라 CR-014 가 드러낸 문제다.** 채워 넣으면 시점 필터가
비로소 정상 동작하고, 그 대가로 A층 6개 문서의 후보 자격이 질의별로 달라진다(6/41,031).
**결정 없이 흡수하지 않는다** — D-32 와 같은 형태의 판단이므로 대장에 **D-33** 으로 등재하고
사용자 판단을 받는다. **CR-014 의 종료는 이 결정에 걸려 있지 않다.**

### 8.4 종료

**CR-014 종료(2026-08-08).** D-31 은 닫혔다 — 하류에서 센 수로 닫혔고(§5 의 요구대로),
`make gate` 가 선다. 남은 것은 판독 B 개봉의 **사전등록**이며, 그것은 이 CR 의 범위가 아니다.
