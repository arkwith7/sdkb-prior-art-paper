"""PLAN-074 §2 2단계 관찰 — dev 전용. 결정하지 않는다.

사전등록이 아니라 **요구정의 뒤의 관찰**이다(PLAN-074 §7). 산출물을 만들지 않으며 출력은
표준출력뿐이다 — 등재는 사람이 계획 문서에 한다. 순위·지표는 계산하지 않는다.

§0.1 과의 관계. 원천(의견제출통지서·거절결정서)과 개념 사전은 상류에만 있으므로 상류 경로를
**인자로 받는다**. `src/` 를 건드리지 않고 어떤 make 표적에도 걸리지 않는다.

§1-4 와의 관계. 범위는 dev 200질의뿐이다 — test·test_b 는 인자로도 받지 않으며 봉인 파일을
열지 않는다.

사용
  uv run python scripts/plan074_stage2_observe.py --sdkb ~/Dev/sdkb
"""
from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

import pandas as pd

#: 거절이유 유형 단서 — PLAN-071 §-1.3(c) 의 다섯 유형.
CUES = {
    "결합": r"결합|조합",
    "설계변경": r"설계변경|설계 변경|단순한 설계|설계적 사항",
    "임계적 의의": r"임계적|수치한정|수치 한정",
    "치환": r"치환|균등물",
    "주지관용": r"주지관용|주지 관용|주지기술|관용수단",
}
#: 인용발명 정의 줄 — "인용발명 1 : 공개특허공보 제10-2012-0075051호(2012.07.06.)".
CITE_LINE = re.compile(r"인용발명\s*(\d+)\s*[:：]\s*([^\n]{5,120})")
NUMS = re.compile(
    r"(?:특개|특표|공개특허|등록특허|공보)?\s*(?:제)?\s*"
    r"([0-9]{2,4}[\-–][0-9]{4}[\-–][0-9]{7}|[0-9]{4}[\-–][0-9]{6}|[0-9]{2}[\-–][0-9]{7}|[0-9]{7,13})"
)
#: 대비표 단서 — 표 형식으로 구성 대비가 제시되는가.
TABLE_CUES = {
    "<표 N>": r"<\s*표\s*\d",
    "구성 N-M": r"구성\s*\d+\s*[-–]\s*\d+",
    "구성요소": r"구성요소",
    "대비표 언급": r"대비\s*표|아래\s*표",
    "비고 열": r"비\s?고",
}


def digits(s: str) -> str:
    return re.sub(r"\D", "", str(s))


def load_concepts(sdkb: Path):
    entries = json.loads((sdkb / "mappings/concept_mapping.json").read_text())
    entries = entries["profiles"]["patent-text"]["entries"]
    s2c = {e["surface"].lower(): (e.get("concept") or e.get("concept_id")) for e in entries}
    pat = re.compile("|".join(re.escape(s) for s in sorted(s2c, key=len, reverse=True)), re.I)
    return lambda t: {s2c[m.group(0).lower()] for m in pat.finditer(t or "")}


