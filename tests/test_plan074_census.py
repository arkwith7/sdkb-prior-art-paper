"""PLAN-074 Phase 0′ 계수기의 단위 테스트 (scripts/plan074_phase0prime_census.py).

계수기가 지켜야 하는 것은 셋이다 — **동결된 판단 단위 규칙**(§12.2 조건 셋) · **폴백 없는
인용 측 해소**(D1) · **시드 고정 표본의 결정성**(§12.4). 세 가지가 깨지면 그 위의 문턱 판정이
근거를 잃으므로 기계가 지킨다.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location(
        "plan074", ROOT / "scripts" / "plan074_phase0prime_census.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m  # dataclass 는 모듈이 등록돼 있어야 필드를 해석한다
    spec.loader.exec_module(m)
    return m


NOTICE = """의견제출통지서
출 원 번 호 10-2016-0155007

- 아 래 -
인용발명 1 : 공개특허공보 제10-2012-0075051호(2012.07.06.)
인용발명 2 : 일본 공개특허공보 특개2008-160000호(2008.07.10.)

1. 청구항 1 발명은 인용발명 1의 챔버 구성과 실질적으로 동일하고, 인용발명 2를 결합하여
쉽게 발명할 수 있습니다.

2. 청구항 2 발명에 부가한 구성은 인용발명 1로부터 단순한 설계변경에 지나지 않습니다.
"""


@pytest.fixture()
def corpus():
    return pd.DataFrame(
        [
            {"doc_id": "kr_1020160155007", "claims_full": "복수개의 챔버를 포함하는 증착 장치.\n상기 반송레인은 기판을 이송한다."},
            {"doc_id": "kr_KR1020120075051A", "claims_full": "스퍼터 챔버와 기판 반송 장치."},
            {"doc_id": "jp_JP2008160000A", "claims_full": None},  # 청구항 실물 없음 — 폴백 금지
        ]
    ).set_index("doc_id")


def test_paragraphs_splits_on_numbered_items(mod):
    paras = mod.paragraphs(NOTICE)
    assert any(p.startswith("1. 청구항 1 발명") for p in paras)
    assert any(p.startswith("2. 청구항 2 발명") for p in paras)


def test_cite_map_keeps_definition_lines(mod):
    m = mod.cite_map([("통지서", NOTICE)])
    assert set(m) == {1, 2}
    assert "10-2012-0075051" in m[1] and "특개2008-160000" in m[2]


def test_doc_index_strips_kind_codes(mod):
    """종류코드(A1·B2)의 숫자가 번호에 섞이면 색인이 어긋난다 — §16.2 ③ 의 결함."""
    idx, _ = mod.build_doc_index(
        ["us_US20150255543A1", "jp_JP07091636B2", "wo_WO2015112308A1", "kr_KR1020120075051A"])
    assert idx[("US", "20150255543")] == "us_US20150255543A1"
    assert idx[("JP", "7091636")] == "jp_JP07091636B2"
    assert idx[("WO", "2015112308")] == "wo_WO2015112308A1"


def test_resolve_doc_handles_foreign_number_formats(mod):
    idx, _ = mod.build_doc_index(
        ["us_US20150255543A1", "jp_JP07091636B2", "jp_JP2014017513A", "wo_WO2015112308A1"])
    assert mod.resolve_doc("미국 특허출원공개공보 US2015/0255543호(2015.09.10.)", idx) == "us_US20150255543A1"
    assert mod.resolve_doc("일본 특허공보 특허 제 7091636호(1995.10.04.)", idx) == "jp_JP07091636B2"
    assert mod.resolve_doc("일본공개특허공보 2014-17513(2014.01.30.)", idx) == "jp_JP2014017513A"
    assert mod.resolve_doc("WO2015/112308A1(2015.07.30.)", idx) == "wo_WO2015112308A1"
    assert mod.resolve_doc("아무 번호도 없는 줄", idx) is None


def test_unit_requires_both_references(mod, corpus):
    """§12.2 — 유형 단서만으로는 단위가 되지 않는다. 두 지시가 함께 있어야 한다."""
    no_ref = NOTICE.replace("청구항 1 발명은 인용발명 1의", "이 발명은 위 문헌의")
    apps, dev = ["1020160155007"], ["kr_1020160155007"]
    dbd, _ = mod.build_doc_index(corpus.index)
    units, stat = mod.build_units(apps, dev, {apps[0]: [("통지서", no_ref)]}, corpus, dbd)
    assert all(u.typ != "결합" or u.claim_no for u in units)
    assert stat["지시 불충분"] >= 1


def test_units_and_pairs_are_claim_grounded(mod, corpus):
    apps, dev = ["1020160155007"], ["kr_1020160155007"]
    dbd, _ = mod.build_doc_index(corpus.index)
    units, stat = mod.build_units(apps, dev, {apps[0]: [("통지서", NOTICE)]}, corpus, dbd)
    assert stat["두 지시 보유"] >= 1
    combine = [u for u in units if u.typ == "결합"]
    assert combine and combine[0].claim_no == 1
    # 인용발명 2 는 청구항 실물이 없으므로 D1 대로 개념을 내지 않는다.
    concepts = lambda t: {w for w in ("챔버", "반송레인", "기판", "스퍼터") if w in (t or "")}  # noqa: E731
    claims = {dev[0]: mod.claim_lines(corpus.at[dev[0], "claims_full"])}
    by_type, raw, per_q, by_kind, unit_pairs, dropped = mod.census(
        units, corpus, concepts, {apps[0]: dev[0]}, claims)
    pairs = by_type["결합"]
    assert ("챔버", "스퍼터", "결합") in pairs
    assert all(b in {"스퍼터", "챔버", "기판"} for _, b, _ in pairs)
    assert dropped["인용 청구항 실물 없음"] >= 1  # jp 문헌은 폴백 없이 버려진다
    assert per_q[dev[0]] and raw == len(unit_pairs)


def test_paragraph_without_citation_is_dropped(mod, corpus):
    """인용발명 지시가 없는 문단은 유형 단서가 있어도 단위가 되지 않는다(§12.2 조건 2)."""
    txt = NOTICE.replace("인용발명 1로부터 단순한 설계변경", "단순한 설계변경")
    apps, dev = ["1020160155007"], ["kr_1020160155007"]
    dbd, _ = mod.build_doc_index(corpus.index)
    units, stat = mod.build_units(apps, dev, {apps[0]: [("통지서", txt)]}, corpus, dbd)
    assert not [u for u in units if u.typ == "설계변경"]
    assert stat["지시 불충분"] >= 1


def test_second_claim_uses_its_own_line(mod, corpus):
    """청구항 2 를 지시한 단위는 둘째 줄에 접지된다 — 종속 부모 복원은 하지 않는다(구현 note)."""
    apps, dev = ["1020160155007"], ["kr_1020160155007"]
    dbd, _ = mod.build_doc_index(corpus.index)
    units, _ = mod.build_units(apps, dev, {apps[0]: [("통지서", NOTICE)]}, corpus, dbd)
    design = [u for u in units if u.typ == "설계변경"]
    assert design and design[0].claim_no == 2


def test_sample_is_deterministic_under_seed(mod):
    Unit = mod.Unit
    unit_pairs = [
        (Unit(f"app{i}", "통지서", i, "결합" if i % 2 else "치환", 1, ("d",), f"문단 {i}"),
         (f"c{i}", "x", "결합" if i % 2 else "치환"))
        for i in range(40)
    ]
    rounds = {f"app{i}": 1 if i % 3 else 2 for i in range(40)}
    first, _ = mod.sample_units(unit_pairs, rounds, n=8)
    second, _ = mod.sample_units(unit_pairs, rounds, n=8)
    assert [u.app for u, _ in first] == [u.app for u, _ in second]
    assert len(first) == 8
