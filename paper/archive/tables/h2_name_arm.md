# 조합 능력 — 개념(구조 조합) 단위 vs **명칭 키워드** 단위 조기탐지 (§4.4)

**이 표는 유의성 검정이 아니라 온톨로지 조합 능력의 존재 증명이다.** 온톨로지는 기술을
기존 개념의 **논리 조합**(∧/∨)으로 정의해, 그 기술의 **이름도 전용 코드도 생기기 전에**
추적한다. 분류코드는 소급 재분류로 무효이고(표 6) 명칭 키워드는 이름이 있어야 작동하지만,
조합 정의는 둘 다 없는 국면에서 발화한다. 조합 정의는 JEDEC·IRDS·ITRS ERD·SEMI 표준
용어에서만 도출해 **결과를 보기 전에 동결**했다(`mappings/si_concepts.csv`).

`si_struct` 는 정의에서 **명칭 용어를 뺀 구조 전용**이라 명칭 대조군과 **서로소**다 —
부분집합 자명성(개념 ⊇ 이름)이 결론을 만들지 않는다. 신호 규칙(θ=2.0 · n_min=3 ·
후행창 3년)은 손대지 않았고, 사례는 리드가 아니라 **특허량 기준**으로 사전 확정한 10건이다.

| window | definition | disjoint | n_cases | n_pairs | concept_first | name_first | p | rejects |
|---|---|---|---|---|---|---|---|---|
| 2010–2023 | si | False | 10 | 7 | 5 | 2 | 0.2266 | False |
| 2010–2023 | si_struct | True | 10 | 8 | 4 | 4 | 0.6367 | False |
| 2005–2023 | si | False | 10 | 6 | 5 | 1 | 0.1094 | False |
| 2005–2023 | si_struct | True | 10 | 7 | 5 | 2 | 0.2266 | False |

## 교정 창 · 구조 전용 개념 (서로소 · 주 결과)

| case_id | concept_total | name_total | concept_year | name_year | lead | lead_is_lower_bound | outcome |
|---|---|---|---|---|---|---|---|
| hbm | 29 | 16 | 2009 | 2020 | 11 | False | concept_first |
| tsv | 605 | 149 | 2009 | 2009 | 0 | False | tie |
| 3d_nand | 13 | 6 | 2009 | — | 14 | True | concept_first |
| gaa | 205 | 18 | 2015 | 2016 | 1 | False | concept_first |
| mram | 152 | 86 | 2008 | 2008 | 0 | False | tie |
| finfet | 99 | 60 | 2012 | 2013 | 1 | False | concept_first |
| pcram | 560 | 507 | 2016 | 2016 | 0 | False | tie |
| feram | 212 | 107 | 2016 | 2021 | 5 | False | concept_first |
| reram | 131 | 48 | — | 2008 | — | False | name_first |
| interposer | 4 | 311 | — | 2018 | — | False | name_first |

> **개념(구조) 우선 5 · 동점 3 · 명칭 우선 2.** 리드는 HBM 11년(구조 2009 vs
> 명칭 2020) · 3D NAND ≥14년(명칭 끝내 미탐지) · FeRAM 5년 · GAA·FinFET 각 1년이다.
> **구조가 이름과 진짜로 다른 곳에서 개념은 한 번도 지지 않는다.** 동점은 이름≈구조인
> 사례(TSV·MRAM·PCRAM)이고, 명칭 우선은 이름과 구조가 겹치거나(ReRAM) 구조 정의가 좁아
> 미탐지된(Interposer) 약 사례로 — 어느 것도 명칭이 실제 부상을 먼저 잡은 경우가 아니다.
> 이 약점은 사례 동결 시점에 `name_baseline.csv` 에 미리 적어 두었다.

**유의성이 아니라 능력을 논증하므로 사례 수의 통계적 검정력에 의존하지 않는다** — 이
능력은 조기 탐지 존재 증명으로 성립한다. HBM 은 개념이 2009년, 명칭('HBM')이 2020년이다.