def sources(sdkb: Path, apps: list[str]) -> dict[str, list[str]]:
    """출원번호 → 통지서·결정서 원문 목록."""
    idx = json.loads((sdkb / "data/sources/opinion_notices/_index.json").read_text())
    dec: dict[str, list[Path]] = collections.defaultdict(list)
    for p in (sdkb / "data/sources/rejection_decisions/txt").glob("*.txt"):
        dec[p.stem.split("_")[0]].append(p)
    out = {}
    for app in apps:
        paths = [sdkb / "data/sources/opinion_notices/txt" / f"{d['file']}.txt"
                 for d in idx.get(app, {}).get("docs", [])]
        paths = [p for p in paths if p.exists()] + dec.get(app, [])
        out[app] = [p.read_text(errors="ignore") for p in paths]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sdkb", type=Path, required=True, help="상류 SDKB 작업 트리")
    ap.add_argument("--repo", type=Path, default=Path("."))
    a = ap.parse_args()
    repo, sdkb = a.repo, a.sdkb

    split = pd.read_parquet(repo / "data/processed/ir/split.parquet")
    dev = sorted(split.loc[split.split == "dev", "doc_id"])
    apps = [d.replace("kr_", "") for d in dev]
    texts = sources(sdkb, apps)
    concepts = load_concepts(sdkb)
    corpus = pd.read_parquet(repo / "data/processed/ir/ir_corpus_v09.parquet").set_index("doc_id")
    qrel = pd.read_parquet(repo / "data/processed/ir/qrel_examiner.parquet")
    qd = qrel[qrel.query_id.isin(dev)]
    gold = qd.groupby("query_id").doc_id.apply(set)
    print(f"[범위] dev 질의 {len(dev)} · qrel 행 {len(qd)} · 고유 정답 {qd.doc_id.nunique()}")

    # --- O1 청구항 버전 ---
    rr = pd.read_csv(repo / "data/external/sdkb/rejection_reasons.csv")
    d = rr[rr.doc_id.isin(dev)]
    rounds = d.groupby("doc_id").notice_round.max()
    print("\n=== O1 청구항 버전 ===")
    print(f"대응 문서 {d.doc_id.nunique()} · 최대 라운드 분포 {dict(rounds.value_counts().sort_index())}")
    print(f"라운드 2 이상 {int((rounds >= 2).sum())}/{len(rounds)}")
    amend = sum(1 for app in apps if any("보정" in t for t in texts[app]))
    print(f"'보정' 언급 질의 {amend}/{len(dev)} · 코퍼스 청구항 버전은 문서당 1개")

    # --- O2 인용문헌 식별자 해소 ---
    print("\n=== O2 인용문헌 식별자 해소 ===")
    cover, hit, ncite = [], 0, []
    for app, q in zip(apps, dev):
        ids, n = set(), 0
        for t in texts[app]:
            for m in CITE_LINE.finditer(t):
                n += 1
                ids |= {digits(x.group(1)) for x in NUMS.finditer(m.group(2))}
        ncite.append(n)
        g = {digits(x) for x in gold.get(q, set())}
        if not g:
            continue
        inter = {x for x in g if any(x == i or x.endswith(i) or i.endswith(x) for i in ids)}
        cover.append(len(inter) / len(g))
        hit += int(bool(inter))
    c = pd.Series(cover)
    print(f"인용발명 정의줄 보유 {sum(1 for x in ncite if x)}/{len(dev)} · 문서당 중앙값 {pd.Series(ncite).median():.0f}")
    print(f"식별자가 정답과 겹치는 질의 {hit}/{len(c)} ({hit/len(c):.1%}) · 질의별 회수율 중앙값 {c.median():.1%} · 100 % {int((c == 1).sum())}")

    tbl = collections.Counter()
    for app in apps:
        blob = "\n".join(texts[app])
        for k, v in TABLE_CUES.items():
            tbl[k] += int(bool(re.search(v, blob)))
    print("표 형식 단서 보유 질의:", dict(tbl))

    # --- O3 개념 후보 수와 쌍 상한 ---
    print("\n=== O3 개념 후보 수 · 쌍 상한 ===")
    selfc = {q: concepts(corpus.loc[q, "claims_independent"]) for q in dev}
    ns = pd.Series({q: len(v) for q, v in selfc.items()})
    print(f"[본원] 독립항 개념 — 중앙값 {ns.median():.0f} · 평균 {ns.mean():.1f} · 0개 {int((ns == 0).sum())}")

    def cited_text(x):
        if x not in corpus.index:
            return ""
        r = corpus.loc[x]
        full = r.get("claims_full")
        return full if isinstance(full, str) and full else r["text_main"]

    kip = pd.read_parquet(sdkb / "data/sources/cited_enriched/kipris.parquet")
    kmap = {digits(r.cited_doc_id): r.claims for r in kip.itertuples() if isinstance(r.claims, str)}
    for label, resolve in (("코퍼스", lambda x: concepts(cited_text(x))),
                           ("kipris", lambda x: concepts(kmap.get(digits(x), "")))):
        pairs, per, qok, miss = set(), [], 0, collections.Counter()
        for q in dev:
            cs = set()
            for x in gold.get(q, set()):
                got = resolve(x)
                if not got:
                    miss[x.split("_")[0]] += 1
                cs |= got
            ps = {(s, t) for s in selfc[q] for t in cs}
            pairs |= ps
            per.append(len(ps))
            qok += int(bool(ps))
        p = pd.Series(per)
        print(f"[인용 원천 {label}] 쌍을 얻는 질의 {qok}/{len(dev)} ({qok/len(dev):.1%}) · "
              f"문서당 중앙값 {p.median():.0f} · 총 {p.sum():,} · 고유 {len(pairs):,} · 미해소 {dict(miss)}")

    # --- O4 유형 귀속과 confirmed 재료 ---
    print("\n=== O4 유형 단서 · confirmed 재료 ===")
    have = collections.Counter()
    for app in apps:
        blob = "\n".join(texts[app])
        for k, v in CUES.items():
            have[k] += int(bool(re.search(v, blob)))
    print("유형 단서 보유 질의:", dict(have))
    nt = d[d.notice_type == "의견제출통지서"].doc_id.nunique()
    nd = d[d.notice_type == "거절결정서"].doc_id.nunique()
    print(f"통지서 보유 {nt} · 결정서 보유 {nd} · 양쪽 {len(set(d[d.notice_type=='의견제출통지서'].doc_id) & set(d[d.notice_type=='거절결정서'].doc_id))}")


if __name__ == "__main__":
    main()
