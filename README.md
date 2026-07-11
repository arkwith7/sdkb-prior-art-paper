# sdkb-foresight-paper

CHS7004(Python활용인문사회과학논문쓰기) 논문 프로젝트 — 삼성전자 반도체 특허로 SDKB 온톨로지를
보강하고, **검증 게이트(SHACL·CQ·리즈너)** 를 통과한 그래프로 커버리지(H1)·기술예측 신호(H2)를 검증한다.

> ⚠️ **private repo 유지.** KIPRIS 학술 자격으로 수집한 원문 데이터는 절대 커밋하지 않는다
> (`data/raw` 는 gitignore). 공개 산출물은 메타데이터 그래프만 별도 export 한다.

## 빠른 시작

```bash
uv sync --all-extras          # 의존성 설치
cp .env.example .env          # KIPRIS_API_KEY 입력
make test                     # 단위 테스트
make gate                     # SHACL + CQ 게이트 (샘플 그래프)
```

## 파이프라인

```
KIPRIS API ──┐
             ├─> preprocess(정규화·패밀리 dedup) ─> ontology.mapping ─> 검증 게이트 ─> graph_vN.ttl
BigQuery ────┘        (clean.py)                     (mapping.py)      (validate/*)    (merge.py)
                                                                            │
                                              analysis: coverage(H1) · timeseries(H2) · viz
```

- **검증 게이트**: `make gate` — SHACL 제약 + Competency Question 통과율. 게이트를 통과한
  델타만 `ontology.merge.merge_with_gate()` 로 그래프에 머지된다. CI 가 매 push 마다 동일 게이트를 실행.
- **그래프 스냅샷 규율**: 머지할 때마다 `data/processed/graph_v{n}.ttl` 저장 + `data/MANIFEST.md`
  갱신을 한 커밋으로. H1/H2 의 보강 전후 비교는 스냅샷 간 비교다.
- **그림**: 논문 그림은 전부 `viz/figures.py` 가 생성 (`paper/figures/`). 수작업 그림 금지.

## 주차별 운영 (수업 커리큘럼 매핑)

| 주차 | 수업 내용 | 이 repo 에서 할 일 | 태그 |
|---|---|---|---|
| 3–4 | Python/EDA | 현행 그래프 커버리지 공백 EDA (`wk04`) | |
| 6 | 자료 수집 | KIPRIS 배치 수집 + MANIFEST (`wk06`) | `wk06-collection-done` |
| 7–8 | numpy/pandas | 매핑 + H1 커버리지 정량화 (`wk08`) | |
| 9 | 시각화 | 커버리지 히트맵/그래프 figure | |
| 10 | 가설 검증 | H1 통계 검정 (wilcoxon) | `wk10-h1-verified` |
| 11–12 | ML | 특허→개념 분류 / 군집↔온톨로지 교차검증 | |
| 14 | 시계열 | H2 emerging signal + 원고 마감 | `wk14-final` |

## Colab

`notebooks/wk00_template.ipynb` 의 부트스트랩 셀 사용. GH_TOKEN(fine-grained PAT) 과
KIPRIS_API_KEY 를 **Colab Secrets** 에 저장 — 노트북에 키를 절대 하드코딩하지 않는다.
