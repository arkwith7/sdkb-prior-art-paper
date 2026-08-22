"""A-2 · EP5 CQ 개발 보정 — **개발 건물에서만** 실행한다 (PLAN-064 §2.2).

사전등록(PLAN-064-prereg.md) 발효 이전의 CQ 작성 보정이며, 판정 실행이 아니다. 홀드아웃 건물
(`ex-soda_brick.ttl`)은 이 스크립트가 읽지 않는다 — 읽으면 CQ 가 판정 대상에 맞춰진다.

  uv run python scripts/ep5_cq_calibrate.py

출력: 스위트별 CQ 행 수(개발 건물 · D0 = Brick v1.3.0) · 0 행 CQ 목록 · 스위트별 참조 술어와
(M) 묶음 술어 교집합. 결과는 `data/external/brick/ep5_cq_calibration.json` 에 기록한다.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from rdflib import Graph

ROOT = Path(__file__).resolve().parents[1]
CQ_DIR = ROOT / "queries" / "brick" / "cq"
BRICK_DIR = ROOT / "data" / "external" / "brick"
TBOX_D0 = BRICK_DIR / "Brick-v1.3.0.ttl"           # 계보의 첫 칸 (A-0 경고 ⓐ · v1.3.0 이후로 한정)
DEV_ABOX = ("ex-rice_brick.ttl", "ex-g36-combined-ahu-vav.ttl")
HOLDOUT = "ex-soda_brick.ttl"  # 이 스크립트는 열지 않는다 — 이름만 남겨 의도를 밝힌다

BRICK_NS = "https://brickschema.org/schema/Brick#"
PRED_RE = re.compile(r"brick:([A-Za-z_][A-Za-z0-9_]*)")
CLASS_HEAD = re.compile(r"rdfs:subClassOf\*\s+brick:([A-Za-z_][A-Za-z0-9_]*)")


def meta(text: str) -> dict:
    out = {}
    for line in text.splitlines():
        if not line.startswith("#"):
            break
        if ":" in line:
            k, v = line.removeprefix("#").split(":", 1)
            out[k.strip()] = v.strip()
    return out


def predicates(text: str) -> set[str]:
    """CQ 가 참조하는 brick 술어 — 클래스 위치의 토큰은 뺀다."""
    classes = set(CLASS_HEAD.findall(text)) | {
        m for m in PRED_RE.findall(text) if m[0].isupper()}
    return {m for m in PRED_RE.findall(text) if m not in classes}


def main() -> int:
    if any(a == HOLDOUT for a in DEV_ABOX):
        print("홀드아웃 파일이 개발 목록에 있다 — 보정을 중단한다", file=sys.stderr)
        return 2
    if not TBOX_D0.exists():
        print(f"D0 T-Box 가 없다: {TBOX_D0}", file=sys.stderr)
        return 2
    g = Graph()
    g.parse(TBOX_D0, format="turtle")
    tbox_triples = len(g)
    for a in DEV_ABOX:
        g.parse(BRICK_DIR / a, format="turtle")
    print(f"개발 그래프: T-Box {tbox_triples:,} + 개발 A-Box {len(DEV_ABOX)}개 → 합 {len(g):,} 트리플")

    rows, preds, zero = {}, {}, []
    for rq in sorted(CQ_DIR.glob("*.rq")):
        text = rq.read_text(encoding="utf-8")
        m = meta(text)
        n = len(list(g.query(text)))
        rows[rq.name] = dict(suite=m.get("suite"), expect_min=int(m.get("expect-min", 1)),
                             shared=m.get("shared", "false"), rows=n, passes=n >= int(m.get("expect-min", 1)))
        preds.setdefault(m.get("suite"), set()).update(predicates(text))
        if n == 0:
            zero.append(rq.name)
        print(f"   {m.get('suite'):5s} {rq.name:45s} rows={n:5d} "
              f"{'통과' if n >= int(m.get('expect-min', 1)) else '0행 — 제거 대상'}")

    print("\n== 스위트별 참조 술어")
    for s, p in sorted(preds.items()):
        print(f"   {s}: {sorted(p)}")
    inter = {f"{a}∩{b}": sorted(preds[a] & preds[b])
             for a in preds for b in preds if a < b}
    print("\n== 스위트 간 술어 교집합")
    for k, v in inter.items():
        print(f"   {k}: {v}")

    out = dict(tbox=str(TBOX_D0.name), tbox_triples=tbox_triples, dev_abox=list(DEV_ABOX),
               graph_triples=len(g), cq=rows,
               suite_predicates={k: sorted(v) for k, v in preds.items()},
               suite_intersections=inter, zero_row=zero)
    (BRICK_DIR / "ep5_cq_calibration.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n0 행 CQ {len(zero)}건: {zero}")
    print(f"기록: {BRICK_DIR / 'ep5_cq_calibration.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
