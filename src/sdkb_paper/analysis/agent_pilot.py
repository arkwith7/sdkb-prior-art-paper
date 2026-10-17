"""파일럿 실행기 · A0 · 채점 · 행동 지표 · 언어 구성 진단 (PLAN-096 R3 · R9–R13).

**dev 분할만 받는다.** 정답은 `load_qrel_for_split("dev")`(봉인 원장 비기록 통로)로만 읽는다 — 다른 분할을
부르면 즉시 실패한다(R11 가드). 유료 호출은 `--paid` 가 있을 때만 열리며, 이번 승인 범위에서는 쓰지 않는다.

CLI
  python -m sdkb_paper.analysis.agent_pilot sample              # 30질의 층화 표집(시드 고정) → sample.json
  python -m sdkb_paper.analysis.agent_pilot dryrun --n 1        # LLM 대역 · 실자료 · 무과금 · 5팔
  python -m sdkb_paper.analysis.agent_pilot run --paid --smoke  # (승인 후에만) 연기 시험
  python -m sdkb_paper.analysis.agent_pilot run --paid          # (승인 후에만) 본 실행 · 재개 가능
  python -m sdkb_paper.analysis.agent_pilot report
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
import time
from collections import Counter
from pathlib import Path

from .. import config

PILOT_SPLIT = "dev"
SEED = 20261017
N_SAMPLE = 30
RUNS = config.PILOT_DIR / "runs"
RUNS_SMOKE = config.PILOT_DIR / "runs_smoke"
FREEZE = Path(config.ROOT) / "01.code_spec" / "plans" / "PLAN-096-freeze.json"
FATAL = ("PermissionDeniedError", "BadRequestError", "NotFoundError", "AuthenticationError")
LEDGER = config.PILOT_DIR / "cost_ledger.jsonl"
_HANGUL = re.compile(r"[가-힣]")
_ASCII_WORD = re.compile(r"[A-Za-z]{3,}")


def _guard_split(split: str) -> None:
    if split != PILOT_SPLIT:
        raise PermissionError(f"파일럿은 dev 만 받는다 (요청: {split!r}) — 확증 분할 접근 금지")


def load_gold(split: str = PILOT_SPLIT) -> dict[str, set[str]]:
    _guard_split(split)
    from .metrics import load_qrel_for_split

    return {q: set(v) for q, v in load_qrel_for_split(split).items() if v}


# ── 표집(R12) ─────────────────────────────────────────────────────────────────
def stratified_sample(gold: dict[str, set[str]], lang: dict[str, str], n_elem: dict[str, int],
                      n: int = N_SAMPLE, seed: int = SEED) -> list[str]:
    """층 = 외국어 정답 포함 여부 × 청구항 1항 요소 수(≤3 / >3). 층 비율은 모집단 비율 · 최대 잔여 배분."""
    strata: dict[tuple, list[str]] = {}
    for q in sorted(gold):
        key = (any(lang.get(d) != "ko" for d in gold[q]), n_elem.get(q, 0) > 3)
        strata.setdefault(key, []).append(q)
    total = sum(len(v) for v in strata.values())
    quota = {k: n * len(v) / total for k, v in strata.items()}
    alloc = {k: int(q) for k, q in quota.items()}
    for k in sorted(quota, key=lambda k: (-(quota[k] - alloc[k]), k))[: n - sum(alloc.values())]:
        alloc[k] += 1
    rng = random.Random(seed)
    out = []
    for k in sorted(strata):
        out += sorted(rng.sample(strata[k], alloc[k]))
    return sorted(out)


# ── A0 (R3) ───────────────────────────────────────────────────────────────────
def a0_top(ranked: list[str], allowed: frozenset[str], k: int) -> list[str]:
    """순위 목록을 **먼저 적격 후보로 거른 뒤** 상위 k. 마스크 → 절단 순서가 Boolean 팔과 같다."""
    return [d for d in ranked if d in allowed][:k]


def load_run(path: Path, qids: set[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            q, _, d, r, *_ = line.split()
            if q in qids:
                out.setdefault(q, []).append((int(r), d))
    return {q: [d for _, d in sorted(v)] for q, v in out.items()}


# ── 채점(R11) ─────────────────────────────────────────────────────────────────
def recall(selected: set[str], gold: set[str], family: dict[str, str] | None = None) -> float:
    """분모 A — 코퍼스 안 정답. `family` 를 주면 패밀리 병합(정답 패밀리 중 하나라도 회수되면 적중)."""
    if not gold:
        return float("nan")
    if family is None:
        return len(selected & gold) / len(gold)
    gf = {family.get(d, d) for d in gold}
    sf = {family.get(d, d) for d in selected}
    return len(gf & sf) / len(gf)


# ── 행동 지표 · 언어 구성(R10) ────────────────────────────────────────────────
def behavior(rec: dict, gold: set[str], lang: dict[str, str]) -> dict:
    """로그에서 바로 세는 지표 — **사용·회수 경로의 추적이지 인과적 기여가 아니다**(PLAN-096 R10)."""
    log = rec.get("log", [])
    searches = [e for e in log if e.get("tool") in ("count_results", "submit")]
    executed = [e for e in searches if "size" in e]
    queries = [e.get("query") or "" for e in searches]
    first_hit: dict[str, int] = {}
    for i, e in enumerate(log):
        for d in (e.get("docs") or []):
            if d in gold and d not in first_hit:
                first_hit[d] = i
    distinct = list(dict.fromkeys(queries))
    union = set(rec.get("union", []))
    return {
        "search_calls": len(searches), "executed": len(executed),
        "errors": sum(1 for e in searches if "error" in e),
        "leak_rejected": sum(1 for e in searches if e.get("error") == "leak"),
        "submits_accepted": sum(1 for e in searches if e.get("tool") == "submit" and e.get("accepted")),
        "distinct_queries": len(distinct), "revisions": max(0, len(distinct) - 1),
        "ipc_restricted": sum(1 for e in searches if e.get("ipc")),
        "or_terms_mean": round(sum(q.count("+") for q in queries) / len(queries), 2) if queries else 0.0,
        "queries_with_foreign_term": sum(1 for q in queries if _ASCII_WORD.search(q)),
        "queries_korean_only": sum(1 for q in queries if _HANGUL.search(q) and not _ASCII_WORD.search(q)),
        "knowledge_calls": sum(1 for e in log if e.get("tool") in ("list_element_types", "examination_history")),
        "knowledge_return_chars": sum(e.get("ret_chars", 0) for e in log
                                      if e.get("tool") in ("list_element_types", "examination_history")),
        "union_lang": dict(Counter(lang.get(d, "?") for d in union)),
        "gold_lang": dict(Counter(lang.get(d, "?") for d in gold)),
        "hit_lang": dict(Counter(lang.get(d, "?") for d in union & gold)),
        "first_hit_log_index": first_hit,
    }


def language_composition(qid: str, allowed: frozenset[str], gold: set[str], lang: dict[str, str]) -> dict:
    """질의별 · 언어별 마스크 후 후보 수와 알려진 정답 수(PLAN-094 §2.4.4 ⑨ ⓐ ⓑ)."""
    return {"candidates": dict(Counter(lang.get(d, "?") for d in allowed)),
            "known_gold": dict(Counter(lang.get(d, "?") for d in gold))}


# ── 대역 정책(무과금 실자료 시험) ───────────────────────────────────────────
def scripted_policy(claim: str, arm: str):
    """청구항 낱말로 검색식을 만드는 결정적 대역. **품질을 재지 않는다** — 배선만 본다.

    도구 결과를 읽어 행동을 바꾼다: 건수를 센 뒤 예산 안이면 제출하고, 넘치면 다음 낱말과 AND 로 좁히고,
    0 이면 다음 후보로 넘어간다. 그래서 채택 · 거부 · 수정이 모두 로그에 남는다.
    """
    words = sorted(set(re.findall(r"[가-힣]{2,}", claim or "")), key=lambda w: (len(w), w))[:12] or ["반도체"]
    st = {"next": 1, "cur": [words[0]], "pending": None}

    def last_result(messages):
        m = messages[-1]
        if isinstance(m.get("content"), list):
            for b in m["content"]:
                if isinstance(b, dict) and b.get("type") == "tool_result":
                    return json.loads(b["content"])
        return {}

    def take():
        if st["next"] >= len(words):
            return None
        w = words[st["next"]]
        st["next"] += 1
        return w

    def policy(turn: int, messages):
        if arm == "A4" and turn == 0:
            return [("list_element_types", {})]
        res = last_result(messages) if turn else {}
        if res.get("search_calls_left", 1) <= 0:
            return []
        if "accepted" in res:                      # 제출 직후 — 새 조합을 시작
            w = take()
            if w is None:
                return []
            st["cur"] = [w]
        elif "results" in res and st["pending"] is not None:
            n = res["results"]
            if 0 < n <= res["budget_left"]:
                q, st["pending"] = st["pending"], None
                return [("submit", {"query": q})]
            w = take()
            if w is None:
                return []
            st["cur"] = (st["cur"] + [w]) if n > 0 else (st["cur"][:-1] + [w])
        q = "*".join(st["cur"])
        st["pending"] = q
        return [("count_results", {"query": q})]
    return policy


# ── 실행(R5 · R9) ─────────────────────────────────────────────────────────────
def _setup():
    import pandas as pd

    from ..ontology.judgment_items import KnowledgeView, query_concepts
    from ..retrieval.agent_search import EligibleSearch
    from ..retrieval.boolean_emulator import Emulator
    from ..retrieval.candidate import CandidateMask

    cols = ["doc_id", "is_candidate", "title", "abstract", "claims_full", "claims_independent",
            "first_claim_original", "ipc", "lang"]
    C = pd.read_parquet(config.IR_CORPUS, columns=cols)
    items = json.loads((config.PILOT_DIR / "judgment_items.json").read_text(encoding="utf-8"))["items"]
    ctx = {"claim": dict(zip(C.doc_id, C.first_claim_original)), "abstract": dict(zip(C.doc_id, C.abstract)),
           "lang": dict(zip(C.doc_id, C.lang)), "items": items,
           "search": EligibleSearch(Emulator(C), CandidateMask()),
           "view": lambda q: KnowledgeView(items, query_concepts(q))}
    return ctx


def run_arms(qids: list[str], arms: list[str], client_for, ctx, guard, out_dir: Path, rep: int = 0) -> list[dict]:
    from ..retrieval.agent_search import Session, run_one

    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for q in qids:
        view = ctx["view"](q)
        for arm in arms:
            if not guard.can_start():
                raise SystemExit(f"비용 상한: 누적 ${guard.spent:.2f} + 여유 ${guard.reserve:.2f} > ${guard.cap:.2f}")
            sess = Session(ctx["search"], q, knowledge=view if arm == "A4" else None)
            t0 = time.perf_counter()
            try:
                meta = run_one(client_for(q, arm), arm, ctx["claim"].get(q) or "", ctx["abstract"].get(q) or "",
                               sess, guard, tag=f"{arm}:{q}:{rep}",
                               knowledge_block=view.block_text() if arm == "A3" else None)
            except Exception as e:                    # 상류 failure_policy — 권한·요청·모델 오류는 멈춘다
                if type(e).__name__ in FATAL:
                    raise
                from ..retrieval import agent_frozen as AF
                guard.add_flat(AF.ERROR_CHARGE_USD, f"{arm}:{q}:{rep}", f"exception {type(e).__name__}")
                meta = {"status": f"error:{type(e).__name__}", "usage": {}, "cost_usd": AF.ERROR_CHARGE_USD,
                        "served_model": None, "turns": [], "user_chars": 0, "knowledge_block_chars": 0}
            rec = {"q": q, "arm": arm, "rep": rep, **meta, "seconds": round(time.perf_counter() - t0, 3),
                   "union": sorted(sess.union), "search_calls": sess.search_calls,
                   "knowledge_calls": sess.knowledge_calls, "leak_hits": sess.leak_hits, "log": sess.log,
                   "knowledge_items_visible": sorted(view.items)}
            with (out_dir / f"{arm}.jsonl").open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            rows.append(rec)
    return rows


def evaluate(rows: list[dict], qids: list[str], ctx, gold: dict, a0_run: Path) -> dict:
    import pandas as pd

    fam_df = pd.read_parquet(config.IR_FAMILY_MAP, columns=["doc_id", "family_id"])
    family = dict(zip(fam_df.doc_id, fam_df.family_id))
    ranked = load_run(a0_run, set(qids))
    lang = ctx["lang"]
    per = []
    for q in qids:
        allowed = ctx["search"].allowed(q)
        a0 = a0_top(ranked.get(q, []), allowed, 200)
        per.append({"q": q, "arm": "A0", "recall_doc": recall(set(a0), gold[q]),
                    "recall_family": recall(set(a0), gold[q], family), "review": len(a0),
                    "lang_composition": language_composition(q, allowed, gold[q], lang),
                    "a0_violations": sum(1 for d in a0 if d not in allowed)})
    for r in rows:
        u = set(r["union"])
        allowed = ctx["search"].allowed(r["q"])
        per.append({"q": r["q"], "arm": r["arm"], "rep": r["rep"], "status": r["status"],
                    "recall_doc": recall(u, gold[r["q"]]), "recall_family": recall(u, gold[r["q"]], family),
                    "review": len(u), "cost_usd": r["cost_usd"], "seconds": r["seconds"],
                    "turn_ms": [t["ms"] for t in r["turns"]],
                    "union_violations": sum(1 for d in u if d not in allowed),
                    "behavior": behavior(r, gold[r["q"]], lang),
                    "knowledge_block_chars": r.get("knowledge_block_chars", 0)})
    return {"per_query_arm": per}


# ── 민감도 재생(R2 · PLAN-094 §2.4.4 ④⑥) ─────────────────────────────────────
def replay(log: list[dict], qid: str, search, budget: int = 200) -> set[str]:
    """저장된 도구 호출 순서를 **같은 채택 규칙**으로 다시 실행한다(LLM 재호출 없음 · 결정적).

    이것은 "고정 검색식의 민감도" 다 — Agent 가 달라진 건수에 반응해 다른 검색식을 썼을 전체 효과는 재지 않는다.
    """
    union: set[str] = set()
    for e in log:
        if e.get("tool") != "submit" or "size" not in e:
            continue
        res = search.run(qid, e["query"], e.get("ipc"))
        if res and len(union | res) <= budget:
            union |= res
    return union


class FilingFallbackMask:
    """공개일이 결측이면 출원일 < 질의 출원일로 판정하는 대안 마스크(민감도 전용 · 동결 규칙은 그대로)."""

    def __init__(self, base):
        import numpy as np
        import pandas as pd

        from ..retrieval.candidate import _to_int

        self.base, self.doc_ids = base, base.doc_ids
        f = pd.read_parquet(config.IR_CORPUS, columns=["doc_id", "filing_date"])
        fil = dict(zip(f.doc_id, f.filing_date))
        self._fil = np.array([_to_int(fil.get(d)) for d in self.doc_ids], dtype=np.int64)

    def allowed_array(self, qid: str):
        import numpy as np

        b = self.base
        cutoff = b.q_filing.get(qid, 0)
        alt_time = np.where(b.pub_int > 0, b.pub_int < cutoff, self._fil < cutoff) if cutoff else True
        rest = b.allowed_array(qid) | (b.pub_int >= cutoff)          # 시점 외 조건만 남긴 현행 마스크
        rest &= (b.family != b.q_family.get(qid, qid)) & b.cand_ok
        rest &= np.array([d != qid for d in self.doc_ids])
        return rest & alt_time


def sensitivity(rows: list[dict], ctx, gold: dict) -> list[dict]:
    from ..retrieval.agent_search import EligibleSearch

    base = ctx["search"]
    with_title = EligibleSearch(base.emu, base.mask, fields=("TI", "AB", "CL"))
    alt_mask = EligibleSearch(base.emu, FilingFallbackMask(base.mask), fields=base.fields)
    out = []
    for r in rows:
        g = gold[r["q"]]
        u0 = replay(r["log"], r["q"], base)
        out.append({"q": r["q"], "arm": r["arm"], "rep": r["rep"],
                    "replay_matches_run": u0 == set(r["union"]),
                    "recall_base": recall(u0, g),
                    "recall_with_title": recall(replay(r["log"], r["q"], with_title), g),
                    "recall_filing_fallback": recall(replay(r["log"], r["q"], alt_mask), g)})
    return out


N_REPEAT_QUERIES = 10
N_EXTRA_REPS = 2


def run_plan(sample: list[str], arms: list[str], smoke: bool) -> list[tuple[str, str, int]]:
    """실행 순서(결과 전 고정). 연기 시험 = 첫 질의 × 4팔 × 1회. 본 실행 = 30질의 × 4팔 × 1회를 **먼저** 끝내고,
    해시 순 첫 10질의 × 4팔 × 추가 2회를 뒤에 둔다 — 비용 상한에 걸려도 주 표본이 먼저 완성된다."""
    if smoke:
        return [(sample[0], a, 0) for a in arms]
    plan = [(q, a, 0) for q in sample for a in arms]
    rep_q = sorted(sample, key=lambda q: hashlib.sha256(f"{SEED}:{q}".encode()).hexdigest())[:N_REPEAT_QUERIES]
    for r in range(1, N_EXTRA_REPS + 1):
        plan += [(q, a, r) for q in sorted(rep_q) for a in arms]
    return plan


def done_keys(out_dir: Path) -> set[tuple[str, str, int]]:
    keys = set()
    for p in out_dir.glob("*.jsonl"):
        for line in p.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            keys.add((r["q"], r["arm"], r["rep"]))
    return keys


class StopRun(RuntimeError):
    pass


def check_stop(records: list[dict]) -> str | None:
    """중단 조건(결과 전 고정 · PLAN-094 §4.4) — 성능은 보지 않는다."""
    from ..retrieval import agent_frozen as AF

    if sum(r.get("leak_hits", 0) for r in records) >= AF.LEAK_HITS_STOP:
        return f"누출 검출 누적 ≥ {AF.LEAK_HITS_STOP}"
    for arm in sorted({r["arm"] for r in records}):
        rs = [r for r in records if r["arm"] == arm]
        fail = sum(1 for r in rs if r["status"] != "ok")
        if len(rs) >= AF.FAILURE_MIN_RUNS and fail / len(rs) > AF.FAILURE_RATE_STOP:
            return f"{arm} 실패율 {fail}/{len(rs)} > {AF.FAILURE_RATE_STOP}"
    if any(r["status"] == "cost_cap" for r in records):
        return "비용 상한 도달"
    return None


def _records(out_dir: Path) -> list[dict]:
    return [json.loads(line) for p in sorted(Path(out_dir).glob("*.jsonl"))
            for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def execute(plan, client_factory, ctx, guard, out_dir: Path) -> int:
    """계획을 순서대로 실행 · 끝난 키는 건너뛴다(재개 가능) · 중단 조건이나 상한에 걸리면 멈춘다."""
    done = done_keys(out_dir)
    n = 0
    for q, arm, rep in plan:
        if (q, arm, rep) in done:
            continue
        run_arms([q], [arm], client_factory, ctx, guard, out_dir, rep=rep)
        n += 1
        why = check_stop(_records(out_dir)) if ctx is not None else None
        if why:
            raise StopRun(why)
    return n


def smoke_check(records: list[dict], ctx, ledger: Path) -> list[str]:
    """연기 시험 판정 — 마스크 · 누출 방지 · 계측 · 비용 통제가 정상인가(성능은 보지 않는다)."""
    probs = []
    if len(records) != 4 or {r["arm"] for r in records} != {"A1", "A2", "A3", "A4"}:
        probs.append(f"연기 시험 실행 수·팔 불일치: {len(records)}")
    for r in records:
        tag = f"{r['arm']}"
        if r["status"] != "ok":
            probs.append(f"{tag} 상태 {r['status']}")
        allowed = ctx["search"].allowed(r["q"])
        if any(d not in allowed for d in r["union"]):
            probs.append(f"{tag} 적격 후보 위반")
        from ..validate.leakage_check import scan_publication_numbers
        if any(scan_publication_numbers(e.get("query") or "") for e in r["log"] if "size" in e):
            probs.append(f"{tag} 공보번호가 든 검색식이 실행됨")
        if not r["turns"] or any(t["ms"] <= 0 or t["input_tokens"] + t["cache_read"] + t["cache_write"] <= 0
                                 or t["output_tokens"] <= 0 for t in r["turns"]):
            probs.append(f"{tag} 턴 계측 결측")
        if not r.get("served_model"):
            probs.append(f"{tag} served_model 결측")
        if any("ms" not in e or "ret_chars" not in e for e in r["log"]):
            probs.append(f"{tag} 도구 계측 결측")
        if r["arm"] == "A3" and r["knowledge_items_visible"] and r["knowledge_block_chars"] <= 0:
            probs.append("A3 지식 블록 누락")
        if r["arm"] != "A4" and r["knowledge_calls"] > 0:
            probs.append(f"{tag} 지식 도구가 A4 밖에서 호출됨")
    led = [json.loads(line) for line in Path(ledger).read_text(encoding="utf-8").splitlines() if line.strip()]
    if abs(sum(x["usd"] for x in led) - sum(r["cost_usd"] for r in records)) > 1e-3:
        probs.append("원장 합계 ≠ 실행 비용 합계")
    if len(led) != sum(len(r["turns"]) for r in records):
        probs.append("원장 행 수 ≠ 턴 수")
    return probs


def freeze_state(sample: list[str]) -> dict:
    """동결 대상의 현재 해시. `run --paid` 는 이것이 동결 파일과 같을 때만 시작한다."""
    from ..ontology.vendor_pilot import sha256_file
    from ..retrieval import agent_frozen as AF

    src = Path(config.ROOT) / "src" / "sdkb_paper"
    code = ["retrieval/agent_search.py", "retrieval/agent_frozen.py", "retrieval/boolean_emulator.py",
            "retrieval/candidate.py", "analysis/agent_pilot.py", "analysis/metrics.py",
            "ontology/judgment_items.py", "validate/leakage_check.py"]
    items_doc = json.loads((config.PILOT_DIR / "judgment_items.json").read_text(encoding="utf-8"))
    return {
        "model": AF.MODEL, "effort": AF.EFFORT, "max_tokens": AF.MAX_TOKENS, "max_turns": AF.MAX_TURNS,
        "search_calls": AF.SEARCH_CALLS, "knowledge_calls": AF.KNOWLEDGE_CALLS, "budget": AF.BUDGET,
        "fields": list(AF.FIELDS), "price_per_mtok": AF.PRICE_PER_MTOK, "price_safety": AF.PRICE_SAFETY,
        "cost_cap_usd": AF.COST_CAP_USD, "run_reserve_usd": AF.RUN_RESERVE_USD,
        "error_charge_usd": AF.ERROR_CHARGE_USD, "failure_rate_stop": AF.FAILURE_RATE_STOP,
        "failure_min_runs": AF.FAILURE_MIN_RUNS, "leak_hits_stop": AF.LEAK_HITS_STOP,
        "prompt_sha256": {a: AF.prompt_sha(a) for a in AF.ARMS},
        "code_sha256": {c: sha256_file(src / c) for c in code},
        "corpus_sha256": sha256_file(config.IR_CORPUS), "family_map_sha256": sha256_file(config.IR_FAMILY_MAP),
        "split_sha256": sha256_file(config.IR_SPLIT),
        "claim_features_sha256": sha256_file(config.EXTERNAL_SDKB / "claim_features.parquet"),
        "a0_run_sha256": sha256_file(config.IR_RUNS_DIR / "hybrid_b3_rrf.txt"),
        "argument_ttl_sha256": sha256_file(config.PILOT_ARGUMENT_TTL),
        "items_sha256": items_doc["items_sha256"], "items_n": len(items_doc["items"]),
        "items_status": "파일럿 잠정 입력으로 동결 — 판단 지식으로 확정된 것이 아니다 · 논증층 사람 대조 FAIL 보존",
        "sample_sha256": hashlib.sha256("\n".join(sample).encode()).hexdigest(), "sample": sample,
        "anthropic_sdk": __import__("anthropic").__version__,
    }


def verify_freeze(sample: list[str]) -> None:
    want = json.loads(FREEZE.read_text(encoding="utf-8"))["state"]
    have = freeze_state(sample)
    diff = sorted(k for k in want if want[k] != have.get(k))
    if diff:
        raise SystemExit(f"ERROR: 동결과 다르다 — {diff}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("sample")
    d = sub.add_parser("dryrun")
    d.add_argument("--n", type=int, default=1)
    d.add_argument("--arms", default="A1,A2,A3,A4")
    r = sub.add_parser("run", help="유료 실행 — 승인 후에만 · --paid 필수")
    r.add_argument("--paid", action="store_true")
    r.add_argument("--smoke", action="store_true", help="연기 시험(첫 질의 × 4팔 × 1회)")
    sub.add_parser("report")
    sub.add_parser("freeze")
    a = ap.parse_args(argv)

    gold = load_gold()
    if a.cmd == "sample":
        import pandas as pd

        lang = dict(pd.read_parquet(config.IR_CORPUS, columns=["doc_id", "lang"]).itertuples(index=False))
        cf = pd.read_parquet(config.EXTERNAL_SDKB / "claim_features.parquet", columns=["claim_id", "side"])
        c1 = cf[(cf.side == "rej") & cf.claim_id.str.endswith("_c1")].claim_id.value_counts()
        n_elem = {f"kr_{k.split('_')[1]}": int(v) for k, v in c1.items()}
        s = stratified_sample(gold, lang, n_elem)
        p = config.PILOT_DIR / "sample.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        body = {"seed": SEED, "n": len(s), "qids": s,
                "sha256": hashlib.sha256("\n".join(s).encode()).hexdigest()}
        p.write_text(json.dumps(body, indent=1) + "\n", encoding="utf-8")
        print(f"✓ 표집 {len(s)} · sha {body['sha256'][:16]} → {p}")
        return 0

    if a.cmd == "freeze":
        sample = json.loads((config.PILOT_DIR / "sample.json").read_text(encoding="utf-8"))["qids"]
        body = {"_README": "PLAN-096 유료 파일럿 동결(사용자 승인 2026-10-17 · 204회 · 원장 누적 USD 30). "
                           "run --paid 는 현재 상태가 이 state 와 같을 때만 시작한다.",
                "state": freeze_state(sample)}
        FREEZE.write_text(json.dumps(body, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"✓ 동결 → {FREEZE}")
        return 0
    if a.cmd == "run":
        from ..retrieval.agent_search import CostGuard, make_client

        sample = json.loads((config.PILOT_DIR / "sample.json").read_text(encoding="utf-8"))["qids"]
        verify_freeze(sample)                          # 동결과 다르면 여기서 멈춘다
        client = make_client(paid=a.paid)              # --paid 가 없으면 여기서 멈춘다
        ctx = _setup()
        guard = CostGuard(LEDGER)                      # 연기 시험과 본 실행이 같은 원장 · 합계 상한
        arms = ["A1", "A2", "A3", "A4"]
        if not done_keys(RUNS_SMOKE) >= {(sample[0], x, 0) for x in arms}:
            execute(run_plan(sample, arms, smoke=True), lambda q, arm: client, ctx, guard, RUNS_SMOKE)
        probs = smoke_check(_records(RUNS_SMOKE), ctx, LEDGER)
        print(f"연기 시험 4 · 누적 ${guard.spent:.2f} · 판정 {'통과' if not probs else probs}")
        if probs or a.smoke:
            return 1 if probs else 0
        try:
            n = execute(run_plan(sample, arms, smoke=False), lambda q, arm: client, ctx, guard, RUNS)
        except StopRun as e:
            print(f"■ 중단: {e} · 누적 ${guard.spent:.2f}")
            return 2
        except SystemExit as e:
            print(f"■ {e}")
            return 3
        print(f"✓ 본 실행 {n} · 누적 ${guard.spent:.2f} / 상한 ${guard.cap:.2f}")
        return 0
    if a.cmd == "report":
        rows = [json.loads(line) for p in sorted(RUNS.glob("*.jsonl"))
                for line in p.read_text(encoding="utf-8").splitlines()]
        sample = json.loads((config.PILOT_DIR / "sample.json").read_text(encoding="utf-8"))["qids"]
        ctx = _setup()
        res = evaluate(rows, sample, ctx, gold, config.IR_RUNS_DIR / "hybrid_b3_rrf.txt")
        res["sensitivity"] = sensitivity(rows, ctx, gold)
        (config.PILOT_DIR / "report.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n",
                                                      encoding="utf-8")
        print(f"✓ 보고 {len(res['per_query_arm'])}행 → {config.PILOT_DIR / 'report.json'}")
        return 0

    # dryrun — 실자료 · LLM 대역 · 비용 원장은 별도 파일(유료 원장과 섞지 않는다)
    from ..retrieval.agent_search import CostGuard, ScriptedClient

    sample = json.loads((config.PILOT_DIR / "sample.json").read_text(encoding="utf-8"))["qids"]
    qids = sample[: a.n]
    ctx = _setup()
    guard = CostGuard(config.PILOT_DIR / "dryrun" / "cost_ledger_scripted.jsonl")
    out_dir = config.PILOT_DIR / "dryrun" / "runs"
    for p in out_dir.glob("*.jsonl"):
        p.unlink()
    rows = run_arms(qids, a.arms.split(","),
                    lambda q, arm: ScriptedClient(scripted_policy(ctx["claim"].get(q), arm)),
                    ctx, guard, out_dir)
    res = evaluate(rows, qids, ctx, gold, config.IR_RUNS_DIR / "hybrid_b3_rrf.txt")
    res["sensitivity"] = sensitivity(rows, ctx, gold)
    (config.PILOT_DIR / "dryrun" / "eval.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n",
                                                           encoding="utf-8")
    for x in res["sensitivity"]:
        print("sensitivity", x)
    for r in res["per_query_arm"]:
        b = r.get("behavior", {})
        print(r["q"], r["arm"], r.get("status", "-"), "recall", round(r["recall_doc"], 3), "review", r["review"],
              "viol", r.get("union_violations", r.get("a0_violations")), "calls", b.get("search_calls"),
              "kcalls", b.get("knowledge_calls"), "kchars", b.get("knowledge_return_chars"),
              "blockchars", r.get("knowledge_block_chars"), "cost(scripted)", r.get("cost_usd"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
