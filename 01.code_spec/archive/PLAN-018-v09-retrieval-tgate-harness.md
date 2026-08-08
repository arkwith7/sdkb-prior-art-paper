# PLAN-018 — v0.9 검색 시스템·T-gate·Ablation 하네스 (계층 B 설계·사전등록)

> **📦 아카이브됨 (2026-08-08 · 사용자 지시). 인용 가능 · 재승인 대상 아님.**
> **여기 있다고 계약이 죽은 것이 아니다** — F1–F18 동결은 **여전히 현행 코드의 계약**이고
> `src/` 다수 모듈·테스트가 이 문서의 §7 을 근거로 돈다. 내린 이유는 하나다: **이 계획은
> 실행이 끝났고**(M2–M4 완주 · 확증분할 T-gate 실행 완료) 더 진행할 단계가 없어 `plans/` 의
> "지금 하는 일" 목록에 오래 머물렀다. **F1–F18 을 바꾸려면 이 문서를 고치는 것이 아니라
> 새 사전등록을 쓴다**(CLAUDE.md §1-3).

> **상태: 승인 (2026-07-26 사용자) 🟢 · M2 착수 가능.** F12 확정: Titan v2 주-팔, PaECTER는 결과분석 후
> 선행연구 비교 필요 시 추가(§11.2). F8 확정: 원고 Claim-only 주분석(코드가 원고에 정합).
> PLAN-017(데이터셋 B)의 후속. PLAN-017 §6이 "후속 PLAN"으로 미룬 **검색 시스템·T-gate·결함주입·
> ablation** 전량을 설계·사전등록한다. 이 문서는 **결과를 보기 전에 동결하는 사전등록**이다
> (CLAUDE.md §2 Phase 3 · 규칙 #3 · 원고 §5.6·부록 A). 동결 후 결과를 보고 임계·모델·가중치를 바꾸지 않는다.
> 정본 원고 [paper/논문_v0_9_SDKB_통합초안.md] §4.5–4.10·§5 를 구현으로 옮긴다 — 방법은 원고가 정본.
> 관련: [PLAN-017](../archive/PLAN-017-v09-ir-benchmark-dataset.md) · [SPEC-007](../specs/SPEC-007-ir-corpus-asbuilt.md) ·
> [SPEC-001](../specs/SPEC-001-validation-gate.md) · 메모리 `pivot-v09-retrieval-primary-task`.

---

## 0. 목적과 스코프

**목적:** 조립된 IR 코퍼스(SPEC-007 · 40,552문서·qrel 2,416엣지) 위에 **선행기술 검색 하네스**를 세워
C2(핵심증명)·C3(진화안전)의 미측정 산출물 — Recall@100·nDCG·T-gate·ablation·결함주입 매트릭스 — 을
**검정 가능한 수치로** 만든다. 지지 축: **RQ2(H3 검색 유용성)·RQ3(H4 계층 기여·H5 음성대조군)·
RQ1(H1 게이트 판별력·H2 승인 안전성 = T1/T2/T3)**.

**계층 경계(PLAN-017 §6 재확인):**
| | 다루는 것 | 위치 |
|---|---|---|
| PLAN-017 (계층 A · 데이터) | 코퍼스·qrel 조립(완료) + B2 family·B8 분할·B5 graded qrel·B4 hard neg·B6 누출차단(잔여) | `corpus/`·`validate/leakage_check` |
| **PLAN-018 (계층 B · 검색·게이트)** | **B0–B5·P0–P2 검색 · 순위함수 · T1/T2/T3 · 결함주입 · ablation A1–A8 · 평가·통계** | `retrieval/`·`validate/`·`analysis/` |

**fail-fast 첫 관문(PLAN-017 §4에서 승계):** M2 = **누출 없는 BM25 Recall@100 진입 임계치**. 이 수치가
비공허(정답을 실제로 회수)임이 확인되기 전에는 초록·기여를 확정하지 않고 하류(Dense·Hybrid·T-gate)를
착수하지 않는다.

---

## 1. 사전등록 동결 파라미터 (테스트 개봉 전 고정 · 결과 보고 바꾸지 않음) 🔒

> 원고 부록 A(사전등록 체크리스트)·§5.6과 정합. **이 표가 p-hacking 방지의 계약이다.** 값 변경은
> 사전 동결된 민감도 격자로만, 커밋 해시로 증거를 남긴다(CLAUDE.md 규칙 2·3).

| # | 항목 | 동결값 | 출처·근거 |
|---|---|---|---|
| F1 | **주 지표** | family-level Recall@100 | 원고 §5.1 |
| F2 | 비열등 마진 ε | **0.02** | 원고 §4.9·CLAUDE §5 |
| F3 | 하위집단 마진 δ | **0.05** | 원고 §4.9·CLAUDE §5 |
| F4 | 부트스트랩 | paired, **10,000회**, 95% CI, 질의 단위 | 원고 §5.2 |
| F5 | 결함검정 | 결함 단위 대응 **McNemar** | 원고 §5.2 |
| F6 | 다중비교 보정 | **Holm** (ablation A1–A8) | 원고 §5.2 |
| F7 | 효과크기 | 평균차 + **Cliff's delta** + 질의별 승/패/동 | 원고 §5.2 |
| F8 | 주 질의 표현 | **Claim-only(독립항, 불완전 시 청구항1+제목·초록 보조)** | 원고 §4.2. ⚠️SPEC-007과 대비 — §11.1 |
| F9 | 시점 분할 | filingDate 정렬 **60/20/20** + **family-disjoint** · **경계 train/dev=2016-11-21·dev/test=2021-07-21 동결(2026-07-27)** · test 봉인 | 원고 §4.3·PLAN-017 B8 |
| F10 | 후보 컷오프 | \(t_{pub}(d) < t_{cutoff}(q)\)(=출원일) ∧ \(family(d)\neq family(q)\) | 원고 §4.4 |
| F11 | low-overlap 정의 | **개발셋 분포 하위 사분위**, 형태소/char n-gram Jaccard(불용어 제거) — 결과 보고 정하지 않음 | 원고 §5.3 |
| F12 | Dense 모델 | **Titan Embed Text v2(`amazon.titan-embed-text-v2:0`)** 다국어 주 · PaECTER 영어-피벗 보조(선택) | PLAN-017 §8.1. ⚠️원고 §4.6과 대비 — §11.2 |
| F13 | 토큰화 | BM25 주=**nori `KoreanAnalyzer`(DecompoundMode.NONE) + SDKB 온톨로지 어휘 사용자사전**(전 시스템 동일 적용 토큰화 계층·ablation 밖) · **Kiwi=§5.3 민감도 비교자** · standard(EN)·언어별 색인 후 RRF | PLAN-017 §8.3 · §11.6 결정(2026-07-26) |
| F14 | CQ 스위트 분할 | **pa / em / tf / core** — T3 감시 대상 = em·tf·core | 원고 §4.9·CLAUDE §5 |
| F15 | 결함주입 유형 | 원고 §4.10 표 12종 · 강도 1%/5%/10% · 반복 `[동결후 기입]`회 | 원고 §4.10 |
| F16 | 결정성 시드 | 분할·부트스트랩·hard neg 샘플링 시드 = **`config.SEED`(고정)** | 원고 §5.6 |
| F17 | 3모드 분리 | Oracle-free(주) / Citation-assisted(보조) / GT-assisted(상한) 산출 분리 저장 | 원고 §4.5 |
| F18 | 가중치 w | **개발셋에서만** 학습 또는 사전 격자 선택 · 테스트 qrel 최적화 금지 | 원고 §4.7 |

**미결 동결값 3종은 M2 착수(데이터 감사) 시 확정하고 이 표를 갱신한다:** F9 경계·F15 반복수·F11 정확한
n-gram 파라미터. 확정 시점은 **테스트 개봉 이전**이어야 하며 커밋으로 스냅샷을 남긴다.

---

## 2. 모듈 배치 (CLAUDE.md §3 배치표 준수 · 시그니처)

```
retrieval/                  ── 순위 산출만 (평가·게이트 없음)
  bm25.py         build_index(corpus_df, lang) · search(qids, k) → run(qid→[(doc_id,score)])
  dense.py        embed(texts)→np[N,1024](Titan·캐시) · FaissFlat.search(q_emb,k) → run
  hybrid.py       rrf(runs:list[run], k, c=60) → run          # Pyserini HybridSearcher 대안 자체 RRF
  ontology_rerank.py  concept_overlap·path_sim·feature_cov·ground_compat → rerank(run, features) → run
  candidate.py    D_q(qid): 시점유효·family-disjoint 마스크(pandas) + hard-neg 병합
  systems.py      B0–B5·P0–P2 조립(§3) — 각 시스템 = run 생성 레시피
validate/                   ── L0–L3 + T-gate + 감사 (데이터 수정 없음)
  leakage_check.py   금지간선/파생피처 마스킹·잔여 0 검증 (PLAN-017 B6 · 원고 §4.5·5.6)
  t1_noninferiority.py  LB95(ΔR100) > −ε           (원고 §4.9 T1)
  t2_subgroup.py        max_s Drop_s < δ (거절근거·공정·KR/외국) (T2)
  t3_cross_task_cq.py   ∀f∈{em,tf,core}: pass_f(new) ≥ pass_f(old) — 결정론적 (T3)
  tgate.py              Accept = L0–L3 ∧ T1 ∧ T2 ∧ T3 (원고 §4.9 승인식)
  fault_inject.py       §4.10 12종 결함 × 강도 주입 → 결함 그래프 (검출매트릭스 입력)
analysis/                   ── 검정·효과크기 (그림 없음)
  metrics.py      recall@{50,100,500}·success·mrr·ndcg@20·bpref·set_recall·feature_cov (원고 §5.1·4.8)
  bootstrap.py    paired_bootstrap(runA,runB,qrel,n=10000,seed) → (Δ, LB95, UB95)
  ablation.py     A1–A8 계층 제거 → ΔRecall + Holm 보정 (원고 §5.4)
  subgroup.py     거절근거·공정군·KR/외국 하위집단 분해 (원고 §5.2·5.3)
  faults.py       결함 × 게이트층 검출 매트릭스 + McNemar (원고 §4.10·5.2)
viz/figures.py    C2/C3 그림 신설 (성능표·ablation·검출매트릭스·CQ추이) — B7후속 경로 재라벨 동반
```

- **경계 계약(통합테스트로 강제):** `retrieval/`는 qrel을 읽지 않는다(누출) · `analysis/`는 순위를 만들지
  않는다 · `validate/tgate`는 게이트 우회 경로를 만들지 않는다 · 3모드 산출은 분리 저장.
- 신규 술어·어휘 발명 0(CLAUDE §1.6). 개념·경로 피처의 원천은 `ontology/`·SPEC-007 `concepts` 컬럼.

---

## 3. 검색 시스템과 순위 함수 (원고 §4.6·4.7)

### 3.1 비교 시스템 (원고 §4.6 그대로)
| ID | 시스템 | 증거 | 구현 |
|---|---|---|---|
| B0 | BM25-Claim | 청구항 어휘 | `bm25`(claims_full) |
| B1 | BM25-Fielded | 제목·초록·청구항 | `bm25`(q_repr_title_abstract_claims 필드) |
| B2 | Dense | Titan v2 임베딩 | `dense`(text_main) |
| B3 | Text Hybrid | BM25+Dense RRF | `hybrid([B0/B1, B2])` — **가장 강한 텍스트 기준선** |
| B4 | CPC/IPC | 분류 겹침·거리 | `ontology_rerank`(ipc/cpc만) |
| B5 | Ontology-only | 개념 경로 단독 | `ontology_rerank`(concepts, 텍스트 0) |
| P0 | Text+Ontology | B3 + 개념겹침·경로 | **핵심 제안** |
| P1 | +ClaimFeature | P0 + 한정요소 포괄 | FeatureCoverage 항 |
| P2 | +Ground-aware | P1 + 거절근거 호환(oracle-free 범위) | GroundCompatibility 항 |

### 3.2 순위 함수 (원고 §4.7)
`S(q,d) = w_b·B̃M25 + w_e·c̃os + w_c·ConceptOverlap + w_h·PathSim + w_f·FeatureCoverage + w_r·GroundCompat`
각 항 질의별 [0,1] 정규화 · 가중치 **개발셋 학습/사전격자만**(F18) · 항별 기여·일치개념 기록(설명가능성).
- ConceptOverlap = 공정·소자·재료·장비·고장 개념 가중 Jaccard(`concepts` 컬럼)
- PathSim = 온톨로지 최단경로/정보량 유사도(T-Box 계층)
- FeatureCoverage = 질의 독립항 ClaimFeature 중 후보 포괄 비율(sidecar)
- GroundCompatibility = 거절근거 호환(oracle-free: 질의 rejectedFor 제외 설정에서 배제 — §4.5.1)

---

## 4. 3모드 누출 통제 (원고 §4.5 · PLAN-017 B6)

| 모드 | 허용 | 배제 | 역할 |
|---|---|---|---|
| **Oracle-free(주)** | 질의 이전 공개 문서·언어중립 개념 | 질의 `hasPriorArtExaminer/hasPriorArt/overPriorArt`·qrel 파생 개념·`NoveltyScore`·(설정 시)`rejectedFor` | 배포가능 주 결론 |
| Citation-assisted(보조) | 질의 이전 타 특허 인용망 | 질의 자체 인용 | 역사적 인용 활용 설정 |
| GT-assisted(상한) | 심사관 GT 한정요소·거절근거 | — | "완전 정렬 상한"(성능주장 금지) |

`leakage_check`가 마스킹 후 금지간선 0을 자동 강제(원고 §5.6). SPEC-007 §7이 코퍼스 컬럼에 파생값 0을
이미 검증 — leakage_check는 **런타임 피처 생성 시점**의 잔여를 재검증한다.

---

## 5. T-gate와 결함주입 (원고 §4.9·4.10 · SPEC-001 T-gate 절)

### 5.1 승인식 (원고 §4.9 · CLAUDE §5)
`Accept(ΔG) = 1[L0=L1=L2=L3=pass] · 1[LB95(ΔR100)>−ε]_T1 · 1[max_s Drop_s<δ]_T2 · 1[∀f∈{em,tf,core}: PassRate_f(new)≥PassRate_f(old)]_T3`
- T1 = 비열등성 검정(H0: Δ≤−ε, H1: Δ>−ε) · ε 검정력과 독립 사전등록(F2)
- T2 = 거절근거·공정·**KR/외국 언어** 하위집단, 최소 질의수 충족 시만 차단 규칙
- T3 = **통계검정 아님, 결정론적 통과율 비교** · 하락 시 즉시 실패 · 예외는 waiver 토큰(횟수 보고)

### 5.2 결함주입 검출 매트릭스 (원고 §4.10 · H1 직접 검정)
12종 결함 × 강도(1/5/10%) × 반복 → 각 결함이 **어느 층에서 검출되는가** 매트릭스. 핵심 = 마지막 2종
교차결함(동의어 오병합·공유 계층 역전)이 **L0–L3·T1·T2 통과 후 T3에서만** 검출되면 H1 지지. McNemar로
층간 검출률 비교. 위양성률(정상 델타 오거부) 병행 보고. T3 미검출 시 CQ 스위트 느슨 → 세분화 후 재실행(부록 F).

---

## 6. 평가·통계 (원고 §5)

- **주 지표** family Recall@100(F1). 보조: Recall@{50,500}·Success@K·MRR@K·nDCG@20(등급2 부분집합)·
  bpref·Candidate Reduction·지연/인덱스/메모리(운용은 탐색적 강등).
- 신규성/진보성 분리(§4.8): Single-ref Feature Coverage·Set Recall@K·Set Feature Coverage@K·Min Evidence Set.
- 통계: F4–F7. H3 조건부 = 어휘중첩 사분위 × 시스템 상호작용(F11). 소표본 하위집단 확정결론 금지.
- 전문가 판정(§5.5): 50질의 층화 × 상위 미인용 5 = 최대 250쌍, 2인 블라인드, Cohen's κ. **미룸 — M5 선택**
  (인적 자원 필요 · κ<0.4 시 부록만). 자동 파이프라인 밖 결정.

---

### 6.1 M2 착수 실측 발견 (2026-07-26 · 토큰화 기반 구축)
- **아키텍처 확정:** nori·Kiwi를 **사전토큰화기**(`retrieval/tokenize.py`)로 두고 whitespace 색인 →
  §5.3 토큰화 교체가 색인 파이프라인 무변경. jnius는 **`pyserini.pyclass.autoclass`**(fatjar 클래스패스
  등록)로만 Lucene 클래스 접근 가능(순수 jnius.autoclass는 NoClassDefFound). stopTags=
  `KoreanPartOfSpeechStopFilter.DEFAULT_STOP_TAGS`(30종).
- **★ 사용자사전 필수성 실증:** nori는 OOV 외래어('플라즈마')를 **문맥의존적으로** 분절한다 — 질의
  '플라즈마'→[플라] vs 문서 '플라즈마 식각'→[플라,식각], '플라즈마 공정'→[플,라즈,마]. 입력 동일 시
  결정적(F16 안전)이나, **질의·문서 토큰이 문맥 따라 어긋나 BM25 매칭 훼손** → SDKB 어휘 사용자사전이
  선택이 아니라 정확성 요건(F13 강화). M2 B0에서 userdict 적재를 색인 전 필수 단계로 둔다.
- **테스트 실측(반도체 문장):** nori(NONE)+DEFAULT_STOP_TAGS = 조사 제거·'반도체'/'식각' 보존·'플라즈마'
  OOV파편 · Kiwi = '플라즈마' 보존·'식각'→'식/각' · en = Porter 스테밍('etch','oxid').

### 6.2 SDKB 사용자사전 = 정식 스펙 산출물 (다음 세션 M2 B0 · 사용자 지시 2026-07-26)
> 사용자사전은 F13의 정확성 요건(§6.1 실증)이자 **재현성 대상 스펙**이다. 다음 규율로 만든다:
> - **최대 용어 추출:** SDKB 온톨로지에서 반도체 도메인 어휘를 **되도록 많이** 끌어온다 — 공정·소자·
>   재료·장비·고장(FailureMode) 클래스 인스턴스의 한국어 prefLabel·altLabel, 개념 라벨, 나아가 청구항
>   ClaimFeature·기술노드 등 도메인 표층형까지. 빈약한 사전은 §6.1의 OOV 파편화를 남긴다.
> - **정식 문서화(01.code_spec):** 어떤 반도체 용어가 형태소 분석기 사용자사전으로 정의됐는지 **검증
>   가능하도록** as-built SPEC(가칭 **SPEC-008 · nori 사용자사전 인벤토리**)으로 남긴다 — SPEC-006/007과
>   같은 규율(출처·건수·서명·재측정 스크립트·표층형 표본). 산출 사전 파일 = `config.IR_USERDICT`.
> - **누출 안전:** 도메인 어휘(공정·소자명)만 — qrel 파생·정답 유래 표층형은 넣지 않는다(§4 누출).
> - **적용 대칭:** 질의·문서·전 시스템(B0–P2)에 동일 사전으로 사전토큰화(§6.1 아키텍처).

#### 6.2.1 사전등록 동결 — 어휘 원천·수확 규칙 (2026-07-26 M2 착수 관찰 후 확정 · 테스트 개봉 전) 🔒

> **관찰 결과(2026-07-26 실측):** SDKB 온톨로지의 통제어휘 prefLabel 은 **전량 영어**이고 한국어
> 표층형은 도메인 클래스 altLabel ~88개(Device 27·Material 22·SubProcess 19·Skill 11·Process 5·
> FailureMode 4)에 그친다. 정작 §6.1 이 파편화로 지목한 OOV 외래어 **'플라즈마'는 온톨로지 라벨에
> 부재**(785회 전부 특허 본문). 온톨로지·매핑만으로는 §6.1 문제를 못 덮으므로, 사용자 결정(2026-07-26)
> 으로 **누출-안전 코퍼스 수확 원천을 추가**한다. 이 §6.2.1 은 §6.2 의 "정답 유래 표층형 배제"를
> **문서-일반 빈도 규율로 명시 확장**한 사전등록 개정이며, 결과(Recall)를 보기 전 커밋으로 동결한다.

| # | 항목 | 동결값 |
|---|---|---|
| U1 | 원천 A · 온톨로지 통제어휘 | 벤더 스냅샷 `data/external/sdkb/*.ttl` 의 **도메인 클래스 14종**(Process·SubProcess·Device·Material·Equipment·EquipmentClass·EquipmentModel·FailureMode·RootCause·Mitigation·Skill·Parameter·Metrology·TechnologyNode) 의 `skos:prefLabel`(en)+`skos:altLabel`(ko·en) |
| U2 | 원천 A · 배제 클래스 | Patent·CitedPatent·RejectedPatent(제목=정답유래)·Expert(인명)·**Organization·Vendor(회사명 — 사용자 결정 2026-07-26 제외)**·TBox/governance 전부 |
| U3 | 원천 B · 동결 매핑 CSV | `term_aliases.csv`(`term` 열 전량) · `si_concepts.csv`(`variant`) · `dart_terms.csv`(`pattern`) — `\|` 분리·정규식메타(`\b`,`?`) 제거·`AND`/`OR` 논리토큰 제거 후 표층형. JEDEC/SEMI/IRDS/DART 준거·frozen-2026-07-13·qrel 비유래 |
| U4 | 원천 C · 코퍼스 수확 | `IR_CORPUS.text_main`(질의+후보 **대칭**) 을 **Kiwi**(nori 무관 중립 후보생성기)로 토큰화, 태그∈{SL 외래어, NNG 일반명사}·길이≥2 |
| U5 | 수확 채택 조건 (전부 충족) | (a) **문서빈도 df(T) ≥ 30**(≈40k 중 — 문서-특정 아닌 도메인-일반 보증 = 인용쌍 정보 0의 누출 가드) · (b) **nori(NONE·무사전)가 T 를 ≥2 토큰으로 파편화하거나 ∅ 처리**(nori 가 이미 아는 단어는 불필요) · (c) 고유명 배제: Kiwi NNP·회사명 스톱리스트(Org/Vendor 라벨)·특허 `title` 토큰 제외 |
| U6 | 수확 상한 | df 내림차순 **HARVEST_MAX = 2000**(초과 시 절단 건수 SPEC-008 에 보고 — 무언절단 금지) |
| U7 | 출력 형식 | nori `UserDictionary` — **공백 없는 표층형** 1줄1항(공백 포함 다어절은 nori 단일토큰 불가 → 제외·건수 보고, 공백제거 변이는 altLabel 에 이미 존재) · dedup·정렬·UTF-8 · `#` 주석 헤더에 출처·건수·서명 |
| U8 | 산출·문서화 | `config.IR_USERDICT` 생성 + **SPEC-008(nori 사용자사전 인벤토리)** as-built(SPEC-006/007 규율: 출처·건수·서명·재측정 스크립트·표층형 표본·수확어 전량 검증가능) |

- **적용 대칭 재확인:** 이 사전은 질의·문서·전 시스템 동일 사전토큰화 계층(ablation 밖·기준선 보강 = 온톨로지팔 이득 보수적 하향).
- **결정성:** 수확은 코퍼스 서명(SPEC-007 `ec5ea51b`)·Kiwi/nori 버전에 결정적. df·상한은 이 표로 동결 — 결과 보고 바꾸지 않는다(CLAUDE §1.2·1.3).

## 7. 마일스톤 (fail-fast · 각 후 게이트)

```
M2 진입 임계치   B6 leakage_check → B2 family → B8 분할 → make index → BM25 Recall@100
                 ▶ 비공허 확인(PLAN-017 §5 성공기준5). 실패 시 상류 진단, 하류 착수 금지.
M3 텍스트 기준선  B2 Dense(Titan) → B3 Hybrid(RRF) → metrics·bootstrap → B0–B3 성능표
M4 온톨로지·제안  B4/B5·P0/P1/P2 순위함수 → ablation A1–A8 → subgroup → RQ2/RQ3 표
M5 게이트·결함    T1/T2/T3 배선 → fault_inject 12종 → 검출매트릭스·McNemar → RQ1 표
                 → figures 신설(C2/C3) + B7후속 경로 재라벨
```

- M2가 PLAN-017 §4 진입 임계치를 흡수 — **여기서 초록·기여 확정 해금**.
- 각 마일스톤은 CLAUDE §2 5단계 압축 적용. 데이터/통계/게이트 변경엔 예외 없음(요구·설계 재승인).

### 7.1 M2 진입 임계치 — **통과(2026-07-26 실측)** ✅

> **fail-fast 관문 통과: BM25 단독으로 심사관 인용 선행기술을 비공허하게 회수한다.** 하류(Dense·
> Hybrid·온톨로지·T-gate) 착수 해금 · 초록·기여 확정 해금.

- **구성:** B0 · 문서=`text_main`(초록+청구항 · SPEC-007 주 색인 텍스트) · 질의=`claims_independent`
  (F8 Claim-only 독립항) · nori(NONE)+SDKB 사용자사전(SPEC-008 · 275 표층형) 사전토큰화 → Lucene
  `-pretokenized` whitespace 색인 · BM25(k1=0.9·b=0.4 Anserini 기본) · 자기검색 제외.
- **결과(문서수준 · 매크로 · 정답≥1 질의 981):**

  | K | Recall@K | Success@K |
  |---|---:|---:|
  | 10 | 0.1422 | 0.2579 |
  | 50 | 0.2317 | 0.3976 |
  | **100** | **0.2800** | **0.4659** |
  | 500 | 0.4204 | 0.6218 |
  | 1000 | 0.4681 | 0.6789 |

  MRR 0.1447. 색인 40,491문서(빈 text_main 61 제외) · run `data/processed/ir/runs/bm25_b0_claim.txt`.
- **해석:** Recall@1000 이 ~0.47 에서 포화 — 정답의 en 39%·ja 4%(SPEC-007 §6)가 한국어 BM25 로
  도달 불가한 상한(≈57% 한국어)과 정합. 이 교차언어 격차가 **언어중립 개념 온톨로지팔이 가치를
  증명할 무대**(원고 H2b) — M4 에서 측정.
- **경계·미포함(정직 보고):** 이 진입 수치는 **문서수준**(family 집계 이전 · F1 주지표 family Recall@100
  은 B2 family 그룹핑 후 M3) · 시점유효(F10)·family-disjoint 마스킹 미적용(정답은 정의상 시점선행이라
  recall 측정에 무해) · 3모드 중 oracle-free 주모드. 재현: `make index && make eval`.

### 7.2 M3 진행 — B2 family + F1 주지표 성립 (2026-07-27) 🟢

> **주지표(family-level Recall@100)가 성립했다.** B2 family 그룹핑의 선행조건 — 정답 문서의
> DOCDB family_id 결측 — 을 BigQuery 공개번호 조인으로 해결(사용자 승인 2026-07-27).

- **B2 family 지도:** `collect/bq_family_ir`(신설 · 시계열 `bq_family.py`와 분리). BQ
  `patents-public-data.publications` 공개번호+출원번호 정규화 조인. 40,552 문서 1:1 · **DOCDB 95.8%**
  (fallback-self 4.2%). 정답(qrel 2,211) DOCDB **88.1%**. KR 타입접두(`10`/`20`) 특례로 KR 정답
  1,073건 추가 회수. 프로파일 `data/profiles/ir_family_map.md` · MANIFEST 2026-07-27. dry-run 10.26 GB·~$0.06.
- **F1 정의 동결:** family-level = **fold-then-cut**(순위를 family로 중복 제거 후 top-K family =
  'K개 서로 다른 발명 검토'). `analysis/metrics.evaluate(..., family=...)` · 미조인은 자기자신 family.
- **F1 주지표 기준선(B0 · BM25-Claim):**

  | 수준 | Recall@100 | Success@100 | MRR |
  |---|---:|---:|---:|
  | 문서 | 0.2800 | 0.4659 | 0.1447 |
  | **family(F1)** | **0.2905** | 0.4801 | 0.1490 |

  family 수준이 소폭↑(중복 공개 접힘). **이 데이터셋에선 family≈문서**(정답 병합 질의 5/981 ·
  고유 정답 family 2,193 vs 문서 2,211) — 심사관 인용은 대개 서로 다른 발명이라는 정직한 관찰.
- **B8 시점분할 + F9 동결·봉인(2026-07-27 사용자 승인):** `corpus/split.py` — 질의 60/20/20
  family-disjoint, 경계 **train/dev=2016-11-21·dev/test=2021-07-21**(데이터감사 확정·정확히 600/200/200).
  `build_split` 이 절단결과를 config 동결 경계와 대조(표류 체크섬). **test 200질의 qrel 봉인**(479엣지/
  198질의 → `qrel_test_sealed.parquet`) · 개발용 visible 1,937. `metrics --split{train,dev,test,all}`.
  **B0 dev family Recall@100 = 0.2942**(train 0.2548·all 0.2905). 프로파일 `data/profiles/ir_split.md`.
- **Dense·Hybrid·bootstrap 완료(2026-07-27 사용자 승인·유료실행):** `retrieval/dense.py`(Titan v2
  1024차원·FAISS IndexFlatIP·텍스트해시 캐시) → B2 · `retrieval/hybrid.py`(RRF c=60) → B3 ·
  `analysis/bootstrap.py`(페어드 10k·95%CI·seed 고정). 문서 40,491 임베딩(빈 61 제외)·~$0.5.

  **dev · family-level 성능표 (C2 무대 · 프로파일 `data/profiles/ir_baselines_b0b3.md`):**

  | 시스템 | R@100(주) | R@500 | S@100 | MRR |
  |---|---:|---:|---:|---:|
  | B0 BM25-Claim | 0.2942 | 0.4059 | 0.5076 | 0.1748 |
  | B2 Dense-Titan | 0.2459 | 0.3458 | 0.4112 | 0.1265 |
  | **B3 Hybrid-RRF** | **0.3212** | **0.4776** | **0.5635** | 0.1716 |

  부트스트랩(dev·R@100): **B3−B0 Δ+0.0271 CI[−0.0022,+0.0565]**(양이나 95% 유의 아님·승27패16) ·
  **B2−B0 Δ−0.0483 CI[−0.0936,−0.0026]**(Dense 단독 유의하게 낮음). 정직 해석: 하이브리드가 최강
  텍스트 기준선이나 dev 소표본서 유의 미달 · Dense 단독은 교차언어 격차(M2 정합)로 BM25 하회, 융합서
  상보. **이 표가 C2 무대 — 온톨로지 P0–P2 가 B3 를 넘는가가 H3 핵심(M4).** 성능주장 없음(기준선 관측).
- **잔여(M3→M4):** F10 시점/family-disjoint 후보 마스킹 배선(현 run 은 미적용·정답 정의상 무해) ·
  M4 온톨로지팔(B4/B5·P0–P2)·ablation·subgroup. (M3 텍스트 기준선 목표 달성.)

### 7.3 M4 사전등록 동결 — 온톨로지팔·순위함수·ablation (2026-07-27 사용자 승인 🟢 · 테스트 개봉 전) 🔒

> M4 착수 시 데이터 관찰(Phase 2) 후 확정한 동결값. **결과(dev Recall)를 보기 전 이 커밋으로 동결한다**
> (CLAUDE §1.3·§2 Phase 3). test qrel 봉인 유지. 값 변경은 사전 동결된 민감도 격자로만.

| # | 항목 | 동결값 · 근거 |
|---|---|---|
| M4-1 | **확증 스코프** | B4·B5·**P0**(핵심 제안) + ablation + subgroup. **P1/P2 후속** — 입력 ClaimFeature/featureText ABox 가 벤더 스냅샷에 **0건**(실측 2026-07-27: `data/external/sdkb/` 에 `ClaimFeature` 인스턴스·`featureText`·`hasFeature` 전무). P1/P2 는 claim-feature ABox 재벤더(별도 사용자 승인·MANIFEST) 후 별건. |
| M4-2 | **순위함수 활성 항(§3.2)** | **P0★(결합 제안·ablation 기저)** `S(q,d) = (1−α)·T̃ext(B3) + α·[w_c·ConceptOverlap + w_h·PathSim + w_i·IpcSim]`. **w_f(FeatureCoverage)·w_r(GroundCompat)=0**(M4-1). T̃ext = B3 순위의 질의별 [0,1] 선형 rank-norm. 항별 기여 기록. **개정(2026-07-27·테스트 전):** A1(CPC/IPC 제거) ablation 이 well-defined 이려면 결합계에 IPC 항이 있어야 함 → §3.1 P0(concept+path)를 **IPC 항 포함 P0★로 확장**, 원고 §5.4 ablation 표(A1 분류의존성 포함)와 정합. §3.1 P0(concept+path only)는 부분집합으로 병기 보고. B4(IPC-only)·B5(concept-only)는 독립 비교팔로 유지. |
| M4-3 | **ConceptOverlap** | 코퍼스 `concepts`(141 고유·질의 97.7%) 집합의 **축 가중 Jaccard**. **축 가중치 = 균등 1.0 동결**(차등가중 근거 부재 → 민감도 후속). 축(axis)은 A2/A3 ablation 분할에만 사용. |
| M4-4 | **PathSim** | 개념→ont:클래스 멤버십 기반 **Wu-Palmer**(TBox subClassOf DAG), 집합간 `mean_q max_d WP`. ⚠️ **as-built 관찰: 온톨로지 개념 계층이 사실상 평면**(개념간 관계 4건·TBox subClassOf 9건 — 실측 2026-07-27) → PathSim 은 거의 축-일치로 퇴화. w_h 는 dev 격자가 결정(선판단 없음), 퇴화 시 0 수렴 예상·정직 보고. |
| M4-5 | **F18 가중치 격자** | α∈{0,0.25,0.5,0.75,1.0} × (w_c,w_h,w_i) **단체(simplex) 해상도 0.25**(a+b+c=1, 각∈{0,.25,.5,.75,1} = 15점) = 75 구성. **dev family Recall@100(F1)로만 선택**·동률은 (낮은 α, 사전순 w) 선택으로 결정적·test qrel 최적화 0. |
| M4-6 | **F10 후보 마스크** | `D_q(q)` = 코퍼스 문서 중 (자기 제외) ∧ `publication_date(d) < filing_date(q)` ∧ `family(d)≠family(q)`. B4/B5 는 D_q 위에서만 채점, B0–B3 run 은 D_q 로 사후 필터(정답은 정의상 시점선행·타family → recall 중립). |
| M4-7 | **B4 CPC/IPC** | IPC **주**(전 문서·평균 3.6), CPC 보조(**983/40,552 만 보유** → 희소 정직 보고). 접두 계층(섹션→클래스→서브클래스→그룹) 겹침·거리 유사도. |
| M4-8 | **Ablation 이번 세션** | **A1**(CPC/IPC)·**A2**(공정·소자)·**A3**(재료·장비·고장)·**A6**(경로only)·**A7**(전체온톨로지)·**A8**(전문가계층=Skill·ExpertCase·Mitigation, 음성대조군). **A4·A5 후속**(ClaimFeature·거절근거 = P1/P2 항·입력 부재). Holm 보정(F6). |
| M4-9 | **확증 가설 이번 세션** | **H3**(P0 vs B3 = C2 헤드라인) 검정 · **H5**(A8 음성대조군 특이성) 검정 · **H4**(A4/A5 손실>A1) **후속**(A4/A5 미가용). 페어드 부트스트랩 10k·95%CI(F4). |
| M4-10 | **Subgroup(T2·§5.3)** | 거절근거(rejectedFor 유형)·공정군·**KR/외국 언어** 분해. 최소 질의수 미달 하위집단은 확정결론 금지·표에 n 명기. |

**신규 모듈(§2 배치표):** `ontology/concept_axis.py`(개념→축·TBox 계층, 커밋가능 캐시) · `retrieval/candidate.py`(D_q·F10) · `retrieval/ontology_rerank.py`(ConceptOverlap·PathSim) · `retrieval/systems.py`(B4/B5·P0★) · `analysis/ontology_eval.py`(격자선택·마스터표) · `analysis/ablation.py` · `analysis/subgroup.py`. **어휘 발명 0** — 축·계층은 벤더 TTL 의 `a ont:X`·subClassOf 에서 결정적 추출.

### 7.4 M4 온톨로지팔 dev 결과 (2026-07-27 · 선택·개발용 · test 봉인) 🟢

> **결과값이지 사전등록 아님.** 전량 **dev(197질의·정답≥1)·family(F1)·F10 마스크·oracle-free**.
> 확증 H3/H4/H5 는 **봉인 test** 개봉 시 확정 — 아래로 확증 주장하지 않는다. 프로파일 `data/profiles/ir_ontology_m4.md`.

- **F18 선택:** α=0.75·(w_c,w_h,w_i)=(0.5,0.0,0.5) (dev R@100=0.4167). **w_h=0 선택 — PathSim 기여 0**
  (개념계층 평면·최대깊이 4 → Wu-Palmer 축-일치 퇴화, M4-4 예측 실증). 이득 본체 = ConceptOverlap.
- **마스터표(dev family R@100):** B3(F10-masked) 0.3770 · B4 IPC-only 0.1513 · B5 concept-only 0.1693 ·
  P0 concept 0.4176 · **P0★ 0.4193**. (F10 마스크가 B3 를 M3 무마스크 0.3212→0.3770 로 올림.)
- **H3 헤드라인(dev 유의):** **P0★ − B3 = +0.0422 · 95%CI[+0.0066,+0.0779] · p0.021 · 승34/패12.**
  개념단독 P0 도 +0.0405·p0.014 유의. **온톨로지 보강이 최강 텍스트 기준선을 dev 서 유의 개선**(C2 신호).
- **Ablation(Holm m=6):** A6(경로) Δ=0·A7(전체온톨로지) Δ+0.0422(p0.021)·A1(IPC) +0.0038·A2(공정·소자)
  **−0.0171**(제거가 개선)·A3(재료·고장) +0.0072·A8(전문가Skill) +0.0096(p0.051). **Holm 후 개별계층
  유의 아님**(엄격 임계 0.0083) — 전체 효과는 유의하나 계층분해는 test·전체 필요. B4/B5 단독은 B3 하회.
- **하위집단 T2(dev·δ0.05):** 모든 신뢰집단에서 P0★ 이 B3 개선(회귀 0). max_drop pos_lang −0.0268·
  proc_group −0.0463 (< δ). 교차언어(정답 외국·n133·R≈0.25) 집단도 개선.
- **H4 미검정·H5 잠정:** A4/A5(ClaimFeature·거절근거)=P1/P2 입력 부재 → H4 후속. A8 p0.051(Holm n.s.)
  로 H5(음성대조군) 잠정 지지이나 점추정 비영 → 약한 결합 가능성, test 재확인.
- **잔여:** ① **test 봉인 개봉**(사용자 승인 필요)로 H3/H5 확증 확정 · ② P1/P2(claim-feature 재벤더) →
  H4 · ③ figures 신설(C2 성능표·ablation) · ④ M5 T-gate 결함주입.

### 7.5 P1/P2 사전등록 동결 — FeatureCoverage·GroundCompatibility (2026-07-27 사용자 승인 🟢 · 테스트 개봉 전) 🔒

> H4(A4/A5 손실 > A1) 검정을 위해 P1/P2 를 추가한다. Phase-2 실측: `central_axis.oxstore`(11.6M트립·
> 이미 빌드·sha 스탬프)에 `Patent —hasClaim→ Claim{isIndependent} —hasFeature→ ClaimFeature{featureText}`.
> **질의 독립항 features 100%·후보 features 97.9% 도달**·doc_id↔patent IRI 직결(`kr_...`). featureText 는
> KIPRIS 원문 → **비커밋**(런타임 계산·집계/해시만 커밋). 결과 보기 전 동결(CLAUDE §1.3).

| # | 항목 | 동결값 |
|---|---|---|
| P-1 | **원천** | 기존 `central_axis.oxstore`(사용자 결정). 887MB 스냅샷 추가 안 함. 피처 sidecar parquet 추출(`corpus/claim_features.py` · gitignore 원문 · 집계/서명 커밋). |
| P-2 | **FeatureCoverage(A4·P1)** | 질의 **독립항** ClaimFeature 집합 F_q, 후보 전체 ClaimFeature 집합 F_d. `FC(q,d) = |{f∈F_q : max_{g∈F_d} cos(emb(f),emb(g)) ≥ τ}| / |F_q|`. **Titan v2 임베딩(교차언어·기존 캐시 인프라)**. |
| P-3 | **τ(매칭 임계)** | dev 격자 **{0.5, 0.6, 0.7, 0.8}** 에서 dev family R@100 로 선택·동결. test 최적화 0. |
| P-4 | **순위함수 확장** | P0★ 에 `w_f·FeatureCoverage` 추가 → P1. F18 격자에 w_f 를 4번째 단체 차원으로(해상도 0.25 유지·구성 증가 SPEC 보고). |
| P-5 | **GroundCompatibility(A5·P2)** | 거절근거 호환. **oracle-free 주모드에서 배제(§4.5.1) → 주결론 기여 0.** citation/gt-assisted 보조모드에서만 산출(성능주장 금지·상한). oracle-free H3 헤드라인 불변. |
| P-6 | **Ablation 갱신** | A4(−FeatureCoverage=w_f→0)·A5(−GroundCompat) 추가 → A1–A8 완비. H4 = A4/A5 제거손실 > A1(IPC)·서지. Holm m 갱신(보고). |
| P-7 | **누출 안전** | FeatureCoverage 는 질의 **자기** 독립항 피처(정답 파생 아님)만 사용 → 누출 없음. `leakage_check` 재확인. qrel 미열람. |
| P-8 | **비용 게이트** | 임베딩은 유료 → sidecar 추출 후 **dev 풀 피처 물량·비용 실측 보고 → 사용자 유료 승인 후** 임베딩(M3 규율). |

### 7.6 PathSim 사망 진단 — 탐색적 분석 (2026-07-27 사용자 승인 🟢 · M4 마무리 후 · 상류 불변)

> **배경:** M4 에서 dev 격자가 **w_h=0**(PathSim 기여 0)을 선택. 원인 후보 = 개념 태깅 희소(문서당
> 1.58)·인스턴스 계층 평면(141개 중 121개 depth1)·개념↔개념 인스턴스 관계 4건. **T-Box 재설계는
> 가설이지 확정 아님** — 상류 SDKB 결정([[ontology-outranks-the-paper]])이라 임의로 안 건드린다.
> 아래는 **재설계 전** 병목을 값싸게 분리하는 탐색적 분석(확증 아님·§0.1 탐색 강등·현 동결 스냅샷·
> test 봉인 유지). 원고 §7.6·부록 F(방향 전환 규칙)에 정합.

| # | 진단 | 방법 (코드만·상류 불변) | 판별 |
|---|---|---|---|
| D1 | **밀도 vs 깊이** | 질의를 개념 태깅 밀도(문서당 개념 수) 사분위로 나눠, PathSim-only(w_h=1) 및 P0★ 의 dev R@100 을 밀도 subgroup 별로 분해 | 고밀도 질의에서 PathSim 이 살면 병목=**커버리지**(ABox 확충 과제) · 안 살면 병목=**계층 평면**(T-Box 심화 후보) |
| D3 | **P1 이 PathSim 자리를 메우나** | FeatureCoverage(임베딩·계층 무관)가 "관련 있으나 정확 개념 불일치" 근접 회수를 잡는지 — PathSim 이 노린 near-miss 질의에서 P1 이득 측정 | P1 이 그 신호를 회수하면 PathSim 부재는 **무해**(임베딩이 대체) · 아니면 구조 신호 공백이 실재 |

- **비목표:** D1/D3 는 결정을 위한 진단이지 확증 산출이 아니다. T-Box 심화·개념링크 확충은 결과를 보고
  **사용자에게 상류 과제로 제기**할지 판단(임의 실행 금지). 어느 것도 사전등록 지표를 바꾸지 않는다.

### 7.7 P1 FeatureCoverage + 진단 D1/D3 dev 결과 (2026-07-27 · 임베딩 1.02M 완료 · test 봉인) 🟢

> **전량 dev·선택/개발용·확증 아님.** 프로파일 `data/profiles/ir_ontology_m4.md`. featureText 전량
> (1,023,838) Titan 임베딩 완료. **임베딩 메모리 버그(반환벡터 30GB 누적→WSL OOM) 수정**(커밋 2a57f60·
> 캐시전용 바운드 루프)·transient ModelError 재시도 강건화(0067b13).

- **P1 격자선택:** τ=0.7·α=0.75·(w_c,w_h,w_i,w_f)=(0.25,0,0.25,0.5)·dev R@100=0.4170. **P0★(w_f=0)=0.4167
  → FeatureCoverage 이득 ≈ 0.** w_h 여전히 0.
- **P1 ablation A1–A8(dev·Holm m=8):** A7(전체온톨로지)+0.0425 **p0.004 Holm 유의** · A1(IPC)+0.0131 ·
  **A4(−FeatureCoverage) −0.0013(음·제거가 개선)·A5(GroundCompat) 0** · A6(PathSim) 0 · A8(Skill 음성대조군)
  +0.0036 n.s.
- **★ H4 기각(dev):** A4/A5 손실(≈0·음) **<** A1(+0.0131). ClaimFeature·거절근거 계층이 분류보다 기여
  크다는 가설 미성립. **H5 지지**(A8 n.s.). **이득 본체 = ConceptOverlap + IPC.**
- **D1(밀도vs깊이):** PathSim-only R@100 이 개념밀도와 함께 상승(Q1 0.124→Q3 0.385)하나 전 분위 B3 하회
  → 병목은 저밀도 붕괴(커버리지)+거친 경로신호 둘 다. **계층 심화 단독으론 한계.**
- **D3(P1 이 near-miss 메우나):** 온톨로지 이득은 개념겹침 높은 Q3/Q4 집중(증폭)·**near-miss(Q1)은
  B3≈P0★≈P1 로 아무 항도 못 살림.** FeatureCoverage 임베딩도 PathSim 자리 대체 못 함.
- **상류 시사(사용자 판단 대상):** T-Box 재설계는 정당화 안 됨. near-miss(교차언어·의미격차) 회수는
  계층·claim-feature 로 안 뚫리며, ABox 개념 커버리지·교차언어 검색이 더 우선(천장은 여전히 낮음).
- **잔여:** ① **test 봉인 개봉**(사용자 승인)로 H3/H4/H5 확정 · ② figures(C2 성능표·ablation) · ③ M5 T-gate.

### 7.8 ★ TEST 확증 — 봉인 개봉 (2026-07-27 사용자 승인 🟢 · 198질의 · 동결설정·재선택 없음) 🔒→🟢

> dev 동결 설정을 봉인 test 200질의(정답≥1: 198)에 **1회** 적용. **재선택·재튜닝 없음.** 이것이 논문 확증.
> 프로파일 `data/profiles/ir_ontology_m4.md` §TEST 확증. F9 봉인 절차 준수(개봉 전까지 미열람 확인).

- **★ H3(C2) 조건부 지지:** test family R@100 — B3 0.4315 · **P1 0.4849 (Δ+0.0534·CI[+0.0145,+0.0926]·
  p0.008 유의)** · P0★ 0.4635(Δ+0.0319·p0.181 **유의 미달**) · 개념단독 0.4900(Δ+0.0584·p0.002). **주
  사전지정 P0★ 는 IPC 가중 과적합으로 test 유의 미달 — 이득은 ConceptOverlap 이 실어나름**(IPC ablation
  A1 test 기여 +0.0025≈0). C2 "조건부 개선" 프레임 정합.
- **H4 미지지:** ablation(P1 기저·Holm m=8) A4(−FC)+0.0070·A5 0 이 A1(+0.0025)·서지를 유의하게 못 넘음
  (전부 Holm n.s.). ClaimFeature 계층 독립 기여 없음(원고 §5.4 중복/추출오류 시나리오 확정).
- **★ H5 기각 → 태스크 결합(entanglement) 발견:** **A8(전문가 Skill 계층 제거)이 test 유의 악화**
  (Δ+0.0316·p0.002·유일 Holm 유의). 사전등록 규칙(원고 §5.4·부록 F·신규주장 F) 발동: 음성대조군 폐기,
  **태스크 결합 발견 = T3(교차태스크 게이트) 필요성 직접 증거 = C3 강화.** 실패 아님·실질적 발견.
- **T2 안전:** subgroup(P1 vs B3·δ0.05) 전 신뢰집단 회귀 없음 — pos_lang max_drop −0.0140·proc_group
  −0.0584 · 교차언어(foreign n100) +0.0140 개선.
- **확증 종합:** H3 조건부 지지 · H4 미지지 · **H5→태스크 결합(C3/T3 강화)** · T2 안전. **원고 §6 표 갱신 대상.**
- **잔여:** ① 원고 §6 확증표·§7 해석 갱신(H5→entanglement·H4 미지지·P0★ 과적합) · ② figures(C2·ablation·
  결합발견) · ③ M5 T-gate 결함주입(T3 실측 — 이번 A8 결합발견이 T3 필요성 이미 시사).

## 8. 결정성·재현성 (원고 §5.6)
데이터·shape·CQ·인덱스·모델버전 해시 고정 · 시드/lockfile 공개(F16) · 분할·부트스트랩·hard-neg 시드 고정 ·
Titan `:0`·Haiku temp0 동결·임베딩 캐시 해시 · 3모드 분리 저장 · `check_signatures.py` 서명 검증 ·
FAISS **flat**(근사 인덱스 튜닝 파라미터 0 → ablation 오염 없음).

## 9. 신규 의존성 (2026-07-26 사용자 승인·설치·검증 완료 ✅)
`pyserini`(BM25 + FAISS Dense + RRF) · `faiss-cpu>=1.8`(flat 정확검색) · `boto3`(Titan·Haiku).
pyproject `[ir]` 옵셔널 그룹 추가 · `uv sync --extra ir` 설치. **설치·기능 임포트 검증 실측(2026-07-26):**
faiss 1.14.3 import ✓ · pyserini LuceneSearcher/FaissSearcher/LuceneIndexer import ✓ · JVM 부팅 ✓.
**GPU faiss는 40k 규모 이득 미미(flat 밀리초) + RTX 5090 Blackwell pip 지원 난이도 → CPU 정본**, GPU 후속 옵션(§11.3).

**환경 실측 발견 2종 (M2 착수 전 처리 필요):**
- **E1 · JAVA_HOME 필수:** 장비에 JRE만 있고 javac(JDK) 부재 → pyjnius 자동탐지가 `Unable to find javac`로
  실패. `JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64`(libjvm.so 확인) 명시 시 정상 부팅. **M2에서
  `config`/Makefile/.env에 JAVA_HOME 배선**(하드코딩 아닌 탐지 or 환경변수).
- **E2 · nori 사용 가능·토큰화 확정(2026-07-26 실측·결정 §11.6):** anserini-2.2.0 fatjar에
  `org.apache.lucene.analysis.ko.KoreanAnalyzer`·`KoreanTokenizer`·`DecompoundMode` **번들 확인**.
  pyserini `get_lucene_analyzer('ko')`의 CJK 바이그램은 편의 래퍼일 뿐 — jnius로 `KoreanAnalyzer` 직접
  인스턴스화 시 형태소 분석 확인. **도메인 실측(반도체 특허 문장):** nori(NONE)는 외래어 '플라즈마'를
  '플/라즈/마'로, Kiwi는 한자어 '식각'을 '식/각'으로 파편화 — **엔진 무관하게 도메인 사용자사전이
  핵심 지렛대**. → F13 확정: **nori(NONE)+SDKB 어휘 사용자사전 주**, Kiwi 민감도 비교자.

## 10. 비목표 (스코프 방어선)
- 전문가매칭·기술예측 **성능 주장 없음**(원고 §8.3·8.4 · 별도 AFCP-EM). 이 둘은 C1 표현범위·T3 감시대상·A8 음성대조군으로만 등장.
- G0/G1/G2 온톨로지 자체 변경 없음(코퍼스는 파생 뷰).
- 라이선스 제한 원문 커밋 없음(집계·해시·재구축 절차만).
- 운용효율(H2c)·법적맥락(H3b)·의미도달성(H3c)은 **탐색적 분석**(확증 아님 · §0.1).

## 11. 미해결·사용자 결정 필요 🔒
1. **F8 질의 표현 대비:** 원고 §4.2 주분석=**Claim-only**, SPEC-007/PLAN-017 §7 M1 주표현=**초록+청구항**.
   원고가 SoT — Claim-only를 주분석으로, 초록+청구항은 강건성으로 둔다(코퍼스는 4종 필드 모두 보유해
   양쪽 산출 가능). **원고 불변 · 코드가 원고에 맞춘다.** 확인 필요.
2. **F12 Dense 모델 — 확정(2026-07-26 사용자):** **Titan v2 주-팔**(다국어 코퍼스 KR 질의·후보에 정합).
   **PaECTER는 결과 분석 후 선행연구 비교가 필요하다는 판단이 서면 그때 추가 도출**(영어 정답 부분집합
   대상 영어-피벗 강건성). 원고 §4.6이 "다언어 임베딩 보조 기준선 추가" 여지를 이미 열어둠 → 주/보조
   역할은 이 결정으로 정합. RECONCILIATION §4에 기록.
3. **GPU faiss 시도 여부:** CPU 정본으로 충분(권고). GPU는 M3 이후 선택 실험으로만.
4. **가중치 학습(F18):** 개발셋 사전격자 vs 경량 학습 — M4 착수 시 격자 해상도 동결.
5. **전문가 판정(§6 M5):** 인적 판정 2인 확보 여부 — 미확보 시 탐색적 부록으로 강등.
6. **F13 토큰화 — 확정(2026-07-26 사용자):** nori(DecompoundMode.NONE)+**SDKB 온톨로지 어휘 사용자사전**
   (공정·소자·재료·장비 + 개념 prefLabel) = 주. Kiwi(kiwipiepy) = §5.3 사전등록 민감도 비교자. mecab-ko 생략.
   사용자사전은 **전 시스템(B0–P2) 동일 적용 토큰화 계층** — ablation 밖(기준선 보강 = 온톨로지팔 이득
   보수적 하향). 개발셋에서 Kiwi 유의 승리 시 승격은 사전등록 선택지.
