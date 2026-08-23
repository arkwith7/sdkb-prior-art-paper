# CR-016 · 공개 재현 경로 — 비운 A-Box 를 채우는 방법을 닫는다 (D-37 · **D-38**)

> 제출처: `~/Dev/sdkb` · 양식: 상류 CLAUDE.md §2 **1단계 요구정의**
> 근거: `upstream/DEFECT-LEDGER.md` D-37·**D-38** · 원고 **§10.1·§10.2·§10.3** · 상류 Makefile·`.gitignore`
> 우선순위: **P0 — 투고 게이트**
> 작성 2026-08-09 · **2026-08-09 개정 — D-38(자산 흡수) 편입 · §4 신설**
> 상태: **상류 구현 완료(2026-08-09 · `7ef8bcf`·`835e4be`·`4ea089e`) — ①③ 통과 · ②④⑥ 대기**
> 짝: [CR-015](archive/CR-015-public-release-boundary.md)(경계) — 이 문서는 **채우는 쪽**이다

---

## 0. 한 문장

**"인스턴스는 비우고 채우는 절차를 준다"는 설계는 옳고 이미 절반 실행돼 있다 — 나머지 절반
(진입점 · 입력 출처 · CQ 스위트 · README)을 닫고, 그 절차가 **다른 리포를 거치지 않도록**
`paper_data` 의 재현 경로 자산을 흡수해 **SDKB 단독으로 성립**하게 만든다.**

---

## 1. 설계는 옳다 — 그래서 이 CR 은 방향 전환이 아니라 완성이다

상류는 라이선스 민감 인스턴스를 gitignore 로 비우고 생성기만 공개하는 설계를 이미 택했고,
실제로 대부분 그렇게 돼 있다 — `sdkb-abox-claim-features.ttl`(899 MB) · `sdkb-abox-prior-art.ttl`
(21 MB) · `sdkb-abox-b-layer-queries.ttl` · 외부 특허 본문 전량이 ignore 다. **이 방향을
바꾸자는 것이 아니다.**

문제는 **채우는 쪽에 구멍이 넷** 있다는 것이다.

| # | 구멍 | 실측 |
|---|---|---|
| **ⓐ** | 가장 큰 두 A-Box 층에 **빌드 진입점이 없다** | `grep 'prior.art\|claim.feature' Makefile` → 빌드 타깃 **0건**. 있는 것은 `abox`·`abox-patents`·`abox-b-layer-queries` 셋뿐인데, `build_abox_prior_art.py`·`build_abox_claim_features.py` 는 `scripts/` 에 실재한다 |
| **ⓑ** | 그 두 층의 **입력이 외부에 존재하지 않는다** | `.gitignore:44-46` — `data/patents/fulltext/` 를 *"re-copy from /home/arkwith/Dev/paper_data"* 로 명시. 로컬 개인 디렉터리다 |
| **ⓒ** | 원고가 공개를 약속한 **CQ 스위트가 상류에 없다** | 상류 `*.rq` = **3건**(examples/sparql) · 하류 **비공개** 리포 `queries/cq/*.rq` = **31건**. 원고 §10.1 은 *"CQ 스위트와 실행 결과"* 공개를 약속하고 §10.3 은 하류 리포를 *"공개하지 않는다"* 고 쓴다 — **모순** |
| **ⓓ** | README 에 **"무엇이 비어 있고 어떻게 채우는가"** 가 없다 | README(2026-05-17 최종) 에 A-Box·fill·empty 관련 절 0건. 릴리스 태그도 **0개**(§10.1 의 "릴리스 vX" 가 빈칸) |
| **ⓔ** | **채우는 절차가 다른 리포를 거친다** — 그리고 그 리포와의 사이에 **사본 넷**이 있다(D-38) | `sync_paper_data_assets.sh` 가 로컬 `~/Dev/paper_data` 를 요구 · 같은 자산이 양쪽에 커밋 · **`device_alias_table.json` 이 이미 갈라졌다**(sdkb 34키 ⊃ paper_data 31키 · **`eprom` 누락**) · 어휘 생성기(`build_device_vocab.py`)가 paper_data, 소비처(`add_device_nodes.py`)가 sdkb |

**T-Box 는 문제 없다.** `ontology/sdkb-core.ttl` 이 gitignore 인 것은 결함이 아니다 — 커밋된
`data/semiconductor_v0_3.json`(392 KB)에서 `make owl`·`make convert` 로 재생성되므로 공개
재현이 성립한다. 다만 **README 가 그 말을 하지 않아서** 외부인은 "T-Box 가 없는 리포"로 읽는다.

---

## 2. 요구정의

