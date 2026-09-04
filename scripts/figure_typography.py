#!/usr/bin/env python3
"""figure_typography.py — 도판의 지면 기준 글자 크기와 상자 기하를 잰다 (그림 규격 F2′ · PLAN-089).

**왜 이 검사가 필요한가.** 규격 F2 는 *"라벨 8pt 미만을 쓰지 않는다"* 로 정하는데, 그 하한이
**소스 기준으로 읽히고 있었다.** 글자 크기는 절대값(pt)이고 배치는 정규좌표이므로 캔버스
11인치로 그린 도판이 지면 7인치로 조판되면 모든 라벨에 0.64가 곱해진다 — 소스 8pt 는 지면에서
5.1pt 다. 그래서 여기서는 **유효 크기**를 잰다.

    유효 크기 = 소스 크기 × (지면 폭 / 캔버스 폭)

**기하도 함께 잰다.** 상자 겹침과 캔버스 이탈은 2026-09-04 에 네 장에서 실측으로 나왔고
(`_rbox` 의 여백이 상자를 사방으로 넓힌다는 사실이 간격 계산에서 빠져 있었다), 그것을 고친
커밋의 실측 절차를 여기에 회귀 검사로 남긴다. **한 번 고친 것이 다시 깨지는지는 사람의
눈이 아니라 좌표가 판정한다.**

**경고 모드가 기본이다.** 착수 시점의 유효 크기 위반이 0 이 아니며(개념 도식 일곱 장),
캔버스를 지면 폭으로 내리는 전면 재설계는 PLAN-089 2단계다. 기하 위반만 `--strict` 에서
차단한다 — 그쪽은 이미 0 이기 때문이다.

    uv run python scripts/figure_typography.py            # 전량 · 경고
    uv run python scripts/figure_typography.py --strict   # 기하 위반이 있으면 종료코드 1
    uv run python scripts/figure_typography.py --lang en
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib.patches import FancyBboxPatch  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sdkb_paper.viz import concept, figures, labels  # noqa: E402

# 지면 폭(인치). **투고처 규정이 아니라 우리가 정한 편집 목표다** — 다수 저널의 전폭 도판이
# 갖는 값 가운데 보수적인 쪽이며, 투고처가 정해지면 그 규정으로 대체하고 출처를 여기에 적는다.
PAGE_WIDTH_IN = 7.0
MIN_EFFECTIVE_PT = 8.0
# 겹침·이탈의 허용 오차. 글리프 경계상자는 자간을 포함하므로 0 으로 잡으면 오탐이 난다.
EPS = 0.002


def _measure(fig) -> tuple[list[str], list[str]]:
    """도판 하나 — (기하 위반, 유효 크기 위반).

    **기하 검사는 정규좌표 패널에만 건다.** 개념 도식은 0–1 도화지 위에 상자를 놓지만
    데이터 플롯의 좌표는 값이므로, 같은 자로 재면 축 눈금이 전부 "캔버스 이탈" 로 잡힌다.
    글자 크기는 두 종류 모두에서 재며 축 눈금도 포함한다.
    """
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    scale = PAGE_WIDTH_IN / fig.get_size_inches()[0]
    geom: list[str] = []
    small: list[str] = []
    for ax in fig.axes:
        g, s = _measure_axes(ax, r, scale)
        geom += g
        small += s
    return geom, small


def _is_normalized(ax) -> bool:
    """0–1 도화지인가. 세로는 아래로 넓힌 도판이 있어(그림 8 의 교훈 띠) 상한만 본다."""
    y0, y1 = ax.get_ylim()
    return ax.get_xlim() == (0.0, 1.0) and y1 == 1.0 and y0 <= 0.0


def _measure_axes(ax, r, scale: float) -> tuple[list[str], list[str]]:
    inv = ax.transData.inverted()
    normalized = _is_normalized(ax)

    boxes = []
    for p in (ax.patches if normalized else []):
        if isinstance(p, FancyBboxPatch):
            bb = p.get_window_extent(renderer=r)
            (x0, y0), (x1, y1) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
            boxes.append((x0, y0, x1, y1))

    geom: list[str] = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            w = min(a[2], b[2]) - max(a[0], b[0])
            h = min(a[3], b[3]) - max(a[1], b[1])
            # 큰 상자가 작은 상자를 품는 것은 겹침이 아니라 배치다(띠 안의 단계 상자).
            nested = (a[0] <= b[0] and a[2] >= b[2] and a[1] <= b[1] and a[3] >= b[3]) or (
                b[0] <= a[0] and b[2] >= a[2] and b[1] <= a[1] and b[3] >= a[3]
            )
            if w > EPS and h > EPS and not nested:
                geom.append(f"상자 겹침 {w:.3f}×{h:.3f} :: {[round(v, 3) for v in a]} × {[round(v, 3) for v in b]}")

    small: list[str] = []
    # 축을 끈 도화지(`_blank`)에도 눈금 라벨 아티스트는 남아 있다. 그리지 않는 글자를
    # 세면 개념 도식마다 "0.0 · 0.2 …" 가 위반으로 잡힌다 — 실제로 그렇게 잡혔다.
    texts = list(ax.texts)
    if ax.axison:
        texts += ax.get_xticklabels() + ax.get_yticklabels()
    if ax.get_title():
        texts.append(ax.title)
    texts = [t for t in texts if t.get_visible()]
    for t in texts:
        s = t.get_text().split("\n")[0].strip()
        if not s:
            continue
        eff = t.get_fontsize() * scale
        if eff < MIN_EFFECTIVE_PT:
            small.append(f"{t.get_fontsize():.1f}pt → 지면 {eff:.1f}pt — {s[:40]}")
        if not normalized:
            continue
        bb = t.get_window_extent(renderer=r)
        (x0, y0), (x1, y1) = inv.transform([(bb.x0, bb.y0), (bb.x1, bb.y1)])
        if x0 < -EPS or x1 > 1 + EPS:
            geom.append(f"캔버스 이탈 x[{x0:.3f},{x1:.3f}] — {s[:40]}")
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        inside = [b for b in boxes if b[0] <= cx <= b[2] and b[1] <= cy <= b[3]]
        if inside:
            b = min(inside, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
            dx = max(b[0] - x0, x1 - b[2])
            if dx > EPS:
                geom.append(f"상자 밖 유출 +{dx:.3f} — {s[:40]}")
    return geom, small


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--lang", default="ko", choices=list(labels.LANGS))
    ap.add_argument("--strict", action="store_true", help="기하 위반이 있으면 종료코드 1")
    ap.add_argument("--verbose", action="store_true", help="유효 크기 위반을 전부 나열한다")
    ns = ap.parse_args()
    labels.set_lang(ns.lang)

    targets = [
        (fn, concept._basename(fn))
        for fn in (
            concept.fig_overview, concept.fig_layer_mismatch, concept.fig_tbox_views,
            concept.fig_gate_flow, concept.fig_experiment_flow,
            concept.fig_ep_gate_matrix, concept.fig_detection_port_boundary,
        )
    ] + [(figures.fig_ir_metrics, "ir_metrics.svg")]

    report: dict[str, tuple[list[str], list[str]]] = {}
    for fn, name in targets:
        saver = fn.__globals__["_save"]
        try:
            fn.__globals__["_save"] = lambda fig, out, _n=name: report.__setitem__(_n, _measure(fig)) or out
            fn(Path(name))
        finally:
            fn.__globals__["_save"] = saver

    n_geom = n_small = 0
    for name, (geom, small) in report.items():
        n_geom += len(geom)
        n_small += len(small)
        flag = "✗" if geom else ("△" if small else "✓")
        print(f"{flag} {name:38s} 기하 {len(geom):2d} · 지면 {MIN_EFFECTIVE_PT:.0f}pt 미만 {len(small):2d}")
        for g in geom:
            print(f"    [기하] {g}")
        if ns.verbose:
            for s in small:
                print(f"    [크기] {s}")

    print(f"\n지면 폭 {PAGE_WIDTH_IN}인치 기준 · 기하 위반 {n_geom} · 유효 크기 위반 {n_small}")
    if n_small:
        print("유효 크기 위반은 경고다 — 캔버스를 지면 폭으로 내리는 재설계는 PLAN-089 2단계다.")
    return 1 if (ns.strict and n_geom) else 0


if __name__ == "__main__":
    raise SystemExit(main())
