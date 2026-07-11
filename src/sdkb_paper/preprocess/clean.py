"""수집 원시 데이터 정규화 + 패밀리 단위 중복 제거."""
from __future__ import annotations

import pandas as pd


def normalize_kipris(df: pd.DataFrame) -> pd.DataFrame:
    """날짜 파싱, 공백 정리, IPC 메인그룹 추출."""
    out = df.copy()
    out["application_date"] = pd.to_datetime(out["application_date"], format="%Y%m%d", errors="coerce")
    out["ipc_main"] = out["ipc"].str.split("|").str[0].str.strip()
    out = out.dropna(subset=["application_number", "application_date"])
    return out.drop_duplicates(subset=["application_number"])


def dedup_by_family(df: pd.DataFrame, family_map: pd.DataFrame) -> pd.DataFrame:
    """패밀리 ID 기준으로 대표 출원(최초 출원일)만 남긴다.

    family_map: bq_family.fetch_family_map 산출물 (application_number <-> family_id)
    """
    merged = df.merge(family_map, on="application_number", how="left")
    merged["family_id"] = merged["family_id"].fillna(merged["application_number"])
    return (
        merged.sort_values("application_date")
        .groupby("family_id", as_index=False)
        .first()
    )