```
목적      : 빈 체크아웃 + 본인 KIPRIS 키만 가진 외부인이 논문이 인용한 그래프를
            재구성할 수 있게 만든다. 인스턴스를 공개하지 않으면서 재현을 닫는다.

입력      : Makefile (현 타깃 40여 개)
            scripts/build_abox_prior_art.py · scripts/build_abox_claim_features.py
            scripts/sync_paper_data_assets.sh (제거 대상 경로)
            .gitignore:44-46
            하류 queries/cq/*.rq 31건 · queries/shapes/
            README.md · README.ko.md · provenance/PROVENANCE.json

출력      : (1) Makefile 타깃 둘 신설 —
                  abox-prior-art        : build_abox_prior_art.py
                  abox-claim-features   : build_abox_claim_features.py
                두 타깃을 pipeline-full 계보에 배선한다.
            (2) 두 타깃의 입력 전환 — data/patents/fulltext/ 를 paper_data rsync 가 아니라
                **식별자 목록 + 재인출**로 얻는다. CR-015 의 재인출 스크립트와 같은 경로를 쓴다
                (두 CR 이 같은 수집기를 공유해야 한다 — 규칙이 둘로 갈리면 재현본이 갈린다).
            (3) CQ 스위트 이관 — 하류 queries/cq/*.rq 31건을 상류 queries/cq/ 로 옮기고
                `make cq` 로 실행·리포트한다. **왜 상류인가:** CQ 는 평가 하네스가 아니라
                온톨로지가 무엇에 답할 수 있는가의 명세, 즉 **도메인 자산**이다.
                옮기면 원고 §10.1↔§10.3 모순이 함께 풀린다.
            (4) README 에 절 신설 — "무엇이 비어 있고 어떻게 채우는가".
                층별로 (비어 있는 것 · 왜 · 채우는 명령 · 필요한 자격) 4열 표.
                **이것은 결손 고백이 아니라 설계의 진술이다** — 원고 §0.4 가 FTO 에 쓴
                "빠진 축 명세" 와 같은 형식.
            (5) 릴리스 태그 + Zenodo DOI — 원고 §10.1 의 "릴리스 vX" 와 §10.3 의
                "[최종 릴리스 후 기입]" 을 닫을 수 있게 한다.
            (6) **paper_data 재현 경로 자산의 흡수** — §4. 이관 후
                scripts/sync_paper_data_assets.sh 를 **삭제**한다(동기화할 대상이 없다).

            바뀌는 것: 빌드 배선 · 문서 · 자산 위치. **T-Box 공리·A-Box 내용은 불변.**

성공 기준 : 게이트 통과 형태로 —
            ① 빈 체크아웃 + KIPRIS 키만으로 make pipeline 이 완주하고
               T-Box 트리플 수가 원고 표(§6.1)와 일치한다
            ② 두 A-Box 타깃이 산출한 트리플 수가 하류 PROVENANCE.json 값과 일치한다
            ③ **상류에서 실행한 CQ 통과율이 하류 T3 값(em·tf·core = 1.000)과 일치한다**
               ← 하류 태스크 지표(§0.1 요구)
            ④ 원고 §10.1 이 열거한 공개 항목 전부가 태그된 릴리스에 실재한다
               (공유 T-Box · SHACL shapes · CQ 스위트와 실행 결과 · 그래프별 계수 리포트 ·
                태스크–클래스–관계–CQ 매트릭스 · 공개 가능한 A-Box 메타와 provenance)
            ⑤ make validate · make test 통과
            ⑥ **재현 경로 자산의 교차 리포 사본 0건** ·
               sync_paper_data_assets.sh 부재 ·
               sdkb 단독 체크아웃에서 재생성한 어휘가 34키이고 device:eprom 을 포함한다
               (← D-38 검증기준 ①③)
               **2026-08-09 교정**: 초판은 "동일 basename 사본 0건"이라 썼는데 그것은
               문자 그대로는 **달성 불가**다 — 실측 결과 basename 일치 31쌍 중 27쌍이
               `README.md`·`__init__.py`·`pyproject.toml` 류의 **우연한 이름 충돌**이고,
               실제 사본은 D-38 이 지목한 **넷**뿐이었다. 대상은 그 넷이다.

비목표    : 온톨로지 품질 개선 · 어휘 확장 · 성능 주장.
            KIPRIS 원문의 공개 여부는 이 CR 이 정하지 않는다 — CR-015 소관.
            하류 평가 하네스(봉인 qrel·run·게이트 코드)는 이관하지 않는다 —
            §10.3 대로 비공개 유지. 이관 대상은 CQ 뿐이다.
```

---

