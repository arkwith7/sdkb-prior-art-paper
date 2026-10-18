"""파일럿 동결 상수 · 프롬프트 · 단가 — PLAN-094 §3.1–3.2 · §4.4 · PLAN-096 D5.

`rag/frozen.py` 와 같은 형식이다. **본실험 사전등록에서 값과 프롬프트 sha 를 동결**하며, 파일럿 동안
바꿀 수 있는 것은 실행 불능 결함(형식 · 도구 스키마)뿐이다(PLAN-094 §4.4 수정 허용 범위).

팔 정의(PLAN-094 §3.1 · 2026-10-17 정정 반영)
  A1 일반 지시 Agent   — 상류 b 골격(시스템 지시 + 검색 도구 두 개)
  A2 요소별 계획 Agent — A1 + 요소 분해 계획 지시 블록 하나
  A3                   — A2 + 심사 이력 집계 정보를 표 블록으로(user 메시지)
  A4                   — A2 + 같은 정보를 조회 도구로(호출 ≤ KNOWLEDGE_CALLS)
  A0                   — LLM 없음 · 혼합 순위(B3) 상위 BUDGET (agent_eval 이 계산)
A1–A4 는 모델 · effort · 공통 검색 도구 · 호출 상한 · 턴 상한 · 예산이 같다.
"""
from __future__ import annotations

import hashlib
import json

# ── 모델·설정(상류 t4_freeze_v1 과 같은 값) ────────────────────────────────────
MODEL = "global.anthropic.claude-opus-5-5"      # Bedrock 전역 프로파일(상류 동결과 같음)
EFFORT = "medium"                               # 본실험 값은 파일럿 뒤 PLAN-094 §3.10-7 에서 동결
MAX_TOKENS = 16_000
MAX_TURNS = 24
SEARCH_CALLS = 12                               # count_results + submit 합계
KNOWLEDGE_CALLS = 6                             # A4 지식 도구 합계
BUDGET = 200                                    # 검토 문헌 수 상한
FIELDS = ("AB", "CL")                           # PLAN-094 §2.4.4 ④ — 다섯 팔 공통(제목 제외)
ARMS = ("A1", "A2", "A3", "A4")
# 수정 A4(2026-10-18 · 사용자 결정) — 기존 A4 와 기록이 섞이지 않게 이름을 따로 둔다. 기존 A4 정의는 바꾸지 않는다.
ARMS_R2 = ("A3", "A4r")
MANDATORY_TOOL_ID = "toolu_harness_k0"            # 하네스가 실행한 의무 조회의 tool_use id

# ── 단가(USD / 1M 토큰) · 비용 상한 ───────────────────────────────────────────
# Anthropic 직접 API 요율(claude-api 참고 자료 · 2026-10-06 기준 표). **Bedrock 요율은 별도 고지되며
# 확인하지 않았다** — 그래서 상한 판정에는 안전 계수를 곱한다. 실제 청구액은 사후 AWS 청구서로 대조한다.
PRICE_PER_MTOK = {"input": 4.00, "output": 20.00, "cache_write": 5.00, "cache_read": 0.20}
PRICE_SAFETY = 1.25
COST_CAP_USD = 30.0                             # 연기 시험 + 파일럿 합계(사용자 2026-10-17)
RUN_RESERVE_USD = 0.50                          # 다음 실행 시작 전 남아 있어야 하는 최소 여유
# 실패 호출·재시도 비용도 상한에 넣는다(사용자 2026-10-17). 응답 없이 끝난 예외는 usage 를 알 수 없으므로
# 요청 1회의 최악 추정(입력 ~30k · 출력 16k 토큰 ≈ $0.44)을 올려 USD 0.50 을 원장에 보수적으로 적는다.
ERROR_CHARGE_USD = 0.50
FAILURE_MIN_RUNS = 5                            # 실패율 판정은 팔별 완료 실행이 이 수 이상일 때부터

# ── 고장 정의(결과와 무관한 실패만 · rag/frozen.py 선례) ──────────────────────────
FAILURE_RATE_STOP = 0.20                        # 팔별 실패율이 넘으면 중단
LEAK_HITS_STOP = 3                              # 누출 내용 스캔 검출 누적이 넘으면 중단

SYNTAX = """KIPRIS-style boolean query syntax (this is exactly how queries are executed):
- `A+B` OR, `A*B` AND, `!A` NOT, parentheses for grouping, precedence ! > * > +.
- `"..."` exact phrase. Unquoted words separated by spaces are ANDed.
- Korean terms match as substrings ("식각" also matches "식각하는"). English terms match at word starts ("etch" matches "etching").
- Searched fields: abstract, claims. The collection contains Korean patents and English/Japanese-origin documents (mostly English text).
- Optional `ipc`: list of IPC codes (subclass "H01L", main group "H01L21", or group "H01L21/306"); old/new IPC versions are mapped automatically. A query with ipc only returns documents having one of those codes."""

