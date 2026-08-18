# PLAN-058 — 평가 하네스의 단일 리포 공개 (1단계 산출물: 허용목록 초안 · 라이선스 표)

> **상태: 초안 · 미승인 · 파일 이동 0건.** 이 문서는 무엇을 옮길지의 **목록**이며, 옮기지 않았다.
> 목적은 원고 §4 표 4가 약속한 재현 경로를 실재하게 만드는 것이다(§6.6 정합).
> **판정·수치 변경 0 · 새 실험 0 · qrel 재개봉 0.**

## 0. 결정 (2026-08-18 · 사용자)

리포는 **하나**다 — `sdkb-dataset` 안에 `benchmark/` 하위 트리를 둔다. 데이터셋 참조자와 논문
재현자를 가르는 것은 리포가 아니라 **디렉터리·설치 명령·문서 진입점** 셋이다.

## 1. 허용목록 초안 — 무엇을 옮기는가

출처는 전부 `~/Dev/SKKU/sdkb-prior-art-paper` 이며, 목적지는 `sdkb-dataset/benchmark/` 다.
**디렉터리 통째 복사는 하지 않는다** — 파일 단위 목록이다(상류 `build_public_release.py` 의
허용목록 전환과 같은 규율: *모르는 파일은 공개하지 않는다*).

### 1.1 코드 — `benchmark/src/`  (74 파일 · 전량 실재 확인)

| 출처 | 파일 | 근거 (원고) |
|---|---|---|
| `src/sdkb_paper/` | `config.py` · `__init__.py` | 동결 상수 전량 — `SEED=20260726` · `T_EPSILON=0.02` · `T_DELTA=0.05` · `CQ_TAU=0.05` (§4.5) |
| `retrieval/` | `bm25.py` `dense.py` `dense_local.py` `hybrid.py` `systems.py` `ontology_rerank.py` `candidate.py` `feature_coverage.py` `layers.py` `tokenize.py` `userdict.py` `__init__.py` | **표 4의 진입점 전량** — B0·B2·B3·B4·B5·P0★ |
| `analysis/` | `metrics.py` `bootstrap.py` `ablation.py` `subgroup.py` `effort.py` `overlap.py` `ontology_eval.py` `results_table.py` `faults.py` `failure_typology.py` `judgment_robustness.py` `increment.py` `lang_recall.py` `pathsim_diag.py` `typology_prompt.txt` `__init__.py` | 표 4 채점(`metrics.py`) · P1(`ontology_eval.py::rerank_p1`) · §4.4 절제 · §4.5 통계·판정 전복 문턱 · 실패 유형 코딩 규약 |
| `validate/` | `t1_noninferiority.py` `t2_subgroup.py` `t3_cross_task_cq.py` `t_gate.py` `leakage_check.py` `fault_inject.py` `cq_runner.py` `shacl_gate.py` `reasoner_gate.py` `seal_audit.py` `runset.py` `vocab_coverage.py` `dedup_exempt.py` `quarantine.py` `__init__.py` | §3.4 L0–L3 · §3.5 승인식 · §4.2 누출 차단 · §4.4 결함 주입 |
| `corpus/` | `assemble.py` `split.py` `claim_join.py` `claim_features.py` `concept_link.py` `qrel_b.py` `qrel_family_merge.py` `text.py` `__init__.py` | §4.1 분할 경계·패밀리 분리 · 코퍼스 재구축 |
| `rag/` | `frozen.py` `context.py` `generate.py` `score.py` `t4.py` `count.py` `__init__.py` | §3.5.1 T4 계측기 — **`frozen.py` 가 프롬프트 원문과 `PROMPT_SHA256` 을 함께 진다** |
| `viz/` | `figures.py` `figdata.py` `concept.py` `__init__.py` | §6.6 "그림 생성 코드" · §7.1 규격 F6 |
| `ontology/` | `concept_axis.py` `concept_dict.py` `central_axis.py` `vendor.py` `baseline.py` `merge.py` `mapping.py` | 위 모듈의 임포트 폐포에서 실제로 걸린 것만 |
| `collect/` | `bq_family_ir.py` `__init__.py` | family map — 주 지표가 family 수준이므로 필수 |

