"""결함주입 × 게이트 층 검출 매트릭스 + McNemar (원고 §4.10·§6.5 · H1 · PLAN-020 W4).

각 결함 인스턴스(결함 12종 × 강도 3 × 반복 R)에 대해 **7개 층 전부**를 돌려 "어느 층이 이
결함을 잡는가"를 기록한다. H1 의 직접 검정은 마지막 두 교차결함(F11 동의어 오병합 · F12 공유
계층 역전)이 **L0–L3·T1·T2 를 통과하고 T3 에서만** 검출되는가다.

층 판정 (사전 정의 · 결과를 보고 바꾸지 않는다):

| 층 | 검출 조건 |
|---|---|
| L0 | 산출물이 입력보다 낡음(mtime 역전) |
| L1 | SHACL 비적합 |
| L2 | HermiT 비일관 |
| L3 | 전 스위트(pa 포함) CQ 통과 수 < 정상 그래프 |
| 누출 | 그래프 누출 표면 G-1 위반>0 또는 G-3 이 정상 기준선 초과 |
| T1 | LB₉₅(ΔR₁₀₀) ≤ −ε — 결함본 P1 vs 정상 B3 |
| T2 | max_s drop_s ≥ δ |
| T3 | {em,tf,core} 통과율이 정상 세대보다 하락 |

**오염 규율.** 결함 그래프·파생 뷰는 `validate.quarantine` 격리 디렉터리에만 쓰고, 인스턴스마다
정본 해시를 재검증한다. 정본이 한 바이트라도 변하면 즉시 중단한다(부분 오염으로 가둔다).

**비용.** 인스턴스당 L2(HermiT)가 55초로 지배적이고 최대 RSS 는 750MB 다 — GPU 가속 대상이
아니며(기호 추론), 24코어 CPU 병렬이 유일한 지렛대다. 기본 워커 수는 12.

CLI: `python -m sdkb_paper.analysis.faults --reps 3 --workers 12`
"""
from __future__ import annotations

import argparse
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from .. import config
from ..validate import fault_inject as FI
from ..validate import quarantine as Q

LAYERS = ("L0", "L1", "L2", "L3", "leak", "T1", "T2", "T3")
REPORT = config.PROCESSED / "fault_matrix.json"
BASELINE = config.PROCESSED / "fault_baseline.json"


# --- 정상 그래프 기준선 (오염 **전에** 한 번 재고 동결) -------------------------
def measure_baseline(graph: Path | None = None) -> dict:
    """결함 없는 G₀ 의 층별 기준값. 모든 검출 판정이 이 값과의 차분이다."""
    from ..validate.cq_runner import run_cqs, suite_pass_rates
    from ..validate.leakage_check import audit_graph

    g = graph or config.GRAPH_V0
    res = run_cqs(g)
    leak = audit_graph(g)
    return {"graph": str(g), "n_cq_pass": sum(r.passed for r in res), "n_cq": len(res),
            "suites": suite_pass_rates(res),
            # T3′(세분화 대리지표)의 기준선 — PLAN-020 §5-1 에서 **결과를 보기 전에** 예고한
            # 약점(CQ 28개 중 26개가 `expect-min: 1` 존재검사)을 계량하기 위한 것이다.
            # 통과/불통과가 아니라 **결과행 수**가 줄었는지를 본다: 세분화된 CQ 라면 잡았을
            # 회귀를 현행 CQ 가 얼마나 놓치는가의 측정. 게이트 판정에는 넣지 않는다.
            "cq_rows": {r.name: r.rows for r in res},
            "cq_suite": {r.name: r.suite for r in res},
            "g1_doc_as_concept": leak["g1_doc_as_concept"],
            "g3_gold_concept_copy_pairs": leak["g3_gold_concept_copy_pairs"]}


def load_baseline() -> dict:
    if not BASELINE.exists():
        raise FileNotFoundError(f"기준선 없음: {BASELINE} (--baseline 먼저)")
    return json.loads(BASELINE.read_text(encoding="utf-8"))


# --- 결함 그래프에서 온톨로지 뷰 재유도 ----------------------------------------
def faulted_features(fault_key: str, strength: float, seed: int, ws: Path):
    """**검색이 실제로 보는 자원 전체**(G₀∪G₁∪G₂)에 같은 결함을 넣고 개념·분류·축 뷰를 다시 만든다.

    왜 G₀ 사본만으로는 안 되는가 — 실측(2026-07-28): 개념 링크 81,504건 중 G₀ 는 9,184건
    (**11.3%**)뿐이다. G₀ 에만 10% 를 주입하면 검색이 보는 자원의 1.1% 만 오염돼 T1 이 둔감해지고,
    그 둔감함은 **게이트의 성질이 아니라 주입 범위의 산물**이 된다. 그래서 형식층(L0–L3·T3)은
    G₀ 사본에서, 성능층(T1·T2)은 합집합에서 판정한다 — 결함 사양·강도·시드는 같다.

    합집합 오염본은 **디스크에 쓰지 않는다**(인스턴스당 ~370MB × 108 = 40GB). 임시 스토어에서
    주입하고 뷰만 뽑는다. 텍스트 팔(B0·B2·B3)·임베딩·색인은 결함군 12종이 건드리지 않으므로
    동결본을 그대로 쓴다 — 비용 절감이자 통제다(텍스트 변동이 T1 판정에 섞이지 않는다).
    """
    import random
    import tempfile

    from pyoxigraph import NamedNode, RdfFormat, Store

    from ..corpus.assemble import GRAPHS, _multi
    from ..ontology.concept_axis import extract
    from ..retrieval.ontology_rerank import OntologyFeatures

    spec = FI.BY_KEY[fault_key]
    with tempfile.TemporaryDirectory() as tmp:
        store = Store(path=str(Path(tmp) / "s"))
        for gname, path in GRAPHS.items():
            with open(path, "rb") as fh:
                store.bulk_load(fh, format=RdfFormat.TURTLE, to_graph=NamedNode(gname))
        spec.fn(store, strength, random.Random(seed))   # 합집합 전체에 같은 결함
        multi = _multi(store)
        # 축·계층도 **오염된 합집합**에서 뽑는다(계층 결함 F06·F12 는 여기서만 보인다)
        axis_df, tree = extract(store=store)

    feats = OntologyFeatures()
    def _get(iri_key, key):
        return frozenset(multi.get(iri_key, {}).get(key, set()))

    # 코퍼스 row 순서를 유지한 채 값만 교체한다 (doc_id → IRI 는 지역명 일치로 되짚는다)
    iri_by_local = {k.rsplit("/", 1)[-1]: k for k in multi}
    for i, doc in enumerate(feats.doc_ids):
        iri = iri_by_local.get(doc)
        feats.concepts[i] = _get(iri, "concepts")
        feats.ipc[i] = _get(iri, "ipc")
        feats.cpc[i] = _get(iri, "cpc")

    feats.axis = dict(zip(axis_df["slug"], axis_df["axis_class"]))
    feats.depth, feats._parent = tree["depth"], tree["parent"]
    OntologyFeatures._ancestors.cache_clear()

    feats.inv_concept = {}
    for i, cs in enumerate(feats.concepts):
        for c in cs:
            feats.inv_concept.setdefault(c, set()).add(i)
    feats.inv_ipc = {}
    for i, cs in enumerate(feats.ipc):
        for c in cs:
            for p in feats._ipc_prefixes(c):
                if len(p) >= 4:
                    feats.inv_ipc.setdefault(p, set()).add(i)
    return feats


