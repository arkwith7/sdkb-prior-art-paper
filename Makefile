.PHONY: supplementary-check-en figures-en concept-rel style-check-en glossary-check glossary-inventory gate-profile cq-freeze-profile ep5 figure-data rag ragcount rageval t4 typology-sheet typology-code typology-table faults faults-baseline faults-fc faults-n03 faults-rejudge faults-n03adv faults-rejudge-v3 faults-holdout faults-holdout-judge tables setup lint test vendor snapshot baseline collect profile merge corpus corpus-check family split dense hybrid userdict index eval mapping candidates validate reason cq vocab gate gate-graph leakage cq-freeze tgate freeze-runset runsets tgate-resource s1 s2 h1 h2 cpc cpc-vintage figures serve sig-check verdicts submission-build submission-check style-check submission-stage3 submission-en tables-stability tables-stability-check concept-status

setup:
	uv sync --all-extras

# 린트 대상에 `scripts` 를 포함한다 — 검사기들이 사는 자리다. 빠져 있던 동안
# `style_check_en.py` 의 E741 4건과 `rerank_ceiling.py` 의 미사용 import 가
# 커밋된 채로 남았다: 규율을 강제하는 코드가 규율 밖에 있으면 안 된다.
lint:
	uv run ruff check src tests scripts

# 서명 수치 표류 검사 — 원고·README·DATASET-CARD 가 CANONICAL-INDEX §1 과 정합한가.
# 데이터에 L0(신선도)을 두는 것과 같은 이유로 문서에도 둔다: 해시/커밋은 "안 바뀌었음"만
# 보장하지 "정본과 일치함"은 보장하지 않는다. 재산출로 서명이 바뀌면 CANONICAL §1 갱신
# → 직전 세대를 scripts/check_signatures.py 의 HISTORICAL_SIGNATURES 로 이동.
sig-check:
	uv run python scripts/check_signatures.py

# 판정 문구 정합 — 원고(정본·투고 파생본)가 paper/verdicts.yaml(판정 SSOT)의 금지 문구를
# 쓰지 않는가. CLAUDE.md §0.8 문구 사전의 기계 정본이다. 서명 검사(sig-check)가 **수치**의
# 표류를 막듯 이것은 **판정 강도**의 표류를 막는다 — 재구성마다 재발한 실패 모드다.
# **차단 모드** (2026-08-12 · PLAN-048 3단계 종료 시 승격 · §2.3). 승격 시점의 실측은
# 정본·파생본 모두 위반 0이다 — 경고 모드로 시작한 이유(정본의 제목·서지 플레이스홀더)가
# 3단계에서 해소됐다. 이제 위반은 곧 CI 실패다.
verdicts:
	uv run python scripts/check_verdicts.py

# 투고 파생본을 정본에서 기계로 생성 (PLAN-048 1단계 · 순수 이관).
# 정본은 읽기만 한다 — 파생본의 모든 문장이 정본에 있는지 스크립트가 검증한다.
# `--check` 는 **1단계 동안만** 유효하다: 2단계(구조 리팩터)부터 파생본을 직접 편집하므로
# 그 뒤에는 재생성 정합이 성립하지 않는다. 그때 이 타깃은 이력용으로만 남는다.
submission-build:
	uv run python scripts/build_submission.py

# 투고 파생본의 데스크 리젝 요인 — 플레이스홀더·영문 초록·표/그림 상한·분량·내부 링크.
# 파생본(paper/submission/)이 없으면 대상 부재로 통과한다.
# **차단 모드** (2026-08-12 · PLAN-048 3단계 종료 시 승격 · §2.3).
# **산문 소스 편입 (2026-08-29 · O-15 · 사용자 승인).** D9(§참조 도달성)와 내부 링크 검사는 이
# 검사기에만 있는데 대상이 파생본뿐이어서, **조립을 동결한 기간에는 정본의 죽은 §참조를 어떤
# 검사도 보지 않았다.** 소스에는 D9 와 링크만 대고 분량·표/그림·플레이스홀더는 대지 않는다 —
# 정본에 상한을 걸면 기록을 지우라는 요구가 된다. 편입 시점 실측은 위반 0 이다.
submission-check:
	uv run python scripts/submission_check.py

