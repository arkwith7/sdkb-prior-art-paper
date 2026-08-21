# PLAN-058 — 평가 하네스의 단일 리포 공개 (1단계 산출물: 허용목록 초안 · 라이선스 표)

> **상태: 완료 (2026-08-20 · 커밋 `b04fdda`) · 종결 기록은 §11.** 공개 이관 · 릴리스 · DOI ·
> 원고 §6.6 반영까지 종료되었으며 남은 항목은 없다.
> **판정·수치 변경 0 · 새 실험 0 · qrel 재개봉 0.**
>
> **아래 §0–§10 의 "초안 · 미승인" 서술은 착수 시점의 기록이며 소급 수정하지 않는다.**

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

## 8. 배치와 **내역 처리** — 무엇을 어디에 두고 그 사실을 어떻게 남기는가 (2026-08-19)

### 8.1 배치 원칙 — 복사하되 고치지 않는다

**공개본과 실행본이 한 글자라도 다르면 재현 주장이 무너진다.** 그러므로 이관은 **바이트 동일
복사**이며, 경로를 맞추려고 소스를 고치지 않는다.

이 원칙이 **패키지 이름을 결정한다.** 실측: `src/sdkb_paper/` 안의 **44개 파일**이
`from sdkb_paper.…` 형태의 절대 임포트를 쓴다. 따라서 공개 트리에서도 패키지 디렉터리 이름은
`sdkb_paper` 그대로여야 한다 — 이름을 바꾸면 44개 파일을 수정해야 하고, 그 순간 공개본은
**감사 대상 소스가 아니라 그 변형본**이 된다.

```
benchmark/src/sdkb_paper/retrieval/bm25.py     ← 원고 표 4의 `retrieval/bm25.py::search`
```

접미 경로가 원고 표 4와 그대로 일치하므로, 표의 코드 열은 **접두어 한 줄만 밝히면** 된다.

패키징은 `pyproject.toml` 에 루트를 하나 더하는 것으로 끝난다(공개 리포는 setuptools 다).

```toml
[tool.setuptools.packages.find]
where   = [".", "benchmark/src"]
include = ["config*", "scripts*", "sdkb_paper*"]
```

### 8.2 내역 3종 — 실은 것 · 뺀 것 · 논문과의 대응

**하나만으로는 부족하다.** 심사자는 *"무엇이 있나"* 만 묻지 않고 *"왜 이건 없나"* 를 묻는다.

| 파일 | 내용 | 왜 필요한가 |
|---|---|---|
| `benchmark/MANIFEST.json` | 실은 파일별 **sha256 · 출처 커밋 · 원고 참조 위치**(절·표 번호) | 공개본이 논문이 돌린 그 코드임을 기계로 대조할 수 있다 |
| `benchmark/EXCLUDED.md` | **뺀 파일 목록과 사유** — 원문 계열 · `explore/` · 구 커버리지 모듈 · 미호출 수집기 | 빠진 것이 은폐가 아니라 결정임을 보인다. 목록 없이 빠지면 누락으로 읽힌다 |
| `benchmark/CROSSWALK.md` | **원고 §4 표 4 ↔ 공개 경로 ↔ 산출 순위 파일** | 표 4가 가리키는 것을 클릭 한 번에 연다. §0.9 crosswalk 와 같은 성격이다 |

**세 파일 모두 생성기가 만든다 — 손으로 적지 않는다**(§1-7). `MANIFEST.json` 의 참조 위치 열은
원고에서 코드 경로를 grep 해 채우므로, 절 번호가 바뀌면 다시 조립할 때 따라온다.

### 8.3 검사 — 기존 두 층에 셋을 더한다

공개 리포는 이미 **생성기(`build_public_release.py`) + 검사기(`check_public_release.py`)** 두 층을
갖고 있다. 새 규율을 만들지 않고 그 위에 세 검사를 얹는다.

| | 검사 | 실패 조건 |
|---|---|---|
| **B1** | MANIFEST 대조 | 공개 트리 파일의 sha256 이 MANIFEST 와 다르다 |
| **B2** | 임포트 폐포 스모크 | `benchmark/src` 만으로 §4 모듈이 import 되지 않는다 |
| **B3** | 표 4 경로 실재 | 원고 표 4가 적은 `모듈::함수` 가 공개 트리에 없다 |

**B3 가 이 작업의 핵심이다.** 원고가 코드 경로를 적는 한, 그 경로의 실재는 **문장이 아니라 검사로**
보증되어야 한다. 절 재편으로 표 4가 바뀌면 B3 가 먼저 깨진다.

**B2 는 원문 없이 돈다.** 데이터가 없어도 임포트와 결정성(시드·정렬)은 검증되므로, 공개 CI 에서
KIPRIS 원문 없이 돌릴 수 있는 유일한 층이다.

