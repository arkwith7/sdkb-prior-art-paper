#!/usr/bin/env python3
"""example_delta_demo.py — 관통 예시(running example)를 '실행되는 예시'로 만드는 데모.

data/samples/mini_graph.ttl(예시 그래프 G_ex)에 queries/cq/*.rq 전량을 실행하여 기준 행 수를 얻고,
예시 델타(Δ_ex)를 적용한 뒤 다시 실행하여 CQ 별 행 수 변화를 v2 판정(존재검사 ∧ 극성별 분포검사)으로
읽는다. 목적은 §3–§5 의 관통 예시 문장이 손으로 쓴 가정이 아니라 실제 실행 결과에서 나오게 하는 것이다.

    uv run python scripts/example_delta_demo.py                       # 기본 델타 전량 비교
    uv run python scripts/example_delta_demo.py --delta merge_etch_into_plasma --md > paper/tables/example_delta_a.md
    uv run python scripts/example_delta_demo.py --dump data/samples    # mini_graph_delta_{a,b}.ttl → make example-gate

판정 규칙은 §3.5 의 v2 와 같다: pass_v2(i) = [rows_i >= expect-min_i] ∧ ¬regress_i,
regress_i = rows_i < (1-τ)·base_i (up) / rows_i > (1+τ)·base_i (down). τ 는 §3.5 의 0.05 이다.
사이드카 질의(CQ29–31)는 §3.4 표 3 과 같이 게이트 분모에서 제외하고 참고로만 표시한다.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    from rdflib import Graph, URIRef
except ImportError:  # pragma: no cover
    sys.exit("rdflib 가 필요하다: uv add rdflib")

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "data" / "samples" / "mini_graph.ttl"
CQ_DIR = ROOT / "queries" / "cq"
DATA = "https://w3id.org/sdkb/data/"
SIDECAR = {"CQ29", "CQ30", "CQ31"}
TAU = 0.05

# ─────────────────────────────────────────────────────────────────────────────
# 예시 델타 — 이름 → (설명, 적용 함수). 세 개 모두 S2 의 결함군에 대응하는 '축소판'이다.
# ─────────────────────────────────────────────────────────────────────────────

def _merge_iri(g: Graph, victim: str, survivor: str) -> int:
    """victim IRI 의 모든 출현을 survivor 로 바꾼다 (동의어 오병합 · S2 F11 의 축소판).
    RDF 는 집합이므로 중복 트리플은 저절로 하나로 접힌다 — 이것이 회수는 올리고 변별은 낮추는 이유다."""
    v, s = URIRef(victim), URIRef(survivor)
    changed = 0
    for spo in list(g.triples((v, None, None))):
        g.remove(spo)
        g.add((s, spo[1], spo[2]))
        changed += 1
    for spo in list(g.triples((None, None, v))):
        g.remove(spo)
        g.add((spo[0], spo[1], s))
        changed += 1
    # 자기참조 계층(etch hasSubprocess etch)은 병합의 부산물이므로 제거한다.
    for spo in list(g.triples((s, None, s))):
        g.remove(spo)
        changed += 1
    return changed


def _relocate_edge(g: Graph, subj: str, pred: str, old_obj: str, new_obj: str) -> int:
    """간선 하나의 목적어를 바꾼다 (전문가 사례–결함모드 재배치 · S2 F14 의 축소판). 간선 수 보존."""
    t = (URIRef(subj), URIRef(pred), URIRef(old_obj))
    if t not in g:
        return 0
    g.remove(t)
    g.add((URIRef(subj), URIRef(pred), URIRef(new_obj)))
    return 1


DELTAS = {
    "merge_etch_into_plasma": (
        ("동의어 오병합(F11 축소판): 상위 공정 <process/etch> 를 하위 공정 <subprocess/plasma_etch> 로 흡수 — "
         "회수율을 올리려는 '개념 통합' 시나리오"),
        lambda g: _merge_iri(g, DATA + "process/etch", DATA + "subprocess/plasma_etch"),
    ),
    "merge_plasma_into_etch": (
        "동의어 오병합(F11 축소판 · 반대 방향): <subprocess/plasma_etch> 를 <process/etch> 로 흡수",
        lambda g: _merge_iri(g, DATA + "subprocess/plasma_etch", DATA + "process/etch"),
    ),
    "relocate_case_failuremode": (
        ("전문가 사례–결함모드 재배치(F14 축소판): CASE_M01 의 caseFailureMode 를 "
         "micro_trenching → charging 으로 이전 "
         "(charging 은 RootCause 이므로 타입 서명이 어긋나지만 T-Box 에 서로소 공리가 없어 L2 는 침묵한다)"),
        lambda g: _relocate_edge(
            g, DATA + "expert_case/CASE_M01", "https://w3id.org/sdkb/ont/caseFailureMode",
            DATA + "failure_mode/micro_trenching", DATA + "root_cause/charging"),
    ),
}

# 덤프 파일 이름 — 원고·Makefile 이 참조하는 고정 이름 (예시 델타 A / B).
DUMP_STEM = {
    "merge_etch_into_plasma": "mini_graph_delta_a",
    "relocate_case_failuremode": "mini_graph_delta_b",
    "merge_plasma_into_etch": "mini_graph_delta_a_reverse",
}

# 원고가 서술하는 예시 서사 — 회귀 CQ 집합. tests/test_example_delta.py 가 단언한다.
EXPECTED_REGRESSED = {
    "merge_etch_into_plasma": {"CQ21"},
    "relocate_case_failuremode": {"CQ28"},
}

# ─────────────────────────────────────────────────────────────────────────────

HEADER_RE = re.compile(r"^#\s*(desc|suite|monotone|expect-min):\s*(.*)$")


def load_cqs():
    cqs = []
    for p in sorted(CQ_DIR.glob("CQ*.rq")):
        meta = {"desc": "", "suite": "?", "monotone": "up", "expect-min": "1"}
        for line in p.read_text(encoding="utf-8").splitlines():
            m = HEADER_RE.match(line)
            if m:
                meta[m.group(1)] = m.group(2).strip()
        cqs.append((p.stem.split("_")[0], p, meta))
    return cqs


def rows(g: Graph, q: str) -> int:
    return sum(1 for _ in g.query(q))


# ─────────────────────────────────────────────────────────────────────────────
# 저장소 판정식 재현 (--engine repo)
#
# **왜 두 경로인가.** 기본 경로(rdflib)는 사이드카 스토어(1.8 GB · gitignore) 없이 어디서나
# 돌아야 하므로 CQ 를 직접 실행하고 v2 판정을 이 파일에서 계산한다. 그러나 그러면 판정 규칙이
# 저장소와 이 파일 두 곳에 살고, 한쪽이 바뀌면 예시 서사가 조용히 어긋난다.
#
# 그래서 `--engine repo` 는 **측정도 판정도 저장소 코드에 위임한다** —
# `cq_runner.run_cqs`(oxigraph)로 행 수를 얻고 `CQResult.judge(base_rows, tau)` 로 v2 를 적용한다.
# 두 경로의 행 수가 갈리면 그것 자체가 결함이므로 `--engine both` 가 대조한다.
#
# **`cq_runner` 를 단독으로 돌리면 이 회귀가 보이지 않는다.** 그 CLI 는 기준선을 받지 않아
# v1(존재검사)만 적용하기 때문이다 — 델타 A 의 CQ21 2→1 은 존재검사를 통과한다(1 ≥ 1).
# v2 를 실제 게이트 코드로 재현하는 자리가 바로 이 모드이며, `make example-gate` 가 이것을 쓴다.
def _repo_rows(graph_path: Path) -> dict[str, tuple[int, object]]:
    """저장소 엔진으로 CQ 를 실행해 {CQ 번호: (행 수, CQResult)} 를 낸다."""
    try:
        from sdkb_paper.validate.cq_runner import run_cqs
    except ImportError as e:  # pragma: no cover
        sys.exit(f"저장소 모듈을 불러올 수 없다 ({e}) — `uv run python scripts/...` 로 실행하라.")
    out = {}
    for r in run_cqs(graph_path):
        out[r.name.split("_")[0]] = (r.rows, r)
    return out


def judge(rows_after: int, base: int, monotone: str, expect_min: int) -> tuple[bool, str]:
    exists = rows_after >= expect_min
    if monotone == "down":
        regress = rows_after > (1 + TAU) * base
    else:
        regress = rows_after < (1 - TAU) * base
    ok = exists and not regress
    why = "" if ok else ("존재검사 실패" if not exists else "분포검사 실패(회귀)")
    return ok, why


def evaluate(delta_name: str, dump: Path | None = None, engine: str = "rdflib") -> dict:
    """델타를 적용하고 CQ 전량을 전·후로 실행하여 구조화된 결과를 돌려준다 (테스트·표 생성 공용).

    `engine="repo"` 는 행 수와 v2 판정을 저장소 코드(`cq_runner`)에 위임한다 — 사이드카 스토어가
    필요하며 `make example-gate` 가 쓴다. 기본 `"rdflib"` 는 의존성 없이 어디서나 돈다.
    """
    desc, apply = DELTAS[delta_name]
    g0 = Graph().parse(GRAPH, format="turtle")
    g1 = Graph().parse(GRAPH, format="turtle")
    n_changed = apply(g1)
    stem = DUMP_STEM.get(delta_name, "mini_graph_" + delta_name)
    if dump:
        dump.mkdir(parents=True, exist_ok=True)
        g1.serialize(dump / f"{stem}.ttl", format="turtle")

    repo_rows: dict[str, dict] = {}
    if engine == "repo":
        # 저장소 엔진은 파일을 읽으므로 델타 그래프가 디스크에 있어야 한다.
        target = (dump / f"{stem}.ttl") if dump else (GRAPH.parent / f"{stem}.ttl")
        if not target.exists():
            sys.exit(f"저장소 엔진 모드에는 델타 픽스처가 필요하다: {target}\n"
                     f"  먼저 `make example-delta` 또는 `--dump data/samples` 로 생성하라.")
        repo_rows = {"base": _repo_rows(GRAPH), "after": _repo_rows(target)}

    rows_out = []
    fails: dict[str, int] = {"pa": 0, "em": 0, "tf": 0, "core": 0}
    regressed: set[str] = set()
    for cq, path, meta in load_cqs():
        q = path.read_text(encoding="utf-8")
        if engine == "repo":
            b, _ = repo_rows["base"].get(cq, (0, None))
            a, res = repo_rows["after"].get(cq, (0, None))
            # 판정도 저장소 코드가 한다 — 규칙이 두 곳에 살지 않게 한다.
            ok = res.judge(base_rows=b) if res is not None else False
            why = "" if ok else ("존재검사 실패" if res is None or not res.passed
                                 else "분포검사 실패(회귀)")
        else:
            b, a = rows(g0, q), rows(g1, q)
            ok, why = judge(a, b, meta["monotone"], int(meta["expect-min"]))
        gate = "사이드카(분모 제외)" if cq in SIDECAR else ("L3" if meta["suite"] == "pa" else "T3")
        if not ok and cq not in SIDECAR:
            fails[meta["suite"]] = fails.get(meta["suite"], 0) + 1
            regressed.add(cq)
        rows_out.append((cq, meta["suite"], gate, meta["monotone"], b, a, "통과" if ok else f"실패 · {why}"))
    return {"name": delta_name, "desc": desc, "engine": engine,
            "changed": n_changed, "n0": len(g0), "n1": len(g1),
            "rows": rows_out, "fails": fails, "regressed": regressed,
            "l3_pass": fails["pa"] == 0,
            "t3_pass": not (fails["em"] or fails["tf"] or fails["core"])}


def run(delta_name: str, md: bool, dump: Path | None = None, engine: str = "rdflib") -> int:
    r = evaluate(delta_name, dump, engine)
    out, fails = r["rows"], r["fails"]
    if md:
        engine_note = "저장소 엔진·저장소 판정식(oxigraph · `cq_runner.judge`)" if engine == "repo" \
            else "rdflib · 이 스크립트의 v2 구현"
        print(f"**예시 델타 `{delta_name}`** — {r['desc']}. 변경 트리플 {r['changed']}건 · "
              f"트리플 수 {r['n0']} → {r['n1']} · 측정·판정 {engine_note}.\n")
        print("| CQ | 스위트 | 관찰 층 | 극성 | 행 수(전) | 행 수(후) | v2 판정 |")
        print("|---|---|---|---|---:|---:|---|")
        for row in out:
            print("| " + " | ".join(str(x) for x in row) + " |")
        print()
        print(f"**요약** — L3(pa 스위트): {'통과' if r['l3_pass'] else '실패'} · "
              f"T3(em·tf·core 스위트): {'통과' if r['t3_pass'] else '실패'} "
              f"(회귀 CQ 수 em {fails['em']} · tf {fails['tf']} · core {fails['core']}).")
    else:
        print(f"[{delta_name}] ({engine}) {r['desc']}\n"
              f"  changed={r['changed']} triples={r['n0']}->{r['n1']}")
        for row in out:
            flag = "  " if row[6].startswith("통과") else "!!"
            print(f"  {flag} {row[0]:<5} {row[1]:<5} {row[2]:<18} {row[3]:<4} {row[4]:>3} -> {row[5]:>3}  {row[6]}")
        print(f"  L3 fails(pa)={fails['pa']}  T3 fails em={fails['em']} tf={fails['tf']} core={fails['core']}")
    return 0


def render_summary(engine: str = "rdflib") -> str:
    """본문 예시 2용 최소 표 — 회귀 CQ와 층 판정만 생성한다."""
    labels = {
        "merge_etch_into_plasma": "Δ_ex-A · 공정 개념 오병합",
        "relocate_case_failuremode": "Δ_ex-B · 사례–결함모드 재배치",
    }
    lines = [
        "| 합성 델타 | 선행기술조사 L3 | 교차 태스크 T3 | 회귀 CQ(전→후) |",
        "|---|---|---|---|",
    ]
    for name in labels:
        result = evaluate(name, engine=engine)
        changed = [row for row in result["rows"] if row[0] in result["regressed"]]
        detail = " · ".join(f"{row[0]} {row[4]}→{row[5]}행" for row in changed)
        lines.append(
            f"| {labels[name]} | {'통과' if result['l3_pass'] else '실패'} | "
            f"{'통과' if result['t3_pass'] else '미충족'} | {detail} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--delta", choices=sorted(DELTAS), help="하나만 실행 (기본: 전량)")
    ap.add_argument("--md", action="store_true", help="원고에 붙일 Markdown 표로 출력")
    ap.add_argument("--dump", type=Path, metavar="DIR",
                    help="델타 적용 후 그래프를 DIR/mini_graph_<delta>.ttl 로 저장 — 실제 게이트(make gate)에 L0–L3 를 돌리기 위한 입력")
    ap.add_argument("--engine", choices=("rdflib", "repo", "both"), default="rdflib",
                    help="rdflib(기본 · 의존성 없음) | repo(저장소 cq_runner·judge 위임 · 사이드카 필요) | "
                         "both(두 경로의 행 수를 대조 — 갈리면 exit 1)")
    ap.add_argument("--summary-out", type=Path,
                    help="본문용 최소 요약표를 지정 경로에 쓴다(두 권고 델타 고정)")
    ns = ap.parse_args()
    if ns.summary_out:
        ns.summary_out.parent.mkdir(parents=True, exist_ok=True)
        ns.summary_out.write_text(render_summary(ns.engine), encoding="utf-8")
        print(f"wrote {ns.summary_out}")
        return 0
    names = [ns.delta] if ns.delta else sorted(DELTAS)
    if ns.engine == "both":
        return _compare_engines(names, ns.dump)
    for i, n in enumerate(names):
        if i and not ns.md:
            print()
        run(n, ns.md, ns.dump, ns.engine)
    return 0


def _compare_engines(names: list[str], dump: Path | None) -> int:
    """두 경로의 행 수를 CQ 단위로 대조한다. 갈리면 예시 서사의 근거가 갈린 것이므로 실패다."""
    import tempfile
    bad = 0
    # 저장소 엔진은 파일을 읽으므로 픽스처가 필요하다. `--dump` 를 주지 않았으면 임시 디렉터리에
    # 뜬다 — 대조 때문에 저장소의 고정 픽스처를 덮어쓰지 않는다.
    tmp = None
    if dump is None:
        tmp = tempfile.TemporaryDirectory()
        dump = Path(tmp.name)
    for n in names:
        a = {r[0]: (r[4], r[5]) for r in evaluate(n, dump, "rdflib")["rows"]}
        b = {r[0]: (r[4], r[5]) for r in evaluate(n, dump, "repo")["rows"]}
        diff = sorted(k for k in a if a[k] != b.get(k))
        # 사이드카 CQ 는 기본 경로에 스토어가 없어 0 행이 나오는 것이 정상이다 — 대조에서 뺀다.
        diff = [k for k in diff if k not in SIDECAR]
        mark = "일치" if not diff else f"불일치 {len(diff)}건: " + ", ".join(
            f"{k} rdflib={a[k]} repo={b.get(k)}" for k in diff)
        print(f"[{n}] 행 수 대조 (사이드카 {len(SIDECAR)}개 제외) — {mark}")
        bad += len(diff)
    if tmp:
        tmp.cleanup()
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
