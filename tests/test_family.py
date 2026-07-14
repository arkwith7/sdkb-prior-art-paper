"""패밀리 dedup 의 네 규칙이 실제로 지켜지는가 (§4.5 강건성)."""
from __future__ import annotations

import pandas as pd

from sdkb_paper.preprocess.family import dedup_families, family_keys


def _corpus(rows):
    df = pd.DataFrame(rows, columns=["application_number", "application_date"])
    df["application_date"] = pd.to_datetime(df["application_date"])
    return df


def test_unknown_family_is_never_deduped():
    """규칙 1 — 조인 실패와 '-1' 은 각각 고유 패밀리다. 지우면 표본 삭제다."""
    df = _corpus([("1020100000001", "2010-01-01"), ("1020100000002", "2010-02-01")])
    kept, dropped = dedup_families(df, {"1020100000001": "-1"})  # 2번은 아예 미조인
    assert len(kept) == 2
    assert dropped.empty


def test_shared_family_id_links_applications():
    """규칙 2 — 같은 family_id 를 공유하면 한 패밀리. 가장 이른 출원만 남는다."""
    df = _corpus([("1020100000009", "2011-05-01"), ("1020100000001", "2010-01-01")])
    fam = {"1020100000009": "777", "1020100000001": "777"}
    kept, dropped = dedup_families(df, fam)
    assert list(kept["application_number"]) == ["1020100000001"]  # 최소 출원일
    assert list(dropped["drop_reason"]) == ["family_dup"]


def test_multi_family_id_per_application_is_one_family():
    """규칙 2 — BQ 는 한 출원에 id 를 둘 붙인다(말뭉치의 9.6%). id 하나로 그룹핑하면 같은
    발명이 두 패밀리로 쪼개져 dedup 이 헛돈다. 연결성분으로 묶여야 한다."""
    fam = pd.DataFrame(
        [
            ("1020100000001", "36641129"),
            ("1020100000001", "43681853"),  # 같은 출원, 다른 id
            ("1020100000002", "43681853"),  # 그 id 를 공유 → 같은 패밀리
        ],
        columns=["application_number", "family_id"],
    )
    keys = family_keys(["1020100000001", "1020100000002"], fam)
    assert keys["1020100000001"] == keys["1020100000002"]


def test_tie_broken_by_application_number():
    """규칙 3 — 출원일이 같으면 최소 출원번호. 결정적이어야 한다(입력 순서 무관)."""
    rows = [("1020100000009", "2010-01-01"), ("1020100000001", "2010-01-01")]
    fam = {"1020100000009": "777", "1020100000001": "777"}
    a, _ = dedup_families(_corpus(rows), fam)
    b, _ = dedup_families(_corpus(rows[::-1]), fam)
    assert list(a["application_number"]) == list(b["application_number"]) == ["1020100000001"]


def test_g0_family_members_are_dropped_from_delta():
    """규칙 4 — G₀ 와 패밀리를 공유하는 델타 특허는 델타에서 뺀다. G₀ 는 동결이라 그 자신은
    dedup 되지 않는다 — H1 의 before 가 움직이면 H1 이 재현되지 않는다."""
    df = _corpus([("1020100000002", "2010-02-01")])  # 델타
    fam = {"1019990000001": "555", "1020100000002": "555"}  # G₀ 특허와 같은 패밀리
    kept, dropped = dedup_families(df, fam, g0_apps={"1019990000001"})
    assert kept.empty
    assert list(dropped["drop_reason"]) == ["g0_family"]


def test_g0_family_does_not_drop_unrelated_delta():
    df = _corpus([("1020100000002", "2010-02-01")])
    fam = {"1019990000001": "555", "1020100000002": "999"}
    kept, _ = dedup_families(df, fam, g0_apps={"1019990000001"})
    assert len(kept) == 1


def test_empty_corpus():
    kept, dropped = dedup_families(_corpus([]), {})
    assert kept.empty and dropped.empty
