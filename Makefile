.PHONY: setup lint test vendor snapshot baseline mapping validate reason cq gate figures

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

# IPC/CPC 룰 커버리지 — 특허를 수집하기 전에 매핑의 사각지대를 드러낸다
mapping:
	uv run python -m sdkb_paper.ontology.mapping

# 스냅샷 무결성: 커밋된 SDKB 스냅샷이 PROVENANCE 의 sha256 과 일치하는가.
# SDKB 원본이 필요 없다 — CI 에서 매 push 마다 돈다. baseline 의 출처가 거짓이 되는 것을 막는다.
snapshot:
	uv run python -m sdkb_paper.ontology.vendor --verify

# --- 3층 검증 게이트 (논문 §3.3) --------------------------------------------
# 게이트 대상은 두 그래프다:
#   graph_v0     — 실물 baseline. 얼린 스냅샷과 코드가 여전히 정합한지 본다. 특허 0건.
#   mini_graph   — 합성 특허 3건. 특허 0건인 baseline 으로는 exercise 되지 않는
#                  PatentShape/CQ01/CQ02 를 실제로 때린다. 둘 다 있어야 게이트가 non-vacuous.

# L1 구조 제약 (SHACL)
validate: baseline
	uv run python -m sdkb_paper.validate.shacl_gate data/processed/graph_v0.ttl
	uv run python -m sdkb_paper.validate.shacl_gate data/samples/mini_graph.ttl

# L2 논리 일관성 (HermiT — Java 필요)
reason: baseline
	uv run python -m sdkb_paper.validate.reasoner_gate data/processed/graph_v0.ttl

# L3 기능 검증 (Competency Question)
#   graph_v0 은 특허가 0건이므로 CQ01/CQ02 가 응답 불가인 것이 정상 — 게이트가 아니라 **측정**이다
#   (--min-pass 0). 이 값이 논문 §4.2 의 G₀ 열이 된다. 회귀 감시는 통합 테스트가 맡는다.
#   mini_graph 는 특허가 있으므로 100% 를 요구하는 진짜 게이트다.
cq: baseline
	uv run python -m sdkb_paper.validate.cq_runner data/processed/graph_v0.ttl --report --min-pass 0
	uv run python -m sdkb_paper.validate.cq_runner data/samples/mini_graph.ttl --report

# 머지 전 전체 게이트: 스냅샷 무결성 + baseline 재조립 + L1 + L2 + L3
gate: snapshot validate reason cq

figures:
	uv run python -m sdkb_paper.viz.figures
