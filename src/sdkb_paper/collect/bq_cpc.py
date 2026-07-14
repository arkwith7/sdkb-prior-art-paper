"""말뭉치의 **CPC 코드**를 BigQuery `patents-public-data` 에서 가져온다 (H2 대조군 교정).

**왜 필요한가 (실측된 결함).** KIPRIS `getAdvancedSearch` 는 **IPC 만** 준다. 그런데 H2 의 대조
코드 7개 중 2개(`H10D30/6735` GAA · `H10W20/211` TSV)는 CPC 스킴에서 중괄호로 표시된
**CPC 전용 코드**라 IPC 말뭉치에 **존재할 수 없다** — 34,521건에서 출현 0회다. 그 "코드 미탐지"는
코드 단위 시계열의 실패가 아니라 **분류체계 불일치**이고, H2 에 유리하게 작동하는 인공물이다.

두 팔(개념 · 코드)을 같은 분류체계 위에 올리기 위해 CPC 를 별도로 수집한다.
**임계값을 움직이는 것이 아니라 측정 도구를 고치는 것이다.** 다만 사전등록 결과를 본 뒤의
변경이므로, 사전등록 검정(IPC 대조군 · p=0.5)과 교정 후 검정을 **둘 다** 보고한다.

조인 키: KIPRIS 출원번호 13자리(`1020100000075`) 에서 앞 `10` 을 뺀 11자리가 BQ 의
`application_number`(`KR-20100000075-A`) 숫자부다 (표본 200건 100% 일치로 확인).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from sdkb_paper.config import RAW_BQ, get_secret

CPC_MAP = RAW_BQ / "cpc_map.parquet"

CPC_SQL = """
SELECT
  REGEXP_EXTRACT(p.application_number, r'KR-(\\d+)-') AS bq_app,
  cpc.code AS cpc_code
FROM `patents-public-data.patents.publications` AS p,
     UNNEST(p.cpc) AS cpc
WHERE p.country_code = 'KR'
  AND REGEXP_EXTRACT(p.application_number, r'KR-(\\d+)-') IN UNNEST(@apps)
"""


def _client():
    from google.cloud import bigquery

    # 서비스계정 키 경로는 시크릿이다 — 하드코딩하지 않는다 (CLAUDE.md §1.7).
    # GOOGLE_APPLICATION_CREDENTIALS 가 있으면 google-auth 가 알아서 쓴다.
    get_secret("GOOGLE_APPLICATION_CREDENTIALS")
    return bigquery.Client()


def fetch_cpc(application_numbers: list[str], out: Path = CPC_MAP) -> pd.DataFrame:
    """KIPRIS 출원번호 -> CPC 코드 (특허 1건에 여러 행). 결과는 raw 에 저장한다(커밋하지 않는다)."""
    from google.cloud import bigquery

    client = _client()
    job = client.query(
        CPC_SQL,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ArrayQueryParameter("apps", "STRING", [a[2:] for a in application_numbers])
            ]
        ),
    )
    df = job.to_dataframe()
    df["application_number"] = "10" + df["bq_app"]
    df = df[["application_number", "cpc_code"]].drop_duplicates()

    RAW_BQ.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    return df


# ── 당시(vintage) 분류 — PLAN-007 ────────────────────────────────────────
# BigQuery 는 날짜별 **동결 스냅샷** 테이블을 보존한다. 연도 T 의 관측자는 T 이하의 가장 가까운
# 스냅샷만 볼 수 있다 — 그 스냅샷이 그때의 분류체계다.
#
# 왜 필요한가: H10 스킴(H10B·H10D·H10W)은 **전량 2021년 이후의 소급 재분류**다. 2017-10 과
# 2021-01 스냅샷에는 H10 코드가 **0개**인데 현재 스냅샷에는 588k 행이 있다. 즉 사전등록한 대조
# 코드 7개는 2022년 이전 어느 시점에도 존재하지 않았고, 지금은 2010년 출원에까지 붙어 있다.
# 현재 스냅샷으로 만든 코드 시계열은 **구조적으로 늦을 수 없다** — H2 가 말하는 것을 재지 못한다.
VINTAGE_MAP = RAW_BQ / "cpc_vintage.parquet"

# 관측창(2010–2023)의 탐지 판정에 필요한 스냅샷만 받는다.
SNAPSHOTS = (201710, 201903, 202004, 202101, 202204, 202304)

# 연도 -> 그 해의 관측자가 볼 수 있는 스냅샷. 2010–2016 은 가장 이른 스냅샷(2017-10)으로
# **근사**한다 — 복원할 수 없는 구간이다. H10 대조 코드에 관한 한 이 근사는 안전하다(어느
# 쪽이든 0). 선행 코드 검정에는 편향을 줄 수 있으므로 논문 §5.3 에 적는다 (PLAN-007 §4).
SNAPSHOT_FOR_YEAR = {
    **{y: 201710 for y in range(2010, 2019)},
    2019: 201903,
    2020: 202004,
    2021: 202101,
    2022: 202204,
    2023: 202304,
}

VINTAGE_SQL = """
SELECT
  '{snap}' AS snapshot,
  REGEXP_EXTRACT(p.application_number, r'KR-(\\d+)-') AS bq_app,
  cpc.code AS cpc_code
