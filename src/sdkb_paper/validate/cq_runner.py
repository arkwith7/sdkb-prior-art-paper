"""Competency Question 러너.

queries/cq/*.rq 를 전부 실행해 통과율을 리포트한다.
각 .rq 파일 첫 줄들의 주석 메타데이터를 해석한다:
    # desc: <자연어 질문>
    # suite: <pa|em|tf|core — 태스크 스위트, T3 의 분모 · PLAN-019 §3.2 동결>
    # expect-min: <최소 결과 행 수, 기본 1>

**스위트는 T3(교차 태스크 CQ 비회귀)의 전제다.** 어떤 CQ 가 어느 태스크의 명세인지 파일 안에
적어 두어야 "타 태스크 통과율이 떨어졌는가"를 물을 수 있다(원고 §4.9). 라벨 없는 파일은 `core`
로 떨어지지 않고 **에러**다 — 조용히 분모가 바뀌면 게이트가 공허해진다.

CLI:  python -m sdkb_paper.validate.cq_runner <graph.ttl> [--report] [--min-pass 1.0]
      통과율 < min-pass 이면 exit code 1 (CI 게이트)
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from rdflib import Graph

from sdkb_paper.config import CQ_SUITES, QUERIES_CQ, ROOT


@dataclass
class CQResult:
    name: str
    desc: str
    expect_min: int
    rows: int
    suite: str = "core"

    @property
    def passed(self) -> bool:
        return self.rows >= self.expect_min


def _parse_meta(rq_text: str) -> tuple[str, int, str]:
    """(desc, expect_min, suite). suite 미기재·미지정값은 ValueError(조용한 기본값 금지)."""
    desc, expect_min, suite = "", 1, ""
    for line in rq_text.splitlines():
        line = line.strip()
        if line.startswith("# desc:"):
            desc = line.removeprefix("# desc:").strip()
        elif line.startswith("# expect-min:"):
            expect_min = int(line.removeprefix("# expect-min:").strip())
        elif line.startswith("# suite:"):
            suite = line.removeprefix("# suite:").strip()
        elif line and not line.startswith("#"):
            break
    if suite not in CQ_SUITES:
        raise ValueError(f"CQ 스위트 라벨이 없거나 잘못됐다: '{suite}' (허용 {CQ_SUITES})")
    return desc, expect_min, suite


def run_cqs(graph_path: Path, cq_dir: Path = QUERIES_CQ) -> list[CQResult]:
    g = Graph().parse(graph_path)
    results = []
    for rq in sorted(cq_dir.glob("*.rq")):
        text = rq.read_text(encoding="utf-8")
        desc, expect_min, suite = _parse_meta(text)
        rows = len(list(g.query(text)))
        results.append(CQResult(rq.stem, desc, expect_min, rows, suite))
    return results


def suite_pass_rates(results: list[CQResult]) -> dict[str, dict]:
    """스위트별 {n_pass, n_total, rate} — T3 의 입력. 결정론적 집계이며 검정이 아니다."""
    out: dict[str, dict] = {}
    for r in results:
        rec = out.setdefault(r.suite, {"n_pass": 0, "n_total": 0})
        rec["n_total"] += 1
        rec["n_pass"] += int(r.passed)
    for rec in out.values():
        rec["rate"] = rec["n_pass"] / rec["n_total"] if rec["n_total"] else 0.0
    return out


def report_path(graph_path: Path) -> Path:
    """그래프별 리포트 경로. G₀ 와 G₁ 의 리포트가 서로 덮어쓰지 않아야 논문 §4.2 의
    '보강 전후 CQ 응답률 비교표'를 만들 수 있다."""
    return ROOT / "paper" / "figures" / f"cq_report_{graph_path.stem}.md"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("graph", type=Path)
    ap.add_argument("--report", action="store_true", help="markdown 리포트 파일 생성")
    ap.add_argument("--out", type=Path, default=None, help="리포트 경로 (기본: cq_report_<graph>.md)")
    ap.add_argument(
        "--min-pass", type=float, default=1.0,
        help="요구 통과율 (0~1). baseline(graph_v0)처럼 특허 0건인 그래프는 "
             "CQ01/CQ02 가 응답 불가인 것이 정상이므로 0 으로 두고 '측정'으로 쓴다.",
    )
    args = ap.parse_args()

    results = run_cqs(args.graph)
    if not results:
        print("[cq_runner] no CQ files found")
        sys.exit(2)

    lines = ["| CQ | 스위트 | 질문 | 결과행 | 기준 | 통과 |", "|---|---|---|---:|---:|:--:|"]
    for r in results:
        lines.append(f"| {r.name} | {r.suite} | {r.desc} | {r.rows} | ≥{r.expect_min} | "
                     f"{'✅' if r.passed else '❌'} |")
    n_pass = sum(r.passed for r in results)
    rate = n_pass / len(results)
    table = "\n".join(lines)
    print(f"[cq_runner] graph = {args.graph}")
    print(table)
    print(f"\n[cq_runner] pass rate = {rate:.0%} ({n_pass}/{len(results)})")
    for suite, rec in sorted(suite_pass_rates(results).items()):
        print(f"  · {suite:<5} {rec['rate']:.0%} ({rec['n_pass']}/{rec['n_total']})")

    if args.report:
        out = args.out or report_path(args.graph)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            f"# CQ 응답률 — `{args.graph}`\n\n{table}\n\npass rate: {rate:.0%} ({n_pass}/{len(results)})\n",
            encoding="utf-8",
        )
        print(f"[cq_runner] report -> {out}")

    sys.exit(0 if rate >= args.min_pass else 1)


if __name__ == "__main__":
    main()
