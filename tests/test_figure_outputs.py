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

# 본문 그림 8종 — 영문 원고가 인용하는 것과 같은 목록이다.
BODY_FIGURES = (
    "concept_overview.svg",
    "concept_layer_mismatch.svg",
    "concept_tbox_views.svg",
    "concept_gate_flow.svg",
    "concept_experiment_flow.svg",
    "concept_ep_gate_matrix.svg",
    "ir_metrics.svg",
    "concept_detection_port_boundary.svg",
)

# G2 · 한국어판의 동결 해시
# 2026-08-26 PLAN-082 착수 시점에 고정 · **2026-08-27 갱신(사용자 승인)** — 산출물 라벨을
# `A1`·`A2`·`A3` 에서 **`ART-1`·`ART-2`·`E1`** 로 옮겼다. 구 표기가 절제 조건 `A1`–`A8` 과
# 기호가 겹쳐 같은 기호가 두 가지를 가리켰고, 셋째 띠는 그림만 `A3` 이고 본문은 `E1` 이었다.
# **의도한 변경이므로 값을 갱신한다** — 바뀐 것은 라벨 문자열뿐이고 수치·기하·배치는 그대로다.
# **2026-08-27 갱신 2(사용자 승인 · PLAN-083)** — 셋이 바뀌었다. ⓐ `concept_ep_gate_matrix`:
# 하단 "읽는 법" 띠가 y=0.055 에 있고 EP5 행이 y=0.040–0.185 에 있어 **두 언어 모두에서** 띠가
# 마지막 행을 덮고 있었다. 띠를 그리지 않고 그 내용을 캡션으로 내렸으며, 열 머리글과 판정 요약도
# 줄였다. ⓑ `concept_overview`·ⓒ `concept_tbox_views`: 영문판에서 라벨이 옆 상자를 침범하던
# 자리를 두 언어의 라벨을 함께 줄여 해소하였다. **수치와 자리표시자는 하나도 바뀌지 않았다** —
# 바뀐 것은 설명하는 말의 길이다(규격 F6).
# 2026-09-04 갱신 (사용자 승인 · 기하 수정) — 네 장의 **자리만** 고쳤다. `_rbox` 의 여백이
# 상자를 사방으로 넓힌다는 사실이 간격 계산에서 빠져 있었고, 그래서 그림 1 의 에피소드 상자
# 다섯은 인접 쌍마다 0.004 겹쳤으며(간격 0.186 < 폭 0.178 + 여백 0.012) 그림 6 의 행 라벨은
# 매트릭스와 0.006 겹쳤다. 그림 5 는 행 간격이 0.002 로 붙어 흐름 화살표가 상자에 묻혔고
# 결손 주석 둘이 도판 밖으로 나갔다(x=1.109). 그림 4 는 T1 판정 상세가 x=1.087 까지 나갔다.
# **수치·판정·용어는 하나도 바뀌지 않았다** — 바뀐 것은 상자의 폭·간격·여백과 줄바꿈 자리다.
# 2026-09-05 갱신 (사용자 승인 · PLAN-089 안 A) — 도판의 **담당 주장을 재배정**하였다.
# 그림 1 은 개요도를 대체하여 통제된 자원 교체의 판정 경로(기여 ②)를 지고, 구 개요도의
# ART-1 띠와 ΔG 상자는 그림 3 으로, 승인 게이트 띠는 그림 4 로 갔다. 그림 4 는 판정 열을
# 그림 1 에 넘기고 두 열이 되었으며, 그림 8 은 교훈 셋(기여 ③) 띠를 얻었다. 그림 6 은
# 행 라벨의 폭을 되돌리고 매트릭스 시작점으로 겹침을 풀었다(영문 라벨이 바닥 글자 크기에서도
# 들어가지 않았기 때문이다). **수치·판정은 하나도 바뀌지 않았다** — 값은 전량
# concept_values.json 에서 읽으며 이 작업은 그 파일을 만들지 않았다.
KO_SHA256 = {
    # 2026-09-03 갱신 (PLAN-087 §11 잔여 ②) — ART-1 띠에 관통 예시의 정박점 한 줄을 넣고
    # EP1 상자의 "실재" 를 "선언" 으로 고쳤다. **수치는 넣지도 바꾸지도 않았다.**
    "concept_overview.svg":
        "439b8516f73f14647de0f43a1df3497b88131fb46a7b5c2d1432f3a55f997077",
    "concept_layer_mismatch.svg":
        "2c9ff70afceef91b525b3de085689261436974fbbae073ac42c9d0f8aab26e3a",
    # 2026-09-03 갱신 (PLAN-087 §11 잔여 ②) — 캡션이 주장하는 것을 도판이 보이게 하였다:
    # 그림 3 은 세 뷰가 만나는 예시 노드를, 그림 5 는 정답 간선 제거 행을, 그림 6 은 EP
    # 번호와 본문 절의 두 축을 각각 표시한다. **수치는 넣지도 바꾸지도 않았다.**
    "concept_tbox_views.svg":
        "d55ff574880b1b8e5c1aae7e26526fc0f088e6e16ea74413da54bbdd5b656a1c",
    "concept_gate_flow.svg":
        "ebcd0454a375dd5ee49ce7b797a336ffbfb521b69df055b66115d80fd597da8d",
    "concept_experiment_flow.svg":
        "7055a14f0693305ba41c5f9bb83e7653d6836e7f7a12c1de7156e060c3a9807b",
    "concept_ep_gate_matrix.svg":
        "7293e16fabd5048a4185051c20bcd5768ffcb715b8bc225f0d95263a65fa3c55",
    "ir_metrics.svg":
        "c3118b3128d9b95cb8d33f7c8891b49179d4e0cc433bb3b7463838c966478ee0",
    "concept_detection_port_boundary.svg":
        "ede4a8004db4b22735525848a2357cfeefbf336dfe6ef4c4737c73532f4a085e",
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