FROM `patents-public-data.patents.publications_{snap}` AS p,
     UNNEST(p.cpc) AS cpc
WHERE p.country_code = 'KR'
  AND REGEXP_EXTRACT(p.application_number, r'KR-(\\d+)-') IN UNNEST(@apps)
"""


def fetch_vintage(application_numbers: list[str], out: Path = VINTAGE_MAP) -> pd.DataFrame:
    """스냅샷별 CPC 코드. 스냅샷에 **없는** 특허는 그때 관측자에게 보이지 않았던 것이다 —
    결측이 아니라 관측값이다 (미공개)."""
    from google.cloud import bigquery

    client = _client()
    apps = [a[2:] for a in application_numbers]
    cfg = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ArrayQueryParameter("apps", "STRING", apps)]
    )
    frames = []
    for snap in SNAPSHOTS:
        df = client.query(VINTAGE_SQL.format(snap=snap), job_config=cfg).to_dataframe()
        df["application_number"] = "10" + df["bq_app"]
        frames.append(df[["snapshot", "application_number", "cpc_code"]])
        print(f"  {snap}: {len(df):,}행 · 출원 {df['application_number'].nunique():,}")

    out_df = pd.concat(frames).drop_duplicates()
    RAW_BQ.mkdir(parents=True, exist_ok=True)
    out_df.to_parquet(out, index=False)
    return out_df


def load_vintage(path: Path = VINTAGE_MAP) -> dict[int, dict[str, list[str]]]:
    """{스냅샷: {출원번호: [코드...]}}. 그 스냅샷에 없는 출원은 키가 없다(= 미공개)."""
    df = pd.read_parquet(path)
    df["snapshot"] = df["snapshot"].astype(int)
    return {
        int(snap): sub.groupby("application_number")["cpc_code"].apply(list).to_dict()
        for snap, sub in df.groupby("snapshot")
    }


def load_cpc(path: Path = CPC_MAP) -> dict[str, list[str]]:
    """{KIPRIS 출원번호: [CPC 코드...]}. 파일이 없으면 예외 — 조용히 빈 값으로 넘어가면
    코드 팔이 통째로 0 이 되어 H2 가 거짓으로 지지된다."""
    df = pd.read_parquet(path)
    return df.groupby("application_number")["cpc_code"].apply(list).to_dict()


def corpus_application_numbers() -> list[str]:
    """CPC 를 받아야 할 출원번호 = **두 말뭉치의 합집합** (PLAN-009).

    2010–2025(G₁ 의 원천) ∪ 2005–2009(좌측절단 교정분). 합집합으로 한 번에 받는 이유는
    분리해서 받으면 `make cpc` 재실행이 다른 기간의 행을 덮어써 **코드 팔이 조용히 0 이 되기**
    때문이다 — 그러면 H2 가 거짓으로 지지된다.
    """
    from sdkb_paper.preprocess.profile import PERIODS

    apps: list[str] = []
    for _, delta_path, *_ in PERIODS.values():
        if delta_path.exists():
            apps.extend(pd.read_parquet(delta_path)["application_number"].tolist())
    return sorted(set(apps))


def main() -> int:
    import sys

    apps = corpus_application_numbers()

    if "--vintage" in sys.argv:  # PLAN-007
        df = fetch_vintage(apps)
        print(f"✓ vintage {len(df):,}행 · 스냅샷 {df['snapshot'].nunique()}개 → {VINTAGE_MAP}")
        return 0

    df = fetch_cpc(apps)
    covered = df["application_number"].nunique()
    print(f"✓ CPC {len(df):,}행 · 출원 {covered:,}/{len(apps):,} ({covered / len(apps):.1%}) → {CPC_MAP}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
