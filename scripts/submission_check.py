#!/usr/bin/env python3
"""scripts/submission_check.py — 투고 파생본의 데스크 리젝 요인 검사 (CLAUDE.md §2.3).

용법:  python scripts/submission_check.py [--root .] [--warn]
종료:  0 = 통과(또는 대상 부재/--warn) · 1 = 위반 · 2 = 설정 오류

무엇을 보는가 — PLAN-048 §0 완료 기준(DoD) D2–D6 을 기계로 옮긴 것이다.
  D2  플레이스홀더 0건            (`[서지 재확인 필요]` 류)
  D3  영문 제목·초록 존재
  D4  작업 정본 전용 블록 0건      (원고상태·정정 대장·개봉 원장·미수행 설계 전문)
  D5  본문 표 ≤ 12 · 그림 4–5
  D6  본문 분량 ≤ 동결 기준선의 60 % (= −40 %)
  ＋  내부 링크 도달성 (이관은 삭제가 아니다 — supplementary 링크가 끊기면 실패)

설계 메모
- **대상은 파생본뿐이다**(`paper/submission/**/*.md`). 작업 정본은 감사 기록이므로 이 검사의
  대상이 아니다 — 정본에 상한을 걸면 기록을 지우라는 요구가 된다.
- 파생본이 아직 없으면(PLAN-048 1단계 전) **대상 부재로 통과**시키고 그 사실을 출력한다.
  없는 것을 실패로 만들면 0단계 배선 자체가 CI 를 붉힌다.
- 분량 기준선은 **코드에 동결**한다. 정본을 실시간으로 읽어 비교하면 정본이 자라는 만큼
  목표가 헐거워진다(움직이는 골대).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# 동결 기준선 — paper/논문_v0_9_SDKB_통합초안.md, 2026-08-10 (PLAN-048 승인 시점) 실측.
BASELINE_CHARS = 124_354
LENGTH_TARGET_RATIO = 0.60          # D6: −40 % 이상 축약

MAX_TABLES = 12                     # D5
FIGURE_RANGE = (4, 5)               # D5

PLACEHOLDERS = [                    # D2 — verdicts.yaml PLACEHOLDERS 와 이중 방어
    "[서지 재확인 필요]",
    "[실험 후 기입]",
    "[최종 릴리스 후 기입]",
    "[미확정 서지]",
    "TODO",
]

# D4 — 작업 정본에만 있어야 하는 감사 블록의 표지. 파생본에서 발견되면 이관 누락이다.
WORKDOC_MARKERS = [
    "원고 상태",
    "정정 대장",
    "개봉 원장",
    "봉인 개봉 기록",
    "미수행 설계 전문",
]

TABLE_SEP = re.compile(r"^\|[\s:|-]+\|?\s*$")
IMAGE_REF = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
INTERNAL_LINK = re.compile(r"(?<!!)\[[^\]]*\]\((?!https?:|mailto:)([^)#]+)(?:#[^)]*)?\)")


def strip_fenced(lines: list[str]) -> list[str]:
    out, in_fence = [], False
    for line in lines:
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(line)
    return out


def check_file(path: Path, root: Path) -> list[str]:
    fails: list[str] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = strip_fenced(text.splitlines())
    body = "\n".join(lines)

    # D2 · 플레이스홀더
    for i, line in enumerate(lines, 1):
        for ph in PLACEHOLDERS:
            if ph in line:
                fails.append(f"{path}:{i}: [D2] 플레이스홀더 잔존 — {ph}")

    # D3 · 영문 제목·초록 (ASCII 알파벳이 실질적으로 있는 제목/초록 절)
    has_en_title = bool(re.search(r"^#\s+.*[A-Za-z]{4,}", body, re.M))
    has_en_abstract = bool(re.search(r"^#{1,3}\s*(Abstract|영문 초록)", body, re.M))
    if not has_en_title:
        fails.append(f"{path}: [D3] 영문 제목 없음")
    if not has_en_abstract:
        fails.append(f"{path}: [D3] 영문 초록 절(Abstract) 없음")

    # D4 · 작업 정본 전용 블록
    for i, line in enumerate(lines, 1):
        for marker in WORKDOC_MARKERS:
            if marker in line and line.lstrip().startswith("#"):
                fails.append(f"{path}:{i}: [D4] 작업 정본 전용 블록 잔존 — {marker}")

    # D5 · 표·그림 계수
    n_tables = sum(1 for line in lines if TABLE_SEP.match(line))
    n_figures = len(IMAGE_REF.findall(body))
    if n_tables > MAX_TABLES:
        fails.append(f"{path}: [D5] 본문 표 {n_tables}개 > 상한 {MAX_TABLES}")
    if not (FIGURE_RANGE[0] <= n_figures <= FIGURE_RANGE[1]):
        fails.append(f"{path}: [D5] 그림 {n_figures}개 — 목표 {FIGURE_RANGE[0]}–{FIGURE_RANGE[1]}")

    # D6 · 분량
    limit = int(BASELINE_CHARS * LENGTH_TARGET_RATIO)
    if len(text) > limit:
        pct = 100 * (1 - len(text) / BASELINE_CHARS)
        fails.append(
            f"{path}: [D6] 분량 {len(text):,}자 > 목표 {limit:,}자 "
            f"(기준선 {BASELINE_CHARS:,}자 대비 −{pct:.1f} % · 목표 −40 %)"
        )

    # 내부 링크 도달성
    for i, line in enumerate(lines, 1):
        for target in INTERNAL_LINK.findall(line):
            target = target.strip()
            if not target:
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists() and not (root / target).resolve().exists():
                fails.append(f"{path}:{i}: [LINK] 내부 링크 단절 — {target}")

    return fails


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--warn", action="store_true", help="위반을 출력하되 종료코드 0 (§2.3 경고 모드)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    targets = sorted((root / "paper" / "submission").rglob("*.md"))
    if not targets:
        print("대상 부재: paper/submission/**/*.md — 투고 파생본이 아직 없다 (PLAN-048 1단계 전). 통과.")
        return 0

    fails: list[str] = []
    for f in targets:
        fails += check_file(f, root)

    for line in fails:
        print(line)
    if fails:
        print(f"\n{'경고' if args.warn else '실패'}: 투고 준비 위반 {len(fails)}건 (PLAN-048 DoD D2–D6)")
        if args.warn:
            print("(경고 모드 — CLAUDE.md §2.3: PLAN-048 3단계 종료 시 차단으로 승격)")
            return 0
        return 1
    print(f"통과: {len(targets)}개 파일 · 투고 준비 검사 (D2–D6 · 내부 링크)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