FC_CACHE = config.PROCESSED / "fault_fc_cache.json"


def _pool(split: str):
    """(qids, B3 풀, 마스크) — 결함과 무관하게 고정된 재랭크 무대."""
    from ..analysis.metrics import load_run
    from ..analysis.results_table import run_path
    from ..retrieval.candidate import CandidateMask

    from .results_table import _split_qrel

    qrel = _split_qrel(split)
    qids = [q for q, p in qrel.items() if p]
    return qids, load_run(run_path("B3_rrf", split)), CandidateMask()


def build_fc_cache(split: str = "dev") -> Path:
    """FeatureCoverage 성분을 **한 번만** 계산해 굳힌다 (τ = 동결 P1_TAU).

    왜 필요한가 — `FeatureCoverageIndex` 는 featureText 임베딩을 올려 인스턴스당 최대 RSS
    **24.8GB** 를 쓴다(실측 2026-07-28). 108 인스턴스를 병렬로 돌리면 즉시 OOM 이고, 순차로
    돌리면 같은 값을 108번 다시 계산한다. 결함군 12종 중 **청구항·featureText 를 건드리는
    것은 없으므로** FC 성분은 결함과 무관한 상수다 — 한 번 계산해 재사용하는 것이 정확히
    옳다(근사가 아니다). 정합성은 `verify_fc_cache()` 가 동결 P1 run 재현으로 확인한다.
    """
    from ..analysis.results_table import P1_TAU
    from ..retrieval import systems as S
    from ..retrieval.feature_coverage import FeatureCoverageIndex

    qids, b3, mask = _pool(split)
    pool_docs = set(qids)
    pools = {}
    for qid in qids:
        pools[qid] = [d for d in b3.get(qid, []) if mask.is_allowed(qid, d)][:S.POOL_K]
        pool_docs.update(pools[qid])

    fc = FeatureCoverageIndex(restrict_docs=pool_docs)
    out = {}
    for qid, docs in pools.items():
        row = {}
        for d in docs:
            bs = fc.best_sims(qid, d)
            row[d] = float((bs >= P1_TAU).mean()) if bs.size else 0.0
        out[qid] = row
    FC_CACHE.write_text(json.dumps({"split": split, "tau": P1_TAU, "fc": out}), encoding="utf-8")
    return FC_CACHE


def load_fc_cache(split: str = "dev") -> dict:
    if not FC_CACHE.exists():
        raise FileNotFoundError(f"FC 캐시 없음: {FC_CACHE} (--fc-cache 먼저)")
    d = json.loads(FC_CACHE.read_text(encoding="utf-8"))
    if d["split"] != split:
        raise ValueError(f"FC 캐시 분할 불일치: {d['split']} ≠ {split}")
    return d["fc"]


def p1_run_from(feats, split: str, fc: dict) -> dict:
    """주어진 (오염되었을 수 있는) 뷰로 P1 을 재랭크. 동결 τ·α·w₄ — 재선택 없음.

    점수식은 `ontology_eval.rerank_p1` 과 같다: (1−α)·text̃ + α(w_c·c + w_h·p + w_i·ipc + w_f·fc).
    """
    from ..analysis.results_table import P1_ALPHA, P1_W4
    from ..retrieval import systems as S
    from ..retrieval.ontology_rerank import _query_features

    wc, wh, wi, wf = P1_W4
    qids, b3, mask = _pool(split)
    qrows = _query_features(feats)
    out = {}
    for qid in qids:
        qrow = qrows.get(qid)
        pool = [d for d in b3.get(qid, []) if mask.is_allowed(qid, d)][:S.POOL_K]
        m = len(pool)
        scored = []
        for rank0, d in enumerate(pool):
            drow = feats.row.get(d)
            tn = 1.0 - (rank0 / (m - 1)) if m > 1 else 1.0
            if qrow is None or drow is None:
                scored.append(((1.0 - P1_ALPHA) * tn, d))
                continue
            qc, dc = feats.concepts[qrow], feats.concepts[drow]
            ont_s = (wc * feats.concept_overlap(qc, dc)
                     + wh * feats.path_sim(qc, dc)
                     + wi * feats.ipc_sim(feats.ipc[qrow], feats.ipc[drow])
                     + wf * fc.get(qid, {}).get(d, 0.0))
            scored.append(((1.0 - P1_ALPHA) * tn + P1_ALPHA * ont_s, d))
        scored.sort(key=lambda x: (-x[0], x[1]))
        out[qid] = [d for _, d in scored]
    return out


