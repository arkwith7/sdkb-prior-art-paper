**예시 델타 `relocate_case_failuremode`** — 전문가 사례–결함모드 재배치(F14 축소판): CASE_M01 의 caseFailureMode 를 micro_trenching → charging 으로 이전 (charging 은 RootCause 이므로 타입 서명이 어긋나지만 T-Box 에 서로소 공리가 없어 L2 는 침묵한다). 변경 트리플 1건 · 트리플 수 169 → 169 · 측정·판정 rdflib · 이 스크립트의 v2 구현.

| CQ | 스위트 | 관찰 층 | 극성 | 행 수(전) | 행 수(후) | v2 판정 |
|---|---|---|---|---:|---:|---|
| CQ01 | core | T3 | up | 3 | 3 | 통과 |
| CQ02 | tf | T3 | up | 2 | 2 | 통과 |
| CQ03 | tf | T3 | down | 1 | 1 | 통과 |
| CQ04 | tf | T3 | up | 6 | 6 | 통과 |
| CQ05 | tf | T3 | up | 5 | 5 | 통과 |
| CQ06 | tf | T3 | down | 2 | 2 | 통과 |
| CQ07 | core | T3 | up | 1 | 1 | 통과 |
| CQ08 | core | T3 | up | 2 | 2 | 통과 |
| CQ09 | pa | L3 | up | 1 | 1 | 통과 |
| CQ10 | pa | L3 | up | 1 | 1 | 통과 |
| CQ11 | em | T3 | up | 1 | 1 | 통과 |
| CQ12 | em | T3 | up | 1 | 1 | 통과 |
| CQ13 | core | T3 | up | 1 | 1 | 통과 |
| CQ14 | core | T3 | up | 1 | 1 | 통과 |
| CQ15 | core | T3 | up | 1 | 1 | 통과 |
| CQ16 | pa | L3 | up | 1 | 1 | 통과 |
| CQ17 | em | T3 | up | 1 | 1 | 통과 |
| CQ18 | em | T3 | up | 1 | 1 | 통과 |
| CQ19 | core | T3 | up | 2 | 2 | 통과 |
| CQ20 | em | T3 | up | 2 | 2 | 통과 |
| CQ21 | core | T3 | up | 2 | 2 | 통과 |
| CQ22 | core | T3 | up | 2 | 2 | 통과 |
| CQ23 | core | T3 | up | 4 | 4 | 통과 |
| CQ24 | core | T3 | up | 2 | 2 | 통과 |
| CQ25 | core | T3 | up | 2 | 2 | 통과 |
| CQ26 | pa | L3 | up | 3 | 3 | 통과 |
| CQ27 | pa | L3 | up | 1 | 1 | 통과 |
| CQ28 | em | T3 | up | 1 | 0 | 실패 · 존재검사 실패 |
| CQ29 | pa | 사이드카(분모 제외) | up | 0 | 0 | 실패 · 존재검사 실패 |
| CQ30 | pa | 사이드카(분모 제외) | up | 0 | 0 | 실패 · 존재검사 실패 |
| CQ31 | pa | 사이드카(분모 제외) | up | 0 | 0 | 실패 · 존재검사 실패 |

**요약** — L3(pa 스위트): 통과 · T3(em·tf·core 스위트): 실패 (회귀 CQ 수 em 1 · tf 0 · core 0).
