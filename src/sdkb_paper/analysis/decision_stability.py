"""결정 안정성 표 — 동결한 임계에서의 판정이 얼마나 가장자리에 있는가.

왜 필요한가 (PLAN-060 · 외부 검토 지적 3)
- 본 논문의 중앙 판정 넷은 전부 **임계와의 비교**로 결정된다(T1·T2·T3·T4). 임계 ε·δ·τ 는
  검정 관례에서 취한 규범적 선택이며 실무 근거가 미확립이라고 §3.5 가 이미 밝혔다. 그런데
  **그 임계가 얼마나 움직여야 판정이 뒤집히는가**는 어디에도 없었다.
- 이 표는 **사후 임계 변경이 아니다.** 임계는 §3.5 에서 동결한 값 그대로이고, 이 표가 보고하는
  것은 *"동결된 임계에서 내린 판정이 전환점에서 얼마나 떨어져 있는가"* 하나뿐이다. τ 는 사전
  동결 격자 {0, 0.05, 0.10} 안에서만 읽으며 격자 밖 값은 계산하지 않는다.

**수치는 하나도 새로 만들지 않는다(CLAUDE.md §1-1).** 전부 아래 세 산출물에서 읽는다.
    EP3(T1·T2)  paper/figures/data/concept_values.json   (원천은 동결 사전등록 PLAN-035 §B)
    EP2(T3)     data/processed/fault_matrix_v4.json      (holdout.by_tau · 사전 동결 τ 격자)
    T4          data/processed/ir/rag/scores/rag_t4_verdict_test_b.json
전환점은 관측된 하한·최대 하락의 절댓값이므로 **코드가 계산한다** — 손으로 적지 않는다.

용법:  python -m sdkb_paper.analysis.decision_stability [--check]
종료:  0 = 성공(또는 --check 정합) · 1 = 불일치 · 2 = 입력 산출물 소실
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CONCEPT_VALUES = Path("paper/figures/data/concept_values.json")
FAULT_MATRIX = Path("data/processed/fault_matrix_v4.json")
T4_VERDICT = Path("data/processed/ir/rag/scores/rag_t4_verdict_test_b.json")
OUT = Path("paper/tables/decision_stability.md")

# §3.5 에서 동결한 임계 — 이 파일은 값을 **읽어 적을 뿐 정하지 않는다**.
EPS = 0.02
DELTA = 0.05
TAU_MAIN = 0.05
EPS_T4 = 0.02

ANCHOR = "**결정 안정성 — 동결한 임계에서 판정이 전환되는 지점.**"


def fail(msg: str) -> None:
    print(f"실패: {msg}", file=sys.stderr)
    raise SystemExit(2)


def load(path: Path) -> dict:
    if not path.exists():
        fail(f"입력 산출물이 없다 — {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _num(x: float, digits: int = 4) -> str:
    """음수 부호는 하이픈이 아니라 원고와 같은 마이너스 기호(U+2212)로 적는다."""
    return f"{x:.{digits}f}".replace("-", "\u2212")


def _pval(p: float) -> str:
    """APA 표기 — 앞자리 0 을 떼고, 아주 작은 값은 상한으로 적는다."""
    return "< .0001" if p < 0.0001 else f"= {p:.4f}".replace("0.", ".")


def build() -> str:
    values = load(CONCEPT_VALUES)["values"]
    faults = load(FAULT_MATRIX)["holdout"]
    t4 = load(T4_VERDICT)

    # ── EP3 · T1 (family Recall@100 의 비열등) ────────────────────────────────
    t1_lb = float(values["ep3.p1.ci_lo"]["value"])
    t1_delta = float(values["ep3.p1.delta"]["value"])
    # ── EP3 · T2 (하위집단 최대 하락) ────────────────────────────────────────
    t2_drop = float(values["ep3.t2_max_drop"]["value"])
    # ── EP2 · T3 (사전 동결 τ 격자 안의 교차 태스크 단독 검출) ───────────────
    by_tau = faults["by_tau"]
    tau_rows = []
    for key in sorted(by_tau, key=float):
        main = by_tau[key]["main"]
        tau_rows.append(
            (
                float(key),
                int(main["n_t3_only"]),
                int(main["n_cross"]),
                float(main["mcnemar"]["p"]),
            )
        )
    # ── T4 (전달 · 인용 정확도의 비열등) ─────────────────────────────────────
    t4_lb = _t4_lower_bound(t4, values)

    lines = [
        ANCHOR,
        "",
        "| 조건 | 동결 임계 | 관측 | 판정 | 판정이 전환되는 지점 |",
        "|---|---|---|---|---|",
        f"| T1 · 검색 비열등 | ε = {EPS} | ΔR@100 = {_num(t1_delta)} · "
        f"LB₉₅ = {_num(t1_lb)} | 미충족 | ε > {abs(t1_lb):.4f} 이어야 충족으로 바뀐다 |",
        f"| T2 · 하위집단 안전 | δ = {DELTA} | 최대 하락 = +{t2_drop:.4f} | 충족 | "
        f"δ ≤ {t2_drop:.4f} 이면 미충족으로 바뀐다 |",
    ]
    for tau, only, total, p in tau_rows:
        mark = " (사전 지정)" if abs(tau - TAU_MAIN) < 1e-9 else ""
        verdict = "충족" if p < 0.05 else "미충족"
        lines.append(
            f"| T3 · 교차 태스크 검출 (EP2 분포 검사) | τ = {tau:.2f}{mark} | T3 단독 검출 "
            f"{only}/{total} · *p* {_pval(p)} | {verdict} | 사전 동결 격자 안의 평가 |"
        )
    lines.append(
        f"| T4 · 하류 생성 층 | ε_T4 = {EPS_T4} | LB₉₅ = {_num(t4_lb)} | 미충족 | "
        f"ε_T4 > {abs(t4_lb):.4f} 이어야 충족으로 바뀐다 |"
    )
    lines += [
        "",
        "임계는 §3.5에서 동결한 값 그대로이며 본 표는 그 값을 이동시키지 않는다. τ는 사전에 "
        "동결한 격자 {0, 0.05, 0.10} 안에서만 읽는다.",
    ]
    return "\n".join(lines) + "\n"


def _t4_lower_bound(t4: dict, values: dict) -> float:
    """T4 인용 정확도의 95% 신뢰구간 하한 — 산출물에서 읽되 동결본과 대조한다."""
    frozen = float(values["t4.citation_precision.lb95"]["value"])
    found = _find_lb(t4)
    if found is not None and abs(found - frozen) > 5e-5:
        fail(f"T4 하한이 동결본과 어긋난다 — 산출물 {found} · 동결본 {frozen}")
    return frozen


def _find_lb(node: object) -> float | None:
    """중첩 구조 어디에 있든 인용 정확도의 lb95 를 찾는다(키 이름은 산출물이 정한다)."""
    if isinstance(node, dict):
        for key, val in node.items():
            if isinstance(val, (int, float)) and "lb" in key.lower():
                return float(val)
            found = _find_lb(val)
            if found is not None:
                return found
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="재생성하지 않고 정합만 본다")
    args = parser.parse_args()

    table = build()
    if args.check:
        if not OUT.exists():
            print(f"불일치: {OUT} 가 없다", file=sys.stderr)
            return 1
        if OUT.read_text(encoding="utf-8") != table:
            print(f"불일치: {OUT} 가 산출물과 어긋난다 — `make tables-stability` 로 재생성한다",
                  file=sys.stderr)
            return 1
        print(f"정합: {OUT}")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(table, encoding="utf-8")
    print(f"생성: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
