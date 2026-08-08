"""T-gate 종합 판정 — Accept(ΔG) (PLAN-019 W3 · 원고 §4.9).

    Accept(ΔG) = 1[L0=L1=L2=L3=pass] · 1[LB95(ΔR100) > −ε]_T1
                 · 1[max_s Drop_s < δ]_T2 · 1[∀f∈{em,tf,core}: PassRate_f ≥]_T3

승인식은 **곱**이다. 하나라도 0 이면 승인은 0 이고, 우회 경로는 없다(CLAUDE.md §5). 이 모듈은
T1·T2·T3 를 한 번에 돌려 판정과 근거를 JSON 으로 남기고 실패 시 비영 종료한다. L0–L3 는 별도
타깃(`make gate` 의 선행 단계)이 판정하며, 여기서는 그 결과를 인자로 받아 곱에 넣는다 —
`--l0-l3-pass/--l0-l3-fail`(기본: 통과로 가정하지 않고 `make gate` 가 넘겨준다).

- **누출 전제:** T1 은 누출 감사 통과가 전제다(CLAUDE.md §5). `--skip-leakage` 없이는 감사부터 돈다.
- **경계:** 판정만 한다. 데이터·순위·qrel 을 고치지 않는다.

**두 가지 모드(D-19).** 기본 `--mode system` 은 시스템 대 시스템 비교이고(P1 대 B3 — 기존 동작
불변), **H2(갱신 승인 안전성)의 증거가 아니다**(CLAUDE.md §0). H2 는 `--mode resource` 로만
잰다: 같은 시스템·같은 코드·같은 정답지에 **자원 스냅샷만 다른** 두 run 세트를 넣는다. 적격심사
(`runset.eligibility`)를 통과하지 못하면 T1·T2 를 **돌리지 않고** 미검정으로 끝낸다 — 부적격
비교의 수치는 남기지 않는다. 종료코드: 0 승인 · 1 게이트 불통과 · **2 미검정**.

CLI: `python -m sdkb_paper.validate.t_gate [--split dev] [--graph PATH] [--baseline g0]`
     `python -m sdkb_paper.validate.t_gate --mode resource --old-runset O --new-runset O_prime
      --system P1 --split test`
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
              l0_l3: bool = True, k: int = 100, skip_leakage: bool = False,
              mode: str = "system", old_runset: str | None = None,
              new_runset: str | None = None, system: str = "P1") -> dict:
    """T1·T2·T3(+누출 감사)를 돌려 종합 판정 dict 를 만든다.

    `mode="resource"` 면 적격심사를 먼저 통과해야 한다 — 실패하면 T1·T2 를 돌리지 않는다.
    """
    out: dict = {"mode": mode, "split": split, "k": k,
                 "epsilon": config.T_EPSILON, "delta": config.T_DELTA}

    # 적격심사가 **가장 먼저다** — 검색·평가 모듈을 적재하기 전에 끝낸다. 자격 없는 비교의
    # T1·T2 수치는 아예 만들지 않는다(남으면 언젠가 인용된다).
    mf_old = mf_new = None
    if mode == "resource":
        from . import runset as RS

        if not (old_runset and new_runset):
            raise ValueError("--mode resource 에는 --old-runset 과 --new-runset 이 모두 필요하다")
        mf_old, mf_new = RS.load(old_runset), RS.load(new_runset)
        elig = RS.eligibility(mf_old, mf_new, system)
        out.update({"eligibility": elig, "h2_eligible": elig["eligible"],
                    "verdict": elig["verdict"], "delta_type": elig["delta_type"],
                    "system": system})
        if not elig["eligible"]:
            out.update({"leakage": None, "leakage_pass": None, "t1": None, "t2": None,
                        "t3": None, "l0_l3": l0_l3, "untested": True, "accept": False})
            return out
        split = mf_new["split"]
        out["split"] = split
    else:
        # 시스템 대 시스템 비교는 검색 유용성 비교이지 H2 의 증거가 아니다(CLAUDE.md §0).
        out.update({"h2_eligible": False, "verdict": "system_comparison"})
    out["untested"] = False

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

    if mode == "resource":
        pnew, pold = RS.run_file(mf_new, system), RS.run_file(mf_old, system)
    else:
        pnew = new or run_path("P1", split)
        pold = old or run_path("B3_rrf", split)

    leak = None if skip_leakage else run_audit(split, k)
    out["leakage"] = leak

    qrel = _split_qrel(split)
    fam = load_family_map()
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

    from .runset import format_eligibility

    mode = res.get("mode", "system")
    lines = [f"═══ T-gate 종합 판정 (mode={mode} · split={res['split']} · "
             f"ε={res['epsilon']} · δ={res['delta']})"]
    if mode == "resource":
        lines += [format_eligibility(res["eligibility"]), ""]
        if res.get("untested"):
            lines += [f"  ⇒ H2 미검정 ({res['verdict']}) — T1·T2 를 돌리지 않았다.",
                      "     자격 없는 비교로 '지지'를 만들지 않는다(CLAUDE.md §1-2).",
                      "  ⇒ Accept(ΔG) = 0  미검정"]
            return "\n".join(lines)
    lines += [f"  run: new={res['runs']['new']}  old={res['runs']['old']}", ""]
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
    ap.add_argument("--split", choices=["train", "dev", "test", "test_b", "all"], default="dev")
    ap.add_argument("--mode", choices=["system", "resource"], default="system",
                    help="system=시스템 대 시스템(기본) · resource=O 대 O′(H2 는 이쪽만)")
    ap.add_argument("--old-runset", default=None, help="resource 모드의 구 자원 run 세트 라벨")
    ap.add_argument("--new-runset", default=None, help="resource 모드의 신 자원 run 세트 라벨")
    ap.add_argument("--system", default="P1", help="resource 모드에서 비교할 단일 시스템")
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
    if args.split == "test_b":
        # T2 하위집단 판정은 A층 전용이다(PLAN-045 D5 · PLAN-047 §13.4). B층에는 공정군·
        # 거절근거 라벨의 원천이 없고, 그 상태로 δ 를 적용하면 사전등록이 정한 것과 **다른
        # 표본으로 같은 이름의 판정**을 내게 된다. 선택지로 받아 두고 **여기서 거부**하는
        # 이유는, 조용히 빠지는 것보다 시끄럽게 막히는 편이 안전하기 때문이다.
        raise SystemExit(
            "[t-gate] split=test_b 는 T-gate 대상이 아니다 — T1·T2 는 A층 판정 전용이다"
            "(PLAN-047 §13.4). 판독 B 는 results_table/ablation 으로 판정한다."
        )

    res = run_tgate(args.split, args.new, args.old, args.graph, args.baseline,
                    l0_l3=(args.l0_l3 == "pass"), k=args.k, skip_leakage=args.skip_leakage,
                    mode=args.mode, old_runset=args.old_runset, new_runset=args.new_runset,
                    system=args.system)
    print(format_report(res))
    out = args.out or config.TGATE_REPORT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"✓ {out}")
    # 0 승인 · 1 게이트 불통과 · 2 미검정. "떨어졌다"와 "재보지도 못했다"는 다른 문장이다.
    sys.exit(0 if res["accept"] else (2 if res.get("untested") else 1))


if __name__ == "__main__":
    main()
