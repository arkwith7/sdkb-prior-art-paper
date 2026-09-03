"""그림 라벨의 이중 언어 계약 (PLAN-082 성공기준 G1–G5 · 그림 규격 F-v1).

**무엇을 지키는가.** 그리기 코드는 한 벌이고 글자만 `viz/labels.py` 에서 온다. 그 배선이
깨지는 자리는 넷이며 각각을 한 테스트가 지킨다.

- **G2** 한국어판이 바이트 단위로 불변인가 — 영문화가 국문 그림을 조용히 바꾸지 못하게 한다.
- **G1** 영문 라벨에 한글이 남지 않았는가.
- **G5** 영문 라벨이 §0.8 판정 문구 사전(영문 대응 STYLE-EN §4)을 어기지 않는가.
- **G3** 두 언어의 라벨이 **같은 수치**를 말하는가.

**왜 SVG 가 아니라 라벨 표를 보는가.** SVG 는 글리프로 렌더되어 문자열 대조가 어렵고,
그리기 코드가 아니라 **라벨이 계약의 자리**이기 때문이다. 산출물 수준의 확인(한글 0자 ·
한국어 해시)은 별도 테스트가 파일에서 직접 본다.
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

from sdkb_paper.viz import labels

ROOT = Path(__file__).resolve().parent.parent
HANGUL = re.compile(r"[가-힣]")


def _all_entries() -> list[tuple[str, dict[str, str]]]:
    return list(labels.LABELS.items()) + list(labels.MARKS.items())


# ── G1 · 영문 라벨에 한글이 없다 ──────────────────────────────────────────────
def test_english_labels_have_no_hangul():
    bad = [k for k, e in _all_entries() if HANGUL.search(e["en"])]
    assert bad == [], f"영문 라벨에 한글이 남았다: {bad}"


def test_every_label_has_both_languages():
    missing = [k for k, e in _all_entries() if set(e) != {"ko", "en"}]
    assert missing == [], f"두 언어가 모두 있어야 한다: {missing}"


def test_cell_translations_have_no_hangul_on_the_english_side():
    bad = [k for k, v in labels.CELL_TRANSLATIONS.items() if HANGUL.search(v)]
    assert bad == [], f"추출 칸 번역에 한글이 남았다: {bad}"


# ── G3 · 두 언어가 같은 수치를 말한다 ────────────────────────────────────────
def _numbers(s: str) -> list[str]:
    """라벨이 말하는 **측정치**. 자리표시자를 채운 뒤 센다.

    **한 자리 숫자는 세지 않는다.** 그 자리는 측정치가 아니라 라벨 기호(`T3`·`EP4`·`L0`)이거나
    산문의 수사이기 때문이다 — 한국어는 「판정 1회」로 적고 영문은 `one verdict` 로 적으므로,
    한 자리를 세면 **같은 뜻을 다르게 적은 문장이 전부 위반이 된다.** 원고의 절 대응 점검이
    같은 이유로 같은 규칙을 쓴다.

    이 완화가 놓치는 것은 **한 자리 측정치를 손으로 적은 경우**뿐이며, 두 언어가 같은
    자리표시자를 쓰므로 그 값은 구성상 같다. 손으로 적은 수치는 대개 여러 자리다.
    """
    return sorted(n for n in re.findall(r"\d+(?:[.,]\d+)*", s) if len(n) > 1)


# 호출 시점에 채워지는 자리표시자 — 동결 수치가 아니라 그리기 코드가 넘기는 값이다.
# `ep`·`section` 은 그림 6 행 머리(`matrix.row_tag`)가 쓰며 원천은 paper/episodes.yaml 이다.
CALL_TIME = {"status": "", "target": "", "cq": "", "abox": "", "ep": "", "section": ""}


@pytest.mark.parametrize("key", sorted(labels.LABELS))
def test_two_languages_state_the_same_numbers(key):
    entry = labels.LABELS[key]
    extra = CALL_TIME
    labels.set_lang("ko")
    ko = labels.render(entry["ko"], **extra)
    labels.set_lang("en")
    en = labels.render(entry["en"], **extra)
    labels.set_lang("ko")
    assert _numbers(ko) == _numbers(en), f"{key}: 두 언어의 수치가 다르다\n  ko {ko}\n  en {en}"


# ── G5 · 영문 라벨이 판정 문구 사전을 어기지 않는다 ──────────────────────────
def _style_check_en():
    spec = importlib.util.spec_from_file_location(
        "style_check_en", ROOT / "scripts" / "style_check_en.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_english_labels_obey_the_verdict_wording():
    """그림 글자도 판정 문구 규율의 대상이다(규격 F4) — 지금까지 기계로 확인된 적이 없었다."""
    sce = _style_check_en()
    labels.set_lang("en")
    fails = []
    for key, entry in _all_entries():
        text = labels.render(entry["en"], **CALL_TIME)
        for pat, better in sce.VERDICT_FORBIDDEN_EN:
            if re.search(pat, text, re.I):
                fails.append(f"{key}: 금지 판정 문구 — {better}\n    {text}")
    labels.set_lang("ko")
    assert fails == [], "\n".join(fails)


# ── 조립기와의 일치 · 그림 3 추출 칸 ─────────────────────────────────────────
def test_cell_translations_agree_with_the_submission_builder():
    """같은 한국어 칸이 표와 그림에서 다르게 번역되지 않는다 (PLAN-082 설계 ③).

    지금은 교집합이 0 이다 — 표 3 은 파생본에서 그림 3 으로 대체되어 조립기가 그 칸을
    다룰 일이 없었기 때문이다. 이 테스트는 **앞으로 겹치게 될 때**를 지킨다.
    """
    spec = importlib.util.spec_from_file_location(
        "build_submission_en", ROOT / "scripts" / "build_submission_en.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    clash = [k for k, v in labels.CELL_TRANSLATIONS.items()
             if k in mod.CELLS and mod.CELLS[k] != v]
    assert clash == [], f"조립기와 그림의 번역이 다르다: {clash}"


# ── 라벨 표의 위생 ───────────────────────────────────────────────────────────
def test_every_placeholder_resolves():
    """자리표시자가 동결 수치나 기호에 닿는가 — 닿지 않으면 그림이 실행 중에 죽는다."""
    known = set(labels.values()) | set(labels.MARKS) | set(CALL_TIME)
    unknown = set()
    for _, entry in _all_entries():
        for text in entry.values():
            for m in labels._PLACEHOLDER.finditer(text):
                if m.group(1) not in known:
                    unknown.add(m.group(1))
    assert unknown == set(), f"해석되지 않는 자리표시자: {sorted(unknown)}"
