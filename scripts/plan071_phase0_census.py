"""PLAN-071 §-1.4 Phase 0 계수 — 판단 문장의 쌍 지시율과 개념 해소율.

사전등록이 아니라 **착수 조건의 실측**이다(PLAN-071 §-1.4). 코퍼스·qrel·검색 설정은
읽지 않으며 산출물도 만들지 않는다 — 출력은 표준출력뿐이고, 등재는 사람이 계획 문서에 한다.

§0.1 과의 관계. 원천(의견제출통지서·거절결정서 원문)과 개념 사전은 **상류에만** 있고 벤더
스냅샷에 없다. 그래서 이 스크립트는 상류 경로를 **인자로 받는다** — 파이프라인이 런타임에
상류를 읽는 것이 아니라, `make vendor` 와 같이 사람이 상류를 가리켜 한 번 돌리는 계수기다.
`src/` 를 건드리지 않으며 어떤 make 표적에도 걸리지 않는다.

§1-4 와의 관계. 계수 범위는 **dev 분할뿐**이다. test·test_b 는 인자로도 받지 않는다.

사용
  python scripts/plan071_phase0_census.py --sdkb ~/Dev/sdkb [--dict-refs main HEAD]
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import subprocess
from pathlib import Path

import pandas as pd

#: 거절이유 유형별 단서(cue) — PLAN-071 §-1.3(c) 의 유형 다섯을 문장 층으로 옮긴 것이다.
CUES = {
    "결합": r"결합|조합",
    "설계변경": r"설계변경|설계 변경|단순한 설계|설계적 사항",
    "임계적 의의": r"임계적 의의|임계적|수치한정|수치 한정",
    "치환": r"치환|균등물|균등 수단",
    "주지관용": r"주지관용|주지·관용|주지 관용|주지기술|주지 기술|관용수단|관용 수단",
}
#: 쌍 지시 = 한 문장이 본원 측과 인용 측을 함께 가리킨다.
SELF = r"본원|본 발명|본원발명|이 출원|출원발명|청구항 제?\s*\d+"
CITED = r"인용발명|인용문헌|비교대상발명|선행문헌|인용참증|비교대상 발명"

#: 원문은 문장 중간에서 줄바꿈되므로 줄을 이어 붙인 뒤 나눈다.
_SENT = re.compile(r"(?<=다\.)\s+|(?<=[.。])\s+(?=[가-힣\d])")
_MIN_SENT_CHARS = 10
#: 해소 판정 문턱 — 한 문장에서 서로 다른 표면형이 둘 이상 걸려야 쌍이 성립한다.
MIN_CONCEPTS = 2


def sentences(text: str) -> list[str]:
    flat = re.sub(r"\s+", " ", text)
    return [s.strip() for s in _SENT.split(flat) if len(s.strip()) >= _MIN_SENT_CHARS]


def load_surfaces(sdkb: Path, ref: str) -> list[str]:
    """`patent-text` 프로파일의 표면형. ref 가 'HEAD' 면 작업 트리 파일을 읽는다."""
    path = "mappings/concept_mapping.json"
    if ref == "HEAD":
        raw = (sdkb / path).read_text()
    else:
        raw = subprocess.run(["git", "-C", str(sdkb), "show", f"{ref}:{path}"],
                             capture_output=True, text=True, check=True).stdout
    entries = json.loads(raw)["profiles"]["patent-text"]["entries"]
    return sorted({e["surface"] for e in entries}, key=len, reverse=True)


def make_matcher(surfaces: list[str]):
    pat = re.compile("|".join(re.escape(s) for s in surfaces), re.IGNORECASE)
    return lambda s: {m.group(0).lower() for m in pat.finditer(s)}


def dev_applications(split_parquet: Path) -> list[str]:
    df = pd.read_parquet(split_parquet)
    return [d.replace("kr_", "") for d in sorted(df.loc[df["split"] == "dev", "doc_id"])]


def collect(sdkb: Path, apps: list[str]) -> tuple[list[tuple[str, str, str]], dict[str, int]]:
    """(유형, 문장, 원천종류) 목록과 원천별 대응 문서 수."""
    idx = json.loads((sdkb / "data/sources/opinion_notices/_index.json").read_text())
    decisions: dict[str, list[Path]] = {}
    for p in (sdkb / "data/sources/rejection_decisions/txt").glob("*.txt"):
        decisions.setdefault(p.stem.split("_")[0], []).append(p)

    rows: list[tuple[str, str, str]] = []
    matched = collections.Counter()
    for app in apps:
        notices = [sdkb / "data/sources/opinion_notices/txt" / f"{d['file']}.txt"
                   for d in idx.get(app, {}).get("docs", [])]
        for kind, paths in (("통지서", notices), ("결정서", decisions.get(app, []))):
            present = False
            for path in paths:
                if not path.exists():
                    continue
                present = True
                for s in sentences(path.read_text(errors="ignore")):
                    for name, pat in CUES.items():
                        if re.search(pat, s):
                            rows.append((name, s, kind))
                            break
            matched[kind] += int(present)
    return rows, matched


def census(rows, matcher) -> tuple[dict[str, tuple[int, int, int]], tuple[int, int, int]]:
    per_type, totals = {}, [0, 0, 0]
    for name in CUES:
        cue = [s for n, s, _ in rows if n == name]
        pair = [s for s in cue if re.search(SELF, s) and re.search(CITED, s)]
        resolved = [s for s in pair if len(matcher(s)) >= MIN_CONCEPTS]
        per_type[name] = (len(cue), len(pair), len(resolved))
        for i, v in enumerate((len(cue), len(pair), len(resolved))):
            totals[i] += v
    return per_type, tuple(totals)


def headroom(rows, matcher) -> collections.Counter:
    """미해소 쌍 지시 문장이 이미 몇 개를 걸었는가 — 어휘 확충의 여지.

    0 개는 그 문장에 기술 낱말 자체가 없다는 뜻(정형구)이고, 1 개는 낱말 하나만 더
    등재되면 해소된다는 뜻이다. 불용어 목록 없이 재는 지표이므로 임의성이 없다.
    """
    dist = collections.Counter()
    for _n, s, _k in rows:
        if not (re.search(SELF, s) and re.search(CITED, s)):
            continue
        hits = len(matcher(s))
        if hits >= MIN_CONCEPTS:
            continue
        dist[hits] += 1
    return dist


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sdkb", type=Path, required=True, help="상류 SDKB 작업 트리")
    ap.add_argument("--split", type=Path, default=Path("data/processed/ir/split.parquet"))
    ap.add_argument("--dict-refs", nargs="+", default=["main", "HEAD"],
                    help="비교할 사전 판(상류 git ref). 같은 스크립트로 돌려야 차이가 판정된다")
    args = ap.parse_args()

    apps = dev_applications(args.split)
    rows, matched = collect(args.sdkb, apps)
    print(f"dev 질의 {len(apps)} · 통지서 대응 {matched['통지서']} · 결정서 대응 {matched['결정서']}")

    for ref in args.dict_refs:
        surfaces = load_surfaces(args.sdkb, ref)
        matcher = make_matcher(surfaces)
        per_type, (cue, pair, res) = census(rows, matcher)
        korean = sum(1 for s in surfaces if re.search(r"[가-힣]", s))
        print(f"\n== 사전 {ref} · 표면형 {len(surfaces)} (한글 {korean}) ==")
        print(f"{'유형':<12}{'cue 문장':>9}{'쌍 지시':>9}{'양쪽 해소':>10}")
        for name, (a, b, c) in per_type.items():
            print(f"{name:<12}{a:>9}{b:>9}{c:>10}")
        print(f"{'합계':<12}{cue:>9}{pair:>9}{res:>10}")
        print(f"② 쌍 지시 = {pair}/{cue} = {pair / max(cue, 1):.1%}"
              f" · ③ 해소 = {res}/{max(pair, 1)} = {res / max(pair, 1):.1%}"
              f" · 1×2×3 = {res}")
        if ref == args.dict_refs[-1]:
            dist = headroom(rows, matcher)
            total = sum(dist.values())
            print(f"\n미해소 쌍 지시 문장 {total}건 · 이미 걸린 표면형 수 분포")
            for k in sorted(dist):
                print(f"  {k}개 : {dist[k]:4d} ({dist[k] / max(total, 1):.1%})")


if __name__ == "__main__":
    main()
