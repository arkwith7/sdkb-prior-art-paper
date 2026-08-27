"""개념 도식 — 산출물 구조와 층간 지표 불일치 (그림 규격 [F-v1](../../../paper/FIGURE-SPEC.md)).

**왜 별도 모듈인가.** `figures.py` 는 v0.5 패러다임의 서사 도식과 v0.9 데이터 플롯을 함께
갖고 있고, 그 서사 도식은 **구 패러다임 산출물이라 인용이 금지**돼 있다(CLAUDE.md 정본 회귀).
그 파일에 새 개념 그림을 섞으면 살아 있는 그림과 죽은 그림이 한 파일에서 구분되지 않는다.
**스타일 헬퍼는 재사용하고 내용만 새로 세운다** — 두 갈래가 한 벌로 읽혀야 하기 때문이다.

여기의 네 장은 논문 앞부분(서론·이론적 배경·산출물)이 지고 있던 시각 자료 공백을 메운다.

- `fig_overview` — 산출물 셋과 승인 절차, 그리고 네 평가 에피소드가 측정하는 지점.
- `fig_layer_mismatch` — 세 층의 지표와 층 사이에서 실제로 관측된 어긋남 셋.
- `fig_tbox_views` — 공유 T-Box 위의 세 태스크 뷰와 교차 태스크 결합 통로 (표 하나를 대체).
- `fig_gate_flow` — 승인 절차와 각 항의 미충족 시 처리, 그리고 실제 판정 (표 하나를 대체).

**수치는 한 개도 이 파일에 적혀 있지 않다**(규격 F6) — 전부 `figdata.load()` 가 동결
JSON 에서 읽어 오며, 그 JSON 은 산출물에서 기계로 추출된다.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from sdkb_paper.config import FIGURES
from sdkb_paper.viz import figdata, labels
from sdkb_paper.viz.labels import T
from sdkb_paper.viz.figures import (
    ASIS,
    ASIS_EDGE,
    ASIS_FILL,
    BORDER,
    GOLD,
    GREEN,
    GREEN_FILL,
    INK,
    MUTE,
    TOBE,
    TOBE_EDGE,
    TOBE_FILL,
    _arrow,
    _canvas,
    _chip,
    _fit_text,
    _rbox,
    _save,
)

# 단색 인쇄 안전 (규격 F1) — 색은 보조 부호이고 판정은 기호가 진다.
# 기호도 언어를 탄다 — 값은 `labels.MARKS` 가 지고 여기서는 현재 언어의 것을 읽는다.
def _ko_width(ax, key: str, fontsize: float, **extra) -> float:
    """한국어판이 그 자리에서 실제로 쓰는 폭 — 상자가 없는 자리의 경계다."""
    from sdkb_paper.viz.figures import _text_width
    from sdkb_paper.viz.labels import ko_of
    return _text_width(ax, ko_of(key, **extra), fontsize)


def _mark(name: str) -> str:
    from sdkb_paper.viz.labels import MARKS, lang
    return MARKS[name][lang()]


def _sig(v: float, nd: int = 4) -> str:
    """부호를 명시한 소수 표기. 음수는 유니코드 마이너스로 — 본문 표기와 같게 맞춘다."""
    s = f"{abs(v):.{nd}f}"
    return f"+{s}" if v >= 0 else f"−{s}"


# ═══════════════════════════════════════════════════════════════════════════
# 그림 1 — 연구 개요도
# ═══════════════════════════════════════════════════════════════════════════
def fig_overview(out: Path | None = None) -> Path:
    """산출물 셋 · 승인 절차 · 평가 에피소드의 측정 지점을 한 장에 담는다.

    읽는 순서는 위에서 아래다. 위 띠가 **무엇을 만들었는가**(A1), 가운데 띠가 **변경을
    어떻게 승인하는가**(A2), 아래 띠가 **그 둘을 무엇으로 평가하였는가**(A3)이다.
    """
    out = out or FIGURES / "concept_overview.svg"
    fig, ax = _canvas(11.0, 6.6)

    # ── A1 · 산출물 자원 (위 띠) ──────────────────────────────────────────────
    _rbox(ax, 0.035, 0.715, 0.60, 0.245,
          title=T("overview.a1_title"),
          body="", fill="#FFFFFF", edge=BORDER, ts=11)
    _fit_text(ax, 0.058, 0.855, T("overview.core_head"), 0.560, where="그림1 코어 제목",
              ha="left", va="center", fontsize=9, fontweight="bold", color=MUTE)
    _fit_text(ax, 0.058, 0.826, T("overview.core_body"), 0.560, where="그림1 코어 본문",
              ha="left", va="center", fontsize=8.2, color=MUTE)
    for x, key, color, fill in (
        (0.170, "overview.view_match", MUTE, "#F1F3F6"),
        (0.350, "overview.view_priorart", TOBE, TOBE_FILL),
        (0.530, "overview.view_foresight", MUTE, "#F1F3F6"),
    ):
        _chip(ax, x, 0.772, T(key), color=color, fill=fill)
    ax.text(0.350, 0.737, T("overview.quant_target"), ha="center", va="center",
            fontsize=7.6, color=TOBE)

    # 변경 유입 — 자원은 고정된 것이 아니라 갱신된다.
    _rbox(ax, 0.680, 0.740, 0.285, 0.190,
          title=T("overview.delta_title"), body=T("overview.delta_body"),
          fill="#FFFFFF", edge=BORDER, ts=10.5, bs=8.4)
    _arrow(ax, 0.822, 0.735, 0.822, 0.625, color=INK, lw=1.8)

    # ── A2 · 승인 게이트 (가운데 띠) ─────────────────────────────────────────
    _rbox(ax, 0.035, 0.330, 0.930, 0.290, title="", body="",
          fill="#FBFCFD", edge=BORDER)
    _fit_text(ax, 0.055, 0.585, T("overview.a2_title"), 0.900, where="그림1 A2 제목",
              ha="left", va="center", fontsize=11, fontweight="bold", color=INK)

    stages = [
        (0.055, 0.200, T("overview.stage_l0l3"), T("overview.stage_l0l3_body"),
         "#FFFFFF", BORDER, INK),
        (0.288, 0.170, T("overview.stage_index"), T("overview.stage_index_body"),
         "#FFFFFF", BORDER, INK),
        (0.491, 0.195, T("overview.stage_t12"), T("overview.stage_t12_body"),
         TOBE_FILL, TOBE_EDGE, TOBE),
        (0.719, 0.140, T("overview.stage_t3"), T("overview.stage_t3_body"),
         TOBE_FILL, TOBE_EDGE, TOBE),
        (0.892, 0.073, T("overview.stage_verdict"), T("overview.stage_verdict_body"),
         GREEN_FILL, GREEN, GREEN),
    ]
    for x, w, title, body, fill, edge, tcolor in stages:
        _rbox(ax, x, 0.395, w, 0.150, title=title, body=body,
              fill=fill, edge=edge, tcolor=tcolor, ts=10, bs=8.2)
    for x1, x2 in ((0.259, 0.285), (0.461, 0.488), (0.689, 0.716),
                   (0.862, 0.889)):
        _arrow(ax, x1, 0.470, x2, 0.470, color=INK, lw=1.6, ms=12)

    # T4 는 승인식 밖이다 — 점선과 별도 자리가 그 지위를 진다(§4.5.1).
    ax.annotate("", xy=(0.928, 0.372), xytext=(0.928, 0.393),
                arrowprops=dict(arrowstyle="-|>", linestyle=(0, (3, 2)),
                                color=GOLD, lw=1.4))
    _fit_text(ax, 0.916, 0.352, T("overview.t4_note"), 0.880, where="그림1 T4 주석",
              ha="right", va="center", fontsize=8, color=GOLD)

    # ── A3 · 평가 벤치마크 (아래 띠) ─────────────────────────────────────────
    # **화살표를 쓰지 않는다.** 다섯 에피소드의 측정 대상이 위 두 띠에 흩어져 있어 선으로
    # 이으면 교차가 생기고, 교차한 선은 단색 인쇄에서 읽히지 않는다(규격 F1). 대상은
    # 상자 안의 한 줄이 지시한다.
    _fit_text(ax, 0.055, 0.262, T("overview.a3_title"), 0.900, where="그림1 A3 제목",
              ha="left", va="center", fontsize=11, fontweight="bold", color=INK)
    # 다섯째 상자의 아래 줄은 **검출 수가 아니라 관찰면**이다. 분모가 없는 0 을 적으면
    # 그림이 "게이트가 놓쳤다"고 말하게 된다(§0.8 판정 문구 사전과 같은 규율).
    episodes = [(0.128, "ep1"), (0.314, "ep2"), (0.500, "ep3"),
                (0.686, "ep4"), (0.872, "ep5")]
    for x, ep in episodes:
        _rbox(ax, x - 0.089, 0.045, 0.178, 0.170, title=T(f"overview.{ep}_title"),
              body="", fill="#FFFFFF", edge=BORDER, ts=8.4)
        _fit_text(ax, x, 0.148,
                  T("overview.ep_target", target=T(f"overview.{ep}_target")),
                  0.170, where=f"그림1 {ep} 측정 대상",
                  ha="center", va="center", fontsize=7.2, fontweight="bold", color=TOBE)
        _fit_text(ax, x, 0.092, T(f"overview.{ep}_body"), 0.170,
                  where=f"그림1 {ep} 본문",
                  ha="center", va="center", fontsize=7.0, color=MUTE, linespacing=1.45)
    return _save(fig, out)


# ═══════════════════════════════════════════════════════════════════════════
# 그림 2 — 3층 지표 구조와 층간 불일치
# ═══════════════════════════════════════════════════════════════════════════
LAYER_H = 0.185
OBS_H = 0.215


def _layer(ax, y: float, tag: str, title: str, body: str, fill: str, edge: str) -> None:
    _rbox(ax, 0.045, y, 0.40, LAYER_H, title=title, body=body,
          fill=fill, edge=edge, ts=10.5, bs=8.4, align="left")
    ax.text(0.033, y + LAYER_H / 2, tag, ha="right", va="center", fontsize=9,
            fontweight="bold", color=MUTE, rotation=90)


def _observation(ax, y: float, num: str, head: str, body: str,
                 status: str, color: str, fill: str, edge: str) -> None:
    """오른쪽 관측 칸 — 어긋남 하나. `status` 는 확증 지위를 그림 안에서 명시한다."""
    _rbox(ax, 0.520, y, 0.455, OBS_H, title=f"{num} {head}", body=body,
          fill=fill, edge=edge, tcolor=color, ts=9.6, bs=8.2, align="left")
    _fit_text(ax, 0.966, y + 0.014, T("common.status_prefix", status=status), 0.440,
              where="그림2 지위", ha="right", va="bottom",
              fontsize=7.6, style="italic", color=MUTE)


def fig_layer_mismatch(out: Path | None = None) -> Path:
    """세 층의 지표와 그 사이에서 관측된 어긋남 셋 — 본 연구의 중심 관측(§7.5).

    왼쪽이 층의 구조이고 오른쪽이 각 층 사이에서 실제로 관측된 결과다. 층 사이의 화살표에
    붙은 번호가 오른쪽 관측 번호와 대응한다.
    """
    out = out or FIGURES / "concept_layer_mismatch.svg"
    fig, ax = _canvas(11.0, 7.2)

    # ── 왼쪽 · 세 층 ─────────────────────────────────────────────────────────
    _layer(ax, 0.770, T("layer.tag_resource"), T("layer.title_resource"),
           T("layer.body_resource"), fill="#FFFFFF", edge=BORDER)
    _layer(ax, 0.430, T("layer.tag_retrieval"), T("layer.title_retrieval"),
           T("layer.body_retrieval"), fill=TOBE_FILL, edge=TOBE_EDGE)
    _layer(ax, 0.090, T("layer.tag_generation"), T("layer.title_generation"),
           T("layer.body_generation"), fill="#FFFFFF", edge=BORDER)

    # ── 층 사이 화살표 ───────────────────────────────────────────────────────
    for y1, y2, num, note in (
        (0.765, 0.622, "①", T("layer.arrow_1")),
        (0.425, 0.282, "③", T("layer.arrow_3")),
    ):
        _arrow(ax, 0.135, y1, 0.135, y2, color=INK, lw=1.8)
        ax.text(0.120, (y1 + y2) / 2, num, ha="right", va="center",
                fontsize=11, fontweight="bold", color=INK)
        _fit_text(ax, 0.160, (y1 + y2) / 2, note, 0.340, where="그림2 화살표 주석",
                  ha="left", va="center", fontsize=8, color=MUTE)

    # ② 는 층이 아니라 같은 층의 다른 단위다 — 옆으로 뻗는다.
    _arrow(ax, 0.450, 0.523, 0.512, 0.523, color=INK, lw=1.6, ms=12)
    ax.text(0.481, 0.548, "②", ha="center", va="bottom", fontsize=10,
            fontweight="bold", color=INK)

    # ── 오른쪽 · 관측된 어긋남 셋 ────────────────────────────────────────────
    _observation(ax, 0.765, "①", T("layer.obs1_head"), T("layer.obs1_body"),
                 T("layer.obs1_status"), ASIS, ASIS_FILL, ASIS_EDGE)
    _observation(ax, 0.425, "②", T("layer.obs2_head"), T("layer.obs2_body"),
                 T("layer.obs2_status"), GOLD, "#FBF3E4", "#DCC08A")
    _observation(ax, 0.085, "③", T("layer.obs3_head"), T("layer.obs3_body"),
                 T("layer.obs3_status"), ASIS, ASIS_FILL, ASIS_EDGE)

    # ── 결론 띠 ──────────────────────────────────────────────────────────────
    _fit_text(ax, 0.5, 0.022, T("layer.conclusion"), 0.940, where="그림2 결론 띠",
              ha="center", va="center", fontsize=9.4, fontweight="bold", color=INK,
              bbox=dict(boxstyle="round,pad=0.5", fc="#F7F9FB", ec=BORDER, lw=1.0))
    return _save(fig, out)


# ═══════════════════════════════════════════════════════════════════════════
# 그림 3 — 공유 T-Box와 세 태스크 뷰
# ═══════════════════════════════════════════════════════════════════════════
def _terms(cell: str, per_line: int) -> str:
    """표의 어휘 칸(백틱·가운뎃점 구분)을 그림용 여러 줄로 접는다."""
    items = [t.strip().strip("`") for t in cell.split("·") if t.strip()]
    lines = ["·".join(items[i:i + per_line]) for i in range(0, len(items), per_line)]
    return "\n".join(lines)


def _plain(cell: str) -> str:
    """표 칸의 마크다운 강조와 절 참조를 걷어낸다.

    절 번호를 그대로 옮기지 않는 이유는 하나다 — 출처가 축약 전 전문(S5)이라 그 번호는
    파생본의 절 번호와 다르다. 그림이 죽은 참조를 나르면 `submission-check` 가 잡지 못한다.
    """
    return re.sub(r"\s*\(§[^)]*\)", "", cell.replace("**", "")).strip()


def _status(cell: str) -> str:
    """지위 칸에서 괄호 보충을 걷어낸다 — 상자 폭에 들어가지 않으면 다른 칸을 침범한다."""
    return re.sub(r"\s*\([^)]*\)", "", _plain(cell)).strip()


def fig_tbox_views(out: Path | None = None) -> Path:
    """공유 T-Box 하나 위의 세 태스크 뷰와 교차 태스크 결합 통로.

    이 그림은 세 뷰의 지위표를 대체한다. 표가 보여주지 못하던 것을 보여주기 때문이다 —
    세 뷰는 배타적 모듈이 아니라 공유 어휘를 통해 서로 이어져 있으며, 그 이어짐이 교차
    태스크 회귀가 실재하는 이유이다.
    """
    out = out or FIGURES / "concept_tbox_views.svg"
    v = figdata.load()
    fig, ax = _canvas(11.0, 6.8)

    views = [
        (0.030, v["views.match"], MUTE, "#F1F3F6", "#D7DBE0"),
        (0.352, v["views.priorart"], TOBE, TOBE_FILL, TOBE_EDGE),
        (0.674, v["views.foresight"], MUTE, "#F1F3F6", "#D7DBE0"),
    ]
    for x, cells, color, fill, edge in views:
        cells = [labels.cell(c) for c in cells]
        name, classes, cqs, abox, status = cells[0], cells[1], cells[2], cells[3], cells[4]
        _rbox(ax, x, 0.560, 0.296, 0.400, title=name, body="",
              fill=fill, edge=edge, tcolor=color, ts=11)
        ax.text(x + 0.016, 0.878, _terms(classes, 2), ha="left", va="top",
                fontsize=7.6, color=INK, linespacing=1.5)
        _fit_text(ax, x + 0.016, 0.700, T("tbox.cq_prefix", cq=_plain(cqs)), 0.270,
                   where="그림3 역량질문", ha="left", va="top", fontsize=7.6, color=MUTE)
        _fit_text(ax, x + 0.016, 0.668, T("tbox.abox_prefix", abox=_terms(_plain(abox), 2)),
                  0.270, where="그림3 A-Box", ha="left", va="top", fontsize=7.2,
                  color=MUTE, linespacing=1.5)
        ax.text(x + 0.016, 0.588, T("tbox.status_head"), ha="left", va="center",
                fontsize=7.4, color=MUTE)
        ax.text(x + 0.016, 0.568, _terms(_status(status), 2), ha="left", va="center",
                fontsize=8, fontweight="bold", color=color, linespacing=1.5)

    # ── 결합 통로 ────────────────────────────────────────────────────────────
    # 공유 어휘가 **어느 두 뷰를** 잇는지가 이 그림의 요점이다. 그래서 통로마다 선을 그
    # 두 열의 중심으로만 보낸다 — 세 열 전부에 뻗으면 "공유"와 "결합"이 구분되지 않는다.
    ax.text(0.5, 0.510, T("tbox.channel_title"),
            ha="center", va="center", fontsize=9.5, fontweight="bold", color=INK,
            bbox=dict(boxstyle="square,pad=0.35", fc="#FFFFFF", ec="none"), zorder=5)
    cols = (0.178, 0.500, 0.822)

    def _link(x: float, y: float, label: str, left: float, right: float) -> None:
        _chip(ax, x, y, label, color=GOLD, fill="#FBF3E4")
        for tx in (left, right):
            ax.annotate("", xy=(tx, 0.556), xytext=(x, y + 0.030),
                        arrowprops=dict(arrowstyle="-", linestyle=(0, (2, 2)),
                                        color=GOLD, lw=1.2))

    _link(0.339, 0.445, "Material · Equipment · Organization", cols[0], cols[1])
    _link(0.800, 0.445, T("tbox.channel_class"), cols[1], cols[2])

    # Process·SubProcess 는 1열과 3열을 잇는다 — 가운데 열을 건너뛰므로 선이 아니라
    # **바깥으로 도는 괄호**로 그린다. 직선으로 이으면 위 두 통로의 선과 엉킨다.
    for tx in (0.090, 0.910):
        ax.annotate("", xy=(tx, 0.556), xytext=(tx, 0.322),
                    arrowprops=dict(arrowstyle="-", linestyle=(0, (2, 2)),
                                    color=GOLD, lw=1.2))
        ax.annotate("", xy=(tx, 0.322), xytext=(0.5, 0.322),
                    arrowprops=dict(arrowstyle="-", linestyle=(0, (2, 2)),
                                    color=GOLD, lw=1.2))
    _chip(ax, 0.500, 0.322, "Process · SubProcess", color=GOLD, fill="#FBF3E4")

    # ── 공유 코어 ────────────────────────────────────────────────────────────
    _rbox(ax, 0.030, 0.055, 0.940, 0.190,
          title=T("tbox.core_title"),
          body="", fill="#FFFFFF", edge=BORDER, ts=10.5)
    ax.text(0.5, 0.170,
            "T_SDKB = T_core ∪ V_match ∪ V_priorart ∪ V_foresight",
            ha="center", va="center", fontsize=10, color=INK)
    _fit_text(ax, 0.5, 0.120, T("tbox.core_counts"), 0.910, where="그림3 코어 계수",
              ha="center", va="center", fontsize=8.6, color=MUTE)
    _fit_text(ax, 0.5, 0.085, T("tbox.core_note"), 0.910, where="그림3 코어 주석",
              ha="center", va="center", fontsize=8, color=MUTE)
    return _save(fig, out)


# ═══════════════════════════════════════════════════════════════════════════
# 그림 4 — T-gate 절차와 실제 판정
# ═══════════════════════════════════════════════════════════════════════════
def fig_gate_flow(out: Path | None = None) -> Path:
    """승인 절차의 순서와 각 항의 미충족 시 처리, 그리고 실제 거부 사례의 판정.

    오른쪽 열은 통제된 자원 교체(EP3)에서 각 항이 실제로 낸 판정이다. 형식 검증을 전부
    통과한 변경이 성능 조건 하나에서 거부되었다는 사실이 이 열에서 읽힌다.
    """
    out = out or FIGURES / "concept_gate_flow.svg"
    fig, ax = _canvas(11.0, 7.4)

    ax.text(0.175, 0.960, T("gate.col_procedure"), ha="center", va="center",
            fontsize=10, fontweight="bold", color=INK)
    ax.text(0.560, 0.960, T("gate.col_unmet"), ha="center", va="center",
            fontsize=10, fontweight="bold", color=INK)
    ax.text(0.860, 0.960, T("gate.col_verdict"), ha="center", va="center",
            fontsize=10, fontweight="bold", color=INK)

    rows = [
        (T("gate.row_delta"), "", "", "", "#FFFFFF", BORDER, INK),
        (T("gate.row_formal"), T("gate.rule_formal"),
         _mark("mark.pass"), T("gate.detail_formal"), "#FFFFFF", BORDER, INK),
        (T("gate.row_index"), T("gate.rule_index"),
         _mark("mark.pass"), T("gate.detail_index"), "#FFFFFF", BORDER, INK),
        (T("gate.row_t1"), T("gate.rule_t1"),
         _mark("mark.fail"), T("gate.detail_t1"), ASIS_FILL, ASIS_EDGE, ASIS),
        (T("gate.row_t2"), T("gate.rule_t2"),
         _mark("mark.pass"), T("gate.detail_t2"), TOBE_FILL, TOBE_EDGE, TOBE),
        (T("gate.row_t3"), T("gate.rule_t3"),
         _mark("mark.pass"), T("gate.detail_t3"), TOBE_FILL, TOBE_EDGE, TOBE),
        (T("gate.row_merge"), "", "", "", GREEN_FILL, GREEN, GREEN),
    ]

    top, h, gap = 0.905, 0.093, 0.032
    for i, (title, rule, mark, detail, fill, edge, tcolor) in enumerate(rows):
        y = top - i * (h + gap) - h
        _rbox(ax, 0.030, y, 0.290, h, title=title, body="",
              fill=fill, edge=edge, tcolor=tcolor, ts=9.6)
        if rule:
            ax.text(0.348, y + h / 2, rule, ha="left", va="center",
                    fontsize=8, color=MUTE, linespacing=1.5)
        if mark:
            color = ASIS if mark == _mark("mark.fail") else GREEN
            _chip(ax, 0.760, y + h / 2, mark, color=color,
                  fill=ASIS_FILL if mark == _mark("mark.fail") else GREEN_FILL)
            _fit_text(ax, 0.800, y + h / 2, detail, 0.198, where="그림4 판정 상세",
                      ha="left", va="center", fontsize=8,
                      color=color if mark == _mark("mark.fail") else MUTE)
        if i < len(rows) - 1:
            _arrow(ax, 0.175, y - 0.004, 0.175, y - gap + 0.004, color=INK, lw=1.6, ms=12)

    _fit_text(ax, 0.030, 0.030, T("gate.footer"), 0.950, where="그림4 각주",
              ha="left", va="center", fontsize=8.6, color=INK)
    return _save(fig, out)


# ═══════════════════════════════════════════════════════════════════════════
# 그림 5 — 실무 흐름과 실험 구성의 대응 (PLAN-056)
# ═══════════════════════════════════════════════════════════════════════════
def fig_experiment_flow(out: Path | None = None) -> Path:
    """선행기술조사 실무의 단계와 본 실험의 구성을 나란히 놓고 대응을 표시한다.

    **대응이 없는 자리를 함께 표시하는 것이 이 그림의 요점이다.** 실무의 서지 조건에
    대응하는 구성은 주 기준선에 융합되어 있지 않고, 실무의 순차 검토와 달리 본 실험의
    재순위화는 후보 풀을 넘지 못한다. 결손을 가리는 그림이 아니라 드러내는 그림이다.
    """
    out = out or FIGURES / "concept_experiment_flow.svg"
    fig, ax = _canvas(11.0, 7.4)

    ax.text(0.215, 0.945, T("flow.col_practice"), ha="center", va="center",
            fontsize=10.5, fontweight="bold", color=MUTE)
    ax.text(0.700, 0.945, T("flow.col_experiment"), ha="center", va="center",
            fontsize=10.5, fontweight="bold", color=INK)

    rows = [
        (T("flow.task_claims"), T("flow.title_claims"), T("flow.body_claims"),
         TOBE_FILL, TOBE_EDGE, TOBE),
        (T("flow.task_query"), T("flow.title_query"), T("flow.body_query"),
         "#FFFFFF", BORDER, INK),
        (T("flow.task_search"), T("flow.title_search"), T("flow.body_search"),
         "#FFFFFF", BORDER, INK),
        (T("flow.task_fuse"), T("flow.title_fuse"), T("flow.body_fuse"),
         "#FFFFFF", BORDER, INK),
        (T("flow.task_review"), T("flow.title_review"), T("flow.body_review"),
         TOBE_FILL, TOBE_EDGE, TOBE),
        (T("flow.task_reach"), T("flow.title_reach"), T("flow.body_reach"),
         GREEN_FILL, GREEN, GREEN),
    ]

    top, h, gap = 0.900, 0.108, 0.026
    ys = []
    for i, (task, title, body, fill, edge, tcolor) in enumerate(rows):
        y = top - i * (h + gap) - h
        ys.append(y)
        _rbox(ax, 0.030, y, 0.370, h, title=task, body="",
              fill="#F1F3F6", edge="#D7DBE0", tcolor=MUTE, ts=9.4)
        _rbox(ax, 0.470, y, 0.460, h, title=title, body=body,
              fill=fill, edge=edge, tcolor=tcolor, ts=9.6, bs=8.0)
        _arrow(ax, 0.404, y + h / 2, 0.466, y + h / 2, color=MUTE,
               lw=1.2, style="-", ms=10)
        if i < len(rows) - 1:
            _arrow(ax, 0.700, y - 0.002, 0.700, y - gap + 0.002, color=INK,
                   lw=1.5, ms=11)

    # 대응이 없는 자리 둘 — 오른쪽 여백에 표시한다.
    _fit_text(ax, 0.945, ys[1] + h / 2, T("flow.gap_baseline"),
              _ko_width(ax, "flow.gap_baseline", 7.6), where="그림5 결손 주석 1",
              ha="left", va="center", fontsize=7.6, color=ASIS, linespacing=1.5)
    _fit_text(ax, 0.945, ys[4] + h / 2, T("flow.gap_pool"),
              _ko_width(ax, "flow.gap_pool", 7.6), where="그림5 결손 주석 2",
              ha="left", va="center", fontsize=7.6, color=ASIS, linespacing=1.5)

    # 전제 상자 — 본 장의 수치가 성립하는 조건이다.
    _fit_text(ax, 0.5, 0.028, T("flow.premise"), 0.940, where="그림5 전제",
              ha="center", va="center", fontsize=8.6, color=INK,
            bbox=dict(boxstyle="round,pad=0.5", fc="#F7F9FB", ec=BORDER, lw=1.0))
    return _save(fig, out)


# ═══════════════════════════════════════════════════════════════════════════
# 그림 6 — 평가 에피소드와 승인식 구성요소의 대응 (결과 장의 요약 맵)
# ═══════════════════════════════════════════════════════════════════════════
# 부호도 언어를 탄다 — 값은 `labels.MARKS` 가 진다.
def _none() -> str:
    return _mark("mark.none")

# 열 = 승인식의 구성요소. 맨 왼쪽만 게이트가 아니라 자원이다 — EP1 이 재는 대상이
# 게이트가 아니기 때문이며, 이 열이 없으면 EP1 행이 전부 빈칸이 되어 에피소드 넷이
# 한 축 위에 놓이지 않는다.
def matrix_cols() -> list[tuple[str, str]]:
    return [
        (T("matrix.col_resource"), T("matrix.col_resource_sub")),
        ("L0–L3", T("matrix.col_formal_sub")),
        ("T1", T("matrix.col_t1_sub")),
        ("T2", T("matrix.col_t2_sub")),
        ("T3", T("matrix.col_t3_sub")),
        ("T4*", T("matrix.col_t4_sub")),
    ]


def _cell(ax, cx: float, cy: float, mark: str, note: str = "") -> None:
    """칸 하나 — 판정 부호와 그 근거 한 줄. 부호가 색보다 앞선다(규격 F1)."""
    if mark == _none():
        ax.text(cx, cy, _none(), ha="center", va="center", fontsize=13,
                color=BORDER)
        return
    color, fill = GREEN, GREEN_FILL
    if mark in (_mark("mark.fail"), _mark("mark.unconf")):
        color, fill = ASIS, ASIS_FILL
    elif mark == _mark("mark.obs"):
        color, fill = MUTE, "#F1F3F6"
    elif "/" in mark:
        color, fill = TOBE, TOBE_FILL
    _chip(ax, cx, cy + 0.026, mark, color=color, fill=fill)
    if note:
        ax.text(cx, cy - 0.036, note, ha="center", va="center", fontsize=6.6,
                color=MUTE, linespacing=1.45)


def fig_ep_gate_matrix(out: Path | None = None) -> Path:
    """다섯 평가 에피소드가 승인식의 어느 항을 검증하였고 그 판정이 무엇인가.

    가로로 읽으면 한 에피소드의 검증 범위가 보이고, 세로로 읽으면 같은 항이 서로 다른
    실험에서 낸 판정이 보인다. **이 그림의 요점은 두 행에 있다** — EP3 행에서 형식 검증을
    전부 통과한 변경이 T1 에서 거부되었고, EP4 행에서 T1 을 통과한 구성이 T4 에서 비열등을
    보이지 못하였다. 층간 지표 불일치가 산문의 도움 없이 표면에 드러난다.
    """
    out = out or FIGURES / "concept_ep_gate_matrix.svg"
    v = figdata.load()
    fig, ax = _canvas(11.0, 6.6)

    none = _none()
    rows = [
        ("EP1", T("matrix.ep1_name"), T("matrix.ep1_status"),
         [(_mark("mark.obs"), T("matrix.ep1_cell")),
          (none, ""), (none, ""), (none, ""), (none, ""), (none, "")],
         T("matrix.ep1_verdict")),
        ("EP2", T("matrix.ep2_name"), T("matrix.ep2_status"),
         [(none, ""),
          (str(v["ep2.l3_detected"]), T("matrix.ep2_cell_l3")),
          (none, ""), (none, ""),
          (str(v["ep2.t3_only"]), T("matrix.ep2_cell_t3")),
          (none, "")],
         T("matrix.ep2_verdict")),
        ("EP3", T("matrix.ep3_name"), T("matrix.ep3_status"),
         [(T("matrix.ep3_cell_ratio_mark"), T("matrix.ep3_cell_resource")),
          (_mark("mark.pass"), T("matrix.ep3_cell_formal")),
          (_mark("mark.fail"), T("matrix.ep3_cell_t1")),
          (_mark("mark.pass"), T("matrix.ep3_cell_t2")),
          (_mark("mark.pass"), T("matrix.ep3_cell_t3")),
          (none, "")],
         T("matrix.ep3_verdict")),
        ("EP4", T("matrix.ep4_name"), T("matrix.ep4_status"),
         [(none, ""), (none, ""),
          (_mark("mark.pass"), T("matrix.ep4_cell_t1")),
          (_mark("mark.pass"), T("matrix.ep4_cell_t2")),
          (none, ""),
          (_mark("mark.unconf"), T("matrix.ep4_cell_t4"))],
         T("matrix.ep4_verdict")),
        # EP5 행의 부호는 **검출 실패가 아니라 미판정**이다. 21건 전량에서 어느 층도 검출하지
        # 않았고 층 사이의 불일치 쌍이 0 이므로, T3 를 다른 층과 비교할 표본이 성립하지 않았다.
        # 이 구분을 부호로 세우지 않으면 그림이 산문보다 강한 주장을 하게 된다.
        ("EP5", T("matrix.ep5_name"), T("matrix.ep5_status"),
         [(none, ""),
          (_mark("mark.pass"), T("matrix.ep5_cell_formal")),
          (none, ""), (none, ""),
          (_mark("mark.unconf"), T("matrix.ep5_cell_t3")),
          (none, "")],
         T("matrix.ep5_verdict")),
    ]

    # ── 열 머리글 ────────────────────────────────────────────────────────────
    x0, cw, cgap = 0.175, 0.072, 0.004
    cols = matrix_cols()
    centers = [x0 + cw / 2 + i * (cw + cgap) for i in range(len(cols))]
    for cx, (head, sub) in zip(centers, matrix_cols()):
        ax.text(cx, 0.930, head, ha="center", va="center", fontsize=9.6,
                fontweight="bold", color=INK)
        ax.text(cx, 0.900, sub, ha="center", va="center", fontsize=6.8, color=MUTE)
    ax.text(0.020, 0.930, T("matrix.head_episode"), ha="left", va="center", fontsize=9.6,
            fontweight="bold", color=INK)
    ax.text(0.645, 0.930, T("matrix.head_verdict"), ha="left", va="center", fontsize=9.6,
            fontweight="bold", color=INK)
    ax.plot([0.020, 0.985], [0.876, 0.876], color=BORDER, lw=1.0)

    # ── 행 ───────────────────────────────────────────────────────────────────
    top, h, gap = 0.865, 0.145, 0.025
    for i, (tag, name, status, cells, verdict) in enumerate(rows):
        y = top - i * (h + gap) - h
        _rbox(ax, 0.020, y, 0.145, h, title=tag, body=name,
              fill="#FFFFFF", edge=BORDER, ts=10, bs=7.8)
        _rbox(ax, x0 - 0.004, y, len(cells) * (cw + cgap), h, title="", body="",
              fill="#FBFCFD", edge=BORDER)
        for cx, (mark, note) in zip(centers, cells):
            _cell(ax, cx, y + h / 2, mark, note)
        _fit_text(ax, 0.985, y + h - 0.014, T("common.status_prefix", status=status),
                  0.330, where="그림6 지위", ha="right", va="top",
                  fontsize=6.8, style="italic", color=MUTE)
        _fit_text(ax, 0.645, y + h / 2 - 0.012, verdict, 0.340, where="그림6 판정 요약",
                  ha="left", va="center", fontsize=7.8, color=INK, linespacing=1.6)

    # ── 읽는 법 띠는 그리지 않는다 (2026-08-27 · PLAN-083) ────────────────────
    # 띠는 y=0.055 에 있었고 EP5 행은 y=0.040–0.185 에 있다. 곧 **두 언어 모두에서** 띠가
    # 마지막 행을 덮고 있었다 — 영문 라벨 길이의 문제가 아니라 기하의 결함이다. 읽는 법과
    # T4 각주는 그림이 아니라 **캡션**이 진다(규격 F4 · 그림의 글자는 구조를 지고 구체적
    # 내역은 캡션이 진다). `matrix.reading` 라벨은 캡션 문구의 원천으로 표에 남긴다.
    return _save(fig, out)


def out_dir(lang: str) -> Path:
    """언어별 산출 자리. 한국어판은 국문 정본·supplementary 가 인용하므로 자리를 옮기지 않는다."""
    return FIGURES if lang == "ko" else FIGURES / lang


def main() -> None:
    """개념 도식 전량을 동결 수치에서 결정적으로 재생성한다."""
    ap = argparse.ArgumentParser(description="개념 도식 생성 (PLAN-082)")
    ap.add_argument("--lang", default="ko", choices=list(labels.LANGS),
                    help="라벨 언어. en 은 paper/figures/en/ 으로 낸다")
    args = ap.parse_args()
    labels.set_lang(args.lang)
    d = out_dir(args.lang)
    d.mkdir(parents=True, exist_ok=True)
    for fn in (fig_overview, fig_layer_mismatch, fig_tbox_views, fig_gate_flow,
               fig_experiment_flow, fig_ep_gate_matrix):
        name = fn.__defaults__ and None  # 기본 경로는 각 함수가 정한다
        del name
        out = d / _basename(fn)
        print(f"  ✓ {fn(out).relative_to(FIGURES.parent.parent)}")


_BASENAMES = {
    "fig_overview": "concept_overview.svg",
    "fig_layer_mismatch": "concept_layer_mismatch.svg",
    "fig_tbox_views": "concept_tbox_views.svg",
    "fig_gate_flow": "concept_gate_flow.svg",
    "fig_experiment_flow": "concept_experiment_flow.svg",
    "fig_ep_gate_matrix": "concept_ep_gate_matrix.svg",
}


def _basename(fn) -> str:
    return _BASENAMES[fn.__name__]


if __name__ == "__main__":
    main()
