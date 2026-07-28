.PHONY: faults faults-baseline faults-fc faults-n03 faults-rejudge faults-n03adv faults-rejudge-v3 tables setup lint test vendor snapshot baseline collect profile merge corpus corpus-check family split dense hybrid userdict index eval mapping candidates validate reason cq vocab gate gate-graph leakage cq-freeze tgate s1 s2 h1 h2 cpc cpc-vintage figures serve sig-check

setup:
	uv sync --all-extras

lint:
	uv run ruff check src tests

# 서명 수치 표류 검사 — 원고·README·DATASET-CARD 가 CANONICAL-INDEX §1 과 정합한가.
# 데이터에 L0(신선도)을 두는 것과 같은 이유로 문서에도 둔다: 해시/커밋은 "안 바뀌었음"만
# 보장하지 "정본과 일치함"은 보장하지 않는다. 재산출로 서명이 바뀌면 CANONICAL §1 갱신
# → 직전 세대를 scripts/check_signatures.py 의 HISTORICAL_SIGNATURES 로 이동.
sig-check:
	uv run python scripts/check_signatures.py

test:
	uv run pytest -q

# 근간 온톨로지(SDKB) 스냅샷을 data/external/sdkb/ 로 vendor.
# 상류 TTL 은 **gitignore 되는 빌드 산출물**이라 git 이 최신성을 지켜주지 않는다.
# 그래서 vendor 하기 전에 상류에서 반드시 재빌드한다 — 디스크에 남아 있던 낡은 산출물을
# 그대로 얼리는 사고가 실제로 있었다 (2026-07-14 · G₀ 의 C₀ 가 16 이 아니라 20 이었다).
# SDKB_HOME 으로 원본 위치를 바꿀 수 있다: make vendor SDKB_HOME=/path/to/sdkb
SDKB_HOME ?= $(HOME)/Dev/sdkb
vendor:
	$(MAKE) -C $(SDKB_HOME) owl convert abox abox-patents abox-vendors compliance
	uv run python -m sdkb_paper.ontology.vendor --sdkb-home $(SDKB_HOME)

# baseline 그래프(graph_v0 = H1 의 "before") 를 스냅샷에서 조립. 결정적 산출물.
baseline:
	uv run python -m sdkb_paper.ontology.baseline

# RQ3 소부장 크로스워크 (KSIA 소부장 191사 → G₀ organization slug · match_key · company_type).
# 결정적·사전동결. G₀ 를 읽어 매칭하므로 baseline 이 선행한다. 산출: mappings/ksia_applicant_crosswalk.csv
crosswalk: baseline
	uv run python -m sdkb_paper.preprocess.ksia_crosswalk

# 삼성전자·SK하이닉스 특허 수집 (KIPRIS). 응답은 sqlite 캐시 → 재실행해도 API 를 다시 안 때린다.
# make collect SMOKE=1 이면 클래스 1개만 (파이프라인 관통 검증용)
collect:
	uv run python -m sdkb_paper.collect.collect $(if $(SMOKE),--smoke,) $(if $(CORPUS),--corpus $(CORPUS),) $(if $(DETAILS),--details,)

# 정제 + 데이터 프로파일 (CLAUDE.md §4 의무). 논문 표 4 의 원천.
profile:
	uv run python -m sdkb_paper.preprocess.profile $(if $(CORPUS),--corpus $(CORPUS),)

# PLAN-009 · H2 좌측절단 교정분 (2005–2009). **G₁ 에 병합되지 않는다** — H2 시계열 전용이다.
collect-extended:
	uv run python -m sdkb_paper.collect.collect --period extended

profile-extended:
	uv run python -m sdkb_paper.preprocess.profile --period extended

# PLAN-009 · H2 의 외부 준거 (DART 정기보고서). 문서는 data/raw/dart/ 에 캐시된다.
dart:
	uv run python -c "from sdkb_paper.collect.dart import build; d=build(); print(f'✓ 보고서 {len(d)}건')"

# 델타 트리플 생성 + 게이트 통과분만 병합 → graph_v1 (= G₁, H1 의 "after")
merge:
	uv run python -m sdkb_paper.ontology.delta $(if $(CORPUS),--corpus $(CORPUS),)
	uv run python -m sdkb_paper.ontology.merge_cli $(if $(CORPUS),--corpus $(CORPUS),)

