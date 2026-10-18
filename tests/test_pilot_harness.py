"""파일럿 하네스 고정 예제 — 적격 후보 · 예산 · 누출 · 비용 상한 · 계측 · 지식 동치 · 분할 가드 (PLAN-096 D4-1).

네트워크 0 · 유료 호출 0 · 봉인 정답 0. 정답은 합성이다.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from sdkb_paper import config
from sdkb_paper.analysis import agent_pilot as P
from sdkb_paper.ontology.judgment_items import KnowledgeView, items_sha
from sdkb_paper.retrieval import agent_frozen as F
from sdkb_paper.retrieval import agent_search as S
from sdkb_paper.retrieval.boolean_emulator import Concordance, Emulator


class FakeMask:
    """CandidateMask 와 같은 인터페이스. q0 에 대해 허용 = {d1, d3} (d2 미래 공개 · d4 같은 패밀리 가정)."""

    doc_ids = ["d1", "d2", "d3", "d4", "q0"]

    def allowed_array(self, qid):
        return np.array([True, False, True, False, False])


@pytest.fixture()
def search(tmp_path):
    c = pd.DataFrame({"doc_id": ["d1", "d2", "d3", "d4", "q0"], "is_candidate": [True] * 5,
                      "title": ["t"] * 5, "abstract": ["식각 공정"] * 4 + ["식각 질의"],
                      "claims_full": ["식각"] * 5, "claims_independent": [""] * 5, "ipc": [[]] * 5})
    conc = tmp_path / "c.csv"
    conc.write_text("from_symbol,to_symbol\n", encoding="utf-8")
    return S.EligibleSearch(Emulator(c, Concordance(conc)), FakeMask())


def test_same_eligible_set_at_count_submit_and_a0(search):
    sess = S.Session(search, "q0")
    cnt = json.loads(sess.tool("count_results", {"query": "식각"}))
    sub = json.loads(sess.tool("submit", {"query": "식각"}))
    allowed = search.allowed("q0")
    assert cnt["results"] == 2 and sub["accepted"] and sess.union == {"d1", "d3"} == set(allowed)
    assert P.a0_top(["d2", "d4", "d3", "q0", "d1"], allowed, 200) == ["d3", "d1"]
    assert P.a0_top(["d2", "d3", "d1"], allowed, 1) == ["d3"]          # 마스크 → 절단 순서


def test_parity_mode_has_no_mask(search):
    up = S.EligibleSearch(search.emu, None)
    assert up.run("q0", "식각") == {"d1", "d2", "d3", "d4"}            # 상류 조건: 자기 문서만 제외


def test_budget_and_call_limits(search):
    sess = S.Session(search, "q0", budget=1)
    assert json.loads(sess.tool("submit", {"query": "식각"}))["accepted"] is False
    assert sess.union == set()
    for _ in range(F.SEARCH_CALLS):
        sess.tool("count_results", {"query": "식각"})
    assert "limit" in json.loads(sess.tool("count_results", {"query": "식각"}))["error"]


def test_leak_query_is_rejected_and_counted(search):
    sess = S.Session(search, "q0")
    out = json.loads(sess.tool("submit", {"query": "식각 * KR 10-2016-0014323"}))
    assert "publication number" in out["error"] and sess.leak_hits == 1 and sess.union == set()


def test_tool_calls_record_latency_and_return_size(search):
    sess = S.Session(search, "q0")
    sess.tool("count_results", {"query": "식각"})
    assert sess.log[-1]["ms"] >= 0 and sess.log[-1]["ret_chars"] > 0


def test_cost_guard_ledger_and_reserve(tmp_path):
    led = tmp_path / "l.jsonl"
    g = S.CostGuard(led, cap=1.0, reserve=0.5)
    g.add({"input_tokens": 100_000, "output_tokens": 0}, "x")       # 0.4 × 1.25 = 0.5
    assert abs(g.spent - 0.5) < 1e-9 and g.can_start()
    g.add({"input_tokens": 1, "output_tokens": 0}, "y")
    assert not g.can_start()
    assert abs(S.CostGuard(led, cap=1.0).spent - g.spent) < 1e-9       # 다음 실행으로 누적이 이어진다


def test_run_stops_at_cost_cap_mid_run(search, tmp_path):
    g = S.CostGuard(tmp_path / "l.jsonl", cap=0.01, reserve=0.0)
    client = S.ScriptedClient(lambda t, m: [("count_results", {"query": "식각"})], usage=(10_000, 1_000))
    sess = S.Session(search, "q0")
    meta = S.run_one(client, "A1", "청구항", "초록", sess, g, tag="t")
    assert meta["status"] == "cost_cap" and client.calls == 1
    assert meta["turns"][0]["ms"] >= 0 and meta["usage"]["input_tokens"] == 10_000


def test_run_loop_and_turn_limit(search, tmp_path):
    g = S.CostGuard(None, cap=1e9)
    sess = S.Session(search, "q0")
    meta = S.run_one(S.ScriptedClient(lambda t, m: [("count_results", {"query": "식각"})]),
                     "A2", "c", "a", sess, g, tag="t")
    assert meta["status"] == "max_turns" and len(meta["turns"]) == F.MAX_TURNS


ITEMS = {"material:dielectric": {"element_type": "material:dielectric", "applications": 9, "judgments": 12},
         "process:etch": {"element_type": "process:etch", "applications": 7, "judgments": 8},
         "process:cmp": {"element_type": "process:cmp", "applications": 6, "judgments": 6}}


def test_a3_block_and_a4_tool_carry_the_same_content():
    v = KnowledgeView(ITEMS, {"process:etch", "material:dielectric", "unknown:x"})
    block = {json.dumps({k: x for k, x in json.loads(line).items() if k != "label"}, sort_keys=True, ensure_ascii=False)
             for line in v.block_text().splitlines()}
    tool = {json.dumps({k: x for k, x in v.history(t["element_type"]).items() if k != "label"},
                       sort_keys=True, ensure_ascii=False) for t in v.list_types()["element_types"]}
    assert block == tool == v.content_set() and len(block) == 2
    assert "error" in v.history("process:cmp")                        # 질의에 없는 유형은 보이지 않는다


def test_knowledge_tools_only_on_a4_and_limited(search):
    v = KnowledgeView(ITEMS, {"process:etch"})
    sess = S.Session(search, "q0", knowledge=v)
    for _ in range(F.KNOWLEDGE_CALLS):
        sess.tool("list_element_types", {})
    assert "limit" in json.loads(sess.tool("examination_history", {"element_type": "process:etch"}))["error"]
    assert "unknown tool" in json.loads(S.Session(search, "q0").tool("list_element_types", {}))["error"]


def test_items_sha_is_deterministic():
    assert items_sha(ITEMS) == items_sha(dict(reversed(list(ITEMS.items()))))


def test_prompt_skeletons_differ_only_by_their_block():
    a1, a2, a3, a4 = (F.system_prompt(a) for a in F.ARMS)
    assert a2 == a1 + "\n" + F.PLAN_BLOCK and a3 == a2 and a4 == a2 + "\n" + F.KNOWLEDGE_TOOL_INTRO
    assert F.tools_for("A1") == F.tools_for("A2") == F.tools_for("A3") == F.SEARCH_TOOLS
    assert F.tools_for("A4") == F.SEARCH_TOOLS + F.KNOWLEDGE_TOOLS
    assert len({F.prompt_sha(a) for a in F.ARMS}) == 4
    assert "title" not in F.SYNTAX.split("Searched fields:")[1].split("\n")[0]


def test_a3_user_message_carries_block_others_do_not():
    assert "Examination history summary" in S.user_message("A3", "c", "a", "{}")
    assert all("Examination history" not in S.user_message(a, "c", "a", "{}") for a in ("A1", "A2", "A4"))


def test_paid_client_requires_explicit_flag():
    with pytest.raises(PermissionError):
        S.make_client(paid=False)


def test_pilot_refuses_confirmatory_splits():
    for s in ("test", "test_b", "all", "train"):
        with pytest.raises(PermissionError):
            P.load_gold(s)


def test_stratified_sample_is_deterministic_and_proportional():
    gold = {f"q{i}": {f"d{i}"} for i in range(40)}
    lang = {f"d{i}": ("en" if i % 4 == 0 else "ko") for i in range(40)}
    n_elem = {f"q{i}": (5 if i % 2 else 2) for i in range(40)}
    a = P.stratified_sample(gold, lang, n_elem, n=20, seed=1)
    assert a == P.stratified_sample(gold, lang, n_elem, n=20, seed=1) and len(a) == 20
    assert sum(1 for q in a if lang[f"d{q[1:]}"] == "en") == 5


def test_behavior_indicators_from_log():
    rec = {"union": ["d1", "d2"], "log": [
        {"tool": "count_results", "query": "식각", "size": 3},
        {"tool": "submit", "query": "식각*etch", "ipc": ["H01L"], "size": 2, "accepted": True, "docs": ["d1", "d2"]},
        {"tool": "submit", "query": "x KR 10-2016-0014323", "error": "leak"},
        {"tool": "examination_history", "input": {}, "ret_chars": 50}]}
    b = P.behavior(rec, {"d2"}, {"d1": "ko", "d2": "en"})
    assert (b["search_calls"], b["executed"], b["leak_rejected"], b["ipc_restricted"]) == (3, 2, 1, 1)
    assert b["queries_with_foreign_term"] == 1 and b["knowledge_return_chars"] == 50
    assert b["first_hit_log_index"] == {"d2": 1} and b["hit_lang"] == {"en": 1}


def test_existing_pipeline_does_not_read_pilot_assets():
    """§2.1 적용 범위 고정(PLAN-096 D2): 파일럿 모듈 밖의 하류 코드는 별도 자산을 읽지 않는다."""
    pilot = {"vendor_pilot.py", "judgment_items.py", "agent_search.py", "agent_frozen.py",
             "boolean_emulator.py", "agent_pilot.py", "config.py", "review_package.py"}
    rx = re.compile(r"EXTERNAL_PILOT|PILOT_ARGUMENT_TTL|PILOT_CONCORDANCE|PILOT_PARITY|sdkb_pilot")
    src = Path(config.ROOT) / "src" / "sdkb_paper"
    offenders = [str(p.relative_to(src)) for p in src.rglob("*.py")
                 if p.name not in pilot and rx.search(p.read_text(encoding="utf-8"))]
    assert offenders == []


def test_run_plan_puts_main_sample_before_repeats():
    sample = [f"q{i:02d}" for i in range(30)]
    plan = P.run_plan(sample, list(F.ARMS), smoke=False)
    assert len(plan) == 30 * 4 + 10 * 4 * 2
    assert all(rep == 0 for _, _, rep in plan[:120]) and all(rep > 0 for _, _, rep in plan[120:])
    assert P.run_plan(sample, list(F.ARMS), smoke=True) == [("q00", a, 0) for a in F.ARMS]


def test_execute_resumes_and_stops_at_cap(search, tmp_path, monkeypatch):
    calls = []

    def fake_run_arms(qids, arms, client_for, ctx, guard, out_dir, rep=0):
        calls.append((qids[0], arms[0], rep))
        out_dir.mkdir(parents=True, exist_ok=True)
        with (out_dir / f"{arms[0]}.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"q": qids[0], "arm": arms[0], "rep": rep}) + "\n")

    monkeypatch.setattr(P, "run_arms", fake_run_arms)
    plan = [("q1", "A1", 0), ("q1", "A2", 0)]
    assert P.execute(plan, None, None, None, tmp_path) == 2
    assert P.execute(plan, None, None, None, tmp_path) == 0          # 재개 — 끝난 키는 건너뛴다
    assert calls == plan


def test_replay_reproduces_union_and_respects_budget(search):
    sess = S.Session(search, "q0")
    sess.tool("submit", {"query": "식각"})
    assert P.replay(sess.log, "q0", search) == sess.union
    assert P.replay(sess.log, "q0", search, budget=1) == set()


def test_stop_rules_ignore_performance():
    ok = [{"arm": "A1", "status": "ok", "leak_hits": 0}] * 4
    assert P.check_stop(ok + [{"arm": "A1", "status": "max_turns", "leak_hits": 0}]) is None   # 1/5 = 20% (초과 아님)
    assert "실패율" in P.check_stop(ok + [{"arm": "A1", "status": "refusal", "leak_hits": 0}] * 2)
    assert "누출" in P.check_stop([{"arm": "A2", "status": "ok", "leak_hits": 3}])
    assert P.check_stop([{"arm": "A2", "status": "cost_cap", "leak_hits": 0}]) == "비용 상한 도달"


def test_flat_error_charge_counts_toward_cap(tmp_path):
    g = S.CostGuard(tmp_path / "l.jsonl", cap=1.0, reserve=0.0)
    g.add_flat(0.5, "t", "exception X")
    assert abs(S.CostGuard(tmp_path / "l.jsonl", cap=1.0).spent - 0.5) < 1e-9


# ── 수정 A4(2차 결정 · 2026-10-18) ───────────────────────────────────────────
def _view():
    items = {"process:etch": {"element_type": "process:etch", "applications": 7,
                              "cited_ipc_main_groups": [{"ipc": "H01L21", "share": 0.9}]},
             "material:dielectric": {"element_type": "material:dielectric", "applications": 9,
                                     "cited_ipc_main_groups": [{"ipc": "C23C16", "share": 0.5}]}}
    return items, KnowledgeView(items, {"process:etch", "material:dielectric"})


def test_a4r_mandatory_lookup_happens_before_first_search(search):
    items, v = _view()
    seen = {}

    def policy(turn, messages):
        if turn == 0:
            seen["first_request"] = [m["role"] for m in messages]
            return [("count_results", {"query": "식각"})]
        return []
    sess = S.Session(search, "q0", knowledge=v)
    S.run_one(S.ScriptedClient(policy), "A4r", "c", "a", sess, S.CostGuard(None, cap=1e9), tag="t")
    assert seen["first_request"] == ["user", "assistant", "user"]           # 의무 조회 왕복이 첫 요청에 있다
    assert sess.log[0]["tool"] == "get_examination_history" and sess.log[0]["mandatory"] is True
    assert sess.log[1]["tool"] == "count_results" and sess.knowledge_calls == 0   # 의무 조회는 상한에 안 든다
    d = P.delivery({"arm": "A4r", "log": sess.log, "knowledge_items_visible": sorted(v.items)}, items)
    assert d["delivered"] and d["first_lookup_before_search"] and d["n_items_visible"] == 2


def test_a3_block_equals_a4r_first_lookup():
    _, v = _view()
    block = [json.loads(line) for line in v.block_text().splitlines()]
    first = v.all_items()["element_types"]
    strip = lambda xs: sorted(json.dumps({k: x[k] for k in x if k != "label"}, sort_keys=True) for x in xs)  # noqa: E731
    assert strip(block) == strip(first)


def test_empty_lookup_is_not_a_delivery(search):
    v = KnowledgeView({}, {"process:etch"})
    sess = S.Session(search, "q0", knowledge=v)
    out = json.loads(sess.tool("get_examination_history", {"_mandatory": True}))
    assert out["element_types"] == []
    d = P.delivery({"arm": "A4r", "log": sess.log, "knowledge_items_visible": []}, {})
    assert d["has_items"] is False and d["delivered"] is False
    d3 = P.delivery({"arm": "A3", "log": [], "knowledge_items_visible": [], "knowledge_block_chars": 0}, {})
    assert d3["delivered"] is False


def test_reflection_trace_counts_item_ipc_and_terms():
    items, v = _view()
    log = [{"tool": "count_results", "query": "etch*플라즈마", "ipc": ["H01L21/3065"], "size": 3}]
    d = P.delivery({"arm": "A3", "log": log, "knowledge_items_visible": sorted(v.items),
                    "knowledge_block_chars": 10}, items)
    assert (d["searches_using_item_ipc"], d["searches_using_item_term"]) == (1, 1)


def test_multiguard_writes_both_ledgers_and_respects_extra_cap(tmp_path):
    g = S.MultiGuard(S.CostGuard(tmp_path / "all.jsonl", cap=30.0, reserve=0.5),
                     S.CostGuard(tmp_path / "r2.jsonl", cap=1.0, reserve=0.5))
    g.add({"input_tokens": 120_000, "output_tokens": 0}, "x")              # 0.48 × 1.25 = 0.6
    assert not g.can_start() and g.guards[0].can_start()
    assert S.CostGuard(tmp_path / "all.jsonl").spent == S.CostGuard(tmp_path / "r2.jsonl").spent


def test_r2_selection_and_plan():
    sample = [f"q{i:02d}" for i in range(30)]
    a, b = P.r2_queries(sample), P.r2_queries(list(reversed(sample)))
    assert a == b and len(a) == 5
    assert len(P.r2_plan(a)) == 20 and {x[1] for x in P.r2_plan(a)} == {"A3", "A4r"}


def test_old_arms_unchanged_against_first_freeze():
    """기존 A1–A4 정의는 바꾸지 않았다 — 1차 동결의 프롬프트 sha 와 같다."""
    frozen = json.loads((Path(config.ROOT) / "01.code_spec/plans/PLAN-096-freeze.json").read_text(encoding="utf-8"))
    for a in F.ARMS:
        assert F.prompt_sha(a) == frozen["state"]["prompt_sha256"][a]
    assert F.prompt_sha("A4r") not in frozen["state"]["prompt_sha256"].values()
    assert "get_examination_history" in [t["name"] for t in F.tools_for("A4r")]


def test_variance_components_and_sample_size_on_synthetic():
    per = []
    for i in range(30):
        per += [{"q": f"q{i}", "arm": "X", "rep": 0, "recall_doc": 0.5 + (0.1 if i % 2 else -0.1)},
                {"q": f"q{i}", "arm": "Y", "rep": 0, "recall_doc": 0.5}]
    for i in range(5):
        for r in (1, 2):
            per += [{"q": f"q{i}", "arm": "X", "rep": r, "recall_doc": per[2 * i]["recall_doc"]},
                    {"q": f"q{i}", "arm": "Y", "rep": r, "recall_doc": 0.5}]
    c = P.variance_components(per, "X", "Y", n_boot=50)
    assert c["within_x"] == pytest.approx(0, abs=1e-12) and c["within_y"] == pytest.approx(0, abs=1e-12)
    assert c["between_diff"] > 0
    t = P.sample_size_table(c, (0.05,), (1, 2), 0.1, 4)
    assert t[0]["queries"] == t[1]["queries"]                    # 실행 간 변동 0 이면 반복은 질의 수를 줄이지 않는다
    assert P.n_required(0.0, 0.04, 1, 0.05) > P.n_required(0.0, 0.04, 4, 0.05)


def test_review_candidates_are_structural_and_public_numbers_strip_prefix():
    from sdkb_paper.ontology import review_package as R

    card = {"scope": "ScopeAddedLimitation", "rationale": ["RationaleDesignChoice"], "common_knowledge": True,
            "cited": [{"ipc_main_groups": ["H01L21", "H10B69"]}]}
    c = R.suggestion_candidates(card, {})
    assert len(c) == 4 and any("H01L21" in x for x in c)
    assert R._public_number("kr_KR1020090012345A") == "KR1020090012345A"
    assert R.OUT.is_relative_to(config.PILOT_DIR)                     # 비커밋 디렉터리에만 쓴다