# 한국어 학술 문체 규격 검사 (paper/STYLE-KO-ACADEMIC.md · CLAUDE.md §8.1).
# 대상은 투고 파생본 계열뿐이다 — 산문 소스 + 조립 산출물. 작업 정본과 supplementary 는
# 감사 기록이므로 제외한다(submission-check 가 정본을 제외하는 것과 같은 이유).
# 보는 것은 넷 — S3 문장 길이 · T2 구어·은유 · T3 문두 접속어 · T5 주장 볼드.
# 나머지 규칙(문단 구조·서술어·용어 일관)은 사람이 지킨다: 통과는 필요조건이지 충분조건이 아니다.
style-check:
	uv run python scripts/style_check.py

# 영문 학술 문체 규격 검사 (paper/STYLE-EN-ACADEMIC.md).
# style-check 의 영문 대응이다 — 같은 자리에서 같은 일을 하되 **언어가 바뀌면 방향이 뒤집히는
# 규칙 셋**(주어 we 허용 · 단문 허용 ≤30단어 · 종결어미 대신 시제 규약)을 따로 본다.
# 판정 강도는 verdicts.yaml 이 한국어만 보므로, 영문 관용구(partial support · replicated ·
# did not transfer 등)의 금지열은 STYLE-EN §4 가 맡는다.
# **차단으로 승격했다 (2026-08-26 · PLAN-080 A-⑤).** 경고로 시작한 이유는 *"영문 본문이
# 끝나기 전에 차단으로 올리면 번역 커밋이 전부 막힌다"* 였고 그 조건은 해소됐다 — 승격 시점
# 실측은 **위반 0 건**(en_source · 파생 산출물 · cover-letter · declarations)이다.
style-check-en:
	uv run python scripts/style_check_en.py

# 용어 첫 등장 규율 검사 (paper/glossary-terms.yaml · STYLE V1·V2 · PLAN-066).
# style-check 가 어체의 표류를, verdicts 가 판정 강도의 표류를 막듯 이것은 **정보 제시 순서의
# 표류**를 막는다 — 절을 옮기거나 S5 로 이관하면 정의가 사용 뒤로 밀리는 일이 재구성마다
# 재발했다(PLAN-066 §1 실측: 파생본 위반 25건). 대상은 투고 파생본 계열뿐이다(style-check 와 같다).
# **차단으로 승격하였다 (2026-08-25 · PLAN-066 DoD 3 충족 · O-2 종결).** 착수 시점 25건이던
# G1·G2·G5 위반은 B-2·B-3′ 반영으로 0 이 되었고, 승격 시점 실측도 0 이다 — 켜면서 고친 문장은
# 없다. **G4(식별자 산문 사용)는 설계상 경고로 남는다**(CLAUDE.md §2.3-5). 승격 경로는
# verdicts·style-check 가 밟은 것과 같다.
# 영문 supplementary 가 원문의 수치를 그대로 옮겼는가 (PLAN-083 · CLAUDE.md §1-1).
# 번역은 사람이 하고 기계는 **측정값 불변만** 보증한다 — 표를 문자 단위로 복사하는
# build_submission_en 과 같은 규율이며, 산문·표가 뒤섞인 감사 기록에 맞춘 형태다.
supplementary-check-en:
	uv run python scripts/check_supplementary_en.py

glossary-check:
	uv run python scripts/check_glossary.py

# 용어별 첫 등장·정의 위치 대장 — PLAN-066 실측표와 glossary.md §J 의 원천. 손으로 세지 않는다.
glossary-inventory:
	uv run python scripts/check_glossary.py --warn --inventory

# 결정 안정성 표 — 동결 임계에서 판정이 전환되는 지점 (PLAN-060 B3 · 외부 검토 지적 3).
# 수치는 기존 산출물에서만 읽는다(concept_values.json · fault_matrix_v4.json · T4 판정 JSON).
# **임계는 움직이지 않는다** — 표가 보고하는 것은 판정과 전환점의 거리뿐이다.
tables-stability:
	uv run python -m sdkb_paper.analysis.decision_stability

tables-stability-check:
	uv run python -m sdkb_paper.analysis.decision_stability --check

# 투고 파생본을 산문 소스 + 동결 표에서 기계로 조립 (PLAN-048 3단계).
# 표의 수치는 축약 전 전문(S5)에서 문자 단위로 복사한다 — 손으로 옮겨 적지 않는다(§1-1).
# `paper/tables/` 의 생성 표는 `{{COPY:…|from:X.md}}` 로 가져온다(PLAN-060 B3).
submission-stage3: tables-stability-check
	uv run python scripts/build_submission_stage3.py

# 영문 투고본 — 산문은 en_source.md 가, 표·그림·서지는 한국어 파생본이 원본이다.
# 수치가 하나라도 달라지면 실패한다(rc 2). 본문 완성 전까지 산출은 초안 경로다.
submission-en:
	uv run python scripts/build_submission_en.py

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