# nori 사용자사전 빌드 (PLAN-018 §6.2.1 · SPEC-008) — 온톨로지+매핑+코퍼스수확.
# 산출: data/processed/ir/userdict_sdkb.txt (gitignore). 색인(make index) 선행 필수.
# JAVA_HOME 필요(nori JVM · config.java_home 가 탐지). corpus 선행.
userdict:
	uv run python -m sdkb_paper.retrieval.userdict

# BM25 색인·검색·평가 (PLAN-018 M2 · B0) — 사전토큰화(nori+사용자사전) → -pretokenized 색인 →
# 질의=독립항 top-100 검색 → 문서수준 Recall@100 진입 임계치. userdict·corpus 선행. JAVA_HOME 필요.
# retrieval/ 는 run 만 산출(qrel 미열람), 평가는 analysis/metrics 가 qrel 대조.
index:
	uv run python -m sdkb_paper.retrieval.bm25

eval:
	uv run python -m sdkb_paper.analysis.metrics

# 논문 §6.2·§6.4 표 전량 재생성 (동결 run 재평가 · 새 검색 없음 · 수기 기입 금지 CLAUDE §1-7).
# 산출: paper/tables/ir_{performance,subgroup,increment}_{dev,test}.md + viz 입력 CSV.
# SPLIT=dev 로 개발 분할만 돌릴 수 있다. test 는 봉인 개봉 후 재평가 전용 — 재선택 금지.
SPLIT ?= test
tables:
	uv run python -m sdkb_paper.analysis.overlap --freeze
	uv run python -m sdkb_paper.analysis.results_table --split $(SPLIT) --write --latency
	uv run python -m sdkb_paper.analysis.subgroup --table --split $(SPLIT)
	uv run python -m sdkb_paper.analysis.increment --split $(SPLIT) --write
	uv run python -m sdkb_paper.analysis.ablation --split $(SPLIT) --p1 \
		--tau 0.7 --alpha 0.75 --w 0.25 0.0 0.25 0.5 --write
	uv run python -m sdkb_paper.analysis.lang_recall --split $(SPLIT) --write

# 논문 §6.2f 교차언어 진단 (PLAN-019 W1) — 정답 언어별 회수·자원 커버리지·후보 풀 편향.
# 동결 run 재집계(새 검색 0). 산출: paper/tables/ir_crosslingual_$(SPLIT).md + CSV.
crosslingual:
	uv run python -m sdkb_paper.analysis.lang_recall --split $(SPLIT) --write

# IR 벤치마크 코퍼스 조립 (PLAN-017 M1) — G₀/G₁/G₂ + sidecar 청구항 → 문서중심 코퍼스.
# 산출: data/processed/ir/ir_corpus_v09.parquet · qrel_examiner.parquet(gitignore) +
#       data/profiles/ir_corpus_v09.md(커밋). merge·central_axis(sidecar) 선행 필요.
corpus:
	uv run python -m sdkb_paper.corpus.assemble

# 재조립 없이 산출물 성공기준(PLAN-017 §5)만 검증
corpus-check:
	uv run python -m sdkb_paper.corpus.assemble --check

# DOCDB family 지도 (B2 · F1 주지표) — BigQuery 공개번호/출원번호 조인. --dry-run 으로 비용 확인.
family:
	uv run python -m sdkb_paper.collect.bq_family_ir

# 시점 분할 (B8 · F9 사전등록) — 60/20/20 family-disjoint · test qrel 봉인. 경계는 config 동결.
split:
	uv run python -m sdkb_paper.corpus.split

# Dense 검색 (B2 · Titan v2 임베딩·FAISS flat). Bedrock 자격증명 필요 · 임베딩 캐시로 재실행 무료.
dense:
	uv run python -m sdkb_paper.retrieval.dense

# Hybrid 검색 (B3 · BM25+Dense RRF). B0·B2 run 선행 필요.
hybrid:
	uv run python -m sdkb_paper.retrieval.hybrid

# IPC/CPC 룰 커버리지 — 특허를 수집하기 전에 매핑의 사각지대를 드러낸다
mapping:
	uv run python -m sdkb_paper.ontology.mapping

