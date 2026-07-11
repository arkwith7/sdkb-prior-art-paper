"""Google BigQuery patents-public-data 에서 DOCDB 패밀리 매핑을 가져온다.

역할: KIPRIS 로 수집한 KR 출원번호 <-> 글로벌 패밀리 ID 조인 테이블 생성.
사전 준비: GCP 프로젝트 + `pip install -e .[bq]` + 인증(gcloud auth application-default login)
"""
from __future__ import annotations

from pathlib import Path

from sdkb_paper.config import RAW_BQ

# KR 출원번호 포맷(1020200012345) <-> BigQuery publication 포맷(KR-1020200012345-A) 변환에 주의
FAMILY_SQL = """
SELECT
  p.publication_number,
  p.family_id,
  p.filing_date,
  cpc.code AS cpc_code
FROM `patents-public-data.patents.publications` AS p,
     UNNEST(p.cpc) AS cpc
WHERE p.country_code = 'KR'
  AND SUBSTR(p.application_number, 4) IN UNNEST(@app_numbers)
"""


def fetch_family_map(kr_application_numbers: list[str], out_name: str = "family_map") -> Path:
    from google.cloud import bigquery

    client = bigquery.Client()
    job = client.query(
        FAMILY_SQL,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ArrayQueryParameter("app_numbers", "STRING", kr_application_numbers)
            ]
        ),
    )
    df = job.to_dataframe()
    RAW_BQ.mkdir(parents=True, exist_ok=True)
    out = RAW_BQ / f"{out_name}.parquet"
    df.to_parquet(out, index=False)
    print(f"saved {len(df)} rows -> {out}")
    return out
