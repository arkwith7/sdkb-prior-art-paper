#!/usr/bin/env python3
"""scripts/build_submission.py — 작업 정본에서 투고 파생본을 **기계로** 만든다.

용법:  python scripts/build_submission.py [--check]
종료:  0 = 성공(또는 --check 정합) · 1 = 불일치 · 2 = 앵커 소실

왜 스크립트인가 (PLAN-048 1단계 · CLAUDE.md §2.3)
- 1단계의 계약은 **"순수 이관 · 문장 수정 0"**이다. 손으로 2,000행을 옮기면 그 계약을
  지켰는지 아무도 확인할 수 없다. 스크립트로 만들면 **발췌가 원문과 문자 단위로 같은지**
  기계가 검증한다 — 그것이 이 파일의 존재 이유다.
- 정본(`paper/archive/논문_v0_9_SDKB_통합초안.md`)은 **읽기만 한다.** 감사 가능한 전체 기록으로
  유지되어야 하므로(CLAUDE.md 서두 투고 파생 경로) 이 스크립트는 정본을 절대 쓰지 않는다.

1단계가 하는 일은 둘뿐이다 (요건 2 이동 대장의 **이관 행만**)
  ① 제목 아래 원고상태 5블록·정정 대장을 **파생본에서 뺀다** — 정본에 그대로 남아 있고
     파생본은 그것을 링크로 가리킨다(이관은 삭제가 아니다).
  ② §6.8 전달 실험을 **부록으로 내린다** — 본문 순서에서 빼 부록 B 앞에 그대로 놓는다.
장 재배열·EP 라벨·축약·재조준은 **2·3단계**이며 이 스크립트는 하지 않는다.

새로 쓰는 문장은 **부록 표제 1행뿐**이고, 그마저 ALLOWED_NEW 에 명시해 검증기가 센다.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SOURCE = Path("paper/archive/논문_v0_9_SDKB_통합초안.md")
TARGET = Path("paper/submission/manuscript.md")

# ── 이관 명세 — 행번호가 아니라 **앵커 문자열**로 잡는다(정본이 자라도 따라간다) ──────────
# (시작 앵커, 끝 앵커) · 끝 앵커 행은 포함하지 않는다.
EXCLUDE = [
    # ① 원고상태 5블록 + 정정 대장 (정본에 남는다 · 파생본에서만 뺀다)
    ("> **원고 상태: v2.0 재구성 4단계", "## 국문 초록"),
]
RELOCATE = [
    # ② §6.8 전달 실험 → 부록
    ("## 6.8 검색 층의 이득은 생성 층으로 옮겨가는가", "# 7. 논의"),
]

# 부록에 놓을 때 붙이는 표제 — 이 스크립트가 새로 쓰는 **유일한** 문장이다.
APPENDIX_HEADING = "# 부록 A. 전달 실험 전문 (RQ5 · T4 판정 1회 · 본문 §6.8에서 이관)"
ALLOWED_NEW = {APPENDIX_HEADING, ""}

APPENDIX_ANCHOR = "# 부록 B. 주장–증거 매트릭스"

# 파생본은 정본보다 한 디렉터리 깊다(paper/ → paper/submission/). 상대 링크를 그대로 두면
# **이관이 링크 단절을 만든다** — "이관은 삭제가 아니다"(CLAUDE.md §2.3)를 깨는 것이므로
# 경로만 기계적으로 고친다. 문장은 건드리지 않으며, 검증도 이 치환을 적용한 뒤 대조한다.
LINK_REWRITES = [("](supplementary/", "](../supplementary/")]


def rewrite_links(line: str) -> str:
    for old, new in LINK_REWRITES:
        line = line.replace(old, new)
    return line


def find(lines: list[str], prefix: str, start: int = 0) -> int:
    for i in range(start, len(lines)):
        if lines[i].startswith(prefix):
            return i
    raise LookupError(prefix)


def build(lines: list[str]) -> tuple[list[str], dict]:
    n = len(lines)
    drop = [False] * n
    moved: list[str] = []
    stats = {"excluded": 0, "relocated": 0}

    for start_a, end_a in EXCLUDE:
        s, e = find(lines, start_a), find(lines, end_a)
        for i in range(s, e):
            drop[i] = True
        stats["excluded"] += e - s

    for start_a, end_a in RELOCATE:
        s, e = find(lines, start_a), find(lines, end_a)
        block = lines[s:e]
        # 블록 끝의 장 구분선(---)과 공백은 본문 자리에 남긴다 — 장 경계는 §6.8 것이 아니다.
        while block and block[-1].strip() in {"", "---"}:
            block.pop()
        for i in range(s, s + len(block)):
            drop[i] = True
        moved += block
        stats["relocated"] += len(block)

    body = [line for i, line in enumerate(lines) if not drop[i]]

    # 옮긴 블록을 부록 B 앞에 놓는다.
    at = find(body, APPENDIX_ANCHOR)
    out = body[:at] + [APPENDIX_HEADING, ""] + moved + ["", "---", ""] + body[at:]
    rewritten = [rewrite_links(line) for line in out]
    stats["link_rewrites"] = sum(1 for a, b in zip(out, rewritten) if a != b)
    return rewritten, stats


def verify(src: list[str], out: list[str]) -> list[str]:
    """파생본의 모든 행이 정본에 있는가 — '순수 이관'의 기계 검증."""
    from collections import Counter

    # 정본도 같은 치환을 적용한 뒤 대조한다 — 경로 치환은 내용 변경이 아니다.
    src_count, out_count = Counter(rewrite_links(x) for x in src), Counter(out)
    problems = []
    for line, k in out_count.items():
        if line in ALLOWED_NEW or line.strip() in {"---"}:
            continue
        if src_count[line] == 0:
            problems.append(f"정본에 없는 행: {line[:90]!r}")
        elif k > src_count[line]:
            problems.append(f"행이 늘었다({src_count[line]}→{k}): {line[:70]!r}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="쓰지 않고 정합만 확인")
    args = ap.parse_args()

    if not SOURCE.exists():
        print(f"정본 없음: {SOURCE}", file=sys.stderr)
        return 2
    src = SOURCE.read_text(encoding="utf-8").splitlines()

    try:
        out, stats = build(src)
    except LookupError as e:
        print(f"앵커 소실 — 정본 구조가 바뀌었다: {e}", file=sys.stderr)
        print("이동 대장(EXCLUDE·RELOCATE)을 정본에 맞춰 갱신할 것.", file=sys.stderr)
        return 2

    problems = verify(src, out)
    for p in problems:
        print(p)
    if problems:
        print(f"\n실패: 순수 이관 위반 {len(problems)}건 — 파생본에 정본에 없는 문장이 있다")
        return 1

    new_text = "\n".join(out) + "\n"
    if args.check:
        cur = TARGET.read_text(encoding="utf-8") if TARGET.exists() else None
        if cur != new_text:
            print(f"불일치: {TARGET} 가 정본에서 재생성한 결과와 다르다 — 재생성할 것")
            return 1
        print(f"정합: {TARGET} = 정본 재생성 결과")
        return 0

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(new_text, encoding="utf-8")
    print(
        f"생성: {TARGET}\n"
        f"  정본 {len(src):,}행 → 파생본 {len(out):,}행 "
        f"(제외 {stats['excluded']}행 · 부록 이관 {stats['relocated']}행 · 신규 표제 1행 · "
        f"상대 링크 경로 치환 {stats['link_rewrites']}행)\n"
        f"  순수 이관 검증 통과 — 파생본의 모든 문장이 정본에 있다."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
