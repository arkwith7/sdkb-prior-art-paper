"""`make robustness` 의 진입점 — **패밀리 중복 제거 전후 비교** (논문 §4.5).

원고 §3.2·§4.5 는 DOCDB 패밀리 단위 중복 제거를 예고했으나 수행되지 않았다(중복 제거는
출원번호 기준뿐이었다). 여기서 실제로 수행하고 **전후를 나란히 싣는다**.

주 분석은 바뀌지 않는다 — 패밀리 dedup 은 **강건성 변이**다. 이유: G₀ 는 동결이라 패밀리
dedup 을 받을 수 없으므로, dedup 된 G₁ 을 dedup 안 된 G₀ 와 비교하면 주 분석이 비대칭해진다.
그래서 델타 쪽만 dedup 하고(G₀ 와 패밀리를 공유하는 델타 특허는 제거), 그 비대칭을 §4.5 에 적는다.

**검정 방법은 불변이다** — H1 은 Wilcoxon 단측·동점 제외, H2′ 는 단측 부호검정. θ·n_min·관측창·
개념 정의를 하나도 건드리지 않는다. 바뀌는 것은 입력 말뭉치 하나뿐이다 (CLAUDE.md §1.2).
"""
from __future__ import annotations

import pandas as pd

from sdkb_paper.analysis.coverage import compare_coverage, legacy_scope_iris, restrict, wilcoxon_h1
from sdkb_paper.analysis.h2_cli import run_h2prime, union_corpus
from sdkb_paper.collect.bq_family import FAMILY_MAP
from sdkb_paper.config import DATA, GRAPH_V0, PROCESSED, TABLES
from sdkb_paper.ontology.delta import build_delta
from sdkb_paper.ontology.merge import merge_with_gate
from sdkb_paper.preprocess.clean import g0_application_numbers
from sdkb_paper.preprocess.family import dedup_families
from sdkb_paper.preprocess.profile import DELTA as DELTA_PARQUET

DELTA_TTL_FD = PROCESSED / "delta_v1_famdedup.ttl"
GRAPH_V1_FD = PROCESSED / "graph_v1_famdedup.ttl"
REPORT = PROCESSED / "robustness_family.md"
PROFILE = DATA / "profiles" / "family_dedup.md"
TABLE = TABLES / "table9_family_dedup.md"

SCOPES = ("expanded49", "legacy20", "process11", "subprocess38")


