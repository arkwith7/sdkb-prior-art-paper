"""하위집단 분해 T2 (PLAN-018 §7.3 M4-10 · 원고 §5.2·5.3 · T-gate T2).

두 시스템의 family Recall@100 을 하위집단별로 분해해 **국소 회귀**(max drop)를 잰다 — T2 안전성 게이트
입력. 하위집단 축:

- **정답 언어(cross-lingual):** 질의 자체는 전량 한국어이므로 **정답(positive)의 언어 구성**으로 나눈다
  (KR-only / 외국포함 / 혼합). 정답의 39% 가 영어·2% 일본어(SPEC-007) — 언어중립 개념 온톨로지팔이
  값을 증명할 무대(원고 H2b). 이 축이 T2 의 핵심 KR/외국 차원이다.
- **공정군(process group):** 질의 지배 개념 축(Process·SubProcess / Device / Material / FailureMode …).
- **거절근거:** 코퍼스에 부재(온톨로지 rejectedFor 조인 필요) → **후속**(레이블 배선 시 추가).

최소 질의수(기본 20) 미달 하위집단은 확정결론 금지 · 표에 n 명기(M4-10).

- **경계:** qrel 읽음(analysis) · 순위생성 없음 · dev 로만.
CLI: `python -m sdkb_paper.analysis.subgroup --a RUN_NEW --b RUN_OLD [--split dev]`.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from .. import config
from .bootstrap import per_query_recall
from .metrics import load_qrel, load_run

MIN_N = 20   # 하위집단 최소 질의수(미달 = 확정결론 금지)


def positive_lang_label(pos_docs: set[str], doc_lang: dict[str, str]) -> str:
    """정답 문서 언어 구성 → 'kr_only' / 'has_foreign' / 'unknown'."""
    langs = {doc_lang.get(d, "") for d in pos_docs}
    langs.discard("")
    if not langs:
        return "unknown"
    foreign = any(lg != "ko" for lg in langs)
    return "has_foreign" if foreign else "kr_only"


def query_labels(qrel: dict[str, set[str]]) -> dict[str, dict[str, str]]:
    """질의 → {'pos_lang': ..., 'proc_group': ...}."""
    import pandas as pd

    from ..ontology.concept_axis import load_axis
    axis = load_axis()
    df = pd.read_parquet(config.IR_CORPUS, columns=["doc_id", "lang", "concepts", "is_query"])
    doc_lang = dict(zip(df["doc_id"].astype(str), df["lang"].astype(str)))
    qconcepts = {str(d): (list(c) if c is not None else [])
                 for d, c, isq in zip(df["doc_id"], df["concepts"], df["is_query"]) if isq}

    def proc_group(qid: str) -> str:
        axes = [axis.get(c, "") for c in qconcepts.get(qid, [])]
        for grp, members in [("process", {"Process", "SubProcess"}),
                             ("device", {"Device"}),
                             ("failure", {"FailureMode"}),
                             ("material", {"Material"})]:
            if any(a in members for a in axes):
                return grp
        return "other"

    out = {}
    for qid, pos in qrel.items():
        if not pos:
            continue
        out[qid] = {"pos_lang": positive_lang_label(pos, doc_lang),
                    "proc_group": proc_group(qid)}
    return out


def by_subgroup(run, qrel, fam, labels, dim: str, k: int = 100) -> dict[str, dict]:
    """dim(pos_lang|proc_group)별 평균 R@k + n. fam 는 family 지도."""
    pq = per_query_recall(run, qrel, k=k, family=fam)
    groups: dict[str, list[float]] = {}
    for qid, r in pq.items():
        g = labels.get(qid, {}).get(dim, "unknown")
        groups.setdefault(g, []).append(r)
    return {g: {"n": len(v), "recall": sum(v) / len(v)} for g, v in groups.items()}


def compare(run_new, run_old, qrel, fam, labels, dim: str, k: int = 100) -> dict:
    """하위집단별 R@k(new,old) + drop(old−new). max drop = T2 입력."""
    a = by_subgroup(run_new, qrel, fam, labels, dim, k)
    b = by_subgroup(run_old, qrel, fam, labels, dim, k)
    rows, max_drop = [], -1.0
    for g in sorted(set(a) | set(b)):
        rn, ro = a.get(g, {}).get("recall", 0.0), b.get(g, {}).get("recall", 0.0)
        n = a.get(g, {}).get("n", b.get(g, {}).get("n", 0))
        drop = ro - rn
        rows.append({"group": g, "n": n, "r_new": rn, "r_old": ro, "drop": drop,
                     "reliable": n >= MIN_N})
        if n >= MIN_N and drop > max_drop:
            max_drop = drop
    return {"dim": dim, "rows": rows, "max_drop": max_drop}


def _fmt(res: dict, delta: float) -> str:
    lines = [f"  [{res['dim']}]  max_drop(신뢰집단만) = {res['max_drop']:+.4f}"
             f"  {'≥δ 국소회귀!' if res['max_drop'] >= delta else '(< δ 안전)'}"]
    lines.append(f"    {'집단':<14}{'n':>5}{'R_new':>9}{'R_old':>9}{'drop':>9}")
    for r in res["rows"]:
        flag = "" if r["reliable"] else "  (n<20·비확정)"
        lines.append(f"    {r['group']:<14}{r['n']:>5}{r['r_new']:>9.4f}"
                     f"{r['r_old']:>9.4f}{r['drop']:>+9.4f}{flag}")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", type=Path, required=True, help="새 시스템 run(예: P0★)")
    ap.add_argument("--b", type=Path, required=True, help="기준 run(예: B3)")
    ap.add_argument("--split", choices=["train", "dev", "test", "all"], default="dev")
    ap.add_argument("--k", type=int, default=100)
    ap.add_argument("--delta", type=float, default=0.05, help="T2 마진 δ(F3)")
    args = ap.parse_args()
    if args.split == "test":
        print("⚠️  test 개봉 — 사전등록 위반 가능(F9)")

    from ..collect.bq_family_ir import load_family_map
    import pandas as pd
    fam = load_family_map()
    qrel = load_qrel()
    if args.split != "all":
        sp = pd.read_parquet(config.IR_SPLIT)
        keep = set(sp.loc[sp["split"] == args.split, "doc_id"])
        qrel = {q: pos for q, pos in qrel.items() if q in keep}
    labels = query_labels(qrel)
    run_a, run_b = load_run(args.a), load_run(args.b)
    print(f"[하위집단 T2 · {args.split} · family R@{args.k} · δ={args.delta}]  new={args.a.name} old={args.b.name}")
    for dim in ("pos_lang", "proc_group"):
        print(_fmt(compare(run_a, run_b, qrel, fam, labels, dim, args.k), args.delta))


if __name__ == "__main__":
    main()