def verify_fc_cache(split: str = "dev") -> dict:
    """정상 뷰 + FC 캐시로 만든 P1 이 **동결 P1 run 과 같은가**. 다르면 실험 경로가 틀린 것이다."""
    from ..analysis.metrics import load_run
    from ..analysis.results_table import run_path
    from ..retrieval.ontology_rerank import OntologyFeatures

    frozen = load_run(run_path("P1", split))
    rebuilt = p1_run_from(OntologyFeatures(), split, load_fc_cache(split))
    same = sum(1 for q in frozen if frozen[q][:100] == rebuilt.get(q, [])[:100])
    return {"n_queries": len(frozen), "identical_top100": same,
            "pass": same == len(frozen)}


_FC: dict = {}


def _fc(split: str) -> dict:
    """워커 프로세스당 FC 캐시 1회 적재 (인스턴스마다 다시 읽지 않는다)."""
    if split not in _FC:
        _FC[split] = load_fc_cache(split)
    return _FC[split]


def faulted_p1_run(fault_key: str, strength: float, seed: int, ws: Path,
                   split: str = "dev", fc: dict | None = None) -> dict:
    """오염 뷰로 P1 을 다시 재랭크한다 (동결 τ·α·w₄ · 재선택 없음)."""
    feats = faulted_features(fault_key, strength, seed, ws)
    return p1_run_from(feats, split, fc if fc is not None else _fc(split))


# --- 한 인스턴스: 결함 주입 → 7층 판정 -----------------------------------------
def run_instance(fault_key: str, strength: float, rep: int, run_id: str,
                 split: str = "dev", skip_t12: bool = False) -> dict:
    """결함 하나를 만들어 전 층에 통과시킨다. 산출물은 전부 격리 디렉터리 안에 남는다."""
    from ..collect.bq_family_ir import load_family_map
    from ..validate.cq_runner import run_cqs, suite_pass_rates
    from ..validate.leakage_check import audit_graph
    from ..validate.t1_noninferiority import t1_gate
    from ..validate.t2_subgroup import t2_gate
    from ..validate.t3_cross_task_cq import load_generation, t3_gate

    from .metrics import load_run
    from .results_table import _split_qrel, run_path
    from .subgroup import query_labels

    base = load_baseline()
    spec = FI.BY_KEY[fault_key]
    seed = FI.seed_for(fault_key, strength, rep)
    label = f"{fault_key}_s{int(strength * 100):02d}_r{rep}"
    ws = Q.workspace(run_id, label, {"fault": fault_key, "strength": strength,
                                     "rep": rep, "seed": seed})
    t0 = time.time()

    # 1) 주입 — 정본은 읽기만 한다
    store = FI.load(config.GRAPH_V0, ws)
    stats = spec.inject(store, strength, seed)
    faulted = FI.dump(store, ws / "graph_faulted.ttl")
    del store

    out = {"fault": fault_key, "label": spec.label, "expected": spec.expected,
           "cross_task": spec.cross_task, "strength": strength, "rep": rep,
           "seed": seed, "workspace": str(ws), "stats": stats, "detected": {}}

    # 2) L0 — F01 은 산출물을 입력보다 낡게 만든다(파일시스템 사실)
    src_mtime = max(p.stat().st_mtime for p in config.EXTERNAL_SDKB.glob("*.ttl"))
    if fault_key == "F01":
        os.utime(faulted, (src_mtime - 86400, src_mtime - 86400))
    out["detected"]["L0"] = faulted.stat().st_mtime < src_mtime

    # 3) L1 SHACL
    from ..validate.shacl_gate import validate_graph
    conforms, _ = validate_graph(faulted, shapes="graph")
    out["detected"]["L1"] = not conforms

    # 4) L2 HermiT
    from ..validate.reasoner_gate import check_consistency
    out["detected"]["L2"] = not check_consistency(faulted)

    # 5) L3 · T3 — CQ 는 한 번만 돌려 두 층이 나눠 쓴다
    cq = run_cqs(faulted)
    n_pass = sum(r.passed for r in cq)
    suites = suite_pass_rates(cq)
    out["n_cq_pass"] = n_pass
    out["detected"]["L3"] = n_pass < base["n_cq_pass"]
    t3 = t3_gate(suites, load_generation("g0")["suites"])
    out["detected"]["T3"] = not t3["pass"]
    out["t3"] = t3

    # 6) 누출 감사 (그래프 층 — F09·F10 표적)
    leak = audit_graph(faulted, baseline=base["g3_gold_concept_copy_pairs"])
    out["detected"]["leak"] = not leak["pass"]
    out["leak"] = {k: leak[k] for k in ("g1_doc_as_concept", "g3_gold_concept_copy_pairs",
                                        "g3_exceeds")}

    # 7) T1·T2 — 오염 뷰로 P1 재랭크 후 정상 B3 와 비교
    if skip_t12:
        out["detected"]["T1"] = out["detected"]["T2"] = None
    else:
        qrel = _split_qrel(split)
        fam = load_family_map()
        b3 = load_run(run_path("B3_rrf", split))
        p1f = faulted_p1_run(fault_key, strength, seed, ws, split)
        t1 = t1_gate(p1f, b3, qrel, family=fam, k=100)
        t2 = t2_gate(p1f, b3, qrel, fam, query_labels(qrel), k=100)
        out["detected"]["T1"] = not t1["pass"]
        out["detected"]["T2"] = not t2["pass"]
        out["t1"], out["t2"] = t1, t2

    out["elapsed_s"] = round(time.time() - t0, 1)
    out["first_layer"] = next((L for L in LAYERS if out["detected"].get(L)), None)

    # 8) 오염 봉인 + 정본 무결성 재검증 (매 인스턴스)
    (ws / "result.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    Q.log({"run_id": run_id, "label": label, "fault": fault_key, "strength": strength,
           "rep": rep, "seed": seed, "first_layer": out["first_layer"]})
    Q.verify_pristine(strict=True)
    return out