**임포트 폐포는 실측으로 확인하였다.** 위 목록 밖에서 §4 모듈이 부르는 것은 없다. 특히
`collect/kipris_client.py`·`bq_cpc.py`·`dart.py` 는 **§4 경로에서 호출되지 않는다**(구
커버리지 패러다임 잔존 모듈이 부른다).

### 1.2 평가 자산 — `benchmark/assets/`

§6.6 이 이미 공개 대상으로 선언한 것들이다. **원문 0열**이 조건이다.

| 자산 | 출처 | 형식 전환 |
|---|---|---|
| 분할 식별자 · 경계 | `data/processed/ir/split.parquet` | → CSV(출원번호·split·출원일) |
| qrel 식별자 | `qrel_examiner.parquet` · `qrel_test_sealed.parquet` · `qrel_b_sealed.parquet` · `qrel_family_merged.parquet` | → CSV(qid·docid·rel) |
| 동결 임계 | `config.py` + `overlap_threshold.json` | 파일 그대로 |
| 개봉 원장 | `seal_access.jsonl` (5행) | 파일 그대로 |
| 런셋 정의 | `data/runsets/*.json` (6개) | 파일 그대로 |
| 결함 주입 명세·행렬 | `data/processed/fault_matrix*.json` (8개) | 파일 그대로 |
| 결과표 원본 | `paper/tables/*.md` (20개) | 파일 그대로 |
| 그림 동결 수치 | `paper/figures/data/concept_values.json` | 파일 그대로 |
| CQ 스위트·shapes | `queries/cq/*.rq` (31) · `queries/shapes/**` (6) | **이미 상류에 있음 — 중복 배치하지 않고 링크** |

### 1.3 문서 — `benchmark/`

`README.md`(원고 §4 표 4 ↔ 모듈 대응표 · 재현 순서 · 알려진 결손 둘) · `MANIFEST.json`(코드
sha256 + 대응 스냅샷 서명 `d578bf3`) · `Makefile.benchmark`.
supplementary 4종(S1·S2·S3·S5)과 crosswalk(S6)은 **원고 리포가 아니라 여기로** 온다 — §6.6 이
평가 자산으로 이미 선언했고, 지금은 도달 경로가 없다.

## 2. 옮기지 않는 것과 사유

| 대상 | 사유 |
|---|---|
| `data/raw/` · `data/interim/` · `data/processed/*` 원문 계열 | §1-5 · KIPRIS 비재배포. 식별자만 CSV 로 나간다 |
| `src/sdkb_paper/explore/` (6 파일) | 내부 뷰어 — 재현에 불필요 |
| `collect/kipris_client.py` · `bq_cpc.py` · `dart.py` · `collect.py` · `b_layer/` | §4 경로가 부르지 않는다. 재인출은 상류 `scripts/refetch_rejected_patents.py` 가 이미 진다 |
| `analysis/{census,s1_coverage*,s2_timeseries*,applicant_cli,ksia_strata_cli,robustness_cli}` | 구 커버리지 패러다임 산출물 — 현 원고가 인용하지 않는다 |
| `01.code_spec/` PLAN 전량 · `upstream/` 결함대장 · `paper/` 원고·정본 | 감사 기록이지 재현물이 아니다. 사전등록 대응은 S6 crosswalk 가 진다 |
| `tests/` (54 파일) | **보류** — §3 의 지문 검사를 통과한 것만 선별 반입(아래 4절) |

## 3. 라이선스 표 — 한 리포 · 두 조건

현행 `pyproject.toml:9` 는 리포 전체를 `CDLA-Permissive-2.0` 으로 선언하는데, CDLA 는 데이터
라이선스이므로 **이미 `scripts/` 의 코드에 부정확하다.** 병합이 만드는 문제가 아니라 드러내는
문제다.

