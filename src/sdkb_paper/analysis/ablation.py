"""Ablation A1–A8 (PLAN-018 §7.3 M4-8 · 원고 §5.4).

선택된 P0★(결합 제안)에서 온톨로지 계층을 하나씩 제거해 **ΔRecall@100(family)** 을 잰다. 각 제거의
페어드 부트스트랩 CI + **Holm 다중비교 보정**(F6). 원고 §5.4 표:

| A | 제거 | 이번 세션 |
|---|---|---|
| A1 | CPC/IPC (use_ipc=False) | ✅ |
| A2 | 공정·소자 (Process·SubProcess·Device 축) | ✅ |
| A3 | 재료·장비·고장 (Material·Equipment·FailureMode 축) | ✅ |
| A4 | ClaimFeature | ⏸ P1/P2 후속(입력 부재) |
| A5 | 거절근거·판단 | ⏸ P1/P2 후속 |
| A6 | 계층 경로(use_path=False, 개념겹침만) | ✅ |
| A7 | 전체 온톨로지 (α=0 → 텍스트전용=B3) | ✅ |
| A8 | 전문가계층(Skill 축) — 음성대조군(H5) | ✅ |

- **H4(계층기여):** A4/A5 손실 > A1 — **A4/A5 미가용 → 후속**.
- **H5(특이성):** A8 의 ΔR@100 이 유의하지 않아야(음성대조군). 유의 악화 시 "태스크 결합" 발견으로 전환(부록 F).

- **경계:** qrel 읽음(analysis) · 순위는 systems 가 만든다 · dev 로만.
"""
from __future__ import annotations

import argparse

from .. import config
from ..retrieval import systems as S
from ..retrieval.candidate import CandidateMask
from ..retrieval.hybrid import RUN_B3
from ..retrieval.ontology_rerank import OntologyFeatures
from .bootstrap import paired_bootstrap
from .metrics import evaluate, load_qrel, load_run
from .ontology_eval import component_cache, rerank_from_cache

# (id, 설명, ablation 인자) — component_cache 를 각 구성으로 재계산(6종만)
ABLATIONS = [
    ("A1", "−CPC/IPC", dict(use_ipc=False)),
    ("A2", "−공정·소자", dict(keep_axes=S.ALL_AXES - S.AXES_PROCESS_DEVICE)),
    ("A3", "−재료·장비·고장", dict(keep_axes=S.ALL_AXES - S.AXES_MATERIAL_EQUIP_FAILURE)),
    ("A6", "−계층경로(개념겹침만)", dict(use_path=False)),
    ("A7", "−전체온톨로지(=텍스트전용)", "TEXT_ONLY"),
    ("A8", "−전문가계층(Skill·음성대조군)", dict(keep_axes=S.ALL_AXES - S.AXES_EXPERT)),
]


def holm(pairs: list[tuple[str, float]], alpha: float = 0.05) -> dict[str, bool]:
    """Holm-Bonferroni: (label, p) → label→reject. 오름차순 p 에 α/(m−i) 임계."""
    m = len(pairs)
    ordered = sorted(pairs, key=lambda x: x[1])
    out, prev_reject = {}, True
    for i, (lab, p) in enumerate(ordered):
        thresh = alpha / (m - i)
        rej = prev_reject and (p < thresh)
        out[lab] = rej
        prev_reject = rej
    return out


def run_ablation(split: str = "dev", alpha: float = 0.5,
                 w: tuple[float, float, float] = (0.5, 0.0, 0.5), k: int = 100) -> dict:
    """선택된 P0★(alpha,w)에서 A1–A8 제거손실. 반환: full R@100 + 각 ablation Δ·CI."""
    import pandas as pd

    from ..collect.bq_family_ir import load_family_map
    fam = load_family_map()
    qrel = load_qrel()
    sp = pd.read_parquet(config.IR_SPLIT)
    if split != "all":
        keep = set(sp.loc[sp["split"] == split, "doc_id"])
        qrel = {q: pos for q, pos in qrel.items() if q in keep}
    qids = [q for q, pos in qrel.items() if pos]

    feats = OntologyFeatures()
    mask = CandidateMask()
    b3 = load_run(RUN_B3)

    # full P0★ (모든 축·경로·IPC)
    cache_full = component_cache(feats, mask, b3, qids)
    run_full = rerank_from_cache(cache_full, alpha, w, k=1000)
    r_full = evaluate(run_full, qrel, ks=(k,), family=fam)["recall"][k]

    rows, pvals = [], []
    for aid, desc, arg in ABLATIONS:
        if arg == "TEXT_ONLY":
            run_ab = rerank_from_cache(cache_full, 0.0, (1.0, 0.0, 0.0), k=1000)
        else:
            cache_ab = component_cache(feats, mask, b3, qids, **arg)
            # A1(use_ipc=False): w_i 를 0 으로 두고 재랭크(항 제거)
            w_ab = (w[0], w[1], 0.0) if arg.get("use_ipc") is False else w
            a_ab = alpha
            run_ab = rerank_from_cache(cache_ab, a_ab, w_ab, k=1000)
        r_ab = evaluate(run_ab, qrel, ks=(k,), family=fam)["recall"][k]
        bs = paired_bootstrap(run_full, run_ab, qrel, k=k, family=fam)
        delta = bs["delta"]      # full − ablated = 제거손실(양수 = 계층이 기여)
        p = bs["p_two_sided"]
        rows.append({"id": aid, "desc": desc, "r_ablated": r_ab, "delta_loss": delta,
                     "lb95": bs["lb95"], "ub95": bs["ub95"], "p": p})
        pvals.append((aid, p))
    reject = holm(pvals)
    for row in rows:
        row["holm_sig"] = reject[row["id"]]
    return {"split": split, "alpha": alpha, "w": w, "r_full": r_full, "k": k, "rows": rows}


def _fmt(res: dict) -> str:
    lines = [f"[Ablation · {res['split']} · P0★ α={res['alpha']} w={res['w']} · family R@{res['k']}]",
             f"  P0★(full) R@{res['k']} = {res['r_full']:.4f}",
             "  ─" * 20,
             f"  {'A':<4}{'제거':<22}{'R@k':>8}{'제거손실Δ':>11}{'95%CI':>20}{'p':>7}{'Holm':>6}"]
    for r in res["rows"]:
        ci = f"[{r['lb95']:+.4f},{r['ub95']:+.4f}]"
        sig = "유의" if r["holm_sig"] else "n.s."
        lines.append(f"  {r['id']:<4}{r['desc']:<22}{r['r_ablated']:>8.4f}"
                     f"{r['delta_loss']:>+11.4f}{ci:>20}{r['p']:>7.3f}{sig:>6}")
    lines.append("  (제거손실Δ = full − ablated · 양수=계층 기여 · A8 은 음성대조군=n.s. 기대)")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "dev", "test", "all"], default="dev")
    ap.add_argument("--alpha", type=float, required=True, help="선택된 P0★ α")
    ap.add_argument("--w", type=float, nargs=3, required=True, metavar=("Wc", "Wh", "Wi"))
    ap.add_argument("--k", type=int, default=100)
    args = ap.parse_args()
    if args.split == "test":
        print("⚠️  test 개봉 — 사전등록 위반 가능(F9)")
    res = run_ablation(args.split, args.alpha, tuple(args.w), args.k)
    print(_fmt(res))


if __name__ == "__main__":
    main()
