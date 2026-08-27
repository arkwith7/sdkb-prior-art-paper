#!/usr/bin/env python3
"""scripts/check_supplementary_en.py — 영문 supplementary 가 원문의 **수치를 그대로 옮겼는가**.

용법:  python scripts/check_supplementary_en.py [--warn]
종료:  0 = 정합 · 1 = 불일치

**왜 이 검사가 필요한가 (CLAUDE.md §1-1).** 영문 원고가 인용하는 supplementary 는 지금까지
한국어뿐이었고, 영문 심사자는 자신이 읽을 수 없는 자리에 근거가 있는 상태였다. 그 자리를
영문으로 옮기는 순간 **표의 수치를 사람이 다시 타자하게 되며, 오탈자가 곧 조작이 된다.**
`build_submission_en.py` 는 이 위험을 표를 문자 단위로 복사해 막지만, supplementary 는
산문과 표가 뒤섞인 감사 기록이라 같은 조립 방식이 맞지 않는다.

그래서 **번역은 사람이 하고 기계는 수치 불변만 보증한다.** 원문과 영문판에서 측정값 토큰을
뽑아 다중집합으로 비교하고, 하나라도 다르면 실패한다. 이 규율은 조립기의
`measurements()` 와 **같은 정의**를 쓴다.

**절 번호는 수치로 세지 않는다.** `§4.5` → `§4.4` 같은 재부여는 수치 변경이 아니며, 영문판이
투고본의 현행 절 번호를 가리키도록 고치는 것은 정당한 교정이다. 마찬가지로 `S5`·`PLAN-031`·
`v1.4.2` 같은 식별자와 ISO 날짜도 제외한다 — 이들은 이름이지 측정값이 아니다.

대상은 `paper/supplementary/<name>.md` ↔ `paper/supplementary/en/<name>.md` 쌍이며,
영문판이 없는 원문은 **미번역으로 보고**하되 실패시키지 않는다(단계적 영문화를 막지 않는다).

**부분 렌더링은 포함 관계로 검사한다(`PARTIAL`).** S5 는 축약 전 원고 전문(11장·표 423행)이고
영문판은 **본문이 실제로 인용하는 자리만** 옮긴 것이므로 전량 대조가 성립하지 않는다. 이런
파일에는 다른 계약을 건다 — **영문판이 원문에 없는 측정값을 새로 만들지 않았는가.** 누락은
설계이고 신설은 결함이므로, 지켜야 하는 것은 등가가 아니라 **포함**이다.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KO_DIR = ROOT / "paper" / "supplementary"
EN_DIR = KO_DIR / "en"

# 부분 렌더링 — 영문판이 원문의 **인용된 자리만** 옮긴 파일. 포함 관계로 검사한다.
PARTIAL = {"S5-submission-full-v2.md"}

NUMERIC = re.compile(r"\d+(?:[.,]\d+)*")
# 측정값이 아닌 자리 — 절 번호 · 식별자 · 날짜 · 커밋 해시 · 파일명
NOT_MEASUREMENT = [
    re.compile(r"§\s?\d+(?:\.\d+)*[a-z]?"),          # §4.5 · §6.4.3 · §1.4a
    re.compile(r"\bS\d+(?:[-.]\w+)*"),                # S5 · S5-submission-full-v2
    re.compile(r"\bPLAN-\d+"),                        # PLAN-031
    re.compile(r"\b(?:CR|D)-\d+"),                    # CR-007 · D-23
    re.compile(r"\bv\d+(?:\.\d+)*"),                  # v1.4.2 · v0.9
    re.compile(r"\d{4}-\d{2}-\d{2}"),                 # 2026-08-15
    re.compile(r"\b(?:DP|EP|CQ|RQ|DRQ|F|A|B|P|T|L|H)\d+"),  # 라벨
    re.compile(r"`[^`]*`"),                           # 코드·식별자 인용
    re.compile(r"\]\([^)]*\)"),                       # 링크 경로
]


def measurements(text: str) -> Counter[str]:
    """원문과 영문판이 말하는 **측정값**. 한 자리 숫자는 세지 않는다.

    `tests/test_figure_labels.py` 가 같은 이유로 같은 규칙을 쓴다 — 한국어는 「판정 1회」로
    적고 영문은 `one verdict` 로 적으므로, 한 자리를 세면 **같은 뜻을 다르게 적은 문장이 전부
    위반이 된다.** 이 완화가 놓치는 것은 한 자리 측정치를 손으로 잘못 적은 경우뿐이며,
    분수 표기(`12/45` · `0/30`)의 두 자리 쪽은 그대로 비교된다.
    """
    for pat in NOT_MEASUREMENT:
        text = pat.sub(" ", text)
    return Counter(n for n in NUMERIC.findall(text) if len(n) > 1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--warn", action="store_true", help="불일치를 경고로만 보고한다")
    args = ap.parse_args()

    ko_files = sorted(p for p in KO_DIR.glob("*.md"))
    fails: list[str] = []
    done = missing = 0

    for ko in ko_files:
        en = EN_DIR / ko.name
        if not en.exists():
            missing += 1
            print(f"[미번역] {ko.name}")
            continue
        done += 1
        a, b = measurements(ko.read_text()), measurements(en.read_text())
        if ko.name in PARTIAL:
            invented = sorted(set(b) - set(a))
            if not invented:
                print(f"[ok]   {ko.name} — 부분 렌더링 · 측정값 {len(set(b))}종 전부 원문에 있다")
                continue
            fails.append(f"{en}: 원문에 없는 측정값을 새로 만들었다\n    {invented}")
            continue
        if a == b:
            print(f"[ok]   {ko.name} — 측정값 {sum(a.values())}개 정합")
            continue
        only_ko = a - b
        only_en = b - a
        fails.append(
            f"{en}: 측정값이 원문과 다르다\n"
            f"    원문에만: {sorted(only_ko.elements())}\n"
            f"    영문에만: {sorted(only_en.elements())}"
        )

    for f in fails:
        print(("[warn] " if args.warn else "[실패] ") + f, file=sys.stderr)

    print(f"\n영문 supplementary {done}개 검사 · 미번역 {missing}개 · 불일치 {len(fails)}건")
    return 1 if (fails and not args.warn) else 0


if __name__ == "__main__":
    raise SystemExit(main())
