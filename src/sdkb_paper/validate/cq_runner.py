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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("graph", type=Path)
    ap.add_argument("--report", action="store_true", help="markdown 리포트 파일 생성")
    ap.add_argument("--min-pass", type=float, default=1.0, help="요구 통과율 (0~1)")
    args = ap.parse_args()

    results = run_cqs(args.graph)
    if not results:
        print("[cq_runner] no CQ files found")
        sys.exit(2)

    lines = ["| CQ | 질문 | 결과행 | 기준 | 통과 |", "|---|---|---:|---:|:--:|"]
    for r in results:
        lines.append(f"| {r.name} | {r.desc} | {r.rows} | ≥{r.expect_min} | {'✅' if r.passed else '❌'} |")
    rate = sum(r.passed for r in results) / len(results)
    table = "\n".join(lines)
    print(table)
    print(f"\n[cq_runner] pass rate = {rate:.0%} ({sum(r.passed for r in results)}/{len(results)})")

    if args.report:
        out = ROOT / "paper" / "figures" / "cq_report.md"
        out.write_text(table + f"\n\npass rate: {rate:.0%}\n", encoding="utf-8")
        print(f"[cq_runner] report -> {out}")

    sys.exit(0 if rate >= args.min_pass else 1)


if __name__ == "__main__":
    main()
