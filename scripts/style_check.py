#!/usr/bin/env python3
"""scripts/style_check.py — 한국어 학술 문체 규격의 기계 검사 (paper/STYLE-KO-ACADEMIC.md).

용법:  python scripts/style_check.py [--root .] [--warn] [--stats]
종료:  0 = 통과(또는 --warn) · 1 = 위반 · 2 = 대상 부재

무엇을 보는가 — 규격 v2 의 열한 항목을 본다.
  S3  문장 길이 ≤ 90자 (공백 포함)
  T2  은유·구어 동사 금지 (치환표)
  T3  문두 접속어는 표준 학술 연결어만 (그래서·그런데·하지만 금지)
  T5  볼드는 용어의 최초 등장에만 — 볼드 안에 종결어미가 있으면 주장 문장이다
  T6  T2 를 **표 셀·그림 캡션·소제목**에도 적용 (규격 v2 · 산문 밖의 사각지대)
  T7  축약형 금지 — 됐다→되었다 · 했다→하였다
  H1  소제목은 명사구형 — 서술형·의문형 종결 금지
  V5  `task` 의 번역은 "태스크" 로 단일화 (예외 합성어만 허용)
  V6  표·그림 번호는 등장 순서로 1부터 연번 — 중복·결번 금지
  V7  `E` 라벨은 본문에서 **평가환경 하나**만 가리킨다 — 적격심사 항을 `E` 로 부르지 않는다
  X1  관통 예시 번호는 1부터 연번이며 증거 지위 표식을 갖는다
  X2  합성 예시는 실제 판정으로 오독되는 판정 낱말을 쓰지 않는다

**S1·S2·S4·T1·T4·V1–V4 는 사람이 지킨다.** 검사기 통과는 규격 준수의 필요조건이지 충분조건이
아니다. `check_verdicts.py` 가 판정 강도의 표류를 막듯, 이 파일은 **어체의 표류**만 막는다.

설계 메모
- **대상은 투고 파생본 계열뿐이다**(산문 소스 + 조립 산출물). 작업 정본과 supplementary 는
  **감사 기록**이므로 제외한다 — 과거 문장을 소급해 다듬으라는 요구가 되기 때문이다
  (`submission_check.py` 가 정본을 제외하는 것과 같은 이유).
- **언급(mention)은 사용(use)이 아니다.** 따옴표·백틱 안은 마스킹해 T2·T3 위반으로 세지 않는다.
- 문장은 **행이 아니라 문단**에서 자른다. 원고는 100열 안팎에서 손으로 줄바꿈하므로 행 단위로
  세면 한 문장이 여러 조각으로 갈려 길이 검사가 무력해진다.
- 길이(S3)·볼드(T5)·문두 접속어(T3)는 산문에만 적용한다. 표 셀은 개조식이 정상이므로 길이와
  종결형을 따지지 않는다. 다만 **어휘 규칙(T2·T7·V5)은 표·캡션·소제목에도 적용한다**(T6) —
  규격 v1 이 산문만 보아 표 안의 구어체가 통째로 남았기 때문이다.
- **판정 문구는 문체 규칙보다 우선한다**(CLAUDE.md §0.8 · `paper/verdicts.yaml`). 사전등록
  원문에 있는 축약형은 `VERDICT_LITERALS` 로 마스킹한다 — 인용이므로 원문 충실성이 앞선다.
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
    # 규격 v2 증설 (2026-08-16) — 외부 검토가 표 셀·소제목에서 실제로 지적한 표현들이다.
    # 산문에서는 이미 사라졌으나 T6 이전에는 표·제목이 검사 대상이 아니어서 남아 있었다.
    (r"(?<![가-힣])잴(?=\s)|(?<![가-힣])재\s*보(?=[지아았])", "측정하다"),
    (r"무너뜨리|무너지|무너진|무너졌", "훼손하다 · 기각되다"),
    (r"멀쩡", "정상적인"),
    (r"일부러", "의도적으로"),
    (r"잡아내|잡아냈|잡아낸", "검출하다"),
    (r"말로\s*풀면", "조건의 내용"),
    # 성능 상한의 은유. 영어 performance ceiling 은 관용이나 국문 학술 레지스터에서는
    # "상한"이 표준어이고, 은유는 정의 없이 표·제목에 먼저 등장하기 쉽다(V1 위반 경로).
    (r"천장", "상한 · 재순위화 상한(reranking ceiling)"),
    # 아래 셋도 같은 경로로 남아 있던 은유·구어다. "해상도"는 한 낱말이 네 뜻으로
    # 쓰이고 있었으므로 V2(동의어 교체 금지)의 반대 방향 위반이기도 하다 —
    # 뜻마다 다른 용어를 쓴다: 개념 밀도 · 관찰 수준 · 매칭 단위 · 검사 세밀도.
    (r"해상도", "개념 밀도 · 관찰 수준 · 단위 · 검사 세밀도 (뜻에 따라 가른다)"),
    (r"사다리", "수준별 표 · 관찰 수준별 도달성"),
    (r"손\s*대(지|고|면|는)", "변경하다"),
    # 원고 가독성 점검(2026-08-20) — 뜻은 통하지만 한국어 학술문에서 낯설거나 기계적인 표현.
    # 문맥에 따라 더 구체적인 보통말로 풀어 쓰도록 한다.
    (r"정박\s*(검색\s*)?평가", "인용을 기준으로 한 평가 · 인용에 근거한 평가"),
    (r"판독", "평가 · 분석 · 결과 확인"),
    (r"계측기", "평가 절차 · 측정 도구 · 평가 체계"),
    (r"충전\s*정도", "인스턴스 데이터가 채워진 정도"),
    (r"검출\s*표면", "검출 가능한 제약 · 검사 범위"),
    (r"갈림|갈렸", "결과가 서로 다르다 · 결과가 일치하지 않다"),
]

# T3 — 문장 첫머리에서 금지되는 접속어.
BANNED_OPENERS = re.compile(r"^(그래서|그런데|하지만)(?=[\s,])")

# T7 — 축약형. 학술 레지스터에서는 본디 형태를 쓴다.
CONTRACTIONS: list[tuple[str, str]] = [
    (r"됐", "되었"),
    (r"했", "하였"),
    (r"봤", "보았"),
    (r"줬", "주었"),
]

# T7·T2 의 예외 — 사전등록·판정 사전의 **원문**. 인용이므로 어체를 고치지 않는다
# (CLAUDE.md §0.8 · paper/verdicts.yaml). 스팬을 마스킹해 위반으로 세지 않는다.
VERDICT_LITERALS = [
    re.compile(r"반복\s*관측됐다"),
    re.compile(r"확증하지\s*못했다"),
]

# V5 — `task` 의 번역은 "태스크" 로 단일화한다. 아래는 **확립된 번역 관행**이거나
# 애초에 task 가 아닌 낱말(assignment·future work)이므로 예외로 둔다.
TASK_TERM_ALLOWED = [
    re.compile(r"과제\s*기반"),          # 과제 기반 평가 (task-based evaluation)
    re.compile(r"후속\s*과제"),          # future work
    re.compile(r"다음\s*과제"),
    re.compile(r"연구\s*과제"),
    re.compile(r"별개의?\s*과제"),
]
TASK_TERM = re.compile(r"과제")

# H1 — 소제목의 서술형·의문형 종결. 명사구형이면 여기에 걸리지 않는다.
HEADING_FINITE = re.compile(
    r"(는가|은가|인가|던가|을까|한가"
    r"|한다|된다|이다|아니다|않다|않는다|없다|있다"
    r"|았다|었다|였다|겠다|린다|진다|난다|둔다|본다|온다|간다|넣는다)$"
)
HEADING_TRAILING_PAREN = re.compile(r"\s*[(（][^()（）]*[)）]\s*$")

# V6 — 표·그림 캡션. 본문 참조("표 8의 …")가 아니라 **캡션 행**만 번호의 원천으로 센다.
CAPTION = re.compile(r"^\*\*(?P<kind>표|그림)\s*(?P<num>\d+)[.\s]")

# V7 — 라벨 이름공간 `E` (CLAUDE.md §0.9 규칙 5 · 2026-08-29).
# **무엇을 막는가.** 본문 약어표는 `E1` 을 **평가환경**(다층 평가 벤치마크)으로 등재하는데,
# 사전등록 PLAN-035 는 같은 `E1`–`E7` 을 **적격심사 일곱 항**으로 쓴다. 본문이 적격심사를 `E`
# 로 부르는 순간 한 문단 안에서 `E1` 이 두 가지를 가리킨다 — `S`-시리즈와 교훈 `L` 에서 이미
# 두 번 난 사고다. 사전등록 문서의 라벨은 추적성을 위해 그대로 두고(§0.9 규칙 1), 막는 것은
# **본문이 그 라벨을 끌어다 쓰는 것**뿐이다.
# 신호는 둘이다 — ① 본문에 `E2`–`E7` 이 나타나면 그것은 평가환경일 수 없다(평가환경은 하나다).
# ② 같은 행에서 `E` 라벨과 "적격심사" 가 함께 나타난다.
E_LABEL = re.compile(r"\bE[1-9]\b")
E_NON_ENV = re.compile(r"\bE[2-9]\b")
E_SCREENING = re.compile(r"적격\s*심사")

# PLAN-087 — 관통 예시의 증거 지위. 합성 예시는 설명·판정식 데모일 뿐 실제 릴리스
# 판정이 아니므로, 예시 머리말에서 둘을 기계적으로 구분한다.
EXAMPLE_HEAD = re.compile(r"^>\s*\*\*예시\s*(?P<num>\d+)\s*[·.]\s*(?P<title>[^*]+)\*\*")
EVIDENCE_MARKERS = ("합성 설명", "합성 실행", "탐색 사례", "사전등록 집계")
SYNTHETIC_VERDICT = re.compile(r"(최종\s*)?(승인|거부|채택|기각|확증|부분\s*지지)")

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
    for rx in VERDICT_LITERALS:
        text = rx.sub(lambda m: " " * len(m.group(0)), text)
    for rx in TASK_TERM_ALLOWED:
        text = rx.sub(lambda m: " " * len(m.group(0)), text)
    return text


def lexical_hits(masked: str, raw: str) -> list[tuple[int, str, str]]:
    """어휘 규칙(T2·T7·V5)의 위반 — (위치, 라벨, 메시지). 산문·표·캡션·소제목에 공통이다.

    T6 이 요구하는 것이 이 공통 적용이다. 길이(S3)·볼드(T5)·문두 접속어(T3)와 달리 어휘
    규칙은 문장 형식과 무관하므로 표 셀에서도 그대로 성립한다.
    """
    hits: list[tuple[int, str, str]] = []
    for pat, fix in BANNED_LEXICON:
        for m in re.finditer(pat, masked):
            hits.append((m.start(), "T2", f"구어·은유 표현 “{raw[m.start():m.end()]}” → {fix}"))
    for pat, fix in CONTRACTIONS:
        for m in re.finditer(pat, masked):
            head = raw[max(0, m.start() - 3):m.end() + 2].strip()
            hits.append((m.start(), "T7", f"축약형 “{head}” → “{fix}~” (사전등록 인용은 style-ok)"))
    for m in TASK_TERM.finditer(masked):
        hits.append((m.start(), "V5", "용어 이중 번역 “과제” → “태스크” (예외 합성어만 허용)"))
    return hits


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
        # 다만 **어휘 규칙은 그대로 적용한다**(T6) — 캡션의 구어체가 규격 v1 의 사각지대였다.
        is_caption = bool(re.match(r"\*\*(표|그림)\s*\d", text))

        masked = mask_quoted(text)

        # T2 · 은유·구어 / T7 · 축약형 / V5 · 용어 단일화
        for pos, label, msg in lexical_hits(masked, text):
            ln = lineno(pos)
            if ln in exempt:
                continue
            fails.append(f"{path}:{ln}: [{label}] {msg}")

        if is_caption:
            continue

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

    fails += check_lines(path, lines, exempt)
    fails += check_numbering(path, lines)
    fails += check_label_namespace(path, lines, exempt)
    fails += check_running_examples(path, lines, exempt)
    return fails


def heading_is_finite(title: str) -> str | None:
    """서술형·의문형으로 끝나는 소제목이면 그 조각을 돌려준다(H1). 명사구형이면 None."""
    body = re.sub(r"^#+\s*", "", title).strip()
    body = re.sub(r"^[\d.]+\s*", "", body)
    for seg in re.split(r"\s*[—–]\s*", body):
        seg = seg.strip().rstrip(".·")
        while HEADING_TRAILING_PAREN.search(seg):
            seg = HEADING_TRAILING_PAREN.sub("", seg).strip()
        seg = re.sub(r"\*\*|`", "", seg).strip().rstrip(".")
        if HEADING_FINITE.search(seg):
            return seg
    return None


def check_lines(path: Path, lines: list[str], exempt: set[int]) -> list[str]:
    """산문 밖의 검사 대상 — 표 셀 · 소제목 · 그림 alt (T6 · H1).

    `blocks()` 는 이들을 통째로 건너뛴다. 규격 v1 이 표 안의 구어체를 한 건도 잡지 못한
    이유가 여기에 있었다. 길이·볼드·문두 접속어는 여전히 적용하지 않는다 — 표 셀의
    개조식(명사형 종결)은 규격이 허용하는 형태이기 때문이다.
    """
    fails: list[str] = []
    in_fence = False
    in_refs = False
    for i, raw in enumerate(lines, 1):
        line = raw.rstrip()
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or in_refs:
            continue
        if REFS_HEAD.match(line.strip()):
            in_refs = True
            continue
        stripped = line.strip()
        is_head = stripped.startswith("#")
        is_row = stripped.startswith("|") and not re.fullmatch(r"[|\-: ]+", stripped)
        is_alt = stripped.startswith("![")
        if not (is_head or is_row or is_alt):
            continue
        if i in exempt or EN_HEAD.match(stripped):
            continue
        if len(re.findall(r"[가-힣]", stripped)) * 2 < len(re.findall(r"[A-Za-z]", stripped)):
            continue
        for _, label, msg in lexical_hits(mask_quoted(stripped), stripped):
            fails.append(f"{path}:{i}: [{label}] {msg} (표·캡션·소제목)")
        if is_head:
            seg = heading_is_finite(stripped)
            if seg:
                fails.append(f"{path}:{i}: [H1] 소제목이 서술형 — “{seg}” (명사구형으로 쓴다)")
    return fails


def check_label_namespace(path: Path, lines: list[str], exempt: set[int]) -> list[str]:
    """`E` 라벨은 본문에서 평가환경 하나만 가리킨다(V7 · CLAUDE.md §0.9 규칙 5)."""
    fails: list[str] = []
    in_fence = False
    for i, raw in enumerate(lines, 1):
        if raw.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or i in exempt:
            continue
        line = mask_quoted(raw)
        m = E_NON_ENV.search(line)
        if m:
            fails.append(
                f"{path}:{i}: [V7] `E` 라벨 {m.group(0)} — 본문의 `E` 는 평가환경 하나뿐이다 "
                f"(적격심사는 서술형으로 “적격심사 일곱 항”)"
            )
            continue
        if E_LABEL.search(line) and E_SCREENING.search(line):
            fails.append(
                f"{path}:{i}: [V7] 적격심사를 `E` 라벨로 부른다 — 서술형으로 쓴다 "
                f"(사전등록 문서의 `E1`–`E7` 은 그대로 두고 대응은 crosswalk 에 적는다)"
            )
    return fails


def check_numbering(path: Path, lines: list[str]) -> list[str]:
    """표·그림 번호는 등장 순서로 1부터 연번이어야 한다(V6) — 중복·결번 금지."""
    fails: list[str] = []
    seen: dict[str, list[tuple[int, int]]] = {"표": [], "그림": []}
    for i, raw in enumerate(lines, 1):
        m = CAPTION.match(raw.strip())
        if m:
            seen[m.group("kind")].append((int(m.group("num")), i))
    for kind, items in seen.items():
        for order, (num, ln) in enumerate(items, 1):
            if num != order:
                fails.append(
                    f"{path}:{ln}: [V6] {kind} 번호가 등장 순서와 다르다 — "
                    f"{kind} {num} 은 {order} 번째 캡션 (1부터 연번 · 중복·결번 금지)"
                )
    return fails


def check_running_examples(path: Path, lines: list[str], exempt: set[int]) -> list[str]:
    """PLAN-087 examples are sequential and carry an explicit evidence-status marker."""
    fails: list[str] = []
    found: list[tuple[int, int, str]] = []
    for lineno, raw in enumerate(lines, 1):
        match = EXAMPLE_HEAD.match(raw.strip())
        if not match or lineno in exempt:
            continue
        number = int(match.group("num"))
        title = match.group("title").strip()
        found.append((number, lineno, title))
        marker = next((item for item in EVIDENCE_MARKERS if item in title), None)
        if marker is None:
            fails.append(
                f"{path}:{lineno}: [X1] 예시 {number}의 증거 지위 표식 누락 — "
                f"{' · '.join(EVIDENCE_MARKERS)} 중 하나를 머리말에 쓴다"
            )
        elif marker.startswith("합성"):
            verdict = SYNTHETIC_VERDICT.search(title)
            if verdict:
                fails.append(
                    f"{path}:{lineno}: [X2] 합성 예시 머리말의 판정 낱말 “{verdict.group(0)}” — "
                    "합성 실행은 행 수와 판정식의 작동만 진술한다"
                )
    for expected, (number, lineno, _) in enumerate(found, 1):
        if number != expected:
            fails.append(
                f"{path}:{lineno}: [X1] 예시 {number}는 {expected}번째 예시 — 1부터 연번으로 쓴다"
            )
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
    # `paper/submission/en/` 은 영문 투고 산출물이다 — 한국어 학술 문체 규격의 대상이 아니다.
    # 규격이 재는 것(서술어 어체·문두 접속어·축약형·`task` 번역)은 전부 한국어 문장의 성질이며,
    # 영문에 적용하면 위반이 아니라 소음이 나온다. **면제가 아니라 적용 범위의 문제다** —
    # 영문 산출물은 `submission_check` 의 D2·D3·D7·D8·D9 와 링크 검사를 그대로 받는다.
    en_dir = root / "paper" / "submission" / "en"
    skipped = [t for t in targets if en_dir in t.parents]
    targets = [t for t in targets if en_dir not in t.parents]
    for t in skipped:
        print(f"[skip] {t.relative_to(root)} — 영문 산출물 (한국어 문체 규격 비대상)")
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
    print(f"통과: {len(targets)}개 파일 · 문체 규격 (S3·T2·T3·T5·T6·T7·H1·V5·V6·V7·X1·X2)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