# 3층 후보 발굴 (PLAN-004) — 후보 리포트만 만든다. 채택은 사람이 한다.
candidates:
	uv run python -m sdkb_paper.ontology.candidates

# 스냅샷 무결성: 커밋된 SDKB 스냅샷이 PROVENANCE 의 sha256 과 일치하는가.
# SDKB 원본이 필요 없다 — CI 에서 매 push 마다 돈다. baseline 의 출처가 거짓이 되는 것을 막는다.
snapshot:
	uv run python -m sdkb_paper.ontology.vendor --verify

# L0 신선도: 산출물이 입력보다 낡지 않았는가. sha256(snapshot)은 "바뀌지 않았음"만 보장하고
# "옳게 빌드되었음"은 보장하지 않는다 — 2026-07-14 사고가 정확히 그 틈으로 났다 (논문 §7.2).
# baseline 이후에 돌아야 파생 산출물 신선도를 볼 수 있다.
l0: snapshot baseline
	uv run python -m sdkb_paper.ontology.vendor --verify-freshness

# --- 4층 검증 게이트 L0–L3 (논문 §4.3) ---------------------------------------
# 게이트 대상은 두 그래프다:
#   graph_v0   — 실물 baseline(G₀ = 현행 SDKB, SIRP 특허 1,000건). 레거시 특허가 섞여 있으므로
#                **완화 shape**(graph) 로 검증한다 — 공정 링크 없는 디바이스 특허를 소급 처벌하지 않는다.
#   mini_graph — 합성 특허 3건. **엄격 shape**(delta) 를 실제로 때린다. 병합될 특허가 지켜야 할
#                계약(개념 매핑 ≥1)이 살아있는지는 여기서만 확인된다.

# L1 구조 제약 (SHACL)
validate: baseline
	uv run python -m sdkb_paper.validate.shacl_gate data/processed/graph_v0.ttl --shapes graph
	uv run python -m sdkb_paper.validate.shacl_gate data/samples/mini_graph.ttl --shapes delta

# L2 논리 일관성 (HermiT — Java 필요)
reason: baseline
	uv run python -m sdkb_paper.validate.reasoner_gate data/processed/graph_v0.ttl

# L3 기능 검증 (Competency Question)
#   graph_v0 의 CQ 는 게이트가 아니라 **측정**이다(--min-pass 0) — 그 값이 논문 §4.2 의 G₀ 열이 된다.
#   현행 CQ 3개는 G₀ 에서 이미 100% 응답한다. 보강 효과를 판별하려면 CQ 확장이 필요하다(부록 A).
#   회귀 감시(특허 유실·링크 단절)는 통합 테스트의 CQ 서명 검사가 맡는다.
#   mini_graph 는 특허가 있으므로 100% 를 요구하는 진짜 게이트다.
cq: baseline
	uv run python -m sdkb_paper.validate.cq_runner data/processed/graph_v0.ttl --report --min-pass 0
	uv run python -m sdkb_paper.validate.cq_runner data/samples/mini_graph.ttl --report

# 어휘 검증 커버리지 (논문 §3.4.2 지표 ii) — CQ 가 어휘의 몇 %를 실제로 심문하는가.
#   **게이트가 아니라 측정이다**(--min-cov 0). 임계값을 세우면 커버리지를 올리려고 CQ 를
#   지어내게 되고, 그것은 CQ 를 태스크에서 도출한다는 프로토콜(SPEC-004)을 배신한다.
#   낮은 값이 나오는 것 자체가 결과다 — "CQ 8/8 · 100%" 가 공허한 게이트임을 드러낸다.
vocab: baseline
	uv run python -m sdkb_paper.validate.vocab_coverage data/processed/graph_v0.ttl --report
	uv run python -m sdkb_paper.validate.vocab_coverage data/samples/mini_graph.ttl --report

# --- T-gate (원고 §4.9 · PLAN-019 W3) ----------------------------------------
# Accept(ΔG) = 1[L0=L1=L2=L3] · 1[LB95(ΔR100)>−ε]_T1 · 1[max_s Drop_s<δ]_T2 · 1[CQ 비회귀]_T3
# ε=0.02 · δ=0.05 는 **테스트 개봉 전 동결된 사전등록 값**(config.T_EPSILON/T_DELTA) — 결과를
# 본 뒤 바꾸지 않는다. 판정은 곱이라 하나만 0 이어도 승인은 0 이다.

