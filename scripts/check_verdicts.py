#!/usr/bin/env python3
"""scripts/check_verdicts.py — 원고 판정 문구를 paper/verdicts.yaml(SSOT)과 대조한다.

용법:  python scripts/check_verdicts.py [--yaml paper/verdicts.yaml] [--root .] [--warn]
종료:  0 = 정합(또는 --warn) · 1 = 위반 발견 · 2 = 설정/입력 오류
CI:    Makefile `verdicts` 타깃 → quality-gate 에 배선 (sig-check 옆).

설계 원칙
- 검사는 '금지 문구의 부재'가 1급 시민이다. 허용 문구(composite_allowed)는 참고 경고만 낸다
  (허용형 강제는 재작성 중 오탐이 많아 게이트로 두지 않는다 — 금지형이 실질 방어선).
- 인용·코드 블록(``` fenced)은 건너뛴다: 검토보고서 인용문이 오탐을 만들지 않게.
- **언급(mention)은 사용(use)이 아니다** (CLAUDE.md §0.8). 원고는 금지 문구를 *"이렇게 쓰지
  않는다"* 형태로 자주 인용한다. 따옴표·백틱 안의 문자열은 마스킹해 위반으로 세지 않는다.
  ※ 볼드(`**...**`)는 마스킹하지 않는다 — 진짜 위반이 강조로 쓰이면 놓치기 때문이다.
- **금지 열을 가진 표는 통째로 면제**한다: §0.4·§7.6 의 결론 규칙 표와 §7 경쟁 설명 표는
  금지 문구와 경쟁 가설을 **나열하는 것이 그 표의 임무**다. 헤더 키워드로 식별한다
  (meta.exempt_tables_with_header).
- 그 외의 문맥 면제는 라벨별 `exempt_line` 정규식으로 명시한다 — 왜 면제인지 yaml 에 남는다.
- 위반 출력은 <파일>:<행>: [<라벨>] <매치 문구> 형식 — 에디터 점프 가능.
"""
from __future__ import annotations

import argparse
import glob
import re
import sys
from pathlib import Path

try:
    import yaml  # PyYAML
