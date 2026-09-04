#!/usr/bin/env python3
"""gen_case_card.py — PLAN-088 관통 사례의 사례 카드를 산출물에서 생성한다.

원고 §5.2·§5.3 이 인용하는 단일 사례의 표를 **손으로 옮겨 적지 않기 위한** 생성기다
(CLAUDE.md §1-1 · §1-7). 사람이 고르는 것은 아무것도 없다 — 사례는 아래 동결 규칙이
정하고, 순위는 동결 runset 의 TREC run 에서 조회하며, 정답은 그래프의 심사관 인용
간선에서 읽는다.

**봉인은 열지 않는다 (PLAN-088 §3.4 · O-18).** 정답지로 봉인 qrel(`test`·`test_b`)을
쓰지 않으므로 열람 원장에 행이 늘지 않는다. 대가로 이 표의 순위는 **문헌 단위**이며
주지표의 family 단위가 아니다 — 카드가 그 사실을 스스로 밝힌다.

선정 규칙 (동결 · PLAN-088 §3.1)
  `key_test.jsonl` 에서 `drop` 이 **중앙값에 가장 가까운 단위**. 동률은 `unit_id`
  오름차순. 다른 조건으로 거르지 않는다.

§1-5 — 원문 리터럴은 어떤 경로로도 출력하지 않는다. `LITERALS_NEVER_EMITTED` 참조.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sdkb_paper import config  # noqa: E402

TYPOLOGY = config.IR_DIR / "typology"
KEY_TEST = TYPOLOGY / "key_test.jsonl"
SHEET_TEST = TYPOLOGY / "sheet_test.jsonl"

# 자원 세대 두 팔 (EP3 · PLAN-035 동결 사본)
ARM_O = "O_d578bf3_linkercode"
ARM_OPRIME = "Oprime_2839afb"
SYSTEMS = [("B3_rrf", "텍스트 하이브리드 B3"),
           ("P1", "온톨로지 결합 P1"),
           ("B5_concept", "온톨로지 단독 B5")]

#: 재배포가 금지된 원문 리터럴과, 게재하지 않기로 한 서지 항목(PLAN-088 §3.5).
#: 출력 문자열에 이 술어의 값이 섞이면 생성기가 죽는다 — §1-5 를 사람이 아니라 코드가 지킨다.
LITERALS_NEVER_EMITTED = ("abstractText", "claimText", "firstClaimText", "prefLabel")

DEFAULT_OUT = ROOT / "paper" / "tables" / "case_card_ep3.md"


def select_unit(key_path: Path = KEY_TEST) -> dict:
    """동결 규칙이 고르는 단위 하나. 규칙에 자유도가 없다(PLAN-088 §3.1)."""
    units = [json.loads(ln) for ln in key_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not units:
        raise ValueError(f"단위가 없다: {key_path}")
    median = statistics.median(u["drop"] for u in units)
    return min(units, key=lambda u: (abs(u["drop"] - median), u["unit_id"]))


def examiner_citations(graph_path: Path, qid: str) -> list[str]:
    """질의 특허의 `hasPriorArtExaminer` 간선. 봉인 qrel 을 열지 않는 정답 경로다."""
    subject = f"pat:{qid} "
    text = graph_path.read_text(encoding="utf-8")
    start = text.find("\n" + subject)
    if start < 0:
        raise ValueError(f"그래프에 질의가 없다: {qid}")
    block = text[start + 1:]
    nxt = re.search(r"\n(?=[a-z]+:\S+ a )", block)
    if nxt:
        block = block[: nxt.start()]
    cited: list[str] = []
    for m in re.finditer(r"ont:hasPriorArtExaminer\s+(.*?);", block, re.S):
        cited += re.findall(r"pat:([^\s,;]+)", m.group(1))
    return sorted(set(cited))


def rank_of(run_path: Path, qid: str, docid: str) -> int | None:
    """TREC run 에서 (질의, 문헌)의 순위. 없으면 None(회수되지 않음)."""
    for ln in run_path.read_text(encoding="utf-8").splitlines():
        p = ln.split()
        if len(p) >= 4 and p[0] == qid and p[2] == docid:
            return int(p[3])
    return None


def crossings(arm: str, system: str, split: str, graph_path: Path, k: int = 100) -> tuple[int, int]:
    """한 팔에서 심사관 인용이 상위 k 안에 있던 질의 수와 전체 질의 수 (C단계 환산용)."""
    run = config.IR_RUNSETS_DIR / arm / f"sys_{system}_{split}.txt"
    top: dict[str, set[str]] = {}
    for ln in run.read_text(encoding="utf-8").splitlines():
        p = ln.split()
        if len(p) >= 4 and int(p[3]) <= k:
            top.setdefault(p[0], set()).add(p[2])
    hit = sum(1 for q, docs in top.items() if docs & set(examiner_citations(graph_path, q)))
    return hit, len(top)


def decomposition_note(qid: str, lost: str) -> str:
    """왜 밀렸는가 — 항별 점수 분해를 산출물에서 읽어 한 문장으로 낸다(§5.3).

    질의·문헌의 개념 집합과 항별 델타는 `sheet_test.jsonl` 이 이미 계산해 두었다.
    수치를 원고에 손으로 옮기지 않기 위하여 이 문장도 생성기가 낸다(§1-1).
    """
    unit_id = f"test:{qid}:"
    row = next(json.loads(ln) for ln in SHEET_TEST.read_text(encoding="utf-8").splitlines()
               if ln.startswith('{"unit_id": "' + unit_id))
    focus = row["focus_slot"]
    qc = set(row["query"]["concepts"])
    lostc = set(next(d["concepts"] for d in row["documents"] if d["slot"] == focus))
    # 밀어 올린 힘이 개념 항에서 나온 경쟁 문서 가운데 개념 델타가 가장 큰 것
    best = max((d for d in row["decomposition"] if d["driver"] == "concept"),
               key=lambda d: d["delta"]["concept"], default=None)
    if best is None:
        return "> 이 사례에서 개념 항이 주도한 역전은 관측되지 않았다."
    comp = set(next(d["concepts"] for d in row["documents"] if d["slot"] == best["slot"]))
    # 원고의 부호 표기는 U+2212 이다 — ASCII 하이픈을 섞으면 수치 대조가 갈린다.
    def sign(v: float) -> str:
        return f"{v:+.4f}".replace("-", "−")

    return (
        f"> **왜 밀렸는가.** 질의가 보유한 개념 {len(qc)}개와 이 문헌이 보유한 개념 "
        f"{len(lostc)}개가 공유하는 것은 {len(qc & lostc)}개이다. 반면 정답이 아닌 한 문서는 "
        f"질의와 개념 {len(qc & comp)}개를 공유하여 개념 항에서 {sign(best['delta']['concept'])}로 "
        f"앞섰고, 본문 점수에서는 {sign(best['delta']['text'])}로 뒤졌다. 곧 개념 항이 본문 "
        "점수의 판단을 뒤집었다."
    )


def _guard(text: str, graph_path: Path, qid: str) -> None:
    """출력에 원문 리터럴이 섞이지 않았는지 확인한다(§1-5)."""
    subject = f"pat:{qid} "
    start = graph_path.read_text(encoding="utf-8").find("\n" + subject)
    block = graph_path.read_text(encoding="utf-8")[start + 1: start + 20000]
    for pred in LITERALS_NEVER_EMITTED:
        for m in re.finditer(rf"{pred}\s+\"+(.{{40,120}})", block):
            frag = m.group(1)[:40]
            if frag and frag in text:
                raise ValueError(f"원문 리터럴이 출력에 섞였다({pred}): {frag[:20]}…")


def render(graph_path: Path = config.GRAPH_V0) -> str:
    unit = select_unit()
    qid, lost = unit["qid"], unit["lost_doc"]
    cited = examiner_citations(graph_path, qid)
    if lost not in cited:
        raise ValueError(f"추적 대상이 심사관 인용이 아니다: {lost}")

    rows = []
    for sys_key, label in SYSTEMS:
        vals = []
        for arm in (ARM_O, ARM_OPRIME):
            r = rank_of(config.IR_RUNSETS_DIR / arm / f"sys_{sys_key}_test.txt", qid, lost)
            vals.append(str(r) if r else "미회수")
        rows.append(f"| {label} | {vals[0]} | {vals[1]} |")

    # **캡션은 이 파일이 내지 않는다.** 표 번호의 연번 검사(§8.1 V6)는 산문 소스를 보므로,
    # 캡션이 생성 파일에만 있으면 소스의 번호가 결번으로 읽힌다. 캡션은 소스에 두고
    # 여기서는 그 캡션이 이 사례를 가리키는지 `--check` 로 대조한다.
    out = [
        "| 순위 함수 | 교체 전 자원(O) | 교체 후 자원(O′) |",
        "|---|---:|---:|",
        *rows,
        "",
        f"> 이 특허의 심사관 인용은 {len(cited)}건이며 위 추적은 그 가운데 한 건이다. "
        "사례는 동결한 규칙이 고른 것이고 결과를 보고 고른 것이 아니다(§4.5). "
        "순위는 문헌 단위이며 주 지표의 패밀리 단위가 아니므로 표 5의 값과 같은 것으로 "
        "읽지 않는다. 이 표는 표 5의 질의 평균을 한 질의에서 읽는 렌즈이며 판정의 근거가 "
        "아니다. 정답은 봉인된 평가셋이 아니라 그래프의 심사관 인용 간선에서 읽었다.",
        "",
        decomposition_note(qid, lost),
    ]
    text = "\n".join(out) + "\n"
    _guard(text, graph_path, qid)
    return text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--crossings", action="store_true",
                    help="C단계 환산 — 심사관 인용이 상위 100 안에 있던 질의 수를 두 팔에서 센다")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    if a.crossings:
        for arm in (ARM_O, ARM_OPRIME):
            hit, total = crossings(arm, "P1", "test", config.GRAPH_V0)
            print(f"{arm} P1 test: 상위100 안에 심사관 인용이 있던 질의 {hit}/{total}")
        return 0

    text = render()
    if a.check:
        # 캡션은 산문 소스에 있으므로 그것이 이 사례를 가리키는지 함께 대조한다.
        unit = select_unit()
        src = (ROOT / "paper" / "manuscript" / "stage3_source.md").read_text(encoding="utf-8")
        caption = next((ln for ln in src.splitlines() if ln.startswith("**표 6.")), "")
        if unit["qid"] not in caption or unit["lost_doc"] not in caption:
            print(f"캡션이 선정 사례와 어긋난다: {caption[:60]}…", file=sys.stderr)
            return 2
        cur = a.out.read_text(encoding="utf-8") if a.out.exists() else ""
        if cur != text:
            print(f"어긋남: {a.out} — `make case-card` 로 다시 생성하라", file=sys.stderr)
            return 2
        print(f"정합: {a.out}")
        return 0
    a.out.write_text(text, encoding="utf-8")
    print(f"생성: {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
