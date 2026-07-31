"""`make by-applicant` 의 진입점 — **출원인별 분리 재검정** (S1 구 H1 강건성 · §4.5.2).
v0.9: C1 2차 재사용 증거. RECONCILIATION-v09.md §1.

G₁ 은 두 출원인이다(삼성전자 · SK하이닉스). 보강 효과가 **한 회사 때문에** 나온 것이라면
"전 공정 보강"이라는 주장이 약해진다. 그래서 각 회사의 특허만으로 델타를 다시 짓고 H1·H2′ 를
따로 검정한다.

**G₀ 는 두 팔의 공통 before 다 — 출원인별로 쪼개지 않는다** (동결 규칙 1). G₀ 는 351개 출원인의
코퍼스이고 동결 대상이다. 쪼개면 baseline 이 움직여 H1 이 재현되지 않는다. 따라서 이 검정이
답하는 질문은 "삼성만의 G₀ 대비"가 아니라 **"같은 G₀ 에 각 회사의 특허만 더해도 커버리지가
늘어나는가"** 다. 그 해석상의 제약을 §4.5 에 함께 적는다.

**검정 방법·임계값·개념 정의·관측창은 불변이다** — 바뀌는 것은 출원인 필터 하나뿐이다.
H2′ 는 이미 유효쌍 4(최소 p=0.0625)라 α=0.05 에 도달할 수 없고, 분리하면 탐지 실패로 쌍이 더
깎일 수 있다. **유의성을 주장하지 않고 승패만 서술한다** — 결과를 보기 전에 선언했다.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from rdflib import Graph

from sdkb_paper.analysis.s1_coverage import compare_coverage, wilcoxon_h1
from sdkb_paper.analysis.s2_timeseries_cli import run_h2prime, union_corpus
from sdkb_paper.analysis.robustness_cli import SCOPES, _scopes
# S-시리즈(구 패러다임) 산출물이다 — 출력은 paper/archive/regenerated/ 로 격리된다.
# v0.9 정본 표·그림(paper/{tables,figures})과 섞지 않는다 (config.ARCHIVE_* 주석 참조).
from sdkb_paper.config import ARCHIVE_TABLES as TABLES
from sdkb_paper.config import GRAPH_V0, ONT, PROCESSED
from sdkb_paper.ontology.delta import build_delta
from sdkb_paper.ontology.merge import merge_with_gate
from sdkb_paper.preprocess.clean import TARGET_APPLICANTS
from sdkb_paper.preprocess.profile import DELTA as DELTA_PARQUET

REPORT = PROCESSED / "robustness_applicant.md"
TABLE = TABLES / "robustness_by_applicant.md"

SHORT = {"삼성전자주식회사": "samsung", "에스케이하이닉스 주식회사": "hynix"}


def h1_by_applicant(applicant: str) -> dict:
    """그 회사의 특허만으로 델타를 다시 지어 G₀ 에 병합하고 H1 을 검정한다."""
    delta = pd.read_parquet(DELTA_PARQUET)
    sub = delta[delta["applicant_name"] == applicant]

    tag = SHORT[applicant]
    delta_ttl = PROCESSED / f"delta_v1_{tag}.ttl"
    graph_ttl = PROCESSED / f"graph_v1_{tag}.ttl"

    build_delta(sub).serialize(delta_ttl, format="turtle")
    merge_with_gate(GRAPH_V0, delta_ttl, graph_ttl)  # 강건성 그래프도 같은 게이트를 통과한다

    df = compare_coverage(GRAPH_V0, graph_ttl)
    return {
        "n_delta": len(sub),
        "n_process_linked": _process_linked_delta(graph_ttl),
        "covered": int((df["after"] > 0).sum()),
        "n_steps": len(df),
        "tests": {s: wilcoxon_h1(x, s) for s, x in _scopes(df).items()},
    }


def _process_linked_delta(graph_ttl: Path) -> int:
    """이 회사의 델타 중 공정에 실제로 연결된 고유 특허 수 (G₀ 기존분 제외).

    증가폭의 비대칭(삼성 185 vs SK 31)이 어디서 오는지는 델타 건수가 아니라 이 수가 말한다 —
    델타가 커도 공정 링크가 없으면 커버리지는 움직이지 않는다. 논문 §6.5.2.
    """
    def linked(path: Path) -> set:
        g = Graph()
        g.parse(path, format="turtle")
        return {s for s, _, _ in g.triples((None, ONT["realizesProcess"], None))}

    return len(linked(graph_ttl) - linked(GRAPH_V0))


def h2_by_applicant(applicant: str, union: pd.DataFrame) -> dict:
    sub = union[union["applicant_name"] == applicant]
    return run_h2prime(sub.sort_values("application_number"))


def _case_rows(res: dict[str, dict], both: dict) -> list[str]:
    """교정 창 · 구조 전용 셀의 **사례별** 결과. 분리가 사례를 소실시키는지 보려면 이것이 필요하다."""
    cell = ("extended", "si_struct")
    lf = {k: v["leads"][cell].set_index("case_id") for k, v in res.items()}
    b = both["leads"][cell].set_index("case_id")
    out = []
    for case in b.index:
        cells = [f"{b.loc[case, 'outcome']} ({int(b.loc[case, 'concept_total'])}건)"]
        for v in lf.values():
            r = v.loc[case]
            cells.append(f"{r['outcome']} ({int(r['concept_total'])}건)")
        out.append(f"| {case} | " + " | ".join(cells) + " |")
    return out


def _h1_rows(res: dict[str, dict]) -> list[str]:
    out = []
    for scope in SCOPES:
        cells = []
        for r in res.values():
            t = r["tests"][scope]
            p = "—" if t.p_value is None else f"{t.p_value:.2e}"
            cells.append(
                f"{t.n_positive} / {t.n} | {t.median_delta_positive:.1f} | {p} | "
                f"{'지지' if t.rejects_null else '**기각 못 함**'}"
            )
        out.append(f"| {scope} | " + " | ".join(cells) + " |")
    return out


def _h2_rows(res: dict[str, dict], both: pd.DataFrame) -> list[str]:
    key = ["window", "definition"]
    b = both.set_index(key)
    m = {k: v["matrix"].set_index(key) for k, v in res.items()}
    out = []
    for idx in b.index:
        r = b.loc[idx]
        cells = [f"{r['concept_first']}승 {r['name_first']}패 (n={r['n_pairs']})"]
        for v in m.values():
            x = v.loc[idx]
            cells.append(f"{x['concept_first']}승 {x['name_first']}패 (n={x['n_pairs']})")
        out.append(f"| {idx[0]} | {idx[1]} | " + " | ".join(cells) + " |")
    return out


def main() -> int:
    union = union_corpus()

    h1 = {a: h1_by_applicant(a) for a in TARGET_APPLICANTS}
    h2 = {a: h2_by_applicant(a, union) for a in TARGET_APPLICANTS}
    both = run_h2prime(union)

    # 합산 G₁ 커버리지는 하드코딩하지 않고 그래프에서 잰다(값이 낡는 것을 막는다).
    df_all = compare_coverage(GRAPH_V0, PROCESSED / "graph_v1.ttl")
    combined_cov, combined_n = int((df_all["after"] > 0).sum()), len(df_all)

    names = list(TARGET_APPLICANTS)
    hdr = " | ".join(f"{n} 증가 단계 | 증가폭 중앙값 | p | 판정" for n in names)
    align = " | ".join(["---:", "---:", "---:", "---"] * len(names))

    lines = [
        "# 강건성 — 출원인별 분리 재검정 (삼성전자 / SK하이닉스 · §4.5.2)",
        "",
        "보강 효과가 **한 회사 때문에** 나온 것인지 확인한다. 각 회사의 특허만으로 델타를 다시 짓고",
        "같은 G₀ 에 병합해 H1·H2′ 를 따로 검정했다. **검정 방법·임계값·개념 정의·관측창은 불변**이며,",
        "바뀌는 것은 출원인 필터 하나뿐이다.",
        "",
        "> **G₀ 는 두 팔의 공통 before 다.** G₀(351개 출원인)를 출원인별로 쪼개지 않는다 — 쪼개면",
        "> baseline 이 움직여 H1 이 재현되지 않는다. 따라서 이 검정이 답하는 질문은 \"삼성만의 G₀",
        "> 대비\"가 아니라 **\"같은 G₀ 에 각 회사의 특허만 더해도 커버리지가 늘어나는가\"** 다.",
        "",
        "## 규모",
        "",
        "| 출원인 | 델타(2010–25) | 공정 링크 특허 | 커버된 공정 |",
        "|---|---:|---:|---:|",
        *(
            f"| {a} | {h1[a]['n_delta']:,} | {h1[a]['n_process_linked']:,} "
            f"| {h1[a]['covered']} / {h1[a]['n_steps']} |"
            for a in names
        ),
        "",
        f"(참고: 두 회사 합산 G₁ 의 커버된 공정은 {combined_cov} / {combined_n} 다.)",
        "",
        "## H1 — 공정 단계별 커버리지 (Wilcoxon 단측 · 동점 제외)",
        "",
        f"| 표본 집합 | {hdr} |",
        f"|---| {align} |",
        *_h1_rows(h1),
        "",
        "## H2′ — 개념 vs 명칭 조기탐지 (단측 부호검정)",
        "",
        "> **유의성을 주장하지 않는다.** 합산에서도 유효쌍이 4(최소 p=0.0625)라 α=0.05 에 도달할 수",
        "> 없고, 분리하면 탐지 실패로 쌍이 더 깎인다. **승패만 서술한다** — 결과를 보기 전에 선언했다.",
        "",
        "| 관측창 | 정의 | 합산(G₁) | " + " | ".join(names) + " |",
        "|---|---|---|" + "---|" * len(names),
        *_h2_rows(h2, both["matrix"]),
        "",
        "### 사례별 — 교정 창 · 구조 전용 정의 (괄호 안은 개념 시계열의 특허 수)",
        "",
        "| 사례 | 합산(G₁) | " + " | ".join(names) + " |",
        "|---|---|" + "---|" * len(names),
        *_case_rows(h2, both),
        "",
        "> **분리는 신호를 소실시킨다 — 이것이 이 표의 가장 중요한 관측이다.** 탐지 규칙이 상대 성장",
        "> (θ × 직전 3년 평균 · 최소 건수)이라 **말뭉치를 쪼개면 임계에 못 미쳐 사례가 통째로 사라진다.**",
        "> HBM 이 그 예다: 합산에서는 2009년에 탐지되지만, 삼성 단독(구조 개념 20건)에서는 미탐지가",
        "> 되어 명칭(2020년)에 지고, 하이닉스 단독(9건)에서는 양쪽 다 미탐지다. HBM 은 두 회사가",
        "> **함께** 만든 기술이고(하이닉스 개발 · 삼성 후속), 어느 한 쪽만 보면 신호가 서지 않는다.",
        ">",
        "> 따라서 **H2′ 의 출원인별 분리는 강건성 점검으로서 정보가 제한적이다.** 유효쌍이 1–2 로",
        "> 떨어지는 것은 개념 단위 시계열이 약해서가 아니라 **표본이 부족해서**다. H1 과 달리 H2′ 는",
        "> 이 분리로 결론을 강화하지도 약화시키지도 못한다 — 그 사실을 그대로 보고한다.",
        "",
        "출처: `make by-applicant` · 입력 graph_v1_samsung.ttl · graph_v1_hynix.ttl (L1 게이트 통과)",
        "",
    ]
    text = "\n".join(lines)

    TABLES.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text, encoding="utf-8")
    TABLE.write_text(text, encoding="utf-8")
    print(text)
    print(f"✓ {REPORT}\n✓ {TABLE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
