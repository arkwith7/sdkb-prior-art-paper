**예시 델타 `merge_etch_into_plasma`** — 동의어 오병합(F11 축소판): 상위 공정 <process/etch> 를 하위 공정 <subprocess/plasma_etch> 로 흡수 — 회수율을 올리려는 '개념 통합' 시나리오. 변경 트리플 9건 · 트리플 수 169 → 168 · 측정·판정 rdflib · 이 스크립트의 v2 구현.

| CQ | 스위트 | 관찰 층 | 극성 | 행 수(전) | 행 수(후) | v2 판정 |
|---|---|---|---|---:|---:|---|
| CQ01 | core | T3 | up | 3 | 5 | 통과 |
| CQ02 | tf | T3 | up | 2 | 3 | 통과 |
| CQ03 | tf | T3 | down | 1 | 1 | 통과 |
| CQ04 | tf | T3 | up | 6 | 18 | 통과 |
| CQ05 | tf | T3 | up | 5 | 5 | 통과 |
| CQ06 | tf | T3 | down | 2 | 1 | 통과 |
| CQ07 | core | T3 | up | 1 | 2 | 통과 |
| CQ08 | core | T3 | up | 2 | 2 | 통과 |
| CQ09 | pa | L3 | up | 1 | 1 | 통과 |
| CQ10 | pa | L3 | up | 1 | 1 | 통과 |
| CQ11 | em | T3 | up | 1 | 4 | 통과 |
| CQ12 | em | T3 | up | 1 | 2 | 통과 |
| CQ13 | core | T3 | up | 1 | 1 | 통과 |
| CQ14 | core | T3 | up | 1 | 1 | 통과 |
| CQ15 | core | T3 | up | 1 | 2 | 통과 |
| CQ16 | pa | L3 | up | 1 | 2 | 통과 |
| CQ17 | em | T3 | up | 1 | 1 | 통과 |
| CQ18 | em | T3 | up | 1 | 1 | 통과 |
| CQ19 | core | T3 | up | 2 | 4 | 통과 |
| CQ20 | em | T3 | up | 2 | 2 | 통과 |
| CQ21 | core | T3 | up | 2 | 1 | 실패 · 분포검사 실패(회귀) |
| CQ22 | core | T3 | up | 2 | 2 | 통과 |
| CQ23 | core | T3 | up | 4 | 4 | 통과 |
| CQ24 | core | T3 | up | 2 | 2 | 통과 |
| CQ25 | core | T3 | up | 2 | 2 | 통과 |
| CQ26 | pa | L3 | up | 3 | 6 | 통과 |
| CQ27 | pa | L3 | up | 1 | 1 | 통과 |
| CQ28 | em | T3 | up | 1 | 1 | 통과 |
| CQ29 | pa | 사이드카(분모 제외) | up | 0 | 0 | 실패 · 존재검사 실패 |
| CQ30 | pa | 사이드카(분모 제외) | up | 0 | 0 | 실패 · 존재검사 실패 |
| CQ31 | pa | 사이드카(분모 제외) | up | 0 | 0 | 실패 · 존재검사 실패 |

**요약** — L3(pa 스위트): 통과 · T3(em·tf·core 스위트): 실패 (회귀 CQ 수 em 0 · tf 0 · core 1).
