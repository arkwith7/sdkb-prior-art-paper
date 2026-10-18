"""이식 동등성 — 상류와 **같은 조건**(자기 문서만 제외 · 마스크 없음 · TI+AB+CL)에서 같은 결과인가 (PLAN-096 R4).

하류 마스크가 들어간 적격 후보 검사는 `test_pilot_harness.py` 에 따로 있다(사용자 지시: 두 검사를 분리).
"""
from __future__ import annotations

import hashlib
import json
import os

import pandas as pd
import pytest

from sdkb_paper import config
from sdkb_paper.retrieval import boolean_emulator as K


@pytest.fixture()
def corpus():
    return pd.DataFrame({
        "doc_id": ["d1", "d2", "d3", "d4", "d5"],
        "is_candidate": [True, True, True, True, False],
        "title": ["플라즈마 식각 장치", "etching chamber", "증착 방법", "sketch tool", "식각"],
        "abstract": ["기판을 식각하는 방법", "plasma etching of wafer", "박막 증착", "drawing", "x"],
        "claims_full": ["식각 단계를 포함", "", "증착 및 식각", "", "y"],
        "claims_independent": ["", "an etch step", "", "a sketch", ""],
        "ipc": [["H01J_37-32"], ["H01L21/3065"], ["C23C16-44"], [], []],
    })


@pytest.fixture()
def emu(corpus, tmp_path):
    conc = tmp_path / "conc.csv"
    conc.write_text("from_symbol,to_symbol\nH01L21/3065,H10P50/20\n", encoding="utf-8")
    return K.Emulator(corpus, K.Concordance(conc))


def test_operators_match_upstream_spec(emu):
    assert emu.run("식각") == ["d1", "d3"]                    # 한글 부분 일치 · 비후보 d5 제외
    assert emu.run("etch") == ["d2"]                          # ASCII 단어 시작 접두 — sketch 불일치
    assert emu.run("식각+증착") == ["d1", "d3"]
    assert emu.run("식각*증착") == ["d3"]
    assert emu.run("식각 !증착") == ["d1"]                    # 공백 = AND
    assert emu.run('"플라즈마 식각"') == ["d1"]
    assert emu.run("식각", exclude=("d1",)) == ["d3"]
    assert emu.run("etch+식각", ipc=["H01L"]) == ["d2"]
    assert emu.run("etch+식각", ipc=["H10P50/20"]) == ["d2"]  # 판 대응 확장
    with pytest.raises(ValueError):
        emu.run("!식각")


def test_field_restriction(emu):
    assert emu.run("장치", fields=("AB", "CL")) == []         # 제목에만 있는 항
    assert emu.run("장치") == ["d1"]


@pytest.mark.skipif(not config.PILOT_PARITY.exists(), reason="별도 고정 자산 미반입 — make vendor-pilot")
def test_parity_with_upstream_on_logged_queries():
    """상류 에뮬레이터로 다시 돌린 결과 집합 해시와, 이식본의 결과 집합 해시가 전 검색식에서 같다."""
    base = json.loads(config.PILOT_PARITY.read_text(encoding="utf-8"))
    rows = base["rows"]
    if os.environ.get("PILOT_PARITY_FULL") != "1":     # 기본: 결정적 20식 표본(전수 3,156식은 약 30분 · 2026-10-17 일치)
        rows = sorted(rows, key=lambda r: hashlib.sha256(r["query"].encode()).hexdigest())[:20]
    cols = ["doc_id", "is_candidate", "title", "abstract", "claims_full", "claims_independent", "ipc"]
    emu = K.Emulator(pd.read_parquet(config.IR_CORPUS, columns=cols))
    bad = []
    for r in rows:
        res = emu.run(r["query"], ipc=r["ipc"] or None, exclude=(r["q"],))
        if hashlib.sha256("\n".join(sorted(res)).encode()).hexdigest() != r["sha256"]:
            bad.append(r["query"])
    assert not bad, f"이식본이 상류와 다른 검색식 {len(bad)}개"
    assert base["logged_size_mismatch"] == 0