## 3. CQ 이관의 경계 — 무엇을 옮기고 무엇을 남기는가

| 자산 | 어디로 | 이유 |
|---|---|---|
| `queries/cq/*.rq` 31건 | **상류로 이관** | 온톨로지가 무엇에 답하는가의 명세 = 도메인 자산 |
| CQ 실행 결과·통과율 리포트 | **상류에서 생성** (`make cq`) | 자산이 상류에 있으면 결과도 상류에서 나온다 |
| `queries/shapes/delta/` | 하류 유지 | 델타 게이트는 **평가 장치**이지 도메인 자산이 아니다 |
| waiver 로그 · T-gate 판정 기록 | 하류 유지 → supplementary | 평가 하네스 산출물 |
| 봉인 qrel · run 파일 | **비공개 유지** | §10.3 |

**이 표가 §10.1↔§10.3 모순의 해소안이다.** 하류가 CQ 를 계속 쓰려면 상류 스냅샷에서 vendor
하면 되고(이미 `make vendor` 경로가 있다), 그러면 **원고가 "공개된다"고 쓴 것은 실제로 공개된
자리에 있게 된다.**

---

## 4. paper_data 흡수 (D-38) — 무엇을 옮기고 무엇을 남기는가

**결정: B(흡수) · 2026-08-09 사용자.** 근거는 **독립성**이다 — *"끊어 놓지 않으면 SDKB 단독
사용이 어렵다."* 의존(A · pinned dependency)을 택하지 않은 이유 둘: ⓐ 원고 §10.1·§10.2 가
**단일 리포 서술**이다(*"논문이 명시한 릴리스 태그를 체크아웃"*) ⓑ **사본 넷이 생긴 원인 자체가
경계가 둘이라서**다 — 경계를 줄이는 편이 재발을 막는다.

### 4.1 옮기는 것 — sdkb 가 실제로 소비하는 산출물의 생산자만

경로는 **이름이 아니라 산출물 의존**으로 뽑았다. sdkb 가 paper_data 에서 받는 것은 여섯이고
(커밋 사본 넷 + sync 둘), 그 여섯의 생산자를 역추적한 결과다.

| sdkb 가 받는 것 | 생산자 (이관 대상) |
|---|---|
| `semiconductor_industry_rejected_patents.jsonl` (canonical 1,000) | `expand_dataset_via_api.py` · `enrich_targets_b3_b5.py` · `apply_phase_c_to_canonical.py` · `merge_legacy_etch_into_semiconductor_dataset.py`(계보 보존용) |
| `rejection_decisions/structured/` (442) | `build_rejection_decisions.py` · `backfill_admin_docs.py` · `backfill_pdfinfo_v2.py` |
| `data/patents/fulltext/prior_arts` · `citation_resolution_full_cache.json` | `collect_cited_fulltext_full.py` · `collect_cited_biblio_claims.py` |
| `data/external/device_vocab/*` | **`build_device_vocab.py`** |
| `citation_norm.py` | 모듈 자체(사본 제거 · paper_data 판을 정본으로) |
| 품질·미해소 리포트 | `build_quality_profile.py` · `report_unresolved_gt.py` |

**함께 옮기는 패키지:** `src/kipris_dataset/`(6파일 — `kipris.py`·`citation_norm.py`·`cohort.py`·
`rejection_decision.py`·`dataset_paths.py`·`__init__.py`). 수집기의 본체이며, 이것 없이 위
스크립트가 서지 않는다.

**함께 옮기는 문서 다섯** (§2 출력 (4)·(6)과 짝):
`docs/semiconductor_industry_rejected_patents_schema.md`(sdkb `dataset_rejected_patents_card.md`
와 **한 쌍**) · `docs/kipris_reject_dataset_source_mapping.md`(재인출 명세의 본체) ·
`docs/private_data_handling_and_upload_policy.md`(공개될 리포에 있어야 심사자가 읽는다) ·
`docs/dataset_full_collection_runbook.md` · `docs/paper_dataset_alignment.md`.

### 4.2 남기는 것 — 옮기면 오히려 경계가 흐려진다

