# 프로파일 — KIPRIS 삼성전자·SK하이닉스 특허 (PLAN-002)
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
| n_process | 매핑된 공정 개념 수 | int64 | 룰 매핑 파생 |
| n_device | 매핑된 소자 개념 수 | int64 | 룰 매핑 파생 |

키: `application_number` (하이픈 제거 후 고유). **CPC 는 KIPRIS 고급검색 응답에 없다 — IPC 만 수집된다.**

## 2. 형태 (shape)

| 단계 | 건수 | 설명 |
|---|---|---|
| 원시 수집 행 | 50,514 | IPC 클래스 × 출원인 질의의 합 (중복 포함) |
| 정규화 후 | 50,514 | 출원번호·출원일 결측 제거 |
| 출원인 정확일치 후 | 47,500 | 계열사·타사 제외 (부분일치 부작용 제거) |
| 출원번호 중복 제거 후 | 34,608 | 한 특허가 여러 IPC 클래스에 잡힌다 |
| G₀ 겹침 제외 | −87 | SIRP 거절특허로 이미 G₀ 에 있음 (H1 오염 방지) |
| **델타 후보** | **34,521** | 병합 대상 |
| └ 룰 매핑됨 | 24,053 (69.7%) | 개념 ≥1 — L1(델타) 통과 조건 |
| └ 미매핑 | 10,468 | 룰의 한계로 탈락. 정직하게 보고한다 |

결측률 (델타 34,521건 기준). **빈 문자열도 결측으로 센다** — KIPRIS 는 미등록 특허의 `registerDate` 를 빈 태그로 준다.

| 컬럼 | 결측/빈값 |
|---|---|
| application_date | 0.0% |
| invention_title | 0.0% |
| abstract | 0.0% |
| register_date | 54.3% |
| register_status | 0.0% |

## 3. 기술통계 (descriptive)

### 출원인별

| 출원인 | 델타 건수 | G₀ 겹침(제외됨) |
|---|---|---|
| 삼성전자주식회사 | 23,901 | 51 |
| 에스케이하이닉스 주식회사 | 10,620 | 36 |

### 출원연도 (범위 2010–2025)

| 연도 | 건수 | 비고 |
|---|---|---|
| 2010 | 2,939 |  |
| 2011 | 2,222 |  |
| 2012 | 2,240 |  |
| 2013 | 1,811 |  |
| 2014 | 1,884 |  |
| 2015 | 1,954 |  |
| 2016 | 1,586 |  |
| 2017 | 1,336 |  |
| 2018 | 1,660 |  |
| 2019 | 1,750 |  |
| 2020 | 2,154 |  |
| 2021 | 2,406 |  |
| 2022 | 2,759 |  |
| 2023 | 3,513 |  |
| 2024 | 3,884 |  |
| 2025 | 423 | ⚠ 미공개분 절단 추정 |

> **최근 연도는 절단(truncation)되어 있다.** 특허는 출원 후 18개월이 지나야 공개되므로, 최근 2년의 출원 건수는 아직 다 드러나지 않았다. **감소가 아니라 미공개다.** H2 의 시계열은 이 구간을 추세 판단에서 제외하거나 절단을 명시해야 한다 (§4.4·§4.5).

### IPC 클래스 상위 (질의 클래스 기준, 중복 계수)

| IPC 클래스 | 건수 |
|---|---|
| G11C | 10,427 |
| H10B | 7,175 |
| H10D | 4,813 |
| H10W | 3,489 |
| H10P | 2,968 |
| H01L | 1,575 |
| G03F | 986 |
| G01N | 958 |
| H01J | 521 |
| C09K | 476 |

### 개념 매핑

| 축 | 건수 |
|---|---|
| 공정 개념 ≥1 | 7,913 |
| 소자 개념 ≥1 | 17,995 |
| 둘 다 없음 (미매핑) | 10,468 |

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