SYSTEM_BASE = f"""You are a patent search specialist building structured prior-art searches for a new technical idea.
Goal: collect a candidate set that contains as many documents as possible that a patent examiner would cite against the idea
(novelty / inventive step), while the total number of unique candidate documents stays within the review budget.
Examiners often combine several documents, each disclosing only some of the idea's elements, so partial-element searches are useful.

Rules of the search system:
- `count_results` runs a query and reports how many documents it returns and how many would be new to your accepted set. It does not add anything.
- `submit` runs a query and adds ALL its documents to the accepted set only if the accepted set stays within the budget; otherwise it is rejected and nothing is added. Documents are never truncated.
- Search calls (`count_results` + `submit`) are limited in total. When you are done, reply with a short final message and no tool call.

{SYNTAX}"""

PLAN_BLOCK = """
Search procedure (follow it):
1. Before any search, write a numbered list of the idea's claim elements.
2. Write a search plan: at least one search per element or small group of elements, plus searches that combine elements.
3. Execute the plan with the tools. After each result, revise the query when it returns too many or too few documents.
4. Finish when the plan is done, the budget is used, or the search calls run out."""

KNOWLEDGE_BLOCK_INTRO = """
Examination history summary (aggregated from past examiner judgments on OTHER applications; no document identifiers).
For each element type found in this idea's claim it gives how examiners judged claims containing that element type:
the share of novelty vs inventive-step grounds, whole-claim vs added-limitation judgments, how often a design-choice
or predictable-effect rationale or common general knowledge was relied on, and the IPC main groups of the documents they cited.
It is a statistical summary, not a rule. Use it only if it helps plan your searches."""

KNOWLEDGE_TOOL_INTRO = """
An examination history tool is available (aggregated from past examiner judgments on OTHER applications; no document identifiers).
`list_element_types` lists the element types found in this idea's claim; `examination_history` returns, for one element type,
the share of novelty vs inventive-step grounds, whole-claim vs added-limitation judgments, how often a design-choice or
predictable-effect rationale or common general knowledge was relied on, and the IPC main groups of the documents examiners cited.
It is a statistical summary, not a rule. Use it only if it helps plan your searches."""

KNOWLEDGE_TOOL_INTRO_R = """
An examination history tool is available (aggregated from past examiner judgments on OTHER applications; no document identifiers).
Before your first search the system has already called `get_examination_history` for you; its full result is in the conversation.
You may call `list_element_types` or `examination_history` for one element type again if useful. It is a statistical summary,
not a rule. Use it only if it helps plan your searches."""

SEARCH_TOOLS = [
    {"name": "count_results", "description": "Run a query without accepting it. Returns result count, how many are new versus the accepted set, and the remaining budget.",
     "input_schema": {"type": "object", "properties": {
         "query": {"type": "string", "description": "Boolean query in the syntax described in the system prompt."},
         "ipc": {"type": "array", "items": {"type": "string"}, "description": "Optional IPC codes to restrict the query."}},
         "required": ["query"], "additionalProperties": False}},
    {"name": "submit", "description": "Run a query and accept all its documents into the candidate set if the set stays within the budget; otherwise reject.",
     "input_schema": {"type": "object", "properties": {
         "query": {"type": "string"}, "ipc": {"type": "array", "items": {"type": "string"}}},
         "required": ["query"], "additionalProperties": False}},
]
KNOWLEDGE_TOOLS = [
    {"name": "list_element_types", "description": "List the element types (concept identifiers) found in this idea's claim that have examination history.",
     "input_schema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "examination_history", "description": "Aggregated examination history for one element type from list_element_types.",
     "input_schema": {"type": "object", "properties": {"element_type": {"type": "string"}},
                      "required": ["element_type"], "additionalProperties": False}},
]


GET_ALL_TOOL = {"name": "get_examination_history",
                "description": "Aggregated examination history for every element type found in this idea's claim (same content for every call).",
                "input_schema": {"type": "object", "properties": {}, "additionalProperties": False}}


def system_prompt(arm: str) -> str:
    """팔별 시스템 프롬프트. A3 의 지식 블록은 질의마다 다르므로 user 메시지에 붙는다(system 은 고정)."""
    if arm == "A1":
        return SYSTEM_BASE
    if arm in ("A2", "A3"):
        return SYSTEM_BASE + "\n" + PLAN_BLOCK
    if arm == "A4":
        return SYSTEM_BASE + "\n" + PLAN_BLOCK + "\n" + KNOWLEDGE_TOOL_INTRO
    if arm == "A4r":
        return SYSTEM_BASE + "\n" + PLAN_BLOCK + "\n" + KNOWLEDGE_TOOL_INTRO_R
    raise ValueError(arm)


def tools_for(arm: str) -> list[dict]:
    if arm == "A4r":
        return SEARCH_TOOLS + [GET_ALL_TOOL] + KNOWLEDGE_TOOLS
    return SEARCH_TOOLS + (KNOWLEDGE_TOOLS if arm == "A4" else [])


def prompt_sha(arm: str) -> str:
    """골격 해시 — 시스템 · 도구 · 설정. 질의별 내용(청구항 · 지식 블록 본문)은 제외."""
    payload = {"system": system_prompt(arm), "tools": tools_for(arm), "model": MODEL, "effort": EFFORT,
               "max_tokens": MAX_TOKENS, "search_calls": SEARCH_CALLS, "knowledge_calls": KNOWLEDGE_CALLS,
               "budget": BUDGET, "fields": list(FIELDS),
               "knowledge_block_intro": KNOWLEDGE_BLOCK_INTRO if arm == "A3" else None}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
