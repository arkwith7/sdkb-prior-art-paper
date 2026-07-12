# PLAN-001 · IPC/CPC → 개념 룰의 H10 계열 보강

| | |
|---|---|
| 지지하는 것 | H1 (커버리지) · H2 (개념 단위 시계열) / 논문 §3.2 · §3.3 · §4.5 |
| 상태 | **완료** (2026-07-12) |
| 승인 | 요구정의·분석·설계 모두 사용자 승인 (2026-07-12) |
| 근거 | `make gate` exit 0 · `pytest` 41 passed · SDKB `ad7fe3d` |

---

## 1. 요구정의  ✅

```
목적      : 삼성 특허를 온톨로지 개념(Process ∪ Device)에 매핑할 수 있도록 룰 테이블의
            H10 계열 공백을 메운다. 룰이 없으면 삼성 특허가 L1(델타) 엄격 shape 에서
            탈락하고 H1 의 커버리지 증가가 과소 추정된다.
입력      : mappings/ipc_to_process.csv (현재 39개 접두어)
            IPC/CPC 공식 분류표 (코드별 정의)
            SIRP 의 IPC 분포 (매핑률을 미리 재는 시험대)
출력      : 확장된 룰 테이블 + 커버리지 리포트 (make mapping)
성공 기준 : 각 신규 룰이 **코드 정의에 근거한 rationale** 을 갖는다.
            SIRP 를 시험대로 한 매핑률이 개선된다 (현재 447/1,000 = 45%).
비목표    : 매핑률을 높이기 위한 근거 없는 룰 추가. 텍스트 임베딩 기반 매핑(별도 단계).
```

---

## 2. 분석  ✅ (2026-07-12 수행)

### 2.1 PLAN 의 사전 경고가 절반 틀렸다 — H10P 는 **공정** 분류다

§2 의 사전 경고("H10 계열은 소자 분류이니 `concernsDevice` 로 보내라")는 H10B/H10D 에는
맞지만, **가장 큰 덩어리인 H10P(562건)와 H10W(143건)에는 틀렸다.**

CPC 2026.01 공식 스킴(아래 2.5 의 원천)에서 확인한 정의:

| 서브클래스 | 공식 제목 | 축 |
|---|---|---|
| **H10P** | Generic **processes or apparatus** for the manufacture or treatment of devices covered by class H10 | **공정** — 구 H01L21 의 후속 |
| H10W | Generic packages, interconnections, connectors or other **constructional details** | 구조(패키지·배선) |
| H10B | **Electronic memory devices** | 소자 |
| H10D | Inorganic electric **semiconductor devices** | 소자 |

H10P 의 그룹은 SDKB 공정과 그대로 맞물린다 — H10P 14(층 형성) → Deposition,
14/24·14/43 → CVD, 14/22·14/44·14/45 → PVD, H10P 30 → Ion Implantation,
H10P 32·34·95/90 → Diffusion/Anneal, H10P 50 → Etch(50/20 → Plasma Etch, 50/60 → Wet Etch),
H10P 52·52/40 → CMP, H10P 70 → Clean, H10P 74·72/06 → Metrology, H10P 76 → Lithography.

### 2.2 EUV/DUV 는 여전히 IPC 로 갈리지 않는다 (요약 모델의 날조를 걸러낸 기록)

조사 중 한 웹 요약이 `H10P 95/041 = DUV lithography` · `H10P 95/042 = EUV lithography`
라는 그룹을 보고했다. **공식 스킴 HTML 을 직접 파싱한 결과 그런 그룹은 존재하지 않는다**
(H10P 95/04 는 "Planarisation of conductive or resistive materials"). 요약 모델의 날조였다.
→ `mapping.py` 의 기존 서술("EUV/DUV 는 IPC 접두어로 구분 불가, 용어 매칭 경로가 필요")이
그대로 유효하다. **룰 제목은 요약이 아니라 스킴 원문에서만 가져온다** (2.5).

### 2.3 놀라운 점 — 매핑 실패의 최대 원인은 룰이 아니라 **SDKB 소자 어휘의 공백**이다

| 코드 | 공식 제목 | 건수 | SDKB 대응 개념 |
|---|---|---:|---|
| **H10B 69/00** | Erasable-and-programmable ROM [EPROM] devices **not provided for in** H10B 41/00–63/00 | 243 | **없음** |
| **H01L 21/8247** | (구 IPC) ROM 구조 중 electrically-programmable = EPROM 제조 | 234 | **없음** |
| H10D 30/67 | Thin-film transistors [TFT] | 62 | 없음 |
| H10D 62/00 · 64/00 | Semiconductor **bodies/regions** · **Electrodes** of devices | 70 | 없음(소자가 아니라 소자의 *부분*) |
| H10K 59/00 · 50/00 | Organic light-emitting devices (OLED) | 55 | 없음(도메인 밖) |
| H10B 51/53 | Ferroelectric RAM [FeRAM] | 4 | 없음(MRAM·ReRAM·PCRAM 은 있는데 FeRAM 만 빠짐) |
| H10D 8/00 | Diodes | 8 | 없음(photodiode 만 있음) |

