"""개념 그림이 인용하는 수치가 산출물과 어긋나지 않는가 (viz/figdata · 그림 규격 F6).

**왜 필요한가.** 데이터 플롯은 CSV 를 직접 그리므로 수치가 저절로 정합한다. 개념 도식은
그렇지 않다 — 값이 그림 코드나 동결 JSON 에 남아 있어, 재측정으로 본문이 갱신돼도 그림은
옛 값을 계속 보여줄 수 있다. 본문과 그림의 수치 불일치는 심사에서 자주 지적되는 결함이며
사람의 주의력으로는 막히지 않는다. 이 테스트가 그 자리를 지킨다.

산출물이 없는 환경(얕은 체크아웃)에서는 추출을 건너뛴다 — 없는 파일을 실패로 만들면
CI 가 데이터 유무로 붉어진다.
"""
from __future__ import annotations

import pytest

from sdkb_paper.config import ROOT
from sdkb_paper.viz import figdata


def _available(rule: figdata.Rule) -> bool:
    return (ROOT / rule.source).exists()


def test_every_rule_matches_exactly_once():
    """규칙이 0회 또는 2회 이상 매치되면 값이 아니라 우연을 읽고 있는 것이다."""
    for rule in figdata.RULES:
        if not _available(rule):
            continue
        figdata._apply(rule)          # 매치 수가 1이 아니면 여기서 예외


def test_frozen_values_match_artifacts():
    """동결 JSON 과 산출물이 어긋나면 실패한다 — `make figure-data` 로 재동결한다."""
    if not figdata.FROZEN.exists():
        pytest.skip("동결본 없음 — `make figure-data` 선행")
    figdata.load(verify=True)


def test_concept_figures_hardcode_no_numbers():
    """개념 그림 코드에 수치 리터럴을 적지 않는다(F6).

    소수점 숫자가 좌표 이외의 자리에 나타나는 것을 막는 완전한 검사는 불가능하다. 대신
    **본문이 인용하는 특징적인 값**이 코드에 문자열로 박혀 있는지 본다 — 하드코딩이
    되살아나는 경로는 실제로 이 형태였다.
    """
    src = (ROOT / "src" / "sdkb_paper" / "viz" / "concept.py").read_text(encoding="utf-8")
    forbidden = ["0.0293", "0.0534", "3.779", "12/45", "0.0205", "0.2282"]
    found = [lit for lit in forbidden if lit in src]
    assert not found, f"수치가 그림 코드에 하드코딩되었다 — figdata 로 옮긴다: {found}"
