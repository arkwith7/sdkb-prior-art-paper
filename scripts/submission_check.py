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
  D7  영문 초록 ≤ 250 단어          (AEI 투고 규정)
  D8  키워드 ≤ 7 개                 (AEI 투고 규정)
  D9  본문 §참조의 도달성           (축약·재배열로 사라진 절을 가리키지 않는가)
  ＋  내부 링크 도달성 (이관은 삭제가 아니다 — supplementary 링크가 끊기면 실패)

설계 메모
- **대상은 파생본뿐이다**(`paper/submission/**/*.md`). 작업 정본은 감사 기록이므로 이 검사의
  대상이 아니다 — 정본에 상한을 걸면 기록을 지우라는 요구가 된다.
- 파생본이 아직 없으면(PLAN-048 1단계 전) **대상 부재로 통과**시키고 그 사실을 출력한다.
  없는 것을 실패로 만들면 0단계 배선 자체가 CI 를 붉힌다.
- 분량 기준선은 **코드에 동결**한다. 정본을 실시간으로 읽어 비교하면 정본이 자라는 만큼
  목표가 헐거워진다(움직이는 골대).
- **D7·D8 은 투고처 규정이므로 협상 대상이 아니다**(D6 의 −40 % 는 우리가 정한 목표라 성격이
  다르다). 규정이 바뀌면 상수를 고치고 출처를 주석에 남긴다.
- **D9 는 §2.3 의 "이관은 삭제가 아니다"를 절 참조로 확장한 것**이다. 파생본은 장 구성을 접으며
  만들어지므로(PLAN-048 2단계: 11장 → 8장) 산문에 남은 옛 절 번호가 조용히 죽은 링크가 된다.
  파일 링크만 검사하면 이것을 놓친다 — 실제로 놓쳤다(§4.8·§4.9·§4.9.1).
  CLAUDE.md 를 가리키는 하이픈 형식(`§1-2`)은 원고 밖 참조이므로 세지 않는다.
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

MAX_ABSTRACT_WORDS = 250            # D7 — AEI Guide for Authors (투고처 규정)
MAX_KEYWORDS = 7                    # D8 — 위와 같음

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

ABSTRACT_HEAD = re.compile(r"^#{1,3}\s*(Abstract|영문 초록)\s*$", re.I)
KEYWORDS_LINE = re.compile(r"^\**\s*(Keywords?|키워드)\s*\**\s*[::]\s*(.+)$", re.I)
HEADING_NUM = re.compile(r"^#+\s+(\d+(?:\.\d+)*)\.?\s")
# 원고 안의 절 참조. 뒤에 하이픈이 오면 CLAUDE.md 조항(§1-2)이므로 제외한다.
SECTION_REF = re.compile(r"§\s?(\d+(?:\.\d+)*)(?![.\d]*-)")
LATIN_WORD = re.compile(r"[A-Za-z]")
# D9 는 참고문헌 앞까지만 본다 — 서지의 §는 법령·심사기준 조항(MPEP § 904, 35 U.S.C. § 102)이지
# 이 원고의 절이 아니다. 같은 기호, 다른 이름공간.
REFS_HEAD = re.compile(r"^#+\s*(참고문헌|References)\b", re.I)


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

    # D7 · 영문 초록 단어수 — Abstract 절 시작부터 다음 제목 또는 Keywords 행 직전까지.
    abs_start = next((i for i, ln in enumerate(lines) if ABSTRACT_HEAD.match(ln.strip())), None)
    if abs_start is not None:
        chunk: list[str] = []
        for ln in lines[abs_start + 1:]:
            if ln.lstrip().startswith("#") or KEYWORDS_LINE.match(ln.strip()):
                break
            chunk.append(ln)
        n_words = sum(1 for w in " ".join(chunk).split() if LATIN_WORD.search(w))
        if n_words > MAX_ABSTRACT_WORDS:
            fails.append(
                f"{path}:{abs_start + 1}: [D7] 영문 초록 {n_words}단어 > 상한 "
                f"{MAX_ABSTRACT_WORDS} (−{n_words - MAX_ABSTRACT_WORDS}단어 필요 · AEI 규정)"
            )

    # D8 · 키워드 개수
    for i, line in enumerate(lines, 1):
        m = KEYWORDS_LINE.match(line.strip())
        if not m:
            continue
        raw = m.group(2)
        parts = [p.strip(" *") for p in re.split(r"[;；]" if ";" in raw or "；" in raw else "[,，]", raw)]
        parts = [p for p in parts if p]
        if len(parts) > MAX_KEYWORDS:
            fails.append(
                f"{path}:{i}: [D8] 키워드 {len(parts)}개 > 상한 {MAX_KEYWORDS} (AEI 규정)"
            )

    # D9 · §참조 도달성 — 축약·재배열로 사라진 절을 가리키면 실패한다.
    defined = {m.group(1) for ln in lines if (m := HEADING_NUM.match(ln))}
    if defined:                      # 번호 제목이 없는 파일(부속물 등)은 대상 아님
        refs_at = next((i for i, ln in enumerate(lines) if REFS_HEAD.match(ln.strip())), len(lines))
        for i, line in enumerate(lines[:refs_at], 1):
            for ref in SECTION_REF.findall(line):
                if ref not in defined:
                    fails.append(f"{path}:{i}: [D9] 없는 절 참조 — §{ref}")

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
        print(f"\n{'경고' if args.warn else '실패'}: 투고 준비 위반 {len(fails)}건 (PLAN-048 DoD D2–D9)")
        if args.warn:
            print("(경고 모드 — CLAUDE.md §2.3: PLAN-048 3단계 종료 시 차단으로 승격)")
            return 0
        return 1
    print(f"통과: {len(targets)}개 파일 · 투고 준비 검사 (D2–D9 · 내부 링크)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