# 누출 감사 — T1 의 전제. 금지간선·qrel 파생 피처·F10 마스크 잔여를 산출물에서 재검증한다.
leakage:
	uv run python -m sdkb_paper.validate.leakage_check --split $(or $(SPLIT),dev)

# T3 세대 동결 (표 6.6 축적). make cq-freeze GEN=g0 GRAPH=data/processed/graph_v0.ttl
# 기준 세대 이후의 세대는 AGAINST 로 이전 세대를 지정한다 — 그래야 T3 판정이 아티팩트에
# 들어가고 표 6.6 의 판정 열이 수기 기입을 타지 않는다(N5e · CLAUDE.md §1-7).
#   make cq-freeze GEN=graph_v1 GRAPH=data/processed/graph_v1.ttl AGAINST=g0
cq-freeze:
	uv run python -m sdkb_paper.validate.t3_cross_task_cq \
		$(or $(GRAPH),data/processed/graph_v0.ttl) --freeze $(or $(GEN),g0) \
		$(if $(AGAINST),--against $(AGAINST),)

# T1·T2·T3 종합 판정 (+ 누출 감사). 실패 시 비영 종료 — 우회 경로 없음.
tgate:
	uv run python -m sdkb_paper.validate.t_gate --split $(or $(SPLIT),dev) \
		$(if $(GRAPH),--graph $(GRAPH),) --baseline $(or $(GEN),g0)

# --- 결함주입 (원고 §4.10·§6.5 · H1 · PLAN-020 W4) ---------------------------
# 게이트의 **판별력**을 재는 유일한 실험이다. 초록불 게이트는 판별력의 증거가 아니다.
#
# 오염 규율(사용자 지시 2026-07-28): 정본은 실험 전에 해시 봉인 + 실복사 백업하고, 결함
#   산출물은 data/quarantine/ 밖으로 나가지 않는다. 인스턴스마다 정본 해시를 재검증하며
#   한 바이트라도 변하면 즉시 중단한다. 격리본은 종료 시 읽기전용으로 잠긴다.
#   격리 산출물은 gitignore — **논문 수치로 절대 쓰지 않는다.**
#
# 순서가 중요하다. baseline(기준선) → fc-cache(FC 성분 1회) → faults(매트릭스).
#   FC 임베딩 인덱스는 최대 RSS 24.8GB 라 인스턴스마다 올리면 OOM 이다. 결함군 12종이
#   featureText 를 건드리지 않으므로 한 번 계산해 재사용하며, 그 정합성은 fc-cache 가
#   **동결 P1 run 재현**(top-100 197/197 일치)으로 확인한다.
faults-baseline:
	uv run python -m sdkb_paper.analysis.faults --baseline

faults-fc:
	uv run python -m sdkb_paper.analysis.faults --fc-cache

faults:
	uv run python -m sdkb_paper.analysis.faults --reps $(or $(REPS),3) --workers $(or $(WORKERS),10)

# W4b (PLAN-021) — CQ 판정 v2. 결함을 **다시 주입하지 않는다**: 새로 넣는 것은 정상 델타 N03
# 뿐이고, 나머지는 W4 격리본을 읽어 판정 규칙만 바꿔 다시 센다(대응 비교 · 정본·격리본 불변).
faults-n03:
	uv run python -m sdkb_paper.analysis.faults --n03 --reps $(or $(REPS),3) --workers $(or $(WORKERS),9)

faults-rejudge:
	uv run python -m sdkb_paper.analysis.faults --rejudge --workers $(or $(WORKERS),10)

# PLAN-022 N5c — 면제 악용 결함 주입(신규 격리 run) → L3·T3 표면 분리 재판정(재주입 없음)
faults-n03adv:
	uv run python -m sdkb_paper.analysis.faults --n03adv --reps $(or $(REPS),3) --workers $(or $(WORKERS),9)

faults-rejudge-v3:
	uv run python -m sdkb_paper.analysis.faults --rejudge-v3 --workers $(or $(WORKERS),10)

