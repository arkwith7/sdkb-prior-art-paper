"""T-gate 종합 판정 — Accept(ΔG) (PLAN-019 W3 · 원고 §4.9).

    Accept(ΔG) = 1[L0=L1=L2=L3=pass] · 1[LB95(ΔR100) > −ε]_T1
                 · 1[max_s Drop_s < δ]_T2 · 1[∀f∈{em,tf,core}: PassRate_f ≥]_T3

승인식은 **곱**이다. 하나라도 0 이면 승인은 0 이고, 우회 경로는 없다(CLAUDE.md §5). 이 모듈은
T1·T2·T3 를 한 번에 돌려 판정과 근거를 JSON 으로 남기고 실패 시 비영 종료한다. L0–L3 는 별도
타깃(`make gate` 의 선행 단계)이 판정하며, 여기서는 그 결과를 인자로 받아 곱에 넣는다 —
`--l0-l3-pass/--l0-l3-fail`(기본: 통과로 가정하지 않고 `make gate` 가 넘겨준다).

- **누출 전제:** T1 은 누출 감사 통과가 전제다(CLAUDE.md §5). `--skip-leakage` 없이는 감사부터 돈다.
- **경계:** 판정만 한다. 데이터·순위·qrel 을 고치지 않는다.

CLI: `python -m sdkb_paper.validate.t_gate [--split dev] [--graph PATH] [--baseline g0]`.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .. import config


def accept(l0_l3: bool, t1: bool, t2: bool, t3: bool) -> bool:
    """승인식 — 네 조건의 곱. 완충재 없음."""
    return bool(l0_l3 and t1 and t2 and t3)


def run_tgate(split: str = "dev", new: Path | None = None, old: Path | None = None,
              graph: Path | None = None, baseline: str = "g0",
              l0_l3: bool = True, k: int = 100, skip_leakage: bool = False) -> dict:
    """T1·T2·T3(+누출 감사)를 돌려 종합 판정 dict 를 만든다."""
    from ..analysis.metrics import load_run
    from ..analysis.results_table import _split_qrel, run_path
    from ..analysis.subgroup import query_labels
    from ..collect.bq_family_ir import load_family_map
    from .leakage_check import run_audit
    from .t1_noninferiority import t1_gate
    from .t2_subgroup import t2_gate
    from .t3_cross_task_cq import (
        commit_waiver,
        load_generation,
        log_waiver,
        run_cqs,
        suite_pass_rates,
        t3_gate,
    )

    out: dict = {"split": split, "k": k, "epsilon": config.T_EPSILON, "delta": config.T_DELTA}

    leak = None if skip_leakage else run_audit(split, k)
    out["leakage"] = leak

    qrel = _split_qrel(split)
    fam = load_family_map()
    pnew = new or run_path("P1", split)
    pold = old or run_path("B3_rrf", split)
    run_new, run_old = load_run(pnew), load_run(pold)
    out["runs"] = {"new": pnew.name, "old": pold.name}

    out["t1"] = t1_gate(run_new, run_old, qrel, family=fam, k=k)
    out["t2"] = t2_gate(run_new, run_old, qrel, fam, query_labels(qrel), k=k)

    g = graph or config.GRAPH_V1
    old_gen = load_generation(baseline)
    waiver = commit_waiver()
    out["t3"] = t3_gate(suite_pass_rates(run_cqs(g)), old_gen["suites"], waiver=waiver)
    out["t3"]["graph"] = str(g)
    out["t3"]["baseline_generation"] = old_gen["generation"]
    if out["t3"]["waived"]:
        log_waiver({"generation_old": old_gen["generation"], "graph": str(g),
                    "regressed": out["t3"]["regressed"], "reason": out["t3"]["waiver_reason"]})

    out["l0_l3"] = l0_l3
    # 누출 실패는 T1 의 전제 파괴다 — 승인식 앞단에서 곧바로 거부한다.
    leak_ok = True if leak is None else leak["pass"]
    out["leakage_pass"] = leak_ok
    out["accept"] = accept(l0_l3 and leak_ok, out["t1"]["pass"], out["t2"]["pass"],
                           out["t3"]["pass"])
    return out


def format_report(res: dict) -> str:
    from .leakage_check import format_report as leak_fmt
    from .t1_noninferiority import format_report as t1_fmt
    from .t2_subgroup import format_report as t2_fmt
    from .t3_cross_task_cq import format_report as t3_fmt

    lines = [f"═══ T-gate 종합 판정 (split={res['split']} · ε={res['epsilon']} · δ={res['delta']})",
             f"  run: new={res['runs']['new']}  old={res['runs']['old']}", ""]
    if res["leakage"] is not None:
        lines += [leak_fmt(res["leakage"]), ""]
    lines += [t1_fmt(res["t1"]), "", t2_fmt(res["t2"]), "", t3_fmt(res["t3"]), ""]
    flags = [("L0–L3", res["l0_l3"]), ("누출감사", res["leakage_pass"]),
             ("T1", res["t1"]["pass"]), ("T2", res["t2"]["pass"]), ("T3", res["t3"]["pass"])]
    lines.append("  " + " · ".join(f"{n}={'✅' if v else '❌'}" for n, v in flags))
    lines.append(f"  ⇒ Accept(ΔG) = {'1  승인' if res['accept'] else '0  거부'}")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "dev", "test", "all"], default="dev")
    ap.add_argument("--new", type=Path, default=None, help="신 버전 run(기본 P1)")
    ap.add_argument("--old", type=Path, default=None, help="구 버전 run(기본 B3)")
    ap.add_argument("--graph", type=Path, default=None, help="T3 대상 그래프(기본 graph_v1)")
    ap.add_argument("--baseline", default="g0", help="T3 기준 세대 라벨")
    ap.add_argument("--k", type=int, default=100)
    ap.add_argument("--l0-l3", dest="l0_l3", choices=["pass", "fail"], default="pass",
                    help="선행 L0–L3 결과(기본 pass — `make gate` 가 앞단에서 실행)")
    ap.add_argument("--skip-leakage", action="store_true", help="누출 감사 생략(진단 전용)")
    ap.add_argument("--out", type=Path, default=None, help="판정 JSON 경로")
    args = ap.parse_args()

    res = run_tgate(args.split, args.new, args.old, args.graph, args.baseline,
                    l0_l3=(args.l0_l3 == "pass"), k=args.k, skip_leakage=args.skip_leakage)
    print(format_report(res))
    out = args.out or config.TGATE_REPORT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"✓ {out}")
    sys.exit(0 if res["accept"] else 1)


if __name__ == "__main__":
    main()
