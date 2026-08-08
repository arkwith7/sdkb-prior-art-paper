"""C2′ 전달 실험의 규율 강제 — PLAN-038 §8 성공기준 1·2·5 (§12.8 착수 조건).

이 테스트가 지키는 것은 셋이다.

  1. **두 팔의 입력 차이가 검색 run 하나뿐**이다 — 프롬프트·모델·K·온도·max_tokens 동일 (§8-1)
  2. **채점이 결정적**이다 — 같은 생성 원문을 두 번 채점하면 바이트 동일 (§8-2)
  3. **컨텍스트에 누출이 없다** — 질의 자신·같은 패밀리·시점 위반 문서는 들어가지 않는다 (§8-5)

더해서 §12.1 동결값과 §12.3 프롬프트가 조용히 바뀌지 않게 잠근다 — 값이 바뀌면 그것은
재측정이 아니라 **새 실험**이다(CLAUDE.md §1-11).
"""
from __future__ import annotations

import json

import pytest

from sdkb_paper.rag import context as ctx
from sdkb_paper.rag import frozen, score

# ── §12.1 동결값 잠금 ───────────────────────────────────────────────────────────
def test_frozen_values_match_preregistration():
    assert frozen.MODEL_ID == "global.anthropic.claude-haiku-4-5-20251001-v1:0"
    assert frozen.K == 10
    assert frozen.TEMPERATURE == 0
    assert frozen.N_REPEATS == 3
    # §12.4 고장 수리 (2026-08-03): 1024 → 4096. 스모크 절단율 0.400 ≥ 0.05 이 근거이며
    # **판독값은 보지 않았다**(인용 정확도·환각률은 파싱 실패로 전량 None 이었다).
    assert frozen.MAX_TOKENS == 4096
    assert frozen.ARMS == ("B3_rrf", "P1")
    assert frozen.RUNSET == "O_pre_linker"
    assert frozen.STATUS == "exploratory", "A층은 확증이 아니다(§7 결정 '다')"


def test_count_tokens_id_shares_the_model_snapshot():
    """계수는 베이스 ID · 호출은 global 프로파일(§12.5) — **같은 스냅샷**이어야 한다(§1-11)."""
    assert frozen.MODEL_ID.endswith(frozen.COUNT_TOKENS_MODEL_ID)


def test_prompt_is_frozen():
    """프롬프트 전문 잠금. 문자 하나가 바뀌면 값이 어긋난다(§1-11 첫 금지)."""
    assert frozen.PROMPT_SHA256 == (
        "17708c71ced91d0b6b483bd11475d707c6f985b1eb365c3de6634ba3b46bf882"
    )


def test_prompt_names_no_arm():
    """모델이 어느 팔인지 알면 그것이 변인이 된다(§12.3 말미)."""
    blob = frozen.SYSTEM_PROMPT + frozen.USER_TEMPLATE + frozen.DOC_TEMPLATE
    for banned in ("온톨로지", "B3", "P1", "RRF", "hybrid", "SDKB"):
        assert banned not in blob, f"프롬프트에 팔·시스템을 알리는 말이 있다: {banned}"


# ── §8-1 두 팔의 차이는 run 하나뿐 ──────────────────────────────────────────────
def test_request_differs_only_by_documents():
    """같은 질의·다른 후보 → payload 는 사용자 메시지 본문 말고 전부 같다."""
    a = ctx.build_request("청구항 1. 반도체 장치.", "[docA] 본문 A")
    b = ctx.build_request("청구항 1. 반도체 장치.", "[docB] 본문 B")

    assert a["modelId"] == b["modelId"] == frozen.MODEL_ID
    assert a["system"] == b["system"]
    assert a["inferenceConfig"] == b["inferenceConfig"]
    # top_p·top_k 는 보내지 않는다(§12.1-3c)
    assert set(a["inferenceConfig"]) == {"temperature", "maxTokens"}

    ta = a["messages"][0]["content"][0]["text"]
    tb = b["messages"][0]["content"][0]["text"]
    assert ta != tb
    # 후보 블록만 다르다 — 나머지 템플릿은 문자 단위로 같다
    assert ta.replace("[docA] 본문 A", "@") == tb.replace("[docB] 본문 B", "@")


