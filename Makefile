.PHONY: setup lint test vendor snapshot baseline collect profile merge mapping candidates validate reason cq gate h1 h2 cpc cpc-vintage figures

setup:
	uv sync --all-extras

lint:
	uv run ruff check src tests

test:
	uv run pytest -q

# 근간 온톨로지(SDKB) 스냅샷을 data/external/sdkb/ 로 vendor.
# SDKB 쪽에서 `make owl convert` 를 먼저 돌려야 한다 (TTL 은 빌드 산출물이라 git 에 없다).
# SDKB_HOME 으로 원본 위치를 바꿀 수 있다: make vendor SDKB_HOME=/path/to/sdkb
vendor:
	uv run python -m sdkb_paper.ontology.vendor $(if $(SDKB_HOME),--sdkb-home $(SDKB_HOME),)

# baseline 그래프(graph_v0 = H1 의 "before") 를 스냅샷에서 조립. 결정적 산출물.
baseline:
	uv run python -m sdkb_paper.ontology.baseline

# 삼성전자·SK하이닉스 특허 수집 (KIPRIS). 응답은 sqlite 캐시 → 재실행해도 API 를 다시 안 때린다.
# make collect SMOKE=1 이면 클래스 1개만 (파이프라인 관통 검증용)
collect:
	uv run python -m sdkb_paper.collect.collect $(if $(SMOKE),--smoke,)

# 정제 + 데이터 프로파일 (CLAUDE.md §4 의무). 논문 표 4 의 원천.
profile:
	uv run python -m sdkb_paper.preprocess.profile

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
	uv run python -m sdkb_paper.ontology.delta
	uv run python -m sdkb_paper.ontology.merge_cli

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

# --- 3층 검증 게이트 (논문 §3.3) --------------------------------------------
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

# 머지 전 전체 게이트: 스냅샷 무결성 + baseline 재조립 + L1 + L2 + L3
gate: snapshot validate reason cq

# H1 검정 — 공정 단계별 커버리지 (Wilcoxon 단측). 게이트를 통과한 두 스냅샷을 읽기만 한다.
# 표본 집합은 확장 49 와 복원 이전 20 **양쪽**으로 병기 보고된다 (PLAN-005).
h1:
	uv run python -m sdkb_paper.analysis.h1_cli

# H2 의 대조군 분류 데이터 (BigQuery patents-public-data · GCP 인증 필요).
#   cpc         — 현재 스냅샷의 CPC. KIPRIS 는 IPC 만 주는데 대조 코드 2개가 CPC 전용이라
#                 IPC 말뭉치에서 구조적으로 0건이었다 (PLAN-007 §1).
#   cpc-vintage — 날짜별 **동결 스냅샷**(2017-10 …). H10 스킴은 전량 2021년 이후의 소급
#                 재분류다 — 현재 코드로 만든 시계열은 구조적으로 늦을 수 없다.
cpc:
	uv run python -m sdkb_paper.collect.bq_cpc

cpc-vintage:
	uv run python -m sdkb_paper.collect.bq_cpc --vintage

# H2 검정 — 개념 단위 vs 코드 단위 시계열의 탐지 시차 (단측 부호검정 · PLAN-006).
# 사례 7건·신호 규칙·판정 규칙은 시계열을 보기 전에 동결됐다 (mappings/h2_cases.csv).
h2:
	uv run python -m sdkb_paper.analysis.h2_cli

# §4.5 강건성 — 패밀리(DOCDB) 중복 제거 전후 비교.
#   family     — BigQuery 에서 DOCDB family_id 조인 (GCP 인증 필요). KIPRIS 원데이터에는
#                우선권·패밀리 필드가 없어 이 조인 외에는 패밀리를 정직하게 잴 방법이 없다.
#   robustness — dedup 된 델타로 G₁ 을 다시 짓고(같은 게이트 통과) H1·H2′ 를 **재검정**한다.
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