# 개념·공리 계기판 (2026-08-23) — 선언 · 실체화 · 작동 세 층을 한 페이지로 잰다.
# **왜 있는가:** 세 층의 지표가 TTL·상류 리포트·코퍼스로 흩어져 있어 "공리 구현이 진척되고
# 있는가"에 답하려면 매번 처음부터 다시 재야 했다. 읽기 전용이며 코퍼스·qrel·게이트·통계
# 산출물을 하나도 쓰지 않는다. 재는 대상은 **동결 벤더 스냅샷과 하류 코퍼스·점수식**이다.
# 산출: data/reports/concept_status.md(사람) + concept_status.json(다음 실행의 델타 기준).
concept-status:
	uv run python -m sdkb_paper.analysis.concept_status

# 개념 쌍 관계 유사도 표 (PLAN-075 §12.5 · 순위 함수 `w_r` 항의 입력). 벤더 개념 그래프의
# 무향 최단 홉을 γ 로 감쇠한 표 — 199×199 상한이라 사전 계산해 두면 질의당 비용은 조회뿐이다.
# 동결값 γ=0.5 · H=2 는 결과를 보기 전에 박은 것이다(§12.3): 민감도는 인자로만 연다.
concept-rel:
	uv run python -m sdkb_paper.ontology.concept_relations

# 운용 효율 (PLAN-036 · 원고 §6.3 탐색적 표) — Effort@Recall · Candidate Reduction ·
# 깊이별 회수 곡선 · 질의당 추가 발견 건수. 동결 팔(runsets/O_pre_linker)의 run 재판독이며
# 새 검색이 없다. **탐색적 기술통계 — 개봉 분할이라 확증에 쓰지 않는다(CLAUDE §2.1).**
# 산출: paper/tables/ir_effort_test.md + data/processed/ir/effort_curve_test.csv(그림 입력).
effort:
	uv run python -m sdkb_paper.analysis.effort --write

# C2′ 전달 실험 (PLAN-038 §12 · RQ5) — 동결 run 상위 K=10 → 생성 → 결정적 채점.
# **`rag` 는 기본이 dry-run 이다**(호출 0). 유상 실행은 `make rag EXECUTE=1` 로만 —
# 1,188 호출 · 입력 34.37M 토큰(§12.6 실측)이며 되돌릴 수 없다.
# A층 산출물은 **탐색적**이다(§7 결정 "다") — 계측기 동결이 목적이고 확증은 B층에서 한다.
RAG_ARGS ?=
rag:
	uv run python -m sdkb_paper.rag.generate $(if $(EXECUTE),--execute,) $(RAG_ARGS)

# 입력 토큰 실측 — `bedrock:CountTokens` 는 **무과금**이다. 유상 실행 승인 전에 규모를
# 추정이 아니라 실측으로 못박는다(§12.6). 생성 호출 0.
ragcount:
	uv run python -m sdkb_paper.rag.count $(RAG_ARGS)

# 인용 정확도·환각률·근거 문장 일치 (LLM 판정자 미사용 · 재채점 시 바이트 동일).
# 산출: paper/tables/rag_transfer_test.md + data/processed/ir/rag/scores/*.json
rageval:
	uv run python -m sdkb_paper.rag.score --write

# T4 판정 — 하류 생성 층 비열등 (PLAN-047 §4.2 동결식 · B층 전용 · 봉인 열람이므로 사유 필수).
# 산출: paper/tables/rag_t4_verdict_test_b.md + data/processed/ir/rag/scores/rag_t4_verdict_test_b.json
t4:
	uv run python -m sdkb_paper.rag.t4 --split test_b --unseal --reason "$(REASON)" --write

# 실패 유형 분류 (PLAN-048 · C4) — 코딩 시트 생성. 결정적·무료·생성 호출 0.
# B층은 봉인 열람이므로 UNSEAL=1 REASON="..." 이 필요하다. 산출은 특허 본문을 포함하므로
# data/processed/ir/typology/ 아래에만 쓴다(§1-5 · gitignore).
TSPLIT ?= test
typology-sheet:
	uv run python -m sdkb_paper.analysis.failure_typology --split $(TSPLIT) \
	  $(if $(UNSEAL),--unseal --reason "$(REASON)",)

