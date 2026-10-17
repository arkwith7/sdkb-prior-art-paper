"""파일럿 별도 고정 자산 반입 — PLAN-096 D2 (사용자 승인 2026-10-17).

주 스냅샷(`data/external/sdkb/`)과 **분리된** 디렉터리 `config.EXTERNAL_PILOT` 에 다음을 얼린다.

1. 상류 논증층 `ontology/sdkb-abox-argument.ttl` — 판단 지식 파생의 원천(비커밋 · 심사 기록 파생).
2. 상류 `mappings/ipc_concordance.csv` — 이식 에뮬레이터의 IPC 판 대응표(커밋).
3. 이식 동등성 기준값 — 상류 dev 실행 로그(`data/queries/t4_dev_v1/dev_{b,d}.jsonl`)의 검색식을
   **상류 에뮬레이터 그대로**(자기 문서만 제외 · 마스크 없음) 다시 실행한 결과 집합의 해시(비커밋).

`PROVENANCE.json`(커밋)에는 상류 코드·입력 버전 · 생성 명령 · 파일 해시 · **품질 상태** · 사용 범위 ·
지식 파생 규칙을 적는다.

**상류 저장소는 이 명령을 사람이 실행할 때만 읽는다**(CLAUDE.md §0.1). 파일럿 실행 코드는 이 디렉터리만 읽는다.
주 스냅샷 PROVENANCE 는 건드리지 않으므로 §2.1 은 발동하지 않는다(PLAN-096 D2 적용 범위).

CLI:  python -m sdkb_paper.ontology.vendor_pilot [--sdkb-home PATH]
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from sdkb_paper import config

ARGUMENT_SRC = Path("ontology") / "sdkb-abox-argument.ttl"
ARGUMENT_REPORT = Path("data") / "reports" / "abox_argument_report.json"
CONCORDANCE_SRC = Path("mappings") / "ipc_concordance.csv"
EMULATOR_SRC = Path("scripts") / "kipris_emulator.py"
AGENT_SRC = Path("scripts") / "llm_query_agent.py"
DEV_LOGS = (Path("data") / "queries" / "t4_dev_v1" / "dev_b.jsonl",
            Path("data") / "queries" / "t4_dev_v1" / "dev_d.jsonl")
NOTICE_DIR = Path("data") / "sources" / "opinion_notices" / "txt"
# 상류 동결 명세의 코퍼스 sha — 하류 IR_CORPUS 와 같아야 기준값이 성립한다.
EXPECTED_CORPUS_SHA = "d856269392bdad5222cf5f87cadade0f66b6c9d842c6205c208845f4fc7be51e"

# 사용 범위(PLAN-096 D3 승인 조건 ④) — 사람 대조 r6 에서 문턱을 넘은 종류만.
ALLOWED_PREDICATES = ("judgesClaim", "judgmentScope", "onGround", "hasRationale",
                      "reliesOnCommonKnowledge", "supportedBy", "includesDocument", "assertedIn")
EXCLUDED_PREDICATES = ("locator", "locatorType", "locatorValue", "partOfJudgment", "inDocument",
                       "refersToJudgment", "categoryVariantOf")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _git(home: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(home), *args], capture_output=True, text=True,
                          check=True).stdout.strip()


def _dir_digest(d: Path) -> dict:
    """입력 디렉터리의 내용 해시 — 파일명은 싣지 않는다(상류 규칙: 통지서 파일명 비공개)."""
    if not d.exists():
        return {"present": False}
    hs = sorted(sha256_file(p) for p in d.rglob("*") if p.is_file())
    return {"present": True, "files": len(hs),
            "content_digest": hashlib.sha256("".join(hs).encode()).hexdigest()}


def _quality(report: dict) -> dict:
    """품질 상태 — 상류 리포트의 사람 대조 결과를 그대로 옮기고 사용 범위를 정한다."""
    r6 = report.get("human_gate_r6", {}).get("by_kind", {})
    kinds = {k: {f: v.get(f) for f in ("judged", "correct", "rate", "pass", "decidable")}
             for k, v in r6.items()}
    return {
        "status": "이전 FAIL 산출물(전체 사람 대조 FAIL 보존) — 교정본 아님 · 검증된 부분집합 아님",
        "human_gate_r6_pass": report.get("human_gate_r6", {}).get("pass"),
        "human_gate_r6_by_kind": kinds,
        "limited_variant": {
            "sha256": report.get("limited", {}).get("output_sha256"),
            "note": "좌표·관계를 뺀 별도 산출물 — 상류 리포트가 '검증을 받은 것이 아니다'라고 적는다 · 반입하지 않는다",
        },
        "use_scope": "r6 에서 문턱을 넘은 종류(판단 블록 · 설계변경 · 예측가능 효과)와 그 구조 필드만 쓴다. "
                     "좌표(locator 0.80 FAIL)와 판단 간 관계(판정 불가)는 쓰지 않는다.",
        "allowed_predicates": list(ALLOWED_PREDICATES),
        "excluded_predicates": list(EXCLUDED_PREDICATES),
        "free_text": "없음 — 리터럴은 라이선스·출처 표기·위치 값·공지기술 플래그뿐(2026-10-17 길이 계수)",
    }


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def build_parity(home: Path) -> dict:
    """상류 에뮬레이터로 상류 dev 로그의 검색식을 다시 돌려 결과 집합 해시를 남긴다(마스크 없음)."""
    import pandas as pd

    if sha256_file(config.IR_CORPUS) != EXPECTED_CORPUS_SHA:
        raise SystemExit("ERROR: 하류 IR_CORPUS 가 상류 동결 코퍼스와 다르다 — 기준값이 성립하지 않는다")
    up = _load_module(home / EMULATOR_SRC, "_upstream_kipris_emulator")
    cols = ["doc_id", "is_candidate", "title", "abstract", "claims_full", "claims_independent", "ipc"]
    corpus = pd.read_parquet(config.IR_CORPUS, columns=cols)
    emu = up.Emulator(corpus, up.Concordance(home / CONCORDANCE_SRC))
    seen, rows, size_mismatch = set(), [], 0
    for log in DEV_LOGS:
        for line in (home / log).read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            for e in r.get("log", []):
                if "query" not in e or "error" in e or e.get("size") is None:
                    continue
                ipc = tuple(e.get("ipc") or ())
                key = (r["q"], e["query"], ipc)
                if key in seen:
                    continue
                seen.add(key)
                res = emu.run(e["query"], ipc=list(ipc) or None, exclude=(r["q"],))
                if len(res) != e["size"]:
                    size_mismatch += 1
                rows.append({"q": r["q"], "query": e["query"], "ipc": list(ipc), "n": len(res),
                             "logged_size": e["size"],
                             "sha256": hashlib.sha256("\n".join(sorted(res)).encode()).hexdigest()})
    rows.sort(key=lambda x: (x["q"], x["query"], x["ipc"]))
    return {"rows": rows, "n_queries": len(rows), "logged_size_mismatch": size_mismatch}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sdkb-home", type=Path, default=config.SDKB_HOME)
    a = ap.parse_args(argv)
    home = a.sdkb_home.resolve()
    out = config.EXTERNAL_PILOT
    out.mkdir(parents=True, exist_ok=True)

    report = json.loads((home / ARGUMENT_REPORT).read_text(encoding="utf-8"))
    src_ttl = home / ARGUMENT_SRC
    ttl_sha = sha256_file(src_ttl)
    if ttl_sha != report.get("output_sha256"):
        raise SystemExit("ERROR: 논증층 TTL 의 sha 가 상류 리포트 output_sha256 과 다르다 — 리포트와 파일이 어긋난다")
    shutil.copy2(src_ttl, config.PILOT_ARGUMENT_TTL)
    shutil.copy2(home / CONCORDANCE_SRC, config.PILOT_CONCORDANCE)

    parity = build_parity(home)
    config.PILOT_PARITY.write_text(json.dumps(parity, ensure_ascii=False, indent=0) + "\n",
                                   encoding="utf-8")

    def last(p: Path) -> str:
        return _git(home, "log", "-1", "--format=%H %cs", "--", str(p))

    prov = {
        "_README": "파일럿 별도 고정 자산(PLAN-096 D2). 주 스냅샷 data/external/sdkb/ 와 분리 — "
                   "기존 파이프라인은 이 디렉터리를 읽지 않는다. 바뀌어도 §2.1 은 발동하지 않으며, "
                   "기존 모듈이 이 디렉터리를 읽게 되면 그때 §2.1 이 다시 적용된다.",
        "vendored_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "command": "python -m sdkb_paper.ontology.vendor_pilot --sdkb-home <SDKB_HOME>",
        "upstream": {
            "head": _git(home, "rev-parse", "HEAD"),
            "branch": _git(home, "rev-parse", "--abbrev-ref", "HEAD"),
            "dirty_paths": len(_git(home, "status", "--porcelain").splitlines()),
        },
        "files": {
            "sdkb-abox-argument.ttl": {
                "source_path": str(ARGUMENT_SRC), "sha256": ttl_sha, "committed": False,
                "tracked_upstream": False,
                "note": "상류에서도 gitignore 된 빌드 산출물 — 상류 워킹트리에서 복사",
                "generated_by": {"command": "make abox-argument (scripts/build_abox_argument.py)",
                                 "script_last_commit": last(Path("scripts") / "build_abox_argument.py"),
                                 "script_sha256": sha256_file(home / "scripts" / "build_abox_argument.py"),
                                 "input": "의견제출통지서 원문(비공개) — 파일명은 싣지 않는다",
                                 "input_digest": _dir_digest(home / NOTICE_DIR),
                                 "report_sha256": sha256_file(home / ARGUMENT_REPORT)},
                "counts": report.get("counts"),
                "judgments_by_split_upstream": report.get("judgments_by_split"),
            },
            "ipc_concordance.csv": {"source_path": str(CONCORDANCE_SRC),
                                    "sha256": sha256_file(config.PILOT_CONCORDANCE),
                                    "last_commit": last(CONCORDANCE_SRC), "committed": True},
            "emulator_parity_upstream.json": {
                "sha256": sha256_file(config.PILOT_PARITY), "committed": False,
                "n_queries": parity["n_queries"],
                "logged_size_mismatch": parity["logged_size_mismatch"],
                "note": "상류 에뮬레이터를 상류와 같은 조건(자기 문서만 제외 · 마스크 없음 · TI+AB+CL)으로 "
                        "다시 실행한 결과 집합 해시. 검색식 원문을 담으므로 비커밋",
            },
        },
        "harness_port": {
            "kipris_emulator.py": {"last_commit": last(EMULATOR_SRC),
                                   "sha256": sha256_file(home / EMULATOR_SRC),
                                   "ported_to": "src/sdkb_paper/retrieval/boolean_emulator.py"},
            "llm_query_agent.py": {"last_commit": last(AGENT_SRC),
                                   "sha256": sha256_file(home / AGENT_SRC),
                                   "ported_to": "src/sdkb_paper/retrieval/agent_search.py"},
        },
        "corpus_sha256": EXPECTED_CORPUS_SHA,
        "quality": _quality(report),
        "derivation_rule": "src/sdkb_paper/ontology/judgment_items.py — PLAN-096 D3 "
                           "(심사 이력 집계 정보 · train 출원만 · 평가 질의 패밀리 제외 · 문헌 식별자 0 · 언어 분포 제외)",
    }
    config.PILOT_PROVENANCE.write_text(json.dumps(prov, ensure_ascii=False, indent=1) + "\n",
                                       encoding="utf-8")
    print(f"✓ 파일럿 자산 → {out} · 논증층 {ttl_sha[:16]} · 동등성 기준값 {parity['n_queries']}식 "
          f"(로그 건수 불일치 {parity['logged_size_mismatch']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
