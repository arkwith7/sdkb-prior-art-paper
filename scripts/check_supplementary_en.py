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

# **부호를 값에 포함한다 (PLAN-086 D15 · 2026-09-01).** 구 정규식은 `\d+(?:[.,]\d+)*` 였고
# 부호가 없어 `+0.0534` 와 `−0.0534` 가 **같은 토큰**이었다. 개선과 저하를 뒤바꿔 적어도
# 이 검사는 통과한다 — 수치 일치는 의미 일치가 아니다. 유니코드 마이너스(U+2212)와 하이픈,
# 그리고 영문 `minus` 표기를 모두 부호로 읽는다.
# 부호는 **낱말 뒤에 붙은 하이픈이 아닐 때만** 부호다 — `pre-2015` 의 하이픈은 음수 기호가
# 아니다. 그래서 부호 앞에 글자·숫자가 오면 부호로 읽지 않는다.
NUMERIC = re.compile(r"(?:(?<![0-9A-Za-z가-힣])[+\u2212-])?\d+(?:[.,]\d+)*")
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


SIGN_NORM = str.maketrans({"\u2212": "-", "\u2013": "-", "\u2010": "-"})


def measurements(text: str) -> Counter[str]:
    """원문과 영문판이 말하는 **측정값**. 한 자리 숫자는 세지 않는다.

    `tests/test_figure_labels.py` 가 같은 이유로 같은 규칙을 쓴다 — 한국어는 「판정 1회」로
    적고 영문은 `one verdict` 로 적으므로, 한 자리를 세면 **같은 뜻을 다르게 적은 문장이 전부
    위반이 된다.** 이 완화가 놓치는 것은 한 자리 측정치를 손으로 잘못 적은 경우뿐이며,
    분수 표기(`12/45` · `0/30`)의 두 자리 쪽은 그대로 비교된다.
    """
    for pat in NOT_MEASUREMENT:
        text = pat.sub(" ", text)
    text = text.translate(SIGN_NORM)
    out: Counter[str] = Counter()
    for n in NUMERIC.findall(text):
        digits = n.lstrip("+-")
        # 천 단위 구분은 표기 관습이지 값이 아니다 — 한국어는 `1000`, 영문은 `1,000` 을 쓴다.
        # 소수점은 지운다면 값이 달라지므로, **소수부가 없을 때만** 쉼표를 제거한다.
        if "," in digits and "." not in digits:
            digits = digits.replace(",", "")
        if len(digits) <= 1:
            continue
        # **부호 없는 자리는 부호 없는 채로 센다.** 한국어가 「0.0293 저하」로 적고 영문이
        # `reduced by 0.0293` 으로 적는 자리가 흔하며, 거기에 부호를 강제하면 거짓 위반이 된다.
        # 이 검사가 잡으려는 것은 **한쪽이 부호를 달고 다른 쪽이 반대 부호를 단** 경우다.
        out[(n[0] + digits) if n[0] in "+-" else digits] += 1
    return out


# ── D15 · 의미 묶음 대조 (PLAN-086 · 2026-09-01) ────────────────────────────
#
# **수치 일치는 의미 일치가 아니다.** 위의 대조는 같은 수를 두 문서가 갖고 있는가만 본다.
# 그러나 실제로 난 사고는 수치가 아니라 **그 수가 무엇의 값인가**에서 났다 — 본문이
# *"쓰지 않는다"* 한 지표를 보충자료가 계산해 보고하고 있었고, 두 문서의 수치는 일치했다.
#
#   M1  배제 선언과의 정합 — 본문이 현행 분석에서 뺀 지표를 보충자료가 **지위 표시 없이**
#       다루면 실패한다. 삭제를 요구하지 않는다(§1-1) — 요구하는 것은 지위의 명시다.
#   M2  판정 지위의 어휘 — `확증`/`confirmatory` 를 세 범주(㉮㉯㉰) 밖에서 쓰지 않는다.
#       "주요 확증 셋에 없다"와 "탐색적이다"는 같은 뜻이 아니며, 그 혼동이 S0·S8 에 있었다.

EXCLUDED_METRICS = {
    # 지표 이름 → 지위 표시로 인정하는 표현(둘 중 하나가 같은 파일에 있어야 한다)
    "bpref": ("과거 실행 기록", "record of a past execution"),
}
# M2 는 **지위를 선언하는 자리**만 본다. `확증 분할`·`확증 점검`·`confirmatory split` 은 동결된
# 용어이고 지위 선언이 아니다 — 그것까지 세면 규칙이 거짓 위반으로 가득 차 아무도 읽지 않는다.
# 선언의 자리는 셋이다: 절 표제 · `확증 · 사전등록 §…` 형태의 꼬리표 · 표 셀 하나가 통째로 `확증`.
STATUS_DECL = [
    re.compile(r"^#{1,6}\s.*(?<![가-힣])확증(?![가-힣])"),
    re.compile(r"^#{1,6}\s.*\bconfirmatory\b", re.I),
    re.compile(r"확증\s*·\s*사전등록"),
    re.compile(r"\bconfirmatory\s*·\s*preregistration", re.I),
    re.compile(r"\|\s*확증\s*\|"),
    re.compile(r"\|\s*[Cc]onfirmatory\s*\|"),
]
STATUS_CATEGORY = re.compile(r"[㉮㉯㉰]")
# 동결된 연어(collocation) — `확증 분할`·`확증 판독` 은 대상의 이름이지 지위의 선언이 아니다.
STATUS_FROZEN = re.compile(
    r"확증\s*(분할|판독|점검|계열|평가\s*점검)|홀드아웃\s*확증|확증에서\s*강등"
    r"|confirmatory\s+(split|readout|check|evaluation\s+check)"
    r"|demoted\s+from\s+confirmatory",
    re.I,
)


def semantic_bundle(path: Path) -> list[str]:
    """M1·M2 — 한 파일 안에서 닫히는 의미 검사."""
    out: list[str] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    flat = re.sub(r"\s+", " ", text)
    for metric, markers in EXCLUDED_METRICS.items():
        # `\b` 를 쓰지 않는다 — 한국어에서 `bpref는` 은 한글이 낱말 문자로 취급되어 경계가
        # 생기지 않고, 그래서 국문판이 통째로 눈에 보이지 않았다.
        pat = rf"(?<![0-9A-Za-z]){metric}(?![0-9A-Za-z])"
        if re.search(pat, flat, re.I) and not any(m in flat for m in markers):
            out.append(
                f"{path}: [M1] 현행 분석에서 제외한 지표 ‘{metric}’ 를 지위 표시 없이 다룬다 "
                f"— {markers[0]!r} 로 표시한다(삭제하지 않는다)"
            )
    for i, line in enumerate(text.splitlines(), 1):
        if STATUS_FROZEN.search(line) or STATUS_CATEGORY.search(line):
            continue
        if any(p.search(line) for p in STATUS_DECL):
            out.append(
                f"{path}:{i}: [M2] 판정 지위 ‘확증’ 을 세 범주 밖에서 쓴다 "
                f"— ㉮ 검색 사전등록 확증 점검 · ㉯ 산출물 검증·승인 판정 · ㉰ 탐색적 분석"
            )
    return out


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
        fails += semantic_bundle(ko)
        fails += semantic_bundle(en)
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
