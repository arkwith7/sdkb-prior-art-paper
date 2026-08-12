#!/usr/bin/env python3
"""scripts/build_submission_stage3.py — 3단계(재조준·축약) 파생본을 **기계로** 조립한다.

용법:  python scripts/build_submission_stage3.py [--check]
종료:  0 = 성공(또는 --check 정합) · 1 = 불일치 · 2 = 앵커 소실·중복

왜 스크립트인가 (PLAN-048 3단계 · CLAUDE.md §1-1·§2.3)
- 3단계는 **문장을 새로 쓰는 단계**다. 그러나 **표의 수치는 새로 쓰는 대상이 아니다** —
  손으로 옮겨 적으면 오탈자가 곧 조작이 된다(§1-1 "수치는 실행된 코드의 출력"). 그래서
  산문은 사람이 쓰고(`paper/manuscript/stage3_source.md`), **표는 축약 전 전문에서 문자
  단위로 복사**한다. 이 파일이 그 경계를 강제한다.
- 복사 원본은 **축약 전 파생본 전문**(`paper/supplementary/S5-submission-full-v2.md`)이다.
  S5 는 2단계 산출물의 동결 사본이므로 3단계 편집이 원본을 움직이지 못한다.
- 앵커가 없거나 둘 이상이면 **조용히 넘어가지 않고 실패**한다(rc 2). 표가 소리 없이
  빠지거나 엉뚱한 표가 실리는 사고를 구조적으로 막기 위해서다.

산문 소스에 쓰는 지시자는 둘뿐이다.
    {{COPY:<앵커 문자열>|table}}     앵커 행 다음에 오는 마크다운 표 블록을 그대로 넣는다
    {{BIB}}                          참고문헌 목록을 그대로 넣되, 아래 BIB_FIXES 만 교체한다

**서지 확정도 손이 아니라 목록으로 한다.** 3단계는 플레이스홀더 6건을 없애는 단계인데(D2),
목록 전체를 다시 타자하면 어느 줄이 왜 바뀌었는지 보이지 않는다. 그래서 **바뀐 줄만** 아래
BIB_FIXES 에 적고, 각 항목이 원문에서 정확히 한 번 매치되지 않으면 실패한다(rc 2).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PROSE = Path("paper/manuscript/stage3_source.md")
FROZEN = Path("paper/supplementary/S5-submission-full-v2.md")
TARGET = Path("paper/submission/manuscript.md")

DIRECTIVE = re.compile(r"\{\{COPY:(?P<anchor>[^|}]+)\|(?P<mode>table)\}\}")

BIB_START = "# 참고문헌"
BIB_END = "[미확정 서지"          # 이 행부터는 싣지 않는다 — 미확정 목록의 두 항목은 본문 미인용이다.

# (원문에서 찾을 조각, 그 행을 대신할 내용) · 내용이 None 이면 그 행을 지운다.
# 근거는 전부 2026-08-12 원문·출판사 페이지 대조다(PLAN-048 3단계 서지 확정).
BIB_FIXES: list[tuple[str, str | None]] = [
    (
        "Brank, J., Grobelnik, M., & Mladenić, D. (2005).",
        "Brank, J., Grobelnik, M., & Mladenić, D. (2005). A survey of ontology evaluation techniques. "
        "In *Proceedings of the Conference on Data Mining and Data Warehouses (SiKDD 2005)* (pp. 166–170). "
        "Ljubljana, Slovenia. https://aile3.ijs.si/dunja/SiKDD2005/Papers/BrankEvaluationSiKDD2005.pdf",
    ),
    (
        "Daniell, S., Buzhinsky, I., & Björkqvist, S. (2025).",
        "Daniell, K., Buzhinsky, I., & Björkqvist, S. (2025). Efficient patent searching using graph "
        "transformers. In *Proceedings of the PatentSemTech Workshop at SIGIR 2025*. "
        "https://doi.org/10.48550/arXiv.2508.10496",
    ),
    (
        "Faruqui, M., Tsvetkov, Y., Rastogi, P., & Dyer, C. (2016).",
        "Faruqui, M., Tsvetkov, Y., Rastogi, P., & Dyer, C. (2016). Problems with evaluation of word "
        "embeddings using word similarity tasks. In *Proceedings of the 1st Workshop on Evaluating "
        "Vector-Space Representations for NLP (RepEval)* (pp. 30–35). https://aclanthology.org/W16-2506/",
    ),
    (
        "Kontokostas, D., Westphal, P.,",
        "Keet, C. M., & Ławrynowicz, A. (2016). Test-driven development of ontologies. In *The Semantic "
        "Web: Latest Advances and New Domains (ESWC 2016)* (LNCS Vol. 9678, pp. 642–657). Springer. "
        "https://doi.org/10.1007/978-3-319-34129-3_39\n\n"
        "Kontokostas, D., Westphal, P., Auer, S., Hellmann, S., Lehmann, J., Cornelissen, R., & Zaveri, A. "
        "(2014). Test-driven evaluation of linked data quality. In *Proceedings of the 23rd International "
        "Conference on World Wide Web* (pp. 747–758). https://doi.org/10.1145/2566486.2568002",
    ),
    (
        "Pauwels, P., van den Bersselaar, R., & Verhelst, J. (2024).",
        "Pauwels, P., Van Den Bersselaar, E., & Verhelst, L. (2024). Validation of technical requirements "
        "for a BIM model using semantic web technologies. *Advanced Engineering Informatics, 60*, 102426. "
        "https://doi.org/10.1016/j.aei.2024.102426",
    ),
    (
        "Porzel, R., & Malaka, R. (2004).",
        "Porzel, R., & Malaka, R. (2004). A task-based approach for ontology evaluation. In *Proceedings "
        "of the ECAI-2004 Workshop on Ontology Learning and Population*. Valencia, Spain.",
    ),
    # TDD 계열의 대표 서지는 데이터셋 논문이 아니라 방법 논문이다 — 위에서 Keet & Ławrynowicz 로
    # 갈음했으므로 이 항목은 뺀다(본문 인용도 함께 바뀌었다).
    ("Potoniec, J., Wiśniewski, D.,", None),
    (
        "Solihin, W., Eastman, C., & Lee, Y.-C. (2015).",
        "Solihin, W., Eastman, C., & Lee, Y.-C. (2015). Toward robust and quantifiable automated IFC "
        "quality validation. *Advanced Engineering Informatics, 29*(3), 739–756. "
        "https://doi.org/10.1016/j.aei.2015.07.006",
    ),
]

# 3단계에서 새로 인용한 문헌(설계과학연구 프레임 · §3). 알파벳 순서 자리에 끼워 넣는다.
BIB_INSERTS: list[tuple[str, str]] = [
    (
        "Grüninger, M., & Fox, M. S. (1995).",
        "Gregor, S., & Hevner, A. R. (2013). Positioning and presenting design science research for "
        "maximum impact. *MIS Quarterly, 37*(2), 337–355. https://doi.org/10.25300/MISQ/2013/37.2.01",
    ),
    (
        "Hogan, A., Blomqvist, E.,",
        "Hevner, A. R., March, S. T., Park, J., & Ram, S. (2004). Design science in information systems "
        "research. *MIS Quarterly, 28*(1), 75–105. https://doi.org/10.2307/25148625",
    ),
    (
        "W3C. (2017).",
        "Venable, J., Pries-Heje, J., & Baskerville, R. (2016). FEDS: A framework for evaluation in design "
        "science research. *European Journal of Information Systems, 25*(1), 77–89. "
        "https://doi.org/10.1057/ejis.2014.36",
    ),
]


def fail(msg: str) -> None:
    print(f"실패: {msg}", file=sys.stderr)
    raise SystemExit(2)


def extract_table(lines: list[str], anchor: str) -> str:
    hits = [i for i, line in enumerate(lines) if anchor in line]
    if not hits:
        fail(f"앵커 소실 — {anchor!r}")
    if len(hits) > 1:
        fail(f"앵커 중복 {len(hits)}건 — {anchor!r} (더 긴 앵커로 특정할 것)")
    i = hits[0]
    # 앵커 행 이후 첫 표 행까지 내려간 뒤, 표가 끝나는 곳까지 담는다.
    j = i
    while j < len(lines) and not lines[j].lstrip().startswith("|"):
        j += 1
        if j - i > 6:
            fail(f"앵커 뒤 6행 안에 표가 없다 — {anchor!r}")
    k = j
    while k < len(lines) and lines[k].lstrip().startswith("|"):
        k += 1
    if k - j < 3:
        fail(f"표가 너무 짧다({k - j}행) — {anchor!r}")
    return "\n".join(lines[j:k])


def extract_bib(lines: list[str]) -> str:
    starts = [i for i, line in enumerate(lines) if line.strip() == BIB_START]
    if len(starts) != 1:
        fail(f"참고문헌 표제가 {len(starts)}건 — 하나여야 한다")
    i = starts[0] + 1
    ends = [k for k in range(i, len(lines)) if BIB_END in lines[k]]
    if not ends:
        fail(f"참고문헌 종료 표지 소실 — {BIB_END!r}")
    body = lines[i:ends[0]]

    def apply(spec: list[tuple[str, str | None]], insert: bool) -> None:
        for probe, text in spec:
            hits = [k for k, line in enumerate(body) if probe in line]
            if len(hits) != 1:
                fail(f"서지 교체 앵커가 {len(hits)}건 — {probe!r}")
            k = hits[0]
            if text is None:
                del body[k]
                while k < len(body) and body[k].strip() == "":
                    del body[k]
                    break
            elif insert:
                body.insert(k, "")
                body.insert(k, text)
            else:
                body[k] = text

    apply(BIB_FIXES, insert=False)
    apply(BIB_INSERTS, insert=True)
    print(f"서지: 교체 {len(BIB_FIXES)}건 · 신규 {len(BIB_INSERTS)}건 · 플레이스홀더 목록 제외")
    return "\n".join(body).strip() + "\n"


def build() -> str:
    if not PROSE.exists():
        fail(f"산문 소스 부재 — {PROSE}")
    if not FROZEN.exists():
        fail(f"복사 원본 부재 — {FROZEN}")
    frozen = FROZEN.read_text(encoding="utf-8").split("\n")
    prose = PROSE.read_text(encoding="utf-8")

    used: list[str] = []

    def sub(match: re.Match[str]) -> str:
        anchor = match.group("anchor").strip()
        used.append(anchor)
        return extract_table(frozen, anchor)

    out = DIRECTIVE.sub(sub, prose)
    if "{{BIB}}" not in out:
        fail("{{BIB}} 지시자가 없다 — 참고문헌이 빠진 원고는 만들지 않는다")
    out = out.replace("{{BIB}}", extract_bib(frozen))
    if "{{COPY" in out:
        fail("해석되지 않은 지시자가 남았다 — 문법은 {{COPY:앵커|table}} 이다")
    print(f"복사한 표 {len(used)}개 · 원본 {FROZEN}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="다시 조립해 현재 파생본과 대조만 한다")
    args = ap.parse_args()

    built = build()
    if args.check:
        current = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
        if current != built:
            print("불일치: 파생본이 산문 소스 + 동결 표와 다르다 (재생성 필요)", file=sys.stderr)
            return 1
        print("정합: 파생본 = 산문 소스 + 동결 표")
        return 0
    TARGET.write_text(built, encoding="utf-8")
    print(f"생성: {TARGET} ({len(built):,}자)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