# 로컬 LLM 2종 × 반복 2회 전수 코딩. **순차 전용**(LLM_WORKERS=1) — 병렬은 VRAM 이 넘친다.
# 유료 API 호출 0. 프롬프트·모델·시드는 동결이며 결과를 본 뒤 고치지 않는다(§1-11).
typology-code:
	LLM_WORKERS=1 uv run python -m sdkb_paper.analysis.failure_typology --split $(TSPLIT) --code

# κ·합의율·유형 빈도표 → paper/tables/failure_typology.md
typology-table:
	uv run python -m sdkb_paper.analysis.failure_typology --table

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

# --- 판독 B (PLAN-047 §8) -----------------------------------------------------
# 순서가 이 두 타깃의 존재 이유다. `retrieve-b` 는 **정답 없이** run 만 만들고(봉인 미열람),
# `tables-b` 는 개봉이라 `UNSEAL=1` 과 사유를 요구한다. 봉인 열람은 원장에 남는다.
#   make retrieve-b                       ← 개봉 전 · 몇 번 돌려도 된다
#   make tables-b UNSEAL=1 REASON="..."   ← 개봉 1회 · 되돌릴 수 없다
retrieve-b:
	uv run python -m sdkb_paper.retrieval.bm25 --layer B --search-only
	uv run python -m sdkb_paper.retrieval.dense --layer B
	uv run python -m sdkb_paper.retrieval.hybrid --layer B
	uv run python -m sdkb_paper.analysis.results_table --split test_b --runs-only

tables-b:
	@test -n "$(UNSEAL)" || { echo "[판독 B] 개봉은 UNSEAL=1 과 REASON 이 있어야 한다 (PLAN-047 §13.3)"; exit 2; }
	@test -n "$(REASON)" || { echo "[판독 B] REASON 이 비어 있다 — 사유 없는 개봉은 하지 않는다"; exit 2; }
	uv run python -m sdkb_paper.analysis.results_table --split test_b --write \
		--unseal --reason "$(REASON)"
	uv run python -m sdkb_paper.analysis.subgroup --table --split test_b \
		--unseal --reason "$(REASON)"
	uv run python -m sdkb_paper.analysis.ablation --split test_b --p1 \
		--tau 0.7 --alpha 0.75 --w 0.25 0.0 0.25 0.5 --write \
		--unseal --reason "$(REASON)"

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

# --- 자원 델타 O/O′ (D-19 · H2 를 잴 수 있게 만드는 경로) --------------------
# H2 는 **변경 없는 동일 파이프라인에 O 와 O′ 를 넣은** 비교로만 잰다. run 경로에는 자원
# 차원이 없어 `make vendor` 뒤 재실행하면 O 의 run 이 덮어써지므로, **재벤더 전에** 얼린다.
#   make freeze-runset LABEL=O_pre_CR007 SPLIT=test NOTE="CR-007 적용 전"
#   ... make vendor → corpus → index → retrieve ...
#   make freeze-runset LABEL=O_post_CR007 SPLIT=test
#   make tgate-resource OLD=O_pre_CR007 NEW=O_post_CR007 SYSTEM=P1 SPLIT=test
# 적격심사 실패는 불통과가 아니라 **미검정**이다(종료코드 2) — T1·T2 를 돌리지 않는다.
freeze-runset:
	uv run python -m sdkb_paper.validate.runset --freeze $(LABEL) \
		--split $(or $(SPLIT),test) $(if $(NOTE),--note "$(NOTE)",)

runsets:
	uv run python -m sdkb_paper.validate.runset --list

tgate-resource:
	uv run python -m sdkb_paper.validate.t_gate --mode resource \
		--old-runset $(OLD) --new-runset $(NEW) --system $(or $(SYSTEM),P1) \
		--split $(or $(SPLIT),test) $(if $(GRAPH),--graph $(GRAPH),) \
		--baseline $(or $(GEN),g0)

# 판정 JSON 은 **실행 정체성이 들어간 이름**으로 나간다(mode·runset·system·split).
# 고정 경로 하나에 쓰면 다음 실행이 앞 판정을 지우고, data/processed 는 gitignore 라
# 복구 경로가 없다 — 실제로 EP3 의 판정이 그렇게 사라졌다(PLAN-060 §10). 같은 이름이
# 이미 있으면 게이트는 돌기 전에 멈춘다(--force 로만 덮는다).
#
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

# W9 (PLAN-025 · 사전등록 동결 a474126) — H1‴ 확증. 판정 규칙·층 정의는 **바꾸지 않고**
#   아직 판정한 적 없는 72 인스턴스(F11·F12 새 rep + 신규 교차결함 F13·F14·F15 + 정상 델타 27)를
#   주입해 복제한다. 인스턴스당 L2(HermiT) ~55초가 지배적 → 9-way 병렬 약 1.1시간.
#   `faults-holdout-judge` 는 격리본을 읽기만 해서 다시 판정한다(재주입 없음).
faults-holdout:
	uv run python -m sdkb_paper.analysis.faults --holdout --workers $(or $(WORKERS),9)

