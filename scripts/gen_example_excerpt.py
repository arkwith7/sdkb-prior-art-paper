#!/usr/bin/env python3
"""Generate the running-example excerpt for §3 from the measured graph.

원고는 예시의 RDF 사실을 손으로 옮겨 적지 않는다(CLAUDE.md §1-1 · §1-7). 이 생성기는
**PLAN-088 이 동결한 관통 사례**의 트리플 아홉을 `data/processed/graph_v0.ttl` 에서 확인한 뒤
안정된 Markdown/Turtle 블록으로 낸다. 하나라도 없으면 그리지 않고 멈춘다.

**PLAN-088 · 합성 픽스처에서 실사례로 (2026-09-04 · 사용자 승인).** 이전 판은
`data/samples/mini_graph.ttl` 의 합성 거절특허를 썼다. 그 예시는 §4 에서 멈추었고 원고가
스스로 판정을 대표하지 않는다고 밝혀, 사례가 증거에서 끊겨 있었다. 이제 §5 의 판정에 실제로
등장하는 거절특허를 §3 부터 쓴다 — 같은 특허가 §3 의 공유 공정 노드, §4 의 평가 질의,
§5 의 추적 대상이다.

**§1-5.** KIPRIS 원문(초록·청구항)과 특허 제목은 어떤 경로로도 출력하지 않는다. 싣는 것은
식별자·날짜·IRI 뿐이며, `FORBIDDEN_PREDICATES` 가 그것을 코드로 강제한다.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sdkb_paper import config  # noqa: E402

DEFAULT_OUT = ROOT / "paper" / "tables" / "example_1_graph.md"

#: 관통 사례 — 선정 규칙과 그 결과는 PLAN-088 §3 이 동결하였다.
#: `scripts/gen_case_card.py` 의 `select_unit()` 이 같은 값을 내는지 회귀 테스트가 확인한다.
QID = "kr_1020210110925"
CITED = "kr_KR1020140023210A"
PROCESS = "process/etch"
SUBPROCESS = "subprocess/plasma_etch"
SKILL = "skill/endpoint_detection"
EXPERT = "expert/EXP_013"
FILING = "2021-08-23"

#: 출력에 값이 실려서는 안 되는 술어(§1-5 · PLAN-088 §3.5).
FORBIDDEN_PREDICATES = ("abstractText", "claimText", "firstClaimText", "prefLabel")


def _block(text: str, subject: str) -> str:
    """주어 하나의 Turtle 블록. 다음 주어가 시작되는 곳에서 끊는다."""
    start = text.find("\n" + subject + " ")
    if start < 0:
        raise ValueError(f"그래프에 주어가 없다: {subject}")
    rest = text[start + 1:]
    nxt = re.search(r"\n(?=(?:<[^>\s]+>|[a-z]+:\S+) a )", rest)
    return rest[: nxt.start()] if nxt else rest


def verify(source: Path) -> None:
    """예시가 주장하는 아홉 트리플이 실제 그래프에 있는지 확인한다."""
    text = source.read_text(encoding="utf-8")
    pat = _block(text, f"pat:{QID}")
    proc = _block(text, f"<https://w3id.org/sdkb/data/{PROCESS}>")
    sub = _block(text, f"<https://w3id.org/sdkb/data/{SUBPROCESS}>")
    exp = _block(text, f"<https://w3id.org/sdkb/data/{EXPERT}>")

    checks = [
        ("ont:Patent", "ont:Patent" in pat),
        ("ont:RejectedPatent", "ont:RejectedPatent" in pat),
        (f"filingDate {FILING}", FILING in pat),
        (f"realizesProcess {PROCESS}", PROCESS in pat),
        ("rejectedFor Rejection_Inventiveness", "Rejection_Inventiveness" in pat),
        (f"hasPriorArtExaminer {CITED}", re.search(rf"hasPriorArtExaminer(.|\n)*?{CITED}", pat) is not None),
        (f"{PROCESS} hasSubprocess {SUBPROCESS}", SUBPROCESS in proc),
        (f"{SUBPROCESS} requiresSkill {SKILL}", SKILL in sub),
        (f"{EXPERT} hasSkill {SKILL}", SKILL in exp),
    ]
    missing = [name for name, ok in checks if not ok]
    if missing:
        raise ValueError("예시 1의 필수 트리플이 그래프에 없다:\n" + "\n".join(f"  - {m}" for m in missing))


def render(source: Path = config.GRAPH_V0) -> str:
    verify(source)
    text = (
        "```turtle\n"
        f"pat:{QID}  a  ont:Patent, ont:RejectedPatent ;\n"
        f"    ont:filingDate          \"{FILING}\"^^xsd:date ;\n"
        f"    ont:realizesProcess     <…/{PROCESS}> ;\n"
        "    ont:rejectedFor         ont:Rejection_Inventiveness ;\n"
        f"    ont:hasPriorArtExaminer <…/patent/{CITED}> .\n"
        f"<…/{PROCESS}>          ont:hasSubprocess <…/{SUBPROCESS}> .\n"
        f"<…/{SUBPROCESS}>    ont:requiresSkill <…/{SKILL}> .\n"
        f"<…/{EXPERT}>        ont:hasSkill      <…/{SKILL}> .\n"
        "```\n"
    )
    for pred in FORBIDDEN_PREDICATES:
        if pred in text:
            raise ValueError(f"금지 술어가 출력에 있다(§1-5): {pred}")
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=config.GRAPH_V0)
    parser.add_argument("-o", "--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    text = render(args.source)
    if args.check:
        if not args.out.exists() or args.out.read_text(encoding="utf-8") != text:
            print(f"불일치: {args.out} — gen_example_excerpt.py 로 재생성한다")
            return 1
        print(f"통과: {args.out} (실측 그래프 유래 트리플 9건)")
        return 0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")
    print(f"wrote {args.out} (실측 그래프 유래 트리플 9건)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
