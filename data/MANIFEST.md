# 데이터 매니페스트

raw 데이터는 git 에 커밋하지 않는다. 모든 수집은 아래 표에 기록해 재현 가능하게 유지한다.

> **⚠ 라벨 규약 (2026-07-31).** 이 문서는 **수집·조립 이력의 기록**이므로 각 행은 그 시점의 표현을
> 그대로 보존한다. §1–§2 본문에 나오는 **"H1"·"H2"·"RQ3"는 전부 구 패러다임 라벨**이며 각각
> **S1(커버리지)·S2(시계열)·S3(이식성)**으로 읽는다 — v0.9 확증가설 H1–H5(검증게이트·검색유용성·
> 계층기여)와 **무관**하다(재라벨 기준 = [RECONCILIATION-v09 §1](../01.code_spec/RECONCILIATION-v09.md)).
> 문서 후반의 2026-07-25 이후 이력(IR 코퍼스·family 지도·시점분할·기준선·표/그림 산출)이 v0.9
> 기조의 기록이다. 서명 수치의 최종 판정은 [CANONICAL-INDEX §1](../01.code_spec/CANONICAL-INDEX.md).

## 1. 근간 온톨로지 스냅샷 (baseline)

이 논문의 baseline 은 SDKB(semiconductor-knowledge-base)를 **특정 커밋에 얼려서** 가져온
`data/external/sdkb/` 스냅샷이다. 살아있는 워킹트리를 참조하지 않는다 — baseline 이 움직이면
S1(구 H1 · 보강 전/후 커버리지 비교)이 재현되지 않기 때문이다. v0.9 에서도 같은 이유가 적용된다 — baseline 이 움직이면 게이트 기준선과 검색 결과가 함께 움직인다.

주의: SDKB 의 `sdkb-core.ttl` / `sdkb-core-data.ttl` 은 SDKB repo 의 **.gitignore 대상(빌드 산출물)**
이다. git 에 없으므로 submodule/pip 로는 가져올 수 없고, SDKB 쪽에서 `make owl convert` 로 생성한
결과를 복사해야 한다. 갱신 절차:

```bash
cd $SDKB_HOME && make owl convert   # 산출물 재생성
cd -                                # 논문 repo 로
make vendor                         # 스냅샷 갱신 (+ PROVENANCE.json 재작성)
make baseline                       # graph_v0 재조립
# -> 아래 표에 새 줄 추가하고 한 커밋으로 묶는다
```

