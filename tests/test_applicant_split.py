"""출원인별 분리가 **분할**인가 — 누락도 중복도 없어야 한다 (§4.5.2)."""
from __future__ import annotations

import pandas as pd

from sdkb_paper.preprocess.clean import TARGET_APPLICANTS, filter_applicants


def _corpus():
    return pd.DataFrame({
        "application_number": ["1", "2", "3", "4"],
        "applicant_name": [
            "삼성전자주식회사",
            "에스케이하이닉스 주식회사",
            "삼성전자주식회사",
            "삼성디스플레이 주식회사",  # 계열사 — 말뭉치에 없어야 한다
        ],
    })


def test_split_partitions_the_corpus():
    """두 팔의 합이 말뭉치와 같고, 교집합이 비어야 한다. 어긋나면 §4.5.2 의 두 팔이
    같은 특허를 세거나(중복) 어떤 특허도 세지 않는다(누락)."""
    df = filter_applicants(_corpus())
    arms = {a: df[df["applicant_name"] == a] for a in TARGET_APPLICANTS}

    assert sum(len(x) for x in arms.values()) == len(df)
    apps = [set(x["application_number"]) for x in arms.values()]
    assert apps[0] & apps[1] == set()


def test_affiliates_are_excluded_before_split():
    """계열사(삼성디스플레이)는 분리 이전에 이미 빠져 있어야 한다 — 정확일치 필터의 계약."""
    df = filter_applicants(_corpus())
    assert set(df["applicant_name"]) <= set(TARGET_APPLICANTS)
    assert "4" not in set(df["application_number"])