| 경로 | 라이선스 | 파일 |
|---|---|---|
| `ontology/` `mappings/` `data/` `validation/` `queries/` `provenance/` | CDLA-Permissive-2.0 | `LICENSE.txt` (현행 유지) |
| `scripts/` `benchmark/src/` `Makefile*` `config/` | Apache-2.0 | `LICENSE-CODE.txt` (신설) |
| `docs/` `README*` `benchmark/README.md` | CC-BY-4.0 | `LICENSE-DOCS.txt` (신설) |

`pyproject.toml` 의 `license` 는 **코드 패키지의 조건**이므로 `Apache-2.0` 으로 정정하고,
데이터 조건은 README 최상단 표와 `CITATION.cff` 가 진다.

## 4. 선행 차단 — 지문 검사가 먼저다

상류 `scripts/check_public_release.py` 의 ①(KIPRIS 원문 지문 60자 대조)을 **`benchmark/` 트리
전량에 먼저 적용**한다. 위험이 몰리는 자리는 셋이다 — `tests/` 픽스처 · `analysis/typology_prompt.txt`
의 예시 · `paper/tables/*.md` 의 사례 인용. 걸리는 것은 식별자·합성 텍스트로 교체하며,
**교체가 불가능하면 그 파일은 넣지 않는다.** 순서를 뒤집으면 되돌릴 수 없다.

이어서 `ALLOW_PREFIXES` 에 `benchmark/` 를 더하고, ⑥(죽은 Makefile 참조)·⑦(죽은 문서 링크)이
새 트리에서도 통과하는지 확인한다.

## 5. 의존성 분리

```toml
[project.optional-dependencies]
benchmark = ["pyserini>=0.22", "faiss-cpu>=1.8", "boto3>=1.34", "scipy>=1.13", "matplotlib>=3.8"]
```

데이터셋 참조자: `uv sync` — **현재와 동일.** 재현자: `uv sync --extra benchmark`.

## 6. 원고 수정 (판정·수치 변경 0)

| 위치 | 현행 | 수정 |
|---|---|---|
| §6.6 "미공개와 사유" | *"평가 하네스 저장소는 공개할 경우 봉인 규율이 무효화된다"* | **삭제** — 봉인은 개봉 완료이고, 봉인을 지키는 것은 코드가 아니라 qrel 파일이다. 남는 미공개는 KIPRIS 원문·기밀 계층 둘 |
| §4.3 표 4 코드 열 | `retrieval/bm25.py::search` | `benchmark/src/retrieval/bm25.py::search` |
| §4.3 B1·P2 문단 | *"`src/` 에 해당 모듈이 없다"* | 공개 트리 기준 재진술 |
| §6.6 평가 자산 | supplementary 링크가 원고 상대경로 | 공개 리포 경로 병기 |

검증은 `make verdicts` · `make submission-check` · `make style-check` 셋 전량.

## 7. 미해결 — 승인 전에 답이 필요한 것 하나

§4.5 가 자인한 재현 결손 ①(개념 링크가 경유하는 **별칭 사전이 스냅샷에서 누락**)은 코드가
열리는 순간 *"돌렸는데 값이 안 나온다"* 가 된다. 상류 `mappings/abox_term_aliases.json` 은
전문가 A-Box 용 사전이라 **이 결손을 메우지 않는다**(실측). 처리는 둘 중 하나다 —
(가) 표면형 사전을 상류에 발행(CR 신설) (나) `benchmark/README.md` 최상단에 결손 명시.
**(가)가 가능한지 확인하기 전에는 2단계를 시작하지 않는다.**

## 7.1 실측 (2026-08-18) — 결손의 **원인이 다르다**

읽기 전용 점검을 돌렸다(스크립트: 스크래치패드 `d16_check2.py` · qrel 미개봉 · 산출물 기록 0 ·
새 실험 아님). 대상은 `sdkb-abox-patents.ttl` 의 거절특허 1,000건 중 개념 링크 보유 **977건**이며,
본문은 파이프라인이 실제로 쓰는 `ir_corpus_v09.parquet` 의 `text_main` 이다.