| 일시 | 소스 | 커밋 | 가져온 것 | 규모 | 산출 그래프 |
|---|---|---|---|---:|---|
| 2026-07-11 | [semiconductor-knowledge-base](https://github.com/arkwith7/semiconductor-knowledge-base) (CDLA-Permissive-2.0) | `e64f90cc74ec` | TBox: core·patent·foresight / ABox: core-data (SIRP 제외) | 3,201 트리플 | (폐기) |
| 2026-07-12 | 〃 | `4fca29c3f6e2` | TBox: core·patent·foresight / ABox: core-data + **SIRP 특허 1,000건** | 24,566 트리플 | (대체됨) |
| 2026-07-12 | 〃 | `ad7fe3d2ecc6` | 〃 + **SemiKong Table 7 공정 어휘 복원**(그룹 1·9·10) + 소자 3개 | 26,973 트리플 | (대체됨) |
| 2026-07-14 | 〃 | `d4dff61…` | 〃 + **상류 지식 적재**(선행기술·거절·초록·청구항·인력·문제·KSIA 벤더) + **낡은 특허 A-Box 재빌드** | 43,745 트리플 | (대체됨) |
| 2026-07-14 | 〃 | `581360a…` | 〃 + **출원인 정체성 통합**(회사 하나 = IRI 하나 · 11쌍 병합) | 43,712 트리플 | (대체됨) |
| 2026-07-14 | 〃 | `23d07a140cec` | 〃 + **Expert·Problem 라벨 규약 교정**(`rdfs:label` → `skos:prefLabel`, 전문가 EN 표기 `altLabel` 100) | 43,812 트리플 | (대체됨) |
| 2026-07-15 | 〃 | `edb8ae48888` | 〃 + **US EAR/CCL 8·KR-ITPA 12 규제 인스턴스 + 개념↔통제 37 + FTO 청구항 어휘**(`ont:claimText`·`claimCount`) | **44,202 트리플** | (대체됨) |
| 2026-07-20 | 〃 | `5cbf149ce8a6` | 〃 + **인력 축 이름 재부여**(전문가 가명 충돌 해소 · 고유 이름 56→110 · 삭제 0) + 프로비넌스 정본화(`docs/deidentification_protocol.md`) | **44,202 트리플** (불변) · 이후 SubProcess 한국어 별칭 승격 `da745ef` 로 **44,221** | (대체됨) |
| 2026-07-21 | 〃 | `d583b0c` | 〃 + **전문가 상세 경력 A-Box 적재** — T-Box 신설(`ont:EquipmentModel`·`ont:ExpertCase`·경력 datatype 23종·사례 objprop 6) + `curated_profiles_kr.json` 상세 경력·장비 모델·사례 실체화(큐레이션 `ontology_alignment` 기반 링크) + 비식별 프로토콜 §1.5 갱신 | **49,210 트리플** (+4,906) | (대체됨) |
| 2026-07-23 | 〃 | `d578bf3` | 〃 + **청구항-feature·거절판단 TBox 반영** — 상류 `sdkb-patent.ttl` 순수 TBox 선언(신규 클래스 4 `Claim`·`ClaimFeature`·`PriorArtJudgment`·`CitedPatent` + object property 10 + datatype property 5)을 재벤더로 반영. **ABox·엣지 0 변경**(realizesProcess 1565·concernsDevice 181·assignedTo 1053·Patent 1000 불변) → C₀ 20/49·H1 네 표본집합 p 전부 불변. 청구항 분해 ABox(Tier 1/2/3)는 벤더 제외 별도 중심축 | **49,307 트리플** (+97) | (대체됨) |
| 2026-07-23 | 〃 | `d578bf3` | 〃 + **미반영 SDKB 온톨로지 전량 반영** (커밋 `3429d66` · 사용자 결정으로 동결 해제) — 스냅샷엔 벤더돼 있으나 `baseline.py` 적재 목록에서 빠져 있던 SDKB 온톨로지 3종을 편입: **(1) 심사관 인용 선행기술 ABox**(`sdkb-abox-prior-art.ttl` · `ont:CitedPatent` **3,034** + 개념링크 · 선행기술조사 정답지), **(2) 상용화 축**(`sdkb-commercialization.ttl` · TRL·라이선싱), **(3) 자원기반관점**(`sdkb-rbv.ttl` · VRIO·역량). **C₀ 20/49·H1 네 표본집합 p 전부 불변**(CitedPatent 는 명시 타입이 `ont:CitedPatent` 라 CQ01 이 안 셈 · CQ01=20·CQ03=29·CQ06=58·CQ10=8 불변) · **선행기술조사 정답지 도달성 0%→95.3%[노드]** · 델타특허 24,179/12,339 불변. SDKB 커밋 `d578bf3` 그대로·벤더 목록만 확장. **라이선스: 특허 전문 스냅샷 2종**(`sdkb-abox-patents.ttl`·`sdkb-abox-prior-art.ttl`)**은 gitignore**(§1.4) — PROVENANCE sha256·집계만 커밋 | **105,588 트리플** (+56,281) | `graph_v0.ttl` |

**G₀ 정의 변경 (2026-07-12) — 아래는 그 시점의 역사 서명이다.** 현재 G₀ 서명(트리플 105,588 ·
커버 20/49 · CQ06 58)은 **§3 과 [CANONICAL-INDEX.md](../01.code_spec/CANONICAL-INDEX.md) §1** 이 정본이다.
아래 표(26,973 · C₀ 16/49 · 공백 33 · CQ06 61)는 2026-07-12 정의 순간의 값으로, 이후 공정 어휘
복원·낡은 스냅샷 교정(C₀ 16→20)·규제 적재를 거치기 **전**이다. 역사 기록으로 남긴다.

이전 스냅샷은 SIRP 특허 ABox 를 의도적으로 제외해 baseline 을
특허 0건으로 두었다. 그러면 모든 공정 단계에서 C₀(s)=0 이 되어 **H1 이 기각될 수 없는 자명한
가설**이 된다. G₀ 는 "현행 SDKB"여야 한다. 정의 순간(2026-07-12)의 서명:

| 항목 | 값 |
|---|---:|
| 트리플 | 26,973 |
| 공정 단계 (H1 의 관측 단위) | **49** (Process 11 + SubProcess 38) |
| 디바이스 (H2 의 개념 축에 포함) | **34** |
| 특허 (SIRP 거절특허) | 1,000 |
| 출원일 보유 특허 | 1,000 (100%) |
| 출원인(Organization) | 353 |
| **커버된 공정 단계 C₀** | **16 / 49** |
| **커버리지 공백** | **33 / 49** |
| 최근 5년(2021–) 출원 전무 개념 (CQ06) | **61 / 83** |
| CQ 응답률 (8개) | **100%** |

**공정 어휘 복원 (2026-07-12, SDKB `ad7fe3d`).** SDKB 의 공정은 SemiKong Appendix A Table 7 의
L1 Process Group 을 원천으로 하는데(`provenance.source_id`), 원천은 그룹이 **10개**인 반면 SDKB 는
7개만 담고 있었다 — **기판준비 · 어드밴스드 모듈 · 후공정**(다이싱·패키징·금속화·웨이퍼 테스트)이
통째로 없었다. Table 7 의 Group·Module 열을 전량 복원해 공정 20 → 49, 소자 31 → 34 가 되었다.
복원된 단계는 G₀ 에서 C₀(s)=0 이므로 H1 에 유리한 편향이 있다 — H1 은 확장 집합(49)과 복원 이전
집합(20) 양쪽으로 병기 보고한다.

**출원인 상위 (SIRP 는 다출원인 코퍼스다)**: SK hynix 128 · **Samsung Electronics 75** ·
Semiconductor Energy Lab 42 · TSMC 29 · Applied Materials 26 · Toshiba 28 · LAM 19.
→ 삼성 특허를 수집할 때 **출원번호 기준 중복 제거가 필수**다. 이 75건이 이미 G₀ 에 있다.

- 상류에서 **출원일이 정정되었다**: SDKB 의 `filing_date` 는 출원일이 아니라 공개일이었다
  (KIPRIS 대조로 확인). SDKB 커밋 `4fca29c` 에서 KIPRIS 권위 원천으로 재수집·교체했다.
  이 정정 없이는 H2 시계열이 1~2년 밀린다.
- SIRP 는 **1,000건**이다. 초기 코호트 스냅샷이 773건이었고 GT 페어가 그 시점에 동결되어 있다 —
  이전 표의 "773건"은 그 혼동이었다.
- 파일별 sha256 은 `data/external/sdkb/PROVENANCE.json` 에 기록.
- `graph_v0.ttl` 은 스냅샷에서 결정적으로 재생성되므로 커밋하지 않는다 (`make baseline`).

## 2. 특허 수집 (KIPRIS / BigQuery)

| 일시 | 소스 | 검색식/쿼리 | 건수 | 저장 파일 | 그래프 반영 버전 |
|---|---|---|---:|---|---|
| 2026-07-13 | KIPRIS Plus `getAdvancedSearch` | `applicant=삼성전자주식회사 ∪ 에스케이하이닉스 주식회사` × `ipcNumber ∈ {룰 테이블의 18개 클래스}` × `applicationDate=20100101~20251231` (patent=true, utility=false) | 원시 50,514행 → 델타 후보 34,521 → **병합 24,179** | `raw/kipris/patents_raw.parquet` · `interim/patents_delta.parquet` (둘 다 gitignore) | `graph_v1.ttl` |
| 2026-07-13 | KIPRIS Plus `getAdvancedSearch` | 위와 **동일한 검색식** · 기간만 `applicationDate=20050101~20091231` (PLAN-009 · H2 좌측절단 교정) | 원시 41,443행 → 정제 후 **29,415** | `raw/kipris/patents_2005_2009.parquet` · `interim/patents_2005_2009.parquet` (둘 다 gitignore) | **없음 — 병합하지 않는다** |
| 2026-07-16 | KIPRIS Plus `getAdvancedSearch` | **RQ3 · C-2 소부장 전체.** `applicant ∈ {KSIA 소부장 188사 — 장비 93·재료 50·부분품 45}` (질의어=크로스워크 match_key) × `ipcNumber ∈ {18개 클래스}` × `20100101~20251231`. 정확일치 필터는 정규화-정확일치(㈜↔(주)·공동출원 파이프분리) | 원시 42,185행 → 정확일치 33,858 → dedup 21,950 → G₀겹침 −63 → 정제 **21,887 → 룰 매핑 12,358행 (+인식층 2 = 12,360행) → 중복 출원번호 −21 → 병합 12,339 노드** | `raw/kipris/patents_ksia_equipment_raw.parquet` · `interim/patents_ksia_equipment_delta.parquet` (gitignore) | `graph_v2.ttl` |
> **N4 해소 (2026-07-18).** 위 행의 매핑↔병합 −19 는 탈락이 아니라 **행 vs 노드**의 단위 차이다.
> 소부장은 회사별로 수집하므로 **KSIA 회원사 간 공동출원**은 양쪽 질의에 각각 잡히고(층별 검정에는
> 두 회사 실적으로 다 계상돼야 한다), 그래프는 출원번호가 키라 특허 하나에 노드 하나다. 실측:
> 정제 델타 21,887행 중 중복 출원번호 35건, 그중 매핑된 21건이 합쳐진다. G₁ 은 삼성·SK하이닉스가
> 서로 공동출원하지 않아 34,521행의 출원번호가 전부 고유했다(중복 0) — 그래서 +114 가 그대로 남았다.

| 2026-07-16 | KIPRIS Plus `getBibliographyDetailInfoSearch` | **초록+전체청구항** (출원번호별 · ServiceKey). 매핑 특허 **12,337건**만 조회(게이트 탈락분 미조회) | 상세 12,337건(청구항 보유 100%) · 청구항 그래프 실체화 **161,184 트리플** | `raw/kipris/patents_ksia_equipment_details.parquet` (gitignore) | `graph_v2.ttl` (`claimText`·`firstClaimText`·`abstractText`·`claimCount`) |
| 2026-07-22 | KIPRIS Plus `getBibliographyDetailInfoSearch` | **§G1 Phase A · 주 대비축 선행기술 feature.** 초록+전체청구항 (출원번호별 · ServiceKey). **G₁ 병합 특허 24,179건 전량**(룰 OR 인식층 = `merged_application_numbers`, 게이트 탈락분 미조회) | 상세 24,179건(청구항 보유 100%·초록 100%) · `claimText` **371,267 트리플**·`abstractText` 24,179·`firstClaimText` 24,179·`claimCount` 24,178(1건 claim_count=0 제외) · 신고>적재 52건 정직계상 | `raw/kipris/patents_samsung_hynix_details.parquet` (gitignore) · 프로파일 `profiles/kipris_samsung_hynix_details.md` | `graph_v1.ttl` (418,738→**862,541** 트리플 · **엣지 중립: realizesProcess 11,647·concernsDevice 23,342·Patent 25,179 불변 → H1 원리 불변**) |
| 2026-07-22 | Bedrock (Haiku 추출 · Sonnet 통합) | **§G1 Phase C · 특허 문제층.** 초록 → 문제원자(FailureMode·RootCause) 추출·정규화. 기존 45개념 재배치 3,378 + 특허에서 자란 신규 FailureMode 30개(사용자 채택 · frozen `data/failuremode_concepts_new.csv`) → 3,621 특허 문제엣지. 어휘 발명 0(`exhibitsFailureMode`·`relatedToTopic` 는 기존 TBox) | exhibitsFailureMode **2,816**·relatedToTopic **3,236**·FailureMode 25→**55**개념 · CQ28(특허↔문제↔전문가) 비공허 11,794행 | `interim/patent_problems.jsonl`·`patent_problems_resolved.jsonl` (gitignore) | `graph_v1.ttl` (862,541→**868,669** · **H1 불변: realizesProcess 11,647·concernsDevice 23,342·Patent 25,179 그대로** — 문제층은 커버리지 엣지 안 건드림) |

**재현 절차**: `make collect && make profile && make merge` (응답은 `raw/kipris/kipris_cache.sqlite`
에 캐시되므로 재실행해도 API 를 다시 때리지 않는다).
2005–2009 분은 `make collect-extended && make profile-extended`.

> **2005–2009 수집분은 그래프에 병합되지 않는다** (PLAN-009 §2). H2 시계열 전용이다 —
> G₁ 은 2010–2025 로 동결돼 있고, 병합하면 **H1 의 after 가 움직여** 이미 보고한 검정이 재현되지
> 않는다. H2 의 말뭉치는 처음부터 G₁ 이 아니라 수집 말뭉치 전체였으므로(미매핑 특허를 빼면 코드
> 팔이 불리해진다) 이 분리는 새로 생긴 비대칭이 아니다.
>
> **출원인명 변천은 검색식에 반영할 필요가 없었다** (실측 2026-07-13): KIPRIS 는 2005–09 출원도
> **현재 사명**으로 색인·반환한다 — H01L 2005–09 하이닉스 1,944건이 전부 `에스케이하이닉스 주식회사`
> 로 나온다(SK 편입은 2012년, 당시 사명은 주식회사 하이닉스반도체).
>
> **말뭉치 밀도가 과거에 더 높다**: 2005–09 는 연평균 **5,883건**, 2010–25 는 **2,158건**이다.
> 상대성장 규칙(θ × 직전 3년 평균)은 **두 팔에 대칭으로** 걸리므로 개념 vs 코드 **비교**는
> 공정하지만, 절대 탐지 시점은 말뭉치 밀도에 영향을 받는다. §5.3 에 교란으로 적는다.

### 2-1. CPC 분류 (BigQuery `patents-public-data`) — S2(구 H2) 의 대조군 (PLAN-007)

| 일시 | 소스 | 쿼리 | 건수 | 저장 파일 | 쓰이는 곳 |
|---|---|---|---:|---|---|
| 2026-07-13 | BQ `patents.publications` (현재 스냅샷) | KR 출원 34,521건의 `cpc.code` | 434,888행 · 출원 **33,266 / 34,521 (96.4%)** | `raw/bigquery/cpc_map.parquet` (gitignore) | H2 경로 B |
| 2026-07-13 | BQ `patents.publications_{201710,201903,202004,202101,202204,202304}` | 같은 출원의 **동결 스냅샷별** CPC | 스냅샷 6개 | `raw/bigquery/cpc_vintage.parquet` (gitignore) | H2 경로 C · C′ |

**재현 절차**: `make cpc && make cpc-vintage` (GCP 서비스계정 필요 —
`GOOGLE_APPLICATION_CREDENTIALS`). 스캔량 ≈ 16.5 GB + 6×16 GB (무료 한도 1 TB/월 내).

### 2-2. DOCDB 패밀리 (BigQuery `patents-public-data`) — §4.5 강건성 (PLAN-011)

| 일시 | 소스 | 쿼리 | 건수 | 저장 파일 | 쓰이는 곳 |
|---|---|---|---:|---|---|
| 2026-07-14 | BQ `patents.publications` | KR 출원 **64,936**건(델타 34,521 ∪ 2005–09 29,415 ∪ G₀ 1,000)의 `family_id` | 69,798행 · 출원 **63,679 / 64,936 (98.1%)** | `raw/bigquery/family_map.parquet` (gitignore) | **§4.5.1 표 9** — H1·H2′ 패밀리 dedup 전후 |

**재현 절차**: `make family && make robustness`. 프로파일은 `data/profiles/family_dedup.md`.

> **왜 G₀ 의 1,000건까지 질의했는가.** 델타 특허가 G₀ 특허와 **같은 패밀리**일 수 있다. 그때
> 그것은 새 발명이 아니라 G₀ 에 이미 있는 발명의 국내 중복 출원이다. G₀ 는 동결이므로 건드리지
> 않고 **델타 쪽을 뺀다**(실측 1건) — H1 의 before 는 한 트리플도 움직이지 않는다.

> **패밀리당 말뭉치 출원이 평균 1.00건이다.** KR 단일 관할만 수집했으므로 대부분의 특허가 자기
> 패밀리의 유일한 KR 구성원이다. 그래서 패밀리 dedup 이 지우는 것은 델타 34,521 중 **178건(0.52%)**,
> H2′ 유니온 63,936 중 **198건(0.31%)** 뿐이고, **H1·H2′ 의 결론은 하나도 바뀌지 않았다.**
> 이것은 dedup 을 안 해도 된다는 뜻이 아니라, **해봤더니 결론이 그것에 의존하지 않더라**는 뜻이다.

> **한 출원에 `family_id` 가 둘 붙는 경우가 9.6%(6,119건)다.** id 하나로 그룹핑하면 같은 발명이
> 두 패밀리로 쪼개져 dedup 이 헛돈다 — 공유 id 로 이어지는 출원들을 **연결성분**으로 묶는다
> (`preprocess/family.py`).

**왜 CPC 를 따로 받았는가.** KIPRIS `getAdvancedSearch` 는 **IPC 만** 준다. 그런데 H2 대조 코드
2개(`H10D30/6735` GAA · `H10W20/211` TSV)는 CPC 전용 코드(스킴에서 중괄호 표기)라 IPC 말뭉치에
**존재할 수 없다** — 34,521건에서 출현 0회였다.

**결측은 관측창 밖에만 있다.** 2010–2023 CPC 커버리지 **100%**. 결측 1,255건은 전부 2024–25년
(18개월 비공개 절단 구간)이라 탐지 판정에 영향이 없다.

> **소급 재분류 (PLAN-007 의 핵심 발견).** H10 스킴(H10B·H10D·H10W)은 **2021년 이후 신설**이고,
> 특허청이 과거 출원에 소급 부여했다. 실측: 2017-10 스냅샷 H10 코드 **0개** · 2021-01 **0개** ·
> 현재 **587,882행**. 2010년 출원의 62%가 지금은 H10 코드를 달고 있다. 따라서 **현재 스냅샷으로
> 만든 코드 시계열은 구조적으로 늦을 수 없다** — H2 가 말하는 것을 재지 못한다. 동결 스냅샷이
> 필요한 이유가 이것이다.

**IPC 18개 클래스**는 손으로 고른 목록이 아니라 `mappings/code_to_concept.csv` 의 코드 접두어에서
파생한다(`collect.ipc_classes()`). 룰과 수집 범위가 어긋나면 룰 없는 코드를 수집해 게이트에서
전량 버리거나, 룰 있는 코드를 빠뜨려 커버리지가 이유 없이 비기 때문이다.

**수집 규모의 감가 이력** (프로파일이 코드로 생성: `data/profiles/kipris_samsung_hynix.md`)

| 단계 | 건수 | 왜 줄었는가 |
|---|---:|---|
| 원시 수집 | 50,514 | 클래스 × 출원인 질의의 합 (한 특허가 여러 클래스에 잡힘) |
| 출원인 정확일치 | 47,500 | KIPRIS `applicant` 는 **부분일치** — 삼성디스플레이 등 계열사 제거 |
| 출원번호 중복 제거 | 34,608 | 클래스 간 중복 |
| G₀ 겹침 제외 | 34,521 | **−87건** (삼성 51 · 하이닉스 36). SIRP 거절특허로 이미 G₀ 에 있다 — 넣으면 H1 의 before/after 가 같은 특허를 센다 |
| 개념 매핑 성공 | **24,179** | 개념 ≥1 (L1 델타 shape 통과 조건). 미매핑 10,342 는 병합하지 않고 보고한다 |

> **24,053 → 24,179 (+126) 은 PLAN-006 의 별칭 확장이다.** H2 사례를 7건으로 사전등록하면서
> 신규 4개 개념(3D NAND·MRAM·FOWLP·TSV)의 1층 별칭을 추가했고, 코드 룰로는 잡히지 않던 특허
> 126건이 **이름 경로로** 들어왔다. 시계열을 보기 전에 동결된 별칭이다 (`mappings/h2_cases.csv`).

> **미매핑 10,342건(30.0%)의 정체.** 대부분이 G11C 메모리 **회로** 코드(입출력·타이밍·전원·테스트)와
> 의도적 미매핑 그룹(H10W29 범용부품 · H10P72 웨이퍼 핸들링 · H10B80 적층조립)이다. SDKB 에 회로
> 설계 축이 없다 — 이것은 데이터의 한계가 아니라 **온톨로지 범위의 경계**다. 자세한 이유는
> `mappings/PROVENANCE.md`.

> **최근 연도는 절단되어 있다.** 2024년 3,884건 → 2025년 423건은 출원 감소가 아니라 **출원 후
> 18개월 비공개**다. H2 시계열은 이 구간을 절단으로 명시해야 한다.

## 3. 파생 그래프 (커밋하지 않는다 — 결정적으로 재생성된다)

`data/processed/` 는 gitignore 다. `graph_v0`·`delta_v1`·`graph_v1` 은 스냅샷과 코드에서
결정적으로 재조립되므로 파일 자체를 커밋하지 않고 **재현 절차와 서명**을 기록한다.

| 그래프 | 트리플 | 만드는 법 | 게이트 |
|---|---:|---|---|
| `graph_v0` (G₀) | **105,713** (구 105,588) | `make baseline` (상류 `2839afb` 스냅샷 · 미반영 SDKB 온톨로지 전량 반영: 선행기술 ABox·상용화·RBV 편입) | L1(완화)·L2·L3 27/28 |
| `delta_v1` | 370,077 | `make merge` 1단계 — 특허 24,179건 | L1(엄격): 개념 ≥1 |
| `graph_v1` (G₁) | **924,814** | `make merge` 2단계 (+ §G1 Phase A 청구항 축 · Phase C 문제층 · baseline 재반영) | L1 통과 · **L2 HermiT consistent=True** · L3 CQ |
| `delta_v2` (소부장) | 385,577 | `make merge CORPUS=ksia-equipment` 1단계 — 특허 **12,339건** · 초록·청구항 포함 | L1(엄격): 개념 ≥1 |
| `graph_v2` (G₂ · RQ3) | **490,529** | 2단계 — G₀ 위 KSIA 소부장 188사 델타 | L1 통과 · **L2 consistent=True** · L3 CQ **28/28** |
| `graph_v2_{equipment,material,component}` (층별) | 각 층 subset | `make ksia-strata` — 층별 H1(표 5b) 전용, 같은 L1 게이트 | L1 통과 |

> **⚠ 세대 불일치 (2026-08-01).** 위 표에서 **G₀ 만 상류 `2839afb` 로 재조립됐다.** `delta_v1`·
> `graph_v1`·`delta_v2`·`graph_v2` 및 층별 subset 은 전부 **2026-07-23 산출물**이며 구 G₀(105,588)
> 위에 얹혀 있다. 세대를 맞추려면 `make merge` 를 다시 돌려야 하고, 그것은 IR 후보 코퍼스 서명을
> 바꾸므로 **§2.1 사전등록 동결이 선행한다**. 그 전까지 G₁·G₂ 값은 *구 세대 실측*으로만 인용한다.

> **G₀·G₁·G₂ 재조립 49,307→105,588 · 868,669→924,814 · 434,342→490,529 (2026-07-23 · 커밋 `3429d66`).**
> 사용자 결정으로 baseline 동결을 풀고, 벤더 스냅샷엔 있으나 `baseline.py` 적재 목록에서 빠져 있던 SDKB
> 온톨로지 3종(**선행기술 ABox** `ont:CitedPatent` 3,034 + 개념링크 · **상용화** TRL·라이선싱 · **RBV**
> VRIO·역량)을 편입했다. **H1 중립 — C₀ 20/49·CQ01=20·CQ03=29·CQ06=58·CQ10=8 불변**(선행기술은 명시
> 타입이 `ont:CitedPatent` 라 CQ01 이 안 셈) · **선행기술조사 정답지 도달성 0%→95.3%[노드]** · 델타특허
> 24,179/12,339 불변 · 통합테스트 21/21·전체 179 passed. SDKB 커밋 `d578bf3` 그대로·벤더 목록만 확장.
> **라이선스: 특허 전문 스냅샷 2종**(`sdkb-abox-patents.ttl`·`sdkb-abox-prior-art.ttl`)**은 gitignore 되어
> 신선한 클론/CI 에는 없다** — `verify_snapshot`(L0)이 이 부재를 관용하도록 손보는 것은 §2 승인 대기 미해결 항목.
>
> **G₀ 재동결 49,210 → 49,307 (2026-07-23).** 상류 SDKB `sdkb-patent.ttl` 의 **순수 TBox 선언**
> (청구항-feature·거절판단 온톨로지 · SDKB `d583b0c→d578bf3`)을 재vendor·재동결했다. **+97 = TBox
> 선언뿐** — 신규 클래스 4(`Claim`·`ClaimFeature`·`PriorArtJudgment`·`CitedPatent`) + 익명 unionOf 1 ·
> ObjectProperty +10 · DatatypeProperty +5. G₀ 에는 이 어휘의 인스턴스가 0이라 ABox·엣지 불변
> (realizesProcess 1565·concernsDevice 181·assignedTo 1053·Patent 1000 불변). **H1 네 표본집합 p
> 전부 불변**(4.77e-07·3.05e-05·1.95e-03·2.44e-04) · C₀ 20/49 불변 · 4층 게이트 통과. 청구항 분해
> ABox(Tier 1/2/3 · 11.6M)는 `VENDOR_FILES` 화이트리스트 밖의 별도 중심축 데이터셋이라 G₀ 무관.
> (과거 44,192→44,202 "+10=TBox 선언 2개" 와 동형.)
>
> **G₀ 재동결 44,192 → 44,202 (2026-07-15).** 상류 SDKB 에 `ont:claimText`·`ont:claimCount`
> (IP-R&D FTO 자기완결성 · SDKB `edb8ae4`)를 신설해 재vendor·재동결했다. **+10 = TBox 선언 2개**
> 뿐이다 — G₀ 의 SIRP 특허는 청구항1만 있어 claimText 사용 0, ABox·엣지 불변. **H1 네 표본집합
> p 전부 불변**(4.77e-07 · 3.05e-05 · 1.95e-03 · 2.44e-04) · C₀ 20/49 불변.
>
> **G₂ (RQ3 · C-2 소부장 전체 · 외적 타당도).** KSIA 소부장 **188사(장비 93·재료 50·부분품 45)**
> 특허를 수집·병합해 프레임워크 재현성을 실증한다. **H1 은 소부장 전체에서 지지된다**(네 표본집합
> 전부, 표 5-소부장): 커버 **G₀ 20 → G₂ 26/49**. **세 층 각각에서도 모두 지지**(표 5b · `make ksia-strata`):
> 장비 26/49·재료 25/49·부분품 24/49.
>
> **폭(breadth)은 26 으로 포화, 깊이(depth)는 소부장이 더한다.** 커버 단계 26 은 G₁ 과 같고(증가
> 단계 21 로 매핑 룰 도달범위에 포화 — 코퍼스 무관), 전체 커버 26 = **장비 층 커버 26**(재료 25·
> 부분품 24 는 부분집합)이라 **폭은 장비가 대고 세 층이 깊이를 쌓는다**. 증가폭 중앙 Δ 는 층 규모로
> 계단진다: 장비 354 > 재료 89 > 부분품 30, 전체 소부장 **573**(G₁ 236 의 2.4배). 잠들어 있던
> 공급사 노드가 특허·청구항으로 활성화(assignedTo 받는 조직 351→439). 청구항 전문 **161,184 트리플**
> (매핑 특허 12,337 · 청구항 보유 100%) — FTO 를 그래프만으로 실행할 수 있다(CQ27 = 144사).
>
> **expanded49 의 p 가 G₁(4.77e-07)과 다른 2.97e-05 인 것은 효과 차이가 아니다** — 증가폭에
> 동점(두 단계가 +20)이 생겨 scipy 가 정확검정→정규근사로 전환한 결과다. W=231·증가 21단계는 동일
> (장비 층만 보면 동점이 없어 exact 4.77e-07 로 재현). 방법 전환이지 신호 약화가 아니다.

## 2026-07-25T15:36:08.205752+00:00 · IR 코퍼스 조립 (PLAN-017 M1)
- 명령: `make corpus` (`python -m sdkb_paper.corpus.assemble`)
- ir_corpus_v09.parquet: 40,552 행 · sha256 `ec5ea51b626d3ff9`
- qrel_examiner.parquet: 2,416 엣지 · sha256 `10ab67f21cc1328d`
- 원천: graph_v0/v1/v2.ttl + central_axis.oxstore(sidecar 청구항 재구성)
- 반영: C2 입력 · 논문 §5–6

## 2026-07-27 · IR DOCDB family 지도 (PLAN-018 M3 · B2 · F1 주지표)
- 명령: `python -m sdkb_paper.collect.bq_family_ir` (dry-run 10.26 GB · 실행 ~$0.06 · 무료 티어)
- 원천: BigQuery `patents-public-data.patents.publications` (공개번호+출원번호 정규화 조인)
- ir_family_map.parquet: 40,552 행(코퍼스 1:1) · DOCDB 95.8% · fallback-self 4.2% · 고유 family 39,899
- 입력 코퍼스 sha256 `ec5ea51b626d3ff9` (불변) · 산출은 raw(비커밋)
- 프로파일: `data/profiles/ir_family_map.md`
- 반영: F1 family-level Recall@100 성립 (B0 = 0.2905 · 문서수준 0.2800). C2 주지표 입력.

## 2026-07-27 · 시점 분할 B8 + F9 동결·봉인 (PLAN-018 M3)
- 명령: `python -m sdkb_paper.corpus.split`
- F9 동결(config): 경계 train/dev=2016-11-21 · dev/test=2021-07-21 · 60/20/20 family-disjoint
- split.parquet: 600/200/200 · 고유 family 959 · 체크섬(경계표류 감지) 통과
- qrel_test_sealed.parquet: test 479 엣지/198 질의 봉인 · 개발용 visible 1,937 엣지
- 산출 raw(비커밋) · 동결 증거 = config 커밋 해시 · 프로파일 data/profiles/ir_split.md
- 반영: F9 사전등록(CLAUDE 규칙 #3·#4) · B0 dev family Recall@100=0.2942

## 2026-07-27 · Dense·Hybrid·bootstrap — B0–B3 텍스트 기준선 (PLAN-018 M3)
- 명령: `make dense && make hybrid` + analysis.{metrics,bootstrap}
- Titan Embed v2(amazon.titan-embed-text-v2:0·1024차원) 문서 40,491+질의 1,000 임베딩 · ~$0.5 · 캐시
- run: bm25_b0_claim·dense_b2_claim·hybrid_b3_rrf (gitignore·재생성) · FAISS flat
- dev family R@100: B0=0.2942·B2=0.2459·B3=0.3212 · 부트스트랩 B3−B0 CI[−0.0022,+0.0565]
- 프로파일 data/profiles/ir_baselines_b0b3.md · 반영: C2 무대(강한 텍스트 기준선 B3 확립)

## 2026-07-28 · 거절근거 법조 라벨 파생 스냅샷 (§5.2·§6.4 하위집단)
- 명령: `python -m sdkb_paper.ontology.vendor --derive-rejection` (TTL 스냅샷 재동결 없음 · G₀ 서명 불변)
- 원천: `~/Dev/sdkb/data/patents/rejected_patents_meta.parquet` 의 `rejection_legal_bases`
  (`"§1×n|§2×m"` = 법조×해당 청구항 수). **원문 열 0개** — 식별자+법조만 추출해 커밋 가능(CLAUDE §1-5).
- 산출: `data/external/sdkb/rejection_basis.csv` (1,000행 · sha256 `651f03010228…` · PROVENANCE 갱신)
- 실측: 진보성(제29조 제2항) 400 · 신규성(제1항) 14 · **신규성 단독 0** · 라벨 없음 600
- **상류 결함 기록:** `sdkb-abox-patents.ttl` 은 이 문자열을 단일 `ont:Rejection_Inventiveness` 로
  접어 **신규성 축을 잃는다**(TTL 신규성 0건). 우회가 아니라 통로다 — 상류 수정은 별건.
- 용도: 하위집단 분해 **전용**(순위 함수 입력 아님 · oracle-free 주모드 불변)
- 반영: §6.4 거절근거 행 · §7.7 "신규성 vs 진보성" 을 자원 부재로 **후속 연구 질문으로 강등**

## 2026-07-28 · §6.2·§6.4 표·그림 전량 산출 (N1·N2·N3·N7·N10)
- 명령: `make tables SPLIT=dev && make tables SPLIT=test && make figures`
- 새 검색 없음 — 동결 run(B0·B2·B3) 재평가 + 동결 설정 재랭크(P0★·P1). 재선택 없음.
- 신규 지표: nDCG@20(**이진 이득** — qrel 전량 등급 1) · bpref(**retrieved-as-judged** 관례) ·
  R@50/500 · Success@100 · MRR@500 · 단계별 지연(비결정적 측정)
- F11 어휘중첩 동결: dev Q1 = **0.0079**(char 3-gram Jaccard·mean) → `data/processed/ir/overlap_threshold.json`
  (test 27 low / 171 high · 임계는 test 분포로 재산출하지 않음)
- 산출: `paper/tables/ir_{performance,subgroup,increment}_{dev,test}.md` ·
  `paper/figures/ir_{increment,metrics,ablation,subgroup}.svg` · `data/processed/ir/ir_*.csv`(viz 입력)
- **가설에 불리한 실측 3건**: ① nDCG@20 미개선(P1 −0.0176 p=0.227 · P0★ −0.0395 p=0.029 유의 악화)
  ② low-overlap 집단 Δ−0.0586 < high +0.0711 (§7.3 반증) ③ 교차언어 집단 이득 유의 미달(+0.0140 p=0.518)
- 반영: 원고 §5.1·§5.3·§6.2·§6.3·§6.4·§7.3·§7.5·§7.6·§7.7·§8.5·§9.1

## 2026-07-31 · B2′ 강한 밀집 기준선 모델 동결 (PLAN-031 §5 · 개봉 전)
- 명령: `huggingface_hub.snapshot_download("BAAI/bge-m3", revision="5617a9f6…")` + 로컬 sha256 산출
- **모델: `BAAI/bge-m3`** · **revision(commit): `5617a9f61b028005a4858fdac845db406aefb181`**
  (HF lastModified 2024-07-03) — 이후 **변경하지 않는다. 바꾸면 재선택이다**(PLAN-031 §5·§8)
- 사양(config 실측): xlm-roberta · hidden 1024 · **max_seq_length 8192** · vocab 250,002 · float32
  → 질의 중앙값 527자·문서 2,255자를 **절단 없이** 수용(선정 기준 "한국어·장문 대응 공개 인코더")
- 풀링: CLS(`1_Pooling/config.json` · mean 아님) — 임베딩 차원 1024
- 가중치 sha256(로컬 재계산 = HF LFS 메타와 일치):
  - `pytorch_model.bin` 2,271,145,830 B · `b5e0ce3470abf5ef3831aa1bd5553b486803e83251590ab7ff35a117cf6aad38`
  - `tokenizer.json` 17,098,108 B · `21106b6d7dab2952c1d496fb21d5dc9db75c28ed361a05f5020bbba27810dd08`
  - `sentencepiece.bpe.model` 5,069,051 B · `cfc8146abe2a0488e9e2a0c56de7952f7c11ab059eca145a0a727afce0db2865`
  - `colbert_linear.pt` 2,100,674 B · `19bfbae397c2b7524158c919d0e9b19393c5639d098f0a66932c91ed8f5f9abb`
  - `sparse_linear.pt` 3,516 B · `45c93804d2142b8f6d7ec6914ae23a1eee9c6a1d27d83d908a20d2afb3595ad9`
  - `config.json` 687 B · `26159e7ad065073448460117eb24b7a4572f6f4e78eadff65dc0a11c052449fa`
  - `sentence_bert_config.json` 54 B · `eb9b44b13c0f52a3b3685c3b1cbdea1ba8b04bea123b98f61610048940776eb1`
  - `1_Pooling/config.json` 191 B · `e54c164a07274f2eb45bb724f54a79d1efcc90c41573887cd9a29aeee0597352`
- 실행 환경: 로컬 GPU · torch 2.13.0+cu130 · `torch.cuda.is_available()=True`
- 가중치는 **커밋하지 않는다**(HF 캐시 · 위 revision+sha256 이 재현 좌표)
- **아직 하지 않은 것:** 추론 실행·임베딩 산출. `sentence-transformers` 미설치이며
  의존성 추가는 별도 승인 대상(CLAUDE §1-10). 이 항목은 **모델 동결 기록일 뿐 B2′ 실행이 아니다**
- 반영: PLAN-031 §5 `[동결 시 기입: revision · sha256]` 해소 (C2 재확증 기준선)

## 2026-07-31 · PLAN-032 2단계 분석 — KIPRIS 검색 API 프로브 (수집 아님 · 저장물 없음)
- 명령: scratchpad 프로브 3본 (`probe_sort.py` · `probe_range.py` · `probe_pop.py`)
- 오퍼레이션: `getAdvancedSearch` (`plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchSevice`)
- **검색 호출 81콜** (25+25+9+22) — PLAN-032 §1 호출 회계상 **파일럿 500콜(서지상세)과 별도 계정**.
  서지상세(`getBibliographyDetailInfoSearch`) 호출 **0**. `quota_hit` 없음(전 호출 `resultCode=00`)
- 확인 사항(상세 PLAN-032 §2.5): ① `sortSpec=AD&descSort=false` **서버측 출원일 오름차순 지원** ·
  동일 요청 2회 순서 동일 · 페이지 1↔2 중복 0 ② `applicationDate=20050101~20251231` **물결 표기만
  지원**(파이프·연도만 = `INVALID_REQUEST_PARAMETER_ERROR`) ③ `numOfRows` 상한 **500**
  ④ 검색 응답이 `ipcNumber`(주분류 포함)·`registerStatus`·`astrtCont`를 이미 실어 보냄
  ⑤ 2005–2025 창 21 IPC 모집단 합 **737,834**(중복 포함) ⑥ `registerStatus` 결측률 = **0/100**
  (H10B·2005–2025) — §8.1 전제("자주 빈다")가 이 창에서는 성립하지 않음
- **원문 데이터 미저장**: 응답은 메모리 내 집계만 하고 raw 를 저장·커밋하지 않았다(CLAUDE §1-5).
  scratchpad 산출물은 집계 JSON뿐
- 반영: PLAN-032 §2.5·§2.6 (2단계 분석 · C2 재확증 전제)

## 2026-08-01 · PLAN-032 5단계 — B층 파일럿 수집 실행 (**목표 200건 도달 · 개봉 안 함**)
- 명령: `python -m sdkb_paper.collect.b_layer` (기본 캡 target=200 · detail 500 · search 300 · audit 50)
- 오퍼레이션: `getAdvancedSearch` · `getBibliographyDetailInfoSearch`
  (`plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchSevice`)
- 검색식: `ipcNumber={21종 각각}` · `applicationDate=20050101~20251231` · `sortSpec=AD` ·
  `descSort=false` · `numOfRows=500` · `patent=true&utility=false`
- **호출 회계(4계정 분리 · §1 동결)**: search **25** · detail **335** · audit **50** · notice **0** ·
  `quota_hit=false` (전 호출 `resultCode=00` — 할당초과 실물은 이번에도 관측되지 않음)
- 정지 사유: `target_reached` (detail 캡 500 중 335 소비 · search 캡 300 중 25 소비)
- 건수: 스크리닝 원장 **4,331행**(free 3,946 · detail 335 · audit 50) · 고유 출원번호 **4,281** ·
  **채택 200건**(전건 `register_status=거절` · claim1 결측 0) · 봉인 qrel **390행 / 질의 200**
- 비율(Wilson 95 % CI · 결정 B): `r_free` 0.0783 [0.0706, 0.0867] (335/4,281) ·
  `r_family` 1.0000 [0.9887, 1.0000] (335/335) · **`r` 0.5970 [0.5437, 0.6482] (200/335)**
- 감사(결정 E · `r` 분모 제외): `status_not_rejected` 배제분 앞에서부터 50건 전건 확인 →
  **위음성 0/50 · 0.0000 [0.0000, 0.0713]** — "검색 `registerStatus` = 포함 1" 가정이 지지됨
- 배제 1·2 확인: 채택 200건 ∩ A층 출원번호 1,000 = **0** · ∩ A층 패밀리 959 = **0**
- 채택분 출원일 범위 **20050103 ~ 20050228**(전건 2005년 1–2월).
  PLAN-031 §3의 "출원일 오름차순 앞에서부터"의 직접 귀결이다 — A층(1997–2025)과 시기 분포가
  다르므로 **A층 test 결과와 직접 비교하지 않는다**(프로파일 §3.3 경고와 동일)
- 파일 sha256:
  - `data/processed/ir/b_layer/screening_ledger.jsonl` · `62a564c5504ec05bdaa318259979b9bb701c3232c5879215f26d848656fc8238`
  - `data/processed/ir/b_layer/accepted.parquet` · `7b355b9b13716f8a05dac4e43549227966493bbf7b84fd0d93621da69a5ff5e1`
  - `data/processed/ir/qrel_b_sealed.parquet` **🔒봉인** · `f0d423268b4f3554ccd05d1bf511daab70d5f5f4c4c5c00e77a79e3e4a69206a`
  - `data/raw/kipris/b_layer_cache.sqlite` (410 응답 · A층 캐시와 분리) · `2953ecbf14e55272f9da6fdac024f3c095ff24e3042b1950c8f2a87ebc8603f7`
- 봉인 규율: 파일럿은 `qrel_b_sealed.parquet` 을 **쓰기만** 했다. 위 행수·질의수는 파일 형태
  (shape)에서 읽은 집계이고 **인용 식별자는 열지 않았다**
- 반영: PLAN-032 §1 성공기준 ①②③④⑤ · §5.7 (C2 재확증 전제 · B층 질의 200건 확보)

## 2026-08-01 · KR DOCDB 패밀리 지도 1회 적재 (BigQuery · PLAN-032 결정 D의 집행 정정)
- 명령: `sdkb_paper.collect.b_layer.family.load_kr_family_map()` (`KR_MAP_SQL`)
- dry-run 실측: **스캔 5.22 GB · $0.0326** — 스캔량은 `IN UNNEST(@apps)` 파라미터 개수와 **무관**
  (1·100·1,000·10,000건 전부 5.22 GB). 후보 1건마다 조회하면 같은 5.22 GB 를 수백 번 다시 낸다
- 산출: `data/interim/kr_family_map.parquet` · **4,878,954행**(KR 출원번호 11자리 → family_id) ·
  76.6 MB · sha256 `4b660c5eac2b303ad300aa3844ba09be7c7007430f8ef84e2246ddee081185af`
- 규칙 불변 검증: A층 1,000건을 이 지도로 다시 풀어 `split.parquet` 과 대조 →
  **일치 998 · 불일치 0 · 미조인 2**(= §5.0 이 기록한 fallback-self 2건과 동일 건)
- 반영: PLAN-032 §5.1 ③ "배치 조회" 의 집행. `resolve_families()`·`build_family_map()` 은 불변

## 2026-08-01 · B층 사전등록 개정 §3 표집 창 + 2005년 산출물 은퇴 (PLAN-031 §9 · **재수집 착수 전**)
- 승인: 2026-08-01 사용자 "개정안대로 진행" (3안 중 **질의 재표집** 선택)
- 개정 내용: `B_LAYER_DATE_FROM` **20050101 → 20180101** · `B_LAYER_DATE_TO` **20251231 → 20201231**.
  **그 외는 전부 불변** — IPC 21종 · 포함기준 5 · 목표 200 · 호출 캡(search 300 / detail 500 /
  audit 50) · 평가 프로토콜(§4) · 시스템 정의(§5 · B2′ `BAAI/bge-m3` revision 고정)
- 사유(실측): 구 창에서 채택 200건이 전부 2005-01~02 출원이 되어, 후보 코퍼스 40,552건 중
  **공개일 < 질의 출원일** 을 만족하는 문서가 **2건**뿐이었다(공개일 결측 4,492 · 대부분 2005년 이전
  출원분). 대조로 A층 test 질의(출원 2021–2025)는 마스크 후 **19,039~23,000건**을 마주한다.
  새 창의 마스크 후 후보는 질의 2018년 **13,801** · 2020년 **17,209**(A층 test 의 60–75 %)
- 은퇴 처리: 2005년 창 산출물 4개를 `data/processed/ir/b_layer_retired_2005/` 로 이동(삭제 아님).
  **폐기 시점 sha256 이 파일럿 기록과 전건 동일** = 파일럿 이후 한 번도 열리거나 바뀌지 않았다는 증명:
  - `qrel_b_sealed.parquet` **🔒봉인 미개봉** · `f0d423268b4f3554ccd05d1bf511daab70d5f5f4c4c5c00e77a79e3e4a69206a`
  - `accepted.parquet` · `7b355b9b13716f8a05dac4e43549227966493bbf7b84fd0d93621da69a5ff5e1`
  - `screening_ledger.jsonl` · `62a564c5504ec05bdaa318259979b9bb701c3232c5879215f26d848656fc8238`
  - `call_budget.json` · `bd871ae6c04947369316184d24a78c4e0c57fb1e5b22af8cbdeae285faaddf90`
- 유지: `data/raw/kipris/b_layer_cache.sqlite`(410 응답 · 원 API 증거이므로 지우지 않는다) ·
  `data/interim/kr_family_map.parquet`(KR 전량이라 창과 무관하게 재사용)
- 판정 기록 보존: 파일럿의 `r` 0.5970 · `r_free` 0.0783 · `r_family` 1.0000 · 감사 위음성 0/50 은
  **2005년 표본에서의 관측**으로 남는다. 새 창의 `r` 는 다시 잰다 — 연도가 다르면 거절률이 다르다
- 반영: PLAN-031 §9(동결) · `src/sdkb_paper/config.py` · STATUS §2

## 2026-08-01 · B층 재수집 (개정 창 2018–2020 · PLAN-031 §10) — **200건 도달 · 봉인 미개봉**
- 명령: `python -m sdkb_paper.collect.b_layer` (개정 커밋 `0de9ea8` 이후)
- 정지 사유: `target_reached` · 호출 search 22 · detail 210 · audit 50 · `quota_hit=false`
- 건수: 스크리닝 원장 **2,623행** · 고유 출원번호 **2,573** · **채택 200건** ·
  봉인 qrel **538행 / 질의 200**
- 비율: `r` **0.9524** [0.9146, 0.9739] (200/210) · `r_free` 0.0816 [0.0717, 0.0928] (210/2,573) ·
  `r_family` 1.0000 [0.9820, 1.0000] (210/210) · 감사 위음성 **0/50**
- 채택분 출원일 **20180102 ~ 20180216** · 주분류 H10P 58 · B23K 21 · H10K 20 · C23C 18
- **건초더미 복구 확인**: 마스크(공개일 < 질의 출원일) 후 후보 **13,801 ~ 14,053**
  (구 창에서는 **2건**이었다 — 개정의 목적이 달성됨)
- **A층 배제 규칙 작동 확인**: `dup_application_a_layer` **5건**(구 창에서는 0이라 미검증이었다)
- 🛑 **§9.4 도달성 검사 실패 — 개봉 전 차단**: 고유 인용 식별자 514 중 후보 코퍼스 적중 **6**
  (도달성 0.0117 · A층 대조 0.953). 원인 둘 — ① KR 인용 235건은 **공개번호**인데 코퍼스 KR
  37,518건은 **출원번호** 키(측정 불가) ② 외국 문헌 **268건(52 %)** 이 코퍼스에 부재.
  **KR 전량 해소를 가정해도 상한 0.457.** 후보 코퍼스 증분 설계(§10.4) 승인 전까지 개봉 금지
- 봉인 규율: `qrel_b_sealed.parquet` 은 **쓰기** 후 §9.4 ①이 허용한 **집계 통계만** 읽었다 —
  질의별 정답·인용 목록은 산출하지 않았고 어떤 튜닝에도 쓰이지 않았다
- 파일 sha256:
  - `data/processed/ir/b_layer/screening_ledger.jsonl` · `eeb414c542105e6d18a3f82efc641585b2d9b49304c11481e7045c51b6efcb03`
  - `data/processed/ir/b_layer/accepted.parquet` · `b81257e95f5324e248cdaca83d38d05c2432d57339a5ad30f6b72d79cb41b26d`
  - `data/processed/ir/qrel_b_sealed.parquet` **🔒봉인** · `127a138f1c1651676ea81b9ecf50aa53e0172ca4ee7ff0c5b8f26e9d171db4c3`
  - `data/raw/kipris/b_layer_cache.sqlite` · `f0e1b7ebc81251a216b7adb0ec107db438ce4ee771693b41351ddfb00a8201fd`
- 반영: PLAN-031 §9(개정) 집행 · §10(실행 기록) · STATUS §2

## 2026-08-01T08:54:37.324369+00:00 · IR 코퍼스 조립 (PLAN-017 M1)
- 명령: `make corpus` (`python -m sdkb_paper.corpus.assemble`)
- ir_corpus_v09.parquet: 40,552 행 · sha256 `ec5ea51b626d3ff9`
- qrel_examiner.parquet: 2,416 엣지 · sha256 `10ab67f21cc1328d`
- 원천: graph_v0/v1/v2.ttl + central_axis.oxstore(sidecar 청구항 재구성)
- 반영: C2 입력 · 논문 §5–6

## 2026-08-01 · PROVENANCE 메타데이터 복원 (license_restricted 2건) — **파일 해시 무변경**
- 조작: `data/external/sdkb/PROVENANCE.json` 의 `sdkb-abox-patents.ttl`·`sdkb-abox-prior-art.ttl`
  항목에 `license_restricted: true` 를 되돌림. **TTL 은 한 바이트도 건드리지 않았다** —
  파일별 sha256 17종 전량 불변 · 스냅샷 서명 `b98ad787d1fe` 불변 · `--verify` 17/17 통과
- 사유: 이 플래그는 04ab68b 에서 **손으로** 들어갔고 `vendor()` 는 그것을 쓸 줄 몰랐다.
  그래서 다음 `make vendor`(fa16f2f)가 조용히 지웠고, 특허 전문 TTL 2종이 gitignore 되는
  신선한 클론·CI 에서 L0 가 다시 깨졌다(논문 §7.2 "상류 없이 재현 가능" 주장이 걸린 지점)
- 재발 방지: `vendor.LICENSE_RESTRICTED` 상수를 신설해 **코드가** 플래그를 박는다 +
  회귀 테스트 `test_license_restricted_flag_comes_from_code_not_from_hand`
- 사용자 승인: 2026-08-01 (선택지 "메타데이터만 직접 복원")

## 2026-08-01 · G₀ 관측 서명 세대 갱신 (상류 2839afb 스냅샷)
- 트리플 105,588 → **105,713**(+125) · Process 11 → **12**(신규 `data:process/plasma_processing`)
- 공정 단계 49 → **50** · 커버 **20 불변** · 공백 29 → **30** · 매핑 규칙 83 → **84** ·
  CQ06 58 → **59**
- 처리: 구 값을 덮어쓰지 않고 `tests/test_baseline_integration.py::SNAPSHOT_OBSERVATIONS` 에
  `pre_remediation` / `current` 두 세대로 분리 기록(CLAUDE.md §1-3 소급 수정 금지 · §2.1)
- **D-19 확증**: 개념층은 이만큼 자랐는데 `ir_corpus_v09.parquet` sha256 은 `ec5ea51b626d3ff9`
  로 바이트 단위 동일했다 — 자원은 움직였고 검색 파이프라인만 읽지 않았다
- **처리 완료(2026-08-01)**: 정본 서명 체인을 G₀=**105,713** 으로 갱신 — CANONICAL-INDEX §0·§1 ·
  GLOSSARY · STATUS · DATASET-CARD(§②·§③·계보도) · MANIFEST §3 · SPEC-006/007 세대 헤더 ·
  CLAUDE.md(§0 H2 경계 · §5 G1/G2). 구 값 `105,588` 은 `check_signatures.py` 의
  `HISTORICAL_SIGNATURES` 로 내렸고, **원고 v0.9 의 105,588 인용 4곳은 수치를 바꾸지 않고**
  `<!-- sig-history -->` 로 예외 처리했다 — v0.9 §6 의 모든 결과가 그 세대 위에서 측정됐으므로
  새 값으로 갈아끼우면 실제로 돌린 자원과 달라진다(§1-1·§1-3)
- **함께 확인된 것 두 가지**
  - **T-Box 가 연구 최초로 바뀌었다**: `owl:ObjectProperty` 97 → **98**(`skos:broader` 선언) ·
    `skos:broader` 11 → **18** · 클래스 103·DatatypeProperty 81 불변(rdflib 실측). CLAUDE.md §0
    델타유형표의 **유형 ① = H2 자격 있음**. 단 D-19 로 하류가 읽지 않아 **여전히 미검정**
  - **세대 불일치**: `graph_v1/v2.ttl` 은 2026-07-23 산출물이라 구 G₀(105,588) 위에 있다.
    `make merge` 재실행은 IR 후보 코퍼스 서명을 바꾸므로 **§2.1 사전등록 동결이 선행한다**

## 2026-08-01T12:29:15.456393+00:00 · IR 코퍼스 조립 (PLAN-017 M1)
- 명령: `make corpus` (`python -m sdkb_paper.corpus.assemble`)
- ir_corpus_v09.parquet: 40,552 행 · sha256 `ec5ea51b626d3ff9`
- qrel_examiner.parquet: 2,416 엣지 · sha256 `10ab67f21cc1328d`
- 원천: graph_v0/v1/v2.ttl + central_axis.oxstore(sidecar 청구항 재구성) + 개념 사전 없음(적용기 무작동)
- 반영: C2 입력 · 논문 §5–6

## 2026-08-01T14:14:23.312846+00:00 · IR 코퍼스 조립 (PLAN-017 M1)
- 명령: `make corpus` (`python -m sdkb_paper.corpus.assemble`)
- ir_corpus_v09.parquet: 40,552 행 · sha256 `ec5ea51b626d3ff9`
- qrel_examiner.parquet: 2,416 엣지 · sha256 `10ab67f21cc1328d`
- 원천: graph_v0/v1/v2.ttl + central_axis.oxstore(sidecar 청구항 재구성) + 개념 사전 없음(적용기 무작동)
- 반영: C2 입력 · 논문 §5–6

## 2026-08-01T14:28:38.348101+00:00 · IR 코퍼스 조립 (PLAN-017 M1)
- 명령: `make corpus` (`python -m sdkb_paper.corpus.assemble`)
- ir_corpus_v09.parquet: 40,552 행 · sha256 `9fec15c6c325413e`
- qrel_examiner.parquet: 2,416 엣지 · sha256 `10ab67f21cc1328d`
- 원천: graph_v0/v1/v2.ttl + central_axis.oxstore(sidecar 청구항 재구성) + concept_mapping.json(적용기 링크 128,875건)
- 반영: C2 입력 · 논문 §5–6