except ImportError:  # pragma: no cover
    print("PyYAML 필요: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


# 따옴표류 인용 — 여는/닫는 짝. 백틱은 인라인 코드.
_QUOTE_SPANS = [
    re.compile(r"`[^`\n]*`"),
    re.compile(r"“[^”\n]*”"),
    re.compile(r'"[^"\n]*"'),
    re.compile(r"「[^」\n]*」"),
    re.compile(r"'[^'\n]*'"),
]


def mask_quoted(text: str) -> str:
    """따옴표·백틱 안을 공백으로 치환(길이 보존 → 행 내 위치가 어긋나지 않는다)."""
    for rx in _QUOTE_SPANS:
        text = rx.sub(lambda m: " " * len(m.group(0)), text)
    return text


def iter_targets(root: Path, patterns: list[str]) -> list[Path]:
    files: list[Path] = []
    for pat in patterns:
        files += [Path(p) for p in glob.glob(str(root / pat), recursive=True)]
    return sorted({f for f in files if f.is_file()})


def scannable(lines: list[str], exempt_headers: list[str]) -> list[tuple[int, str, str]]:
    """검사 대상 (행번호, 마스킹본, 원문) 목록.

    제외: (a) fenced code block 내부 (b) 헤더에 면제 키워드가 있는 표의 전 행.
    마스킹본은 따옴표·백틱 안이 지워진 것(언급 면제용), 원문은 scan_raw 라벨용이다.
    """
    out: list[tuple[int, str, str]] = []  # (행번호, 마스킹본, 원문)
    in_fence = False
    table_exempt = False
    for i, line in enumerate(lines, 1):
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        is_row = stripped.startswith("|")
        if not is_row:
            table_exempt = False
        elif not table_exempt:
            # 표의 시작 행인가 — 다음 행이 구분선(|---|)이면 이 행이 헤더다.
            nxt = lines[i].lstrip() if i < len(lines) else ""
            if re.match(r"^\|[\s:|-]+\|?\s*$", nxt) and any(k in line for k in exempt_headers):
                table_exempt = True
        if table_exempt:
            continue

        out.append((i, mask_quoted(line), line))
    return out


# --- 스펙 키 엄격 검사 (PLAN-076 C-3 · O-6) ------------------------------------
# **왜 있는가.** 허용 문구 키는 `allowed` 가 아니라 `composite_allowed` 이고, 오타로 적으면
# 검사기가 그 규칙을 **조용히 무시한다** — EP5 에서 실제로 그렇게 됐다. 규칙이 없는 것과
# 규칙이 무시되는 것은 다르며, 뒤쪽은 통과처럼 보인다. 그래서 미지 키를 rc 2 로 멈춘다.
META_KEYS = frozenset({"plan", "frozen_date", "scan_targets", "exempt_tables_with_header"})
VERDICT_KEYS = frozenset({"forbidden", "composite_allowed", "exempt_line", "scan_raw", "record"})


def unknown_keys(cfg: dict) -> list[tuple[str, str]]:
    """(자리, 미지 키) 목록. 빈 목록이면 스펙의 키가 전부 알려진 것이다."""
    out: list[tuple[str, str]] = []
    out += [("meta", k) for k in (cfg.get("meta") or {}) if k not in META_KEYS]
    for label, spec in (cfg.get("verdicts") or {}).items():
        out += [(f"verdicts.{label}", k) for k in (spec or {}) if k not in VERDICT_KEYS]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--yaml", default="paper/verdicts.yaml")
    ap.add_argument("--root", default=".")
    ap.add_argument(
        "--warn",
        action="store_true",
        help="위반을 출력하되 종료코드 0 (PLAN-048 3단계 전의 경고 모드 · CLAUDE.md §2.3)",
    )
    args = ap.parse_args()

    root = Path(args.root)
    cfg_path = root / args.yaml
    if not cfg_path.exists():
        print(f"SSOT 없음: {cfg_path}", file=sys.stderr)
        return 2
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))

    unknown = unknown_keys(cfg)
    if unknown:
        for where, key in unknown:
            print(f"{cfg_path}: 미지 키 '{key}' ({where}) — 오타면 규칙이 조용히 무시된다",
                  file=sys.stderr)
        print("허용 키: meta=" + ", ".join(sorted(META_KEYS))
              + " · verdicts.<라벨>=" + ", ".join(sorted(VERDICT_KEYS)), file=sys.stderr)
        return 2

    meta = cfg.get("meta", {}) or {}
    targets = iter_targets(root, meta.get("scan_targets", []) or [])
    if not targets:
        print("검사 대상 파일이 없다 — meta.scan_targets 확인", file=sys.stderr)
        return 2
    exempt_headers = meta.get("exempt_tables_with_header", []) or []

    # 라벨별 규칙 컴파일
    rules: list[tuple[str, re.Pattern, bool]] = []    # (라벨, 금지 정규식, 원문검사 여부)
    exempt: dict[str, list[re.Pattern]] = {}          # 라벨별 문맥 면제
    allowed: dict[str, list[re.Pattern]] = {}
    for label, spec in (cfg.get("verdicts") or {}).items():
        raw = bool(spec.get("scan_raw", False))
        for pat in spec.get("forbidden", []) or []:
            rules.append((label, re.compile(pat), raw))
        exempt[label] = [re.compile(p) for p in spec.get("exempt_line", []) or []]
        allowed[label] = [re.compile(p) for p in spec.get("composite_allowed", []) or []]

    violations = 0
    for f in targets:
        lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        for lineno, text, raw_text in scannable(lines, exempt_headers):
            for label, rx, use_raw in rules:
                subject = raw_text if use_raw else text
                m = rx.search(subject)
                if not m:
                    continue
                if any(ex.search(subject) for ex in exempt.get(label, [])):
                    continue
                violations += 1
                print(f"{f}:{lineno}: [{label}] 금지 문구: “{m.group(0)}”")

    # 참고 경고: 허용 합성 서술이 문서 전체에 한 번도 없으면 알림 (게이트 아님)
    corpus = "\n".join(
        t for f in targets
        for _, t, _raw in scannable(
            f.read_text(encoding="utf-8", errors="replace").splitlines(), exempt_headers
        )
    )
    for label, pats in allowed.items():
        for rx in pats:
            if not rx.search(corpus):
                print(f"(참고) [{label}] 허용 합성 서술 미검출: /{rx.pattern}/")

    if violations:
        print(f"\n{'경고' if args.warn else '실패'}: 판정 문구 위반 {violations}건 — verdicts.yaml(§0.8)과 정합시킬 것")
        if args.warn:
            print("(경고 모드 — CLAUDE.md §2.3: PLAN-048 3단계 종료 시 차단으로 승격)")
            return 0
        return 1
    print(f"통과: {len(targets)}개 파일 · 판정 문구 정합")
    return 0


if __name__ == "__main__":
    sys.exit(main())
