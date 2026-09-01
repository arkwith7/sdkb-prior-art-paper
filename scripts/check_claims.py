#!/usr/bin/env python3
"""scripts/check_claims.py — 본문의 **주장 강도**가 근거보다 커지지 않는가 (PLAN-086 D14).

용법:  python scripts/check_claims.py [--warn]
종료:  0 = 정합 · 1 = 위반

**왜 `verdicts.yaml` 로는 못 잡는가.** 그 파일은 **판정 문구**를 본다 — "H3 는 지지되었다" 처럼
판정 자체를 잘못 옮긴 문장이 대상이다. 그러나 외부 검토가 지적한 셋은 판정을 옮긴 문장이
아니었다. *"we found no design"*(선취 주장) · *"불안전한 변경"*(허용 마진 초과의 함의) ·
미실행 이력의 본문 잔류가 그것이며, 셋 다 검사기 다섯을 전부 통과하였다.

**이 검사가 보는 것은 두 가지다.**

  C1  선취·최상급 — "최초" · `first to` · `we found no` 처럼 **문헌 전수를 전제하는 표현**.
      CLAUDE.md §0.2 는 *"'최초'를 주장하지 않는다"* 를 이미 규약으로 갖고 있었고, 이 검사는
      그 규약에 기계를 붙인다.
  C2  미실행 이력의 본문 잔류 — "실행하지 않았다" · "구현되지 않았다" · `was not run` 은
      **S3(설계하였으나 실행하지 않은 평가 옵션) 의 수용처**로 가야 한다(§2.3 "이관은 삭제가
      아니다"). 본문에 남으면 독자는 그것을 결과로 읽는다.

**적용 범위는 본문 계열뿐이다.** 보충자료 `S` 계열은 감사 기록이므로 대상이 아니다 — 미실행
이력을 **적는 것이 임무인 문서**에 이 규칙을 걸면 그 문서를 지우라는 요구가 된다.

**언급은 사용이 아니다.** 따옴표·백틱 안의 인용은 위반으로 세지 않는다(§0.8 과 같은 규칙).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TARGETS = [
    "paper/manuscript/stage3_source.md",
    "paper/manuscript/en_source.md",
    "paper/submission/manuscript.md",
    "paper/submission/en/manuscript.md",
]

# (규칙, 정규식, 왜 금지인가 / 대신 무엇을 쓰는가)
RULES: list[tuple[str, re.Pattern, str]] = [
    ("C1", re.compile(r"\bwe\s+found\s+no\b", re.I),
     "문헌 전수를 전제한다 — “to the extent that we have surveyed” 로 좁힌다"),
    ("C1", re.compile(r"\bfirst\s+to\s+(propose|introduce|present|report|apply)\b", re.I),
     "선취 주장이다 — 신규성은 결합과 실험설계의 차별성으로 적는다(§0.2)"),
    ("C1", re.compile(r"최초로?\s*(제안|제시|도입|보고|적용)"),
     "선취 주장이다 — 신규성은 결합과 실험설계의 차별성으로 적는다(§0.2)"),
    ("C1", re.compile(r"(유일한|유일하게)\s*(연구|설계|접근|방법)"),
     "전수를 전제한다 — “우리가 확인한 범위에서는” 으로 좁힌다"),
    ("C1", re.compile(r"\bthe\s+only\s+(study|design|approach|method)\b", re.I),
     "전수를 전제한다 — “to the extent that we have surveyed” 로 좁힌다"),
    ("C2", re.compile(r"\bwas\s+not\s+run\b", re.I),
     "미실행 이력이다 — S3(설계하였으나 실행하지 않은 평가 옵션)으로 이관한다"),
    ("C2", re.compile(r"\b(is|was|are|were)\s+not\s+implemented\b", re.I),
     "미실행 이력이다 — S3 로 이관한다"),
    ("C2", re.compile(r"\bwere\s+designed\s+but\s+(not|never)\b", re.I),
     "미실행 이력이다 — S3 로 이관한다"),
    ("C2", re.compile(r"(설계하였으나|설계했으나)\s*(실행|수행)하지\s*않"),
     "미실행 이력이다 — S3 로 이관한다"),
    ("C2", re.compile(r"(구현되지|구현하지)\s*않았다"),
     "미실행 이력이다 — S3 로 이관한다"),
]

# 면제 — 규칙이 원리적으로 발동해야 하는 자리. 왜 면제인지 함께 적는다.
EXEMPT: list[re.Pattern] = [
    # S3 로 가라는 안내 문장 자체는 이관의 증거이지 이관 누락이 아니다.
    re.compile(r"\bS3\b"),
    # 결손 표와 한계 절은 "무엇을 못 하였는가" 를 적는 것이 임무다. 그 자리를 막으면
    # 정직성 장치를 지우라는 요구가 된다(PLAN-086 §7.1 "줄이지 않는 것 여섯").
    re.compile(r"(결손|해소하는 측정|Deficit|remedy)"),
    # 반증 조건 서술 — "…이면 이 교훈은 약화된다" 는 §0.6 조건 4 가 요구하는 문장이다.
    re.compile(r"(약화된다|weakens if)"),
]

QUOTED = re.compile(r"`[^`]*`|“[^”]*”|\"[^\"]*\"|'[^']*'|\*\*[^*]*\*\*(?=\s*(?:라|이라|로|으로))")
BIB_HEAD = re.compile(r"^#\s+(참고문헌|References)\s*$")


def scannable(path: Path) -> list[tuple[int, str]]:
    """참고문헌 앞까지의 산문 · 코드 펜스 제외 · 인용 마스킹."""
    out: list[tuple[int, str]] = []
    fenced = False
    for i, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if BIB_HEAD.match(line):
            break
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        out.append((i, QUOTED.sub(" ", line)))
    return out


# 면제는 **문단 창(window)** 으로 본다. 미실행 이력을 본문에 남기는 것이 정당한 자리는
# 언제나 "전문은 S3 에 있다" 를 함께 적는데, 그 안내가 다음 줄로 넘어가는 일이 흔하다.
# 줄 단위로만 보면 그 자리가 전부 거짓 위반이 된다.
EXEMPT_WINDOW = 3


def check(path: Path) -> list[str]:
    fails: list[str] = []
    rows = scannable(path)
    for k, (i, line) in enumerate(rows):
        window = " ".join(t for _, t in rows[max(0, k - EXEMPT_WINDOW): k + EXEMPT_WINDOW + 1])
        if any(p.search(window) for p in EXEMPT):
            continue
        for rule, pat, why in RULES:
            if m := pat.search(line):
                fails.append(f"{path}:{i}: [{rule}] 주장 강도 “{m.group(0)}” — {why}")
    return fails


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--warn", action="store_true", help="위반을 출력하되 종료코드 0")
    args = ap.parse_args()

    fails: list[str] = []
    seen = 0
    for rel in TARGETS:
        p = ROOT / rel
        if not p.exists():
            print(f"[없음] {rel} — 조립 동결 중이면 정상이다")
            continue
        seen += 1
        fails += check(p)

    for line in fails:
        print(("[warn] " if args.warn else "[실패] ") + line, file=sys.stderr)
    if fails:
        print(f"\n{'경고' if args.warn else '실패'}: 주장 강도 위반 {len(fails)}건 (PLAN-086 D14)")
        return 0 if args.warn else 1
    print(f"통과: {seen}개 파일 · 주장 강도 (C1 선취·최상급 · C2 미실행 이력의 본문 잔류)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
