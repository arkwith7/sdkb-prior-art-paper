"""SDKB 온톨로지 스냅샷 vendoring.

근간 온톨로지(semiconductor-knowledge-base)를 이 repo 로 **얼려서** 가져온다.
살아있는 워킹트리를 참조하지 않는 이유:

1. H1(보강 전/후 커버리지 비교)의 baseline 이 움직이면 재현이 불가능하다.
2. 필요한 TTL(sdkb-core.ttl, sdkb-core-data.ttl)은 SDKB repo 의 .gitignore 대상 —
   즉 git 에 없는 **빌드 산출물**이다. submodule/pip 로는 가져올 수 없고,
   SDKB 쪽에서 `make owl convert` 로 생성한 결과를 복사하는 수밖에 없다.

그래서 스냅샷을 `data/external/sdkb/` 에 커밋하고, 출처(커밋 SHA)와 무결성(sha256)을
PROVENANCE.json 에 박아둔다. SDKB 를 갱신하려면 이 스크립트를 재실행하고 MANIFEST 를 갱신한다.

라이선스: SDKB 는 CDLA-Permissive-2.0 — 재배포 가능. (KIPRIS 원문 금지 규칙과 무관)

CLI:  python -m sdkb_paper.ontology.vendor [--sdkb-home PATH]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from sdkb_paper.config import EXTERNAL_SDKB, SDKB_HOME

# vendor 대상: (SDKB 내 상대경로, 역할)
#
# SIRP 특허 ABox(sdkb-abox-patents.ttl)를 **포함한다**. 예전에는 baseline 을 특허 0건으로
# 두려고 제외했지만, 그러면 모든 공정 단계에서 C₀(s)=0 이 되어 H1 이 기각될 수 없는 자명한
# 가설이 된다. G₀ 는 "현행 SDKB" 여야 한다 (CLAUDE.md §0).
VENDOR_FILES: list[tuple[str, str]] = [
    ("ontology/sdkb-core.ttl", "TBox: 제조 코어(Process/SubProcess/Equipment/Material/Device/FailureMode)"),
    ("ontology/sdkb-patent.ttl", "TBox: 특허 모듈(Patent/IPC/realizesProcess/concernsDevice)"),
    ("ontology/sdkb-foresight.ttl", "TBox: 예측 모듈(Scenario/Signal/STEEPVE) — H2 의 기반"),
    ("ontology/sdkb-core-data.ttl", "ABox: 도메인 인스턴스 (공정 20 · 디바이스 31 …)"),
    ("ontology/sdkb-abox-patents.ttl", "ABox: SIRP 거절특허 1,000건 — H1 의 before 를 구성한다"),
    ("data/semiconductor_v0_3.json", "ABox 의 커밋된 원천(=재현 기준점)"),
    ("data/schema_report.json", "원천의 sha256 + 노드/엣지 카운트"),
]

# 산출물이 커밋된 원천과 정합한지 확인하는 기준
SOURCE_JSON = "data/semiconductor_v0_3.json"
SCHEMA_REPORT = "data/schema_report.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(sdkb_home: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(sdkb_home), *args],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


def _verify_source(sdkb_home: Path) -> dict:
    """빌드 산출물이 커밋된 원천 JSON 에서 나온 것인지 검증.

    schema_report.json 에 기록된 sha256 != 실제 JSON sha256 이면, 산출물이 낡았거나
    원천이 바뀐 것 — 그대로 vendor 하면 출처가 거짓이 된다.
    """
    src = sdkb_home / SOURCE_JSON
    report = json.loads((sdkb_home / SCHEMA_REPORT).read_text(encoding="utf-8"))
    actual, recorded = sha256(src), report["file_sha256"]
    if actual != recorded:
        raise SystemExit(
            f"[vendor] 원천 불일치: {SOURCE_JSON} 의 sha256={actual[:12]}… 인데 "
            f"schema_report 기록은 {recorded[:12]}… 이다.\n"
            f"         SDKB 에서 `make owl convert` 로 산출물을 다시 빌드한 뒤 재실행할 것."
        )
    return report


def verify_snapshot(dest: Path = EXTERNAL_SDKB) -> list[str]:
    """커밋된 스냅샷이 PROVENANCE.json 의 sha256 과 여전히 일치하는지 검사.

    SDKB 원본이 필요 없다 — 커밋된 파일만 본다. 그래서 CI 에서 매 push 마다 돌 수 있다.
    스냅샷이 제자리에서 수정되면(누가 TTL 을 손으로 고치면) baseline 의 출처가 거짓이 되고
    H1 의 before 가 조용히 움직인다. 이 검사가 그걸 막는다.

    문제 목록을 반환한다 (빈 리스트 = 정상).
    """
    prov_path = dest / "PROVENANCE.json"
    if not prov_path.exists():
        return [f"PROVENANCE.json 이 없다: {prov_path} — `make vendor` 를 먼저 실행할 것."]

    prov = json.loads(prov_path.read_text(encoding="utf-8"))
    problems = []
    for entry in prov["files"]:
        f = dest / entry["file"]
        if not f.exists():
            problems.append(f"{entry['file']}: 스냅샷에 파일이 없다")
            continue
        actual = sha256(f)
        if actual != entry["sha256"]:
            problems.append(
                f"{entry['file']}: sha256 불일치 — 기록 {entry['sha256'][:12]}… / 실제 {actual[:12]}…"
            )

    # PROVENANCE 가 모르는 TTL 이 스냅샷에 섞여 있으면 baseline 이 조용히 오염될 수 있다.
    known = {e["file"] for e in prov["files"]} | {"PROVENANCE.json"}
    for stray in sorted(p.name for p in dest.glob("*.ttl") if p.name not in known):
        problems.append(f"{stray}: PROVENANCE 에 없는 파일이 스냅샷에 있다 (SIRP ABox 유입?)")

    return problems


def vendor(sdkb_home: Path = SDKB_HOME, dest: Path = EXTERNAL_SDKB) -> Path:
    if not (sdkb_home / ".git").exists():
        raise SystemExit(f"[vendor] SDKB git repo 를 찾을 수 없음: {sdkb_home}")

    missing = [rel for rel, _ in VENDOR_FILES if not (sdkb_home / rel).exists()]
    if missing:
        raise SystemExit(
            "[vendor] SDKB 에 다음 파일이 없음 (빌드 산출물은 git 에 없다):\n  "
            + "\n  ".join(missing)
            + f"\n\n  cd {sdkb_home} && make owl convert   # 를 먼저 실행할 것"
        )

    report = _verify_source(sdkb_home)
    commit = _git(sdkb_home, "rev-parse", "HEAD")
    dirty = bool(_git(sdkb_home, "status", "--porcelain"))

    dest.mkdir(parents=True, exist_ok=True)
    files = []
    for rel, role in VENDOR_FILES:
        out = dest / Path(rel).name
        shutil.copy2(sdkb_home / rel, out)
        files.append({"file": out.name, "source_path": rel, "role": role, "sha256": sha256(out)})

    prov = {
        "source_repo": _git(sdkb_home, "remote", "get-url", "origin"),
        "source_commit": commit,
        "source_commit_date": _git(sdkb_home, "log", "-1", "--format=%cI", commit),
        "source_dirty": dirty,
        "source_license": "CDLA-Permissive-2.0",
        "vendored_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "baseline_counts": report["counts"],
        "excluded": {},
        "files": files,
    }
    (dest / "PROVENANCE.json").write_text(
        json.dumps(prov, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"[vendor] {len(files)} files -> {dest}")
    print(f"[vendor] source commit = {commit[:12]}{'  ⚠ DIRTY WORKTREE' if dirty else ''}")
    if dirty:
        print("[vendor] ⚠ SDKB 워킹트리에 커밋되지 않은 변경이 있다 — 스냅샷의 출처가 "
              "커밋 SHA 만으로 재현되지 않는다. SDKB 를 먼저 커밋할 것.", file=sys.stderr)
    return dest


def main() -> None:
    ap = argparse.ArgumentParser(description="SDKB 온톨로지 스냅샷을 data/external/sdkb/ 로 vendor")
    ap.add_argument("--sdkb-home", type=Path, default=SDKB_HOME)
    ap.add_argument(
        "--verify", action="store_true",
        help="스냅샷 무결성만 검사한다 (SDKB 원본 불필요 — CI 게이트용). 갱신하지 않는다.",
    )
    args = ap.parse_args()

    if args.verify:
        problems = verify_snapshot()
        for p in problems:
            print(f"[vendor] ✗ {p}", file=sys.stderr)
        if problems:
            print(
                "[vendor] 스냅샷이 PROVENANCE 와 어긋난다 — baseline 의 출처가 거짓이 된다.\n"
                "         의도한 갱신이라면 `make vendor` 로 PROVENANCE 를 재작성하고 "
                "data/MANIFEST.md 에 새 줄을 추가할 것.",
                file=sys.stderr,
            )
            sys.exit(1)
        prov = json.loads((EXTERNAL_SDKB / "PROVENANCE.json").read_text(encoding="utf-8"))
        print(
            f"[vendor] ✓ 스냅샷 무결 — {len(prov['files'])} files, "
            f"SDKB commit {prov['source_commit'][:12]}"
        )
        return

    vendor(args.sdkb_home)


if __name__ == "__main__":
    main()
