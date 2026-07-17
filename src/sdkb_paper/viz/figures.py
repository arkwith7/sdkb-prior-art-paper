"""논문 그림은 전부 이 모듈이 생성한다 → paper/figures/ (수작업 그림 금지).

두 갈래다.
1. **서사 도식**(fig_gap_map · fig_evolution · fig_research_model · fig_pipeline ·
   fig_vacuous_gate · fig_traps · fig_rq3_portability · fig_summary_matrix) — 논문의
   주장 흐름을 나른다. 수치는 §4 표에서 확정된 실측값이며 여기서는 시각화만 한다.
2. **데이터 플롯**(fig_coverage_gap · fig_h1_coverage · fig_h2_timeseries) — analysis
   산출 CSV(`data/processed/`)를 그린다.

출력은 전부 **SVG**다. `make figures` 하나가 CSV·상수에서 전량을 결정적으로 재생성한다.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager as fm
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from sdkb_paper.config import FIGURES

PROCESSED = FIGURES.parents[1] / "data" / "processed"

# ── 한글 폰트 (없으면 두부(□)가 된다) ──────────────────────────────────────────
_FONT_FILES = [
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
]


def _setup_fonts() -> None:
    family: list[str] = []
    for path in _FONT_FILES:
        if not Path(path).exists():
            continue
        try:
            fm.fontManager.addfont(path)
            family.append(fm.FontProperties(fname=path).get_name())
        except Exception:  # ttc 등록 실패 시 남은 후보로 폴백
            continue
    family.append("DejaVu Sans")  # 라틴·기호 폴백
    matplotlib.rcParams["font.family"] = family
    matplotlib.rcParams["axes.unicode_minus"] = False
    matplotlib.rcParams["svg.fonttype"] = "path"  # 글리프를 벡터로 구워 이식성 확보


_setup_fonts()

# ── 스타일 시스템 (그림 전체가 한 벌로 읽히도록) ──────────────────────────────
INK = "#1A202C"
MUTE = "#5A6472"
BORDER = "#CBD5E0"
ASIS = "#B23A48"
ASIS_FILL = "#F7E8EA"
ASIS_EDGE = "#D98A92"
TOBE = "#2B6CB0"
TOBE_FILL = "#E4EEF8"
TOBE_EDGE = "#7FA8D6"
GREEN = "#2F855A"
GREEN_FILL = "#E4F0EA"
GOLD = "#B7791F"
GRID = "#E2E8F0"


def _rbox(
    ax,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str = "",
    body: str = "",
    fill: str = "#FFFFFF",
    edge: str = BORDER,
    tcolor: str = INK,
    ts: int = 11,
    bs: int = 9,
    align: str = "center",
) -> None:
    """제목+본문을 담은 둥근 상자."""
    ax.add_patch(
        FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.006,rounding_size=0.014",
            linewidth=1.4, edgecolor=edge, facecolor=fill,
        )
    )
    ha = "left" if align == "left" else "center"
    tx = x + (0.018 if align == "left" else w / 2)
    if title:
        ax.text(tx, y + h - 0.028, title, ha=ha, va="top",
                fontsize=ts, fontweight="bold", color=tcolor)
    if body:
        dy = 0.028 + 0.045 * (title.count("\n") + 1) + 0.008
        ax.text(tx, y + h - dy, body, ha=ha, va="top",
                fontsize=bs, color=MUTE, linespacing=1.4)


def _arrow(ax, x1, y1, x2, y2, color=INK, lw=2.0, style="-|>", ms=16) -> None:
    ax.add_patch(
        FancyArrowPatch(
            (x1, y1), (x2, y2), arrowstyle=style, mutation_scale=ms,
            linewidth=lw, color=color, shrinkA=0, shrinkB=0,
        )
    )


def _chip(ax, x, y, text, color=GREEN, fill=GREEN_FILL) -> None:
    ax.text(x, y, text, ha="center", va="center", fontsize=8.5,
            fontweight="bold", color=color,
            bbox=dict(boxstyle="round,pad=0.3", fc=fill, ec=color, lw=1.0))


def _canvas(w=11.0, h=6.5):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    return fig, ax


def _save(fig, out: Path) -> Path:
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


# ═══════════════════════════════════════════════════════════════════════════
# 서사 도식
# ═══════════════════════════════════════════════════════════════════════════
def fig_gap_map(out: Path | None = None) -> Path:
    """그림 1 — 세 AS-IS를 세 TO-BE로 (신규성 한 장 요약, §1·§2.6)."""
    out = out or FIGURES / "fig1_gap_map.svg"
    fig, ax = _canvas(11.5, 6.6)
    ax.text(0.5, 0.965, "연구 갭 — 세 개의 AS-IS를 세 개의 TO-BE로",
            ha="center", va="top", fontsize=15, fontweight="bold", color=INK)
    ax.text(0.5, 0.915, "각 갭은 본 연구의 독립적 방법론 기여로 대응된다",
            ha="center", va="top", fontsize=10, color=MUTE)
    rows = [
        ("갭 1", "기여 (i)",
         "온톨로지 검증 = 소수 SPARQL 예제",
         "응답률 100%가 어휘의 9%만 심문\n(공허한 게이트)",
         "병합 전 4층 게이트(L0–L3)\n+ 어휘 검증 커버리지",
         "응답률이 놓치는 것을 진단"),
        ("갭 2", "기여 (iii)",
         "재현성 = 해시(sha256)만",
         "낡게 빌드된 스냅샷도 통과\n(C₀가 16으로 낮게 잡힘)",
         "신선도 검증 (L0)",
         "산출물이 입력보다 낡았는지 검사"),
        ("갭 3", "기여 (ii)",
         "기술예측 집계 = 분류코드·키워드",
         "코드는 소급 재분류(시간적 무효)\n이름은 표준화 이후라 늦음",
         "개념의 논리 조합(∧·∨)",
         "이름·코드 이전에 조기탐지"),
    ]
    y0, hh, gap = 0.60, 0.205, 0.055
    for i, (gtag, ctag, a_t, a_b, b_t, b_b) in enumerate(rows):
        y = y0 - i * (hh + gap)
        ax.text(0.055, y + hh / 2, gtag, ha="center", va="center",
                fontsize=10, fontweight="bold", color=MUTE)
        _rbox(ax, 0.10, y, 0.36, hh, a_t, a_b, ASIS_FILL, ASIS_EDGE, ASIS, 11, 9, "left")
        ax.text(0.28, y + hh + 0.012, "AS-IS", ha="center", fontsize=8,
                fontweight="bold", color=ASIS)
        _arrow(ax, 0.475, y + hh / 2, 0.545, y + hh / 2, color=INK, lw=2.2)
        _rbox(ax, 0.555, y, 0.36, hh, b_t, b_b, TOBE_FILL, TOBE_EDGE, TOBE, 11, 9, "left")
        ax.text(0.735, y + hh + 0.012, "TO-BE", ha="center", fontsize=8,
                fontweight="bold", color=TOBE)
        _chip(ax, 0.955, y + hh / 2, ctag)
    return _save(fig, out)


def fig_evolution(out: Path | None = None) -> Path:
    """그림 2 — SDKB 3단계 진화와 본 연구의 위치 (§2.5)."""
    out = out or FIGURES / "fig2_evolution.svg"
    fig, ax = _canvas(11.5, 6.2)
    ax.text(0.5, 0.96, "SDKB의 3단계 진화 — 각 단계가 다른 타당성 차원을 확보한다",
            ha="center", va="top", fontsize=15, fontweight="bold", color=INK)
    stages = [
        ("1단계 · 전문가 매칭", "개념 타당성",
         "공개 온톨로지·분류·표준·규제를\n큐레이션·정렬 (스키마 수준)", "#EDF2F7", "#A0AEC0", INK),
        ("2단계 · 선행기술조사", "근거 타당성",
         "심사관 인용 문헌으로 정박\n(weak ground truth)", TOBE_FILL, TOBE_EDGE, TOBE),
        ("3단계 · 기술예측", "커버리지·시간 차원",
         "삼성·SK하이닉스 전 공정 특허 보강\n+ 4층 게이트 — 본 연구", GREEN_FILL, GREEN, GREEN),
    ]
    x0, ww, hh = 0.06, 0.285, 0.30
    for i, (title, dim, body, fill, edge, tc) in enumerate(stages):
        x = x0 + i * 0.315
        y = 0.24 + i * 0.14
        _rbox(ax, x, y, ww, hh, title, body, fill, edge, tc, 12, 9.5, "left")
        ax.text(x + 0.014, y + hh - 0.006, dim, ha="left", va="bottom",
                fontsize=9, fontweight="bold", color=tc)
        if i < 2:
            _arrow(ax, x + ww + 0.004, y + hh / 2, x + 0.315 - 0.004,
                   y + 0.14 + hh / 2, color=MUTE, lw=2.0)
    ax.text(0.50, 0.16, "G₀ = 2단계까지 완료한 현행 SDKB (동결 baseline)",
            ha="center", fontsize=9.5, color=TOBE, fontweight="bold")
    ax.text(0.685, 0.10, "G₁·G₂ = 3단계 보강 (본 연구의 처치)",
            ha="center", fontsize=9.5, color=GREEN, fontweight="bold")
    return _save(fig, out)


def fig_research_model(out: Path | None = None) -> Path:
    """그림 3 — 연구 모형: 보강 처치 → 게이트 → 태스크 성능 (§3.1)."""
    out = out or FIGURES / "fig3_research_model.svg"
    fig, ax = _canvas(11.5, 5.6)
    ax.text(0.5, 0.95, "연구 모형 — 보강 처치 → 품질 게이트 → 태스크 성능",
            ha="center", va="top", fontsize=15, fontweight="bold", color=INK)
    _rbox(ax, 0.03, 0.44, 0.22, 0.26, "G₀", "현행 SDKB\n(특허 1,000 포함)",
          "#EDF2F7", "#A0AEC0", INK, 13, 9.5)
    _rbox(ax, 0.39, 0.42, 0.24, 0.30, "4층 게이트", "L0 신선도 · L1 SHACL\nL2 추론 · L3 CQ",
          TOBE_FILL, TOBE_EDGE, TOBE, 12, 9.5)
    _rbox(ax, 0.75, 0.44, 0.22, 0.26, "G₁", "보강 온톨로지\n(통과분만 병합)",
          GREEN_FILL, GREEN, GREEN, 13, 9.5)
    _arrow(ax, 0.25, 0.57, 0.385, 0.57, TOBE, 2.4)
    ax.text(0.315, 0.60, "특허 보강 (독립변수)", ha="center", fontsize=9,
            color=TOBE, fontweight="bold")
    _arrow(ax, 0.63, 0.57, 0.745, 0.57, GREEN, 2.4)
    ax.text(0.69, 0.60, "통과분만", ha="center", fontsize=8.5, color=GREEN)
    ax.text(0.51, 0.375, "매개: 게이트 통과", ha="center", fontsize=8.5, color=MUTE)
    _rbox(ax, 0.58, 0.05, 0.18, 0.20, "H1", "공정 단계별\n개념 커버리지",
          "#FFFFFF", GREEN, GREEN, 12, 9)
    _rbox(ax, 0.79, 0.05, 0.18, 0.20, "H2", "신흥기술 신호\n조기탐지 시차",
          "#FFFFFF", GREEN, GREEN, 12, 9)
    _arrow(ax, 0.83, 0.44, 0.70, 0.255, GREEN, 1.8)
    _arrow(ax, 0.88, 0.44, 0.88, 0.255, GREEN, 1.8)
    ax.text(0.86, 0.30, "종속변수", ha="center", fontsize=8.5, color=MUTE)
    return _save(fig, out)


def fig_pipeline(out: Path | None = None) -> Path:
    """그림 4 — 검증 게이트 내장 보강 파이프라인 (§3.3)."""
    out = out or FIGURES / "fig4_pipeline.svg"
    fig, ax = _canvas(12.0, 5.4)
    ax.text(0.5, 0.95, "검증 게이트 내장 보강 파이프라인 — 통과분만 병합된다",
            ha="center", va="top", fontsize=15, fontweight="bold", color=INK)
    steps = [
        ("수집", "KIPRIS 학술 API"),
        ("전처리", "정규화·dedup·결측"),
        ("개념 매핑", "3층: 별칭·조합·후보"),
    ]
    y, hh, ww = 0.58, 0.20, 0.20
    xs = [0.02, 0.235, 0.45]
    for (t, b), x in zip(steps, xs, strict=True):
        _rbox(ax, x, y, ww, hh, t, b, "#EDF2F7", "#A0AEC0", INK, 11, 8.5)
    _rbox(ax, 0.665, y - 0.02, 0.315, hh + 0.04, "4층 게이트", "",
          TOBE_FILL, TOBE_EDGE, TOBE, 11)
    for i, lay in enumerate(["L0 신선도", "L1 SHACL", "L2 추론", "L3 CQ"]):
        ax.text(0.68 + i * 0.076, y + hh / 2 - 0.02, lay, ha="left", va="center",
                fontsize=7.6, color=TOBE)
    for x in xs[1:]:
        _arrow(ax, x - 0.013, y + hh / 2, x - 0.002, y + hh / 2, MUTE, 1.8, ms=12)
    _arrow(ax, 0.45 + ww + 0.001, y + hh / 2, 0.663, y + hh / 2, MUTE, 1.8, ms=12)
    _rbox(ax, 0.79, 0.06, 0.19, 0.18, "병합 → G₁", "개념 ≥1 통과분",
          GREEN_FILL, GREEN, GREEN, 11, 8.5)
    _arrow(ax, 0.82, y - 0.02, 0.87, 0.245, GREEN, 2.0)
    _rbox(ax, 0.45, 0.06, 0.28, 0.18, "L1에서 탈락", "개념 매핑 없는 델타 10,456건",
          ASIS_FILL, ASIS_EDGE, ASIS, 11, 8.5)
    _arrow(ax, 0.72, y - 0.021, 0.62, 0.245, ASIS, 2.0)
    ax.text(0.60, 0.30, "게이트 판별력\n(RQ1)", ha="center", fontsize=8,
            color=ASIS, fontweight="bold")
    return _save(fig, out)


def fig_vacuous_gate(out: Path | None = None) -> Path:
    """그림 6 — 공허한 게이트: 응답률은 둘 다 100%, 어휘 커버리지가 차이를 드러낸다 (§4.2).

    수치는 §4.2 표(`make vocab`) 확정값이다.
    """
    out = out or FIGURES / "fig6_vacuous_gate.svg"
    fig, ax = plt.subplots(figsize=(9, 5.4))
    groups = ["CQ 응답률", "술어 커버리지", "클래스 커버리지"]
    k8 = [100.0, 9.4, 16.0]
    k14 = [100.0, 32.1, 28.0]
    x = list(range(len(groups)))
    w = 0.36
    b1 = ax.bar([i - w / 2 for i in x], k8, w, label="K=8 (손으로 선정)",
                color="#B0B7C3", edgecolor="#8A93A3")
    b2 = ax.bar([i + w / 2 for i in x], k14, w, label="K=14 (태스크 도출)",
                color=TOBE, edgecolor="#1E4E82")
    for bars in (b1, b2):
        for r in bars:
            if r.get_height() >= 100:  # 100% 막대는 라벨 생략 (범례·밴드와 겹침)
                continue
            ax.text(r.get_x() + r.get_width() / 2, r.get_height() + 1.5,
                    f"{r.get_height():.1f}", ha="center", fontsize=9, color=INK)
    ax.axhspan(97, 103, color=ASIS_FILL, zorder=0)
    ax.text(2.34, 100, "응답률은\n둘 다 100%", ha="center", va="center",
            fontsize=9, color=ASIS, fontweight="bold")
    ax.set_ylim(0, 112)
    ax.set_xticks(x)
    ax.set_xticklabels(groups, fontsize=10)
    ax.set_ylabel("백분율 (%)")
    ax.set_title("공허한 게이트 — 응답률만 보면 9%짜리와 32%짜리가 구별되지 않는다",
                 fontsize=12, fontweight="bold")
    ax.legend(loc="upper left", framealpha=0.9)
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    return _save(fig, out)


def fig_traps(out: Path | None = None) -> Path:
    """그림 9 — 개념 단위 조기탐지 측정의 세 함정과 회피 설계 (§4.4·§5.3)."""
    out = out or FIGURES / "fig9_traps.svg"
    fig, ax = _canvas(12.0, 5.2)
    ax.text(0.5, 0.95, "개념 단위 조기탐지의 세 함정 — 규명하고 회피한다",
            ha="center", va="top", fontsize=15, fontweight="bold", color=INK)
    traps = [
        ("소급 재분류", "현재 코드가 과거 출원에 소급 부여\n(H10 스킴 전량 2021년 이후 신설)",
         "명칭 키워드 대조군\n(명세는 소급 재작성 안 됨 · 시점 유효)"),
        ("개념의 코드 기생", "개념 시계열에 회로 코드가 혼입\n(예: MRAM 자기메모리 회로)",
         "구조 전용(si_struct) 정의\n— 명칭 대조군과 서로소"),
        ("관측창 좌측절단", "창이 열릴 때 이미 정점이면\n상대성장 규칙이 부상을 못 봄",
         "교정 창(2005–) 사용\n(HBM 2016 → 2009로 이동)"),
    ]
    ww = 0.30
    for i, (t, asis, tobe) in enumerate(traps):
        x = 0.035 + i * 0.325
        ax.text(x + ww / 2, 0.83, f"함정 {i + 1} · {t}", ha="center",
                fontsize=11.5, fontweight="bold", color=INK)
        _rbox(ax, x, 0.44, ww, 0.30, "증상 (AS-IS)", asis,
              ASIS_FILL, ASIS_EDGE, ASIS, 9.5, 9, "left")
        _arrow(ax, x + ww / 2, 0.435, x + ww / 2, 0.375, GREEN, 2.2)
        _rbox(ax, x, 0.06, ww, 0.30, "회피 (TO-BE)", tobe,
              GREEN_FILL, GREEN, GREEN, 9.5, 9, "left")
    return _save(fig, out)


def fig_rq3_portability(out: Path | None = None) -> Path:
    """그림 10 — RQ3 이식성: 폭은 포화, 깊이가 갈린다 (§4.6).

    수치는 §4.6·표 15 확정값(G₁ 236 vs G₂ 573; 커버 26=26).
    """
    out = out or FIGURES / "fig10_rq3_portability.svg"
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    ax = axes[0]
    ax.bar(["G₁ (종합 IDM)", "G₂ (소부장)"], [26, 26],
           color=["#B0B7C3", GREEN], edgecolor="#5A6472")
    for i, v in enumerate([26, 26]):
        ax.text(i, v + 0.4, f"{v}/49", ha="center", fontsize=11, fontweight="bold")
    ax.set_ylim(0, 32)
    ax.set_title("폭(breadth) — 커버된 공정 단계\n코퍼스와 무관하게 26으로 포화",
                 fontsize=11, fontweight="bold")
    ax.set_ylabel("커버된 단계 수")
    ax = axes[1]
    ax.bar(["G₁ (종합 IDM)", "G₂ (소부장)"], [236, 573],
           color=["#B0B7C3", GREEN], edgecolor="#5A6472")
    for i, v in enumerate([236, 573]):
        ax.text(i, v + 12, f"{v}", ha="center", fontsize=11, fontweight="bold")
    ax.annotate("2.4배", xy=(1, 573), xytext=(0.5, 600), ha="center",
                color=GREEN, fontsize=13, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=GREEN, lw=1.2))
    ax.set_ylim(0, 660)
    ax.set_title("깊이(depth) — 증가 단계 중앙 증가폭\n소부장이 특화 구간의 깊이를 더한다",
                 fontsize=11, fontweight="bold")
    ax.set_ylabel("증가폭 중앙값 (특허 수)")
    for a in axes:
        a.spines[["top", "right"]].set_visible(False)
    fig.suptitle("RQ3 — 같은 프레임워크가 코퍼스 성격을 그대로 드러낸다 (외적 타당도)",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    return _save(fig, out)


def fig_summary_matrix(out: Path | None = None) -> Path:
    """그림 11 — 결과 한 장 요약: RQ ↔ 가설 ↔ 결과 ↔ 근거 (§5.1)."""
    out = out or FIGURES / "fig11_summary.svg"
    fig, ax = _canvas(12.0, 5.0)
    ax.text(0.5, 0.95, "결과 요약 — 세 질문, 세 답",
            ha="center", va="top", fontsize=15, fontweight="bold", color=INK)
    cols = ["", "질문", "가설·판정", "핵심 수치", "근거"]
    xw = [0.06, 0.24, 0.26, 0.24, 0.16]
    xs = [0.02]
    for w in xw[:-1]:
        xs.append(xs[-1] + w)
    rows = [
        ("RQ1", "게이트가 정합성 훼손 델타를 거부하며\n커버리지를 확장하는가",
         "H1 지지\n(단측 Wilcoxon)", "커버 20 → 26 / 49\np = 4.8×10⁻⁷", "그림 5·7\n표 6"),
        ("RQ2", "코드·이름 없는 국면을\n표현·조기탐지하는가",
         "H2 능력 존재 증명\n(유의성 아님)", "HBM 개념 2009\nvs 명칭 2020 (11년차)", "그림 8·9\n표 7–10"),
        ("RQ3", "프레임워크가 코퍼스를 바꿔도\n재현되는가 (이식성)",
         "H1 소부장서도 지지\n세 층 모두", "폭 26 포화\n깊이 236 → 573", "그림 10\n표 15·16"),
    ]
    y0, hh = 0.72, 0.205
    for j, (c, w) in enumerate(zip(cols, xw, strict=True)):
        if c:
            ax.text(xs[j] + w / 2, 0.80, c, ha="center", fontsize=10,
                    fontweight="bold", color=MUTE)
    for i, row in enumerate(rows):
        y = y0 - i * (hh + 0.01) - hh
        fill = ["#F7FAFC", "#EFF4F9", "#F7FAFC"][i]
        ax.add_patch(FancyBboxPatch((0.02, y), 0.96, hh,
                     boxstyle="round,pad=0.004,rounding_size=0.01",
                     linewidth=1.0, edgecolor=GRID, facecolor=fill))
        for j, cell in enumerate(row):
            tc = TOBE if j == 0 else (GREEN if j == 2 else INK)
            fw = "bold" if j in (0, 2) else "normal"
            fs = 12 if j == 0 else 9.2
            ax.text(xs[j] + xw[j] / 2, y + hh / 2, cell, ha="center", va="center",
                    fontsize=fs, color=tc, fontweight=fw, linespacing=1.3)
    return _save(fig, out)


# ═══════════════════════════════════════════════════════════════════════════
# 데이터 플롯 (data/processed CSV)
# ═══════════════════════════════════════════════════════════════════════════
def fig_coverage_gap(df: pd.DataFrame, out: Path | None = None) -> Path:
    """그림 5 — 보강 전(G₀) 공정 단계별 커버리지 편중 (§4.1).

    `before` 만 그린다 — 보강 효과는 그림 7의 몫이고, 이 그림은 "왜 보강이
    필요한가"라는 §4.1 의 동기를 그린다. 공백(before=0) 단계는 회색 라벨로 드러낸다.
    """
    out = out or FIGURES / "fig5_coverage_gap.svg"
    plot = df.sort_values(["level", "before"], ascending=[True, False]).copy()
    plot.index = plot["label"]
    covered = plot["before"] > 0
    colors = covered.map({True: TOBE, False: "#e0e0e0"})
    ax = plot["before"].plot.barh(
        figsize=(8.5, max(4, 0.28 * len(plot))), color=list(colors), width=0.8
    )
    ax.set_xscale("symlog")
    ax.set_xlabel("mapped patents in G₀ (symlog)")
    ax.set_ylabel("process step")
    n_cov, n_gap = int(covered.sum()), int((~covered).sum())
    ax.set_title(
        f"G₀ process coverage before augmentation — "
        f"{n_cov} covered / {n_gap} empty of {len(plot)} steps"
    )
    gap_labels = set(plot.index[~covered])
    for lbl in ax.get_yticklabels():
        if lbl.get_text() in gap_labels:
            lbl.set_color("#999999")
    plt.tight_layout()
    return _save(plt.gcf(), out)


def fig_h1_coverage(df: pd.DataFrame, out: Path | None = None) -> Path:
    """그림 7 — H1: 공정 단계별 커버리지 G₀ vs G₁ (§4.3).

    복원 이전 20개 단계를 레이블 * 로 표시한다 — 복원 단계는 G₀ 에서 0 이라 H1 에
    유리하므로 어느 막대가 그쪽인지 그림에서 바로 보여야 한다.
    """
    out = out or FIGURES / "fig7_h1_coverage.svg"
    plot = df.sort_values(["level", "delta"], ascending=[True, True]).copy()
    marker = plot["in_legacy20"].map({True: "", False: " *"}) if "in_legacy20" in plot else ""
    plot.index = plot["label"] + marker
    ax = plot[["before", "after"]].plot.barh(
        figsize=(9, max(4, 0.28 * len(plot))), color=["#B0B7C3", TOBE]
    )
    ax.set_xscale("symlog")
    ax.set_xlabel("mapped patents (symlog)   * = step restored from SemiKong Table 7")
    ax.set_ylabel("process step")
    ax.legend(["G₀ (before)", "G₁ (after)"])
    plt.tight_layout()
    return _save(plt.gcf(), out)


def fig_h2_timeseries(ts: pd.DataFrame, leads: pd.DataFrame, out: Path | None = None) -> Path:
    """그림 8 — 사례별 개념 vs 코드 출원 시계열 (§4.4).

    개념 실선 · 코드 점선 · 탐지연도 마커. 관측창 밖(2024–2025)은 18개월 비공개
    절단이라 제외했다. 코드가 CPC 전용이라 IPC 말뭉치에 없는 사례는 제목에 명시한다.
    """
    out = out or FIGURES / "fig8_h2_timeseries.svg"
    # ts·leads 는 scheme(ipc/cpc)별로 중복된다 — 한 스킴만 그린다(개념 vs 코드 IPC).
    cases = list(dict.fromkeys(leads["case_id"]))
    ncol = 4
    nrow = (len(cases) + ncol - 1) // ncol
    fig, axes = plt.subplots(nrow, ncol, figsize=(4 * ncol, 3.5 * nrow), sharex=True)
    for ax, case_id in zip(axes.flat, cases, strict=False):
        row = leads[leads["case_id"] == case_id].iloc[0]
        m = ts["case_id"] == case_id
        if "scheme" in ts:
            m &= ts["scheme"] == row["scheme"]
        sub = ts[m].pivot(index="year", columns="kind", values="n")
        if "concept" in sub:
            ax.plot(sub.index, sub["concept"], "-", color=TOBE, label="concept (ontology)")
        if "code" in sub:
            ax.plot(sub.index, sub["code"], "--", color=ASIS, label="code (CPC/IPC)")
        for kind, year, col in (("concept", row["concept_year"], TOBE),
                                ("code", row["code_year"], ASIS)):
            if pd.notna(year) and kind in sub and int(year) in sub.index:
                ax.axvline(int(year), ls=":", lw=0.8, color=col)
                ax.plot(int(year), sub.loc[int(year), kind], "o", ms=6, color=col)
        zero = " — code absent (CPC-only)" if row["code_total"] == 0 else ""
        ax.set_title(f"{case_id} · {row['control_code']}{zero}", fontsize=9)
        ax.set_ylabel("filings")
    for ax in axes.flat[len(cases):]:
        ax.axis("off")
    axes.flat[0].legend(fontsize=8)
    fig.suptitle("H2 — concept-unit vs code-unit filing series (2010–2023; 2024–25 truncated)")
    plt.tight_layout()
    return _save(fig, out)


# ═══════════════════════════════════════════════════════════════════════════
def main() -> None:
    """CSV·상수에서 논문 그림 전량을 SVG 로 결정적으로 재생성한다."""
    made: list[Path] = []
    for fn in (fig_gap_map, fig_evolution, fig_research_model, fig_pipeline,
               fig_vacuous_gate, fig_traps, fig_rq3_portability, fig_summary_matrix):
        made.append(fn())
    h1 = pd.read_csv(PROCESSED / "h1_coverage.csv")
    made.append(fig_coverage_gap(h1))
    made.append(fig_h1_coverage(h1))
    ts = pd.read_csv(PROCESSED / "h2_timeseries.csv")
    leads = pd.read_csv(PROCESSED / "h2_leadtime.csv")
    made.append(fig_h2_timeseries(ts, leads))
    for p in made:
        print(f"  ✓ {p.relative_to(FIGURES.parents[1])}")
    print(f"{len(made)} figures → {FIGURES}")


if __name__ == "__main__":
    main()
