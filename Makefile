.PHONY: setup lint test validate cq gate figures

setup:
	uv sync --all-extras

lint:
	uv run ruff check src tests

test:
	uv run pytest -q

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
