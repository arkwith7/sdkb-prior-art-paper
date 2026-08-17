"""PLAN-054 실행 배선 — 적격심사 · B0c · B6/B8 인코딩 · B7/B9/B10 융합 · B★ 선정 · P1′.

사전등록(01.code_spec/plans/PLAN-054)의 §7 적격심사와 §9 실행 절차를 코드로 옮긴 것이다.
**판정 규칙을 여기서 만들지 않는다** — B★ 선정은 §4.2, 보고 문장은 §8 이 이미 정했고 이 스크립트는
그 규칙을 적용할 뿐이다.

부명령
  verify    적격심사 E1–E3·E5–E7 (E4 는 `make leakage`)
  b0c       현행 코퍼스에서 BM25 재산출 → `bm25_b0c_claim{,_B}.txt`   (D4)
  encode    B6·B8 인코딩과 FAISS 검색 (직렬 · 모델 하나만 상주)        (D1·D2)
  assemble  마스크·분할 → `sys_{B0c,B6,B7,B8,B9,B10}_{split}.txt`
  select    B★ 선정 (dev 전용 · §4.2) 과 평가표 산출
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

from sdkb_paper import config
from sdkb_paper.analysis.metrics import _fold, load_run, load_qrel_for_split
from sdkb_paper.retrieval import dense_local as dl
from sdkb_paper.retrieval import layers, systems as S
from sdkb_paper.retrieval.candidate import CandidateMask
from sdkb_paper.retrieval.hybrid import RRF_C, rrf

RUNS = config.IR_RUNS_DIR
RUN_B0C = RUNS / "bm25_b0c_claim.txt"
OUT_JSON = config.IR_DIR / "plan054_multilingual.json"

#: 동결 서명 (사전등록 §1·§7 E2 · OBS8.1)
SIG = {
    "ir_corpus_v09.parquet": "83eef760ed0a",
    "split.parquet": "f93c18d28857",
    "qrel_examiner.parquet": "10ab67f21cc1",
}
#: 실행 전후로 바이트가 바뀌면 안 되는 기존 run (E3)
FROZEN_PREFIXES = ("sys_B0_", "sys_B2_", "sys_B3_", "sys_B4_", "sys_B5_",
                   "sys_P0star_", "sys_P1_")
SPLITS = ("dev", "test", "test_b")


def sha12(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:12]


# --- 적격심사 -----------------------------------------------------------------

def cmd_verify(args) -> int:
    ok = True
    print("E2 · 입력 서명")
    for name, want in SIG.items():
        got = sha12(config.IR_DIR / name)
        mark = "✓" if got == want else "✗"
        ok &= got == want
        print(f"  {mark} {name:24s} {got} (원장 {want})")

    print("E1 · 자원 조건 — 원고 §5 는 O, 디스크는 O′ 이며 P1′ 은 O′ 짝으로만 쓴다(D3)")
    c = pd.read_parquet(config.IR_CORPUS, columns=["is_candidate", "concepts"])
    cand = c[c["is_candidate"]]
    vocab = {x for v in cand["concepts"] if v is not None for x in v}
    per_doc = float(sum(len(v) for v in cand["concepts"] if v is not None) / len(cand))
    print(f"  개념 어휘 {len(vocab)} (O′ 원장 199) · 문서당 {per_doc:.3f} (O′ 원장 3.726)")
    ok &= len(vocab) == 199 and abs(per_doc - 3.726) < 0.01

    print("E7 · 모델 다이제스트")
    for enc in dl.ENCODERS.values():
        try:
            dl.verify_digest(enc)
            print(f"  ✓ {enc.system} {enc.tag} {enc.digest[:12]}")
        except SystemExit as e:
            ok = False
            print(f"  ✗ {e}")

    print("E6 · 절단 조건 (num_ctx 8192 · 어댑터 선절단)")
    texts = pd.read_parquet(config.IR_CORPUS, columns=["is_candidate", "text_main"])
    texts = [str(t or "") for t in texts.loc[texts["is_candidate"], "text_main"]]
    for enc in dl.ENCODERS.values():
        n_cut = sum(1 for t in texts if dl.truncate(t, enc)[1])
        share = n_cut / len(texts)
        print(f"  {enc.system} 초과 {n_cut}건 ({share:.4%}) — B2 는 2건 · "
              f"{'E6 문턱(5 %) 통과' if share < 0.05 else 'B★ 후보 제외'}")
        ok &= share < 0.05

    print("E5 · 결정성(표본 3건 · 동일 입력 2회)")
    for enc in dl.ENCODERS.values():
        same = all(dl._embed_one(t[:2000], enc) == dl._embed_one(t[:2000], enc)
                   for t in texts[:3])
        ok &= same
        print(f"  {'✓' if same else '✗'} {enc.system}")

    print("E3 · 기존 run 서명 기록(실행 후 재대조)")
    base = {p.name: sha12(p) for p in sorted(RUNS.glob("sys_*"))
            if p.name.startswith(FROZEN_PREFIXES)}
    (config.IR_DIR / "plan054_frozen_runs.json").write_text(
        json.dumps(base, indent=2), encoding="utf-8")
    print(f"  {len(base)}개 기록 → plan054_frozen_runs.json")

    print("\n" + ("✓ 적격심사 통과 — E4(`make leakage`)만 남았다" if ok else "✗ 실패 — 실행하지 않는다"))
    return 0 if ok else 1


def cmd_frozen_check(args) -> int:
    """E3 사후 대조 — 기존 run 이 바이트 단위로 불변인가."""
    base = json.loads((config.IR_DIR / "plan054_frozen_runs.json").read_text())
    bad = [n for n, h in base.items() if sha12(RUNS / n) != h]
    print("✓ 기존 run 전량 불변" if not bad else f"✗ 변경됨: {bad}")
    return 0 if not bad else 1


# --- B0c · 인코딩 --------------------------------------------------------------

def cmd_b0c(args) -> int:
    """D4 — 현행 코퍼스에서 BM25 재산출. 색인·토큰화는 바꾸지 않는다(§11-3)."""
    from sdkb_paper.retrieval import bm25

    for layer in (layers.LAYER_A, layers.LAYER_B):
        path = layers.run_path_for_layer(RUN_B0C, layer)
        print(f"BM25 재산출 · layer={layer} → {path.name}")
        bm25.search(k=1000, layer=layer, run_path=path, tag="bm25_b0c")
    return 0


def cmd_encode(args) -> int:
    """B6·B8 — 모델 하나만 상주시키고 직렬로 돈다(§3.3).

    로그는 `data/logs/` 로 남긴다 — `/tmp` 는 재부팅이 지운다(2026-08-17 사고).
    """
    import time

    sys.stdout = dl._Tee(dl.LOG_DIR / f"dense_local_{args.model}.log")   # type: ignore[assignment]
    print(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} · PLAN-054 encode {args.model}"
          f" · 간격 {dl.MIN_INTERVAL_S}s ===")
    for layer in (layers.LAYER_A, layers.LAYER_B):
        dl.search(args.model, k=1000, layer=layer)
    return 0


# --- 조립 ---------------------------------------------------------------------

def _mask_split(raw: dict[str, list[str]], qids: list[str], mask: CandidateMask
                ) -> dict[str, list[str]]:
    """기존 표(`results_table.build_runs`)와 **같은 규칙**으로 마스크·절단한다."""
    return {q: [d for d in raw.get(q, []) if mask.is_allowed(q, d)][: S.POOL_K] for q in qids}


def _split_qids(split: str) -> list[str]:
    sp = pd.read_parquet(config.IR_SPLIT, columns=["doc_id", "split"])
    return sorted(sp.loc[sp["split"] == split, "doc_id"].astype(str))


def _write(run: dict[str, list[str]], path: Path, tag: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for qid, docs in run.items():
            for rank, doc in enumerate(docs, 1):
                f.write(f"{qid} Q0 {doc} {rank} {1.0 / rank:.6f} {tag}\n")
    return path


def cmd_assemble(args) -> int:
    """융합과 분할 — B7 = RRF(B0c, B6) · B9 = RRF(B0c, B8) · B10 = RRF(B0c, B4)."""
    from sdkb_paper.retrieval.ontology_rerank import OntologyFeatures

    mask = CandidateMask()
    feats = OntologyFeatures()
    for split in SPLITS:
        layer = layers.LAYER_B if split == "test_b" else layers.LAYER_A
        qids = _split_qids(split)
        raw = {
            "B0c": load_run(layers.run_path_for_layer(RUN_B0C, layer)),
            "B6": load_run(layers.run_path_for_layer(dl.RUN_PATHS["bge-m3"], layer)),
            "B8": load_run(layers.run_path_for_layer(dl.RUN_PATHS["arctic"], layer)),
        }
        b4 = S.build_b4(feats, mask, qids=qids)
        fused = {
            "B7": rrf([raw["B0c"], raw["B6"]], k=S.POOL_K, c=RRF_C),
            "B9": rrf([raw["B0c"], raw["B8"]], k=S.POOL_K, c=RRF_C),
            "B10": rrf([raw["B0c"], b4], k=S.POOL_K, c=RRF_C),
        }
        for name, r in raw.items():
            _write(_mask_split(r, qids, mask), RUNS / f"sys_{name}_{split}.txt", f"{name}_{split}")
        for name, r in fused.items():
            _write(_mask_split(r, qids, mask), RUNS / f"sys_{name}_{split}.txt", f"{name}_{split}")
        print(f"  {split}: " + " ".join(f"sys_{n}_{split}.txt" for n in [*raw, *fused]))
    return 0


# --- 선정·평가 ----------------------------------------------------------------

def _recall100(run: dict[str, list[str]], qrel_f: dict[str, set[str]], fam, qids) -> float:
    tot = n = 0.0
    for q in qids:
        pos = qrel_f.get(q, set())
        if not pos:
            continue
        tot += len(set(_fold(run.get(q, []), fam)[:100]) & pos) / len(pos)
        n += 1
    return tot / n if n else 0.0


def cmd_select(args) -> int:
    """B★ 선정(§4.2 · dev 전용)과 전 구성의 R@100. 개봉 분할은 선정에 쓰지 않는다."""
    from sdkb_paper.collect.bq_family_ir import load_family_map

    fam = load_family_map()
    out: dict = {"rrf_c": RRF_C, "top_k": 100}
    for split in SPLITS:
        qrel = load_qrel_for_split(
            split, unseal=(split == "test_b"),
            reason=f"PLAN-054 다국어 기준선 평가 (탐색적 · 확증 아님 · split={split})")
        qrel_f = {q: {fam.get(d, d) for d in pos} for q, pos in qrel.items()}
        qids = [q for q in _split_qids(split) if qrel_f.get(q)]
        row = {}
        for name in ("B0", "B3", "B0c", "B6", "B7", "B8", "B9", "B10", "P1"):
            p = RUNS / f"sys_{name}_{split}.txt"
            if p.exists():
                row[name] = _recall100(load_run(p), qrel_f, fam, qids)
        out[split] = {"n_queries": len(qids), "recall100": row}
        print(f"[{split}] n={len(qids)} " + " ".join(f"{k} {v:.4f}" for k, v in row.items()))

    dev = out["dev"]["recall100"]
    if "B7" in dev and "B9" in dev:
        # §4.2 — |Δ| < 0.005 이면 B7(BGE-M3). 개봉 분할은 보지 않는다.
        star = "B7" if (dev["B7"] >= dev["B9"] or dev["B9"] - dev["B7"] < 0.005) else "B9"
        out["b_star"] = star
        print(f"\nB★ = {star} (dev B7 {dev['B7']:.4f} · B9 {dev['B9']:.4f} · 규칙 §4.2)")
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ {OUT_JSON}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("verify")
    sub.add_parser("frozen-check")
    sub.add_parser("b0c")
    e = sub.add_parser("encode")
    e.add_argument("--model", choices=sorted(dl.ENCODERS), required=True)
    sub.add_parser("assemble")
    sub.add_parser("select")
    args = ap.parse_args()
    return {
        "verify": cmd_verify, "frozen-check": cmd_frozen_check, "b0c": cmd_b0c,
        "encode": cmd_encode, "assemble": cmd_assemble, "select": cmd_select,
    }[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
