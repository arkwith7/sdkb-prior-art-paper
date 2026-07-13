.PHONY: setup lint test vendor snapshot baseline collect profile merge mapping validate reason cq gate h1 figures

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

# 델타 트리플 생성 + 게이트 통과분만 병합 → graph_v1 (= G₁, H1 의 "after")
merge:
	uv run python -m sdkb_paper.ontology.delta
	uv run python -m sdkb_paper.ontology.merge_cli

# IPC/CPC 룰 커버리지 — 특허를 수집하기 전에 매핑의 사각지대를 드러낸다
mapping:
	uv run python -m sdkb_paper.ontology.mapping

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

figures:
	uv run python -m sdkb_paper.viz.figures
