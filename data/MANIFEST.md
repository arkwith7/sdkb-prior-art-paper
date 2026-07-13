# 데이터 매니페스트

raw 데이터는 git 에 커밋하지 않는다. 모든 수집은 아래 표에 기록해 재현 가능하게 유지한다.

## 1. 근간 온톨로지 스냅샷 (baseline)

이 논문의 baseline 은 SDKB(semiconductor-knowledge-base)를 **특정 커밋에 얼려서** 가져온
`data/external/sdkb/` 스냅샷이다. 살아있는 워킹트리를 참조하지 않는다 — baseline 이 움직이면
H1(보강 전/후 커버리지 비교)이 재현되지 않기 때문이다.

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
| 2026-07-12 | 〃 | `ad7fe3d2ecc6` | 〃 + **SemiKong Table 7 공정 어휘 복원**(그룹 1·9·10) + 소자 3개 | 26,973 트리플 | `graph_v0.ttl` |

**G₀ 정의 변경 (2026-07-12).** 이전 스냅샷은 SIRP 특허 ABox 를 의도적으로 제외해 baseline 을
특허 0건으로 두었다. 그러면 모든 공정 단계에서 C₀(s)=0 이 되어 **H1 이 기각될 수 없는 자명한
가설**이 된다. G₀ 는 "현행 SDKB"여야 한다. 새 baseline 의 서명:

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

**재현 절차**: `make collect && make profile && make merge` (응답은 `raw/kipris/kipris_cache.sqlite`
에 캐시되므로 재실행해도 API 를 다시 때리지 않는다).

### 2-1. CPC 분류 (BigQuery `patents-public-data`) — H2 의 대조군 (PLAN-007)

| 일시 | 소스 | 쿼리 | 건수 | 저장 파일 | 쓰이는 곳 |
|---|---|---|---:|---|---|
| 2026-07-13 | BQ `patents.publications` (현재 스냅샷) | KR 출원 34,521건의 `cpc.code` | 434,888행 · 출원 **33,266 / 34,521 (96.4%)** | `raw/bigquery/cpc_map.parquet` (gitignore) | H2 경로 B |
| 2026-07-13 | BQ `patents.publications_{201710,201903,202004,202101,202204,202304}` | 같은 출원의 **동결 스냅샷별** CPC | 스냅샷 6개 | `raw/bigquery/cpc_vintage.parquet` (gitignore) | H2 경로 C · C′ |

**재현 절차**: `make cpc && make cpc-vintage` (GCP 서비스계정 필요 —
`GOOGLE_APPLICATION_CREDENTIALS`). 스캔량 ≈ 16.5 GB + 6×16 GB (무료 한도 1 TB/월 내).

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
| `graph_v0` (G₀) | 26,973 | `make baseline` | L1(완화)·L2·L3 |
| `delta_v1` | 370,077 | `make merge` 1단계 — 특허 24,179건 | L1(엄격): 개념 ≥1 |
| `graph_v1` (G₁) | **396,501** | `make merge` 2단계 | L1 통과 · **L2 HermiT consistent=True** · L3 CQ 8/8 |
