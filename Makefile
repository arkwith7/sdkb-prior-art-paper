.PHONY: setup lint test vendor baseline mapping validate cq gate figures

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

# SHACL 게이트: 대상 그래프를 shapes 전체로 검증
validate:
	uv run python -m sdkb_paper.validate.shacl_gate data/samples/mini_graph.ttl

# Competency Question 통과율 리포트
cq:
	uv run python -m sdkb_paper.validate.cq_runner data/samples/mini_graph.ttl --report

# 머지 전 전체 게이트 (SHACL + CQ)
gate: validate cq

figures:
	uv run python -m sdkb_paper.viz.figures
