"""사례 카드 사람 검증 패키지 — 본실험 진입 조건(2차 결정 · 2026-10-18 · PLAN-096).

**원문은 이 코드가 읽지 않는다.** 통지서 원문은 상류 결정(2026-10-09)상 LLM 에 보내지 않으므로, 검토자가 직접 원문을 열어
근거 문장을 대조하도록 **식별자 · 구조 필드 · 대조표**만 만든다. 출력은 비커밋 디렉터리(`PILOT_DIR/review/`)에 쓴다 —
통지서 식별자를 공개 트리에 싣지 않는다(상류 규칙).

통계 집계 항목(`judgment_items.json`)과 사례 카드를 구분한다. 카드의 "검색 행동 제안 후보" 는 구조 필드에서 기계적으로 만든
**미검증 후보**이며, 검토자가 채택·기각하기 전에는 어떤 실행에도 쓰지 않는다.
"""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

from .. import config
from .judgment_items import LABEL, _local

OUT = config.PILOT_DIR / "review"
CODES = ("일치", "부분 일치", "불일치", "판단 불가")


def _judgment_index(ttl: Path) -> dict[str, dict]:
    """jid(판단 IRI 해시) → 판단 IRI · 통지서 IRI · 근거 연결(문헌 · 위치 종류 · 위치 값)."""
    import rdflib

    g = rdflib.Graph()
    g.parse(str(ttl), format="turtle")
    by = defaultdict(list)
    for s, p, o in g:
        by[_local(p)].append((s, o))
    asserted = {s: o for s, o in by["assertedIn"]}
    part = defaultdict(list)
    for s, o in by["partOfJudgment"]:
        part[o].append(s)
    in_doc = {s: o for s, o in by["inDocument"]}
    loc = {s: o for s, o in by["locator"]}
    ltype = {s: _local(o) for s, o in by["locatorType"]}
    lval = {s: str(o) for s, o in by["locatorValue"]}
    idx = {}
    for j in {s for s, _ in by["judgesClaim"]}:
        jid = hashlib.sha256(str(j).encode()).hexdigest()[:12]
        links = []
        for link in part.get(j, []):
            lo = loc.get(link)
            links.append({"document": _local(in_doc.get(link, "")), "locator_type": ltype.get(lo),
                          "locator_value": lval.get(lo)})
        idx[jid] = {"judgment_iri": str(j), "notice_iri": str(asserted.get(j, "")),
                    "links": sorted(links, key=lambda x: (x["document"], str(x["locator_value"])))}
    return idx


def _public_number(doc_local: str) -> str:
    """`kr_KR1020090012345A` → `KR1020090012345A` (공개 공보번호)."""
    return doc_local.split("_", 1)[1] if "_" in doc_local else doc_local


def suggestion_candidates(card: dict, items: dict) -> list[str]:
    """구조 필드에서 만든 **미검증** 검색 행동 후보 — 검토자 판정 전에는 쓰지 않는다."""
    out = []
    if card.get("scope") == "ScopeAddedLimitation":
        out.append("부가 한정 요소를 독립항과 따로 검색한다(판단 범위 = 부가 한정)")
    if "RationaleDesignChoice" in card.get("rationale", []):
        out.append("설계변경 논거 — 요소를 단독으로 개시한 문헌과 결합 대상 문헌을 각각 찾는 검색식을 둔다")
    if "RationalePredictableEffect" in card.get("rationale", []):
        out.append("예측가능 효과 논거 — 효과 표현(목적·작용) 쪽 낱말로도 검색한다")
    if card.get("common_knowledge"):
        out.append("공지기술로 처리된 요소는 문헌이 없을 수 있다 — 그 요소만으로 검토량을 쓰지 않는다")
    ipcs = sorted({g for c in card.get("cited", []) for g in c.get("ipc_main_groups", [])})
    if ipcs:
        out.append("인용 문헌 IPC 메인그룹 한정 검색 후보: " + ", ".join(ipcs[:5]))
    return out


