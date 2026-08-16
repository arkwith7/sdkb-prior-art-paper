#!/usr/bin/env python3
"""scripts/style_check.py — 한국어 학술 문체 규격의 기계 검사 (paper/STYLE-KO-ACADEMIC.md).

용법:  python scripts/style_check.py [--root .] [--warn] [--stats]
종료:  0 = 통과(또는 --warn) · 1 = 위반 · 2 = 대상 부재

무엇을 보는가 — 규격 v1 의 네 항목만 본다.
  S3  문장 길이 ≤ 90자 (공백 포함)
  T2  은유·구어 동사 금지 (치환표)
  T3  문두 접속어는 표준 학술 연결어만 (그래서·그런데·하지만 금지)
  T5  볼드는 용어의 최초 등장에만 — 볼드 안에 종결어미가 있으면 주장 문장이다

**S1·S2·S4·T1·T4·V1–V4 는 사람이 지킨다.** 검사기 통과는 규격 준수의 필요조건이지 충분조건이
아니다. `check_verdicts.py` 가 판정 강도의 표류를 막듯, 이 파일은 **어체의 표류**만 막는다.

설계 메모
- **대상은 투고 파생본 계열뿐이다**(산문 소스 + 조립 산출물). 작업 정본과 supplementary 는
  **감사 기록**이므로 제외한다 — 과거 문장을 소급해 다듬으라는 요구가 되기 때문이다
  (`submission_check.py` 가 정본을 제외하는 것과 같은 이유).
- **언급(mention)은 사용(use)이 아니다.** 따옴표·백틱 안은 마스킹해 T2·T3 위반으로 세지 않는다.
- 문장은 **행이 아니라 문단**에서 자른다. 원고는 100열 안팎에서 손으로 줄바꿈하므로 행 단위로
  세면 한 문장이 여러 조각으로 갈려 길이 검사가 무력해진다.
- 표·수식·코드·서지·영문 초록은 검사하지 않는다. 규격이 정하는 것은 한국어 산문의 어체다.
- `<!-- style-ok: 사유 -->` 로 면제한다. 그 행에 있으면 그 행만, 문단 **바로 앞 줄**에 홀로
  있으면 그 문단 전체를 면제한다. 사유 없는 면제는 두지 않는다.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MAX_SENT_CHARS = 90                      # S3

# T2 — (금지 정규식, 치환 제안). 규격 v1 의 치환표와 1:1 대응한다.
BANNED_LEXICON: list[tuple[str, str]] = [
    (r"망가뜨리|망가트리|망가지", "훼손하다 · 저해하다"),
    (r"깨뜨리", "무효화하다 · 반증하다"),
    (r"건지(다|는|고|면)|건져", "회수하다"),
    (r"(?<![가-힣])재\s*본다|(?<![가-힣])잰다|(?<![가-힣])재는(?=\s|\b)", "측정하다 · 평가하다"),
    (r"아프다|아픈\s|뼈아프", "심각하다 · 중대하다"),
    (r"뒷걸음", "저하되다"),
    (r"갈아\s*끼우|갈아\s*낀|갈아\s*끼운|갈아끼", "교체하다"),
    (r"좋아지|나빠지|나빠졌", "향상되다 · 저하되다"),
    (r"새어\s*(나가|들어)", "유출되다 · 전파되다"),
    (r"꽂아\s*넣", "적용하다 · 결합하다"),
    (r"넘겨\s*짚", "과잉 일반화하다"),
    (r"붙잡아\s*두", "제약하다 · 근거로 고정하다"),
    (r"쓸모", "유용성"),
    (r"지어내|지어낼|지어낸", "사실과 다른 내용을 생성하다"),
    (r"헐거워", "완화되다"),
    (r"건초더미", "대규모 후보 집합"),
    (r"조용히\s", "그 사실이 드러나지 않은 채"),
]

# T3 — 문장 첫머리에서 금지되는 접속어.
BANNED_OPENERS = re.compile(r"^(그래서|그런데|하지만)(?=[\s,])")

# T5 — 볼드 안에 종결어미가 있으면 용어가 아니라 주장 문장이다.
BOLD = re.compile(r"\*\*(?P<inner>[^*\n]{2,})\*\*")
PREDICATE_END = re.compile(r"(다|요|함|음)[.!?]?\s*$|다[.!?]\s")

_QUOTE_SPANS = [
    re.compile(r"`[^`\n]*`"),
    re.compile(r"“[^”\n]*”"),
    re.compile(r'"[^"\n]*"'),
    re.compile(r"「[^」\n]*」"),
    re.compile(r"'[^'\n]*'"),
]

SENT_SPLIT = re.compile(r"(?<=[가-힣\)\]”』」])[.?!](?=\s|$)")
LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
MATH = re.compile(r"\\\([^)]*\\\)|\\\[[^\]]*\\\]")
SKIP_LINE = re.compile(r"^\s*(\||>?\s*\{\{|!\[|\\\[|\\\]|<!--|---+\s*$|#)")
REFS_HEAD = re.compile(r"^#+\s*(참고문헌|References)\b", re.I)
EN_HEAD = re.compile(r"^#{1,3}\s*(Abstract|Keywords?)\b", re.I)


def mask_quoted(text: str) -> str:
    for rx in _QUOTE_SPANS:
        text = rx.sub(lambda m: " " * len(m.group(0)), text)
    return text


def visible_len(sent: str) -> int:
    """마크다운 장식·링크 주소·영문 삽입구를 뺀 길이 — 한국어 산문의 부담만 센다.

    괄호 안이 영문·숫자 위주이면(서지 인용 `(Lupu & Hanbury, 2013)`, 용어 원어 병기
    `(competency question, CQ)`) 길이에서 뺀다. 규격 V1 이 요구하는 원어 병기가 규격 S3 을
    위반하게 만들면 두 규칙이 서로를 무효화하기 때문이다. 한국어 삽입구는 그대로 센다.
    """
    s = LINK.sub(r"\1", sent)
    s = MATH.sub("M", s)
    s = s.replace("**", "").replace("`", "")

    def drop_latin_paren(m: re.Match[str]) -> str:
        inner = m.group(1)
        hangul = len(re.findall(r"[가-힣]", inner))
        latin = len(re.findall(r"[A-Za-z0-9]", inner))
        return "" if latin > hangul else m.group(0)

    s = re.sub(r"\(([^()]*)\)", drop_latin_paren, s)
    return len(s.strip())


def blocks(lines: list[str]) -> list[tuple[int, str, list[int]]]:
    """검사 대상 문단 목록 — (시작행, 문단 텍스트, 글자별 행번호).

    연속한 산문 행을 한 문단으로 잇는다. 표·수식·코드·제목·서지·영문 절은 제외한다.
    문단 **바로 앞 줄**에 `<!-- style-ok: 사유 -->` 가 있으면 그 문단은 통째로 면제한다 —
    열거 문장(시스템 정의·자원 계수·수식)처럼 분할이 오히려 뜻을 해치는 자리를 위한 것이며,
    사유를 적게 해 남용을 막는다.
    """
    out: list[tuple[int, str, list[int]]] = []
    buf: list[str] = []
    owner: list[int] = []
    start = 0
    in_fence = False
    in_refs = False
    in_english = False
    pending_exempt = False

    exempt_block = [False]

    def flush() -> None:
        nonlocal buf, owner, start
        if buf:
            text = " ".join(buf)
            # 영문 문단(영문 제목·초록·서지 조각)은 대상이 아니다 — 규격은 한국어 산문의 어체다.
            hangul = len(re.findall(r"[가-힣]", text))
            latin = len(re.findall(r"[A-Za-z]", text))
            if hangul * 2 >= latin and not exempt_block[0]:
                out.append((start, text, owner))
        exempt_block[0] = False
        buf, owner = [], []

    for i, raw in enumerate(lines, 1):
        line = raw.rstrip()
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            flush()
            continue
        if in_fence:
            continue
        if REFS_HEAD.match(line.strip()):
            in_refs = True
        if in_refs:
            continue
        if line.startswith("#"):
            in_english = bool(EN_HEAD.match(line.strip()))
            flush()
            continue
        if in_english:
            continue
        if not line.strip() or SKIP_LINE.match(line):
            if "<!-- style-ok" in line:
                pending_exempt = True
            flush()
            continue
        text = re.sub(r"^\s*(?:>\s*|[-*]\s+|\d+\.\s+)", "", line)
        if not buf:
            start = i
            exempt_block[0] = pending_exempt
            pending_exempt = False
        buf.append(text)
        owner += [i] * (len(text) + 1)
    flush()
    return out


def check_file(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    exempt = {i for i, ln in enumerate(lines, 1) if "<!-- style-ok" in ln}
    fails: list[str] = []

    for start, text, owner in blocks(lines):
        def lineno(pos: int) -> int:
            return owner[pos] if pos < len(owner) else start

        # 표·그림 캡션은 산문이 아니라 라벨이다 — 길이·볼드 규칙의 대상이 아니다.
        is_caption = bool(re.match(r"\*\*(표|그림)\s*\d", text))
        if is_caption:
            continue

        masked = mask_quoted(text)

        # T2 · 은유·구어
        for pat, fix in BANNED_LEXICON:
            for m in re.finditer(pat, masked):
                ln = lineno(m.start())
                if ln in exempt:
                    continue
                fails.append(f"{path}:{ln}: [T2] 구어·은유 표현 “{text[m.start():m.end()]}” → {fix}")

        # T5 · 주장 문장 볼드
        for m in BOLD.finditer(text):
            inner = m.group("inner")
            if not PREDICATE_END.search(inner):
                continue
            ln = lineno(m.start())
            if ln in exempt:
                continue
            head = inner if len(inner) <= 34 else inner[:32] + "…"
            fails.append(f"{path}:{ln}: [T5] 주장 문장에 볼드 — “{head}” (볼드는 용어 최초 등장만)")

        # S3 · 문장 길이 · T3 · 문두 접속어
        pos = 0
        for m in list(SENT_SPLIT.finditer(text)) + [None]:
            end = m.end() if m else len(text)
            sent = text[pos:end].strip()
            spos = pos
            pos = end
            if not sent:
                continue
            ln = lineno(spos)
            if ln in exempt:
                continue
            if BANNED_OPENERS.match(sent.lstrip("*_ ")):
                bad = BANNED_OPENERS.match(sent.lstrip("*_ ")).group(1)
                fails.append(
                    f"{path}:{ln}: [T3] 문두 접속어 “{bad}” → 그러나·따라서·이러한·특히·반면·더욱이·요컨대"
                )
            n = visible_len(sent)
            if n > MAX_SENT_CHARS:
                head = sent[:36].replace("\n", " ")
                fails.append(f"{path}:{ln}: [S3] 문장 {n}자 > {MAX_SENT_CHARS}자 — “{head}…”")
    return fails


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--warn", action="store_true", help="위반을 출력하되 종료코드 0")
    ap.add_argument("--stats", action="store_true", help="라벨별 집계만 출력")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    targets = [root / "paper" / "manuscript" / "stage3_source.md"]
    targets += sorted((root / "paper" / "submission").rglob("*.md"))
    targets = [t for t in targets if t.exists()]
    if not targets:
        print("대상 부재: paper/manuscript/stage3_source.md · paper/submission/**/*.md")
        return 2

    fails: list[str] = []
    for f in targets:
        fails += check_file(f)

    if args.stats:
        from collections import Counter

        c = Counter(re.search(r"\[(\w+)\]", ln).group(1) for ln in fails if re.search(r"\[(\w+)\]", ln))
        for label, n in sorted(c.items()):
            print(f"{label}: {n}")
        print(f"합계 {len(fails)}건 · 대상 {len(targets)}개 파일")
        return 0 if not fails or args.warn else 1

    for line in fails:
        print(line)
    if fails:
        print(f"\n{'경고' if args.warn else '실패'}: 문체 규격 위반 {len(fails)}건 (paper/STYLE-KO-ACADEMIC.md)")
        return 0 if args.warn else 1
    print(f"통과: {len(targets)}개 파일 · 문체 규격 (S3·T2·T3·T5)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