# 머지 전 전체 게이트: L0(무결성+신선도) + baseline 재조립 + L1 + L2 + L3 + 어휘 커버리지 측정
#   + 누출 감사 + T1·T2·T3. IR 산출물(run·코퍼스)이 없는 환경에서는 tgate 가 먼저 실패하므로
#   그래프만 검증하려면 `make gate-graph` 를 쓴다.
gate: gate-graph leakage tgate

gate-graph: l0 validate reason cq vocab

# S1(구 H1) 자원 형성 타당성 — 공정 단계별 커버리지 (Wilcoxon 단측). 게이트를 통과한 두 스냅샷을 읽기만 한다.
# 표본 집합은 확장 49 와 복원 이전 20 **양쪽**으로 병기 보고된다 (PLAN-005 · v0.9 S-시리즈 재라벨).
# v0.9 확증 가설 H1(게이트 판별력)과 다른 개념 — RECONCILIATION-v09.md §1.
s1:
	uv run python -m sdkb_paper.analysis.s1_coverage_cli $(if $(CORPUS),--corpus $(CORPUS),)

h1: s1   # 구 별칭 (호환 유지 · 향후 제거 예정) → make s1

# S3(구 RQ3) 소부장 층별 커버리지 — 장비/재료/부분품 각각 별도 델타·그래프(같은 게이트)로 정식 검정 (표 5b).
# 검정 방법·임계값·개념 정의는 불변 · 바뀌는 건 company_type 필터 하나 (PLAN-014 §3.3 사전등록).
ksia-strata:
	uv run python -m sdkb_paper.analysis.ksia_strata_cli

# H2 의 대조군 분류 데이터 (BigQuery patents-public-data · GCP 인증 필요).
#   cpc         — 현재 스냅샷의 CPC. KIPRIS 는 IPC 만 주는데 대조 코드 2개가 CPC 전용이라
#                 IPC 말뭉치에서 구조적으로 0건이었다 (PLAN-007 §1).
#   cpc-vintage — 날짜별 **동결 스냅샷**(2017-10 …). H10 스킴은 전량 2021년 이후의 소급
#                 재분류다 — 현재 코드로 만든 시계열은 구조적으로 늦을 수 없다.
cpc:
	uv run python -m sdkb_paper.collect.bq_cpc

cpc-vintage:
	uv run python -m sdkb_paper.collect.bq_cpc --vintage

# S2(구 H2/RQ2) 시간분석 2차 재사용 — 개념 단위 vs 코드 단위 시계열의 탐지 시차 (단측 부호검정 · PLAN-006).
# 사례 7건·신호 규칙·판정 규칙은 시계열을 보기 전에 동결됐다 (mappings/h2_cases.csv · v0.9 S-시리즈 재라벨).
s2:
	uv run python -m sdkb_paper.analysis.s2_timeseries_cli

h2: s2   # 구 별칭 (호환 유지 · 향후 제거 예정) → make s2

# §4.5 강건성 — 패밀리(DOCDB) 중복 제거 전후 비교.
#   family     — BigQuery 에서 DOCDB family_id 조인 (GCP 인증 필요). KIPRIS 원데이터에는
#                우선권·패밀리 필드가 없어 이 조인 외에는 패밀리를 정직하게 잴 방법이 없다.
#   robustness — dedup 된 델타로 G₁ 을 다시 짓고(같은 게이트 통과) S1·S2(구 H1·H2′) 를 **재검정**한다.
#                검정 방법·임계값·개념 정의는 불변 — 바뀌는 것은 입력 말뭉치 하나뿐이다.
family:
	uv run python -m sdkb_paper.collect.bq_family

robustness:
	uv run python -m sdkb_paper.analysis.robustness_cli

# §4.5 강건성 — 출원인별 분리 재검정. G₁ 은 두 출원인이므로, 보강 효과가 한 회사 때문에
# 나온 것인지 확인한다. G₀ 는 두 팔의 공통 before 다 (쪼개면 baseline 이 움직인다).
by-applicant:
	uv run python -m sdkb_paper.analysis.applicant_cli

figures:
	uv run python -m sdkb_paper.viz.figures

# --- 온톨로지 탐색·모니터링 로컬 웹앱 (읽기 전용) ---
serve:
	uv run python -m sdkb_paper.explore.server --port $(or $(PORT),8000)