def build(cards_path: Path | None = None) -> Path:
    cards = json.loads(Path(cards_path or config.PILOT_DIR / "case_cards.json").read_text(encoding="utf-8"))
    items = json.loads((config.PILOT_DIR / "judgment_items.json").read_text(encoding="utf-8"))["items"]
    idx = _judgment_index(config.PILOT_ARGUMENT_TTL)
    OUT.mkdir(parents=True, exist_ok=True)
    lines = ["# 사례 카드 사람 검증 시트 (비커밋 · PLAN-096 2차 결정)", "",
             "> 원문(의견제출통지서)은 검토자가 직접 연다. 이 시트는 원문 문장을 담지 않는다.",
             f"> 판정 코드: {' · '.join(CODES)}. 근거 문장은 검토자가 원문에서 옮겨 적는다(필요한 최소 분량).",
             "> 아래 '통계 집계 항목' 은 카드와 다른 층이다 — 카드가 그 집계를 대표하는지만 본다.", ""]
    rows = []
    for c in cards:
        if not c.get("found"):
            lines += [f"## {c['slot']} — 해당 판단 없음", ""]
            continue
        meta = idx.get(c["jid"], {})
        cand = suggestion_candidates(c, items)
        lines += [f"## {c['slot']} · 카드 {c['jid']}", "",
                  f"- 출원(공개): {', '.join(c['application'])} · 판단 대상 청구항: {', '.join(c['claims'])}",
                  f"- 통지서 식별자(원문 찾기용): `{meta.get('notice_iri', '?')}` · 판단 블록: `{meta.get('judgment_iri', '?').rsplit('/', 1)[-1]}`",
                  f"- 구조 필드: 근거 {c['ground']} · 범위 {c['scope']} · 논거 {c['rationale'] or '없음'} · 공지기술 {c['common_knowledge']}",
                  "- 인용 문헌(공개 번호 · 위치는 **검증 FAIL 0.80 — 참고용**):"]
        for link in meta.get("links", []):
            lines.append(f"  - {_public_number(link['document'])} · {link['locator_type'] or '-'} {link['locator_value'] or ''}")
        if not meta.get("links"):
            lines.append(f"  - (근거 연결 없음 · 인용 수 {c['n_cited']})")
        lines += [f"- 요소 유형(청구항 단위 한정요소 개념): {', '.join(c['element_types']) or '없음'}",
                  f"- 통계 집계 항목({LABEL}) — 이 카드의 요소 유형 중 항목이 있는 것: {', '.join(c['element_types_with_item']) or '없음'}",
                  "", "| 고리 | 대조할 것 | 검토자 기입(근거 문장 · 메모) | 판정 |", "|---|---|---|---|",
                  "| ① 원문 판단 근거 | 위 구조 필드(근거·범위·논거·공지기술)가 통지서의 해당 블록 서술과 맞는가 | | |",
                  "| ② 적용 요소·조건 | 판단이 실제로 다룬 청구항 요소가 위 요소 유형과 맞는가 · 어떤 조건에서 그 판단이 나왔는가 | | |",
                  "| ③ 검색 행동 제안 | 아래 후보 각각이 이 사례의 판단에서 정당하게 나오는가(채택/기각) | | |",
                  "| ④ 적용 한계 | 이 사례를 다른 출원에 옮길 때 깨지는 조건 | | |", "",
                  "검색 행동 제안 후보(**미검증 · 구조 필드에서 기계 생성**):"] + [f"- [ ] {x}" for x in cand] + [""]
        rows.append({"slot": c["slot"], "jid": c["jid"], "candidates": len(cand), "links": len(meta.get("links", []))})
    sheet = OUT / "case_review_sheet.md"
    sheet.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (OUT / "summary.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return sheet


if __name__ == "__main__":
    print(f"✓ 검증 시트 → {build()}")
