# PLAN-002 · 삼성전자 특허 수집과 G₁ 구축

| | |
|---|---|
| 지지하는 것 | H1 (커버리지) · H2 (조기 탐지) / 논문 §3.2 · §4.1 · §4.3 · §4.4 |
| 상태 | **요구정의 🛑 — 승인 대기.** PLAN-001 완료 후 착수 |
| 승인 | — |

---

## 0. 선행 조건 (반드시 먼저)

1. **PLAN-001(H10 룰 보강) 완료.** 룰이 없으면 삼성 특허의 상당수가 매핑되지 않아 L1(델타)에서
   탈락하고 H1 이 과소 추정된다.
2. **G₀ 동결.** 수집을 시작하기 전에 상류 SDKB 를 더 이상 건드리지 않는다. 분석 도중 before 가
   움직이면 H1 이 재현되지 않는다.

---

## 1. 요구정의  🛑

```
목적      : 삼성전자 반도체 특허를 수집·전처리·매핑해 게이트를 통과시킨 뒤 G₁ 을 만든다.
            G₀ vs G₁ 이 H1·H2 의 유일한 대비다.
입력      : KIPRIS Plus 학술 API (출원인=삼성전자, 반도체 분류, 기간 [확정 필요])
            Google Patents BigQuery — DOCDB 패밀리 (패밀리 단위 dedup)
출력      : data/raw/kipris/*.parquet (커밋 안 함)
            data/profiles/kipris_samsung.md  ← **데이터 프로파일 의무** (CLAUDE.md §4)
            data/processed/graph_v1.ttl (스냅샷) + data/MANIFEST.md 갱신 (한 커밋으로)
성공 기준 : 델타가 L1(엄격)·L2·L3 를 통과해 merge_with_gate() 로 병합된다.
            프로파일 4종(구조·형태·기술통계·사용목적)이 코드로 산출된다.
비목표    : 타 출원인 확장. 텍스트 임베딩 매핑(미매핑 잔여는 정직하게 보고).
```

### ⚠ 중복 제거 (이미 확인된 사실)

**G₀ 에 삼성전자 특허가 이미 75건 있다** (SIRP 출원인 실측: SK hynix 128 · **Samsung 75** ·
SEL 42 · TSMC 29 · Toshiba 28 · AMAT 26 · LAM 19 — Organization 351개).

이 75건을 걸러내지 않으면 **같은 특허가 before(G₀)와 after(델타) 양쪽에 들어가** H1 의 대응표본
비교가 오염된다.

→ 삼성 델타를 만들 때 **출원번호(하이픈 제거 정규화) 기준으로 G₀ 의 특허와 중복 제거**하고,
중복 건수를 MANIFEST 와 프로파일에 보고한다.

### 확정해야 할 것 (논문 §3.2 의 `[최종 확정 목록]`)

- 검색식: 출원인 표기 변형(삼성전자 / SAMSUNG ELECTRONICS CO., LTD. / 계열사 분리)
- 반도체 분류 목록: H01L, H10 계열, G03F, C23C … — PLAN-001 의 결과와 정합해야 함
- 분석 기간 (§3.2 는 "[예: 2010–2025년]")
  → **결과를 본 뒤에 기간을 바꾸는 것은 p-hacking 이다.** 여기서 확정한다.

---

## 2. 분석  🛑 (아직 수행하지 않음)

- 소량(1페이지) 수집으로 **KIPRIS 응답 스키마를 실물로 확인**한다.
  `collect/kipris_client.py` 는 아직 골격이다 — 엔드포인트·태그명에 TODO 가 달려 있다.
  (참고: `getBibliographyDetailInfoSearch` 는 검증됨 — SDKB 정비에서 1,000건 수집에 사용)
- 예상 규모, 출원인 표기 변형, 결측률을 실측한다.

## 3. 설계  🛑 (미정)

- `collect/` → `preprocess/` → `ontology/mapping` → `merge` 경계의 계약을 확정한다.
- 패밀리 dedup 을 BigQuery 로 할지, 출원번호만으로 할지.

## 4. 구현

## 5. 검증  🛑

- **데이터 프로파일 의무** (CLAUDE.md §4): 구조 · 형태 · 기술통계 · 사용 목적.
  → `data/profiles/kipris_samsung.md` (코드가 생성). 논문 **표 3** 의 원천.
- `make gate` 통과. `graph_v1.ttl` 스냅샷 + MANIFEST 를 **한 커밋으로**.
- G₁ 의 CQ 리포트(`cq_report_graph_v1.md`)로 §4.2 의 after 열을 만든다.
  → 비교 대상은 [SPEC-003](../specs/SPEC-003-competency-questions.md) 의 G₀ before 값:
  CQ01=16 · CQ03=4 · CQ06=29 · CQ07=46 · CQ08=317
