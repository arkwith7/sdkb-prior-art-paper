"""H1 — 공정 단계별 개념 커버리지: 보강 전(G₀) vs 후(G₁).

관측 단위는 **공정 단계 s** 이지 특허가 아니다. SDKB 의 공정 계층 두 층위를 모두 센다:
  - process    (11개) ont:Process     — SemiKong Table 7 의 L1 그룹
  - subprocess (38개) ont:SubProcess  — L2 모듈 + SDKB 고유 유닛

C(s) = s 에 ont:realizesProcess 로 **직접** 연결된 고유 특허 수. 부모 공정으로 roll-up 하지
않는다 — 올리면 같은 특허가 두 층위에 이중 계상되어 표본이 부풀려진다.

H1 은 두 표본 집합으로 병기 보고된다 (PLAN-001 §3.5 · PLAN-005):
  - 확장 49      — 현재 어휘 전량
  - 복원 이전 20 — SemiKong Table 7 복원 전의 공정 (mappings/process_scope_legacy20.csv)
복원된 단계는 G₀ 에서 C₀(s)=0 이라 H1 에 구조적으로 유리하다. 그 편향을 독자가 직접
판별할 수 있어야 검정이 정직하다.

SDKB 는 rdfs:label 이 아니라 skos:prefLabel(en) / skos:altLabel(ko) 을 쓴다.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from rdflib import Graph
from scipy.stats import wilcoxon

from sdkb_paper.config import CODE_MAPPING, LEGACY_SCOPE

# 층위를 VALUES 로 명시 — RDFS 추론 없이 Process/SubProcess 를 각각 집계한다.
# (SubProcess ⊑ Process 라서 추론을 켜면 SubProcess 가 두 층위에 이중 계상된다.)
# OPTIONAL 이므로 특허 0건인 단계도 행으로 남는다 — 그 공백이 곧 H1 의 대상이다.
COVERAGE_SPARQL = """
PREFIX ont:  <https://w3id.org/sdkb/ont/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?level ?step ?stepLabel (COUNT(DISTINCT ?patent) AS ?n)
WHERE {
  VALUES (?stepType ?level) { (ont:Process "process") (ont:SubProcess "subprocess") }
  ?step a ?stepType ; skos:prefLabel ?stepLabel .
  OPTIONAL { ?patent a ont:Patent ; ont:realizesProcess ?step . }
}
GROUP BY ?level ?step ?stepLabel
"""


def coverage_by_process_step(graph_path: Path) -> pd.DataFrame:
    """(level, step) 별 고유 특허 수. 인덱스는 IRI — 레이블은 표시용 컬럼."""
    g = Graph().parse(graph_path)
    rows = [
        {"level": str(r.level), "step": str(r.step), "label": str(r.stepLabel), "patents": int(r.n)}
        for r in g.query(COVERAGE_SPARQL)
    ]
    return (
        pd.DataFrame(rows, columns=["level", "step", "label", "patents"])
        .set_index(["level", "step"])
        .sort_index()
    )


def compare_coverage(before: Path, after: Path) -> pd.DataFrame:
    """보강 전/후 커버리지 표. 컬럼 계약: label · before · after · delta (viz 가 의존한다)."""
    b, a = coverage_by_process_step(before), coverage_by_process_step(after)
    df = pd.DataFrame({
        "label": a["label"].combine_first(b["label"]),
        "before": b["patents"],
        "after": a["patents"],
    })
    df[["before", "after"]] = df[["before", "after"]].fillna(0).astype(int)
    df["delta"] = df["after"] - df["before"]
    return df.sort_values(["level", "delta"], ascending=[True, False])


def legacy_scope_iris(path: Path = LEGACY_SCOPE) -> set[str]:
    """복원 이전 공정 20개의 IRI. 손으로 고르지 않는다 — 커밋 스냅샷에서 동결된 목록이다."""
    return set(pd.read_csv(path)["iri"])


def restrict(df: pd.DataFrame, iris: set[str]) -> pd.DataFrame:
    """표본 집합을 IRI 목록으로 제한한다 (인덱스 level 2 = step IRI)."""
    return df[df.index.get_level_values("step").isin(iris)]


def residual_gap_report(
    df: pd.DataFrame, other: pd.DataFrame | None = None, other_label: str = "G₂"
) -> pd.DataFrame:
    """보강 후에도 여전히 공백(after=0)인 단계의 성격을 분류한다 (§4.5.3).

    "왜 34,521건을 더해도 이 단계는 0인가"를 코드로 답한다. 분류는 룰 테이블
    (`code_to_concept.csv`)에서 결정적으로 도출한다:
      - **has_rule=False** — 이 개념을 겨냥한 매핑 룰이 0개다. 어떤 코퍼스로도 룰
        경로로는 채울 수 없다 → 분류체계·온톨로지 범위의 경계이지 코퍼스의 결함이 아니다.
      - **has_rule=True** — 룰은 있으나 그 미세 코드가 이 코퍼스에 한 번도 부여되지
        않았다 → 코퍼스 특이적 공백(다르게 특화된 코퍼스는 채울 여지가 있다).

    other 를 주면(다른 코퍼스의 compare_coverage 결과) 그 코퍼스가 같은 공백을
    채우는지 대조 열을 붙인다 — breadth 포화를 실증하기 위함이다.
    """
    rules = pd.read_csv(CODE_MAPPING)
    n_rules = rules.groupby("concept_iri").size()

    gaps = df[df["after"] == 0].copy()
    step_iri = gaps.index.get_level_values("step")
    gaps["n_rules"] = [int(n_rules.get(s, 0)) for s in step_iri]
    gaps["has_rule"] = gaps["n_rules"] > 0
    if other is not None:
        other_after = other["after"].reindex(df.index).fillna(0).astype(int)
        gaps[f"{other_label}_after"] = other_after.loc[gaps.index].to_numpy()
    return gaps.reset_index()[
        ["level", "label", "before", "after", "has_rule", "n_rules"]
        + ([f"{other_label}_after"] if other is not None else [])
    ]


# §4.5.4 H1 민감도 — 증가폭 임계 k. 결과를 보기 전에 동결한다 (사전등록 · 사용자 확정 2026-07-16).
# 한 단계가 "증가"로 계수되려면 Δ≥k 여야 한다. k 를 올리면 얇은 증가가 0 으로 접히므로,
# "H1 이 1~2건짜리 얇은 커버리지에 기대는가"(§5.3(g))를 정면으로 검정한다. k 값은 최소 양의
# Δ(=38)부터 요구가 큰 200 까지 범위로 고정한다.
H1_SENSITIVITY_KS = (1, 10, 38, 84, 120, 200)


def threshold_sensitivity(
    df: pd.DataFrame, scope: str = "expanded49", ks: tuple[int, ...] = H1_SENSITIVITY_KS
) -> pd.DataFrame:
    """증가폭 임계 k 를 흔들며 H1 을 재검정한다 (그래프 재빌드 없음 · h1_coverage.csv 만).

    각 k 에서 Δ<k 인 단계는 Δ=0 으로 접고(증가 아님) Wilcoxon 을 다시 돌린다.
    검정 방법·단측·동점 제외는 그대로다 — 바뀌는 것은 "증가"의 문턱뿐이다.
    """
    d0 = df["delta"].to_numpy()
    out = []
    for k in ks:
        capped = pd.DataFrame({"delta": np.where(d0 >= k, d0, 0)}, index=df.index)
        r = wilcoxon_h1(capped, f"{scope}·Δ≥{k}")
        out.append({
            "k": k, "n": r.n, "increased": r.n_positive,
            "share": r.share_increased, "W": r.statistic,
            "p": r.p_value, "rejects": r.rejects_null,
        })
    return pd.DataFrame(out)


@dataclass(frozen=True)
class WilcoxonResult:
    """H1 의 검정 결과. 사전 확정: 단측(greater) · α=0.05 · 표본 단위는 공정 단계.

    **효과크기로 rank-biserial r 을 보고하지 않는다.** 병합은 특허를 더하기만 하므로
    (G₁ = G₀ ∪ 델타) 어떤 단계도 특허를 잃을 수 없다 — Δ<0 이 구조적으로 불가능하고
    r 은 항상 +1 이 된다. 계산된 값이 아니라 설계의 귀결이므로 보고하면 독자를 오도한다.
    대신 **증가한 단계의 비율**과 **증가한 단계의 중앙값 증가폭**으로 크기를 말한다.
    검정이 묻는 것은 "증가 방향인가"가 아니라 "증가한 단계가 충분히 많은가"이다 (§5.3).
    """

    scope: str
    n: int              # 표본 크기 (공정 단계 수)
    n_tied: int         # delta = 0 인 쌍 (zero_method="wilcox" 로 제외됨)
    n_positive: int
    n_negative: int
    median_delta: float          # 전 단계의 중앙값 — 동점이 과반이면 0 이 된다
    median_delta_positive: float  # 증가한 단계만의 중앙값 증가폭
    statistic: float | None   # W (scipy 의 단측 검정 통계량)
    p_value: float | None

    @property
    def share_increased(self) -> float:
        """증가한 단계의 비율. H1 이 실패할 수 있는 유일한 경로가 이 값이 작은 경우다."""
        return self.n_positive / self.n if self.n else 0.0

    @property
    def rejects_null(self) -> bool:
        """H₀(median ≤ 0) 를 기각하는가 = 논문의 H1 이 지지되는가."""
        return self.p_value is not None and self.p_value < 0.05


def wilcoxon_h1(df: pd.DataFrame, scope: str) -> WilcoxonResult:
    """H1: 비영 차이의 유사중앙값(C₁(s) − C₀(s)) > 0 — Wilcoxon 부호순위, 단측.

    동점 쌍(delta=0)은 zero_method="wilcox" 로 제외된다 — 그래서 검정이 말하는 것은
    **비영 차이의 유사중앙값**이지 전 단계의 리터럴 중앙값이 아니다. 동점이 과반이면
    median_delta 는 0 인데 검정은 기각할 수 있다. 둘 다 보고한다 (숨기면 모순으로 읽힌다).
    유효 쌍이 없으면 검정 없이 그 사실을 남긴다.
    """
    d = df["delta"].to_numpy()
    nz = d[d != 0]
    pos = d[d > 0]
    med_pos = float(np.median(pos)) if pos.size else 0.0

    if nz.size == 0:
        return WilcoxonResult(
            scope=scope, n=len(d), n_tied=len(d), n_positive=0, n_negative=0,
            median_delta=float(np.median(d)) if len(d) else 0.0,
            median_delta_positive=med_pos, statistic=None, p_value=None,
        )

    res = wilcoxon(nz, alternative="greater", zero_method="wilcox")

    return WilcoxonResult(
        scope=scope,
        n=len(d),
        n_tied=int((d == 0).sum()),
        n_positive=int((d > 0).sum()),
        n_negative=int((d < 0).sum()),
        median_delta=float(np.median(d)),
        median_delta_positive=med_pos,
        statistic=float(res.statistic),
        p_value=float(res.pvalue),
    )
