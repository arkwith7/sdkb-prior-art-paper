"""Competency Question 러너.

queries/cq/*.rq 를 전부 실행해 통과율을 리포트한다.
각 .rq 파일 첫 줄들의 주석 메타데이터를 해석한다:
    # desc: <자연어 질문>
    # expect-min: <최소 결과 행 수, 기본 1>

CLI:  python -m sdkb_paper.validate.cq_runner <graph.ttl> [--report] [--min-pass 1.0]
      통과율 < min-pass 이면 exit code 1 (CI 게이트)
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from rdflib import Graph

from sdkb_paper.config import QUERIES_CQ, ROOT


@dataclass
class CQResult:
    name: str
    desc: str
    expect_min: int
    rows: int

    @property
    def passed(self) -> bool:
        return self.rows >= self.expect_min


def _parse_meta(rq_text: str) -> tuple[str, int]:
    desc, expect_min = "", 1
    for line in rq_text.splitlines():
        line = line.strip()
        if line.startswith("# desc:"):
            desc = line.removeprefix("# desc:").strip()
        elif line.startswith("# expect-min:"):
            expect_min = int(line.removeprefix("# expect-min:").strip())
        elif line and not line.startswith("#"):
            break
    return desc, expect_min


def run_cqs(graph_path: Path, cq_dir: Path = QUERIES_CQ) -> list[CQResult]:
    g = Graph().parse(graph_path)
    results = []
    for rq in sorted(cq_dir.glob("*.rq")):
        text = rq.read_text(encoding="utf-8")
        desc, expect_min = _parse_meta(text)
        rows = len(list(g.query(text)))
        results.append(CQResult(rq.stem, desc, expect_min, rows))
    return results


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

    lines = ["| CQ | 질문 | 결과행 | 기준 | 통과 |", "|---|---|---:|---:|:--:|"]
    for r in results:
        lines.append(f"| {r.name} | {r.desc} | {r.rows} | ≥{r.expect_min} | {'✅' if r.passed else '❌'} |")
    n_pass = sum(r.passed for r in results)
    rate = n_pass / len(results)
    table = "\n".join(lines)
    print(f"[cq_runner] graph = {args.graph}")
    print(table)
    print(f"\n[cq_runner] pass rate = {rate:.0%} ({n_pass}/{len(results)})")

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