def test_request_builder_takes_no_arm_argument():
    """팔 이름이 요청 조립에 들어갈 수 없어야 §8-1 이 구조로 강제된다."""
    import inspect

    params = set(inspect.signature(ctx.build_request).parameters)
    assert params == {"query_claims", "docs_block"}


def test_context_block_preserves_rank_order():
    qc = ctx.QueryContext(
        qid="q1", query_claims="c", doc_ids=("d1", "d2"), doc_texts=("t1", "t2"), n_masked=0
    )
    block = qc.docs_block()
    assert block.index("[d1]") < block.index("[d2]"), "순위 순서가 보존돼야 한다"


# ── §8-5 누출 통제 ──────────────────────────────────────────────────────────────
class _FakeMask:
    """질의 자신과 같은 패밀리(접두 `fam1_`)를 막는 마스크."""

    def is_allowed(self, qid: str, doc_id: str) -> bool:
        return doc_id != qid and not doc_id.startswith("fam1_")


def test_context_excludes_leaking_documents(tmp_path, monkeypatch):
    """마스크가 막는 문서는 컨텍스트에 들어가지 않고, 다음 순위로 채워진다."""
    run = tmp_path / "sys_P1_test.txt"
    ranked = ["q1", "fam1_a", "ok1", "ok2", "fam1_b", "ok3"]
    run.write_text(
        "".join(f"q1 Q0 {d} {i} {1.0 / i:.6f} P1_test\n" for i, d in enumerate(ranked, 1)),
        encoding="utf-8",
    )
    monkeypatch.setattr(ctx, "ARM_DIR", tmp_path)

    out = ctx.build_arm_contexts(
        "P1",
        doc_text={d: f"본문 {d}" for d in ranked},
        q_text={"q1": "청구항"},
        mask=_FakeMask(),
        qids=["q1"],
        k=3,
    )
    got = out["q1"]
    assert got.doc_ids == ("ok1", "ok2", "ok3")
    assert got.n_masked == 3, "질의 자신 1건 + 같은 패밀리 2건이 걷혔다"
    assert "q1" not in got.docs_block().split("[")[1]


@pytest.mark.parametrize("arm", frozen.ARMS)
def test_frozen_run_contexts_have_zero_leakage(arm):
    """실데이터 감사 — 동결 run 상위 K 에 누출 문서가 섞이지 않았는가(§1-4)."""
    pytest.importorskip("pandas")
    from sdkb_paper import config

    if not (ctx.run_path(arm).exists() and config.IR_CORPUS.exists()
            and config.IR_QREL_TEST_SEALED.exists() and config.IR_FAMILY_MAP.exists()):
        pytest.skip("동결 run·코퍼스·봉인 qrel 이 로컬에 없다 (gitignore 대상)")

    from sdkb_paper.retrieval.candidate import CandidateMask

    doc_text, q_text = ctx.load_texts()
    qids = ctx.test_qids()[:20]          # 감사 표본 — 전량은 CLI 가 돈다
    out = ctx.build_arm_contexts(arm, doc_text, q_text, CandidateMask(), qids)
    for qc in out.values():
        assert qc.qid not in qc.doc_ids, "질의 자신이 컨텍스트에 있다"
        assert len(qc.doc_ids) <= frozen.K
        assert all(t for t in qc.doc_texts), "본문 결측 문서가 컨텍스트에 있다"