### 8.4 동기화 정책 — 공개본은 파생물이다

- **공개 리포에서 직접 편집하지 않는다.** 고칠 것이 있으면 논문 리포에서 고치고 다시 생성한다.
- **태그에 얼린다.** 논문이 인용하는 것은 `v1.1-paper` 태그이며, 그 이후의 개선은 다음 태그로 간다.
- **이 규칙의 근거는 실패 사례다** — 같은 자산의 사본이 두 리포에 갈려 최빈 개념이 한쪽에서
  빠졌던 D-38 이 정확히 "양쪽에서 편집"의 결과였다.

### 8.5 코드를 공개해도 재현되지 않는 것 (README 최상단에 싣는다)

1. **KIPRIS 원문** — 재배포 불가. 식별자와 재인출 절차로 대체한다.
2. **세대 차이** — 공개 사전은 교정 후 세대이므로 원고 §6 의 값이 아니라 O′ 값이 나온다(§7.1).
3. **하이브리드 산출물의 바이트 재현성** — 기록 순서 의존. 내용 동등성으로 검증한다.

**셋을 먼저 밝히는 것이 재현성을 낮추지 않는다** — 재현자가 나중에 발견하는 것과 리포가 먼저
말하는 것은 심사에서 다르게 읽힌다.

## 9. P0 진행 기록 (2026-08-19)

**완료 — §6.6 자기모순 제거.** "평가 하네스 저장소는 공개할 경우 봉인 규율이 무효화된다" 절을
삭제했다. 봉인은 개봉 완료이고, 같은 절이 qrel 식별자를 공개 대상으로 이미 선언하므로 이 사유는
성립하지 않았다. 검사 3종 통과 · 판정·수치 변경 0.

**보류 둘 — 사실이 된 뒤에 쓴다.**

| 항목 | 왜 지금 쓰지 않는가 | 언제 쓰는가 |
|---|---|---|
| 하네스를 §6.6 **공개 목록**에 추가 | 아직 이관되지 않았다. 원고가 미래를 약속하면 그 문장은 투고 시점에 거짓일 수 있다 | `benchmark/` 이관 완료 커밋에서 |
| 스냅샷 인용을 **공개 태그**로 교체 | 태그가 아직 없다 | 태그 발행 후 |

**갈래 확인 (2026-08-19 실측).** `~/Dev/sdkb` = `semiconductor-knowledge-base`(비공개 상류) ·
`sdkb-dataset` = 그 공개 트리(`build_public_release.py` 산출). 상류에서 `d578bf3` 는 정상
해석되므로, 결손은 "해시가 틀렸다"가 아니라 **"심사자가 볼 수 없는 이름공간의 해시를 인용한다"** 이다.
따라서 PROVENANCE 확장은 공개 리포 직접 수정이 아니라 **상류 생성기 변경**이며, 상류 CLAUDE.md
§2 의 5단계 정지 게이트를 탄다(메모리 `session-may-act-as-upstream-sdkb`).

### 9.1 P0 완료 · 태그 연기 (2026-08-19)

**상류 `3372d7b`** — 무결성 기록을 자산 **1건 → 195건**으로 넓혔다(`scripts/build_provenance.py`).
해시는 **공개 트리의 바이트**로 잰다. 승인 설계는 "허용목록에 걸리는 추적 파일"이었으나, 2단계
관찰에서 공개본이 복사되며 변형된다는 사실이 드러나(사설 블록·죽은 링크·원문 스크럽·절대경로)
원본 해시를 실으면 심사자가 계산한 값과 어긋남이 확인되어 대상 트리를 바꿨다.

부수로 `make public-release` 가 기본값 `PYTHON=python3` 에서 `$(CURDIR)/python3` 를 만들어
완주하지 못하던 결함을 고쳤다. **어휘·IRI·T-Box·shape 변경 0 · 하류 재측정 불필요(§2.1 미발동).**

**태그 `v1.1-paper` 는 `benchmark/` 이관 후로 연기한다(2026-08-19 사용자 결정).** Zenodo 는
릴리스 시점의 리포 전체를 보관하므로, 지금 끊으면 **평가 코드가 빠진 판이 DOI 로 영구 고정**되고
논문이 인용할 판과 심사자가 받는 판이 갈린다. 순서는 다음과 같다.

```
지문 검사 → benchmark/ 이관 → Zenodo 연결 → 태그 v1.1-paper → Release 발행 → DOI
→ CITATION.cff 갱신 → 원고 §6.6 (공개 태그 + Version DOI · 하네스를 공개 목록으로)
```

## 10. 지문 검사 결과 (2026-08-19) — 원문은 0건, 그러나 셋이 걸렸다