H10B69 와 H01L21/8247 은 사실상 **같은 특허군**(구형 플래시/EPROM)이고, 둘이 SIRP 미매핑
553건의 대부분을 설명한다. SDKB Device 31개에 **EPROM 이 없다** — E2PROM 은 있으나 다른 소자다.
이를 `device/eeprom` 이나 `device/nand_flash` 로 보내는 것은 CLAUDE.md §1.2 가 금지하는 날조다.

### 2.4 매핑률 시뮬레이션 (SIRP 1,000건 시험대)

| 룰 구성 | 매핑률 |
|---|---:|
| 현행 39개 접두어 | 447 / 1,000 = **44.7%** |
| + H10P 공정 룰 | 543 = 54.3% |
| + 공정 + **SDKB 에 이미 있는** 소자 룰 | 600 = 60.0% |
| + 공정 + 소자 + **신규 개념 3개**(EPROM·FeRAM·Diode) | **848 = 84.8%** |

즉 **EPROM 개념 하나가 매핑률 25%p 를 좌우한다.** 이것은 룰의 한계가 아니라 어휘의 공백이다.

### 2.5 원천 (재현 가능)

코드 제목은 CPC 2026.01 공식 스킴 HTML(`https://www.uspto.gov/web/patents/classification/cpc/html/cpc-<SUBCLASS>.html`,
16개 서브클래스)을 내려받아 **직접 파싱**한 값이다. 요약 모델을 거치지 않는다(2.2 의 교훈).

---

## 3. 설계  🛑 (승인 대기)

### 3.1 룰 테이블 — 단일 파일 + `axis` 컬럼

`mappings/ipc_to_process.csv` → **`mappings/code_to_concept.csv`** (개명: 더는 공정 전용이 아니다)

```
code_prefix, axis, concept_iri, level, scheme, code_title, rationale, confidence, status
H10P50/20, process, .../subprocess/plasma_etch, subprocess, CPC, "Dry etching; Plasma etching; Reactive-ion etching", H01L21/3065 의 후속 그룹, high, author-defined
H10B12,     device,  .../device/dram,           device,     CPC, "Dynamic random access memory [DRAM] devices", 코드 정의가 곧 소자, high, author-defined
```

- `axis ∈ {process, device}` — 병합 시 `ont:realizesProcess` / `ont:concernsDevice` 를 가른다.
- `code_title` 은 **공식 스킴 원문 그대로**. 출처·판본·sha256 은 `mappings/PROVENANCE.md` 에 기록.
- 긴 접두어 우선 매칭은 그대로(H10P50/20 이 H10P50 보다 먼저 잡힌다).

### 3.2 코드 계약 변경 (영향 범위는 좁다 — 델타 트리플 생성기가 아직 없다)

| 파일 | 변경 |
|---|---|
| `config.py` | `IPC_MAPPING` → `CODE_MAPPING = MAPPINGS / "code_to_concept.csv"` |
| `ontology/mapping.py` | `load_code_mapping() -> dict[str, list[tuple[str, str]]]` (iri, axis)<br>`map_codes_to_concepts(codes, table) -> dict[str, list[str]]` = `{"process": [...], "device": [...]}`<br>`rule_coverage()` 를 Device 축까지 확장 (커버리지 리포트가 51개 개념 전체를 본다) |
| `tests/test_mapping.py` | 축 분기·긴접두어 우선·공백 정규화(`"H10P 50/26"`)·미매핑 반환 계약 |
| `Makefile` | `make mapping` 이 공정·소자 두 축의 커버리지를 함께 보고 |

`merge.py` · SHACL delta shape 는 **손대지 않는다** — 이미 `Process ∪ Device` 를 허용한다.

### 3.3 상류 SDKB: 소자 개념 3개 추가 (사용자 결정 2026-07-12)

`~/Dev/sdkb` 에서 고치고 → `make vendor` → `make baseline` → G₀ 재동결.
아직 G₀ 를 동결하지 않았으므로 "SDKB 정비 → 재vendor → G₀ 동결" 순서와 정합적이다.

| 신규 개념 | 근거 | 이 개념이 여는 코드 |
|---|---|---|
| `device/eprom` (EPROM) | H10B 69/00 의 코드 정의 자체. SDKB 에 E2PROM 은 있고 EPROM 만 없다 | H10B69 · H01L21/8247 · G11C16 |
| `device/feram` (FeRAM) | MRAM·ReRAM·PCRAM 이 있는데 FeRAM 만 빠진 **어휘의 비대칭** | H10B51 · H10B53 |
| `device/diode` (Diode) | photodiode 만 있고 일반 다이오드가 없다 | H10D8 |

**추가하지 않는 것 (그리고 그 이유):**
- **공정 개념은 하나도 추가하지 않는다.** H10P10(웨이퍼 본딩, 128건)·H10P54/58(다이싱)·
  H10P72(핸들링, 140건)에 대응하는 SDKB 공정이 없지만, **공정 개념을 추가하면 H1 의 관측 단위가
  20 → 21+ 로 바뀐다**(§3.4.3). 게다가 새 공정은 G₀ 에서 C₀(s)=0 이므로 G₁ 이 채우면 **H1 이
  이기도록 설계된 셈**이 된다 — §1.2 가 금지하는 조작이다. 미매핑으로 남기고 §4.5 에 보고한다.