def _worker(args: tuple) -> dict:
    try:
        return run_instance(*args)
    except Exception as e:                    # 한 인스턴스 실패가 배치를 죽이지 않게
        return {"fault": args[0], "strength": args[1], "rep": args[2],
                "error": f"{type(e).__name__}: {e}", "detected": {}}


# --- 매트릭스 · 검정 ----------------------------------------------------------
def mcnemar(pairs: list[tuple[bool, bool]]) -> dict:
    """대응 McNemar (양측·연속성 보정). pairs = [(L0–L3 검출, T-gate 검출)] 결함 단위.

    b = 형식층만 잡음 · c = T-gate 만 잡음. c ≫ b 이면 T-gate 가 추가 판별력을 갖는다.
    표본이 작으면(b+c < 25) 정확 이항검정을 쓴다 — χ² 근사가 깨지는 구간이다.
    """
    from scipy import stats

    b = sum(1 for x, y in pairs if x and not y)
    c = sum(1 for x, y in pairs if y and not x)
    n = b + c
    if n == 0:
        return {"b": 0, "c": 0, "n_discordant": 0, "p": 1.0, "test": "none(불일치 0)"}
    if n < 25:
        p = float(stats.binomtest(c, n, 0.5).pvalue)
        test = "exact binomial"
    else:
        chi2 = (abs(b - c) - 1) ** 2 / n
        p = float(stats.chi2.sf(chi2, 1))
        test = "chi2 (연속성 보정)"
    return {"b": b, "c": c, "n_discordant": n, "p": p, "test": test}


def summarize(results: list[dict]) -> dict:
    """결함별 층 검출률 · 최초 검출층 · McNemar · 교차결함 H1 판정."""
    ok = [r for r in results if not r.get("error")]
    by_fault: dict[str, dict] = {}
    for spec in FI.FAULTS + FI.NORMALS:
        rs = [r for r in ok if r["fault"] == spec.key]
        if not rs:
            continue
        rates = {L: (sum(1 for r in rs if r["detected"].get(L)) / len(rs)) for L in LAYERS}
        firsts = [r["first_layer"] for r in rs]
        by_fault[spec.key] = {
            "label": spec.label, "expected": spec.expected, "cross_task": spec.cross_task,
            "n": len(rs), "rates": rates,
            "first_layer": max(set(firsts), key=firsts.count) if firsts else None,
            "undetected": sum(1 for f in firsts if f is None),
        }

    ok = [r for r in ok if not r["fault"].startswith("N")]
    normals = [r for r in results if r["fault"].startswith("N") and not r.get("error")]
    fp = [r for r in normals if r["first_layer"]]
    pairs = [(any(r["detected"].get(L) for L in ("L0", "L1", "L2", "L3")),
              any(r["detected"].get(L) for L in ("T1", "T2", "T3")))
             for r in ok]
    cross = [r for r in ok if r["cross_task"]]
    t3_only = [r for r in cross
               if r["detected"].get("T3")
               and not any(r["detected"].get(L) for L in ("L0", "L1", "L2", "L3", "T1", "T2"))]
    return {"n_instances": len(ok), "n_errors": sum(1 for r in results if r.get("error")),
            "false_positive": {"n_normal": len(normals), "n_rejected": len(fp),
                               "rate": (len(fp) / len(normals)) if normals else None,
                               "rejected": [{"fault": r["fault"], "strength": r["strength"],
                                             "layer": r["first_layer"]} for r in fp]},
            "by_fault": by_fault, "mcnemar": mcnemar(pairs),
            "h1": {"n_cross_instances": len(cross), "n_t3_only": len(t3_only),
                   "rate_t3_only": (len(t3_only) / len(cross)) if cross else 0.0}}


def run_matrix(reps: int = 3, strengths: tuple = FI.STRENGTHS, workers: int = 12,
               split: str = "dev", faults: tuple | None = None,
               skip_t12: bool = False, run_id: str | None = None,
               report: Path = REPORT) -> dict:
    run_id = run_id or f"w4_r{reps}"
    keys = faults or tuple(f.key for f in FI.FAULTS + FI.NORMALS)
    jobs = [(k, s, r, run_id, split, skip_t12)
            for k in keys for s in strengths for r in range(reps)]
    results = []
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_worker, j): j for j in jobs}
        for i, fut in enumerate(as_completed(futs), 1):
            r = fut.result()
            results.append(r)
            print(f"  [{i}/{len(jobs)}] {r['fault']} s={r['strength']} r={r['rep']} "
                  f"→ {r.get('first_layer') or r.get('error') or '미검출'}", flush=True)
    results.sort(key=lambda r: (r["fault"], r["strength"], r["rep"]))
    out = {"run_id": run_id, "split": split, "reps": reps, "strengths": list(strengths),
           "workers": workers, "elapsed_s": round(time.time() - t0, 1),
           "summary": summarize(results), "instances": results}
    report.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    Q.lock(Q.QUARANTINE / run_id)
    return out


