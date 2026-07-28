"""누출 감사 단일 진입점 (PLAN-017 B6 · PLAN-018 §4 · PLAN-019 W3 · 원고 §4.5·§5.6·§10).

**왜 조립 시점 검사만으로는 부족한가.** `corpus/assemble.py` 는 코퍼스를 만들 때 금지 술어를
질의하지 않는다(FORBIDDEN 상수). 그러나 순위 산출은 그 뒤에도 여러 자원을 더 읽는다 — 개념축·
claim-feature sidecar·family 지도·후보 마스크. 조립이 깨끗해도 **런타임 피처 생성 시점**에
정답 파생 정보가 되돌아올 수 있다. 이 모듈은 그 잔여를 독립적으로 재검증하고, 하나라도 걸리면
비영 종료한다(우회 경로를 만들지 않는다 · CLAUDE.md §5).

네 검사:

- **L-1 코퍼스 피처** — IR 코퍼스의 컬럼명·개념값에 금지 술어(`hasPriorArt*`·`overPriorArt`·
  `NoveltyScore`) 유래 흔적이 0 인가.
- **L-2 런타임 피처 자원** — 개념축·feature sidecar 의 컬럼에 금지 술어 유래·qrel 파생
  (`relevance`·`qrel`·`is_positive` 류) 컬럼이 0 인가.
- **L-3 run 마스크 잔여** — 산출된 run 상위 K 에 F10 위반(자기 자신·동일 패밀리·시점 미래)이
  0 인가. 마스크가 코드에 있다는 것과 산출물이 실제로 지켜졌다는 것은 다른 명제다.
- **L-4 qrel 봉인 상태** — qrel 파일 sha256 과 봉인 test qrel 존재 여부를 기록한다(차단 아님·기록).

- **경계:** 이 모듈은 데이터를 고치지 않는다. 판정하고 보고할 뿐이다(CLAUDE.md §3).

CLI: `python -m sdkb_paper.validate.leakage_check [--split dev] [--k 100]`  → 위반 시 exit 1.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

from .. import config

# 문서 피처로 절대 들어오면 안 되는 누출원 (corpus/assemble.FORBIDDEN 과 같은 목록 · 단일 정의).
from ..corpus.assemble import FORBIDDEN

# qrel 에서 파생된 값임을 드러내는 컬럼명 조각. 피처 자원에 있으면 정답이 새어든 것이다.
QREL_DERIVED = ("relevance", "qrel", "is_positive", "prior_art", "priorart", "cited_by_examiner")


def _norm(s: str) -> str:
    return s.replace("_", "").replace("-", "").lower()


def check_names(names: list[str], forbidden: tuple[str, ...] = FORBIDDEN) -> list[str]:
    """이름 목록(컬럼·필드)에서 금지 술어 유래 항목을 찾는다. 대소문자·구분자 무시."""
    bad = []
    for n in names:
        nn = _norm(str(n))
        if any(_norm(f) in nn for f in forbidden):
            bad.append(str(n))
    return bad


def check_qrel_derived(names: list[str]) -> list[str]:
    """qrel 파생 컬럼(정답 라벨 그 자체)이 피처 자원에 섞였는지."""
    return check_names(names, QREL_DERIVED)


def check_concept_values(values: list[str]) -> list[str]:
    """개념 링크 값에 금지 술어 유래 IRI/지역명이 섞였는지 (샘플이 아니라 전량 검사)."""
    return sorted(set(check_names(values)))


def check_run_mask(run: dict[str, list[str]], is_allowed, k: int = 100) -> list[dict]:
    """run 상위 K 의 F10 위반 목록. 빈 목록 = 통과.

    `is_allowed(qid, doc_id) -> bool` 은 `retrieval.candidate.CandidateMask.is_allowed` 를 받는다
    (analysis 가 마스크를 재구현하지 않는다 — 정본은 retrieval 쪽 하나뿐).
    """
    viol = []
    for qid, ranked in run.items():
        for rank, doc in enumerate(ranked[:k], start=1):
            if not is_allowed(qid, doc):
                viol.append({"query_id": qid, "doc_id": doc, "rank": rank})
    return viol


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --- 파일을 실제로 여는 층 (테스트는 위의 순수 함수를 때린다) -------------------

def audit_corpus() -> dict:
    """L-1: IR 코퍼스 컬럼·개념값."""
    import pandas as pd

    df = pd.read_parquet(config.IR_CORPUS)
    bad_cols = check_names(list(df.columns))
    vals: list[str] = []
    if "concepts" in df.columns:
        for c in df["concepts"]:
            if c is not None:
                vals.extend(str(x) for x in c)
    bad_vals = check_concept_values(vals)
    return {"check": "L-1 코퍼스 피처", "n_rows": len(df), "n_cols": len(df.columns),
            "bad_columns": bad_cols, "bad_concept_values": bad_vals,
            "pass": not bad_cols and not bad_vals}


def audit_feature_sources() -> dict:
    """L-2: 런타임 피처 자원(개념축·claim-feature sidecar)."""
    import pandas as pd

    bad: dict[str, list[str]] = {}
    checked = []
    for name, path in (("concept_axis", config.IR_CONCEPT_AXIS),
                       ("feature_sidecar", config.IR_FEATURE_SIDECAR)):
        if not Path(path).exists():
            continue
        cols = list(pd.read_parquet(path).columns)
        checked.append(name)
        hits = check_names(cols) + check_qrel_derived(cols)
        if hits:
            bad[name] = sorted(set(hits))
    return {"check": "L-2 런타임 피처 자원", "checked": checked, "bad_columns": bad,
            "pass": not bad}


def audit_runs(split: str, k: int = 100) -> dict:
    """L-3: 동결 run 상위 K 의 F10 마스크 잔여."""
    from ..analysis.metrics import load_run
    from ..analysis.results_table import SYSTEM_LABELS, run_path
    from ..retrieval.candidate import CandidateMask

    mask = CandidateMask()
    rows, total_viol = [], 0
    for sysname, _label in SYSTEM_LABELS:
        p = run_path(sysname, split)
        if not p.exists():
            continue
        viol = check_run_mask(load_run(p), mask.is_allowed, k)
        total_viol += len(viol)
        rows.append({"system": sysname, "run": p.name, "violations": len(viol),
                     "examples": viol[:3]})
    return {"check": f"L-3 run 마스크 잔여 (top-{k} · split={split})", "systems": rows,
            "n_violations": total_viol, "n_runs": len(rows), "pass": total_viol == 0}


def audit_qrel() -> dict:
    """L-4: qrel 해시·봉인 상태 기록(차단하지 않는다 — 증거 기록이 목적)."""
    out = {"check": "L-4 qrel 봉인·해시", "pass": True}
    for key, path in (("qrel_examiner", config.QREL_EXAMINER),
                      ("qrel_test_sealed", config.IR_QREL_TEST_SEALED)):
        out[key] = {"exists": Path(path).exists(),
                    "sha256": sha256_file(path) if Path(path).exists() else None}
    return out


def run_audit(split: str = "dev", k: int = 100) -> dict:
    checks = [audit_corpus(), audit_feature_sources(), audit_runs(split, k), audit_qrel()]
    return {"split": split, "k": k, "checks": checks,
            "pass": all(c["pass"] for c in checks)}


def format_report(res: dict) -> str:
    lines = [f"[leakage_check] split={res['split']} · top-{res['k']}",
             "─" * 60]
    for c in res["checks"]:
        lines.append(f"  {'✅' if c['pass'] else '❌'} {c['check']}")
        for key in ("bad_columns", "bad_concept_values"):
            if c.get(key):
                lines.append(f"       {key}: {c[key]}")
        if "n_violations" in c:
            lines.append(f"       위반 {c['n_violations']}건 · 검사 run {c['n_runs']}개")
            for row in c["systems"]:
                if row["violations"]:
                    lines.append(f"       - {row['system']}: {row['violations']}건 "
                                 f"예 {row['examples']}")
        if c["check"].startswith("L-4"):
            for key in ("qrel_examiner", "qrel_test_sealed"):
                v = c[key]
                lines.append(f"       {key}: exists={v['exists']} sha256="
                             f"{(v['sha256'] or '')[:16]}")
    lines.append("─" * 60)
    lines.append(f"  누출 감사 = {'PASS (금지간선 잔여 0)' if res['pass'] else 'FAIL'}")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "dev", "test", "all"], default="dev")
    ap.add_argument("--k", type=int, default=100)
    args = ap.parse_args()
    res = run_audit(args.split, args.k)
    print(format_report(res))
    sys.exit(0 if res["pass"] else 1)


if __name__ == "__main__":
    main()