# ── §8-2 채점의 결정성 ──────────────────────────────────────────────────────────
_REC = {
    "qid": "q1",
    "ok": True,
    "stop_reason": "end_turn",
    "context_doc_ids": ["d1", "d2", "d3"],
    "text": json.dumps(
        {
            "cited": ["d1", "[d2]", "dX"],
            "evidence": [
                {"doc_id": "d1", "quote": "게이트 절연막을 형성한다", "why": "동일 공정"},
                {"doc_id": "d2", "quote": "본문에 없는 문장", "why": "허위"},
            ],
            "insufficient": False,
        },
        ensure_ascii=False,
    ),
}
_DOCS = {
    "d1": "반도체 소자에서 게이트 절연막을  형성한다. 이후 식각한다.",
    "d2": "다른 내용.",
    "d3": "또 다른 내용.",
}


def test_scoring_is_deterministic_byte_for_byte():
    a = score.score_one(_REC, {"d1"}, _DOCS)
    b = score.score_one(json.loads(json.dumps(_REC)), {"d1"}, _DOCS)
    dump = lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True)  # noqa: E731
    assert dump(a) == dump(b)
    assert dump(score.aggregate([a])) == dump(score.aggregate([b]))


def test_scoring_counts_are_correct():
    s = score.score_one(_REC, {"d1"}, _DOCS)
    assert s["n_cited"] == 3
    assert s["n_cited_correct"] == 1                 # d1 만 qrel 양성
    assert s["n_cited_out_of_context"] == 1          # dX 는 컨텍스트에 없다 = 환각
    assert s["n_pos_in_context"] == 1
    assert s["n_quotes"] == 2
    assert s["n_quotes_grounded"] == 1, "공백 정규화 후 원문에 있는 인용만 인정한다"
    assert s["parse_fail"] is False


def test_parse_failure_is_counted_not_repaired():
    """출력이 스키마를 어기면 **고쳐 읽지 않고** 실패로 센다(§12.4 판별 기준)."""
    bad = dict(_REC, text="여기 답이 있습니다: {\"cited\": [\"d1\"]} 감사합니다")
    assert score.score_one(bad, {"d1"}, _DOCS)["parse_fail"] is True
    assert score.score_one(dict(_REC, ok=False, text=""), {"d1"}, _DOCS)["parse_fail"] is True


def test_code_fence_is_unwrapped_but_only_the_shell():
    """§12.4 수리 — 껍질(```json)만 벗긴다. 펜스 밖에 글자가 있으면 여전히 실패다."""
    body = json.dumps({"cited": ["d1"], "evidence": [], "insufficient": False}, ensure_ascii=False)
    for fence in (f"```json\n{body}\n```", f"```\n{body}\n```", f"  ```json\n{body}\n```  "):
        assert score.score_one(dict(_REC, text=fence), {"d1"}, _DOCS)["parse_fail"] is False
    # 펜스가 있어도 밖에 설명이 붙으면 고쳐 읽지 않는다(§13.3-2 원칙 유지).
    assert score.score_one(
        dict(_REC, text=f"아래와 같습니다.\n```json\n{body}\n```"), {"d1"}, _DOCS
    )["parse_fail"] is True
    # 여는 펜스 줄에 다른 내용이 섞이면 언랩하지 않는다.
    assert score.score_one(
        dict(_REC, text=f"```json 답:\n{body}\n```"), {"d1"}, _DOCS
    )["parse_fail"] is True


def test_prose_after_closing_fence_is_dropped():
    """§12.4 수리 2 (PLAN-047 §17.2) — 닫는 펜스 **뒤**의 설명은 버리고 읽는다.

    B층 1,188 호출에서 실패 39건이 전부 이 형태였다(전부 `insufficient: true`).
    포장의 문제이므로 판독값과 무관하다 — 넓어지는 것은 이 한 경우뿐이다.
    """
    body = json.dumps({"cited": ["d1"], "evidence": [], "insufficient": False}, ensure_ascii=False)
    scored = score.score_one(
        dict(_REC, text=f"```json\n{body}\n```\n\n**설명:** 후보 문헌에는 …"), {"d1"}, _DOCS
    )
    assert scored["parse_fail"] is False
    assert scored["n_cited"] == 1 and scored["n_cited_correct"] == 1
    # 닫는 펜스가 없으면(절단 등) 수리 후에도 실패다 — 완화의 범위를 여기서 못박는다.
    assert score.score_one(
        dict(_REC, text=f"```json\n{body}"), {"d1"}, _DOCS
    )["parse_fail"] is True