def t3_prime(run_id: str = "w4_r3") -> dict:
    """**T3′ — CQ 세분화 대리지표** (탐색적 진단 · 게이트 판정 아님).

    현행 CQ 는 28개 중 26개가 `expect-min: 1` 이라 "결과행이 하나라도 있는가"만 묻는다. 결함이
    CQ 를 **0행으로 만들어야만** L3·T3 가 반응하므로, 1–10% 강도의 국소 결함은 원리적으로 통과한다
    (PLAN-020 §5-1 에서 실행 **전에** 예고했다). 이 진단은 통과/불통과 대신 **결과행 수**를 보고
    "CQ 를 세분화했다면 잡혔을 회귀"를 계량한다 — 부록 F 처방의 기대효과 측정이자, T3 가 놓친
    것이 게이트 구조의 문제인지 CQ 해상도의 문제인지를 가른다.

    격리된 결함 그래프를 **읽기만 한다**(재주입 없음 · 정본 불변).
    """
    from ..validate.cq_runner import run_cqs

    base = load_baseline()
    rows_base, suite_of = base["cq_rows"], base["cq_suite"]
    cross = {"em", "tf", "core"}
    out = []
    for d in sorted((Q.QUARANTINE / run_id).iterdir()):
        g = d / "graph_faulted.ttl"
        res_path = d / "result.json"
        if not (g.exists() and res_path.exists()):
            continue
        inst = json.loads(res_path.read_text(encoding="utf-8"))
        rows = {r.name: r.rows for r in run_cqs(g)}
        dropped = {k: (rows_base[k], rows[k]) for k in rows_base
                   if rows.get(k, 0) < rows_base[k]}
        dropped_cross = {k: v for k, v in dropped.items() if suite_of[k] in cross}
        out.append({"fault": inst["fault"], "strength": inst["strength"], "rep": inst["rep"],
                    "cross_task": inst["cross_task"], "t3_detected": inst["detected"].get("T3"),
                    "n_cq_dropped": len(dropped), "n_cross_dropped": len(dropped_cross),
                    "cross_cqs": sorted(dropped_cross)})
    by_fault: dict[str, dict] = {}
    for r in out:
        rec = by_fault.setdefault(r["fault"], {"n": 0, "t3": 0, "t3_prime": 0, "cqs": set()})
        rec["n"] += 1
        rec["t3"] += int(bool(r["t3_detected"]))
        rec["t3_prime"] += int(r["n_cross_dropped"] > 0)
        rec["cqs"].update(r["cross_cqs"])
    for rec in by_fault.values():
        rec["cqs"] = sorted(rec["cqs"])
    return {"run_id": run_id, "by_fault": by_fault, "instances": out}


# --- W4b 재판정 (PLAN-021) — 결함을 다시 넣지 않는다 ---------------------------
REPORT_V2 = config.PROCESSED / "fault_matrix_v2.json"
REJUDGE_RUNS = ("w4_r3", "w4b_n03")


def _rejudge_one(args: tuple) -> dict:
    """격리 인스턴스 하나를 **읽기만 해서** CQ 를 다시 세고 τ 격자 전체로 판정한다."""
    from ..validate.cq_runner import regressions, run_cqs, suite_pass_rates

    d, taus = Path(args[0]), args[1]
    base = load_baseline()
    inst = json.loads((d / "result.json").read_text(encoding="utf-8"))
    res = run_cqs(d / "graph_faulted.ttl")
    base_rows = base["cq_rows"]
    gen_suites = json.loads((config.CQ_GEN_DIR / "cq_g0.json").read_text(encoding="utf-8"))["suites"]

    from ..validate.t3_cross_task_cq import t3_gate
    per_tau = {}
    for tau in taus:
        n_pass = sum(1 for r in res if r.judge(base_rows.get(r.name), tau))
        rates = suite_pass_rates(res, base_rows, tau)
        t3 = t3_gate(rates, gen_suites)
        regs = regressions(res, base_rows, tau)
        per_tau[f"{tau:.2f}"] = {
            "L3": n_pass < base["n_cq_pass"], "T3": not t3["pass"],
            "n_cq_pass": n_pass, "regressed_suites": t3["regressed"],
            "regressed_cqs": [r["cq"] for r in regs],
            "cross_regressed_cqs": [r["cq"] for r in regs if r["suite"] in config.T3_SUITES],
        }
    return {"fault": inst["fault"], "label": inst["label"], "expected": inst["expected"],
            "cross_task": inst["cross_task"], "strength": inst["strength"], "rep": inst["rep"],
            "v1": inst["detected"], "v2_by_tau": per_tau}


def rejudge(runs: tuple = REJUDGE_RUNS, taus: tuple = config.CQ_TAU_GRID,
            workers: int = 10) -> dict:
    """**W4b — 판정 규칙만 바꿔 W4 격리본을 다시 읽는다** (PLAN-021 §4).

    결함을 다시 주입하지 않는다: 바뀐 것은 CQ 판정 규칙(v1 존재검사 → v2 존재∧분포)뿐이고,
    L0·L1·L2·누출·T1·T2 는 결함 그래프의 함수라 v1 인스턴스의 저장값을 그대로 승계한다.
    같은 인스턴스의 **대응 비교**가 되므로 McNemar 가 정당하고, 1,908초 배치·47GB 재생성이
    사라진다. 격리본은 0444 잠금 그대로 — 읽기만 한다.
    """
    dirs = []
    for run_id in runs:
        root = Q.QUARANTINE / run_id
        if not root.exists():
            continue
        dirs += [d for d in sorted(root.iterdir())
                 if (d / "graph_faulted.ttl").exists() and (d / "result.json").exists()]
    if not dirs:
        raise FileNotFoundError(f"재판정할 격리 인스턴스가 없다: {runs}")

    t0 = time.time()
    out = []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(_rejudge_one, (str(d), taus)) for d in dirs]
        for i, fut in enumerate(as_completed(futs), 1):
            r = fut.result()
            out.append(r)
            print(f"  [{i}/{len(dirs)}] {r['fault']} s={r['strength']} r={r['rep']} "
                  f"→ v2(τ={config.CQ_TAU}) L3={r['v2_by_tau'][f'{config.CQ_TAU:.2f}']['L3']} "
                  f"T3={r['v2_by_tau'][f'{config.CQ_TAU:.2f}']['T3']}", flush=True)
    out.sort(key=lambda r: (r["fault"], r["strength"], r["rep"]))
    res = {"runs": list(runs), "taus": list(taus), "rule_version": config.CQ_RULE_VERSION,
           "tau_main": config.CQ_TAU, "elapsed_s": round(time.time() - t0, 1),
           "summary": {f"{t:.2f}": summarize_v2(out, t) for t in taus},
           "instances": out}
    REPORT_V2.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    Q.verify_pristine(strict=True)
    return res


