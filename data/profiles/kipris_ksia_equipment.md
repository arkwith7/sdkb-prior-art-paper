# 프로파일 — KIPRIS KSIA 소부장 188사 특허 (RQ3 · PLAN-014 C-2 · G₂ · 장비·재료·부분품)
> 이 파일은 `python -m sdkb_paper.preprocess.profile` 이 생성한다. 손으로 고치지 않는다.

## 1. 구조 (structure)

| 컬럼 | 의미 | dtype | 원천 |
|---|---|---|---|
| application_number | 출원번호 (하이픈 제거, 키) | str | KIPRIS applicationNumber |
| applicant_name | 출원인 명칭 | str | KIPRIS applicantName |
| application_date | 출원일 — H2 시계열의 시간축 | datetime64[us] | KIPRIS applicationDate |
| invention_title | 발명의 명칭 — 텍스트 매칭(HBM·EUV) 입력 | str | KIPRIS inventionTitle |
| ipc_number | IPC 코드 원문 ('|' 구분) | str | KIPRIS ipcNumber |
| abstract | 요약 — 텍스트 매칭 입력 | str | KIPRIS astrtCont |
| open_date | 공개일 (출원일과 혼동 금지) | str | KIPRIS openDate |
| register_date | 등록일 (결측 = 미등록) | str | KIPRIS registerDate |
| register_status | 등록 상태 (공개/등록/거절 등) | str | KIPRIS registerStatus |
| query_applicant | 이 행을 가져온 질의의 출원인 | str | 수집기 부여 |
| query_ipc | 이 행을 가져온 질의의 IPC 클래스 | str | 수집기 부여 |
| ipc_codes | IPC 코드 리스트 — 룰 매핑 입력 | object | ipc_number 파생 |
| matched_slug | — | str | — |
| n_process | 매핑된 공정 개념 수 | int64 | 룰 매핑 파생 |
| n_device | 매핑된 소자 개념 수 | int64 | 룰 매핑 파생 |

키: `application_number` (하이픈 제거 후 고유). **CPC 는 KIPRIS 고급검색 응답에 없다 — IPC 만 수집된다.**

## 2. 형태 (shape)

| 단계 | 건수 | 설명 |
|---|---|---|
| 원시 수집 행 | 42,185 | IPC 클래스 × 출원인 질의의 합 (중복 포함) |
| 정규화 후 | 42,185 | 출원번호·출원일 결측 제거 |
| 출원인 정확일치 후 | 33,858 | 계열사·타사 제외 (부분일치 부작용 제거) |
| 출원번호 중복 제거 후 | 21,950 | 한 특허가 여러 IPC 클래스에 잡힌다 |
| G₀ 겹침 제외 | −63 | SIRP 거절특허로 이미 G₀ 에 있음 (H1 오염 방지) |
| **정제 후 특허** | **21,887** | G₁ 병합 대상 |
| └ 룰 매핑됨 | 12,358 (56.5%) | 개념 ≥1 — L1(델타) 통과 조건 |
| └ 미매핑 | 9,529 | 룰의 한계로 탈락. 정직하게 보고한다 |

결측률 (델타 21,887건 기준). **빈 문자열도 결측으로 센다** — KIPRIS 는 미등록 특허의 `registerDate` 를 빈 태그로 준다.

| 컬럼 | 결측/빈값 |
|---|---|
| application_date | 0.0% |
| invention_title | 0.0% |
| abstract | 0.0% |
| register_date | 35.5% |
| register_status | 0.0% |

## 3. 기술통계 (descriptive)

### 출원인별

