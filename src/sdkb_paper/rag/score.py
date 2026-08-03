"""채점 — 인용 식별자 대조 (PLAN-038 §12.1-9 · `make rageval`).

**결정적이다**(§8 성공기준 2). LLM 판정자를 쓰지 않고, 시각·경로·난수를 산출물에 넣지 않으며,
같은 생성 원문을 두 번 채점하면 **바이트 동일**한 JSON 이 나온다.

지표(§6). 넷 다 식별자·문자열 대조로만 정해진다.
  - **인용 정확도** = 인용한 식별자 중 봉인 qrel 양성의 비율
  - **환각률** = 인용한 식별자 중 **컨텍스트에 없던** 것의 비율(식별자 층 · 결정적)
  - **근거 문장 일치** = evidence 의 quote 가 해당 문서 본문에 그대로 있는 비율
    (§6 "근거 지역화"의 **결정적 하한**이다 — 사람 표본 검증은 등급 2 로 따로 한다)
  - **반복 분산** = 회차별 지표의 표준편차. 0 이 아니어도 그대로 싣는다(§1-11)

보고 규칙 둘(§11.4 동결). ① 인용 정확도는 **전체**와 **근거 존재 질의 조건부** 둘 다 낸다 —
K=10 컨텍스트에는 정답이 한 건도 없는 질의가 다수이고, 거기서 "정확한 인용"은 정의상 불가능하다.
② **문서 단위**다 — 주분석의 family 단위와 분모가 다르므로 섞지 않는다(CLAUDE §0 분모 규율).

CLI: `uv run python -m sdkb_paper.rag.score [--write]`
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics as st
from pathlib import Path

from .. import config
from . import frozen

_WS = re.compile(r"\s+")


def norm_id(raw: object) -> str:
    """`[kr_KR10…]` · 공백 → `kr_KR10…`. 대소문자는 보존한다(코퍼스 식별자가 대소문자 혼합)."""
    return str(raw).strip().strip("[]").strip()


def norm_text(s: str) -> str:
    return _WS.sub(" ", s).strip()


def parse_answer(text: str) -> dict | None:
    """엄격 파싱 — 스키마를 만족하지 않으면 None(파싱 실패로 계수한다)."""
    try:
        obj = json.loads(text.strip())
    except (ValueError, AttributeError):
        return None
    if not isinstance(obj, dict) or not isinstance(obj.get("cited"), list):
        return None
    if not isinstance(obj.get("evidence", []), list):
        return None
    return obj


def score_one(rec: dict, positives: set[str], doc_text: dict[str, str]) -> dict:
    """1건 채점. run·모델을 다시 부르지 않는다 — 기록된 원문만 본다."""
    ctx_ids = [norm_id(d) for d in rec.get("context_doc_ids", [])]
    ctx_set = set(ctx_ids)
    n_pos_in_ctx = len(ctx_set & positives)
    out = {
        "qid": rec.get("qid", ""),
        "ok": bool(rec.get("ok")),
        "truncated": rec.get("stop_reason") == "max_tokens",
        "n_pos_in_context": n_pos_in_ctx,
        "parse_fail": False,
        "insufficient": False,
        "n_cited": 0,
        "n_cited_correct": 0,
        "n_cited_out_of_context": 0,
        "n_quotes": 0,
        "n_quotes_grounded": 0,
    }
    if not out["ok"]:
        out["parse_fail"] = True
        return out

    ans = parse_answer(rec.get("text", ""))
    if ans is None:
        out["parse_fail"] = True
        return out

    cited = [norm_id(c) for c in ans["cited"]]
    out["insufficient"] = bool(ans.get("insufficient"))
    out["n_cited"] = len(cited)
    out["n_cited_correct"] = sum(1 for c in cited if c in positives)
    out["n_cited_out_of_context"] = sum(1 for c in cited if c not in ctx_set)

    for ev in ans.get("evidence", []):
        if not isinstance(ev, dict):
            continue
        quote = norm_text(str(ev.get("quote", "")))
        if not quote:
            continue
        out["n_quotes"] += 1
        body = norm_text(doc_text.get(norm_id(ev.get("doc_id", "")), ""))
        if body and quote in body:
            out["n_quotes_grounded"] += 1
    return out


def _ratio(num: int, den: int) -> float | None:
    return round(num / den, 6) if den else None


def aggregate(scored: list[dict]) -> dict:
    """한 (팔 × 회차) 의 집계. 분모를 지표마다 명시한다 — 혼용 금지(§0 분모 규율)."""
    n = len(scored)
    n_ok = sum(1 for s in scored if s["ok"])
    cond = [s for s in scored if s["n_pos_in_context"] > 0]   # 근거 존재 질의
    cited_all = sum(s["n_cited"] for s in scored)
    cited_cond = sum(s["n_cited"] for s in cond)
    return {
        "n_queries": n,
        "n_call_fail": n - n_ok,
        "parse_fail_rate": _ratio(sum(1 for s in scored if s["parse_fail"]), n),
        "truncation_rate": _ratio(sum(1 for s in scored if s["truncated"]), n),
        "insufficient_rate": _ratio(sum(1 for s in scored if s["insufficient"]), n),
        "n_queries_with_evidence": len(cond),
        "mean_cited_per_query": round(cited_all / n, 6) if n else None,
        # 인용 정확도 — 전체(분모 = 인용 식별자 전량)
        "citation_precision": _ratio(sum(s["n_cited_correct"] for s in scored), cited_all),
        # 인용 정확도 — 근거 존재 질의 조건부(§11.4-①)
        "citation_precision_cond": _ratio(sum(s["n_cited_correct"] for s in cond), cited_cond),
        # 환각률 — 컨텍스트에 없던 식별자
        "hallucination_rate": _ratio(sum(s["n_cited_out_of_context"] for s in scored), cited_all),
        # 근거 문장 일치 — 근거 지역화의 결정적 하한
        "quote_grounded_rate": _ratio(
            sum(s["n_quotes_grounded"] for s in scored), sum(s["n_quotes"] for s in scored)
        ),
    }


VARIANCE_KEYS = (
    "citation_precision", "citation_precision_cond", "hallucination_rate",
    "quote_grounded_rate", "insufficient_rate", "truncation_rate",
)


def across_repeats(per_rep: list[dict]) -> dict:
    """회차 간 평균·표준편차. 회차가 1이면 sd 는 None — 0 으로 적지 않는다."""
    out: dict[str, dict] = {}
    for k in VARIANCE_KEYS:
        vals = [r[k] for r in per_rep if r.get(k) is not None]
        out[k] = {
            "mean": round(st.fmean(vals), 6) if vals else None,
            "sd": round(st.stdev(vals), 6) if len(vals) > 1 else None,
            "n_reps": len(vals),
        }
    return out


# ── 적재·CLI ────────────────────────────────────────────────────────────────────
def load_jsonl(path: Path) -> tuple[dict, list[dict]]:
    header, recs = {}, []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        (header.update(obj) if obj.get("_header") else recs.append(obj))
    return header, recs


def score_all(gen_dir: Path | None = None) -> dict:
    """생성 JSONL 전량 → 결정적 채점 보고. 시각·경로 절대값을 넣지 않는다."""
    import pandas as pd

    from ..analysis.metrics import load_qrel

    gen_dir = gen_dir or config.RAG_GEN_DIR
    qrel = load_qrel(config.IR_QREL_TEST_SEALED)
    corpus = pd.read_parquet(config.IR_CORPUS, columns=["doc_id", "text_main"])
    doc_text = {str(d): ("" if t is None else str(t)) for d, t in zip(corpus["doc_id"], corpus["text_main"])}

    report: dict = {"frozen": frozen.frozen_manifest(), "arms": {}, "inputs": {}}
    for arm in frozen.ARMS:
        per_rep = []
        for path in sorted(gen_dir.glob(f"gen_*_{arm}_rep*.jsonl")):
            header, recs = load_jsonl(path)
            scored = [score_one(r, qrel.get(r.get("qid", ""), set()), doc_text) for r in recs]
            agg = aggregate(scored)
            agg["rep"] = header.get("rep")
            agg["run_sha256"] = header.get("run_sha256", "")
            per_rep.append(agg)
            report["inputs"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        report["arms"][arm] = {"per_rep": per_rep, "across_repeats": across_repeats(per_rep)}
    return report


def to_markdown(report: dict) -> str:
    """원고 §6.8 탐색적 표. **A층은 확증이 아니다** — 표 머리에 그 사실을 박는다."""
    lines = [
        "# C2′ 전달 실험 — A층 탐색적 판독 (PLAN-038 §12 · RQ5)",
        "",
        "**확증이 아니다.** A층의 목적은 계측기 동결이며(§7 결정 \"다\"), 확증은 B층에서 한다.",
        f"모델 `{frozen.MODEL_ID}` · K={frozen.K} · 온도 {frozen.TEMPERATURE} · "
        f"반복 {frozen.N_REPEATS}회 · 프롬프트 sha256 `{frozen.PROMPT_SHA256[:16]}…`",
        "",
        "| 지표 | " + " | ".join(f"{a} 평균 (sd)" for a in frozen.ARMS) + " |",
        "|---|" + "---|" * len(frozen.ARMS),
    ]
    labels = {
        "citation_precision": "인용 정확도 (전체)",
        "citation_precision_cond": "인용 정확도 (근거 존재 질의 조건부)",
        "hallucination_rate": "환각률 (컨텍스트 밖 식별자)",
        "quote_grounded_rate": "근거 문장 일치 (결정적 하한)",
        "insufficient_rate": "근거 불충분 선언 비율",
        "truncation_rate": "출력 절단율",
    }
    for key, label in labels.items():
        cells = []
        for arm in frozen.ARMS:
            v = report["arms"].get(arm, {}).get("across_repeats", {}).get(key, {})
            m, sd = v.get("mean"), v.get("sd")
            cells.append("—" if m is None else f"{m:.4f}" + (f" ({sd:.4f})" if sd is not None else " (—)"))
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "질의는 문서 단위이며 주분석(family 단위 R@100)과 **분모가 다르다**(§11.4-②).",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="C2′ 전달 실험 — 결정적 채점 (PLAN-038 §12.1-9)")
    ap.add_argument("--write", action="store_true", help="JSON·표를 파일로 쓴다")
    a = ap.parse_args()

    report = score_all()
    if not report["inputs"]:
        print(f"[없음] 생성 산출물이 없다: {config.RAG_GEN_DIR} — 먼저 `make rag` 를 돌린다.")
        return 1
    text = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)
    print(to_markdown(report))
    if a.write:
        config.RAG_SCORE_DIR.mkdir(parents=True, exist_ok=True)
        (config.RAG_SCORE_DIR / "rag_transfer_score.json").write_text(text + "\n", encoding="utf-8")
        config.RAG_TABLE.parent.mkdir(parents=True, exist_ok=True)
        config.RAG_TABLE.write_text(to_markdown(report), encoding="utf-8")
        print(f"[기록] {config.RAG_TABLE.relative_to(config.ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
