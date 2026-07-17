"""`make ksia-strata` 의 진입점 — **소부장 층별 H1 정식 재검정** (RQ3 · 논문 §4.6 · 표 5b).

G₂ 는 소부장 세 층이다: 장비(equipment) · 재료(material) · 부분품(component). 전체 소부장에서
H1 이 지지돼도(표 5), 그 지지가 **어느 층 때문인지**는 층을 쪼개 봐야 안다. PLAN-014 §3.3 은
층별로 커버 공정이 다를 것을 사전등록했다(장비=식각·증착, 재료=CMP 슬러리 …).

**by-applicant(§4.5.2)와 같은 패턴이다.** 각 층의 특허만으로 델타를 다시 짓고 같은 G₀ 에
병합해(같은 L1 게이트) H1 을 따로 검정한다. **검정 방법·임계값·개념 정의·표본 단위·관측창은
불변** — 바뀌는 것은 company_type 필터 하나뿐이다. 층별로 기각될 수 있다(특히 표본이 작은 층).
**기각되면 기각된 대로 §4.6 에 쓴다** (사전등록 · CLAUDE.md §1.2).

G₀ 는 세 팔의 공통 before 다 — 층별로 쪼개지 않는다(동결 규칙). 이 검정이 답하는 질문은
"이 층만의 G₀ 대비"가 아니라 **"같은 G₀ 에 이 층의 특허만 더해도 커버리지가 늘어나는가"** 다.
"""
from __future__ import annotations

import pandas as pd

from sdkb_paper.analysis.coverage import compare_coverage, wilcoxon_h1
from sdkb_paper.analysis.robustness_cli import SCOPES, _scopes
from sdkb_paper.config import GRAPH_V0, PROCESSED, TABLES
from sdkb_paper.ontology.delta import ACTIVITY_KSIA, _org_ksia, build_delta
from sdkb_paper.ontology.merge import merge_with_gate
from sdkb_paper.preprocess.clean import load_ksia_crosswalk
from sdkb_paper.preprocess.profile import KSIA_DELTA

REPORT = PROCESSED / "h1_strata_ksia.md"
TABLE = TABLES / "h1_ksia_strata.md"

# 층 라벨(company_type) → 표시명. 순서는 규모 큰 순(장비·재료·부분품)으로 고정한다.
STRATA = [("equipment", "장비"), ("material", "재료"), ("component", "부분품")]


def slug_to_type() -> dict[str, str]:
    cw = load_ksia_crosswalk()
    return dict(zip(cw["org_slug"], cw["company_type"]))


def h1_by_stratum(delta: pd.DataFrame, ctype: str) -> dict:
    """그 층의 특허만으로 델타를 다시 지어 G₀ 에 병합하고 H1 을 검정한다.

    커버리지는 realizesProcess 링크에만 의존하므로 청구항 상세(details)는 넣지 않는다 —
    층 그래프는 H1 을 위한 커버리지 전용 부분집합이다. 같은 L1 게이트를 통과한다.
    """
    sub = delta[delta["company_type"] == ctype]

    delta_ttl = PROCESSED / f"delta_v2_{ctype}.ttl"
    graph_ttl = PROCESSED / f"graph_v2_{ctype}.ttl"

    build_delta(sub, org_of=_org_ksia, activity=ACTIVITY_KSIA,
                activity_label=f"KIPRIS KSIA {ctype} ingest (RQ3 · PLAN-014 C-2 · stratum)"
                ).serialize(delta_ttl, format="turtle")
    merge_with_gate(GRAPH_V0, delta_ttl, graph_ttl)  # 층 그래프도 같은 게이트를 통과한다

    df = compare_coverage(GRAPH_V0, graph_ttl)
    return {
        "n_firms": sub["matched_slug"].nunique(),
        "n_delta": sub["application_number"].nunique(),
        "covered": int((df["after"] > 0).sum()),
        "n_steps": len(df),
        "tests": {s: wilcoxon_h1(x, s) for s, x in _scopes(df).items()},
    }


def _rows(res: dict[str, dict]) -> list[str]:
    out = []
    for scope in SCOPES:
        cells = []
        for _, disp in STRATA:
            t = res[disp]["tests"][scope]
            p = "—" if t.p_value is None else f"{t.p_value:.2e}"
            cells.append(f"{t.n_positive} / {t.n} | {t.median_delta_positive:.1f} | {p} | "
                         f"{'지지' if t.rejects_null else '**기각 못 함**'}")
        out.append(f"| {scope} | " + " | ".join(cells) + " |")
    return out


def main() -> int:
    delta = pd.read_parquet(KSIA_DELTA)
    delta["company_type"] = delta["matched_slug"].map(slug_to_type())
    unmapped = int(delta["company_type"].isna().sum())
    if unmapped:
        # 크로스워크에 없는 slug 가 델타에 있으면 층 배정이 안 된다 — 조용히 버리지 않고 드러낸다.
        print(f"⚠ company_type 미배정 델타 행 {unmapped} (크로스워크 밖 slug) — 층별에서 제외")
        delta = delta.dropna(subset=["company_type"])

    res = {disp: h1_by_stratum(delta, ctype) for ctype, disp in STRATA}

    hdr = " | ".join(f"{d} 증가 단계 | 증가폭 중앙값 | p | 판정" for _, d in STRATA)
    align = " | ".join(["---:", "---:", "---:", "---"] * len(STRATA))

    lines = [
        "# RQ3 소부장 **층별** H1 — 장비 / 재료 / 부분품 (Wilcoxon 단측 · 동점 제외 · §4.6)",
        "",
        "전체 소부장 H1(표 5)의 지지가 어느 층에서 오는지 본다. 각 층의 특허만으로 델타를 다시",
        "짓고 같은 G₀ 에 병합해(같은 L1 게이트) H1 을 따로 검정했다. **검정 방법·임계값·개념 정의·",
        "표본 단위·관측창은 불변**이며, 바뀌는 것은 company_type 필터 하나뿐이다 (PLAN-014 §3.3 사전등록).",
        "",
        "> **G₀ 는 세 팔의 공통 before 다.** 층별로 쪼개지 않는다 — 쪼개면 baseline 이 움직여 H1 이",
        "> 재현되지 않는다. 답하는 질문은 **\"같은 G₀ 에 이 층의 특허만 더해도 커버리지가 늘어나는가\"** 다.",
        "",
        "## 규모 (층별)",
        "",
        "| 층 | 회사 | 델타(2010–25) | 커버된 공정 |",
        "|---|---:|---:|---:|",
        *(f"| {d} | {res[d]['n_firms']} | {res[d]['n_delta']:,} | {res[d]['covered']} / {res[d]['n_steps']} |"
          for _, d in STRATA),
        "",
        "## H1 — 공정 단계별 커버리지 증가",
        "",
        f"| 표본 집합 | {hdr} |",
        f"|---| {align} |",
        *_rows(res),
        "",
        "출처: `make ksia-strata` · 입력 graph_v0.ttl · graph_v2_{equipment,material,component}.ttl (L1 게이트 통과)",
        "",
    ]
    text = "\n".join(lines)

    TABLES.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text, encoding="utf-8")
    TABLE.write_text(text, encoding="utf-8")
    print(text)
    print(f"✓ {REPORT}\n✓ {TABLE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
