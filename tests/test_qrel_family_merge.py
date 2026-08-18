"""PLAN-057 병합 규칙의 단위 검증 — 동결 규칙 R1·R3·R5·R7 이 코드에 실재하는가."""
from __future__ import annotations

import pandas as pd

from sdkb_paper.corpus import qrel_family_merge as m


def test_r1_only_x_or_y_categories():
    """R1 — X·Y 를 포함한 범주만 거절 근거로 채택하고 A·I 단독은 제외한다."""
    keep = ["X", "Y", "XY", "YX", "XI", "XA", "YA", "XYI", "XAI"]
    drop = ["A", "I", "", None, "L", "P"]
    s = pd.Series(keep + drop, dtype="object")
    hit = s.fillna("").str.contains(m.XY_RE, na=False)
    assert list(hit[: len(keep)]) == [True] * len(keep)
    assert list(hit[len(keep) :]) == [False] * len(drop)


def test_r3_bq_key_matches_normalize_pub_rule():
    """R3 — 공개번호 키는 국가 + 앞 0 제거 숫자부다(기존 규칙과 같은 공간)."""
    assert m._bq_key("US-1234567-A") == "US1234567"
    assert m._bq_key("JP-0007654-B2") == "JP7654"
    assert m._bq_key("WO-2011012345-A1") == "WO2011012345"
    assert m._bq_key("NPL text without number") is None
    assert m._bq_key(None) is None


def test_r7_test_b_is_not_merged(monkeypatch):
    """R7 — `test_b` 는 병합하지 않는다. 증분 1쌍을 위해 봉인 파생본을 만들지 않는다."""
    calls = {}

    def fake_load(split, **kw):
        calls["split"] = split
        return {"q1": {"d1"}}

    monkeypatch.setattr("sdkb_paper.analysis.metrics.load_qrel_for_split", fake_load)
    out = m.merged_qrel("test_b")
    assert out == {"q1": {"d1"}}          # 병합분이 더해지지 않는다


def test_merged_qrel_adds_only_to_known_queries(monkeypatch, tmp_path):
    """R5 — 병합분은 기존 질의에만 붙고 relevance 는 1 이며 새 질의를 만들지 않는다."""
    add = pd.DataFrame({"query_id": ["q1", "q_unknown"], "doc_id": ["d2", "d9"],
                        "relevance": [1, 1]})
    p = tmp_path / "merged.parquet"
    add.to_parquet(p, index=False)
    monkeypatch.setattr(m, "QREL_MERGED", p)
    monkeypatch.setattr("sdkb_paper.analysis.metrics.load_qrel_for_split",
                        lambda split, **kw: {"q1": {"d1"}})
    out = m.merged_qrel("test")
    assert out["q1"] == {"d1", "d2"}
    assert "q_unknown" not in out