스테이징 트리 **117 파일**(코드 74 + 표 20 + supplementary 5 + 결함행렬·런셋·임계 등)에 상류
`check_public_release.py` 를 적용했다. 판정 근거는 KIPRIS 비공개 정본에서 뽑은 **지문 3,341개
(고유 2,322)** 다.

### 10.1 통과 — KIPRIS 원문 **적중 0건**

**코드 74 파일 · 결과표 20 · supplementary 5 어디에도 특허 원문이 없다.** 사전에 위험지로 지목한
셋(테스트 픽스처 · `typology_prompt.txt` · 표의 사례 인용) 모두 무적중이다. 이관의 가장 큰 위험은
해소되었다.

### 10.2 차단 — 홈 절대경로 **218건**

| 파일 | 건수 |
|---|---|
| `fault_matrix.json` | 126 |
| `fault_matrix_holdout.json` | 72 |
| `fault_matrix_n03.json` · `fault_matrix_n03adv.json` | 각 9 |
| `fault_baseline.json` · `ir_effort_test.md` | 각 1 |

경로의 뿌리는 **217건이 `…/sdkb-foresight-paper`** 다. 즉 격리 산출물의 실행 경로가 값이 아니라
흔적으로 남았고, 그 흔적이 **이 저장소의 옛 이름을 노출한다.** 처리는 발행 시 경로를 상대화하는
변환 단계이며, 상류 `scrub_abs_paths` 가 이미 그 일을 한다 — `wants_abs_scrub` 의 대상에
`benchmark/assets/` 를 더한다. **JSON 값 자체는 건드리지 않는다**(경로 문자열만 치환).

### 10.3 차단 — 옛 리포 슬러그 2건 · 죽은 문서 링크 2건

| 파일 | 내용 | 처리 |
|---|---|---|
| `config.py` · `ontology/vendor.py` | 비공개 상류 슬러그 `semiconductor-knowledge-base` 1회씩 | **허용목록 등재**(사유: 스냅샷 출처 기록). 소스를 고치면 §8.1 "복사하되 고치지 않는다"가 깨진다. 상류도 `config/namespaces.py` 를 같은 이유로 예외 처리한다 |
| `S6-preregistration-crosswalk.md` | `../논문_v0_9_SDKB_통합초안.md` · `../verdicts.yaml` | 정본 링크는 **평문화**. `verdicts.yaml` 은 판정 SSOT 이므로 **함께 싣는 편이 낫다** — 심사자가 판정 문구의 출처를 직접 볼 수 있다 |

### 10.4 남은 확인 — 아직 검사하지 못한 것

qrel·분할 **식별자 CSV** 는 변환기가 없어 스테이징에 포함되지 않았다. 원문 0열이 설계상 보장되나
**변환 후 같은 검사를 다시 돌린다** — 검사하지 않은 것을 통과로 세지 않는다.

---

## 11. 공개 완료 (2026-08-20)

| 단계 | 결과 |
|---|---|
| 지문 검사 | KIPRIS 원문 적중 **0건** · 절대경로 218 → 0 · 슬러그 2건 허용목록 · 죽은 링크 2건 평문화 |
| `benchmark/` 이관 | **127 파일** · 코드 74 는 원본과 **바이트 불일치 0** |
| 무결성 기록 | `PROVENANCE.json` 자산 1 → **324건**(공개 트리 바이트 기준) |
| 라이선스 | 데이터 CDLA-Permissive-2.0 · 코드 Apache-2.0 · 문서 CC-BY-4.0 |
| 릴리스 | `v1.1-paper` → 공개 커밋 `9847929` |
| DOI | version **10.5281/zenodo.22030396** · concept **10.5281/zenodo.22030395** |
| 원고 §6.6 | 재현 기준을 비공개 커밋 `d578bf3` → 공개 릴리스 + version DOI 로 교체 · 하네스를 공개 목록으로 |

**Zenodo 1차 아카이빙은 실패했고 원인은 메타데이터였다.** `CITATION.cff` 의 `orcid: ""` 는
CFF 1.2.0 스키마 위반이고, 이중 라이선스를 단일 식별자로 선언하고 있었다. `.zenodo.json` 을
신설해 파싱 모호성을 없애고 라이선스는 `other-open` + 본문 명시로 바꾼 뒤 재발행하여 성공했다.

**태그는 다시 끊지 않는다.** DOI 배지·CHANGELOG 확정은 태그 이후 커밋이며, 재발행하면 새
version DOI 가 발급되어 원고 §6.6 이 가리키는 값이 무효가 된다. 아카이브가 배지를 포함하지 않는
것은 DOI 발급의 선후 관계상 정상이다.

**남은 것.** 없음 — M5 가이드의 P0·P1·P2 전량 종료.