def _scopes(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    legacy = legacy_scope_iris()
    return {
        "expanded49": df,
        "legacy20": restrict(df, legacy),
        "process11": df.loc[["process"]],
        "subprocess38": df.loc[["subprocess"]],
    }


def h1_arm(fam: pd.DataFrame, g0: set[str]) -> dict:
    """패밀리 dedup 된 델타로 G₁ 을 다시 짓고 H1 을 재검정한다. G₀ 는 손대지 않는다."""
    delta = pd.read_parquet(DELTA_PARQUET)
    kept, dropped = dedup_families(delta, fam, g0_apps=g0)

    g = build_delta(kept)
    g.serialize(DELTA_TTL_FD, format="turtle")
    merge_with_gate(GRAPH_V0, DELTA_TTL_FD, GRAPH_V1_FD)  # 강건성 그래프도 같은 게이트를 통과한다

    before = compare_coverage(GRAPH_V0, PROCESSED / "graph_v1.ttl")
    after = compare_coverage(GRAPH_V0, GRAPH_V1_FD)
    return {
        "delta_before": len(delta),
        "delta_after": len(kept),
        "dropped": dropped["drop_reason"].value_counts().to_dict(),
        "base": {s: wilcoxon_h1(sub, s) for s, sub in _scopes(before).items()},
        "dedup": {s: wilcoxon_h1(sub, s) for s, sub in _scopes(after).items()},
        "covered_base": int((before["after"] > 0).sum()),
        "covered_dedup": int((after["after"] > 0).sum()),
        "n_steps": len(before),
    }


def h2_arm(fam: pd.DataFrame, g0: set[str]) -> dict:
    """패밀리 dedup 된 유니온 말뭉치로 H2′ 를 재검정한다. 신호 규칙은 불변."""
    union = union_corpus()
    kept, dropped = dedup_families(union, fam, g0_apps=g0)
    return {
        "union_before": len(union),
        "union_after": len(kept),
        "dropped": dropped["drop_reason"].value_counts().to_dict(),
        "base": run_h2prime(union)["matrix"],
        "dedup": run_h2prime(kept.sort_values("application_number"))["matrix"],
    }


def _h1_rows(h1: dict) -> list[str]:
    out = []
    for s in SCOPES:
        b, d = h1["base"][s], h1["dedup"][s]
        bp = "—" if b.p_value is None else f"{b.p_value:.2e}"
        dp = "—" if d.p_value is None else f"{d.p_value:.2e}"
        flip = "" if b.rejects_null == d.rejects_null else " ⚠️ **판정 변동**"
        out.append(
            f"| {s} | {b.n_positive} / {b.n} | {d.n_positive} / {d.n} | "
            f"{b.median_delta_positive:.1f} | {d.median_delta_positive:.1f} | "
            f"{bp} | {dp} | {'지지' if d.rejects_null else '기각 못 함'}{flip} |"
        )
    return out


def _h2_rows(h2: dict) -> list[str]:
    key = ["window", "definition"]
    b = h2["base"].set_index(key)
    d = h2["dedup"].set_index(key)
    out = []
    for idx in b.index:
        rb, rd = b.loc[idx], d.loc[idx]
        flip = "" if rb["rejects"] == rd["rejects"] else " ⚠️ **판정 변동**"
        swing = "" if (rb["concept_first"], rb["name_first"]) == (
            rd["concept_first"], rd["name_first"]
        ) else " ⚠️ **승패 변동**"
        out.append(
            f"| {idx[0]} | {idx[1]} | {rb['concept_first']}승 {rb['name_first']}패 (n={rb['n_pairs']}) | "
            f"{rd['concept_first']}승 {rd['name_first']}패 (n={rd['n_pairs']}) | "
            f"{rb['p']:.4f} | {rd['p']:.4f} |{flip}{swing} |"
        )
    return out


def _profile(fam: pd.DataFrame, h1: dict, h2: dict, n_apps: int) -> str:
    per_app = fam.groupby("application_number")["family_id"].nunique()
    sizes = fam.groupby("family_id")["application_number"].nunique()
    return "\n".join([
        "# 데이터 프로파일 · DOCDB 패밀리 맵 (family_map)",
        "",
        "출처: BigQuery `patents-public-data.patents.publications` · `make family`",
        "생성: `sdkb_paper.collect.bq_family` (커밋하지 않는다 — raw)",
        "",
        "## 1. 구조",
        "",
        "| 컬럼 | dtype | 의미 | 원천 |",
        "|---|---|---|---|",
        "| `application_number` | str(13) | KIPRIS 출원번호 (키) | `KR-<11자리>-A` 에 `10` 을 붙여 복원 |",
        "| `family_id` | str | DOCDB simple family ID. `-1` 은 미상 | `publications.family_id` |",
        "",
        "## 2. 형태",
        "",
        f"- 행 {len(fam):,} · 고유 출원 {fam['application_number'].nunique():,} "
        f"/ 질의 {n_apps:,} (**조인율 {fam['application_number'].nunique() / n_apps:.1%}**)",
        f"- 미조인 {n_apps - fam['application_number'].nunique():,}건 · `family_id = -1` "
        f"{int((fam['family_id'] == '-1').sum()):,}건 → **dedup 하지 않는다**(동결 규칙 1)",
        f"- **한 출원에 family_id 가 여럿**: {int((per_app > 1).sum()):,}건 "
        f"({(per_app > 1).mean():.2%}) · 최대 {int(per_app.max())}개",
        "  → id 하나로 그룹핑하면 같은 발명이 두 패밀리로 쪼개진다. 공유 id 의 **연결성분**으로 묶는다(규칙 2).",
        "",
        "## 3. 기술통계",
        "",
        f"- 고유 family_id {fam['family_id'].nunique():,}",
        f"- **패밀리당 말뭉치 출원 수: 평균 {sizes.mean():.3f} · 중앙 {sizes.median():.0f} "
        f"· 최대 {int(sizes.max())}**",
        f"- 출원이 2건 이상인 패밀리: {int((sizes > 1).sum()):,} ({(sizes > 1).mean():.2%})",
        "",
        "> **이 한 줄이 §4.5 의 결과를 설명한다.** 패밀리당 평균 출원이 1.0 이다 — 우리는 **KR 단일",
        "> 관할**만 수집했으므로 대부분의 특허가 자기 패밀리의 유일한 KR 구성원이다. 패밀리 중복은",
        "> 여러 관할을 합칠 때 커지는 문제이고, 이 말뭉치에는 애초에 크게 존재하지 않는다.",
        "",
        "## 4. 사용 목적",
        "",
        f"- **논문 §4.5 (표 7) 강건성** — 패밀리 dedup 전후 H1·H2′ 비교. 델타 {h1['delta_before']:,} → "
        f"{h1['delta_after']:,} · H2′ 유니온 {h2['union_before']:,} → {h2['union_after']:,}",
        "- 주 분석(표 5·6·그림 3·4)에는 **쓰지 않는다** — G₀ 가 동결이라 dedup 을 받을 수 없어",
        "  주 분석으로 삼으면 before/after 가 비대칭해진다.",
        "- `family_id` 외 컬럼은 받지 않았다(publication_number·filing_date 등) — 쓰지 않을 컬럼을",
        "  남기지 않는다.",
        "",
    ])


def main() -> int:
    if not FAMILY_MAP.exists():
        print(f"❌ {FAMILY_MAP} 가 없다. `make family` 를 먼저 돌린다.")
        return 1

    fam = pd.read_parquet(FAMILY_MAP)
    g0 = g0_application_numbers()

    h1 = h1_arm(fam, g0)
    h2 = h2_arm(fam, g0)

    from sdkb_paper.collect.bq_family import corpus_application_numbers

    n_apps = len(corpus_application_numbers())

    lines = [
        "# 표 7 · §4.5 강건성 — 패밀리(DOCDB) 중복 제거 전후",
        "",
        "현행 중복 제거는 **출원번호 기준**이다. 같은 발명의 국내 분할·계속출원은 서로 다른 출원번호를",
        "받으므로 남는다. DOCDB `family_id` 로 묶어 **가장 이른 출원만** 남기고 재검정한다.",
        "**검정 방법·임계값·개념 정의는 하나도 바꾸지 않았다** — 입력 말뭉치만 바뀐다.",
        "",
        "## 규모",
        "",
        f"- BigQuery 조인율 **{fam['application_number'].nunique() / n_apps:.1%}** "
        f"({fam['application_number'].nunique():,}/{n_apps:,})",
        f"- 델타(G₁ 원천): {h1['delta_before']:,} → **{h1['delta_after']:,}** "
        f"(−{h1['delta_before'] - h1['delta_after']:,} · "
        f"{(h1['delta_before'] - h1['delta_after']) / h1['delta_before']:.2%}) {h1['dropped']}",
        f"- H2′ 유니온 말뭉치: {h2['union_before']:,} → **{h2['union_after']:,}** "
        f"(−{h2['union_before'] - h2['union_after']:,} · "
        f"{(h2['union_before'] - h2['union_after']) / h2['union_before']:.2%}) {h2['dropped']}",
        f"- 커버된 공정: G₁ {h1['covered_base']} → dedup 후 **{h1['covered_dedup']}** / {h1['n_steps']}",
        "",
        "`family_dup` = 같은 패밀리의 늦은 출원 · `g0_family` = G₀ 특허와 같은 패밀리인 델타 특허",
        "(G₀ 는 동결이므로 델타 쪽을 뺀다 — H1 의 before 는 한 트리플도 움직이지 않는다).",
        "",
        "## H1 — 공정 단계별 커버리지 (Wilcoxon 단측 · 동점 제외)",
        "",
        "| 표본 집합 | 증가 단계 (전) | 증가 단계 (후) | 증가폭 중앙값 (전) | (후) | p (전) | p (후) | 판정 (후) |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
        *_h1_rows(h1),
        "",
        "## H2′ — 개념 vs 명칭 조기탐지 (단측 부호검정)",
        "",
        "| 관측창 | 정의 | 전 | 후 | p (전) | p (후) | |",
        "|---|---|---|---|---:|---:|---|",
        *_h2_rows(h2),
        "",
        "출처: `make family` → `make robustness` · 입력 `family_map.parquet` · "
        "graph_v1_famdedup.ttl(L1 게이트 통과)",
        "",
    ]
    text = "\n".join(lines)

    TABLES.mkdir(parents=True, exist_ok=True)
    PROFILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text, encoding="utf-8")
    TABLE.write_text(text, encoding="utf-8")
    PROFILE.write_text(_profile(fam, h1, h2, n_apps), encoding="utf-8")

    print(text)
    print(f"✓ {REPORT}\n✓ {TABLE}\n✓ {PROFILE}\n✓ {GRAPH_V1_FD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
