#!/usr/bin/env python3
"""scripts/check_crossrefs.py — 상호참조가 **실재하는 것을 가리키는가** (PLAN-086 D11·D12).

용법:  python scripts/check_crossrefs.py [--warn]
종료:  0 = 정합 · 1 = 위반

**왜 이 검사가 필요한가.** `submission_check` 의 D9 는 §참조의 **도달성**만 본다 — 가리키는 절이
존재하면 통과한다. 그래서 **존재하는 다른 절을 가리키는 것**은 잡히지 않았고, 표·그림 번호와
보충자료 → 본문 표 참조는 아무 검사도 보지 않았다. 실제로 넷이 살아남았다(PLAN-086 §1.4):
영문 그림 4 캡션이 §5.1(실재 §5.2) · S8 이 본문 표 10(실재 표 9) · 영문 S5 가 존재하지 않는
§13 · S6 이 이미 이관된 §5.3.2.

검사는 다섯이다.

  X1  EP ↔ 절 — `paper/episodes.yaml` 이 단일 원천이다. 산문이 "EP3 · §5.7" 이라 쓰면 실패한다.
  X2  표·그림 상호참조 — "표 N" · "그림 N" 이 그 문서에 실재하는 번호인가.
  X3  표·그림 번호의 연번 — 캡션이 1부터 빠짐없이 이어지는가(중복·결번 금지).
  X4  보충자료 → 본문 표·그림 번호 — 보충자료가 "본문 표 N" 이라 밝힌 참조만 본다.
  X5  국·영문 대조(D12) — 같은 문서 쌍의 §참조 집합·표/그림 번호 집합이 일치하는가.

**X5 가 D12 다.** 국문만 고치고 영문이 뒤처지는 것이 이 저장소에서 가장 자주 난 사고이며,
그림 4 캡션 오류가 그렇게 살아남았다.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "paper" / "episodes.yaml"

# 캡션 — 산문에서 표·그림을 **정의**하는 자리. 본문 캡션 규약은 `**표 N.**` · `**그림 N.**` 이고
# 영문은 `**Table N.**` · `**Figure N.**` 이다. 이미지 대체텍스트(`![그림 N. …]`)는 캡션의
# 사본이므로 정의로 세지 않는다 — 세면 전량이 중복 번호가 된다.
CAPTION = {
    "ko": (re.compile(r"^\*\*표\s*(\d+)\."), re.compile(r"^\*\*그림\s*(\d+)\.")),
    "en": (re.compile(r"^\*\*Table\s*(\d+)\."), re.compile(r"^\*\*Figure\s*(\d+)\.")),
}
# 영문 **산문 소스**는 캡션을 갖지 않는다 — `build_submission_en.py` 가 `{{TABLE:n}}` 자리에
# 국문 파생본의 표를 문자 단위로 복사해 넣기 때문이다(서지가 갈리지 않게 하는 설계).
# 그러므로 소스에서 표·그림의 **정의**는 이 지시자이며, 캡션 정규식으로는 하나도 보이지 않는다.
PLACEHOLDER = (re.compile(r"\{\{TABLE:(\d+)\}\}"), re.compile(r"\{\{FIGURE:(\d+)\}\}"))
# 참조 — 산문 어디에서든 표·그림을 **가리키는** 자리.
REF = {
    "ko": (re.compile(r"표\s*(\d+)"), re.compile(r"그림\s*(\d+)")),
    "en": (re.compile(r"\bTable\s*(\d+)"), re.compile(r"\bFigure\s*(\d+)")),
}
SECTION_HEAD = re.compile(r"^#{1,6}\s+(\d+(?:\.\d+)*)\s")
SECTION_REF = re.compile(r"§\s?(\d+(?:\.\d+)*)(?![.\d]*-)")
BIB_HEAD = re.compile(r"^#\s+(참고문헌|References)\s*$")

# 보충자료가 **본문을 명시적으로 가리키는** 표·그림 참조. D10 이 §참조에 한 일을 표·그림에 한다.
SUPP_BODY_TABLE = {
    "ko": re.compile(r"본문\s*(?:의\s*)?표\s*(\d+)"),
    "en": re.compile(r"\bTable\s*(\d+)\s+(?:in|of)\s+the\s+manuscript"),
}
SUPP_BODY_FIGURE = {
    "ko": re.compile(r"본문\s*(?:의\s*)?그림\s*(\d+)"),
    "en": re.compile(r"\bFigure\s*(\d+)\s+(?:in|of)\s+the\s+manuscript"),
}


def strip_fenced(lines: list[str]) -> list[str]:
    """코드 펜스 안은 산문이 아니다 — 예시의 절 번호를 참조로 세지 않는다."""
    out, fenced = [], False
    for line in lines:
        if line.lstrip().startswith("```"):
            fenced = not fenced
            out.append("")
            continue
        out.append("" if fenced else line)
    return out


def prose(path: Path) -> list[str]:
    """참고문헌 앞까지의 산문. 서지의 `§` 는 법령 조항이고 표 번호도 서지에는 없다."""
    lines = strip_fenced(path.read_text(encoding="utf-8", errors="replace").splitlines())
    for i, line in enumerate(lines):
        if BIB_HEAD.match(line):
            return lines[:i]
    return lines


def captions(lines: list[str], lang: str) -> tuple[list[int], list[int]]:
    """이 문서가 **정의**하는 표·그림 번호. 조립 지시자도 정의로 센다(위 PLACEHOLDER 주석)."""
    t_pat, f_pat = CAPTION[lang]
    tables = [int(m.group(1)) for line in lines if (m := t_pat.match(line))]
    figures = [int(m.group(1)) for line in lines if (m := f_pat.match(line))]
    if not tables and not figures:
        tp, fp = PLACEHOLDER
        body = "\n".join(lines)
        tables = [int(x) for x in tp.findall(body)]
        figures = [int(x) for x in fp.findall(body)]
    return tables, figures


def sections(lines: list[str]) -> set[str]:
    out = set()
    for line in lines:
        if m := SECTION_HEAD.match(line):
            out.add(m.group(1))
            # 상위 절도 존재로 센다 — §5.3.2 가 있으면 §5.3 과 §5 를 가리켜도 도달한다.
            parts = m.group(1).split(".")
            for k in range(1, len(parts)):
                out.add(".".join(parts[:k]))
    return out


def numbering_gaps(nums: list[int], kind: str, path: Path) -> list[str]:
    """연번 위반 — 중복과 결번. V6(§8.1)을 산문 캡션에 적용한다."""
    out = []
    seen = sorted(set(nums))
    dup = sorted({n for n in nums if nums.count(n) > 1})
    if dup:
        out.append(f"{path}: [X3] {kind} 번호 중복 — {dup}")
    if seen and seen != list(range(1, len(seen) + 1)):
        missing = [n for n in range(1, max(seen) + 1) if n not in seen]
        out.append(f"{path}: [X3] {kind} 번호 결번 — {missing} (실재 {seen})")
    return out


def check_document(path: Path, lang: str, eps: dict) -> list[str]:
    """X1·X2·X3 — 한 문서 안에서 닫히는 검사."""
    fails: list[str] = []
    lines = prose(path)
    tables, figures = captions(lines, lang)
    fails += numbering_gaps(tables, "표" if lang == "ko" else "Table", path)
    fails += numbering_gaps(figures, "그림" if lang == "ko" else "Figure", path)

    t_set, f_set = set(tables), set(figures)
    t_ref, f_ref = REF[lang]
    for i, line in enumerate(lines, 1):
        # X2 · 실재하지 않는 표·그림을 가리키지 않는가.
        for n in {int(x) for x in t_ref.findall(line)} - t_set:
            fails.append(f"{path}:{i}: [X2] 없는 표 참조 — {n} (실재 {sorted(t_set)})")
        for n in {int(x) for x in f_ref.findall(line)} - f_set:
            fails.append(f"{path}:{i}: [X2] 없는 그림 참조 — {n} (실재 {sorted(f_set)})")

    # X1 · EP ↔ 절. 같은 행에서 EP 와 §절이 함께 나오면 그 대응이 단일 원천과 같아야 한다.
    # **같은 행에 EP 가 둘 이상이면 검사하지 않는다** — "EP3 · EP4 · EP5 (§6)" 처럼 묶어
    # 가리키는 자리가 정당하게 있고, 그 자리에서 대응을 요구하면 거짓 위반이 된다.
    for i, line in enumerate(lines, 1):
        found = sorted(set(re.findall(r"\bEP(\d)\b", line)))
        if len(found) != 1:
            continue
        ep = f"EP{found[0]}"
        want = eps.get(ep, {}).get("section")
        if not want:
            continue
        # 절 참조 가운데 §5.x 만 본다 — 결과 장의 대응이 이 검사의 대상이다.
        refs = [r for r in SECTION_REF.findall(line) if r.startswith("5.")]
        wrong = [r for r in refs if r != want and not r.startswith(want + ".")]
        if wrong:
            fails.append(
                f"{path}:{i}: [X1] {ep} 의 절은 §{want} 인데 §{'·§'.join(wrong)} 을 함께 가리킨다"
            )
    return fails


SUPP_POINTER = re.compile(r"\[(S\d+)\]\(")


def check_pair(ko: Path, en: Path, *, count_pointers: bool) -> list[str]:
    """X5(D12) — 같은 문서 쌍의 §참조·표·그림 번호·보충자료 포인터가 일치하는가."""
    fails: list[str] = []
    kl, el = prose(ko), prose(en)
    # 보충자료 포인터의 대칭 — 한쪽 언어의 독자만 근거에 도달하는 상태를 막는다.
    # **산문 소스끼리는 세지 않는다** — 표 안의 포인터는 영문 소스에 `{{TABLE:n}}` 로만 있고
    # 조립 때 국문 파생본에서 복사되므로, 소스 단계의 개수 차이는 설계이지 결함이 아니다.
    if count_pointers:
        ka = [m.group(1) for line in kl for m in SUPP_POINTER.finditer(line)]
        ea = [m.group(1) for line in el for m in SUPP_POINTER.finditer(line)]
        from collections import Counter
        a, b = Counter(ka), Counter(ea)
        if a != b:
            fails.append(
                f"{en}: [X5] 국·영문 보충자료 포인터 수 불일치\n"
                f"    국문에만: {sorted((a - b).elements())}\n"
                f"    영문에만: {sorted((b - a).elements())}"
            )
    for kind, get in (
        ("§참조", lambda ls, lang: {r for line in ls for r in SECTION_REF.findall(line)}),
        ("표 번호", lambda ls, lang: set(captions(ls, lang)[0])),
        ("그림 번호", lambda ls, lang: set(captions(ls, lang)[1])),
    ):
        a, b = get(kl, "ko"), get(el, "en")
        if a == b:
            continue
        fails.append(
            f"{en}: [X5] 국·영문 {kind} 불일치\n"
            f"    국문에만: {sorted(a - b)}\n"
            f"    영문에만: {sorted(b - a)}"
        )
    return fails


def check_supplementary(supp_dir: Path, lang: str, tables: set[int], figures: set[int]) -> list[str]:
    """X4 — 보충자료가 "본문 표 N" 이라 밝힌 참조가 본문에 실재하는가."""
    fails: list[str] = []
    for path in sorted(supp_dir.glob("*.md")):
        for i, line in enumerate(prose(path), 1):
            for n in {int(x) for x in SUPP_BODY_TABLE[lang].findall(line)} - tables:
                fails.append(f"{path}:{i}: [X4] 본문에 없는 표를 본문으로 가리킨다 — 표 {n}")
            for n in {int(x) for x in SUPP_BODY_FIGURE[lang].findall(line)} - figures:
                fails.append(f"{path}:{i}: [X4] 본문에 없는 그림을 본문으로 가리킨다 — 그림 {n}")
    return fails


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--warn", action="store_true", help="위반을 출력하되 종료코드 0")
    args = ap.parse_args()

    cfg = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    eps = cfg["episodes"]
    targets = cfg["meta"]["targets"]

    fails: list[str] = []
    checked = 0
    ko_paths = [ROOT / p for p in targets["ko"]]
    en_paths = [ROOT / p for p in targets["en"]]

    for lang, paths in (("ko", ko_paths), ("en", en_paths)):
        for p in paths:
            if not p.exists():
                print(f"[없음] {p.relative_to(ROOT)} — 조립 동결 중이면 정상이다")
                continue
            checked += 1
            fails += check_document(p, lang, eps)

    # X5 · 국·영문 대조는 **산문 소스끼리, 파생본끼리** 짝짓는다.
    for k, (ko, en) in enumerate(zip(ko_paths, en_paths)):
        if ko.exists() and en.exists():
            # 첫 쌍은 산문 소스, 둘째 쌍은 조립된 파생본이다(episodes.yaml 의 순서).
            fails += check_pair(ko, en, count_pointers=(k > 0))

    # X4 · 보충자료 → 본문. 기준 본문은 산문 소스다(파생본이 동결되어도 검사가 산다).
    for lang, body_rel, dir_key in (
        ("ko", targets["ko"][0], "ko"),
        ("en", targets["en"][0], "en"),
    ):
        body = ROOT / body_rel
        supp = ROOT / cfg["meta"]["supplementary"][dir_key]
        if not (body.exists() and supp.exists()):
            continue
        t, f = captions(prose(body), lang)
        fails += check_supplementary(supp, lang, set(t), set(f))

    for line in fails:
        print(("[warn] " if args.warn else "[실패] ") + line, file=sys.stderr)
    if fails:
        print(f"\n{'경고' if args.warn else '실패'}: 상호참조 위반 {len(fails)}건 (PLAN-086 D11·D12)")
        return 0 if args.warn else 1
    print(f"통과: {checked}개 문서 · 상호참조 (X1 EP↔절 · X2 표/그림 · X3 연번 · X4 보충자료→본문 · X5 국·영문 대조)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
