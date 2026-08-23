"""PLAN-074 Phase 0′ 계수 — 판단 단위(문단)에서 성립하는 개념 쌍을 센다.

**사전등록이 아니라 동결된 설계의 실행**이다(PLAN-074 §12 · 승인 커밋으로 규칙이 박혔다).
문턱 여섯은 §4.2 에서, 판정식은 §12.6 에서 결과를 보기 전에 동결됐다.

§0.1 과의 관계. 원천(의견제출통지서·거절결정서)과 개념 사전은 상류에만 있으므로 상류 경로를
인자로 받는다. `src/` 를 건드리지 않고 어떤 make 표적에도 걸리지 않는다.

§1-4 · §5 와의 관계. 범위는 dev 200질의뿐이며 test·test_b 는 인자로도 받지 않는다.
**정답(qrel)을 열지 않는다**(D2) — 그래서 이 계수기는 회수율·순위를 산출할 수 없다.
리포트에는 출원번호·`reason_id` 를 남기지 않고 개념 식별자만 싣는다(§5-3).

사용
  uv run python scripts/plan074_phase0prime_census.py --sdkb ~/Dev/sdkb
"""
from __future__ import annotations

import argparse
import collections
import json
import random
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

#: 거절이유 유형 단서 (PLAN-074 §12.2 조건 1 · §10.1 O4 와 같은 정규식).
CUES = {
    "결합": r"결합|조합",
    "설계변경": r"설계변경|설계 변경|단순한 설계|설계적 사항",
    "임계적 의의": r"임계적|수치한정|수치 한정",
    "치환": r"치환|균등물",
    "주지관용": r"주지관용|주지 관용|주지기술|관용수단",
}
#: 인용발명 정의줄 — "인용발명 1 : 공개특허공보 제10-2012-0075051호(2012.07.06.)".
CITE_DEF = re.compile(r"인용발명\s*(\d+)\s*[:：]\s*([^\n]{5,120})")
#: 문단 안의 인용발명 지시 (§12.2 조건 2).
CITE_REF = re.compile(r"인용발명\s*(\d+)")
#: 문단 안의 청구항 지시 (§12.2 조건 3). 범위 표현이면 **첫 번호만** 쓴다 — 결정적이고 보수적이다.
CLAIM_REF = re.compile(r"청구항\s*(?:제)?\s*(\d+)")
NUMS = re.compile(
    r"(?:특개|특표|공개특허|등록특허|공보)?\s*(?:제)?\s*"
    r"([0-9]{2,4}[\-–][0-9]{4}[\-–][0-9]{7}|[0-9]{4}[\-–][0-9]{6}|[0-9]{2}[\-–][0-9]{7}|[0-9]{7,13})"
)
#: 문단 분할 — 번호 매김 항목 또는 빈 줄 (§12.2).
PARA_SPLIT = re.compile(r"\n(?=\s*\d+\.\s)|\n{2,}")
MIN_PARA_CHARS = 40
SEED = 20260823
SAMPLE_N = 100


def digits(s: str) -> str:
    return re.sub(r"\D", "", str(s))


@dataclass(frozen=True)
class Unit:
    """판단 단위 — (원천 문서, 문단, 유형)."""

    app: str
    kind: str  # 통지서 · 결정서
    para: int
    typ: str
    claim_no: int
    cited: tuple[str, ...]  # 해소된 인용문헌 doc_id
    text: str


def paragraphs(text: str) -> list[str]:
    return [p.strip() for p in PARA_SPLIT.split(text) if len(p.strip()) >= MIN_PARA_CHARS]


def load_concept_matcher(sdkb: Path):
    entries = json.loads((sdkb / "mappings/concept_mapping.json").read_text())
    entries = entries["profiles"]["patent-text"]["entries"]
    s2c = {e["surface"].lower(): (e.get("concept") or e.get("concept_id")) for e in entries}
    pat = re.compile("|".join(re.escape(s) for s in sorted(s2c, key=len, reverse=True)), re.I)

    def concepts(t: str | None) -> set[str]:
        return {s2c[m.group(0).lower()] for m in pat.finditer(t or "")}

    return concepts