faults-holdout-judge:
	uv run python -m sdkb_paper.analysis.faults --holdout-judge --workers $(or $(WORKERS),9)

# 머지 전 전체 게이트: L0(무결성+신선도) + baseline 재조립 + L1 + L2 + L3 + 어휘 커버리지 측정
#   + 누출 감사 + T1·T2·T3. IR 산출물(run·코퍼스)이 없는 환경에서는 tgate 가 먼저 실패하므로
#   그래프만 검증하려면 `make gate-graph` 를 쓴다.
# --- 제2 도메인 프로파일 (EP5 · PLAN-064 A-1 · C7) ----------------------------
# **자원만 바뀌고 게이트 코드는 그대로다** — 그것이 이 타깃의 존재 이유이자 C3 의 코드 증거다.
# T1·T2 는 이 자원에 **설계상 없다**. 그래서 판정은 승인식이 아니라 부분 승인식이며
# (`accept=null` · `Accept_partial`), 그 사실을 JSON 스키마가 말한다.
#   make gate-profile PROFILE=brick GRAPH=<D_n.ttl> BASELINE=d0
gate-profile:
	uv run python -m sdkb_paper.validate.shacl_gate $(GRAPH) --shapes graph --profile $(or $(PROFILE),brick)
	uv run python -m sdkb_paper.validate.reasoner_gate $(GRAPH)
	uv run python -m sdkb_paper.validate.cq_runner $(GRAPH) --report --min-pass 0
	uv run python -m sdkb_paper.validate.t_gate --mode t3only --graph $(GRAPH) 		--baseline $(or $(BASELINE),d0) --profile $(or $(PROFILE),brick)

# 프로파일 세대 동결 (D0 기준 세대 → 이후 델타의 비교 기준)
#   make cq-freeze-profile PROFILE=brick GEN=d0 GRAPH=<D0.ttl> [AGAINST=<이전세대>]
cq-freeze-profile:
	uv run python -m sdkb_paper.validate.t3_cross_task_cq $(GRAPH) 		--freeze $(GEN) $(if $(AGAINST),--against $(AGAINST),) --profile $(or $(PROFILE),brick)

# EP5 전량 (A-4). 결함 21 + 정상 31 + 릴리스 계보 10 을 **각 1회** 판정한다. 재판정은 없다.
# 선행: `make ep5-freeze` (기준 세대 D₀ 동결 · **이 시점에 홀드아웃이 열린다**).
#   make ep5 [STAGE=faults|normal|lineage|all] [WORKERS=4]
ep5:
	uv run python -m sdkb_paper.analysis.ep5 --stage $(or $(STAGE),all) --workers $(or $(WORKERS),4)

# 기준 세대 D₀ = Brick v1.3.0 + 홀드아웃 A-Box. 동결이 곧 개봉이다(SPEC-010 §4).
ep5-freeze:
	uv run python -m sdkb_paper.analysis.ep5_freeze

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

# 개념 도식이 인용하는 수치를 산출물에서 다시 뽑아 동결한다 (그림 규격 F6 · paper/FIGURE-SPEC.md).
# 손으로 고치는 파일이 아니다 — 산출물이 갱신되면 이것을 돌리고 본문 수치도 함께 확인한다.
figure-data:
	uv run python -m sdkb_paper.viz.figdata

# 데이터 플롯(figures) + 개념 도식(concept). 개념 도식은 동결 수치와 산출물이 어긋나면
# 그리지 않고 멈춘다 — 낡은 수치를 담은 그림은 없는 그림보다 나쁘다.
figures:
	uv run python -m sdkb_paper.viz.figures
	uv run python -m sdkb_paper.viz.concept

# 영문 본문 그림 7종 — 라벨만 영어이고 그리기 코드·수치는 한국어판과 같은 한 벌이다
# (PLAN-082). 넘치는 라벨이 있으면 **그리지 않고 실패한다**.
figures-en:
	uv run python -m sdkb_paper.viz.concept --lang en
	uv run python -m sdkb_paper.viz.figures --lang en

# --- 온톨로지 탐색·모니터링 로컬 웹앱 (읽기 전용) ---
serve:
	uv run python -m sdkb_paper.explore.server --port $(or $(PORT),8000)
