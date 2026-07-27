"""시점 분할(B8 · F9) 단위 테스트 — family-disjoint·결정성·경계 체크섬 (corpus/split)."""
from __future__ import annotations

import pandas as pd
import pytest

from sdkb_paper.corpus import split as S


def _corpus(rows):
    # rows: (doc_id, filing_date)
    df = pd.DataFrame(rows, columns=["doc_id", "filing_date"])
    df["is_query"] = True
    return df


def test_family_disjoint_and_deterministic(monkeypatch):
    # 10 질의 · fraction (0.6,0.2,0.2) → train 6 / dev 2 / test 2.
    # a,b 는 같은 family(F_ab) → 절대 분리되지 않는다.
    rows = [(f"q{i}", f"20{10+i:02d}-01-01") for i in range(10)]
    corpus = _corpus(rows)
    fam = {f"q{i}": f"F{i}" for i in range(10)}
    fam["q0"] = fam["q1"] = "F_ab"          # q0,q1 같은 family
    monkeypatch.setattr(S.config, "F9_SPLIT_FRACTIONS", (0.6, 0.2, 0.2))
    # 경계 체크섬 우회: build_split 이 config 경계와 대조하므로 실제 경계로 맞춘다.
    # 정렬: F_ab(2010), F2(2012)…F9(2019). 누적 절단 확인만.
    monkeypatch.setattr(S.config, "F9_BOUNDARY_TRAIN_DEV", "2016-01-01")
    monkeypatch.setattr(S.config, "F9_BOUNDARY_DEV_TEST", "2018-01-01")
    out = S.build_split(corpus, fam)
    # 결정성: 재실행 동일
    out2 = S.build_split(corpus, fam)
    pd.testing.assert_frame_equal(out, out2)
    # family-disjoint: q0,q1 같은 split
    s = dict(zip(out["doc_id"], out["split"]))
    assert s["q0"] == s["q1"]
    # 비율 대략 60/20/20
    vc = out["split"].value_counts().to_dict()
    assert vc["train"] == 6 and vc["dev"] == 2 and vc["test"] == 2


def test_boundary_checksum_detects_drift(monkeypatch):
    rows = [(f"q{i}", f"20{10+i:02d}-01-01") for i in range(10)]
    corpus = _corpus(rows)
    fam = {f"q{i}": f"F{i}" for i in range(10)}
    monkeypatch.setattr(S.config, "F9_SPLIT_FRACTIONS", (0.6, 0.2, 0.2))
    monkeypatch.setattr(S.config, "F9_BOUNDARY_TRAIN_DEV", "1999-01-01")  # 틀린 값
    monkeypatch.setattr(S.config, "F9_BOUNDARY_DEV_TEST", "2018-01-01")
    with pytest.raises(SystemExit, match="경계 표류"):
        S.build_split(corpus, fam)


def test_missing_filing_date_fails(monkeypatch):
    corpus = _corpus([("q0", None), ("q1", "2010-01-01")])
    fam = {"q0": "F0", "q1": "F1"}
    with pytest.raises(SystemExit, match="출원일 결측"):
        S.build_split(corpus, fam)
