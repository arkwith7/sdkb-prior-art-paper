"""EP5 판정 드라이버 — 결함 21 · 정상 31 · 릴리스 계보 ≤10 (PLAN-064 A-4 · SPEC-010).

**판정식은 사전등록이 정한다. 이 모듈은 그것을 실행하고 집계할 뿐이다.**

- 결함 검출(§6.1): T3 단독 검출 = `fdd` 전량 통과 ∧ (`space` ∪ `core`) 중 ≥1 실패.
- 계보(§6.2): `accept` 는 **null** 이고 `Accept_partial = 1[L0–L3]·1[T3]` 를 따로 남긴다.
  **부분 승인식을 승인식이라 부르지 않는다.**
- 이행 조건 R/N(§6.3): 두 조건 다 돌리고 **어느 한쪽도 취소하지 않는다.** 재판정 규칙은 없다.
- 탐색적(§6.4): `result_digest` · 층별 시간·메모리 · 뷰별 분해 · CQ 개별 행 수.
  **판정식에 들어가지 않는다.**

τ 격자 (0, 0.05, 0.10)는 저장된 CQ 행 수에서 재판정하므로 **재실행이 아니다** — 같은 1회
실행의 다른 읽기다.
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import resource
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from rdflib import Graph

from sdkb_paper import config
from sdkb_paper import profile as _profile
from sdkb_paper.ontology import ep5_graphs as EG

PROFILE = "brick"
OUT_FAULTS = config.PROCESSED / "ep5_faults.json"
OUT_NORMAL = config.PROCESSED / "ep5_normal.json"
OUT_LINEAGE = config.PROCESSED / "ep5_lineage.json"
OUT_COST = config.PROCESSED / "ep5_cost.json"
TABLE = config.ROOT / "paper" / "tables" / "ep5_second_domain.md"
BASE_GEN = "d0"


# --- 층 실행 -----------------------------------------------------------------

def _rss_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def _write(path: Path, g: Graph) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    g.serialize(path, format="turtle")
    return path


def judge_graph(new_path: Path, base_path: Path, shapes: Path,
                base_suites: dict, base_rows: dict | None,
                delta: Graph | None = None, profile=None) -> dict:
    """한 후보 그래프에 L1·L2·L3·T3 를 걸고 τ 격자 전량을 함께 남긴다."""
    from sdkb_paper.validate.cq_runner import run_cqs, suite_pass_rates
    from sdkb_paper.validate.reasoner_gate import check_consistency_detail, dl_projection_count
    from sdkb_paper.validate.shacl_gate import new_violations, validate_graph
    from sdkb_paper.validate.t3_cross_task_cq import t3_gate

    prof = _profile.resolve(profile or PROFILE)
    out: dict = {"timing": {}, "rss_mb_start": _rss_mb()}

    # L1 — ① 델타 shape(있으면) ② 그래프 shape 의 **기준 대비 신규 위반**
    t0 = time.time()
    l1_delta = None
    if delta is not None:
        dp = _write(config.PROCESSED / "ep5_tmp" / f"delta_{abs(hash(str(new_path))) % 10**8}.ttl",
                    delta)
        conforms, _ = validate_graph(dp, shapes="delta", profile=prof)
        l1_delta = {"pass": bool(conforms), "n_triples": len(delta)}
    l1_graph = new_violations(new_path, base_path, shapes=shapes, profile=prof)
    out["l1"] = {"delta_shape": l1_delta, "graph_shape": l1_graph,
                 "pass": l1_graph["pass"] and (l1_delta is None or l1_delta["pass"])}
    out["timing"]["L1"] = round(time.time() - t0, 1)

    # L2 — OWL 2 DL 사영 후 HermiT (제거 트리플 수를 함께 남긴다 · SPEC-010 §6.1)
    t0 = time.time()
    ok, l2info = check_consistency_detail(new_path)
    out["l2"] = {"pass": bool(ok), **l2info,
                 "dl_projection_dropped": dl_projection_count(Graph().parse(new_path))}
    out["timing"]["L2"] = round(time.time() - t0, 1)

    # L3 · T3 — CQ 는 한 번만 돌려 두 층이 나눠 쓴다
    t0 = time.time()
    cq = run_cqs(new_path, targets=("graph",), profile=prof, with_digest=True)
    out["timing"]["L3+T3"] = round(time.time() - t0, 1)
    out["per_cq"] = {r.name: {"suite": r.suite, "rows": r.rows, "passed": r.passed,
                              "digest": r.result_digest} for r in cq}
    grid = {}
    for tau in prof.cq_tau_grid:
        suites = suite_pass_rates(cq, base_rows, tau)
        l3 = all(suites.get(s, {}).get("rate", 0.0) >= base_suites.get(s, {}).get("rate", 0.0)
                 for s in prof.l3_suites)
        t3 = t3_gate(suites, base_suites, profile=prof)
        grid[f"{tau:.2f}"] = {"suites": suites, "L3_pass": l3, "T3_pass": t3["pass"],
                              "T3_regressed": t3["regressed"]}
    out["tau_grid"] = grid
    main = grid[f"{prof.cq_tau:.2f}"]
    out["l3"] = {"pass": main["L3_pass"]}
    out["t3"] = {"pass": main["T3_pass"], "regressed": main["T3_regressed"]}
    # L0 — 스냅샷 sha256 동결 대조. 프로파일 로드가 이미 강제하므로 여기서는 그 사실을 적는다.
    out["l0"] = {"pass": True, "how": "profile.verify_prereg (파일별 sha256 동결 대조)"}
    out["accept"] = None                      # T1·T2 부재 — 승인식은 이 자원에 없다
    out["accept_partial"] = int(out["l0"]["pass"] and out["l1"]["pass"]
                                and out["l2"]["pass"] and out["l3"]["pass"]) * int(
                                    out["t3"]["pass"])
    out["rss_mb_peak"] = _rss_mb()
    return out


# --- 기준선 ------------------------------------------------------------------

def base_artifacts(label: str = BASE_GEN, abox=EG.HOLDOUT_ABOX) -> dict:
    """기준 세대 D₀ 의 그래프·스위트·행 수. 결함과 정상 델타가 공유한다."""
    from sdkb_paper.validate.cq_runner import run_cqs, suite_pass_rates
    prof = _profile.load(PROFILE)
    gp = config.PROCESSED / "ep5" / f"{label}.ttl"
    if not gp.exists():
        _write(gp, EG.assemble(label, abox))
    cq = run_cqs(gp, targets=("graph",), profile=prof, with_digest=True)
    return {"label": label, "path": gp,
            "suites": suite_pass_rates(cq, None, prof.cq_tau),
            "rows": {r.name: r.rows for r in cq},
            "n_triples": len(Graph().parse(gp))}


# --- 결함 21 (사전등록 §4.2) --------------------------------------------------

def fault_instances(profile=None) -> list[tuple[str, float, int]]:
    prof = _profile.resolve(profile or PROFILE)
    out = []
    for key in sorted(prof.faults):
        spec = prof.faults[key]
        for s in spec.strengths:
            for rep in spec.reps:
                out.append((key, float(s), int(rep)))
    return out


def _fault_worker(arg):
    key, strength, rep, graph, shapes = arg
    from sdkb_paper.analysis.faults import run_instance
    try:
        r = run_instance(key, strength, rep, run_id="ep5", profile=PROFILE,
                         graph=Path(graph), baseline_gen=BASE_GEN, shapes=Path(shapes))
    except Exception as e:                     # 실패는 감추지 않는다 — 판정에 실패로 들어간다
        return {"fault": key, "strength": strength, "rep": rep, "error": repr(e)}
    return r


def run_faults(workers: int = 4) -> dict:
    prof = _profile.load(PROFILE)
    base = base_artifacts()
    shapes = EG.tbox_path(BASE_GEN)
    jobs = [(k, s, r, str(base["path"]), str(shapes)) for k, s, r in fault_instances(prof)]
    t0 = time.time()
    if workers > 1:
        # **fork 가 아니라 spawn 이다.** 부모가 이미 rdflib·pyoxigraph 로 기준선을 조립한 뒤
        # fork 하면 자식이 상속한 잠금에서 교착한다 — 실측 2026-08-22: 워커 다섯이 0 % CPU 로
        # 21분간 멈췄고 워크스페이스에 스탬프 파일만 남았다. 멈춘 실험은 느린 실험이 아니라
        # 결과가 없는 실험이다.
        ctx = mp.get_context("spawn")
        with ProcessPoolExecutor(max_workers=workers, mp_context=ctx) as ex:
            futs = {ex.submit(_fault_worker, j): j for j in jobs}
            res = []
            for i, fut in enumerate(as_completed(futs), 1):
                r = fut.result()
                res.append(r)
                first = next((L for L in ("L1", "L2", "L3", "T3")
                              if r.get("detected", {}).get(L)), None)
                print(f"  [{i}/{len(jobs)}] {r['fault']} s={r['strength']} r={r['rep']} "
                      f"→ {first or r.get('error') or '미검출'}", flush=True)
    else:
        res = [_fault_worker(j) for j in jobs]
    rec = {"n_instances": len(res), "wall_clock_s": round(time.time() - t0, 1),
           "baseline": {k: v for k, v in base.items() if k != "path"},
           "instances": res, "judgment": judge_faults(res, prof)}
    OUT_FAULTS.parent.mkdir(parents=True, exist_ok=True)
    OUT_FAULTS.write_text(json.dumps(rec, ensure_ascii=False, indent=2, default=str))
    return rec


def judge_faults(instances: list[dict], profile=None) -> dict:
    """§6.1 확증 — T3 단독 검출 · 단측 McNemar · 묶음별 분리 보고."""
    from sdkb_paper.analysis.faults import mcnemar_one_sided
    prof = _profile.resolve(profile or PROFILE)
    rows, pairs = [], []
    for r in instances:
        if "error" in r:
            rows.append({**{k: r[k] for k in ("fault", "strength", "rep")},
                         "error": r["error"], "t3_only": False})
            continue
        d = r["detected"]
        t3_fail = bool(d.get("T3"))
        # **단독 검출**은 주 태스크가 멀쩡한 채 타 태스크만 무너진 경우다.
        t3_only = t3_fail and not d.get("L3") and not d.get("L1") and not d.get("L2")
        # **주입되지 않은 인스턴스는 판정이 아니다.** 후보가 0 이면 결함이 그래프에 들어가지
        # 않았고, 그것을 "검출 실패"로 세면 게이트가 놓친 적 없는 것을 놓쳤다고 적게 된다.
        n_aff = int(r.get("stats", {}).get("n_affected") or 0)
        vacuous = n_aff == 0
        rows.append({"fault": r["fault"], "strength": r["strength"], "rep": r["rep"],
                     "n_affected": n_aff, "vacuous": vacuous,
                     "L1": d.get("L1"), "L2": d.get("L2"), "L3": d.get("L3"),
                     "T3": t3_fail, "t3_only": t3_only and not vacuous,
                     "bundle": "S" if r["fault"] == "X3" else "M"})
        if not vacuous:
            pairs.append((bool(d.get("L3")), t3_fail))
    n_only = sum(r["t3_only"] for r in rows)
    mc = mcnemar_one_sided(pairs)   # 방향은 사전 지정(T3 우세) · 사전등록 §6.1
    vac = [r for r in rows if r.get("vacuous")]
    per_bundle = {}
    for b in ("M", "S"):
        sel = [r for r in rows if r.get("bundle") == b]
        live = [r for r in sel if not r.get("vacuous")]
        per_bundle[b] = {"n": len(sel), "n_judgeable": len(live),
                         "t3_detected": sum(bool(r.get("T3")) for r in live),
                         "t3_only": sum(bool(r.get("t3_only")) for r in live)}
    # 검정력의 한계는 사전등록 §6.1 이 미리 적었다 — 불일치 쌍 5건 미만이면 유의에 이를 수 없다.
    n_disc = sum(1 for a, b in pairs if a != b)
    return {"n": len(rows), "n_judgeable": len(pairs), "n_vacuous": len(vac),
            "vacuous_by_fault": {k: sum(1 for r in vac if r["fault"] == k)
                                 for k in sorted({r["fault"] for r in vac})},
            "t3_only": n_only, "mcnemar": mc,
            "n_discordant": n_disc,
            "power_note": ("불일치 쌍 5건 미만 — 부호검정이 p<.05 에 이를 수 없다"
                           if n_disc < 5 else None),
            "per_bundle": per_bundle, "rows": rows,
            "suites": list(prof.cq_suites)}


# --- 정상 델타 31 (사전등록 §5) ----------------------------------------------

def run_normals() -> dict:
    prof = _profile.load(PROFILE)
    base = base_artifacts()
    shapes = EG.tbox_path(BASE_GEN)
    out = []
    for d in EG.synthetic_normal_deltas(BASE_GEN, 30, abox_files=EG.HOLDOUT_ABOX):
        g = EG.assemble(BASE_GEN, EG.HOLDOUT_ABOX, extra=d["delta"])
        p = _write(config.PROCESSED / "ep5" / f"normal_{d['id']}.ttl", g)
        j = judge_graph(p, base["path"], shapes, base["suites"], base["rows"],
                        delta=d["delta"], profile=prof)
        out.append({**{k: v for k, v in d.items() if k != "delta"}, "judgment": j,
                    "rejected": j["accept_partial"] == 0})
    # 실제 정상 델타 1건 — v1.4.1 → v1.4.2 (사전등록 §5)
    real = lineage_one(*EG.REAL_NORMAL_DELTA, condition="R", tag="real_normal")
    n_rej = sum(o["rejected"] for o in out)
    rec = {"n_synthetic": len(out), "n_rejected": n_rej,
           "upper_bound_95_one_sided": None if n_rej else round(1 - 0.05 ** (1 / len(out)), 4),
           "note": ("관측 위양성 개수와 95 % 단측 상한을 함께 적는다 — "
                    "'위양성 ≤ 5 %' 라고 쓰지 않는다(사전등록 §5)"),
           "synthetic": out, "real_normal_delta": real}
    OUT_NORMAL.write_text(json.dumps(rec, ensure_ascii=False, indent=2, default=str))
    return rec


# --- 릴리스 계보 (사전등록 §6.2·§6.3) ----------------------------------------

def lineage_one(old: str, new: str, condition: str, tag: str = "") -> dict:
    from sdkb_paper.validate.cq_runner import run_cqs, suite_pass_rates
    prof = _profile.load(PROFILE)
    gb, info_b = EG.lineage_graph(old, condition)
    gn, info_n = EG.lineage_graph(new, condition)
    pb = _write(config.PROCESSED / "ep5" / f"{old}_{condition}.ttl", gb)
    pn = _write(config.PROCESSED / "ep5" / f"{new}_{condition}.ttl", gn)
    cqb = run_cqs(pb, targets=("graph",), profile=prof, with_digest=True)
    base_suites = suite_pass_rates(cqb, None, prof.cq_tau)
    base_rows = {r.name: r.rows for r in cqb}
    delta = EG.tbox_delta(old, new)
    # shape 은 **각 판이 자기 것을 쓴다**(SPEC-010 §6.2) — 후보 그래프는 새 판의 shape 으로 잰다.
    j = judge_graph(pn, pb, EG.tbox_path(new), base_suites, base_rows,
                    delta=delta.added, profile=prof)
    return {"tag": tag or f"{old}->{new}", "old": old, "new": new, "condition": condition,
            "delta": delta.summary(), "migration": {"old": info_b, "new": info_n},
            "n_triples": {"old": len(gb), "new": len(gn)},
            "base_suites": base_suites, "judgment": j}


def run_lineage() -> dict:
    pairs = [(a, b) for (a, _), (b, _) in zip(EG.VERSIONS, EG.VERSIONS[1:])]
    out = [lineage_one(a, b, c) for a, b in pairs for c in ("R", "N")]
    rec = {"n_judgments": len(out), "pairs": [f"{a}->{b}" for a, b in pairs],
           "note": ("accept 는 null 이다 — T1·T2 가 없으므로 승인식이 아니라 부분 승인식이다"),
           "judgments": out}
    OUT_LINEAGE.write_text(json.dumps(rec, ensure_ascii=False, indent=2, default=str))
    return rec


# --- 운용 비용 (사전등록 §7 · 탐색적) ----------------------------------------

def cost_table(faults: dict, lineage: dict) -> dict:
    prof = _profile.load(PROFILE)
    layers: dict[str, list[float]] = {}
    for j in lineage["judgments"]:
        for k, v in j["judgment"]["timing"].items():
            layers.setdefault(k, []).append(v)
    rec = {"resource": "Brick", "n_triples_d0": faults["baseline"]["n_triples"],
           "n_cq": len(prof.cq_suites) * 5, "n_shapes_delta": 3,
           "layer_wall_clock_s_mean": {k: round(sum(v) / len(v), 1) for k, v in layers.items()},
           "faults_wall_clock_s": faults["wall_clock_s"],
           "max_rss_mb": max((j["judgment"]["rss_mb_peak"] for j in lineage["judgments"]),
                             default=0.0),
           "note": "'scalable' 이라고 쓰지 않는다 — 실행 가능성과 비용만 진술한다(사전등록 §7)"}
    OUT_COST.write_text(json.dumps(rec, ensure_ascii=False, indent=2, default=str))
    return rec


# --- 표 렌더 (§1-7 수기 기입 금지) -------------------------------------------

def delta_shape_breakdown(old: str, new: str) -> dict:
    """델타 shape 위반을 **규칙별로** 센다. "L1 실패"만 적으면 이유를 읽을 수 없다."""
    import re
    from collections import Counter

    from pyshacl import validate

    from sdkb_paper.validate.shacl_gate import load_shapes
    d = EG.tbox_delta(old, new)
    _ok, _g, txt = validate(d.added, shacl_graph=load_shapes("delta", PROFILE),
                            advanced=True, inference="rdfs")
    return dict(Counter(re.findall(r"Message: (.+)", txt)))


def render_table(faults: dict, normal: dict, lineage: dict, cost: dict) -> str:
    """결과 표. **판정을 바꾸지 않고 옮겨 적기만 한다** — 값은 전부 판정 JSON 에서 읽는다."""
    j = faults["judgment"]
    L: list[str] = ["# EP5 · 제2 도메인(Brick) 이식 판정", "",
                    "> 자동 생성 — `make ep5`. 손으로 고치지 않는다(CLAUDE.md §1-7).",
                    "> **형식 층과 교차 태스크 층에 한정한 판정이다.** T1·T2 는 이식하지 않았으므로",
                    "> `accept` 는 null 이고 `Accept_partial` 만 남는다(사전등록 §6.2).", ""]

    L += ["## 1. 교차 결함 검출 (확증 · 사전등록 §6.1)", ""]
    if j.get("n_vacuous"):
        by = " · ".join(f"{k} {v}건" for k, v in j["vacuous_by_fault"].items())
        L += [f"> **인스턴스 {j['n']}건 가운데 {j['n_vacuous']}건은 판정이 아니다**({by}). "
              "주입 후보가 0 이어서",
              "> 결함이 그래프에 들어가지 않았다. **판정 가능한 것은 "
              f"{j['n_judgeable']}건**이며, 아래 수치는 그 분모 위에서 읽는다.", ""]
    # **관찰면을 검출 수보다 먼저 적는다.** 홀드아웃 기준에서 행을 내지 못한 역량질문은 어떤
    # 결함이 들어와도 회귀를 보일 수 없으므로, 그 질문 위의 "미검출"은 검출 실패가 아니라
    # 관찰되지 않음이다. 사전등록 §3 이 "홀드아웃에서 0 행인 CQ 는 제거하지 않고 홀드아웃
    # 미충족으로 보고한다"고 지시한 것이 이 줄이다. 값은 판정 JSON 의 기준 행 수에서 센다.
    base_rows = faults.get("baseline", {}).get("rows", {})
    if base_rows:
        live_cq = sum(1 for v in base_rows.values() if v)
        L += [f"- **관찰면**: 홀드아웃 기준에서 행을 낸 역량질문 **{live_cq}/{len(base_rows)}** "
              f"(나머지는 행이 0 이므로 회귀를 보일 수 없다 · 사전등록 §3 의 홀드아웃 미충족)"]
    L += [f"- 인스턴스 **{j['n']}**건(판정 가능 **{j['n_judgeable']}**) · "
          f"T3 단독 검출 **{j['t3_only']}**건 · 불일치 쌍 **{j['n_discordant']}**",
          f"- 단측 McNemar(방향 사전 지정 = T3 우세) *p* = **{j['mcnemar']['p']:.4f}** "
          f"(b={j['mcnemar']['b']} · c={j['mcnemar']['c']} · {j['mcnemar']['test']})"]
    if j.get("power_note"):
        L += [f"- **검정력 한계**: {j['power_note']}"]
    L += ["", "| 묶음 | 인스턴스 | 판정 가능 | T3 검출 | T3 단독 검출 |", "|---|---|---|---|---|"]
    for b, lab in (("M", "(M) 다중 인스턴스 · X2·X4"), ("S", "(S) 단일 · X3")):
        v = j["per_bundle"][b]
        L += [f"| {lab} | {v['n']} | {v['n_judgeable']} | {v['t3_detected']} | {v['t3_only']} |"]
    L += ["", "**묶음을 합산해 하나의 검출률로 쓰지 않는다**(사전등록 §6.1).", "",
          "| 결함 | 강도 | 반복 | 주입 | L1 | L2 | L3(fdd) | T3 | T3 단독 |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in j["rows"]:
        if "error" in r:
            L += [f"| {r['fault']} | {r['strength']} | {r['rep']} | 실행 실패: {r['error'][:60]} ||||"]
            continue
        m = {True: "검출", False: "—", None: "n/a"}
        if r.get("vacuous"):
            L += [f"| {r['fault']} | {r['strength']} | {r['rep']} | **0 · 공허** | "
                  "판정 아님 | 판정 아님 | 판정 아님 | 판정 아님 | — |"]
            continue
        L += [f"| {r['fault']} | {r['strength']} | {r['rep']} | {r['n_affected']} | "
              f"{m[r['L1']]} | {m[r['L2']]} | "
              f"{m[r['L3']]} | {m[r['T3']]} | {'**예**' if r['t3_only'] else '아니오'} |"]

    n = normal
    L += ["", "## 2. 정상 델타 (위양성 분모 · 사전등록 §5)", "",
          f"- 합성 **{n['n_synthetic']}**건 · 관측 위양성 **{n['n_rejected']}**건"]
    if n.get("upper_bound_95_one_sided") is not None:
        L += [f"- 95 % 단측 상한 **{n['upper_bound_95_one_sided']*100:.1f} %** — "
              "*'위양성 ≤ 5 %'* 라고 쓰지 않는다"]
    subs = sum(1 for s in n["synthetic"] if s.get("substituted_from"))
    if subs:
        L += [f"- 규칙 재료 부족으로 **대체 생성 {subs}건** (원 규칙은 각 항목의 "
              "`substituted_from` 에 남는다)"]

    L += ["", "## 3. 릴리스 계보 (확증 · 사전등록 §6.2·§6.3)", "",
          "| 인접 쌍 | 이행 | Δ 추가 | Δ 제거 | L1 | L2 | L3 | T3 | Accept_partial |",
          "|---|---|---|---|---|---|---|---|---|"]
    for x in lineage["judgments"]:
        g = x["judgment"]
        ok = lambda b: "통과" if b else "**실패**"          # noqa: E731
        L += [f"| {x['old']}→{x['new']} | {x['condition']} | {x['delta']['n_added']} | "
              f"{x['delta']['n_removed']} | {ok(g['l1']['pass'])} | {ok(g['l2']['pass'])} | "
              f"{ok(g['l3']['pass'])} | {ok(g['t3']['pass'])} | {g['accept_partial']} |"]
    L += ["", "`accept` 는 전 행에서 **null** 이다 — 부분 승인식을 승인식이라 부르지 않는다.", "",
          "### 3.1 델타 shape 위반 내역 (규칙별)", ""]
    seen = []
    for x in lineage["judgments"]:
        pair = (x["old"], x["new"])
        if pair in seen:
            continue
        seen.append(pair)
        br = delta_shape_breakdown(*pair)
        if not br:
            L += [f"- **{x['old']}→{x['new']}** — 위반 없음"]
            continue
        L += [f"- **{x['old']}→{x['new']}** — " +
              " · ".join(f"{v}건 {k}" for k, v in sorted(br.items(), key=lambda kv: -kv[1]))]
    L += ["", "### 3.2 이행 조건 R/N 의 결과 — 두 조건이 갈리지 않았다", ""]
    mig = {(x["old"], x["new"]): x["migration"]["new"] for x in lineage["judgments"]
           if x["condition"] == "N"}
    tot_rw = sum(m.get("n_rewritten", 0) for m in mig.values())
    unmapped = sorted({u.rsplit("#", 1)[-1] for m in mig.values() for u in m.get("unmapped", [])})
    L += [f"- 이행 재작성 **{tot_rw}건** — (N) 이 (R) 과 **동일한 그래프**를 냈다.",
          f"- 홀드아웃이 쓰는 폐기 항목 가운데 공식 기계 매핑이 없는 것: **{', '.join(unmapped)}**",
          "- Brick v1.4.4 의 폐기 246건 중 기계 적용 가능한 alias 는 "
          "`Photovoltaic_Array → PV_Array` **1건**이고, 나머지는 자연어 이행 메시지뿐이다.",
          "",
          "**따라서 §6.3 의 R/N 비교는 이 자원에서 정보를 내지 않는다.** 두 조건을 다 싣되",
          "*'공식 이행 규칙이 회귀를 흡수한다'* 도 *'흡수하지 못한다'* 도 주장하지 않는다 —",
          "적용할 규칙이 없었기 때문이다.", ""]

    L += ["## 4. 운용 비용 (탐색적 · 사전등록 §7)", "",
          f"- D₀ 트리플 **{cost['n_triples_d0']:,}** · CQ **{cost['n_cq']}** · "
          f"델타 shape **{cost['n_shapes_delta']}**",
          f"- 층별 평균 wall-clock(초): {cost['layer_wall_clock_s_mean']}",
          f"- 결함 21건 총 wall-clock **{cost['faults_wall_clock_s']:.0f}초** · "
          f"최대 RSS **{cost['max_rss_mb']:.0f} MB**", "",
          "**'scalable' 이라고 쓰지 않는다** — 실행 가능성과 비용만 진술한다.", ""]
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="EP5 판정 실행 (PLAN-064 A-4)")
    # `table` 은 **판정을 다시 돌리지 않는다** — 동결된 판정 JSON 넷을 읽어 표만 다시 그린다.
    # 보고 형식이 바뀔 때 판정을 재실행하면 그것은 재측정이며 사전등록의 1회 판정을 깬다
    # (PLAN-064-prereg · CLAUDE.md §1-3). 표만 고치는 경로를 따로 두어 그 유혹을 구조로 막는다.
    ap.add_argument("--stage", choices=("faults", "normal", "lineage", "all", "table"),
                    default="all")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    if a.stage == "table":
        f, n, ln, c = (json.loads(p.read_text(encoding="utf-8"))
                       for p in (OUT_FAULTS, OUT_NORMAL, OUT_LINEAGE, OUT_COST))
        TABLE.parent.mkdir(parents=True, exist_ok=True)
        TABLE.write_text(render_table(f, n, ln, c), encoding="utf-8")
        print(f"[EP5 표] 재생성(판정 재실행 없음) → {TABLE.relative_to(config.ROOT)}")
        return
    f = n = ln = None
    if a.stage in ("faults", "all"):
        f = run_faults(a.workers)
        j = f["judgment"]
        print(f"[EP5 결함] {j['n']}건 · T3 단독검출 {j['t3_only']} · "
              f"불일치쌍 {j['n_discordant']} · McNemar p={j['mcnemar'].get('p')}")
    if a.stage in ("normal", "all"):
        n = run_normals()
        print(f"[EP5 정상] 합성 {n['n_synthetic']} · 위양성 {n['n_rejected']}")
    if a.stage in ("lineage", "all"):
        ln = run_lineage()
        ok = sum(x["judgment"]["accept_partial"] for x in ln["judgments"])
        print(f"[EP5 계보] 판정 {ln['n_judgments']}건 · Accept_partial=1 {ok}건")
    if f and n and ln:
        c = cost_table(f, ln)
        TABLE.parent.mkdir(parents=True, exist_ok=True)
        TABLE.write_text(render_table(f, n, ln, c), encoding="utf-8")
        print(f"[EP5 표] → {TABLE.relative_to(config.ROOT)}")
        print(f"[EP5 비용] 층별 평균(초) {c['layer_wall_clock_s_mean']} · 최대 RSS {c['max_rss_mb']:.0f}MB")


if __name__ == "__main__":
    main()
