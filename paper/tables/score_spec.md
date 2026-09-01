<!-- 자동 생성 — scripts/export_score_spec.py · 손으로 고치지 않는다 (CLAUDE.md §1-1·§1-7) -->

### 표 S10-1 · 점수 함수 확정표 (코드에서 추출)

온톨로지 결합 구성의 점수는 다음과 같다.

```
score(q, d) = (1 − α) · text_norm(q, d)
            +      α · ( w_c·ConceptOverlap + w_h·PathSim
                        + w_i·IpcSim + w_f·FeatureCoverage@τ )
```

| 구성 | 후보 풀 | 최종 가중치 | 텍스트 정규화 | 임계 | 코드 위치 |
|---|---|---|---|---|---|
| B4 (분류 단독) | 분류 접두 공유 ∩ 시점·패밀리 허용 집합 | `IpcSim` 단독 | — | — | `retrieval/systems.py:143` |
| B5 (온톨로지 단독) | 개념 정확 공유 ∩ 시점·패밀리 허용 집합 | `α=1.0` · `w_c=1.0` · `w_h=0.0` · `w_i=0.0` | IpcSim 미사용 | — | `retrieval/systems.py:172` |
| P0★ (사전 지정 주 구성) | **B3 상위 1000건 재순위화** — 후보집합 불확대 | `α=0.75` · `(w_c, w_h, w_i) = (0.5, 0.0, 0.5)` | 선형 rank-norm `1 − rank/(m−1)` ∈ [0,1] | — | `retrieval/systems.py:111` |
| P1 (부차 구성 · +한정요소) | **B3 상위 1000건 재순위화** — 후보집합 불확대 | `α=0.75` · `(w_c, w_h, w_i, w_f) = (0.25, 0.0, 0.25, 0.5)` | 선형 rank-norm `1 − rank/(m−1)` ∈ [0,1] | `τ = 0.7` | `analysis/ontology_eval.py:155` |

| 항 | 정의 | 입력 | 코드 위치 |
|---|---|---|---|
| ConceptOverlap `c` | **비가중 Jaccard** — `|Q∩D| / |Q∪D|`. 집합 연산이며 개념별 가중·문서빈도 가중이 없다 | 개념 슬러그 집합(frozenset · 축 6종) | `retrieval/ontology_rerank.py:89` |
| PathSim `p` | 축 클래스의 Wu–Palmer — `2·depth(LCA) / (depth(a)+depth(b))`. 개념 쌍이 아니라 **축 클래스**를 읽는다 | 개념 집합 → 축 클래스 | `retrieval/ontology_rerank.py:76` |
| IpcSim `i` | 분류 접두 계층의 **비가중 Jaccard** — 접두 집합 교집합/합집합 | IPC·CPC 코드 집합 | `retrieval/ontology_rerank.py:176` |
| FeatureCoverage `f` | 질의 독립항 한정요소 중 후보에 `cos ≥ τ` 매칭이 있는 **비율** | 한정요소 임베딩 행렬 | `retrieval/feature_coverage.py:120` |

**`w_h = 0` 이므로 계층·정렬만 바꾸는 자원 변경은 P0★·P1 의 점수에 원리적으로 비가시이다.** 이 값은 개발셋 격자 선택의 결과이며 사전등록 항목이 아니다.

**`ConceptOverlap` 은 비가중이다.** 개념별 가중이나 문서빈도 가중은 어느 구성에도 들어가지 않으며, 자원의 어휘를 늘리면 분모가 함께 커진다 — 평가 결과 §5.2 의 해석이 이 사실에 걸려 있다.