def _merged_layers(inst: dict, tau: float) -> dict:
    """v1 의 층 판정에 v2 의 L3·T3 를 얹은 최종 검출 벡터."""
    v2 = inst["v2_by_tau"][f"{tau:.2f}"]
    d = dict(inst["v1"])
    d["L3"], d["T3"] = v2["L3"], v2["T3"]
    return d


def summarize_v2(instances: list[dict], tau: float) -> dict:
    """τ 하나에서의 v1 vs v2 요약 — 검출률·McNemar·H1′·위양성."""
    by_fault: dict[str, dict] = {}
    for spec in FI.FAULTS + FI.NORMALS:
        rs = [r for r in instances if r["fault"] == spec.key]
        if not rs:
            continue
        merged = [_merged_layers(r, tau) for r in rs]
        firsts = [next((L for L in LAYERS if m.get(L)), None) for m in merged]
        by_fault[spec.key] = {
            "label": spec.label, "expected": spec.expected, "cross_task": spec.cross_task,
            "n": len(rs),
            "rates": {L: sum(1 for m in merged if m.get(L)) / len(rs) for L in LAYERS},
            "v1_L3": sum(1 for r in rs if r["v1"].get("L3")),
            "v1_T3": sum(1 for r in rs if r["v1"].get("T3")),
            "v2_L3": sum(1 for m in merged if m["L3"]),
            "v2_T3": sum(1 for m in merged if m["T3"]),
            "first_layer": max(set(firsts), key=firsts.count) if firsts else None,
            "undetected": sum(1 for f in firsts if f is None),
            "cross_cqs": sorted({c for r in rs
                                 for c in r["v2_by_tau"][f"{tau:.2f}"]["cross_regressed_cqs"]}),
        }
    faults = [r for r in instances if not r["fault"].startswith("N")]
    normals = [r for r in instances if r["fault"].startswith("N")]
    fp = [r for r in normals
          if any(_merged_layers(r, tau).get(L) for L in LAYERS)]
    pairs = [(any(_merged_layers(r, tau).get(L) for L in ("L0", "L1", "L2", "L3")),
              any(_merged_layers(r, tau).get(L) for L in ("T1", "T2", "T3")))
             for r in faults]
    cross = [r for r in faults if r["cross_task"]]
    t3_only = [r for r in cross
               if _merged_layers(r, tau)["T3"]
               and not any(_merged_layers(r, tau).get(L)
                           for L in ("L0", "L1", "L2", "L3", "T1", "T2"))]
    return {"tau": tau, "n_instances": len(faults), "by_fault": by_fault,
            "n_t3_v1": sum(1 for r in faults if r["v1"].get("T3")),
            "n_t3_v2": sum(1 for r in faults if _merged_layers(r, tau)["T3"]),
            "n_l3_v1": sum(1 for r in faults if r["v1"].get("L3")),
            "n_l3_v2": sum(1 for r in faults if _merged_layers(r, tau)["L3"]),
            "false_positive": {"n_normal": len(normals), "n_rejected": len(fp),
                               "rate": (len(fp) / len(normals)) if normals else None,
                               "rejected": [{"fault": r["fault"], "strength": r["strength"]}
                                            for r in fp]},
            "mcnemar": mcnemar(pairs),
            "h1p": {"n_cross_instances": len(cross), "n_t3_only": len(t3_only),
                    "n_t3_detected": sum(1 for r in cross if _merged_layers(r, tau)["T3"]),
                    "rate_t3_only": (len(t3_only) / len(cross)) if cross else 0.0}}


def render_table_v2(res: dict) -> str:
    """원고 표 6.5v2 — 판정 규칙 v1 vs v2. 수기 기입 없음(CLAUDE §1-7)."""
    tau = res["tau_main"]
    s = res["summary"][f"{tau:.2f}"]
    lines = [
        "# 표 6.5v2 결함 주입 재판정 — CQ 판정 v1(존재검사) vs v2(존재∧분포검사)",
        "",
        f"판정 규칙 {res['rule_version']} · 주 τ={tau} · 사전 동결 격자 {res['taus']} · "
        f"결함 재주입 없음(격리본 재판정 · PLAN-021 §4)",
        "",
        "**H1 은 사전등록대로 기각된 채다.** 아래는 부록 F 가 실행 전에 예고한 처방(CQ 세분화)을 "
        "수행한 뒤의 **사후 재설계 검정 H1′**이며, 같은 데이터의 재판정이므로 독립 증거가 아니다.",
        "",
        "| 결함 | 예상층 | " + " | ".join(LAYERS) + " | L3 v1→v2 | T3 v1→v2 | 최초 검출층 | 미탐지 |",
        "|---|---|" + "---:|" * len(LAYERS) + "---:|---:|---|---:|",
    ]
    for key, r in s["by_fault"].items():
        if key.startswith("N"):
            continue
        name = f"**{r['label']}**" if r["cross_task"] else r["label"]
        cells = " | ".join(f"{r['rates'][L]:.2f}" for L in LAYERS)
        lines.append(f"| {name} | {r['expected']} | {cells} | "
                     f"{r['v1_L3']}→{r['v2_L3']} | {r['v1_T3']}→{r['v2_T3']} | "
                     f"{r['first_layer'] or '—'} | {r['undetected']}/{r['n']} |")
    m, h, fp = s["mcnemar"], s["h1p"], s["false_positive"]
    lines += [
        "",
        f"- **T3 검출** v1 {s['n_t3_v1']}/{s['n_instances']} → **v2 {s['n_t3_v2']}/{s['n_instances']}** · "
        f"L3 검출 v1 {s['n_l3_v1']} → v2 {s['n_l3_v2']}",
        f"- **H1′ 교차결함 T3 단독검출**: {h['n_t3_only']}/{h['n_cross_instances']} "
        f"(T3 가 잡은 교차결함은 {h['n_t3_detected']}/{h['n_cross_instances']})",
        f"- **McNemar**(L0–L3 vs T-gate · 결함 단위 대응): b={m['b']} · c={m['c']} · "
        f"p={m['p']:.4f} ({m['test']})",
        f"- **위양성**(정상 델타 거부): {fp['n_rejected']}/{fp['n_normal']}"
        + (f" = {fp['rate']:.1%}" if fp["rate"] is not None else ""),
    ]
    for key in ("N01", "N02", "N03"):
        r = s["by_fault"].get(key)
        if r:
            lines.append(f"  - {key} {r['label']}: 거부 {r['n'] - r['undetected']}/{r['n']}")
    lines += ["", "## τ 민감도 (사전 동결 격자 · 결과를 보고 고르지 않는다)", "",
              "| τ | T3 검출 | L3 검출 | 위양성 | H1′ T3 단독 |", "|---:|---:|---:|---:|---:|"]
    for t in res["taus"]:
        st = res["summary"][f"{t:.2f}"]
        lines.append(f"| {t:.2f} | {st['n_t3_v2']}/{st['n_instances']} | "
                     f"{st['n_l3_v2']}/{st['n_instances']} | "
                     f"{st['false_positive']['n_rejected']}/{st['false_positive']['n_normal']} | "
                     f"{st['h1p']['n_t3_only']}/{st['h1p']['n_cross_instances']} |")
    cross_rows = [(k, r) for k, r in s["by_fault"].items() if r["cross_task"] or r["cross_cqs"]]
    if cross_rows:
        lines += ["", "## v2 에서 회귀로 판정된 교차 태스크 CQ", "",
                  "| 결함 | 하락한 교차 태스크 CQ |", "|---|---|"]
        for k, r in cross_rows:
            lines.append(f"| {r['label']} | {', '.join(c.split('_')[0] for c in r['cross_cqs']) or '—'} |")
    return "\n".join(lines) + "\n"


