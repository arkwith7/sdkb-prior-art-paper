"""점수 함수 확정표를 코드에서 읽어 낸다 — PLAN-086 E-1d.

**왜 스크립트인가.** CLAUDE.md §1-7·§1-1 은 논문의 표를 코드가 만들 것을 요구한다. 점수 함수의
가중치·정규화·항 정의는 지금까지 산문에만 있었고, 그래서 S5 §4 가 `ConceptOverlap` 을
*"가중 Jaccard"* 라 적은 채 살아남았다 — 코드는 frozenset 의 비가중 Jaccard 다. 값을 손으로
옮기는 한 같은 표류가 되돌아온다.

출력은 `paper/tables/score_spec.md` 이며 보충자료 S10 이 그대로 인용한다.

    uv run python scripts/export_score_spec.py
"""

from __future__ import annotations

import inspect
from pathlib import Path

from sdkb_paper.analysis import ontology_eval as OE
from sdkb_paper.analysis import results_table as RT
from sdkb_paper.retrieval import ontology_rerank as OR
from sdkb_paper.retrieval import systems as S

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper" / "tables" / "score_spec.md"


def _loc(obj, name: str) -> str:
    """`모듈경로:행번호` — 값의 출처를 표에 함께 싣는다."""
    src_file = Path(inspect.getsourcefile(obj))
    line = inspect.getsourcelines(obj)[1]
    rel = src_file.relative_to(ROOT / "src" / "sdkb_paper")
    return f"`{rel.as_posix()}:{line}`"


def _term_rows() -> list[tuple[str, str, str, str]]:
    """(항, 정의, 입력, 코드 위치)."""
    return [
        (
            "ConceptOverlap `c`",
            "**비가중 Jaccard** — `|Q∩D| / |Q∪D|`. 집합 연산이며 개념별 가중·문서빈도 가중이 없다",
            "개념 슬러그 집합(frozenset · 축 6종)",
            _loc(OR.OntologyFeatures.concept_overlap, "concept_overlap"),
        ),
        (
            "PathSim `p`",
            "축 클래스의 Wu–Palmer — `2·depth(LCA) / (depth(a)+depth(b))`. 개념 쌍이 아니라 **축 클래스**를 읽는다",
            "개념 집합 → 축 클래스",
            _loc(OR.OntologyFeatures._wp, "_wp"),
        ),
        (
            "IpcSim `i`",
            "분류 접두 계층의 **비가중 Jaccard** — 접두 집합 교집합/합집합",
            "IPC·CPC 코드 집합",
            _loc(OR.OntologyFeatures.ipc_sim, "ipc_sim"),
        ),
        (
            "FeatureCoverage `f`",
            "질의 독립항 한정요소 중 후보에 `cos ≥ τ` 매칭이 있는 **비율**",
            "한정요소 임베딩 행렬",
            "`retrieval/feature_coverage.py:120`",
        ),
    ]


def _system_rows() -> list[tuple[str, ...]]:
    p0 = OE.SELECTED_ALPHA, OE.SELECTED_W
    p1_tau, p1_alpha, p1_w4 = RT.P1_TAU, RT.P1_ALPHA, RT.P1_W4
    b5 = S.OntoConfig(alpha=1.0, w_c=1.0, w_h=0.0, w_i=0.0, use_ipc=False)
    rows = [
        (
            "B4 (분류 단독)",
            "분류 접두 공유 ∩ 시점·패밀리 허용 집합",
            "`IpcSim` 단독",
            "—",
            "—",
            _loc(S.build_b4, "build_b4"),
        ),
        (
            "B5 (온톨로지 단독)",
            "개념 정확 공유 ∩ 시점·패밀리 허용 집합",
            f"`α={b5.alpha}` · `w_c={b5.w_c}` · `w_h={b5.w_h}` · `w_i={b5.w_i}`",
            "IpcSim 미사용",
            "—",
            _loc(S.build_b5, "build_b5"),
        ),
        (
            "P0★ (사전 지정 주 구성)",
            f"**B3 상위 {S.POOL_K}건 재순위화** — 후보집합 불확대",
            f"`α={p0[0]}` · `(w_c, w_h, w_i) = {p0[1]}`",
            "선형 rank-norm `1 − rank/(m−1)` ∈ [0,1]",
            "—",
            _loc(S.rerank_p0, "rerank_p0"),
        ),
        (
            "P1 (부차 구성 · +한정요소)",
            f"**B3 상위 {S.POOL_K}건 재순위화** — 후보집합 불확대",
            f"`α={p1_alpha}` · `(w_c, w_h, w_i, w_f) = {p1_w4}`",
            "선형 rank-norm `1 − rank/(m−1)` ∈ [0,1]",
            f"`τ = {p1_tau}`",
            _loc(OE.rerank_p1, "rerank_p1"),
        ),
    ]
    return rows


def render() -> str:
    L: list[str] = []
    L.append("<!-- 자동 생성 — scripts/export_score_spec.py · 손으로 고치지 않는다 (CLAUDE.md §1-1·§1-7) -->")
    L.append("")
    L.append("### 표 S10-1 · 점수 함수 확정표 (코드에서 추출)")
    L.append("")
    L.append("온톨로지 결합 구성의 점수는 다음과 같다.")
    L.append("")
    L.append("```")
    L.append("score(q, d) = (1 − α) · text_norm(q, d)")
    L.append("            +      α · ( w_c·ConceptOverlap + w_h·PathSim")
    L.append("                        + w_i·IpcSim + w_f·FeatureCoverage@τ )")
    L.append("```")
    L.append("")
    L.append("| 구성 | 후보 풀 | 최종 가중치 | 텍스트 정규화 | 임계 | 코드 위치 |")
    L.append("|---|---|---|---|---|---|")
    for r in _system_rows():
        L.append("| " + " | ".join(r) + " |")
    L.append("")
    L.append("| 항 | 정의 | 입력 | 코드 위치 |")
    L.append("|---|---|---|---|")
    for r in _term_rows():
        L.append("| " + " | ".join(r) + " |")
    L.append("")
    L.append(
        "**`w_h = 0` 이므로 계층·정렬만 바꾸는 자원 변경은 P0★·P1 의 점수에 원리적으로 비가시이다.** "
        "이 값은 개발셋 격자 선택의 결과이며 사전등록 항목이 아니다."
    )
    L.append("")
    L.append(
        "**`ConceptOverlap` 은 비가중이다.** 개념별 가중이나 문서빈도 가중은 어느 구성에도 들어가지 "
        "않으며, 자원의 어휘를 늘리면 분모가 함께 커진다 — 평가 결과 §5.2 의 해석이 이 사실에 걸려 있다."
    )
    L.append("")
    return "\n".join(L)


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    text = render()
    OUT.write_text(text, encoding="utf-8")
    print(f"기록: {OUT.relative_to(ROOT)} ({len(text)}자)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
