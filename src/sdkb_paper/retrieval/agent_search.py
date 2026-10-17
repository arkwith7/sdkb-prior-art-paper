"""파일럿 Agent 검색 하네스 — 상류 `llm_query_agent.py` 이식 + 하류 마스크·계측·비용 통제 (PLAN-096 R1·R5·R7·R9).

이식 원본: 상류 `scripts/llm_query_agent.py` @ `ad54abe` (sha 는 `data/external/sdkb_pilot/PROVENANCE.json`).
상류와 같은 것: 합집합 판정을 LLM 이 아니라 시스템이 한다 · 검색식 단위 채택 · 합집합 ≤ 예산 · 절단 금지 ·
도구 결과에 문헌 식별자를 싣지 않는다 · thinking 블록을 그대로 되돌려 보낸다 · 고정 접두 캐시 지점.
하류가 더한 것:
  (1) **적격 후보 마스크** — `EligibleSearch` 가 에뮬레이터 결과에 `CandidateMask` 를 곱한 뒤에야
      `count_results` 건수 · `submit` 채택 · 예산을 계산한다(PLAN-094 §2.4.4 ⑤ · §4.2 ⑦).
  (2) **지식 제공 두 방식** — A3 블록 · A4 조회 도구(같은 `KnowledgeView`).
  (3) **계측** — 턴·도구 호출별 지연, 지식 도구 반환량, usage(캐시 포함), 실패 유형.
  (4) **비용 상한** — `CostGuard` 가 누적 원장으로 상한을 지킨다. 상한은 여러 번의 실행에 걸쳐 합산된다.
  (5) **누출 내용 스캔** — 공보번호가 든 검색식은 실행하지 않고 실패로 기록한다(PLAN-094 §3.6).

**유료 호출은 `make_client(paid=True)` 로만 열린다.** 무과금 검증은 `ScriptedClient` 를 쓴다.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace

from ..validate.leakage_check import scan_publication_numbers
from . import agent_frozen as F


# ── (1) 적격 후보 ──────────────────────────────────────────────────────────────
class EligibleSearch:
    """에뮬레이터 결과 위에 적격 후보 마스크를 건다. `mask=None` 이면 상류 조건(자기 문서만 제외)."""

    def __init__(self, emulator, mask=None, fields: tuple[str, ...] = F.FIELDS):
        self.emu, self.mask, self.fields = emulator, mask, tuple(fields)
        self._allowed: dict[str, frozenset[str]] = {}

    def allowed(self, qid: str) -> frozenset[str] | None:
        if self.mask is None:
            return None
        if qid not in self._allowed:
            arr = self.mask.allowed_array(qid)
            self._allowed[qid] = frozenset(d for d, ok in zip(self.mask.doc_ids, arr) if ok)
        return self._allowed[qid]

    def run(self, qid: str, query: str, ipc=None) -> set[str]:
        res = self.emu.run(query, fields=self.fields, ipc=list(ipc) if ipc else None, exclude=(qid,))
        ok = self.allowed(qid)
        return set(res) if ok is None else {d for d in res if d in ok}


# ── (4) 비용 상한 ──────────────────────────────────────────────────────────────
def usage_cost(u: dict) -> float:
    """응답 usage → USD(안전 계수 포함). 입력 토큰은 캐시 미적용분만 들어 있다(SDK 의미)."""
    p = F.PRICE_PER_MTOK
    raw = (u.get("input_tokens", 0) * p["input"] + u.get("output_tokens", 0) * p["output"]
           + u.get("cache_write", 0) * p["cache_write"] + u.get("cache_read", 0) * p["cache_read"]) / 1e6
    return raw * F.PRICE_SAFETY


class BudgetExhausted(RuntimeError):
    pass


class CostGuard:
    """누적 원장(JSON Lines) 기반 상한. 다음 실행은 `spent + reserve ≤ cap` 일 때만 시작한다."""

    def __init__(self, ledger: Path | None, cap: float = F.COST_CAP_USD,
                 reserve: float = F.RUN_RESERVE_USD):
        self.ledger, self.cap, self.reserve = ledger, cap, reserve
        self.spent = 0.0
        if ledger is not None and Path(ledger).exists():
            for line in Path(ledger).read_text(encoding="utf-8").splitlines():
                if line.strip():
                    self.spent += float(json.loads(line)["usd"])

    def can_start(self) -> bool:
        return self.spent + self.reserve <= self.cap

    def exceeded(self) -> bool:
        return self.spent >= self.cap

    def add_flat(self, usd: float, tag: str, note: str) -> float:
        """usage 를 알 수 없는 실패(응답 없는 예외)의 보수적 비용."""
        self.spent += usd
        if self.ledger is not None:
            Path(self.ledger).parent.mkdir(parents=True, exist_ok=True)
            with Path(self.ledger).open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"tag": tag, "usd": round(usd, 6), "flat": note}) + "\n")
        return usd

    def add(self, usage: dict, tag: str) -> float:
        c = usage_cost(usage)
        self.spent += c
        if self.ledger is not None and c > 0:
            Path(self.ledger).parent.mkdir(parents=True, exist_ok=True)
            with Path(self.ledger).open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"tag": tag, "usd": round(c, 6), "usage": usage}) + "\n")
        return c


# ── 세션 ──────────────────────────────────────────────────────────────────────
@dataclass
class Session:
    search: EligibleSearch
    q: str
    budget: int = F.BUDGET
    knowledge: object | None = None          # KnowledgeView (A4 만 도구로 노출)
    union: set = field(default_factory=set)
    search_calls: int = 0
    knowledge_calls: int = 0
    leak_hits: int = 0
    log: list = field(default_factory=list)

    def tool(self, name: str, inp: dict) -> str:
        t0 = time.perf_counter()
        out = self._tool(name, inp)
        self.log[-1]["ms"] = round((time.perf_counter() - t0) * 1000, 2)
        self.log[-1]["ret_chars"] = len(out)
        return out

    def _tool(self, name: str, inp: dict) -> str:
        if name in ("count_results", "submit"):
            query, ipc = inp.get("query", ""), inp.get("ipc")
            if self.search_calls >= F.SEARCH_CALLS:
                self.log.append({"tool": name, "query": query, "ipc": ipc, "error": "limit"})
                return json.dumps({"error": "search call limit reached — finish now"})
            self.search_calls += 1
            leaks = scan_publication_numbers(query)
            if leaks:
                self.leak_hits += 1
                self.log.append({"tool": name, "query": query, "ipc": ipc, "error": "leak", "leak": leaks})
                return json.dumps({"error": "query rejected: it contains a patent publication number",
                                   "search_calls_left": F.SEARCH_CALLS - self.search_calls})
            try:
                res = self.search.run(self.q, query, ipc)
            except ValueError as e:
                self.log.append({"tool": name, "query": query, "ipc": ipc, "error": str(e)})
                return json.dumps({"error": f"invalid query: {e}",
                                   "search_calls_left": F.SEARCH_CALLS - self.search_calls})
            new = len(res - self.union)
            accepted = False
            if name == "submit":
                merged = self.union | res
                accepted = bool(res) and len(merged) <= self.budget
                if accepted:
                    self.union = merged
            self.log.append({"tool": name, "query": query, "ipc": ipc, "size": len(res), "new": new,
                             "accepted": accepted, "docs": sorted(res) if name == "submit" and accepted else None})
            out = {"results": len(res), "new_vs_accepted": new, "accepted_set_size": len(self.union),
                   "budget_left": self.budget - len(self.union),
                   "search_calls_left": F.SEARCH_CALLS - self.search_calls}
            if name == "submit":
                out["accepted"] = accepted
            return json.dumps(out)
        if self.knowledge is None or name not in ("list_element_types", "examination_history"):
            self.log.append({"tool": name, "input": inp, "error": "unknown tool"})
            return json.dumps({"error": f"unknown tool {name}"})
        if self.knowledge_calls >= F.KNOWLEDGE_CALLS:
            self.log.append({"tool": name, "input": inp, "error": "limit"})
            return json.dumps({"error": "examination history call limit reached"})
        self.knowledge_calls += 1
        self.log.append({"tool": name, "input": inp})
        if name == "list_element_types":
            return json.dumps(self.knowledge.list_types(), ensure_ascii=False)
        return json.dumps(self.knowledge.history(inp.get("element_type", "")), ensure_ascii=False)


# ── 루프(상류 run_one 이식) ───────────────────────────────────────────────────
def _with_cache(msg: dict) -> dict:
    c = msg["content"]
    blocks = [{"type": "text", "text": c}] if isinstance(c, str) else [dict(b) if isinstance(b, dict) else b for b in c]
    last = blocks[-1]
    if isinstance(last, dict):
        blocks[-1] = {**last, "cache_control": {"type": "ephemeral"}}
        return {**msg, "content": blocks}
    return msg


def user_message(arm: str, claim: str, abstract: str, knowledge_block: str | None) -> str:
    msg = (f"Review budget: at most {F.BUDGET} unique candidate documents. Search calls available: {F.SEARCH_CALLS}.\n\n"
           f"Idea (claim 1):\n{claim}\n\nAbstract:\n{abstract}")
    if arm == "A3":
        msg += "\n\n" + F.KNOWLEDGE_BLOCK_INTRO.strip() + "\n\n" + (knowledge_block or "(no element type with examination history)")
    return msg


def run_one(client, arm: str, claim: str, abstract: str, sess: Session, guard: CostGuard,
            tag: str, knowledge_block: str | None = None) -> dict:
    user = user_message(arm, claim, abstract, knowledge_block)
    messages = [{"role": "user", "content": user}]
    usage = {"input_tokens": 0, "output_tokens": 0, "cache_read": 0, "cache_write": 0}
    turns, status, served, cost = [], "ok", None, 0.0
    system = [{"type": "text", "text": F.system_prompt(arm), "cache_control": {"type": "ephemeral"}}]
    for _ in range(F.MAX_TURNS):
        req = messages[:-1] + [_with_cache(messages[-1])]
        t0 = time.perf_counter()
        resp = client.messages.create(model=F.MODEL, max_tokens=F.MAX_TOKENS, system=system,
                                      tools=F.tools_for(arm), output_config={"effort": F.EFFORT}, messages=req)
        ms = round((time.perf_counter() - t0) * 1000, 1)
        u = {"input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens,
             "cache_read": getattr(resp.usage, "cache_read_input_tokens", 0) or 0,
             "cache_write": getattr(resp.usage, "cache_creation_input_tokens", 0) or 0}
        for k in usage:
            usage[k] += u[k]
        cost += guard.add(u, tag)
        served = getattr(resp, "model", None)
        texts = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
        turns.append({"ms": ms, "stop": resp.stop_reason, **u, "text": texts})
        if resp.stop_reason == "refusal":
            status = "refusal"
            break
        if resp.stop_reason == "max_tokens":
            status = "max_tokens"
            break
        calls = [b for b in resp.content if getattr(b, "type", None) == "tool_use"]
        messages.append({"role": "assistant", "content": resp.content})
        if not calls:
            break
        if guard.exceeded():
            status = "cost_cap"
            break
        messages.append({"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": c.id, "content": sess.tool(c.name, c.input)} for c in calls]})
    else:
        status = "max_turns"
    return {"status": status, "usage": usage, "cost_usd": round(cost, 6), "served_model": served,
            "turns": turns, "user_chars": len(user),
            "knowledge_block_chars": len(knowledge_block or "") if arm == "A3" else 0}


# ── 클라이언트 ────────────────────────────────────────────────────────────────
def make_client(*, paid: bool):
    """실제 Bedrock 클라이언트. **paid=True 가 아니면 만들지 않는다**(무과금 검증 단계 보호)."""
    if not paid:
        raise PermissionError("유료 호출은 승인 후 --paid 로만 연다 (PLAN-096 D4)")
    from anthropic import AnthropicBedrock
    from dotenv import load_dotenv

    from ..config import ROOT, get_secret
    load_dotenv(ROOT / ".env")                       # 접근 키를 환경으로(상류와 같다 · 값은 기록하지 않는다)
    return AnthropicBedrock(aws_region=get_secret("AWS_REGION"), max_retries=3)


class ScriptedClient:
    """LLM 대역 — 미리 정한 정책이 도구 호출을 낸다. usage 를 보고해 계측·상한을 검사할 수 있다.

    `policy(turn_index, messages) -> list[tuple[name, input]]` 가 빈 목록을 내면 종료 턴(text 만)이다.
    """

    def __init__(self, policy, usage=(1000, 200), model="scripted"):
        self.policy, self.usage, self.model_name = policy, usage, model
        self.calls = 0
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kw):
        turn = self.calls
        self.calls += 1
        acts = self.policy(turn, kw["messages"])
        content = [SimpleNamespace(type="text", text=f"turn {turn}")]
        for i, (name, inp) in enumerate(acts):
            content.append(SimpleNamespace(type="tool_use", id=f"t{turn}_{i}", name=name, input=inp))
        u = SimpleNamespace(input_tokens=self.usage[0], output_tokens=self.usage[1],
                            cache_read_input_tokens=0, cache_creation_input_tokens=0)
        return SimpleNamespace(content=content, usage=u, model=self.model_name,
                               stop_reason="tool_use" if acts else "end_turn")