def render_table(res: dict) -> str:
    """원고 표 6.5 — 결함 × 게이트 층 검출 매트릭스. 수기 기입 없음(CLAUDE §1-7)."""
    s = res["summary"]
    head = ("| 결함 | 예상층 | " + " | ".join(LAYERS) + " | 최초 검출층 | 미탐지 |")
    sep = "|---|---|" + "---:|" * len(LAYERS) + "---|---:|"
    lines = ["# 표 6.5 결함 주입 × 게이트 층 검출 매트릭스",
             "",
             f"분할 {res['split']} · 결함 12종 × 강도 {res['strengths']} × 반복 {res['reps']} "
             f"= {s['n_instances']}인스턴스 (정상 델타 {s['false_positive']['n_normal']}건 별도) · "
             f"셀 = 해당 층 검출률", "", head, sep]
    for key, r in s["by_fault"].items():
        if key.startswith("N"):
            continue
        name = f"**{r['label']}**" if r["cross_task"] else r["label"]
        cells = " | ".join(f"{r['rates'][L]:.2f}" for L in LAYERS)
        lines.append(f"| {name} | {r['expected']} | {cells} | "
                     f"{r['first_layer'] or '—'} | {r['undetected']}/{r['n']} |")
    m, h, fp = s["mcnemar"], s["h1"], s["false_positive"]
    lines += ["",
              f"- **McNemar**(L0–L3 검출 vs T-gate 검출, 결함 단위 대응): b={m['b']} · c={m['c']} · "
              f"불일치 {m['n_discordant']} · p={m['p']:.4f} ({m['test']})",
              f"- **H1 교차결함 T3 단독검출**: {h['n_t3_only']}/{h['n_cross_instances']} "
              f"= {h['rate_t3_only']:.1%}",
              f"- **위양성률**(정상 델타 거부): {fp['n_rejected']}/{fp['n_normal']}"
              + (f" = {fp['rate']:.1%}" if fp["rate"] is not None else "")]
    for key in ("N01", "N02"):
        r = s["by_fault"].get(key)
        if r:
            lines.append(f"  - {key} {r['label']}: 거부 {r['n'] - r['undetected']}/{r['n']}")

    tp_path = config.PROCESSED / "fault_t3_prime.json"
    if tp_path.exists():
        tp = json.loads(tp_path.read_text(encoding="utf-8"))
        lines += ["", "## 표 6.5b T3′ — CQ 세분화 대리지표 (탐색적 진단 · 게이트 판정 아님)", "",
                  "현행 CQ 는 28개 중 26개가 `expect-min: 1` 존재검사라 결함이 CQ 를 **0행으로**",
                  "만들어야만 T3 가 발화한다. T3′ 는 통과/불통과 대신 **결과행 수 하락**을 보아",
                  "\"CQ 를 세분화했다면 잡혔을 회귀\"를 계량한다(PLAN-020 §5-1 에서 실행 전 예고).", "",
                  "| 결함 | T3 검출 | **T3′ 행수하락** | n | 하락한 교차 태스크 CQ |",
                  "|---|---:|---:|---:|---|"]
        for key, r in sorted(tp["by_fault"].items()):
            spec = FI.BY_KEY.get(key)
            name = spec.label if spec else key
            if key.startswith("N"):
                name += " ※위양성 분모"
            lines.append(f"| {name} | {r['t3']}/{r['n']} | **{r['t3_prime']}/{r['n']}** | "
                         f"{r['n']} | {', '.join(c.split('_')[0] for c in r['cqs']) or '—'} |")
        tot = sum(r["t3_prime"] for k, r in tp["by_fault"].items() if not k.startswith("N"))
        n_f = sum(r["n"] for k, r in tp["by_fault"].items() if not k.startswith("N"))
        fp = sum(r["t3_prime"] for k, r in tp["by_fault"].items() if k.startswith("N"))
        n_n = sum(r["n"] for k, r in tp["by_fault"].items() if k.startswith("N"))
        lines += ["", f"- 결함 검출 **{tot}/{n_f}** (T3 는 0/{n_f}) · 정상 델타 오탐 **{fp}/{n_n}**"]
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", action="store_true", help="정상 그래프 기준선 측정·동결")
    ap.add_argument("--fc-cache", action="store_true",
                    help="FeatureCoverage 성분 1회 계산·동결(+동결 P1 재현 검증)")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--split", default="dev", choices=["dev"], help="dev 전용(test 재개봉 금지)")
    ap.add_argument("--faults", default=None, help="쉼표구분 결함키(기본 전량)")
    ap.add_argument("--skip-t12", action="store_true", help="T1·T2 생략(연기 진단용)")
    ap.add_argument("--write", action="store_true", help="표 6.5 를 paper/tables/ 에 기록")
    ap.add_argument("--from-report", action="store_true", help="재실행 없이 기존 매트릭스로 표만")
    ap.add_argument("--t3-prime", action="store_true",
                    help="CQ 세분화 대리지표(탐색적 진단 · 격리 그래프 재질의)")
    ap.add_argument("--n03", action="store_true",
                    help="W4b 정상 델타 N03(완전중복 병합)만 주입 → run_id w4b_n03")
    ap.add_argument("--rejudge", action="store_true",
                    help="W4b 재판정 — 격리본을 읽어 CQ 판정 v1 vs v2 × τ 격자 (재주입 없음)")
    args = ap.parse_args()

    if args.baseline:
        Q.seal()
        b = measure_baseline()
        BASELINE.write_text(json.dumps(b, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[기준선] CQ {b['n_cq_pass']}/{b['n_cq']} · G-1 {b['g1_doc_as_concept']} · "
              f"G-3 {b['g3_gold_concept_copy_pairs']} → {BASELINE}")
        return

    if args.fc_cache:
        p = build_fc_cache(args.split)
        v = verify_fc_cache(args.split)
        print(f"[FC 캐시] {p}")
        print(f"  동결 P1 재현: top-100 일치 {v['identical_top100']}/{v['n_queries']} "
              f"→ {'PASS' if v['pass'] else 'FAIL — 실험 경로가 정본과 다르다'}")
        raise SystemExit(0 if v["pass"] else 1)

    if args.t3_prime:
        tp = t3_prime()
        out = config.PROCESSED / "fault_t3_prime.json"
        out.write_text(json.dumps(tp, ensure_ascii=False, indent=2), encoding="utf-8")
        print("[T3′ CQ 세분화 대리지표 · 탐색적]  결함  T3 검출 / T3′ 행수하락 / n")
        for k, r in sorted(tp["by_fault"].items()):
            print(f"  {k}  {r['t3']:>2} / {r['t3_prime']:>2} / {r['n']:>2}   "
                  f"{','.join(r['cqs'][:6])}")
        print(f"  → {out}")
        return

    if args.n03:
        Q.verify_pristine(strict=True)
        res = run_matrix(args.reps, workers=min(args.workers, 9), split=args.split,
                         faults=("N03",), run_id="w4b_n03",
                         report=config.PROCESSED / "fault_matrix_n03.json")
        s = res["summary"]
        print(f"\n[N03 정상 델타] {s['n_instances'] + s['false_positive']['n_normal']}인스턴스 · "
              f"오류 {s['n_errors']} · {res['elapsed_s']}초 · "
              f"거부 {s['false_positive']['n_rejected']}/{s['false_positive']['n_normal']}")
        return

    if args.rejudge:
        res = rejudge(workers=args.workers)
        tau = res["tau_main"]
        s = res["summary"][f"{tau:.2f}"]
        print(f"\n[W4b 재판정] 규칙 {res['rule_version']} · 주 τ={tau} · {res['elapsed_s']}초")
        print(f"  T3 검출 v1 {s['n_t3_v1']}/{s['n_instances']} → v2 {s['n_t3_v2']}/{s['n_instances']}"
              f"  ·  L3 v1 {s['n_l3_v1']} → v2 {s['n_l3_v2']}")
        print(f"  H1′ 교차결함 T3 단독검출 {s['h1p']['n_t3_only']}/{s['h1p']['n_cross_instances']} "
              f"(T3 검출 {s['h1p']['n_t3_detected']}/{s['h1p']['n_cross_instances']})")
        print(f"  McNemar b={s['mcnemar']['b']} c={s['mcnemar']['c']} p={s['mcnemar']['p']:.4f}")
        print(f"  위양성 {s['false_positive']['n_rejected']}/{s['false_positive']['n_normal']}")
        out = config.ROOT / "paper" / "tables" / "fault_matrix_v2.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_table_v2(res), encoding="utf-8")
        print(f"  표 → {out}\n  → {REPORT_V2}")
        return

    if args.from_report:
        res = json.loads(REPORT.read_text(encoding="utf-8"))
        out = config.ROOT / "paper" / "tables" / "fault_matrix.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_table(res), encoding="utf-8")
        print(render_table(res))
        print(f"→ {out}")
        return

    Q.verify_pristine(strict=True)
    faults = tuple(args.faults.split(",")) if args.faults else None
    res = run_matrix(args.reps, workers=args.workers, split=args.split,
                     faults=faults, skip_t12=args.skip_t12)
    s = res["summary"]
    print(f"\n[결함주입 매트릭스] {s['n_instances']}인스턴스 · 오류 {s['n_errors']} · "
          f"{res['elapsed_s']}초")
    print(f"  McNemar b={s['mcnemar']['b']} c={s['mcnemar']['c']} "
          f"p={s['mcnemar']['p']:.4f} ({s['mcnemar']['test']})")
    print(f"  H1 교차결함 T3 단독검출 {s['h1']['n_t3_only']}/{s['h1']['n_cross_instances']}")
    fp = s["false_positive"]
    print(f"  위양성(정상 델타 거부) {fp['n_rejected']}/{fp['n_normal']}"
          + (f" = {fp['rate']:.1%}" if fp["rate"] is not None else ""))
    if args.write:
        out = config.ROOT / "paper" / "tables" / "fault_matrix.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_table(res), encoding="utf-8")
        print(f"  표 → {out}")
    print(f"  → {REPORT}")


if __name__ == "__main__":
    main()