| KSIA 회원사 (상위 20) | 델타 건수 | G₀ 겹침(제외됨) |
|---|---|---|
| 세메스㈜ (`semes`) | 6,623 | 12 |
| 동우화인켐㈜ (`dongwoo_fine_chem`) | 2,598 | 2 |
| 주식회사 원익아이피에스 (`wonik_ips_co`) | 1,458 | 4 |
| ㈜케이씨텍 (`kctech_co_ltd`) | 1,074 | 0 |
| 주성엔지니어링㈜ (`jusung_engineering`) | 796 | 5 |
| ㈜에스에프에이 (`sfa_engineering_corp`) | 603 | 0 |
| ㈜케이씨 (`kc_co_ltd`) | 583 | 0 |
| ㈜테스 (`tes_co`) | 464 | 1 |
| ㈜동진쎄미켐 (`dongjin_semichem_co_ltd`) | 436 | 0 |
| 솔브레인㈜ (`soulbrain`) | 362 | 12 |
| ㈜에스앤에스텍 (`s_stech`) | 268 | 1 |
| ㈜탑엔지니어링 (`top_engineering_co_ltd`) | 242 | 0 |
| 한미반도체 (`hanmi_semiconductor`) | 238 | 0 |
| ㈜제우스 (`zeus_co_ltd`) | 223 | 0 |
| ㈜테크윙 (`techwing_inc`) | 221 | 0 |
| 피에스케이홀딩스㈜ (`psk_holdings`) | 209 | 1 |
| ㈜이엔에프테크놀로지 (`enf_technology_co_ltd`) | 197 | 0 |
| 한화세미텍 주식회사 (`hanwha_semitech`) | 190 | 5 |
| 주식회사 저스템 (`justem`) | 177 | 0 |
| 에스케이엔펄스 주식회사 (`sk_enpulse`) | 173 | 1 |

### 출원연도 (범위 2010–2025)

| 연도 | 건수 | 비고 |
|---|---|---|
| 2010 | 975 |  |
| 2011 | 1,101 |  |
| 2012 | 1,144 |  |
| 2013 | 1,273 |  |
| 2014 | 1,347 |  |
| 2015 | 1,347 |  |
| 2016 | 1,337 |  |
| 2017 | 1,273 |  |
| 2018 | 1,406 |  |
| 2019 | 1,603 |  |
| 2020 | 1,574 |  |
| 2021 | 1,699 |  |
| 2022 | 1,938 |  |
| 2023 | 1,775 |  |
| 2024 | 1,766 |  |
| 2025 | 329 | ⚠ 미공개분 절단 추정 |

> **최근 연도는 절단(truncation)되어 있다.** 특허는 출원 후 18개월이 지나야 공개되므로, 최근 2년의 출원 건수는 아직 다 드러나지 않았다. **감소가 아니라 미공개다.** H2 의 시계열은 이 구간을 추세 판단에서 제외하거나 절단을 명시해야 한다 (§4.4·§4.5).

### IPC 클래스 상위 (질의 클래스 기준, 중복 계수)

| IPC 클래스 | 건수 |
|---|---|
| H10P | 9,781 |
| G03F | 2,635 |
| C23C | 2,155 |
| H01J | 1,696 |
| C09K | 1,090 |
| G01N | 960 |
| B24B | 691 |
| B08B | 573 |
| C09G | 420 |
| G01B | 388 |

### 개념 매핑

| 축 | 건수 |
|---|---|
| 공정 개념 ≥1 | 12,295 |
| 소자 개념 ≥1 | 188 |
| 둘 다 없음 (미매핑) | 9,529 |

## 4. 사용 목적 (purpose)

| 컬럼 | 논문에서 쓰이는 곳 |
|---|---|
| `application_date` | H2 시계열의 시간축 (§4.4). 공개일이 아니라 **출원일**이다 |
| `ipc_codes` | 룰 매핑 → `realizesProcess`/`concernsDevice` 트리플 (§3.3) |
| `invention_title`·`abstract` | 텍스트 매칭 경로 — **HBM·EUV/DUV 는 IPC 로 안 갈린다** (§3.3) |
| `applicant_name` | §4.5 출원인별 강건성 재검정 |
| `application_number` | G₀ 중복 제거의 키. 특허 IRI 생성 |
| `register_date`·`register_status` | **이번 검정에는 쓰지 않는다.** 등록 여부는 H1·H2 의 관측 단위가 아니다. 후속 연구(등록/거절 대비)를 위해 남긴다 |
| `query_applicant`·`query_ipc` | 출처 추적 — 어느 질의가 이 행을 가져왔는가 |