| 남기는 것 | 이유 |
|---|---|
| 레거시 에칭 PoC 계보 — `collect_etching_dataset.py` · `build_etching_corpus.py` · `resolve_citations.py` · `build_manifest.py` · `prototype_rejection_decision_rest.py` | 현 데이터셋의 **전신**이지 재현 경로가 아니다. 계보는 `merge_legacy_etch_*` 한 파일이 잇는다 |
| ~~`enrich_unresolved.py`~~ → **이관했다(2026-08-09 실행 중 정정)** | 이 표는 이 파일을 레거시로 분류했는데 **실물이 그 분류를 반박했다** — sdkb 의 `collect_b_layer_queries.py`(CR-012 수집기)가 `sys.path` 에 paper_data 를 끼워 넣고 이 모듈의 `_biblio`·`_extract_*` 를 임포트하고 있었다. 즉 **커밋된 스크립트가 커밋되지 않은 파일에 의존**했고, 그대로 공개했으면 외부에서 `ImportError` 로 죽는다. 982행 전부 옮겼다 |
| PTAB·PatentsView — `src/ptab_dataset/`(4) · 노트북 00·04·05·06 | 논문·SDKB 어느 쪽 산출물도 아니다 |
| **`freeze_eval_splits.py` · `eval_recall_baseline.py` · `eval_splits_v1.json`** | **평가 자산이라 sdkb 로 가면 안 된다** — 원고 §10.3(하네스 비공개)과 충돌한다. 다만 이것들은 paper_data 에도 있을 자리가 아니다(논문 리포 소관). 현 논문의 분할은 `split.parquet` 이며 **이 구 v1 분할과 다르다** — 이관하지 않되 **그 사실을 양쪽 README 에 명시**한다 |
| `data/` 291 MB 전량 | gitignore 유지 |

### 4.3 순서 — 사본을 먼저 없애고 옮긴다

> **2026-08-09 2단계 실측 셋 — 셋 다 이 절을 더 쉽게 만든다.**
> ⓐ `device_alias_table.json` 의 **공통 31키는 값이 완전히 같다** — 갈린 것은 누락 3키뿐이다.
>   따라서 sdkb 판 채택은 값을 바꾸지 않는다. 위험은 반대로 덮어쓰는 경우 하나뿐이다.
> ⓑ `citation_norm.py` 두 판의 차이는 **docstring 참조 한 줄**이고 코드는 동일하다 —
>   정본 통합이 `cited_doc_id` 정규화를 바꾸지 않는다(하류 qrel 매칭에 무영향).
> ⓒ paper_data 는 canonical jsonl 을 **커밋하고 있지 않다**(원격도 404) —
>   **공개 노출 경로는 sdkb 하나뿐**이다. 흡수는 노출을 늘리지 않는다.
>
> **그리고 CR-016 §4 가 CR-015 보다 먼저다.** CR-015 §3 출력 (2)의 재인출 스크립트가
> 흡수 대상 수집기(`expand_dataset_via_api.py` = abstract·claim1 ·
> `enrich_targets_b3_b5.py:127` = claims_full)를 호출하기 때문이다. 대기열 표의
> 번호(1=CR-015, 2=CR-016)는 우선순위이지 실행 순서가 아니다.

1. **갈라진 사본 정리 먼저.** `device_alias_table.json` 은 **sdkb 판(34키)이 정본**이다 —
   paper_data 판(31키)은 `device:diode`·`device:eprom`·`device:feram` 이 빠져 있고, `eprom` 은
   코퍼스 최빈 개념(df 5,146)이라 그 판으로 재구성하면 논문이 재현되지 않는다. **paper_data 판을
   버리고 sdkb 판을 남긴다.** 반대 방향으로 덮어쓰면 조용히 논문이 깨진다.
2. `citation_norm.py` — paper_data 판을 정본으로 옮기고 sdkb 사본 삭제. **docstring 의 문서
   참조를 실재하는 파일로 고친다**(현 sdkb 사본은 없는 문서를 가리킨다).
3. §4.1 이관 → Makefile 배선(§2 출력 (1)(2)) → `sync_paper_data_assets.sh` 삭제.
4. paper_data README 에 **"재현 경로는 sdkb 로 이관됐다"** 를 적고 개발 이력 리포로 남긴다.

**paper_data 를 공개하지 않아도 된다** — 흡수의 부수 이득이다. A(의존)를 택했다면 sdkb 공개의
선결로 paper_data 공개가 따라붙었을 것이다.

---

## 5. 하류가 확인할 것 (이 CR 이 닫힌 뒤)

1. 빈 컨테이너에서 **sdkb 만** 클론 → `make pipeline` → 성공기준 ①②⑥ (**paper_data 없이 서야 한다**)
2. `make vendor` 로 CQ 를 다시 받아 T3 통과율 대조 (성공기준 ③)
3. 원고 §10.1 목록과 릴리스 실물의 항목 단위 대조 (성공기준 ④)
4. §10.2 에 **"비운 A-Box 와 채우는 절차"** 한 줄 추가 — 강점으로 쓴다
5. 태그·DOI 를 §10.1·§10.3 에 기입 → CR-015 와 함께 §10 이 닫힌다
