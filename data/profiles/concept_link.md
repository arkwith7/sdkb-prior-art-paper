# 개념 적용기 프로파일 — concept_link (PLAN-034 · D-19)

> 코드 생성물. 재생성: `make corpus`. 원문은 담지 않는다 — 표면형은 **사전의 어휘**이지
> 특허 본문이 아니다(CLAUDE.md §1-5·§4).

- 생성(UTC): 2026-08-01T14:28:38+00:00
- 지지 주장: **C3**(O/O′ 개념 링크 델타를 0 이 아니게 만들어 H2 를 검정 가능하게) · C0(D-19)
- 사전: `concept_mapping.json` 프로파일 `patent-text`

## 1. 구조 (사이드카 컬럼·목적)
| 컬럼 | 목적 |
|---|---|
| doc_id | 코퍼스 문서 식별자 |
| **concept_id** | 접두어(축) 포함 정본 식별자 — 코퍼스 `concepts` 열은 지역명만 보관하므로 **축은 여기에만 남는다** |
| slug | 지역명 = 코퍼스 `concepts` 의 키(결정 A) |
| axis | 사전 `concept_type` |
| surface | 발화한 정규화 표면형 |
| rule_id·confidence·ambiguous | 상류 규칙 출처 — **점수에 반영하지 않는다**(결정 B) |

## 2. 형태
- 사전: 표면형 **636** (경계요구 487 · 한글전용 149) · 항목 653 · 개념 274 · 지역명 269 · 다의 표면형 16
- 발화 표면형: **380/636** (무발화 256 — 특허 산문에 안 나오는 장비 모델명·Vendor 중심. **결함이 아니다**(설계 결정 C))
- 신규 링크: **128,875건** · 문서 40,552
- 문서당 개념(합집합): 평균 **3.779** · 중앙값 3 · 보유율 98.9%
- 개념 어휘(합집합): **199**
- 적용 전: 문서당 평균 1.545 · 보유율 98.0%

## 3. 기술통계

### 3.1 언어별 (T2 하위집단의 사전 관측)
| lang | 문서 | 적용기 링크 | 문서당 신규 | 합집합 문서당 |
|---|---:|---:|---:|---:|
| en | 1,189 | 4,039 | 3.397 | 3.465 |
| ja | 117 | 0 | 0.000 | 0.000 |
| ko | 39,246 | 101,444 | 2.585 | 3.800 |

> **일본어는 이 모듈로 열리지 않는다** — 사전의 `lang: ja` 표면형이 0개라 구조적 0이다.
> D-21(CR-003 후속) 대상이며, 여기 수치가 그 사실의 관측이다(PLAN-034 §6 위험 A 확증).

### 3.2 축 분포 (적용기 신규 링크 기준)
| 축 | 링크 | 비율 |
|---|---:|---:|
| Material | 55,973 | 43.4% |
| Process | 49,428 | 38.4% |
| SubProcess | 10,321 | 8.0% |
| EquipmentClass | 6,596 | 5.1% |
| Device | 3,345 | 2.6% |
| Skill | 1,436 | 1.1% |
| FailureMode | 528 | 0.4% |
| Parameter | 513 | 0.4% |
| TechnologyNode | 400 | 0.3% |
| RootCause | 118 | 0.1% |
| Mitigation | 108 | 0.1% |
| Metrology | 49 | 0.0% |
| Organization | 32 | 0.0% |
| Equipment | 14 | 0.0% |
| Vendor | 14 | 0.0% |

> D-15 는 전문가용 사전을 특허에 적용하면 Skill 축이 18.1 % 를 먹는다고 경고했다. `patent-text` 프로파일에서 그 값이 얼마인지가 **상류 교정(CR-007)이 작동했는지의 하류 확인**이다.

### 3.3 다의 표면형 (Q3: 후보 전부 유지)
| 표면형 | 문서 | 개념 |
|---|---:|---|
| `산화막` | 2,528 | material:oxide, material:sio2 |
| `oxide` | 902 | material:oxide, material:sio2 |
| `annealing` | 146 | process:diffusion, subprocess:annealing |
| `oxidation` | 88 | rootcause:oxidation, subprocess:oxidation |
| `particle` | 88 | failuremode:particle, process:clean |
| `overlay` | 37 | metrology:overlay, skill:overlay_optimization |
| `photomask` | 23 | material:photomask, skill:mask_engineering |
| `process gas` | 19 | material:process_gas, skill:gas_chemistry |
| `cd sem` | 5 | equipment_class:cd_sem, metrology:cd_sem |
| `implanter` | 1 | equipment:implanter, equipment_class:implanter |

### 3.4 df 상위 표면형
| 표면형 | 문서 | 개념 |
|---|---:|---|
| `식각` | 7,376 | process:etch |
| `챔버` | 6,463 | equipment_class:process_chamber |
| `절연막` | 6,431 | material:dielectric |
| `가스` | 6,096 | material:process_gas |
| `플라즈마` | 4,390 | process:plasma_processing |
| `마스크` | 4,276 | material:photomask |
| `증착` | 4,159 | process:deposition |
| `산화물` | 3,821 | material:oxide |
| `박막` | 2,626 | process:deposition |
| `산화막` | 2,528 | material:oxide, material:sio2 |
| `질화물` | 2,466 | material:sin |
| `세정` | 2,149 | process:clean |
| `정렬` | 2,101 | subprocess:overlay_control |
| `포토` | 2,009 | process:lithography |
| `알루미늄` | 1,989 | material:aluminum |

## 4. 알려진 사전 결함 — **하류에서 고치지 않는다**

우회 패치는 스냅샷 출처를 거짓으로 만든다(CLAUDE.md §0.1). 그대로 통과시키고 상류 CR 로 회신한다.

| 표면형 | 매핑 | 문서 | 문제 |
|---|---|---:|---|
| `hf` | `material:hf_acid` | 1,234 | D-20(P1) 반도체 특허의 단독 Hf 는 하프늄(high-k)이다 — 불산 오링크 |
| `co` | `material:cobalt` | 965 | D-20 부수 위험: CO(일산화탄소)·Co.(회사명) 혼입 가능 |
| `high k` | `material:hfO2` | 111 | D-20 부수: 부류(high-k)를 특정 물질로 축소하는 과대특정 |

## 5. 사용 목적
- 코퍼스 `concepts` 열 → 온톨로지 재랭크팔(P0★·P1)·B5 독립팔의 입력.
- 사이드카 `concept_id` → 축 지도 확장(A2/A3/A8 절제가 신규 개념을 누락하지 않게).
- 언어별 표 → T2 하위집단 해석의 사전 관측(판정은 `make gate` 가 한다).
- **점수 가중에는 쓰지 않는다** — confidence·rule_id 는 감사·회신 전용(결정 B).

## 6. 누출 통제
- 사전은 온톨로지 개념 어휘에서만 유도되며 인용 간선(`hasPriorArt*`)을 보지 않는다.
  그 진술을 믿지 않고 `make leakage` 가 사전 파일을 직접 열어 재확인한다(L-2).
- 질의·후보에 **같은 함수·같은 사전**이 적용된다 — `match()` 는 역할 인자를 받지 않는다.