def read_sources(sdkb: Path, apps: list[str]) -> dict[str, list[tuple[str, str]]]:
    """출원번호 → [(원천 종류, 원문)] · 통지서를 먼저 둔다(정의줄 상속 순서)."""
    idx = json.loads((sdkb / "data/sources/opinion_notices/_index.json").read_text())
    dec: dict[str, list[Path]] = collections.defaultdict(list)
    for p in (sdkb / "data/sources/rejection_decisions/txt").glob("*.txt"):
        dec[p.stem.split("_")[0]].append(p)
    out: dict[str, list[tuple[str, str]]] = {}
    for app in apps:
        rows: list[tuple[str, str]] = []
        for d in idx.get(app, {}).get("docs", []):
            p = sdkb / "data/sources/opinion_notices/txt" / f"{d['file']}.txt"
            if p.exists():
                rows.append(("통지서", p.read_text(errors="ignore")))
        for p in sorted(dec.get(app, [])):
            rows.append(("결정서", p.read_text(errors="ignore")))
        out[app] = rows
    return out


def cite_map(texts: list[tuple[str, str]]) -> dict[int, str]:
    """인용발명 번호 → 식별자 숫자열. 출원 단위로 병합한다(결정서는 재정의하지 않는 일이 잦다)."""
    m: dict[int, str] = {}
    for _, t in texts:
        for hit in CITE_DEF.finditer(t):
            nums = [digits(x.group(1)) for x in NUMS.finditer(hit.group(2))]
            if nums:
                m.setdefault(int(hit.group(1)), nums[0])
    return m


def claim_lines(claims_full: str | None) -> list[str]:
    return [x.strip() for x in (claims_full or "").split("\n") if x.strip()]


def build_units(apps, dev, sources, corpus, doc_by_digits) -> tuple[list[Unit], collections.Counter]:
    stat: collections.Counter = collections.Counter()
    units: list[Unit] = []
    for app, q in zip(apps, dev):
        texts = sources[app]
        cmap = cite_map(texts)
        lines = claim_lines(corpus.at[q, "claims_full"]) if q in corpus.index else []
        for kind, t in texts:
            for i, para in enumerate(paragraphs(t)):
                types = [k for k, v in CUES.items() if re.search(v, para)]
                if not types:
                    continue
                stat["유형 문단"] += 1
                cref = [int(x.group(1)) for x in CITE_REF.finditer(para)]
                qref = CLAIM_REF.search(para)
                if not cref or not qref:
                    stat["지시 불충분"] += 1
                    continue
                stat["두 지시 보유"] += 1
                resolved = []
                for n in dict.fromkeys(cref):
                    d = cmap.get(n)
                    doc = doc_by_digits.get(d) if d else None
                    if doc:
                        resolved.append(doc)
                    else:
                        stat["인용문헌 미해소"] += 1
                if not resolved:
                    stat["단위 폐기: 인용문헌"] += 1
                    continue
                cno = int(qref.group(1))
                if not (1 <= cno <= len(lines)):
                    stat["단위 폐기: 청구항 번호"] += 1
                    continue
                for typ in types:
                    units.append(Unit(app, kind, i, typ, cno, tuple(dict.fromkeys(resolved)), para))
    return units, stat


