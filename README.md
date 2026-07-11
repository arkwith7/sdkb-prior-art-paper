# sdkb-foresight-paper

CHS7004(Python활용인문사회과학논문쓰기) 논문 프로젝트 — 삼성전자 반도체 특허로 SDKB 온톨로지를
보강하고, **검증 게이트(SHACL·CQ·리즈너)** 를 통과한 그래프로 커버리지(H1)·기술예측 신호(H2)를 검증한다.

> ⚠️ **private repo 유지.** KIPRIS 학술 자격으로 수집한 원문 데이터는 절대 커밋하지 않는다
> (`data/raw` 는 gitignore). 공개 산출물은 메타데이터 그래프만 별도 export 한다.

## 빠른 시작

```bash
uv sync --all-extras          # 의존성 설치
cp .env.example .env          # KIPRIS_API_KEY 입력
make vendor                   # 근간 온톨로지(SDKB) 스냅샷 가져오기  ← 최초 1회
make baseline                 # graph_v0 조립 (H1 의 "before")
make test                     # 단위 테스트
make gate                     # SHACL + CQ 게이트 (샘플 그래프)
```

## 근간 온톨로지 (SDKB)

이 논문은 **SDKB v1.0**([semiconductor-knowledge-base](https://github.com/arkwith7/semiconductor-knowledge-base),
CDLA-Permissive-2.0)을 보강한다. 어휘를 새로 발명하지 않고 SDKB 실물을 그대로 쓴다:

| 개념 | SDKB 어휘 |
|---|---|
| 공정 계층 (관측 단위) | `ont:Process` (8) ⊐ `ont:SubProcess` (12) |
| 특허 | `ont:Patent` (+ `Rejected`/`Granted`/`Pending`) |
| 특허 → 공정 링크 | `ont:realizesProcess` |
| 특허 식별/시점 | `ont:applicationNumber`, `ont:filingDate` |
| 분류코드 | `ont:hasIPC`, `ont:hasCPC` |
| 예측 신호 (H2) | `ont:Signal`, `ont:Scenario`, STEEPVE |
| 레이블 | `skos:prefLabel`(en) / `skos:altLabel`(ko) — **`rdfs:label` 아님** |

네임스페이스는 slash 3분리: `ont:` = TBox, `data:` = ABox 인스턴스, `gov:` = 거버넌스(미사용).
이 논문이 만드는 특허 인스턴스는 `data:patent/` 서브트리에 둬서 상류와 충돌하지 않는다.

baseline 은 SDKB 특정 커밋을 **얼린 스냅샷**(`data/external/sdkb/`)이다 — 살아있는 워킹트리를
참조하면 H1 의 before 가 움직여 재현이 깨진다. 출처·무결성은 `PROVENANCE.json`, 갱신 절차는
[data/MANIFEST.md](data/MANIFEST.md) 참조. SDKB 의 SIRP 거절특허 773건은 baseline 에서
**의도적으로 제외**했다 (before 를 특허 0건으로 두어야 보강 효과가 측정된다).

## 파이프라인

```
SDKB repo ──> vendor ──> data/external/sdkb/ ──> baseline ──> graph_v0.ttl  (특허 0건)
             (스냅샷 고정)                      (조립)              │  H1 의 before
                                                                   ▼
KIPRIS API ──┐                                                  검증 게이트
             ├─> preprocess(정규화·패밀리 dedup) ─> ontology.mapping ─> (validate/*) ─> graph_vN.ttl
BigQuery ────┘        (clean.py)                     (mapping.py)         │           (merge.py)
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
