"""Competency Question 러너.

queries/cq/*.rq 를 전부 실행해 통과율을 리포트한다.
각 .rq 파일 첫 줄들의 주석 메타데이터를 해석한다:
    # desc: <자연어 질문>
    # suite: <pa|em|tf|core — 태스크 스위트, T3 의 분모 · PLAN-019 §3.2 동결>
    # expect-min: <최소 결과 행 수, 기본 1>

**스위트는 T3(교차 태스크 CQ 비회귀)의 전제다.** 어떤 CQ 가 어느 태스크의 명세인지 파일 안에
적어 두어야 "타 태스크 통과율이 떨어졌는가"를 물을 수 있다(원고 §4.9). 라벨 없는 파일은 `core`
로 떨어지지 않고 **에러**다 — 조용히 분모가 바뀌면 게이트가 공허해진다.

**엔진(PLAN-020 W4-0).** 기본은 `oxigraph` 다 — rdflib 인메모리는 graph_v0(23MB)에서 150초가 걸려
결함주입 108 인스턴스를 감당하지 못한다. 두 엔진은 `--verify-engines` 로 CQ 28개 전량 결과행이
동일함을 확인한 뒤에만 교체됐다(불일치 1건이라도 나오면 게이트 판정이 엔진에 의존한다는 뜻이므로
전환하지 않는다). `--engine rdflib` 로 언제든 되돌릴 수 있다.

CLI:  python -m sdkb_paper.validate.cq_runner <graph.ttl> [--report] [--min-pass 1.0]
      python -m sdkb_paper.validate.cq_runner <graph.ttl> --verify-engines
      통과율 < min-pass 이면 exit code 1 (CI 게이트)
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from sdkb_paper.config import CQ_SUITES, QUERIES_CQ, ROOT

ENGINES = ("oxigraph", "rdflib")
DEFAULT_ENGINE = "oxigraph"


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


def _count_rdflib(graph_path: Path, texts: list[str]) -> list[int]:
    from rdflib import Graph

    g = Graph().parse(graph_path)
    return [len(list(g.query(t))) for t in texts]


def _count_oxigraph(graph_path: Path, texts: list[str]) -> list[int]:
    """pyoxigraph 온디스크 스토어로 같은 질의를 센다 (rdflib 대비 ~10배 빠름).

    대용량 그래프에서 인메모리는 메모리를 폭주시킨다(메모리 `central-axis-use-oxigraph-ondisk`)
    — 임시 디렉터리 스토어에 적재하고 종료 시 버린다. **기본 그래프에 적재**하므로 CQ 의
    `?s ?p ?o` 패턴 의미가 rdflib 과 같다.
    """
    from pyoxigraph import RdfFormat, Store

    with tempfile.TemporaryDirectory() as tmp:
        store = Store(path=str(Path(tmp) / "cq"))
        with open(graph_path, "rb") as fh:
            store.bulk_load(fh, format=RdfFormat.TURTLE)
        return [sum(1 for _ in store.query(t)) for t in texts]


def run_cqs(graph_path: Path, cq_dir: Path = QUERIES_CQ,
            engine: str = DEFAULT_ENGINE) -> list[CQResult]:
    if engine not in ENGINES:
        raise ValueError(f"알 수 없는 CQ 엔진: '{engine}' (허용 {ENGINES})")
    rqs = sorted(cq_dir.glob("*.rq"))
    texts = [rq.read_text(encoding="utf-8") for rq in rqs]
    metas = [_parse_meta(t) for t in texts]
    counts = (_count_oxigraph if engine == "oxigraph" else _count_rdflib)(graph_path, texts)
    return [CQResult(rq.stem, desc, expect_min, rows, suite)
            for rq, (desc, expect_min, suite), rows in zip(rqs, metas, counts)]


def verify_engines(graph_path: Path, cq_dir: Path = QUERIES_CQ) -> list[dict]:
    """두 엔진의 CQ 별 결과행을 대조한다. 불일치가 있으면 엔진 전환은 무효다."""
    rqs = sorted(cq_dir.glob("*.rq"))
    texts = [rq.read_text(encoding="utf-8") for rq in rqs]
    ox = _count_oxigraph(graph_path, texts)
    rd = _count_rdflib(graph_path, texts)
    return [{"cq": rq.stem, "oxigraph": o, "rdflib": r, "same": o == r}
            for rq, o, r in zip(rqs, ox, rd)]


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
    ap.add_argument("--engine", choices=ENGINES, default=DEFAULT_ENGINE,
                    help="SPARQL 엔진. 기본 oxigraph — rdflib 은 되돌림용/대조용")
    ap.add_argument("--verify-engines", action="store_true",
                    help="두 엔진 결과행 대조(전환 근거). 불일치 1건이라도 있으면 exit 1")
    args = ap.parse_args()

    if args.verify_engines:
        rows = verify_engines(args.graph)
        bad = [r for r in rows if not r["same"]]
        print(f"[cq_runner] 엔진 대조 · graph = {args.graph}  ({len(rows)} CQ)")
        for r in rows:
            mark = "✅" if r["same"] else "❌"
            print(f"  {mark} {r['cq']:<40} oxigraph={r['oxigraph']:<8} rdflib={r['rdflib']}")
        print(f"\n[cq_runner] 불일치 {len(bad)}건")
        sys.exit(0 if not bad else 1)

    results = run_cqs(args.graph, engine=args.engine)
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