**① 사전은 누락되어 있지 않다.** 두 자산 모두 동결 스냅샷에 있고 `PROVENANCE.json` 에 등재돼
있으며, 공개 리포 사본과 **바이트 동일**하다 — `concept_mapping.json` md5 `d372a694…`(417,875 B) ·
`abox_term_aliases.json` md5 `c753adca…`. git 이력상 두 파일은 `5546e6e`·`2314689`(PLAN-035 ·
2026-08-01)에서 스냅샷에 들어왔다. **D-16 의 사실 기술은 그 시점 이후 낡았다.**

**② 그러나 그래프 A-Box 링크는 재현되지 않는다 — 그리고 재현되어서는 안 된다.**

| | 값 |
|---|---|
| G · 그래프 A-Box 링크 (쌍) | 2,900 |
| A · 공개 사전 재현 링크 (쌍) | 4,694 |
| 교집합 | 1,689 |
| G 재현율 | **0.5824** |
| 집합 완전 일치 | **False** |

**차이는 무작위가 아니라 CR-007 재지정 그 자체다.** G 에만 있는 상위 항목과 A 에만 있는 상위
항목이 축 단위로 짝을 이룬다 — `plasma_diagnostics`(154) ↔ `plasma_processing`(256) ·
`gas_chemistry`(143) ↔ `process_gas`(281) · `chamber_conditioning`(142) ↔ `process_chamber`(202) ·
`mask_engineering`(87) ↔ `photomask`(150) · `sio2`(188) ↔ `oxide`·`dielectric`. 이는 D-15 가
지목하고 CR-007 이 고친 **전문가용 Skill 축 별칭의 특허 프로파일 재지정**과 정확히 일치한다.

**그러므로 D-16 의 검증기준(*"링크 수·집합이 그래프 A-Box와 일치"*)은 통과할 수 없다 — 통과하면
CR-007 이 적용되지 않았다는 뜻이 된다.** 기준이 CR-007 이전에 쓰였고, 그 사이 상류가 자산을
의도적으로 바꿨다. 자원 지표만으로 검증기준을 세우면 이렇게 된다(§0.1 의 하류 지표 요구).

**③ 결손 자체는 남는다 — 이유가 다를 뿐이다.** 공개 사전으로 재현되는 것은 **O′ 세대 링크**이고
원고 §6 의 수치는 **O 세대**다. 즉 재현자는 파이프라인을 돌릴 수 있으나 **§6 의 값이 아니라 O′
값을 얻는다.** 원고 §4.5 결손 ①의 *결론*(스냅샷 단독으로 §6 의 링크를 재현할 수 없다)은 참이고,
*진술된 원인*(사전 누락)은 사실과 다르다.

**측정의 한계.** 대상은 거절특허 977건이며 코퍼스 40,552 전량이 아니다. 전량 대조는 O 세대
코퍼스가 디스크에 없어(메모리 `disk-resource-is-oprime-manuscript-is-o-arm`) 이 점검으로는
닫히지 않는다.

## 7.2 그래서 무엇을 하는가 — (가)도 (나)도 아니다

1. **원고 §4.5 결손 ① 의 원인 문구를 정정한다** — "별칭 사전이 스냅샷에서 누락" → "공개 사전은
   교정 후 세대이고 §6 의 수치는 교정 전 세대다". **판정·수치 변경 0 · 결손의 존재 불변.**
2. **`benchmark/README.md` 최상단에 세대 경고를 싣는다** — *"공개 사전으로 재현하면 O′ 세대 값이
   나오며 §6 의 값과 다르다"*. 이것이 (나)가 하려던 일의 정확한 형태다.
3. **D-16 의 검증기준을 갱신해 상류에 회신한다(C0)** — 자원 일치 기준을 폐기하고 **세대별 기대
   링크 수 + 하류 지표**로 다시 쓴다. D-16 은 "미해결"이 아니라 **"기준이 무효"** 다.
