#!/usr/bin/env python3
"""scripts/check_glossary.py — 용어 첫 등장 규율의 기계 검사 (paper/glossary-terms.yaml · STYLE V1·V2).

용법:  python scripts/check_glossary.py [--root .] [--warn] [--inventory] [--strict-g4]
종료:  0 = 통과(또는 --warn) · 1 = 위반 · 2 = 대상·정본 부재

무엇을 보는가 — `paper/glossary-terms.yaml` 의 용어마다 다섯 규칙을 본다.
  G1  정의 선행   — 본문(§1 이후) 첫 등장이 정의형(`한글(영문)`)이거나 정의 뒤에 온다
  G2  약어 선행   — 약어가 정의형보다 먼저 단독 등장하지 않는다
  G3  정의 위치   — 정의가 `define_in` 절에 있다 (경고)
  G4  식별자 산문 — identifier 부류는 표·캡션·수식·코드 밖 산문에 나오지 않는다 (경고 · --strict-g4 로 차단)
  G5  동의어·다의어 — `synonyms_forbidden`(V2) · `forbid_patterns`(한 낱말 두 뜻)

**V1·V2 의 나머지(정의문의 품질·예시 유무·한 절 새 용어 ≤3)는 사람이 지킨다.** 검사기 통과는
규격 준수의 필요조건이지 충분조건이 아니다. `style_check.py` 가 어체의 표류를, `check_verdicts.py`
가 판정 강도의 표류를 막듯, 이 파일은 **정보 제시 순서의 표류**만 막는다 — 절을 옮기거나
S5 로 이관할 때 정의가 사용 뒤로 밀리는 일이 재구성마다 재발하기 때문이다(PLAN-066 §1).

설계 메모
- **대상은 투고 파생본 계열뿐이다**(산문 소스 + 조립 산출물). 작업 정본·supplementary 는 감사
  기록이므로 제외한다(`style_check.py` 와 같은 이유). 영문 산출물(`paper/submission/en/`)도
  제외한다 — 영문 첫 등장 규율은 D-1 용어집 동결 이후 `--lang en` 으로 따로 붙인다.
- **초록·약어표는 기점에서 제외한다.** 둘 다 자기완결 단위라 본문보다 먼저 읽히며, 약어표는
  색인이지 정의가 아니다 — 약어표에 있다고 본문 첫 등장의 정의를 생략하면 독자는 표로
  되돌아가야 한다. 기점은 `meta.body_start`(기본 `# 1. `)다.
- **언급(mention)은 사용(use)이 아니다.** 백틱·따옴표 안은 마스킹한다. 수식(`\\(…\\)` · `$…$`)도
  마스킹한다 — 기호 `ε`·`δ` 와 식별자는 수식 안에서 정상이다.
- **표·캡션에 먼저 나오는 것은 G1 위반이다**(STYLE V2 역방향: "그 낱말이 표·제목에 먼저 등장하면
  독자는 정의를 만나기 전에 뜻을 추측하게 된다"). 다만 G4(식별자)는 표·캡션을 허용한다 —
  라벨은 표에만 두는 것이 규칙이므로.
- 정의형의 기본 꼴은 `meta.definition_form` 이고 용어마다 `definition_pattern` 으로 덮어쓴다.
  `aliases_ko` 는 첫 등장 판단에 ko 와 같이 센다(영문 그대로 쓴 `Oracle-free` 같은 잠정 표기).
- `<!-- glossary-ok: 사유 -->` 로 그 행을 면제한다. 사유 없는 면제는 두지 않는다.
- **--inventory** 는 위반이 아니라 **대장**을 찍는다 — 용어별 첫 사용 위치·정의 위치·상태.
  PLAN-066 의 실측표와 glossary.md §J 는 이 출력에서 옮긴다(손으로 세지 않는다).
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("PyYAML 이 필요하다: uv sync", file=sys.stderr)
    raise

EXEMPT_RE = re.compile(r"<!--\s*glossary-ok:\s*\S.*?-->")
SECTION_RE = re.compile(r"^#{1,4}\s+(\d+(?:\.\d+)*)\b")
CAPTION_RE = re.compile(r"^\s*(\*\*)?(표|그림)\s*\d+\.|^\s*!\[")
TABLE_RE = re.compile(r"^\s*\|")


@dataclass
class Term:
    id: str
    category: str
    ko: str
    en: str
    aliases_ko: list[str] = field(default_factory=list)
    abbr: str | None = None
    abbr_pattern: str | None = None
    define_in: str | None = None
    definition_pattern: str | None = None
    synonyms_forbidden: list[str] = field(default_factory=list)
    forbid_patterns: list[dict] = field(default_factory=list)
    gloss: str | None = None

    @classmethod
    def from_dict(cls, d: dict) -> "Term":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in known})


@dataclass
class Hit:
    line: int      # 1-based
    section: str
    kind: str      # "def" | "use" | "abbr"
    context: str   # "prose" | "table" | "caption" | "heading"


# ───────────────────────── 마스킹 ─────────────────────────
def mask(text: str) -> str:
    """백틱·따옴표·수식 안을 같은 길이의 공백으로 바꾼다(위치 보존)."""

    def blank(m: re.Match[str]) -> str:
        return re.sub(r"[^\n]", " ", m.group(0))  # 줄바꿈은 남긴다 — 행 번호 보존

    text = re.sub(r"```.*?```", blank, text, flags=re.S)
    text = re.sub(r"`[^`\n]*`", blank, text)
    text = re.sub(r"\\\((.*?)\\\)", blank, text, flags=re.S)
    text = re.sub(r"\$\$.*?\$\$", blank, text, flags=re.S)
    text = re.sub(r"(?<!\$)\$[^$\n]+\$", blank, text)
    text = re.sub(r"[“\"][^”\"\n]{1,80}[”\"]", blank, text)
    text = re.sub(r"<!--.*?-->", blank, text, flags=re.S)
    return text


def line_context(raw: str) -> str:
    if TABLE_RE.match(raw):
        return "table"
    if CAPTION_RE.match(raw):
        return "caption"
    if raw.lstrip().startswith("#"):
        return "heading"
    return "prose"


# ───────────────────────── 본문 범위·절 ─────────────────────────
def body_lines(lines: list[str], start_re: str, end_re: str) -> tuple[int, int]:
    s_re, e_re = re.compile(start_re), re.compile(end_re)
    start = next((i for i, ln in enumerate(lines) if s_re.match(ln)), 0)
    end = next((i for i, ln in enumerate(lines) if i > start and e_re.match(ln)), len(lines))
    return start, end


def section_map(lines: list[str]) -> list[str]:
    cur, out = "(front)", []
    for ln in lines:
        m = SECTION_RE.match(ln)
        if m:
            cur = "§" + m.group(1)
        out.append(cur)
    return out


def in_section(sec: str, wanted: str | None) -> bool:
    if not wanted:
        return True
    w = wanted if wanted.startswith("§") else "§" + wanted
    return sec == w or sec.startswith(w + ".")


# ───────────────────────── 용어별 스캔 ─────────────────────────
def compile_term(t: Term, default_form: str) -> dict[str, re.Pattern[str]]:
    ko_alts = [re.escape(t.ko)] + [re.escape(a) for a in t.aliases_ko]
    pats: dict[str, re.Pattern[str]] = {"use": re.compile("|".join(ko_alts))}
    if t.definition_pattern:
        pats["def"] = re.compile(t.definition_pattern)
    else:
        form = default_form.replace("{ko}", "(?:" + "|".join(ko_alts) + ")").replace(
            "{en}", re.escape(t.en)
        )
        pats["def"] = re.compile(form, re.I)
    if t.abbr_pattern:
        pats["abbr"] = re.compile(t.abbr_pattern)
    elif t.abbr:
        pats["abbr"] = re.compile(r"(?<![A-Za-z0-9])" + re.escape(t.abbr) + r"(?![A-Za-z0-9])")
    return pats


def scan_term(t: Term, pats: dict[str, re.Pattern[str]], lines: list[str], masked: list[str],
              secs: list[str], start: int, end: int) -> list[Hit]:
    hits: list[Hit] = []
    for i in range(start, end):
        raw, m = lines[i], masked[i]
        if EXEMPT_RE.search(raw):
            continue
        ctx = line_context(raw)
        if pats["def"].search(m):
            hits.append(Hit(i + 1, secs[i], "def", ctx))
            continue  # 정의행은 사용으로 다시 세지 않는다
        if pats["use"].search(m):
            hits.append(Hit(i + 1, secs[i], "use", ctx))
        if "abbr" in pats and pats["abbr"].search(m):
            hits.append(Hit(i + 1, secs[i], "abbr", ctx))
    return hits


def judge(t: Term, hits: list[Hit], path: str, strict_g4: bool) -> tuple[list[str], list[str], dict]:
    """위반·경고·대장 행을 돌려준다."""
    fails: list[str] = []
    warns: list[str] = []
    defs = [h for h in hits if h.kind == "def"]
    uses = [h for h in hits if h.kind == "use"]
    abbrs = [h for h in hits if h.kind == "abbr"]
    first_def = defs[0] if defs else None
    first_any = min(hits, key=lambda h: h.line) if hits else None

    status = "미사용"
    if hits:
        if first_def is None:
            status = "정의 없음"
            target = first_any
            if t.category != "identifier":
                fails.append(
                    f"{path}:{target.line}: [G1] ‘{t.ko}’ 정의 없음 — 첫 등장 {target.section}"
                    f"({target.context}) · 첫 등장을 `{t.ko}({t.en}{', ' + t.abbr if t.abbr else ''})` 정의형으로"
                )
        elif first_any.line < first_def.line:
            status = "정의가 뒤에"
            label = "G2" if first_any.kind == "abbr" else "G1"
            what = f"약어 ‘{t.abbr or t.abbr_pattern}’" if label == "G2" else f"‘{t.ko}’"
            fails.append(
                f"{path}:{first_any.line}: [{label}] {what} 가 정의({first_def.section} L{first_def.line})"
                f"보다 먼저 등장 — {first_any.section}({first_any.context})"
            )
        else:
            status = "적합"
        if first_def and not in_section(first_def.section, t.define_in):
            warns.append(
                f"{path}:{first_def.line}: [G3] ‘{t.ko}’ 정의가 {first_def.section} 에 있다 — "
                f"계획 위치 {t.define_in}"
            )

    # G4 — 식별자 산문
    if t.category == "identifier":
        prose_abbr = [h for h in abbrs if h.context == "prose"]
        if prose_abbr:
            h = prose_abbr[0]
            msg = (f"{path}:{h.line}: [G4] 식별자 ‘{t.abbr or t.abbr_pattern}’ 산문 사용 {len(prose_abbr)}회 "
                   f"(첫 {h.section}) — 산문은 ‘{t.ko}’ 로, 라벨은 표·캡션에만")
            (fails if strict_g4 else warns).append(msg)

    row = {
        "id": t.id, "cat": t.category, "ko": t.ko,
        "first": f"{first_any.section} L{first_any.line} ({first_any.kind}/{first_any.context})" if first_any else "—",
        "def": f"{first_def.section} L{first_def.line}" if first_def else "—",
        "n_use": len(uses), "n_abbr": len(abbrs), "status": status,
    }
    return fails, warns, row


def scan_forbidden(t: Term, lines: list[str], masked: list[str], secs: list[str],
                   start: int, end: int, path: str) -> list[str]:
    fails: list[str] = []
    pats = [(re.compile(re.escape(s)), f"동의어 ‘{s}’ → ‘{t.ko}’ (V2)") for s in t.synonyms_forbidden]
    pats += [(re.compile(fp["pattern"]), fp.get("message", "금지 패턴")) for fp in t.forbid_patterns]
    for i in range(start, end):
        if EXEMPT_RE.search(lines[i]):
            continue
        for p, msg in pats:
            if p.search(masked[i]):
                fails.append(f"{path}:{i + 1}: [G5] {msg} — {secs[i]}")
    return fails


# ───────────────────────── 파일 단위 ─────────────────────────
def check_file(path: Path, spec: dict, strict_g4: bool = False) -> tuple[list[str], list[str], list[dict]]:
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    masked = mask(text).split("\n")
    assert len(masked) == len(lines)
    secs = section_map(lines)
    meta = spec.get("meta", {})
    start, end = body_lines(lines, meta.get("body_start", r"^# 1\. "), meta.get("body_end", r"^# 참고문헌"))
    form = meta.get("definition_form", r"{ko}\**\s*\(\s*{en}")
    rel = str(path)
    fails, warns, rows = [], [], []
    for d in spec["terms"]:
        t = Term.from_dict(d)
        pats = compile_term(t, form)
        hits = scan_term(t, pats, lines, masked, secs, start, end)
        f, w, row = judge(t, hits, rel, strict_g4)
        fails += f
        warns += w
        rows.append(row)
        fails += scan_forbidden(t, lines, masked, secs, start, end, rel)
    return fails, warns, rows


def print_inventory(path: Path, rows: list[dict]) -> None:
    print(f"\n## 용어 대장 — {path}")
    print("| id | 부류 | 용어 | 첫 등장 | 정의 | 사용 | 약어 | 상태 |")
    print("|---|---|---|---|---|---:|---:|---|")
    for r in rows:
        print(f"| {r['id']} | {r['cat']} | {r['ko']} | {r['first']} | {r['def']} | {r['n_use']} | {r['n_abbr']} | {r['status']} |")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--spec", default="paper/glossary-terms.yaml")
    ap.add_argument("--warn", action="store_true", help="위반을 출력하되 종료코드 0")
    ap.add_argument("--strict-g4", action="store_true", help="G4(식별자 산문)를 경고가 아니라 차단으로")
    ap.add_argument("--inventory", action="store_true", help="용어별 첫 등장·정의 위치 대장을 출력")
    ap.add_argument("paths", nargs="*", help="대상 파일(생략 시 spec.meta.targets)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    spec_path = root / args.spec
    if not spec_path.exists():
        print(f"정본 부재: {spec_path}")
        return 2
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))

    targets = [Path(p) for p in args.paths] if args.paths else [root / p for p in spec["meta"]["targets"]]
    targets = [t for t in targets if t.exists()]
    if not targets:
        print("대상 부재: " + " · ".join(spec["meta"]["targets"]))
        return 2

    all_fails: list[str] = []
    all_warns: list[str] = []
    for f in targets:
        fails, warns, rows = check_file(f, spec, args.strict_g4)
        all_fails += fails
        all_warns += warns
        if args.inventory:
            print_inventory(f.relative_to(root) if f.is_relative_to(root) else f, rows)

    for ln in all_warns:
        print("[warn] " + ln)
    for ln in all_fails:
        print(ln)
    n_terms = len(spec["terms"])
    if all_fails:
        print(f"\n{'경고' if args.warn else '실패'}: 용어 첫 등장 규율 위반 {len(all_fails)}건 · 경고 {len(all_warns)}건 "
              f"(paper/glossary-terms.yaml · {n_terms}항)")
        return 0 if args.warn else 1
    print(f"통과: {len(targets)}개 파일 · 용어 {n_terms}항 (G1·G2·G5{' ·G4' if args.strict_g4 else ''}) · 경고 {len(all_warns)}건")
    return 0


if __name__ == "__main__":
    sys.exit(main())
