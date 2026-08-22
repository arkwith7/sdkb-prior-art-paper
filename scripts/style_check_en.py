#!/usr/bin/env python3
"""scripts/style_check_en.py — 영문 학술 문체 규격의 기계 검사 (paper/STYLE-EN-ACADEMIC.md v1).

용법:  python scripts/style_check_en.py [--root .] [--warn]
종료:  0 = 통과(또는 --warn) · 1 = 위반 · 2 = 대상 부재

무엇을 보는가 (규격 §8)
  S3  문장 길이 ≤ 30 단어 (인용·수식·괄호 기호 제외)
  T1  `this study / the present study` 문단당 1회 초과 → 경고
  T3  it was found that / it can be seen that / it should be noted that
  T4  of … of … of 3중 연쇄 → 경고
  T5  볼드 안의 finite verb (주장 문장 볼드)
  T6  강조 부사 (clearly, obviously, very, …) · 통계 맥락 없는 significantly
  T7  구어·은유 (break, catch, swap in, plug in, haystack, readout, …)
  T8  영국식 철자 → 경고
  T9  축약형 (don't, can't, it's, …)
  H1  소제목의 finite verb · 의문형
  V   판정 강도 금지 구문 (verdicts.yaml 의 영문 대응, 규격 §4)
  J   highlights.md 불릿 3–5개 · 각 ≤ 85자

설계 메모 — style_check.py 와 같은 원칙을 따른다.
- 언급은 사용이 아니다: 따옴표·백틱·수식 안은 마스킹한다.
- 문장은 행이 아니라 문단에서 자른다.
- `<!-- style-ok: reason -->` 로 면제한다(그 행, 또는 문단 바로 앞 단독 행이면 문단 전체).
- 표 행(`|`)에는 길이·볼드·문두 규칙을 적용하지 않는다. 어휘 규칙(T6·T7·T9·V)은 적용한다.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MAX_SENT_WORDS = 30

# T3 — 비인칭 피동 관용구
IMPERSONAL = re.compile(
    r"\b(it (was|is|has been) (found|observed|shown|noted|seen)( that)?"
    r"|it (can|could|may|should) be (seen|noted|observed|argued)( that)?)\b", re.I)

# T6 — 강조 부사. significantly 는 같은 문장에 p/CI 가 없을 때만 위반.
INTENSIFIERS = re.compile(
    r"\b(clearly|obviously|very|quite|extremely|importantly|interestingly|remarkably|notably|"
    r"undoubtedly|indeed)\b", re.I)
SIGNIFICANT = re.compile(r"\bsignificant(ly)?\b", re.I)
STAT_CONTEXT = re.compile(r"\bp\s*[=<>]|\bCI\b|confidence interval|Holm|bootstrap|McNemar", re.I)

# T7 — 구어·은유. (정규식, 치환 제안)
BANNED_LEXICON: list[tuple[str, str]] = [
    (r"\bbreaks?\b(?! down)(?=[^.]{0,40}\b(task|path|query|view|gate)s?\b)", "degrade · impair · disrupt"),
    (r"\bkill(s|ed)?\b|\bdies\b", "eliminate · remove"),
    (r"\bcatch(es|ing)?\b(?=[^.]{0,30}\b(fault|regression|defect)s?\b)", "detect"),
    (r"\b(grab|grabs|pull|pulls)\b(?=[^.]{0,30}\b(document|candidate|result)s?\b)", "retrieve"),
    (r"\bswap(ped|s)? (in|out)\b|\bplug(ged|s)? in\b", "substitute · replace · apply"),
    (r"\b(blow|blew|blows) up\b|\bexplode[sd]?\b", "increase sharply"),
    (r"\bleaks?\b(?=[^.]{0,30}\b(regression|into other tasks|to other tasks)\b)", "propagate (leakage 는 qrel 누출 전용)"),
    (r"\bhaystack\b", "large candidate pool"),
    (r"\breadouts?\b", "evaluation · analysis"),
    (r"\binstruments?\b(?=[^.]{0,25}\b(evaluation|measure)\b)", "evaluation procedure"),
    (r"\bsanity checks?\b", "preliminary check"),
    (r"\bladder\b", "reachability by observation level"),
    (r"\bceiling\b(?![^.]{0,60}\breranking ceiling\b)", "reranking ceiling (첫 등장에 정의 1회)"),
    (r"\bresolution\b", "concept density · observation level · matching unit · check granularity"),
    (r"\bentanglement\b|\bentangled\b", "cross-task dependency"),
]

# T8 — 영국식 철자 (경고)
BRITISH = re.compile(
    r"\b(analys(e|ed|es|ing)|behaviour|modelling|modelled|centre|colour|optimis(e|ed|ation)|"
    r"normalis(e|ed|ation)|generalis(e|ed|ation)|characteris(e|ed|ation)|judgement|programme|"
    r"catalogue|labelled|labelling|favour|towards|whilst|amongst)\b")

# T9 — 축약형
CONTRACTIONS = re.compile(r"\b(\w+n't|it's|we've|we're|we'll|that's|there's|isn't|aren't|can't|don't|doesn't|won't)\b", re.I)

# V — 판정 강도 금지 (규격 §4 · glossary.md E절). 확정 시 verdicts.yaml `en:` 로 이관.
VERDICT_FORBIDDEN_EN: list[tuple[str, str]] = [
    (r"\bpartial(ly)? support(ed)?\b", "supported for the primary metric only"),
    (r"\breplicat(ed|es|ion)\b", "observed in both splits"),
    (r"\b(confirmed|held) in both splits\b", "composite prediction held in neither split"),
    (r"\b(refuted|failed)\b(?=[^.]{0,25}\b(hypothesis|prediction|check)\b)", "not supported"),
    (r"\bfailed to replicate\b", "not reproduced; no verdict can be issued"),
    (r"\bdynamic (task )?coupling\b", "cross-task dependency (PLAN-049 실측 전 금지)"),
    (r"\bgate (guarantees|ensures|proves)\b", "the safety of accepted changes was not tested"),
    (r"\b(did|does) not transfer\b|\bno transfer\b", "we could not confirm transfer"),
    (r"\bRAG performance\b", "generation-layer non-regression"),
    (r"\binconclusive\b\.", "absence of transfer and insufficient power are not distinguished"),
    (r"\bmain system\b", "prespecified primary configuration / secondary configuration"),
    (r"\bresource(-side)? metrics do not (represent|reflect)\b", "can still degrade task performance (조건부 형태)"),
    (r"\bunsealed once\b(?![^.]{0,60}\bledger\b)", "all accesses were recorded in the access ledger"),
    (r"\b(robust|consistent|strong) (evidence|effect|gain|improvement)s?\b", "improved · reduced · was observed"),
    (r"\b(demonstrates?|shows?|proves?) conclusively\b|\bclearly (shows?|demonstrates?)\b", "shows (한정 없이)"),
    (r"\bbeyond the scope\b", "we did not … / remains untested"),
    (r"\bfuture work will\b", "would require … (conditional)"),
]

HEADING_FINITE = re.compile(
    r"\b(is|are|was|were|does|do|did|has|have|can|cannot|fails?|failed|shows?|breaks?|"
    r"diverges?|holds?|matters?)\b", re.I)
BOLD = re.compile(r"\*\*(?P<inner>[^*\n]{2,})\*\*")
BOLD_FINITE = re.compile(r"\b(is|are|was|were|does|do|did|has|have|can|cannot|remains?)\b", re.I)
OF_CHAIN = re.compile(r"\bof\b[^.,;]{1,30}\bof\b[^.,;]{1,30}\bof\b", re.I)
THIS_STUDY = re.compile(r"\b(this study|the present study|the present work|this paper)\b", re.I)

_MASK = [
    re.compile(r"`[^`\n]*`"),
    re.compile(r'"[^"\n]*"'),
    re.compile(r"“[^”\n]*”"),
    re.compile(r"\\\([^)]*?\\\)"),
    re.compile(r"\\\[[\s\S]*?\\\]"),
    re.compile(r"\([A-Z][^()]*\d{4}[a-z]?\)"),      # (Author, 2013)
    re.compile(r"\{\{[^}]*\}\}"),
    re.compile(r"!\[[^\]]*\]\([^)]*\)"),
    re.compile(r"\]\([^)]*\)"),
]
STYLE_OK = re.compile(r"<!--\s*style-ok(?::[^>]*)?-->")


def mask(s: str) -> str:
    for rx in _MASK:
        s = rx.sub(lambda m: " " * len(m.group(0)), s)
    return s


def sentences(par: str):
    # 약어·소수점 보호
    s = re.sub(r"\b(e\.g|i\.e|et al|cf|vs|Fig|Eq|Sec|Tab)\.", lambda m: m.group(0).replace(".", "§"), par)
    s = re.sub(r"(\d)\.(\d)", r"\1§\2", s)
    for sent in re.split(r"(?<=[.!?])\s+", s):
        yield sent.replace("§", ".").strip()


def paragraphs(lines: list[str]):
    """(시작행번호, 텍스트, 면제여부) — 빈 행으로 구분. 직전 단독 style-ok 행이면 면제."""
    buf: list[str] = []
    start = 0
    exempt_next = False
    for i, line in enumerate(lines, 1):
        if line.strip() == "":
            if buf:
                yield start, buf, exempt_next
                buf = []
                exempt_next = False
            continue
        if STYLE_OK.fullmatch(line.strip()) and not buf:
            exempt_next = True
            continue
        if not buf:
            start = i
        buf.append(line)
    if buf:
        yield start, buf, exempt_next


def check_file(path: Path, fails: list[str], warns: list[str]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    in_fence = False
    clean: list[str] = []
    for ln in lines:
        if ln.strip().startswith("```"):
            in_fence = not in_fence
            clean.append("")
            continue
        clean.append("" if in_fence else ln)
    bib_at = next((i for i, ln in enumerate(clean)
                   if ln.strip() in ("# References", "# 참고문헌")), len(clean))
    clean = clean[:bib_at]

    for start, buf, exempt in paragraphs(clean):
        if exempt:
            continue
        rows = [(start + k, ln) for k, ln in enumerate(buf) if not STYLE_OK.search(ln)]
        if not rows:
            continue
        first = rows[0][1].lstrip()
        is_heading = first.startswith("#")
        is_table = first.startswith("|")
        is_bullet = bool(re.match(r"[-*]\s|\d+\.\s", first))
        # 불릿 목록은 항목마다 문장으로 자른다 — 이어 붙이면 한 문장으로 세어 S3 오탐이 난다
        raw = ("\n" if is_bullet else " ").join(ln.strip() for _, ln in rows)
        text = mask(raw)
        loc = f"{path}:{start}"

        # 어휘 규칙 — 모든 블록
        for rx, hint in BANNED_LEXICON:
            for m in re.finditer(rx, text):
                fails.append(f"{loc}: [T7] 구어·은유 “{m.group(0)}” → {hint}")
        for rx, hint in VERDICT_FORBIDDEN_EN:
            for m in re.finditer(rx, text, re.I):
                fails.append(f"{loc}: [V] 판정 강도 “{m.group(0)}” → {hint}")
        for m in CONTRACTIONS.finditer(text):
            fails.append(f"{loc}: [T9] 축약형 “{m.group(0)}”")
        for m in BRITISH.finditer(text):
            warns.append(f"{loc}: [T8] 영국식 철자 “{m.group(0)}” — 미국식으로 통일")

        if is_heading:
            title = re.sub(r"^#+\s*[\d.]*\s*", "", first).strip()
            t = mask(title)
            if t.rstrip().endswith("?") or HEADING_FINITE.search(re.sub(r"\(.*?\)", "", t)):
                fails.append(f"{loc}: [H1] 서술형·의문형 소제목 “{title}”")
            continue
        if is_table:
            continue

        # 산문 전용
        for sent in (text.split("\n") if is_bullet else sentences(text)):
            words = [w for w in re.findall(r"[A-Za-z][A-Za-z'’\-]*", sent)]
            if len(words) > MAX_SENT_WORDS:
                fails.append(f"{loc}: [S3] 문장 {len(words)}단어 > {MAX_SENT_WORDS} — “{sent[:60].strip()}…”")
            if IMPERSONAL.search(sent):
                fails.append(f"{loc}: [T3] 비인칭 피동 “{IMPERSONAL.search(sent).group(0)}”")
            for m in INTENSIFIERS.finditer(sent):
                fails.append(f"{loc}: [T6] 강조 부사 “{m.group(0)}”")
            if SIGNIFICANT.search(sent) and not STAT_CONTEXT.search(sent):
                fails.append(f"{loc}: [T6] 통계 맥락 없는 “significant” — p/CI 를 같은 문장에 두거나 삭제")
            if OF_CHAIN.search(sent):
                warns.append(f"{loc}: [T4] of-사슬 3중 — 동사로 풀 것")
        if not is_bullet and len(THIS_STUDY.findall(text)) > 1:
            warns.append(f"{loc}: [T1] ‘this study/paper’ 문단당 {len(THIS_STUDY.findall(text))}회 — `we` 로")
        for m in BOLD.finditer(raw):
            inner = m.group("inner")
            if BOLD_FINITE.search(inner) and not inner.rstrip().endswith("."):
                fails.append(f"{loc}: [T5] 볼드 안의 주장 문장 “{inner[:40]}”")


def check_highlights(path: Path, fails: list[str]) -> None:
    bullets = [ln for ln in path.read_text(encoding="utf-8").splitlines()
               if re.match(r"\s*[-*•]\s", ln)]
    if not 3 <= len(bullets) <= 5:
        fails.append(f"{path}: [J] Highlights 불릿 {len(bullets)}개 — 3–5개여야 한다")
    for b in bullets:
        body = re.sub(r"^\s*[-*•]\s*", "", b)
        if len(body) > 85:
            fails.append(f"{path}: [J] Highlight {len(body)}자 > 85 — “{body[:50]}…”")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--warn", action="store_true", help="위반을 경고로만 보고한다")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    targets = [root / "paper" / "manuscript" / "en_source.md"]
    targets += sorted((root / "paper" / "submission" / "en").glob("*.md")) if (root / "paper" / "submission" / "en").exists() else []
    targets = [t for t in targets if t.exists()]
    if not targets:
        print("대상 부재: paper/manuscript/en_source.md · paper/submission/en/*.md")
        return 2

    fails: list[str] = []
    warns: list[str] = []
    for t in targets:
        if t.name == "highlights.md":
            check_highlights(t, fails)
        check_file(t, fails, warns)

    for w in warns:
        print(f"[경고] {w}")
    for f in fails:
        print(f)
    if fails:
        print(f"\n{'경고' if args.warn else '실패'}: 영문 문체 규격 위반 {len(fails)}건 (paper/STYLE-EN-ACADEMIC.md)")
        return 0 if args.warn else 1
    print(f"통과: {len(targets)}개 파일 · 영문 문체 규격 (S3·T3·T5·T6·T7·T9·H1·V·J) · 경고 {len(warns)}건")
    return 0


if __name__ == "__main__":
    sys.exit(main())