- **OLED·LED·태양전지**(H10K·H10H·H10F, 약 90건): SDKB 의 반도체 공정 도메인 밖이다.
  SIRP 커버리지를 좇아 온톨로지를 늘리는 것은 데이터에 어휘를 맞추는 것이다. 범위 경계로 보고한다.
- **소자의 *부분*** (H10D62 영역 · H10D64 전극 · H10W40 방열): 소자 유형이 아니므로 Device 축에
  들어갈 수 없다.

### 3.4 결정성

룰은 CSV 이고 매칭은 문자열 접두어다. 난수 없음. 같은 입력 → 같은 출력.

---

### 3.5 설계 중 뒤집힌 것 — 공정 개념도 추가한다 (사용자 결정 2026-07-12)

3.3 은 "공정 개념은 하나도 추가하지 않는다"고 적었다. 그 근거는 *새 공정은 G₀ 에서 C₀(s)=0 이라
H1 이 이기도록 설계하는 셈*이라는 것이었다. 그런데 **SDKB 의 공정 8개가 전부 SemiKong 한 출처에서
인용된 것**임을 확인하고 원문(arXiv:2411.13802 Appendix A, Table 7)을 열어 보니, **원천은 Process
Group 이 10개인데 SDKB 는 7개만 담고 있었다.** 누락: **1. Substrate Preparation · 9. Advanced
Modules · 10. Back-End Processes**(다이싱·패키징·금속화·웨이퍼 테스트 전체).

이로써 판단이 뒤집힌다 — 후공정 개념을 넣는 것은 **어휘의 발명이 아니라 출처 분류의 복원**이다.
선택이 우리 특허 분포와 무관하므로 §1.2 의 조작에 해당하지 않는다. 다만 복원된 단계가 G₀ 에서
전부 비어 있다는 편향은 남으므로, **H1 을 두 집합(49 / 20)으로 병기 보고**한다.

---

## 4. 구현 ✅

**상류 SDKB** (`ad7fe3d`)
- `scripts/add_semikong_process_nodes.py` (신규·멱등) — Table 7 의 Group·Module 열 전량 복원.
  Process 8 → **11**, SubProcess 12 → **38**. 기존 20개 IRI 불변(하류가 가리킨다).
- Device 31 → **34** (EPROM `Q378210` · FeRAM `Q703656` · Diode `Q11656`).
  Wikidata 상 EEPROM(Q205908)이 EPROM 의 `P279 subclass of` 하위임을 확인 — 별개 소자다.

**논문 저장소**
- `mappings/code_to_concept.csv` (구 `ipc_to_process.csv`) — 룰 39 → **96** (공정 76 · 소자 20).
  `axis` 컬럼 신설. 코드 제목은 **CPC 2026.01 공식 스킴 원문**(`mappings/PROVENANCE.md`).
- `ontology/mapping.py` — `load_code_mapping() -> {code: [(iri, axis)]}`,
  `map_codes_to_concepts() -> {"process": [...], "device": [...]}`, `rule_coverage()` 가 Device 축 포함.
- `config.CODE_MAPPING`, `tests/test_mapping.py`(축 분기·폐지코드·후공정·핸들링 미매핑 계약).

## 5. 검증 ✅

| 검증 | 결과 |
|---|---|
| `make lint` · `pytest` | All checks passed · **41 passed** |
| `make gate` | **exit 0** — 스냅샷 무결 → baseline → L1(graph+delta) → L2 HermiT → L3 CQ 8/8 |
| `make baseline` 결정성 | 2회 실행 동일 sha256 (통합 테스트가 강제) |
| **SIRP 매핑률** (룰 시험대) | **447/1,000 (44.7%) → 870/1,000 (87.0%)** |
| 룰이 도달하는 개념 | 41 / 83 (공정 9/11 · 서브공정 19/38 · 소자 13/34) |

**G₀ 서명 변화** — STATUS.md · 논문 표 3 을 같은 커밋에서 갱신했다.

| | 전 | 후 |
|---|---:|---:|
| 트리플 | 26,676 | **26,973** |
| 공정 단계 (H1 관측 단위) | 20 | **49** |
| 디바이스 | 31 | **34** |
| 커버된 공정 / 공백 | 16 / 4 | **16 / 33** |
| CQ06 최근 5년 출원 전무 개념 | 29 / 51 | **61 / 83** |

**남은 사각지대(의도적 미매핑).** H10P72(웨이퍼 핸들링 140건) · H10D62/64(소자의 영역·전극) ·
H10D30/67(TFT) · H10W20(배선 구조) · H10K/H10H/H10F(OLED·LED·광전). 대응 개념이 없어서이며,
억지 매핑하지 않고 §4.5 에 공백으로 보고한다. 근거는 `mappings/PROVENANCE.md`.