def census(units, corpus, concepts, dev_by_app, claims_cache, fallback: bool = False):
    """쌍 생성 (§12.3).

    주 계수는 인용 측 `claims_full` 실물만 쓰고 폴백하지 않는다(D1). `fallback=True` 는 D1 이
    **부차로 병기하라**고 정한 `text_main` 폴백 계수이며 **문턱 판정에 쓰지 않는다.**
    """
    pairs_by_type: dict[str, set] = collections.defaultdict(set)
    raw = 0
    per_query: dict[str, set] = collections.defaultdict(set)
    by_kind: dict[str, set] = collections.defaultdict(set)
    unit_pairs: list[tuple[Unit, tuple[str, str, str]]] = []
    dropped = collections.Counter()
    for u in units:
        q = dev_by_app[u.app]
        lines = claims_cache[q]
        self_c = concepts(lines[u.claim_no - 1])
        if not self_c:
            dropped["본원 개념 0"] += 1
            continue
        cited_c: set[str] = set()
        for d in u.cited:
            txt = corpus.at[d, "claims_full"] if d in corpus.index else None
            if not (isinstance(txt, str) and txt.strip()):
                dropped["인용 청구항 실물 없음"] += 1
                txt = corpus.at[d, "text_main"] if (fallback and d in corpus.index) else None
            if isinstance(txt, str) and txt.strip():
                cited_c |= concepts(txt)
        if not cited_c:
            dropped["인용 개념 0"] += 1
            continue
        for a in self_c:
            for b in cited_c:
                p = (a, b, u.typ)
                pairs_by_type[u.typ].add(p)
                per_query[q].add(p)
                by_kind[u.kind].add(p)
                unit_pairs.append((u, p))
                raw += 1
    return pairs_by_type, raw, per_query, by_kind, unit_pairs, dropped


