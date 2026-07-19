"""논문 그림은 전부 이 모듈이 생성한다 → paper/figures/ (수작업 그림 금지).

두 갈래다.
1. **서사 도식**(fig_gap_and_model · fig_pipeline · fig_vacuous_gate ·
   fig_rq3_portability · fig_summary_matrix) — 논문의 주장 흐름을 나른다.
   수치는 **v0.5 §6 의 표**에서 확정된 실측값이며 여기서는 시각화만 한다.
2. **데이터 플롯**(fig_h1_coverage · fig_h2_name_arm · fig_h2_timeseries) — analysis
   산출 CSV(`data/processed/`)를 그린다.

출력은 전부 **SVG**다. `make figures` 하나가 CSV·상수에서 전량을 결정적으로 재생성한다.

**본문 그림은 6장이다 (AEI 25페이지 감축 재편 · 2026-07-19).** 그림만 순서대로 읽어도
갭 → 방법 → 검증 발견 → 결과(H1·H2) → 이식성이 이어지도록 배치한다.
그림 1 `fig1_gap_map`(갭+연구 모형) · 그림 2 `fig4_pipeline` · 그림 3 `fig6_vacuous_gate` ·
그림 4 `fig7_h1_coverage` · 그림 5 `fig8_h2_timeseries`(H2 시계열+세 함정) ·
그림 6 `fig10_rq3_portability`. `fig11_summary` 는 본문이 아니라 **그래픽 초록**이다.
구 fig2(진화)·fig3(모형+파이프라인)·fig5(G₀ 편중)·fig9(함정 단독)는 생성하지 않는다 —
진화는 본문 서술로, 모형은 그림 1 로, G₀ 편중은 그림 4 의 before 막대로, 함정은 그림 5 의
하단 패널로 흡수됐다.

**파일명 figN 과 원고 본문의 [그림 n] 은 일치하지 않는다 — 정상이다.** 파일명은 v0.3 산출물
명칭을 유지한다. 지금 파일명을 바꾸면 이 모듈·표 대응·원고 참조가 동시에 흔들린다.
번호 정렬은 **최종 조판 시**.
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
# **순서가 중요하다 — Noto 가 먼저다.** NanumGothic 은 U+2192(→)를 cmap 에 갖고 있으면서
# 정체(regular) 자형이 깨져 있어 화살표가 두부(▯)로 찍힌다. 굵은체는 Nanum 에 볼드 페이스가
# 없어 DejaVu 로 폴백되므로 멀쩡히 나오고, 그래서 **제목은 정상인데 본문만 깨지는** 형태로
# 드러났다(감사 2026-07-18 · 그림 9 의 "커버 20 → 26"). Noto 를 앞에 두면 정체에서도 옳게 나온다.
_FONT_FILES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
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
    _blank(ax)
    return fig, ax


def _blank(ax):
    """패널 하나를 0–1 정규좌표의 빈 도화지로 만든다.

    v0.5 가 그림 둘을 하나로 합치면서 도식 함수는 **패널에 그리는 것**이 되었다 —
    도식마다 자기 figure 를 만들면 합칠 수가 없다. 좌표계를 패널마다 0–1 로 고정해
    기존 도식 코드를 그대로 재사용한다.
    """
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    return ax


def _stack(w: float, h: float, ratios: list[float]):
    """세로로 쌓인 패널들. 통합 그림(그림 2·9)의 뼈대다."""
    fig, axes = plt.subplots(len(ratios), 1, figsize=(w, h),
                             gridspec_kw={"height_ratios": ratios})
    for ax in axes:
        _blank(ax)
    return fig, axes


def _save(fig, out: Path) -> Path:
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


# ═══════════════════════════════════════════════════════════════════════════
# 서사 도식
# ═══════════════════════════════════════════════════════════════════════════
def _draw_gap_map(ax) -> None:
    """연구 갭 — 세 AS-IS를 세 TO-BE로 (§2.4). **그림 1 의 위 패널.**

    감축 재편(2026-07-19)에서 요약 그림의 위 절반에서 그림 1 로 옮겨 왔다 — "그림만
    이어 봐도 신규성 주장이 보여야 한다"는 요구에서 갭 도식이 결론에 가 있으면
    독자가 신규성을 마지막에야 만난다. 갭은 논문의 첫 그림이어야 한다.
    """
    ax.text(0.5, 0.965, "(a) 연구 갭 — 세 개의 AS-IS를 세 개의 TO-BE로",
            ha="center", va="top", fontsize=14, fontweight="bold", color=INK)
    ax.text(0.5, 0.905, "각 갭은 본 연구의 독립적 방법론 기여로 대응된다",
            ha="center", va="top", fontsize=9.5, color=MUTE)
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


def _draw_research_model(ax) -> None:
    """연구 모형 — 보강 처치 → 게이트 → 태스크 성능 (§5.1). **그림 1 의 아래 패널.**"""
    ax.text(0.5, 0.95, "(b) 연구 모형 — 보강 처치 → 품질 게이트 → 태스크 성능",
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
    ax.text(0.945, 0.335, "종속변수", ha="center", fontsize=8.5, color=MUTE)


def _draw_pipeline(ax) -> None:
    """검증 게이트 내장 보강 파이프라인 (§4). **그림 2**(단독)의 본체."""
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
    # 10,342 = 실제 L1 탈락. 프로파일의 10,456 은 **룰 경로만** 센 값이라 신기술 인식층
    # (별칭·조합 정의)이 잡은 114건을 탈락으로 오계상한다 (감사 2026-07-18 · N1 해소).
    _rbox(ax, 0.45, 0.06, 0.28, 0.18, "L1에서 탈락", "개념 매핑 없는 델타 10,342건 (30.0%)",
          ASIS_FILL, ASIS_EDGE, ASIS, 11, 8.5)
    _arrow(ax, 0.72, y - 0.021, 0.62, 0.245, ASIS, 2.0)
    ax.text(0.50, 0.34, "게이트 판별력\n(RQ1)", ha="center", fontsize=8,
            color=ASIS, fontweight="bold")


def fig_gap_and_model(out: Path | None = None) -> Path:
    """**그림 1** — (a) 연구 갭 + (b) 연구 모형 (감축 재편 2026-07-19).

    "무엇이 없었는가"와 "그 공백을 어떤 설계로 메우는가"가 논문의 첫 그림에서
    한 번에 읽힌다. 구 `fig3_research_model.svg`(모형+파이프라인)는 생성하지 않는다 —
    모형은 여기로, 파이프라인은 그림 2(`fig4_pipeline.svg`)로 갈라졌다.
    """
    out = out or FIGURES / "fig1_gap_map.svg"
    fig, axes = _stack(11.8, 11.2, [1.25, 1.0])
    _draw_gap_map(axes[0])
    _draw_research_model(axes[1])
    plt.tight_layout()
    return _save(fig, out)


def fig_pipeline(out: Path | None = None) -> Path:
    """**그림 2** — 검증 게이트 내장 보강 파이프라인 (§4)."""
    out = out or FIGURES / "fig4_pipeline.svg"
    fig, ax = _canvas(11.8, 5.2)
    _draw_pipeline(ax)
    return _save(fig, out)


def fig_vacuous_gate(out: Path | None = None) -> Path:
    """**그림 3** — 공허한 게이트: 응답률은 세 CQ 집합을 구별하지 못한다 (§6.2).

    수치는 §6.2 표(`make vocab` · 실사용 술어 54 · 클래스 25) 확정값이다.
    """
    out = out or FIGURES / "fig6_vacuous_gate.svg"
    fig, ax = plt.subplots(figsize=(9.5, 5.4))
    groups = ["CQ 응답률", "술어 커버리지", "클래스 커버리지"]
    sets = [
        ("K=8 (손으로 선정)", [100.0, 9.3, 16.0], "#B0B7C3", "#8A93A3"),
        ("K=14 (태스크 도출)", [100.0, 31.5, 28.0], TOBE, "#1E4E82"),
        ("K=27 (전 배터리)", [96.3, 66.7, 72.0], GREEN, "#1F5C40"),
    ]
    x = list(range(len(groups)))
    w = 0.26
    for k, (label, vals, fc, ec) in enumerate(sets):
        bars = ax.bar([i + (k - 1) * w for i in x], vals, w, label=label,
                      color=fc, edgecolor=ec)
        for r in bars:
            if r.get_height() >= 100:  # 100% 막대는 라벨 생략 (범례·밴드와 겹침)
                continue
            ax.text(r.get_x() + r.get_width() / 2, r.get_height() + 1.5,
                    f"{r.get_height():.1f}", ha="center", fontsize=8.5, color=INK)
    ax.axhspan(95, 103, color=ASIS_FILL, zorder=0)
    ax.text(2.44, 99, "응답률은 좁은 집합을\n벌하지 못한다\n(넓은 쪽만 96.3)", ha="center",
            va="center", fontsize=8.5, color=ASIS, fontweight="bold")
    ax.set_ylim(0, 112)
    ax.set_xticks(x)
    ax.set_xticklabels(groups, fontsize=10)
    ax.set_ylabel("백분율 (%)")
    ax.set_title("공허한 게이트 — 응답률만 보면 어휘의 9%를 만지는 CQ 집합과\n"
                 "67%를 만지는 집합이 구별되지 않는다",
                 fontsize=12, fontweight="bold")
    ax.legend(loc="upper left", framealpha=0.9)
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    return _save(fig, out)


def _draw_traps(ax) -> None:
    """개념 단위 조기탐지 측정의 세 함정과 회피 설계 (§6.4). **그림 5 의 아래 패널.**

    감축 재편(2026-07-19)에서 단독 그림(구 fig9)에서 H2 시계열의 하단 패널로 흡수됐다 —
    함정은 곧 "그림 5 위 패널의 시계열을 왜 이 설계로 읽어야 하는가"이므로 결과와
    같은 자리에서 읽혀야 한다.
    """
    ax.text(0.5, 1.08, "(b) 개념 단위 조기탐지의 세 함정 — 규명하고 회피한다",
            ha="center", va="bottom", fontsize=13, fontweight="bold", color=INK)
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
        ax.text(x + ww / 2, 0.92, f"함정 {i + 1} · {t}", ha="center", va="center",
                fontsize=11.5, fontweight="bold", color=INK)
        _rbox(ax, x, 0.46, ww, 0.34, "증상 (AS-IS)", asis,
              ASIS_FILL, ASIS_EDGE, ASIS, 9.5, 9, "left")
        _arrow(ax, x + ww / 2, 0.455, x + ww / 2, 0.40, GREEN, 2.2)
        _rbox(ax, x, 0.04, ww, 0.34, "회피 (TO-BE)", tobe,
              GREEN_FILL, GREEN, GREEN, 9.5, 9, "left")


def fig_rq3_portability(out: Path | None = None) -> Path:
    """**그림 6** — RQ3 이식성: 폭은 포화, 깊이가 갈린다 (§6.6).

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


