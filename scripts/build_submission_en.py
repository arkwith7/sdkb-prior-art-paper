#!/usr/bin/env python3
"""scripts/build_submission_en.py — 영문 투고본을 **한국어 파생본에서 조립한다** (CLAUDE.md §2.3).

**왜 손으로 번역하지 않는가.** 원고에는 표 12개와 그림 8개가 있고, 그 안의 수치는 전부 실행된
코드의 출력이다(§1-1). 영문본을 통째로 다시 타자하면 **수치를 손으로 옮겨 적게 되고**, 그것이
정확히 `build_submission_stage3.py` 가 막으려고 존재하는 실패 양상이다. 그래서 같은 규율을 한
단계 더 적용한다 — **산문은 사람이 영문으로 쓰고, 표와 그림은 한국어 파생본에서 복사한 뒤
라벨만 치환한다.**

배선:

    paper/manuscript/en_source.md      영문 산문 (사람이 쓴다 · {{TABLE:n}} · {{FIGURE:n}} 지시자)
      + paper/submission/manuscript.md 한국어 파생본 (표·그림·캡션의 복사 원본)
      → paper/submission/en/manuscript.md

지시자:

    {{TABLE:7}}      한국어 파생본의 `**표 7. …**` 캡션과 뒤따르는 표를 가져와 라벨을 치환한다
    {{FIGURE:3}}     `![그림 3. …](경로)` 와 뒤따르는 `**그림 3.** …` 설명을 가져와 치환한다

**수치 불변을 기계가 강제한다.** 치환 전후의 수치 토큰이 하나라도 달라지면 실패한다(rc 2).
절 번호(`§4.5`)는 수치로 세지 않는다 — 재번호는 수치 변경이 아니기 때문이다. 이 규칙은
`build_submission_stage3.py` 의 `measurements()` 와 같은 정의를 쓴다.

**용어 치환은 목록으로만 한다.** `TERMS` 는 (한국어, 영문) 쌍이며 **긴 것부터** 적용한다.
치환 후에도 한글이 남으면 그 자리를 전부 보고하고 실패한다 — 조용히 한글이 섞인 영문 표를
내보내는 것이 이 스크립트가 막아야 할 유일한 실패다.

CLI:
    uv run python scripts/build_submission_en.py            # 조립
    uv run python scripts/build_submission_en.py --check    # 조립 결과가 디스크와 같은지만 본다
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROSE = ROOT / "paper" / "manuscript" / "en_source.md"
KOREAN = ROOT / "paper" / "submission" / "manuscript.md"
# **본문이 완성되기 전까지는 초안 경로로 낸다.** `paper/submission/**` 는 `submission_check` 의
# 대상이고, 절이 아직 없는 원고는 D9(절 참조 도달성)에서 정당하게 실패한다. 미완성 산출물을
# 검사 대상 트리에 두고 게이트를 빨갛게 만들면, 다음 세션은 그 빨강을 정상으로 여기게 된다.
# 본문 번역이 끝나면 이 경로를 `paper/submission/en/manuscript.md` 로 바꾼다 — 그때 D2·D3·D7·
# D8·D9 와 링크 검사가 영문 원고에도 걸린다.
TARGET = ROOT / "paper" / "manuscript" / "en_draft.md"

TABLE_RE = re.compile(r"\{\{TABLE:(\d+)\}\}")
FIGURE_RE = re.compile(r"\{\{FIGURE:(\d+)\}\}")

# 수치 토큰 — 절 번호는 뺀다(§4.9 → §4.5 는 재번호이지 수치 변경이 아니다).
NUMERIC = re.compile(r"\d+(?:[.,]\d+)*")
SECTION_TOKEN = re.compile(r"§\s?\d+(?:\.\d+)*")
HANGUL = re.compile(r"[가-힣]")


def fail(msg: str) -> None:
    print(f"[en] 실패 — {msg}", file=sys.stderr)
    raise SystemExit(2)


def measurements(text: str) -> list[str]:
    return NUMERIC.findall(SECTION_TOKEN.sub("", text))


# ── 셀·캡션 번역 ─────────────────────────────────────────────────────────────
# **왜 용어 치환이 아니라 셀 사전인가.** 표 셀에는 한국어 문장이 들어 있어 단어 치환으로는
# 번역되지 않는다. 게다가 부분 문자열 치환은 `대표`·`지표` 를 `대Table`·`지Table` 로 망가뜨린다
# (첫 구현에서 실제로 그랬다). 그래서 **셀 전체를 키로 하는 사전**을 쓰고, 사전에 없는 셀에
# 한글이 남으면 실패한다. 사전은 사람이 쓰고 기계는 **수치가 변하지 않았음만** 보증한다.
#
# 캡션 도입어(`**표 7.` · `![그림 3.` · `**그림 3.**`)는 형태가 고정되어 있으므로 정규식으로
# 처리한다 — 사전에 넣으면 캡션 문장 전체를 키로 잡아야 해서 유지되지 않는다.
# 캡션은 산문이다 — 사전 키로 잡으면 유지되지 않는다. 그래서 **영문 캡션은 사람이 쓰고**,
# 기계는 그 캡션의 수치가 한국어 캡션과 같은지만 본다. 표는 `T<n>`, 그림은 `F<n>` 키다.
CAPTIONS: dict[str, str] = {
    "F1alt": "Figure 1. Study overview — two artifacts and one evaluation environment, the release "
             "approval procedure, and what the four episodes measure.",
    "F1": "**Figure 1.** Study overview. The top band is artifact A1, a resource placing three task "
          "views on one shared T-Box; the middle band is artifact A2, the release gate that reviews "
          "a resource change before it ships; the bottom band is evaluation environment E1, the "
          "four episodes and what each measures. The middle band reads left to right, and a failed "
          "stage stops the ones behind it. T4, shown dashed, is not part of the approval rule "
          "(§3.5.1).",
    "T1": "**Table 1. Position relative to prior work — the contribution is the combination and the "
          "experimental design, not primacy.**",
}

# 셀 사전 — 한국어 셀 **전체**를 키로 하는 완전 일치 치환. 부분 문자열 치환을 쓰지 않는 이유는
# `대표`·`지표` 가 `대Table`·`지Table` 로 망가지기 때문이다(첫 구현에서 실제로 그랬다).
# 지표·게이트·라벨 이름(L0–L3 · T1–T4 · Recall@100 · P0★ · B3 · EP1–EP4)은 이미 라틴 문자이며
# 바꾸면 다른 것을 가리키므로 사전에 없다. 숫자만 든 셀도 없다 — 손대지 않는다.
CELLS: dict[str, str] = {
    # ── 표 1 · 관련연구 대비 위치 ────────────────────────────────────────────
    "연구 흐름": "Research strand",
    "대표 문헌": "Representative work",
    "남는 공백": "Remaining gap",
    "본 연구의 확장": "What this study adds",
    "특허 선행기술 검색과 그래프 활용":
        "Patent prior-art retrieval and the use of graphs",
    "그래프가 성능을 위한 입력 표현에 머물러, 그래프 자체의 변경 통제는 다루지 않는다":
        "The graph serves as an input representation for performance; controlling change in the "
        "graph itself is not addressed",
    "질의 인용 간선 마스킹과 시점·패밀리 분리 위에서, 검색 성능을 자원 변경의 승인 조건으로 "
    "사용하고 그 결합의 **성능 상한**까지 보고":
        "On top of query-citation masking and time/family separation, retrieval performance becomes "
        "an approval condition for resource change, and the **performance ceiling** of that "
        "coupling is reported",
    "온톨로지 품질·진화 검증": "Ontology quality and evolution validation",
    "변경이 온톨로지를 훼손하는가만 보고, 태스크를 훼손하는가는 보지 않는다":
        "Asks only whether a change damages the ontology, not whether it damages a task",
    "형식 검증 위에 3조건 태스크 게이트와 비열등 병합 규칙":
        "A 3-condition task gate and a non-inferiority merge rule on top of formal validation",
    "과제 기반 평가와 다운스트림 평가": "Task-based and downstream evaluation",
    "온톨로지를 비교·선택하는 **기준** 또는 완성 이후의 사후 비교로 사용되었다":
        "Used as a **criterion** for comparing and selecting ontologies, or as a post-hoc "
        "comparison once construction is finished",
    "같은 태스크 성능을 릴리스 **전** 승인식의 항으로 사용":
        "The same task performance becomes a term in the approval rule applied **before** release",
    "자원 지표를 유용성의 대리로 쓰는 관행":
        "The practice of treating resource indicators as proxies for utility",
    "어긋남이 상관 분석 수준에서 보고될 뿐 **통제된 사례와 그에 대한 결정**은 드물다":
        "The mismatch is reported at the level of correlation; **a controlled case and a decision "
        "taken on it** are rare",
    "자원 번들만 교체한 두 조건에서의 통제된 확인과 **승인 판정**(§5.3)":
        "Controlled confirmation in two conditions differing only in the resource bundle, and an "
        "**approval verdict** (§5.3)",
    "공학 정보학의 의미 표현·검증과 응용":
        "Semantic representation, validation and application in engineering informatics",
    "표현의 표준화·구조 준수·응용 성능은 제시되나 **변경의 승인 규칙**은 다루지 않는다":
        "Standardized representation, structural conformance and application performance are "
        "shown; **a rule for approving change** is not addressed",
    "사용 가능성이 아니라 **변경 수용 가능성**을 판정하고 실제 심사 기록을 제시(§5.3)":
        "Judges **whether a change may be accepted** rather than whether the resource is usable, "
        "and reports an actual review (§5.3)",
    "공유 그래프의 교차 도메인 활용": "Cross-domain use of a shared graph",
    "도메인 사이의 영향을 **관찰**하는 데 머문다":
        "Stops at **observing** influence between domains",
    "같은 영향을 승인 조건인 **교차 태스크 비회귀**로 집행":
        "Enforces the same influence as an approval condition — **cross-task non-regression**",
}

TABLE_CAP = re.compile(r"^\*\*표 (\d+)\.")
FIG_IMG = re.compile(r"^!\[그림 (\d+)\.[^\]]*\]\((.*)\)\s*$")
FIG_CAP = re.compile(r"^\*\*그림 (\d+)\.\*\*")


def translate_line(line: str) -> str:
    m = TABLE_CAP.match(line)
    if m:
        return CAPTIONS.get(f"T{m.group(1)}", line)
    m = FIG_IMG.match(line)
    if m:
        # alt 텍스트는 캡션을 재사용하지 않는다 — 같은 문장을 두 번 실으면 수치도 두 번 세어져
        # 불변 검사가 정당하게 실패한다(첫 구현에서 실제로 그랬다). 한국어 alt 가 담는 것은
        # 그림 번호와 짧은 제목이므로 영문도 그렇게 둔다.
        alt = CAPTIONS.get(f"F{m.group(1)}alt")
        if alt is None:
            fail(f"FIGURE {m.group(1)} 의 alt 텍스트가 CAPTIONS 에 없다 — 'F{m.group(1)}alt' 키")
        # 영문본은 한 단계 깊은 곳에 있다(`paper/submission/en/`) — 상대 경로를 그대로 옮기면
        # 그림이 죽는다. 깊이 차이는 배선이 알고 있으므로 사람이 세지 않는다.
        src = m.group(2)
        if src.startswith("../") and not src.startswith("../../"):
            src = "../" + src
        return f"![{alt}]({src})"
    m = FIG_CAP.match(line)
    if m:
        return CAPTIONS.get(f"F{m.group(1)}", line)
    if line.lstrip().startswith("|"):
        return "|".join(CELLS.get(p.strip(), p) for p in line.split("|"))
    return CELLS.get(line.strip(), line)


def translate(text: str) -> str:
    """그림 설명 문단은 캡션 한 줄로 접는다 — 영문 캡션이 그 문단을 대신한다."""
    lines = text.split("\n")
    out: list[str] = []
    folding = False
    for ln in lines:
        m = FIG_CAP.match(ln)
        if m:
            folding = True
            out.append(translate_line(ln))
            continue
        if folding:
            if not ln.strip():
                folding = False
                out.append(ln)
            continue                      # 한국어 설명의 나머지 행은 버린다
        out.append(translate_line(ln))
    return "\n".join(out)


def block_from_korean(korean: list[str], head_re: re.Pattern[str], kind: str, n: int) -> list[str]:
    """캡션 행부터 그 표(또는 그림 설명)까지만 가져온다.

    빈 줄 둘을 경계로 삼던 첫 구현은 표 하나를 요청했는데 다음 절 전체를 끌고 왔다. 경계는
    **구조**로 잡는다 — 표는 `|` 로 시작하는 연속 행이고, 그림 설명은 `**그림 n.**` 으로
    시작하는 한 문단이다.
    """
    starts = [i for i, ln in enumerate(korean) if head_re.match(ln)]
    if len(starts) != 1:
        fail(f"{kind} {n} 앵커가 {len(starts)}건 — 한국어 파생본에서 정확히 한 번 걸려야 한다")
    i = starts[0]
    out = [korean[i]]
    j = i + 1
    while j < len(korean) and not korean[j].strip():      # 캡션과 본체 사이의 빈 줄 하나
        out.append(korean[j])
        j += 1
    if kind == "TABLE":
        while j < len(korean) and korean[j].lstrip().startswith("|"):
            out.append(korean[j])
            j += 1
        if not any(ln.lstrip().startswith("|") for ln in out):
            fail(f"TABLE {n} 캡션 뒤에 표가 없다 — 앵커를 확인할 것")
    else:
        cap = re.compile(rf"^\*\*그림 {n}\.\*\*")
        while j < len(korean) and not cap.match(korean[j]):
            if korean[j].strip():
                fail(f"FIGURE {n} 이미지 뒤에 설명 문단이 바로 오지 않는다")
            out.append(korean[j])
            j += 1
        while j < len(korean) and korean[j].strip():
            out.append(korean[j])
            j += 1
    while out and not out[-1].strip():
        out.pop()
    return out


def build() -> str:
    if not PROSE.exists():
        fail(f"영문 산문 소스 부재 — {PROSE}")
    if not KOREAN.exists():
        fail(f"복사 원본 부재 — {KOREAN} (먼저 `make submission-stage3`)")
    korean = KOREAN.read_text(encoding="utf-8").split("\n")
    out = PROSE.read_text(encoding="utf-8")

    copied = 0
    residue: list[str] = []

    def render(kind: str, n: int) -> str:
        nonlocal copied
        if kind == "TABLE":
            head = re.compile(rf"^\*\*표 {n}\.")
        else:
            head = re.compile(rf"^!\[그림 {n}\.")
        block = "\n".join(block_from_korean(korean, head, kind, n))
        moved = translate(block)
        before, after = measurements(block), measurements(moved)
        if before != after:
            fail(f"{kind} {n} 치환에서 수치가 달라졌다 — {before} → {after}")
        for ln_no, line in enumerate(moved.split("\n"), 1):
            if HANGUL.search(line):
                residue.append(f"{kind} {n} L{ln_no}: {line.strip()[:110]}")
        copied += 1
        return moved

    out = TABLE_RE.sub(lambda m: render("TABLE", int(m.group(1))), out)
    out = FIGURE_RE.sub(lambda m: render("FIGURE", int(m.group(1))), out)

    # 참고문헌은 이미 영문 APA 다 — 다시 타자하면 서지가 갈린다(D-38 의 실패 형태).
    if "{{BIB}}" in out:
        starts = [i for i, ln in enumerate(korean) if ln.strip() == "# 참고문헌"]
        if len(starts) != 1:
            fail(f"참고문헌 표제가 {len(starts)}건 — 하나여야 한다")
        bib = "\n".join(korean[starts[0] + 1:]).strip()
        n_refs = sum(1 for ln in bib.split("\n") if ln.strip() and not ln.startswith("#"))
        out = out.replace("{{BIB}}", bib)
        print(f"[en] 참고문헌 {n_refs}행 복사")

    if residue:
        print("[en] 치환되지 않은 한글 — TERMS 에 추가하거나 산문으로 옮길 것:", file=sys.stderr)
        for r in residue:
            print(f"      {r}", file=sys.stderr)
        fail(f"한글 잔존 {len(residue)}행")

    print(f"[en] 복사한 표·그림 {copied}개 · 원본 {KOREAN.relative_to(ROOT)}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="조립 결과가 디스크와 같은지만 확인")
    args = ap.parse_args()

    text = build()
    if args.check:
        if not TARGET.exists() or TARGET.read_text(encoding="utf-8") != text:
            fail(f"{TARGET.relative_to(ROOT)} 이 산문 소스와 어긋난다 — 다시 조립할 것")
        print("[en] 대조 통과")
        return 0
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(text, encoding="utf-8")
    print(f"[en] 생성: {TARGET.relative_to(ROOT)} ({len(text):,}자)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