def sample_units(unit_pairs, rounds, n=SAMPLE_N, seed=SEED):
    """정밀도 표본 (§12.5) — 유형(결합/그 외) × 라운드(1/≥2) 네 칸 층화 · 시드 고정."""
    rng = random.Random(seed)
    cells: dict[tuple[str, str], list] = collections.defaultdict(list)
    for u, p in unit_pairs:
        cells[("결합" if u.typ == "결합" else "그 외",
               "r1" if rounds.get(u.app, 1) <= 1 else "r2+")].append((u, p))
    quota, out, short = n // 4, [], {}
    for key in sorted(cells):
        rows = sorted(cells[key], key=lambda x: (x[0].app, x[0].kind, x[0].para, x[1]))
        rng.shuffle(rows)
        take = rows[:quota]
        out += take
        if len(take) < quota:
            short[key] = quota - len(take)
    # 부족분은 남은 칸에서 보충한다 — 보충량은 리포트에 적는다(§12.5).
    if len(out) < n:
        rest = [x for k in sorted(cells) for x in cells[k] if x not in out]
        rng.shuffle(rest)
        out += rest[: n - len(out)]
    return out, short


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sdkb", type=Path, required=True, help="상류 SDKB 작업 트리")
    ap.add_argument("--repo", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path, default=Path("01.code_spec/reports/PLAN-074-phase0prime-census.md"))
    ap.add_argument("--sample-out", type=Path, default=Path("data/interim/plan074_precision_sample.tsv"),
                    help="정밀도 코딩 표본 — 원문을 담으므로 gitignore 경로에만 쓴다(§1-5)")
    a = ap.parse_args()
    repo, sdkb = a.repo, a.sdkb

    split = pd.read_parquet(repo / "data/processed/ir/split.parquet")
    dev = sorted(split.loc[split.split == "dev", "doc_id"])
    apps = [d.replace("kr_", "") for d in dev]
    dev_by_app = dict(zip(apps, dev))
    corpus = pd.read_parquet(repo / "data/processed/ir/ir_corpus_v09.parquet").set_index("doc_id")
    doc_by_digits: dict[str, str] = {}
    ambiguous = 0
    for d in corpus.index:
        k = digits(d)
        if k in doc_by_digits:
            ambiguous += 1
            continue
        doc_by_digits[k] = d
    concepts = load_concept_matcher(sdkb)
    sources = read_sources(sdkb, apps)
    rr = pd.read_csv(repo / "data/external/sdkb/rejection_reasons.csv")
    rounds = {d.replace("kr_", ""): int(r) for d, r in
              rr[rr.doc_id.isin(dev)].groupby("doc_id").notice_round.max().items()}

    units, stat = build_units(apps, dev, sources, corpus, doc_by_digits)
    claims_cache = {q: claim_lines(corpus.at[q, "claims_full"]) for q in dev}
    pairs_by_type, raw, per_query, by_kind, unit_pairs, dropped = census(
        units, corpus, concepts, dev_by_app, claims_cache)

    fb_by_type, fb_raw, fb_per_q, _, _, _ = census(
        units, corpus, concepts, dev_by_app, claims_cache, fallback=True)
    fb_uniq = len(set().union(*fb_by_type.values())) if fb_by_type else 0
    fb_cov = sum(1 for q in dev if fb_per_q[q]) / len(dev)

    all_pairs = set().union(*pairs_by_type.values()) if pairs_by_type else set()
    p_uniq = len(all_pairs)
    q_cov = sum(1 for q in dev if per_query[q]) / len(dev)
    c_conf = len(by_kind["통지서"] & by_kind["결정서"])
    verdict = ("통과" if (p_uniq >= 400 and q_cov >= 0.50) else
               "미달" if (p_uniq < 400 and q_cov < 0.50) else "부분")

    sample, short = sample_units(unit_pairs, rounds)
    a.sample_out.parent.mkdir(parents=True, exist_ok=True)
    with a.sample_out.open("w") as f:
        f.write("idx\t유형\t라운드\t본원개념\t인용개념\t문단\n")
        for i, (u, p) in enumerate(sample, 1):
            f.write(f"{i}\t{u.typ}\t{'r1' if rounds.get(u.app,1)<=1 else 'r2+'}\t"
                    f"{p[0]}\t{p[1]}\t{u.text[:400].replace(chr(9),' ')}\n")

    top = collections.Counter((p[0], p[1]) for _, p in unit_pairs).most_common(10)
    lines = [
        "# PLAN-074 Phase 0′ 계수 결과",
        "",
        "**PLAN-074 §12 의 동결 설계로 실행한 계수다.** 범위는 dev 200질의뿐이며 qrel 을 읽지 않는다(D2).",
        "개념 쌍은 개념 식별자로만 싣는다(§5-3).",
        "",
        "## 판정",
        "",
        f"- **P_uniq = {p_uniq}** (문턱 400) · **Q_cov = {q_cov:.1%}** (문턱 0.50) · "
        f"**C_conf = {c_conf}** (문턱 100)",
        f"- P_raw = {raw:,} · 판단 단위 {len(units):,}",
        f"- **부차(D1 폴백 · 판정 비사용)**: P_uniq = {fb_uniq:,} · Q_cov = {fb_cov:.1%} · "
        f"P_raw = {fb_raw:,}",
        f"- **판정(Prec 제외) = {verdict}** — `Prec` 은 사람 코딩 전이므로 미산출이며, "
        "§13 대로 그때까지 최종 판정은 *부분* 이다",
        "",
        "## 유형별",
        "",
        "| 유형 | P_uniq | 문턱 |",
        "|---|---|---|",
    ]
    for t in CUES:
        thr = {"결합": "250", "설계변경": "60"}.get(t, "—")
        lines.append(f"| {t} | {len(pairs_by_type.get(t, ())):,} | {thr} |")
    lines += [
        "",
        "## 단위 생성 계수",
        "",
        "| 항목 | 수 |",
        "|---|---|",
    ] + [f"| {k} | {v:,} |" for k, v in stat.items()] + [
        f"| 쌍 폐기 · {k} | {v:,} |" for k, v in dropped.items()
    ] + [
        f"| 식별자 중복으로 버린 코퍼스 행 | {ambiguous:,} |",
        "",
        "## 빈출 개념 쌍 상위 10",
        "",
        "| 본원 개념 | 인용 개념 | 단위 빈도 |",
        "|---|---|---|",
    ] + [f"| {a_} | {b_} | {n} |" for (a_, b_), n in top] + [
        "",
        f"정밀도 표본 {len(sample)}건은 `{a.sample_out}` 에 있다(원문을 담으므로 gitignore 경로다).",
        f"층 부족분 보충: {short or '없음'} · seed = {SEED}.",
    ]
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:20]))
    print(f"\n[리포트] {a.out}")


if __name__ == "__main__":
    main()
