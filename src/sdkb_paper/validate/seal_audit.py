"""봉인 열람 감사 — 기본은 **거부**, 열면 원장에 남는다 (PLAN-047 §13.3 · G7).

**왜 이 모듈이 있는가.** 판독 B 의 순서는 "run 을 먼저 만들고, 그 다음에 봉인을 연다"이다
(PLAN-047 §5 G7). 그런데 순서를 사람의 기억에 맡기면 지켜졌는지 사후에 증명할 수 없고,
한 번 열린 봉인은 되돌릴 수 없다. 그래서 순서를 **프로그램이 지키게** 한다 —

- 봉인 파일을 여는 유일한 통로는 `open_sealed()` 이고 **기본 인자는 거부**다.
- 여는 데에는 명시적 `allow=True`(CLI `--unseal`)와 **사유 문자열**이 필요하다.
- 열린 사실은 `config.SEAL_ACCESS_LOG` 에 **추가전용 1행**으로 남는다(시각·커밋·호출자·
  파일 sha256·사유·층·분할). 배관 검증이 끝난 시점에 이 원장이 **0행**이면 "열람 0회"가
  증명되고, 개봉 후에는 정확히 **1행**이어야 한다.

**층이 둘이고 규율이 다르다 (2026-08-24 · PLAN-076 · O-6).** B층(`qrel_b_sealed.parquet`)은
**허가 없이는 열리지 않고**, A층(`qrel_test_sealed.parquet`)은 **이미 1회 공표 개봉됐으므로
막지 않되 기록한다**. 두 층을 한 원장에 담으므로 `layer` 필드가 그 둘을 가른다 — 이 필드가
없으면 CLAUDE.md §0.8 이 요구하는 **층 한정 진술**을 사람이 파일명으로 역추론하게 된다.
**PLAN-076 이전에 쌓인 25행은 전량 B층이며 `layer` 필드가 없다** — `access_log()` 가 경로로
보정해 돌려주고, **원장의 기존 행은 고쳐 쓰지 않는다**(추가전용).

**이 모듈은 파일을 읽지 않는다** — 경로를 돌려줄 뿐이고, 해시는 바이트를 스트리밍해 계산한다.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .. import config


class SealedAccessError(RuntimeError):
    """봉인 파일을 허가 없이 열려 했다 — 사전등록 순서 위반."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _commit() -> str | None:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=config.ROOT,
                             capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _caller() -> str:
    """호출자 모듈:함수 — 누가 열었는지 원장이 지목할 수 있어야 한다."""
    for frame in inspect.stack()[1:]:
        mod = frame.frame.f_globals.get("__name__", "")
        if mod != __name__:
            return f"{mod}:{frame.function}"
    return "unknown"


def access_log() -> list[dict]:
    """원장 전량(없으면 빈 리스트). G7 증거 판독용.

    `layer` 가 없는 구 행(PLAN-076 이전 25행)은 **파일 경로로 보정**해 돌려준다 — 디스크의
    행은 고치지 않는다(추가전용).
    """
    path = Path(config.SEAL_ACCESS_LOG)
    if not path.exists():
        return []
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    for r in rows:
        if "layer" not in r:
            r["layer"] = "A" if str(r.get("file", "")).endswith(
                Path(config.IR_QREL_TEST_SEALED).name) else "B"
    return rows


def open_sealed(path: Path, *, reason: str, allow: bool,
                layer: str = "B", split: str | None = None) -> Path:
    """봉인 파일 경로를 돌려준다 — `allow=False` 면 열지 않고 예외를 던진다.

    반환값은 경로일 뿐이며 읽기는 호출자가 한다. 그럼에도 이 함수를 "여는 통로"라 부르는
    이유는, 봉인 경로가 **여기를 거치지 않고는 소비자에게 도달하지 않도록** 배선했기
    때문이다(`analysis.metrics.load_qrel_for_split`).

    `layer` 는 `"A"`(공표 개봉된 A층 test) 또는 `"B"`(판독 B 봉인)이고, `split` 은 그 접근이
    어느 분할을 읽었는지다. **A층 호출도 사유는 필수다** — 막지 않는 것과 익명으로 여는 것은
    다르다(PLAN-076 §8.2).
    """
    path = Path(path)
    if not allow:
        raise SealedAccessError(
            f"봉인 파일 열람 거부: {path.name} — 개봉은 사전등록(PLAN-047) 동결 커밋 이후 "
            f"`--unseal` 로만 한다. 사유='{reason}'"
        )
    if not reason.strip():
        raise SealedAccessError("개봉에는 사유가 필요하다 — 빈 사유로는 열지 않는다")
    rec = {
        "opened_at": _now(),
        "commit": _commit(),
        "caller": _caller(),
        "file": str(path.relative_to(config.ROOT)) if path.is_relative_to(config.ROOT) else str(path),
        "sha256": sha256_file(path) if path.exists() else None,
        "reason": reason,
        "layer": layer,
        "split": split,
    }
    log = Path(config.SEAL_ACCESS_LOG)
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    verb = "봉인 개봉 기록" if layer == "B" else "A층 열람 기록"
    print(f"🔓 {verb} → {log} · {rec['file']} · 사유={reason}")
    return path
