"""T3 — 교차 태스크 CQ 비회귀 게이트 (PLAN-018 §5.1 · PLAN-019 W3 · 원고 §4.9·§6.6·§10).

`1[∀f∈{em,tf,core}: PassRate_f(new) ≥ PassRate_f(old)]`.

**이것은 통계 검정이 아니다.** CQ 는 명세이고, 명세는 확률적으로 통과하지 않는다. 그래서 T3 는
결정론적 통과율 비교이며 하락은 곧 실패다 — 표본 부족·유의성 같은 완충재가 없다. 예외는 커밋
메시지의 명시적 waiver 토큰(`config.T3_WAIVER_TOKEN`)뿐이고, 그 **횟수는 로그에 남아 표 6.6에
보고된다**(면제가 조용해지면 게이트는 장식이 된다).

주 태스크(pa)는 T3 의 분모가 아니다 — 선행기술 검색의 회귀는 T1 이 통계적으로 담당한다. T3 가
지키는 것은 "다른 뷰가 조용히 부서지지 않았는가"다(원고 §7.6 태스크 결합 발견이 근거).

**세대 아티팩트.** 기준값은 `data/cq_generations/<label>.json` 에 얼린다(집계·해시만 → 커밋 가능).
`--freeze <label>` 로 현재 그래프의 통과율을 세대로 기록하고, 이후 델타는 그 세대와 비교한다.
누적된 세대 파일이 곧 표 6.6(세대별 CQ 통과율 추이)의 원천이다.

CLI:
  python -m sdkb_paper.validate.t3_cross_task_cq <graph.ttl> --freeze g0     # 세대 동결
  python -m sdkb_paper.validate.t3_cross_task_cq <graph.ttl> --baseline g0   # 비회귀 판정
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from .. import config
from .cq_runner import run_cqs, suite_pass_rates


def compare_rates(new: dict[str, dict], old: dict[str, dict],
                  suites: tuple[str, ...] = config.T3_SUITES) -> dict:
    """스위트별 (old→new) 비교. 하나라도 하락하면 regressed.

    스위트가 새 쪽에 아예 없으면(=CQ 가 사라졌으면) 통과율 0 으로 본다 — CQ 삭제로 게이트를
    통과하는 우회로를 막는다.
    """
    rows, regressed = [], []
    for f in suites:
        o = old.get(f, {}).get("rate", 0.0)
        n = new.get(f, {"rate": 0.0, "n_pass": 0, "n_total": 0})
        rate_new = n.get("rate", 0.0)
        drop = o - rate_new
        row = {"suite": f, "rate_old": o, "rate_new": rate_new, "drop": drop,
               "n_pass_new": n.get("n_pass", 0), "n_total_new": n.get("n_total", 0),
               "n_total_old": old.get(f, {}).get("n_total", 0),
               "regressed": rate_new < o}
        rows.append(row)
        if row["regressed"]:
            regressed.append(f)
    return {"rows": rows, "regressed": regressed}


def commit_waiver(message: str | None = None) -> str | None:
    """커밋 메시지에서 waiver 토큰 뒤의 사유를 뽑는다. 없으면 None."""
    if message is None:
        try:
            message = subprocess.run(["git", "log", "-1", "--format=%B"], cwd=config.ROOT,
                                     capture_output=True, text=True, check=True).stdout
        except (OSError, subprocess.CalledProcessError):
            return None
    tok = config.T3_WAIVER_TOKEN
    if tok not in message:
        return None
    return message.split(tok, 1)[1].strip().splitlines()[0].strip() or "(사유 미기재)"


def t3_gate(new_rates: dict[str, dict], old_rates: dict[str, dict],
            suites: tuple[str, ...] = config.T3_SUITES,
            waiver: str | None = None) -> dict:
    """T3 판정. waiver 가 있으면 하락에도 통과시키되 waived=True 로 남긴다."""
    cmp = compare_rates(new_rates, old_rates, suites)
    regressed = bool(cmp["regressed"])
    return {"gate": "T3", "suites": suites, "rows": cmp["rows"],
            "regressed": cmp["regressed"], "waived": bool(regressed and waiver),
            "waiver_reason": waiver if regressed else None,
            "pass": (not regressed) or bool(waiver)}


def generation_path(label: str) -> Path:
    return config.CQ_GEN_DIR / f"cq_{label}.json"


def freeze_generation(graph_path: Path, label: str) -> dict:
    """현재 그래프의 스위트별 통과율을 세대 아티팩트로 얼린다(표 6.6 축적)."""
    from .leakage_check import sha256_file

    results = run_cqs(graph_path)
    gpath = Path(graph_path).resolve()
    rel = gpath.relative_to(config.ROOT) if gpath.is_relative_to(config.ROOT) else gpath
    rec = {"generation": label, "graph": str(rel),
           "graph_sha256": sha256_file(graph_path),
           "n_cq": len(results), "suites": suite_pass_rates(results),
           "per_cq": {r.name: {"suite": r.suite, "rows": r.rows,
                               "expect_min": r.expect_min, "passed": r.passed}
                      for r in results}}
    config.CQ_GEN_DIR.mkdir(parents=True, exist_ok=True)
    generation_path(label).write_text(json.dumps(rec, ensure_ascii=False, indent=2),
                                      encoding="utf-8")
    return rec


def load_generation(label: str) -> dict:
    p = generation_path(label)
    if not p.exists():
        raise FileNotFoundError(
            f"세대 아티팩트 없음: {p} — 먼저 `--freeze {label}` 로 기준 세대를 동결하라")
    return json.loads(p.read_text(encoding="utf-8"))


def log_waiver(rec: dict) -> None:
    """waiver 사용 이력 append (횟수를 논문 표 6.6 에 보고하기 위한 원장)."""
    config.CQ_GEN_DIR.mkdir(parents=True, exist_ok=True)
    with config.T3_WAIVER_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def waiver_count() -> int:
    if not config.T3_WAIVER_LOG.exists():
        return 0
    return sum(1 for line in config.T3_WAIVER_LOG.read_text(encoding="utf-8").splitlines()
               if line.strip())


def format_report(r: dict) -> str:
    lines = [f"[T3 교차 태스크 CQ 비회귀] 스위트 {', '.join(r['suites'])} "
             "(주 태스크 pa 는 T1 담당 — 분모 아님)",
             f"    {'스위트':<8}{'구':>10}{'신':>10}{'하락':>10}"]
    for row in r["rows"]:
        flag = "  ❌ 회귀" if row["regressed"] else ""
        lines.append(f"    {row['suite']:<8}{row['rate_old']:>10.3f}{row['rate_new']:>10.3f}"
                     f"{row['drop']:>+10.3f}{flag}"
                     f"   ({row['n_pass_new']}/{row['n_total_new']})")
    if r["waived"]:
        lines.append(f"  ⚠ waiver 적용 — 사유: {r['waiver_reason']} "
                     f"(누적 {waiver_count()}회 · 표 6.6 보고 대상)")
    lines.append(f"  판정: {'PASS (비회귀)' if r['pass'] else 'FAIL (타 태스크 CQ 하락)'}")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("graph", type=Path, help="판정 대상 그래프 TTL")
    ap.add_argument("--freeze", metavar="LABEL", default=None,
                    help="현재 통과율을 세대 아티팩트로 동결(판정하지 않는다)")
    ap.add_argument("--baseline", metavar="LABEL", default=None,
                    help="비교 기준 세대 라벨(기본 g0)")
    args = ap.parse_args()

    if args.freeze:
        rec = freeze_generation(args.graph, args.freeze)
        print(f"[T3] 세대 '{args.freeze}' 동결 → {generation_path(args.freeze)}")
        for f, s in sorted(rec["suites"].items()):
            print(f"  · {f:<5} {s['rate']:.3f} ({s['n_pass']}/{s['n_total']})")
        return

    old = load_generation(args.baseline or "g0")
    new_rates = suite_pass_rates(run_cqs(args.graph))
    waiver = commit_waiver()
    r = t3_gate(new_rates, old["suites"], waiver=waiver)
    print(f"[T3] new={args.graph.name}  old=세대 '{old['generation']}'")
    print(format_report(r))
    if r["waived"]:
        log_waiver({"generation_old": old["generation"], "graph": str(args.graph),
                    "regressed": r["regressed"], "reason": r["waiver_reason"]})
    sys.exit(0 if r["pass"] else 1)


if __name__ == "__main__":
    main()
