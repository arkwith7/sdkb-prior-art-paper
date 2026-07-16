# 표 · 잔여 공백 — 보강 후에도 특허가 매핑되지 않은 공정 단계 (§4.5.3)

보강 후 커버 26/49 · **잔여 공백 23/49**. 공백을 룰 테이블(`code_to_concept.csv`)로
분류한다: **룰 없음** = 개념을 겨냥한 매핑 룰이 0개라 어떤 코퍼스로도 룰 경로로는 채울 수
없다(분류체계·온톨로지 범위의 경계). **룰 있음** = 룰은 있으나 그 미세 코드가 이 코퍼스에
부여되지 않았다(코퍼스 특이적).

- 룰 없음: **15** / 룰 있으나 코퍼스 0건: **8**
- 소부장 코퍼스(G₂)가 새로 채운 공백: **0** — breadth 는 26/49 로 포화한다.

| 단계 | 층위 | 룰 수 | 룰 있음 | G₂ after |
|---|---|---:|---|---:|
| Advanced Modules | process | 0 | 아니오 | 0 |
| Substrate Preparation | process | 0 | 아니오 | 0 |
| 3D Structures | subprocess | 0 | 아니오 | 0 |
| Defect Inspection | subprocess | 0 | 아니오 | 0 |
| Electrical Metrology | subprocess | 0 | 아니오 | 0 |
| Etchback Planarization | subprocess | 0 | 아니오 | 0 |
| High-k/Metal Gate | subprocess | 0 | 아니오 | 0 |
| In-situ Doping | subprocess | 0 | 아니오 | 0 |
| Multilayer Interconnect | subprocess | 0 | 아니오 | 0 |
| Physical Metrology | subprocess | 0 | 아니오 | 0 |
| Strain Engineering | subprocess | 0 | 아니오 | 0 |
| Wafer Manufacturing | subprocess | 0 | 아니오 | 0 |
| Wafer Polishing | subprocess | 0 | 아니오 | 0 |
| Wafer Testing | subprocess | 0 | 아니오 | 0 |
| Wafer Thinning | subprocess | 0 | 아니오 | 0 |
| Advanced Cleaning | subprocess | 1 | 예 | 0 |
| Dopant Activation | subprocess | 1 | 예 | 0 |
| Dry Cleaning | subprocess | 1 | 예 | 0 |
| Epitaxial Growth | subprocess | 1 | 예 | 0 |
| Interconnect Patterning | subprocess | 1 | 예 | 0 |
| Metal CMP | subprocess | 3 | 예 | 0 |
| Oxide CMP | subprocess | 2 | 예 | 0 |
| Wet Cleaning | subprocess | 1 | 예 | 0 |

출처: `make h1` · h1_coverage.csv · h1_coverage_ksia.csv · mappings/code_to_concept.csv
