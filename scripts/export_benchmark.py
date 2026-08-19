#!/usr/bin/env python3
"""평가 하네스를 공개 트리로 내보낸다 (PLAN-058 §8 · 단일 생산자).

**왜 스크립트인가.** 손으로 복사하면 두 리포의 사본이 갈린다 — 상류 D-38 이 정확히 그
실패였고, 그때 갈린 사본에서 코퍼스 최빈 개념이 빠졌다. 목록·해시·제외 사유를 **코드가**
낸다(CLAUDE.md §1-7).

**복사하되 고치지 않는다.** 패키지 이름 `sdkb_paper` 를 유지한다 — 44개 파일이
`from sdkb_paper.…` 절대 임포트를 쓰므로, 이름을 바꾸면 공개본은 감사 대상 소스가 아니라
그 변형본이 된다(PLAN-058 §8.1).

**대상 디렉터리는 상류 워킹트리다.** 발행은 상류의 기존 기계(허용목록·절대경로 세척·지문
검사·PROVENANCE)가 그대로 처리한다. **상류는 이 디렉터리를 편집하지 않는다.**

CLI:
    python scripts/export_benchmark.py --out ~/Dev/sdkb/benchmark
    python scripts/export_benchmark.py --out ~/Dev/sdkb/benchmark --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "sdkb_paper"

# ── 코드 허용목록 (PLAN-058 §1.1 · 임포트 폐포를 실측으로 닫았다) ────────────────
CODE = {
    "": ["config.py", "__init__.py"],
    "retrieval": ["bm25", "dense", "dense_local", "hybrid", "systems", "ontology_rerank",
                  "candidate", "feature_coverage", "layers", "tokenize", "userdict", "__init__"],
    "analysis": ["metrics", "bootstrap", "ablation", "subgroup", "effort", "overlap",
                 "ontology_eval", "results_table", "faults", "failure_typology",
                 "judgment_robustness", "increment", "lang_recall", "pathsim_diag", "__init__"],
    "validate": ["t1_noninferiority", "t2_subgroup", "t3_cross_task_cq", "t_gate",
                 "leakage_check", "fault_inject", "cq_runner", "shacl_gate", "reasoner_gate",
                 "seal_audit", "runset", "vocab_coverage", "dedup_exempt", "quarantine",
                 "__init__"],
    "corpus": ["assemble", "split", "claim_join", "claim_features", "concept_link",
               "qrel_b", "qrel_family_merge", "text", "__init__"],
    "rag": ["frozen", "context", "generate", "score", "t4", "count", "__init__"],
    "viz": ["figures", "figdata", "concept", "__init__"],
    "ontology": ["concept_axis", "concept_dict", "central_axis", "vendor", "baseline",
                 "merge", "mapping"],
    "collect": ["bq_family_ir", "__init__"],
}
EXTRA_CODE = ["analysis/typology_prompt.txt"]

# ── 평가 자산 (§6.6 이 공개 대상으로 이미 선언한 것) ─────────────────────────────
ASSET_GLOBS = [
    ("paper/tables", "*.md"),
    ("data/runsets", "*.json"),
]
ASSET_FILES = [
    "data/processed/fault_matrix.json", "data/processed/fault_matrix_v2.json",
    "data/processed/fault_matrix_v3.json", "data/processed/fault_matrix_v4.json",
    "data/processed/fault_matrix_holdout.json", "data/processed/fault_matrix_n03.json",
    "data/processed/fault_matrix_n03adv.json", "data/processed/fault_baseline.json",
    "data/processed/ir/overlap_threshold.json", "data/processed/ir/seal_access.jsonl",
    "paper/verdicts.yaml",
]
FIGURE_DATA = "paper/figures/data/concept_values.json"
SUPPLEMENTARY = ("paper/supplementary", "S*.md")

# 식별자만 내보내는 parquet → CSV. **원문 열은 구조적으로 존재하지 않는다.**
QREL_EXPORTS = [
    ("data/processed/ir/split.parquet", "split.csv"),
    ("data/processed/ir/qrel_examiner.parquet", "qrel_examiner.csv"),
    ("data/processed/ir/qrel_test_sealed.parquet", "qrel_test_sealed.csv"),
    ("data/processed/ir/qrel_b_sealed.parquet", "qrel_b_sealed.csv"),
    ("data/processed/ir/qrel_family_merged.parquet", "qrel_family_merged.csv"),
]
TEXTY = re.compile(r"text|abstract|claim|title|body|content", re.I)

# ── 제외 목록과 사유 (내역 ②) ───────────────────────────────────────────────────
EXCLUDED = [
    ("data/raw/ · data/interim/ · data/processed/ 원문 계열",
     "KIPRIS 학술이용 조건상 재배포 불가. 식별자와 재인출 절차로 대체한다"),
    ("src/sdkb_paper/explore/ (6 파일)", "내부 뷰어 — 재현에 쓰이지 않는다"),
    ("src/sdkb_paper/collect/ 나머지 (kipris_client·bq_cpc·dart·collect·b_layer)",
     "§4 경로가 호출하지 않는다. 재인출은 상류 scripts/refetch_rejected_patents.py 가 담당한다"),
    ("src/sdkb_paper/analysis/{census,s1_coverage*,s2_timeseries*,applicant_cli,ksia_strata_cli,robustness_cli}",
     "구 커버리지 패러다임 산출물 — 현 원고가 인용하지 않는다"),
    ("01.code_spec/ · upstream/ · paper/ 원고 정본",
     "감사 기록이며 재현물이 아니다. 사전등록 대응은 supplementary S6 이 담당한다"),
    ("tests/ (54 파일)", "지문 검사를 통과한 것만 선별 반입한다 — 이번 판에서는 반입하지 않는다"),
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def head() -> str:
    try:
        return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return ""


def code_sources() -> list[tuple[Path, str]]:
    out = []
    for pkg, mods in CODE.items():
        for m in mods:
            name = m if m.endswith(".py") else f"{m}.py"
            src = SRC / pkg / name if pkg else SRC / name
            rel = f"src/sdkb_paper/{pkg}/{name}" if pkg else f"src/sdkb_paper/{name}"
            out.append((src, rel))
    for e in EXTRA_CODE:
        out.append((SRC / e, f"src/sdkb_paper/{e}"))
    return out


def asset_sources() -> list[tuple[Path, str]]:
    out = []
    for d, pat in ASSET_GLOBS:
        for p in sorted((ROOT / d).glob(pat)):
            out.append((p, f"assets/{p.name}"))
    for f in ASSET_FILES:
        out.append((ROOT / f, f"assets/{Path(f).name}"))
    out.append((ROOT / FIGURE_DATA, "figures/data/concept_values.json"))
    # 진입 문서 — 산문은 사람이 쓰고(docs/benchmark/README.md) 생성기는 옮기기만 한다.
    out.append((ROOT / "docs" / "benchmark" / "README.md", "README.md"))
    for p in sorted((ROOT / SUPPLEMENTARY[0]).glob(SUPPLEMENTARY[1])):
        out.append((p, f"supplementary/{p.name}"))
    return out


def export_qrels(out: Path) -> list[str]:
    """parquet → 식별자 CSV. **원문 계열 열이 있으면 멈춘다** — 통과시키지 않는다."""
    import pandas as pd
    written = []
    for src, name in QREL_EXPORTS:
        p = ROOT / src
        if not p.exists():
            print(f"      건너뜀(부재): {src}")
            continue
        df = pd.read_parquet(p)
        bad = [c for c in df.columns if TEXTY.search(str(c))]
        if bad:
            raise SystemExit(f"ERROR: {src} 에 원문 계열 열 {bad} — 내보내지 않는다")
        dst = out / "assets" / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        df.sort_values(list(df.columns)).to_csv(dst, index=False)
        written.append(f"assets/{name}")
    return written


def crosswalk() -> str:
    """원고 §4 표의 코드 열을 읽어 대응표를 만든다 — 손으로 옮겨 적지 않는다."""
    man = (ROOT / "paper" / "submission" / "manuscript.md").read_text(encoding="utf-8")
    rows = []
    for line in man.splitlines():
        if line.startswith("|") and "`" in line and ".py" in line:
            cells = [c.strip() for c in line.strip("|").split("|")]
            mod = next((c for c in cells if ".py" in c), None)
            if mod:
                rows.append((cells[0], mod, cells[-1]))
    body = "\n".join(f"| {a} | {b} | `benchmark/src/sdkb_paper/` 하위 | {c} |" for a, b, c in rows)
    return ("# CROSSWALK — 원고 §4 표의 코드 진입점과 공개 경로\n\n"
            "**이 표는 생성기가 만든다**(`scripts/export_benchmark.py`). 원고의 표가 바뀌면 다시 조립한다.\n\n"
            "| 구성 | 원고가 적은 진입점 | 공개 트리 접두어 | 산출 순위 파일 |\n|---|---|---|---|\n"
            + body + "\n")


def excluded_doc() -> str:
    rows = "\n".join(f"| `{a}` | {b} |" for a, b in EXCLUDED)
    return ("# EXCLUDED — 싣지 않은 것과 사유\n\n"
            "**빠진 것이 은폐가 아니라 결정임을 보이는 목록이다.** 목록 없이 빠지면 누락으로 읽힌다.\n\n"
            "| 대상 | 사유 |\n|---|---|\n" + rows + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--check", action="store_true", help="쓰지 않고 MANIFEST 대조만 한다")
    a = ap.parse_args()
    out: Path = a.out.expanduser()

    pairs = code_sources() + asset_sources()
    missing = [rel for src, rel in pairs if not src.exists()]
    if missing:
        for m in missing[:10]:
            print(f"ERROR: 원본 없음 {m}", file=sys.stderr)
        return 2

    if a.check:
        mf = out / "MANIFEST.json"
        if not mf.exists():
            print(f"FAIL: {mf} 가 없다", file=sys.stderr)
            return 1
        cur = json.loads(mf.read_text(encoding="utf-8"))
        drift = [rel for src, rel in pairs
                 if cur["files"].get(rel, {}).get("sha256") != sha256(src)]
        if drift:
            for d in drift[:20]:
                print(f"FAIL: 원본과 공개본이 다르다 — {d}", file=sys.stderr)
            print(f"FAIL: 총 {len(drift)}건", file=sys.stderr)
            return 1
        print(f"[bench] 대조 통과 · 코드·자산 {len(pairs)}건")
        return 0

    if out.exists():
        shutil.rmtree(out)
    files: dict[str, dict] = {}
    for src, rel in pairs:
        dst = out / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        files[rel] = {"sha256": sha256(src), "bytes": src.stat().st_size,
                      "source": str(src.relative_to(ROOT))}
    for rel in export_qrels(out):
        p = out / rel
        files[rel] = {"sha256": sha256(p), "bytes": p.stat().st_size,
                      "source": "parquet → 식별자 CSV (원문 열 없음을 검사기가 강제)"}

    (out / "CROSSWALK.md").write_text(crosswalk(), encoding="utf-8")
    (out / "EXCLUDED.md").write_text(excluded_doc(), encoding="utf-8")
    manifest = {
        "_README": "평가 하네스의 이관 내역. 생성기: scripts/export_benchmark.py (논문 리포). "
                   "이 디렉터리는 상류에서 편집하지 않는다 — 편집하면 사본이 갈린다.",
        "producer_repo": "sdkb-prior-art-paper",
        "producer_commit": head(),
        "files_count": len(files),
        "files": dict(sorted(files.items())),
    }
    (out / "MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[bench] {out} · 파일 {len(files)}건 · commit {manifest['producer_commit'][:7]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