def _draw_summary_matrix(ax) -> None:
    """결과 한 장 요약 — RQ ↔ 가설 ↔ 판정 ↔ 검증 방식 (§7.1). **그래픽 초록의 본체.**

    근거 열에 그림·표 번호를 굽지 않는다(CLAUDE.md §7) — 그래픽 초록은 본문 밖에서
    단독으로 읽히므로 본문 번호는 여기서 무의미하고, 조판에서 고칠 수도 없다.
    대신 검증 방식(무엇으로 확인했는가)을 적는다.
    """
    ax.text(0.5, 0.95, "결과 요약 — 세 질문, 세 답",
            ha="center", va="top", fontsize=14, fontweight="bold", color=INK)
    cols = ["", "질문", "가설·판정", "핵심 수치", "검증 방식"]
    xw = [0.06, 0.24, 0.26, 0.24, 0.16]
    xs = [0.02]
    for w in xw[:-1]:
        xs.append(xs[-1] + w)
    rows = [
        ("RQ1", "게이트가 정합성 훼손 델타를 거부하며\n커버리지를 확장하는가",
         "H1 지지\n(단측 Wilcoxon)", "커버 20 → 26 / 49\np = 4.8×10⁻⁷", "커버리지 검정\n4개 표본집합"),
        ("RQ2", "코드·이름 없는 국면을\n표현·조기탐지하는가",
         "H2 능력 존재 증명\n(유의성 아님)", "HBM 개념 2009\nvs 명칭 2020 (11년차)",
         "10사례 시계열\n+ 진단 D1·D2"),
        ("RQ3", "프레임워크가 코퍼스를 바꿔도\n재현되는가 (이식성)",
         "H1 소부장서도 지지\n세 층 모두", "폭 26 포화\n깊이 236 → 573", "층별 재검정\nCQ 27/27"),
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


def fig_summary_matrix(out: Path | None = None) -> Path:
    """**그래픽 초록** — 결과 한 장 요약 (본문 그림 아님 · 감축 재편 2026-07-19).

    갭 맵은 그림 1 로 옮겨 갔고, 이 파일은 AEI 제출물의 graphical abstract 가 된다 —
    본문 페이지를 쓰지 않으면서 결과 요약을 유지하는 자리다. 파일명은 선행 파일명
    (`fig11_summary.svg`)을 유지한다.
    """
    out = out or FIGURES / "fig11_summary.svg"
    fig, ax = _canvas(12.0, 5.4)
    _draw_summary_matrix(ax)
    return _save(fig, out)


# ═══════════════════════════════════════════════════════════════════════════
# 데이터 플롯 (data/processed CSV)
# ═══════════════════════════════════════════════════════════════════════════
def fig_h1_coverage(df: pd.DataFrame, out: Path | None = None) -> Path:
    """**그림 4** — H1: 공정 단계별 커버리지 G₀ vs G₁ (§6.3).

    복원 이전 20개 단계를 레이블 * 로 표시한다 — 복원 단계는 G₀ 에서 0 이라 H1 에
    유리하므로 어느 막대가 그쪽인지 그림에서 바로 보여야 한다.
    구 fig5(G₀ 편중 단독)는 생성하지 않는다 — before 막대가 같은 사실을 말한다
    (감축 재편 2026-07-19).
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


def fig_h2_name_arm(ts: pd.DataFrame, leads: pd.DataFrame, out: Path | None = None) -> Path:
    """**그림 5** — (a) 개념 vs 명칭 시계열 10사례 + (b) 세 함정 (§6.4 · 주논증 C).

    이 자리에는 오래도록 **코드 팔**(개념 vs 코드 · 7사례)이 걸려 있었다. 그런데 §6.4 는
    코드 대조군을 소급 재분류 때문에 무효로 선언하고 **진단 D1** 으로 강등했다 — 주논증이
    아닌 축이 주논증의 그림 자리를 차지하고 있었고, 정작 논증 C(10사례)에는 그림이 없었다.
    표는 10사례인데 그림은 7사례였다 (감사 2026-07-18 · S5).

    명칭 대조군이 옳은 상대인 이유: 명세 텍스트는 **소급 재작성되지 않는다.** 2010년 특허의
    초록은 지금도 2010년의 초록이다. 개념 정의는 `si_struct`(명칭 용어를 뺀 구조 전용)라
    대조군과 **서로소**이므로, 개념 ⊇ 이름의 자명성이 결론을 만들지 않는다.

    감축 재편(2026-07-19)에서 세 함정 도식(구 fig9)이 (b) 패널로 들어왔다 — (a) 의
    대조군·정의·관측창 선택이 전부 (b) 의 회피 설계이므로 한 장에서 읽혀야 한다.
    """
    out = out or FIGURES / "fig8_h2_timeseries.svg"
    order = ["concept_first", "tie", "name_first"]
    leads = leads.copy()
    leads["_rank"] = leads["outcome"].map({k: i for i, k in enumerate(order)}).fillna(9)
    # 판정군 안에서는 리드가 큰 순 — 논증의 무게 순으로 읽히게 한다(3D NAND ≥14 · HBM 11 …).
    # case_id 를 동점 타이브레이커로 두어 정렬은 결정적이다.
    leads = leads.sort_values(["_rank", "lead", "case_id"], ascending=[True, False, True])
    cases = list(leads["case_id"])

    ncol = 5
    nrow = (len(cases) + ncol - 1) // ncol
    fig = plt.figure(figsize=(3.5 * ncol, 3.1 * nrow + 3.3))
    gs = fig.add_gridspec(2, 1, height_ratios=[3.1 * nrow, 3.0], hspace=0.30)
    gs_ts = gs[0].subgridspec(nrow, ncol, hspace=0.42)
    axes = [fig.add_subplot(gs_ts[k // ncol, k % ncol]) for k in range(len(cases))]
    for ax, case_id in zip(axes, cases, strict=True):
        row = leads[leads["case_id"] == case_id].iloc[0]
        sub = ts[ts["case_id"] == case_id].pivot(index="year", columns="kind", values="n")
        for kind, style, color, label in (
            ("concept", "-", TOBE, "개념 (구조 조합)"),
            ("name", "--", ASIS, "명칭 키워드"),
        ):
            if kind in sub:
                ax.plot(sub.index, sub[kind], style, color=color, lw=1.8, label=label)
        for kind, year, color in (("concept", row["concept_year"], TOBE),
                                  ("name", row["name_year"], ASIS)):
            if pd.notna(year) and kind in sub and int(year) in sub.index:
                ax.axvline(int(year), ls=":", lw=0.8, color=color)
                ax.plot(int(year), sub.loc[int(year), kind], "o", ms=6, color=color)
        # 미탐지는 빈칸으로 두지 않는다 — "명칭이 끝내 잡지 못했다"가 결과의 일부다.
        verdict = {"concept_first": "개념 우선", "tie": "동점",
                   "name_first": "명칭 우선"}.get(row["outcome"], row["outcome"])
        lead = row["lead"]
        if pd.notna(lead):
            verdict += f" · {'≥' if row['lead_is_lower_bound'] else '+'}{int(lead)}년"
        if pd.isna(row["name_year"]):
            verdict += " (명칭 미탐지)"
        color = {"concept_first": TOBE, "tie": MUTE}.get(row["outcome"], ASIS)
        ax.set_title(f"{case_id}\n{verdict}", fontsize=9.5, color=color, fontweight="bold")
        ax.set_ylabel("출원 건수", fontsize=8)
        ax.tick_params(labelsize=7.5)
        # 연도는 정수다 — 기본 로케이터는 2007.5 같은 눈금을 찍는다.
        ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(5))
        ax.xaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%d"))
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].legend(fontsize=8)
    traps_ax = fig.add_subplot(gs[1])
    _blank(traps_ax)
    _draw_traps(traps_ax)
    fig.suptitle(
        "(a) H2 (주논증 C) — 개념(구조 조합) vs 명칭 키워드 조기탐지 · 사전 확정 10사례\n"
        "구조가 이름과 진짜로 다른 곳에서 개념은 한 번도 지지 않는다 (2005–2023)",
        fontsize=12.5, fontweight="bold",
    )
    return _save(fig, out)


def fig_h2_timeseries(ts: pd.DataFrame, leads: pd.DataFrame, out: Path | None = None) -> Path:
    """**진단 D1** — 사례별 개념 vs **코드** 출원 시계열 (§6.4 · 본문 그림 번호 없음).

    이 팔은 가설이 아니다. 코드 대조군의 **시간적 무효성**(H10 스킴 전량 소급 재분류 ·
    당시 스냅샷 해상도 바닥 2017)을 보이는 진단이고, 검정력을 요구하지 않는다.

    개념 실선 · 코드 점선 · 탐지연도 마커. 관측창 밖(2024–2025)은 18개월 비공개
    절단이라 제외했다. 코드가 CPC 전용이라 IPC 말뭉치에 없는 사례는 제목에 명시한다.
    """
    out = out or FIGURES / "fig8c_h2_code_arm_d1.svg"
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
    for fn in (fig_gap_and_model, fig_pipeline,
               fig_vacuous_gate, fig_rq3_portability, fig_summary_matrix):
        made.append(fn())
    h1 = pd.read_csv(PROCESSED / "h1_coverage.csv")
    made.append(fig_h1_coverage(h1))
    # 그림 5 = 주논증 C(명칭 팔) + 세 함정 패널. 코드 팔은 진단 D1 로만 남는다 —
    # 두 팔은 사례 집합도 대조군도 다르므로 각자의 CSV 에서 그린다 (감사 2026-07-18 · S5).
    made.append(fig_h2_name_arm(
        pd.read_csv(PROCESSED / "h2_name_timeseries.csv"),
        pd.read_csv(PROCESSED / "h2_name_leadtime.csv"),
    ))
    made.append(fig_h2_timeseries(
        pd.read_csv(PROCESSED / "h2_timeseries.csv"),
        pd.read_csv(PROCESSED / "h2_leadtime.csv"),
    ))
    for p in made:
        print(f"  ✓ {p.relative_to(FIGURES.parents[1])}")
    print(f"{len(made)} figures → {FIGURES}")


if __name__ == "__main__":
    main()