def test_aggregate_reports_conditional_and_denominators():
    """§11.4-① — 전체와 '근거 존재 질의 조건부' 를 함께 낸다."""
    no_ev = dict(_REC, qid="q2", context_doc_ids=["d2", "d3"],
                 text=json.dumps({"cited": ["d2"], "evidence": [], "insufficient": False}))
    scored = [score.score_one(_REC, {"d1"}, _DOCS), score.score_one(no_ev, {"d1"}, _DOCS)]
    agg = score.aggregate(scored)
    assert agg["n_queries"] == 2
    assert agg["n_queries_with_evidence"] == 1
    assert agg["citation_precision"] == pytest.approx(1 / 4)       # 인용 4건 중 1건 정답
    assert agg["citation_precision_cond"] == pytest.approx(1 / 3)  # 근거 존재 질의만
    assert agg["hallucination_rate"] == pytest.approx(1 / 4)


def test_variance_is_reported_not_hidden():
    """§1-11 — 반복 분산은 0 이 아니어도 그대로 싣는다. 1회차면 sd 는 None(0 아님)."""
    reps = [{"citation_precision": 0.2}, {"citation_precision": 0.3}]
    v = score.across_repeats(reps)["citation_precision"]
    assert v["mean"] == pytest.approx(0.25) and v["sd"] is not None
    assert score.across_repeats([reps[0]])["citation_precision"]["sd"] is None


def test_score_all_is_byte_identical_on_rerun(tmp_path):
    """§8-2 를 CLI 경로에서도 확인한다 — 같은 생성 원문 → 같은 바이트."""
    pytest.importorskip("pandas")
    from sdkb_paper import config

    if not (config.IR_CORPUS.exists() and config.IR_QREL_TEST_SEALED.exists()):
        pytest.skip("코퍼스·봉인 qrel 이 로컬에 없다 (gitignore 대상)")

    qid = ctx.test_qids()[0]
    for arm in frozen.ARMS:
        path = tmp_path / f"gen_{frozen.RUNSET}_{frozen.SPLIT}_{arm}_rep0.jsonl"
        header = {"_header": True, "arm": arm, "rep": 0, "run_sha256": "x" * 64}
        rec = dict(_REC, qid=qid, arm=arm, rep=0)
        path.write_text(
            json.dumps(header, ensure_ascii=False, sort_keys=True) + "\n"
            + json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    dump = lambda r: json.dumps(r, ensure_ascii=False, sort_keys=True, indent=2)  # noqa: E731
    first = dump(score.score_all(tmp_path))
    assert first == dump(score.score_all(tmp_path))
    assert "generations" not in first, "절대 경로·시각이 산출물에 들어가면 결정성이 깨진다"


def test_markdown_table_has_no_timestamp():
    """표가 결정적이어야 재생성 차이가 곧 결과 차이다(§8-2 의 연장)."""
    report = {"arms": {a: {"across_repeats": score.across_repeats([])} for a in frozen.ARMS}}
    md = score.to_markdown(report)
    assert "확증이 아니다" in md, "A층 표에는 지위가 박혀 있어야 한다(§7)"
    assert score.to_markdown(report) == md


# ── 경계: 검색 코드를 건드리지 않는다 (§9-4) ────────────────────────────────────
def test_rag_package_does_not_write_retrieval_artifacts():
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    for p in (root / "src" / "sdkb_paper" / "rag").rglob("*.py"):
        text = p.read_text(encoding="utf-8")
        assert "IR_RUNS_DIR" not in text, f"{p.name}: O′ 로 덮인 최상위 runs/ 를 보면 안 된다(팔 표류)"
        assert "qrel_b_sealed" not in text, f"{p.name}: B층 봉인 qrel 은 A층 코드가 읽지 않는다"
