#!/usr/bin/env python3
"""trace_query.py — 통제된 자원 교체(EP3 · §5.2)를 '한 질의' 위에서 읽는 실측 추적표.

두 실행(O = 교정 전 · O′ = 교정 후)의 순위 파일과 봉인 qrel 을 읽어, 질의 하나에 대하여
정답(심사관 인용) 문헌이 각 시스템에서 몇 위에 있었는지를 표로 낸다. 표 4 의 질의 평균
(−0.0293)이 개별 질의에서 어떤 모습인지 보이는 것이 목적이며, **새 판정을 만들지 않는다**
(탐색적 기술통계 · 확증 판정과 무관 · S9 이관 후보).

입력 형식
  --run     TREC run: `qid Q0 docid rank score tag` (공백 구분). 시스템마다 하나씩 `이름=경로`.
  --qrel    TREC qrels: `qid 0 docid rel` (또는 `qid docid rel`). rel>0 만 정답으로 본다.
  --family  (선택) `docid,family_id` CSV. 있으면 family 단위로 계수한다(§3.3 · 주 결론의 단위).
  --pick    질의 선택 규칙. `drop`(P1 에서 O→O′ 순위가 가장 많이 밀린 질의 · 기본) ·
            `gain`(가장 많이 오른 질의) · `qid:<id>`(직접 지정).

예
  uv run python scripts/trace_query.py \
      --run O:P1=runs/O/sys_P1_test.txt --run Oprime:P1=runs/Oprime/sys_P1_test.txt \
      --run O:B5=runs/O/sys_B5_concept_test.txt --run Oprime:B5=runs/Oprime/sys_B5_concept_test.txt \
      --run O:B3=runs/O/sys_B3_rrf_test.txt \
      --qrel data/processed/ir/qrels_dev.txt --family data/processed/ir/family_map.csv \
      --pick drop --k 100 --md

출력(--md): | 시스템 | 조건 | 정답 문헌(패밀리) 순위 | R@100(이 질의) | 로 된 표 한 장.
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path


def read_run(path: Path) -> dict[str, list[str]]:
    """qid → docid 목록(순위 순)."""
    ranked: dict[str, list[tuple[int, str]]] = defaultdict(list)
    with path.open(encoding="utf-8") as fh:
        for ln in fh:
            parts = ln.split()
            if len(parts) < 4:
                continue
            qid, docid = parts[0], parts[2]
            try:
                rank = int(parts[3])
            except ValueError:
                rank = len(ranked[qid]) + 1
            ranked[qid].append((rank, docid))
    return {q: [d for _, d in sorted(v)] for q, v in ranked.items()}


# 봉인 qrel 을 **파일 경로로 직접 여는 것**을 막는다 (CLAUDE.md §0.8 SEAL · PLAN-068 트랙 C).
# 봉인 분할의 접근은 `analysis.metrics.load_qrel_for_split` 를 지나야 열람 원장에 한 줄이 남는다.
# 이 스크립트가 봉인 파일을 직접 읽으면 원장에 기록되지 않은 접근이 생기고, 그것은 "판독 B 봉인에
# 대한 모든 접근을 열람 원장에 기록했다"는 허용 문구를 거짓으로 만든다.
SEALED_HINT = ("sealed", "봉인")


def _refuse_if_sealed(path: Path) -> None:
    name = str(path).lower()
    if any(h in name for h in SEALED_HINT):
        sys.exit(
            f"봉인 qrel 을 직접 열지 않는다: {path}\n"
            "  봉인 분할의 접근은 `sdkb_paper.analysis.metrics.load_qrel_for_split` 를 지나야\n"
            "  열람 원장(data/processed/ir/seal_access.jsonl)에 기록된다 (CLAUDE.md §0.8 SEAL).\n"
            "  이 스크립트는 탐색적 도구이므로 개봉된 사본이나 개발 분할 qrel 을 준다."
        )


def read_qrel(path: Path) -> dict[str, set[str]]:
    _refuse_if_sealed(path)
    rel: dict[str, set[str]] = defaultdict(set)
    with path.open(encoding="utf-8") as fh:
        for ln in fh:
            parts = ln.split()
            if len(parts) == 4:
                qid, docid, grade = parts[0], parts[2], parts[3]
            elif len(parts) == 3:
                qid, docid, grade = parts
            else:
                continue
            try:
                if float(grade) > 0:
                    rel[qid].add(docid)
            except ValueError:
                continue
    return rel


def read_family(path: Path | None) -> dict[str, str]:
    if not path:
        return {}
    fam: dict[str, str] = {}
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.reader(fh):
            if len(row) >= 2 and row[0] != "docid":
                fam[row[0]] = row[1]
    return fam


def fam_of(docid: str, fam: dict[str, str]) -> str:
    return fam.get(docid, docid)


def positions(ranked: list[str], rels: set[str], fam: dict[str, str]) -> dict[str, int | None]:
    """정답 패밀리별 최초 등장 순위(1-based) · 없으면 None."""
    want = {fam_of(d, fam) for d in rels}
    seen: dict[str, int | None] = {f: None for f in want}
    fam_rank = 0
    seen_fams: set[str] = set()
    for d in ranked:
        f = fam_of(d, fam)
        if f in seen_fams:
            continue
        seen_fams.add(f)
        fam_rank += 1
        if f in seen and seen[f] is None:
            seen[f] = fam_rank
    return seen


def recall_at_k(pos: dict[str, int | None], k: int) -> float:
    if not pos:
        return float("nan")
    return sum(1 for p in pos.values() if p is not None and p <= k) / len(pos)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", action="append", required=True,
                    help="`조건:시스템=경로` (예: O:P1=runs/O/sys_P1_test.txt). 여러 번 지정.")
    ap.add_argument("--qrel", required=True, type=Path)
    ap.add_argument("--family", type=Path)
    ap.add_argument("--pick", default="drop")
    ap.add_argument("--k", type=int, default=100)
    ap.add_argument("--md", action="store_true")
    ns = ap.parse_args()

    runs: dict[tuple[str, str], dict[str, list[str]]] = {}
    for spec in ns.run:
        try:
            cond_sys, path = spec.split("=", 1)
            cond, system = cond_sys.split(":", 1)
        except ValueError:
            sys.exit(f"--run 형식 오류: {spec}")
        runs[(cond, system)] = read_run(Path(path))
    qrel = read_qrel(ns.qrel)
    fam = read_family(ns.family)

    # 질의 선택 — P1 의 O / O′ 가 둘 다 있어야 drop/gain 규칙을 쓸 수 있다.
    if ns.pick.startswith("qid:"):
        qid = ns.pick[4:]
    else:
        need = [("O", "P1"), ("Oprime", "P1")]
        if not all(n in runs for n in need):
            sys.exit("drop/gain 규칙에는 O:P1 과 Oprime:P1 실행이 모두 필요하다 (또는 --pick qid:<id>).")
        deltas = []
        for q, rels in qrel.items():
            if q not in runs[need[0]] or q not in runs[need[1]]:
                continue
            r0 = recall_at_k(positions(runs[need[0]][q], rels, fam), ns.k)
            r1 = recall_at_k(positions(runs[need[1]][q], rels, fam), ns.k)
            deltas.append((r1 - r0, q))
        if not deltas:
            sys.exit("qrel 과 실행 파일에 공통 질의가 없다.")
        deltas.sort()
        qid = deltas[0][1] if ns.pick == "drop" else deltas[-1][1]

    rels = qrel.get(qid, set())
    if not rels:
        sys.exit(f"질의 {qid} 의 qrel 이 없다.")

    rows = []
    for (cond, system), run in sorted(runs.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        ranked = run.get(qid, [])
        pos = positions(ranked, rels, fam)
        pos_txt = " · ".join(f"{f}: {f'{p}위' if p else f'{ns.k}위 밖'}" for f, p in sorted(pos.items()))
        rows.append((system, cond, pos_txt, recall_at_k(pos, ns.k)))

    if ns.md:
        print(f"**질의 {qid}** — 정답 패밀리 {len({fam_of(d, fam) for d in rels})}개 · 검토 깊이 K={ns.k} "
              f"(선택 규칙: `{ns.pick}` · 탐색적 기술 · 판정과 무관).\n")
        print(f"| 시스템 | 조건 | 정답 문헌의 순위 | R@{ns.k} (이 질의) |")
        print("|---|---|---|---:|")
        for s, c, p, r in rows:
            print(f"| {s} | {c} | {p} | {r:.2f} |")
    else:
        print(f"qid={qid} rels={len(rels)} K={ns.k}")
        for s, c, p, r in rows:
            print(f"  {s:<4} {c:<7} R@{ns.k}={r:.2f}  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
