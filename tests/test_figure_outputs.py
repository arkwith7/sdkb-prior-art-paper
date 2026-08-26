"""본문 그림 산출물의 계약 (PLAN-082 성공기준 G1·G2 · 그림 규격 F-v1).

앞의 `test_figure_labels.py` 가 **라벨 표**를 보는 자리라면, 이 파일은 **디스크의 SVG** 를
본다. 둘 다 필요하다 — 라벨이 옳아도 배선이 어긋나면 산출물은 틀린다.

**G2 의 해시는 눈으로 검수를 마친 한국어판의 동결값이다.** 이 값이 바뀌면 둘 중 하나다.
ⓐ 그림을 의도적으로 고쳤다 — 그러면 이 표를 같은 커밋에서 갱신하고 사유를 커밋 메시지에
적는다. ⓑ 영문화 배선이 국문 그림을 조용히 바꾸었다 — 그것이 이 테스트가 막는 사고다.

**왜 재생성하지 않고 디스크를 보는가.** 그림 재생성은 산출물 CSV 와 동결 JSON 을 요구해
단위 테스트의 시간·의존을 넘긴다. 재생성의 정합은 `make figures` 가 지고, 이 테스트는
**저장소에 든 산출물이 그 계약을 지키는가**를 본다.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FIGURES = ROOT / "paper" / "figures"
HANGUL = re.compile(r"[가-힣]")

# 본문 그림 7종 — 영문 원고가 인용하는 것과 같은 목록이다.
BODY_FIGURES = (
    "concept_overview.svg",
    "concept_layer_mismatch.svg",
    "concept_tbox_views.svg",
    "concept_gate_flow.svg",
    "concept_experiment_flow.svg",
    "concept_ep_gate_matrix.svg",
    "ir_metrics.svg",
)

# G2 · 한국어판의 동결 해시 (2026-08-26 · PLAN-082 착수 시점에 고정)
KO_SHA256 = {
    "concept_overview.svg":
        "319278a29a2ac96a5113f263819e35724d1463e8a399cd34e74722d57eacbec1",
    "concept_layer_mismatch.svg":
        "2c9ff70afceef91b525b3de085689261436974fbbae073ac42c9d0f8aab26e3a",
    "concept_tbox_views.svg":
        "a145cbbce0b2dca37ddd9b87a8c7915e6f8a28c23967103b463a2215ac3de6c1",
    "concept_gate_flow.svg":
        "13c200d61b997e68998e18841f04cbf941e37bafd201c09e4dd6c86a43205dcb",
    "concept_experiment_flow.svg":
        "d705ab050d1424ac0ce02396a871ddec83fe134d16fcae904e407e3474031faf",
    "concept_ep_gate_matrix.svg":
        "281957db065196628031951028b0f88dd29d2ea49e1b14b8a6df3fec705af894",
    "ir_metrics.svg":
        "c3118b3128d9b95cb8d33f7c8891b49179d4e0cc433bb3b7463838c966478ee0",
}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


@pytest.mark.parametrize("name", BODY_FIGURES)
def test_korean_figures_are_unchanged(name):
    """G2 — 영문화가 국문 그림을 바꾸지 않았다."""
    p = FIGURES / name
    assert p.exists(), f"한국어 그림이 없다: {p}"
    assert _sha(p) == KO_SHA256[name], (
        f"{name} 이 동결 해시와 다르다. 의도한 변경이면 이 표를 같은 커밋에서 갱신하고 "
        f"사유를 커밋 메시지에 적는다.")


# matplotlib 은 글자를 **패스로 렌더**한다 — SVG 에 `<text>` 노드가 없고, 읽을 수 있는
# 문자열은 각 텍스트 그룹 앞의 **XML 주석**에만 남는다(`<!-- 전문가 매칭 -->`).
# 그러므로 파일 전체에 정규식을 거는 검사는 **주석이 사라지면 조용히 통과**한다.
# 그 침묵을 막기 위해 주석을 명시적으로 뽑고, **하나도 못 뽑으면 실패시킨다.**
TEXT_COMMENT = re.compile(r"<!--\s*(.*?)\s*-->", re.S)


def _rendered_strings(svg: Path) -> list[str]:
    """그림이 실제로 그린 문자열. matplotlib 이 남기는 주석이 유일한 기록이다."""
    return [s for s in TEXT_COMMENT.findall(svg.read_text(encoding="utf-8")) if s.strip()]


@pytest.mark.parametrize("name", BODY_FIGURES)
def test_english_figures_have_no_hangul(name):
    """G1 — 영문판에 한글이 남지 않았다."""
    p = FIGURES / "en" / name
    assert p.exists(), f"영문 그림이 없다: {p} (make figures-en)"
    drawn = _rendered_strings(p)
    assert len(drawn) >= 5, (
        f"{name}: 그린 문자열을 {len(drawn)}개만 찾았다 — matplotlib 이 주석을 남기지 "
        f"않았거나 그림이 비었다. 이 검사는 그 침묵을 통과로 세지 않는다.")
    bad = [s for s in drawn if HANGUL.search(s)]
    assert bad == [], f"{name} 영문판에 한글이 남았다 ({len(bad)}자리): {bad[:6]}"


@pytest.mark.parametrize("name", BODY_FIGURES)
def test_korean_figures_do_render_hangul(name):
    """대조 — 한국어판에는 한글이 있다. 없으면 위 검사가 무엇을 보는지 알 수 없다."""
    drawn = _rendered_strings(FIGURES / name)
    assert any(HANGUL.search(s) for s in drawn), (
        f"{name}: 한국어판에서 한글을 찾지 못했다 — 검사의 전제가 깨졌다")


def test_english_manuscript_points_at_english_figures():
    """G6 — 영문 원고가 한국어 그림을 가리키지 않는다."""
    m = ROOT / "paper" / "submission" / "en" / "manuscript.md"
    if not m.exists():
        pytest.skip("영문 파생본이 아직 조립되지 않았다")
    text = m.read_text(encoding="utf-8")
    stale = re.findall(r"\]\(\.\./\.\./figures/(?!en/)([a-z_]+\.svg)\)", text)
    assert stale == [], f"영문 원고가 한국어 그림을 가리킨다: {sorted(set(stale))}"
