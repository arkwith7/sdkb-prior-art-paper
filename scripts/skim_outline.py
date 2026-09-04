#!/usr/bin/env python3
"""skim_outline.py — '제목과 그림만 읽는 독자'가 보는 원고를 뽑아낸다 (스킴 경로 · skim path).

원고에서 장·절 제목, 그림 캡션(첫 문장), 표 캡션(첫 문장), 예시 박스 첫 문장만 추출하여
paper/SKIM.md 로 쓰고, 절마다 시각 장치(그림·예시 박스)가 하나 이상 있는지 검사한다.
목표: 이 파일만 읽어도 논문의 주장과 발견이 파악되어야 한다(PLAN-087 §2c).

    uv run python scripts/skim_outline.py paper/submission/manuscript.md            # 표준출력
    uv run python scripts/skim_outline.py paper/submission/manuscript.md -o paper/SKIM.md
    uv run python scripts/skim_outline.py ... --check   # §3–§5 의 절(## · ###)에 그림/예시가 없으면 종료코드 1

검사 규칙 K1–K4
  K1  §3–§5 의 모든 ## 절에는 그림·예시 박스·번호가 있는 그림의 명시적 재참조가 하나 이상 있어야 한다.
  K2  그림 캡션의 첫 문장은 '무엇을 그렸다'가 아니라 '무엇이 보인다'(주장)여야 한다 — 기계는 길이만 본다:
      첫 문장이 12자 미만이면 경고(예: "연구 개요도.").
  K3  절 제목이 에피소드 식별자로 시작하면(예: "EP3 · 통제된 자원 교체") 경고 — 제목이 주장을 담아야 한다.
  K4  **그림만 읽는 경로**(PLAN-089 · 그림 규격 F8). `paper/figures-claims.yaml` 의 선언과 원고를
      대조한다: 기여 셋이 각각 하나 이상의 도판을 갖는가 · 선언한 번호의 그림이 원고에 있는가 ·
      그 번호가 가리키는 파일이 선언과 같은가. **경고 모드다** — 담당 배정은 편집 판단이므로
      기계가 차단하지 않고 결손만 알린다.

    uv run python scripts/skim_outline.py paper/submission/manuscript.md --figures-only
        캡션 첫 문장만 순서대로 낸다. 이 목록만 읽어 논지가 서는지는 사람이 판정한다.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

H_RE = re.compile(r"^(#{1,3})\s+(.*)$")
FIG_RE = re.compile(r"^\*\*그림\s*(\d+)\.\*\*\s*(.*)$")
TAB_RE = re.compile(r"^\*\*표\s*(\d+)\.\s*(.*?)\*\*")
EX_RE = re.compile(r"^>\s*\*\*예시\s*(\d+)\s*[·.]\s*([^*]*)\*\*\s*(.*)$")
FIG_REF_RE = re.compile(r"그림\s*(\d+)(?:[·,과와의을를에은는도에서]|\s|$)")
IMG_RE = re.compile(r"^!\[그림\s*(\d+)\.[^\]]*\]\(([^)]+)\)")
CLAIMS_YAML = Path(__file__).resolve().parent.parent / "paper" / "figures-claims.yaml"


def first_sentence(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    m = re.search(r"[.。]\s", s + " ")
    return s[: m.end()].strip() if m else s


def _join_captions(lines: list[str]) -> list[str]:
    """캡션 한 덩어리를 한 줄로 합친다.

    캡션은 산문처럼 여러 줄에 걸쳐 쓰이므로 첫 줄만 읽으면 **첫 문장이 문장 중간에서
    잘린다** — 실측으로 그림 1·8 의 캡션이 그렇게 잘려 K2 를 통과하고 있었다.
    """
    out: list[str] = []
    i = 0
    while i < len(lines):
        if FIG_RE.match(lines[i]):
            buf = [lines[i]]
            i += 1
            while i < len(lines) and lines[i].strip() and not lines[i].startswith(("#", "!", ">", "|")):
                buf.append(lines[i].strip())
                i += 1
            out.append(" ".join(buf))
            continue
        out.append(lines[i])
        i += 1
    return out


def _norm(s: str) -> str:
    """대조용 정규화 — 공백과 강조 기호를 지운다. 낱말은 지우지 않는다."""
    return re.sub(r"[\s*`]", "", s)


def _check_claims(fig_caps: list[tuple[str, str]], fig_files: dict[str, str]) -> list[str]:
    """K4 — 선언(`figures-claims.yaml`)과 원고의 도판을 대조한다.

    **담당은 선언이지 추론이 아니다.** 캡션 문구를 정규식으로 훑어 기여를 추측하면 문구를
    다듬을 때마다 검사가 조용히 거짓 통과한다. 그래서 대조하는 것은 문구가 아니라
    ⓐ 기여마다 담당 도판이 있는가 ⓑ 선언한 번호의 그림이 원고에 있는가 ⓒ 그 번호가 가리키는
    파일이 선언과 같은가, 셋이다.
    """
    if not CLAIMS_YAML.exists():
        return [f"K4 선언 파일이 없다: {CLAIMS_YAML}"]
    try:
        import yaml
    except ImportError:                       # pragma: no cover - 실행 환경에 항상 있다
        return ["K4 PyYAML 이 없어 건너뛴다"]
    spec = yaml.safe_load(CLAIMS_YAML.read_text(encoding="utf-8")) or {}
    figs = spec.get("figures") or []
    contribs = spec.get("contributions") or {}
    warns: list[str] = []

    carried = {f.get("carries") for f in figs if f.get("carries")}
    for key, meta in contribs.items():
        if key not in carried:
            warns.append(f"K4 기여 {key}({meta.get('label', '')})를 담당하는 도판이 없다")
    for key in sorted(carried - set(contribs)):
        warns.append(f"K4 선언에 없는 기여를 담당한다고 적혀 있다: {key}")

    caps = dict(fig_caps)
    seen = set(caps)
    for f in figs:
        num, want = str(f.get("number")), f.get("file", "")
        if num not in seen:
            warns.append(f"K4 선언한 그림 {num}({want})이 원고에 없다")
            continue
        if fig_files.get(num) and fig_files[num] != want:
            warns.append(f"K4 그림 {num} 의 파일이 선언과 다르다: 원고 {fig_files[num]} · 선언 {want}")
        claim = f.get("claim") or ""
        if claim and _norm(claim) not in _norm(caps[num]):
            warns.append(
                f"K4 그림 {num} 의 캡션 첫 문장이 선언한 주장을 진술하지 않는다\n"
                f"      선언: {claim}\n"
                f"      캡션: {caps[num]}"
            )
    for num in sorted(seen - {str(f.get("number")) for f in figs}, key=int):
        warns.append(f"K4 원고의 그림 {num} 이 선언에 없다")
    return warns


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manuscript", type=Path)
    ap.add_argument("-o", "--out", type=Path)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--sections", default="3,4,5", help="K1 을 적용할 장 번호 (쉼표)")
    ap.add_argument("--figures-only", action="store_true",
                    help="그림 캡션 첫 문장만 순서대로 낸다 (그림만 읽는 경로)")
    ns = ap.parse_args()

    lines = ns.manuscript.read_text(encoding="utf-8", errors="replace").splitlines()
    lines = _join_captions(lines)
    out: list[str] = []
    warnings: list[str] = []
    cur_sec = ""
    fig_caps: list[tuple[str, str]] = []      # (번호, 캡션 첫 문장)
    fig_files: dict[str, str] = {}            # 번호 → 그림 파일 이름
    visuals: dict[str, int] = {}
    order: list[str] = []
    in_body = False
    for ln in lines:
        m = H_RE.match(ln)
        if m:
            level, title = len(m.group(1)), m.group(2).strip()
            # 원고의 소제목에는 검사기 면제 주석(`<!-- glossary-ok: … -->`)이 붙는 자리가 있다.
            # 골격 문서는 사람이 읽는 것이므로 주석을 떼고 싣는다 — 남기면 제목이 아니라 배선이 보인다.
            title = re.sub(r"\s*<!--.*?-->\s*$", "", title).strip()
            if re.match(r"^\d+\.", title) or title.startswith("#"):
                in_body = True
            if title.startswith(("참고문헌", "AI 사용 고지")):
                in_body = False
            if not in_body:
                continue
            if level <= 2:
                cur_sec = title
                visuals.setdefault(cur_sec, 0)
                order.append(cur_sec)
            out.append("#" * level + " " + title)
            if level >= 2 and re.search(r"\bEP\d\s*·", title):
                warnings.append(f"K3 제목이 식별자로 시작함(주장형 제목으로): {title}")
            continue
        if not in_body:
            continue
        m = IMG_RE.match(ln)
        if m:
            fig_files[m.group(1)] = m.group(2).rsplit("/", 1)[-1]
        m = FIG_RE.match(ln)
        if m:
            cap = first_sentence(m.group(2))
            fig_caps.append((m.group(1), cap))
            out.append(f"  [그림 {m.group(1)}] {cap}")
            visuals[cur_sec] = visuals.get(cur_sec, 0) + 1
            if len(cap) < 12:
                warnings.append(f"K2 그림 {m.group(1)} 캡션 첫 문장이 주장이 아님: '{cap}'")
            continue

        # K1은 새 그림의 직접 배치만 강제하지 않는다. 본문이 기존 그림을 번호로 다시
        # 가리키고 그 해석을 이어 가는 경우도 논증 장치다(PLAN-087 §4.3).
        if cur_sec and FIG_REF_RE.search(ln) and not ln.lstrip().startswith("!["):
            visuals[cur_sec] = max(visuals.get(cur_sec, 0), 1)
        m = EX_RE.match(ln)
        if m:
            out.append(f"  [예시 {m.group(1)} · {m.group(2).strip()}] {first_sentence(m.group(3))}")
            visuals[cur_sec] = visuals.get(cur_sec, 0) + 1
            continue
        m = TAB_RE.match(ln)
        if m:
            out.append(f"  [표 {m.group(1)}] {first_sentence(m.group(2))}")
            continue

    want = {s.strip() for s in ns.sections.split(",")}
    missing = [s for s in order if re.match(r"^(\d+)\.", s) and s.split(".")[0] in want and visuals.get(s, 0) == 0]
    for s in missing:
        warnings.append(f"K1 시각 장치 없음: {s}")

    warnings += _check_claims(fig_caps, fig_files)

    if ns.figures_only:
        print("# 그림만 읽는 경로 — 캡션 첫 문장")
        for num, cap in fig_caps:
            print(f"\n[그림 {num}] {cap}")
        if warnings:
            print("\n<!-- 검사 경고 -->")
            for w in warnings:
                print(f"- {w}")
        return 0

    text = "\n".join(out) + "\n"
    if warnings:
        text += "\n<!-- 검사 경고 -->\n" + "\n".join(f"- {w}" for w in warnings) + "\n"
    if ns.out:
        ns.out.write_text(text, encoding="utf-8")
        print(f"wrote {ns.out} ({len(out)} lines · 경고 {len(warnings)})")
    else:
        print(text)
    return 1 if (ns.check and missing) else 0


if __name__ == "__main__":
    raise SystemExit(main())
