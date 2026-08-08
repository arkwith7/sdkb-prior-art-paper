# CR-014 — B층 질의 200의 서지 세 속성 (D-31 · L1 게이트 차단)

> 상태: **1단계 요구정의 완료 · 송부 가능 (2026-08-08)** · 우선순위 **P0**
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
