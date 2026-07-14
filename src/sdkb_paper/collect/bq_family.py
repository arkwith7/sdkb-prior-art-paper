"""말뭉치의 **DOCDB 패밀리 ID** 를 BigQuery `patents-public-data` 에서 가져온다 (§4.5 강건성).

**왜 필요한가.** 현행 중복 제거는 **출원번호 기준**이다(`preprocess/clean.py::dedup`). 같은 발명의
국내 분할·계속출원은 서로 다른 출원번호를 받으므로 그대로 남고, 시계열에서 **중복 계수**된다.
원고 §3.2·§4.5 가 패밀리 단위 중복 제거를 예고했으므로 실제로 수행한다.

**KIPRIS 로는 잴 수 없다.** 수집 원데이터에 우선권·패밀리 필드가 없다(컬럼 14개). 명칭 기반
대리 지표는 **날조**다 — 삼성 "반도체 패키지" 1,483건·"반도체 장치" 1,394건은 같은 발명이 아니라
한국 특허의 일반명 관행이다. 패밀리는 `family_id` 조인 외에 정직하게 잴 방법이 없다.

조인 키는 `bq_cpc` 에서 검증된 것과 같다: KIPRIS 출원번호 13자리(`1020100000075`) 에서 앞 `10` 을
뺀 11자리가 BQ 의 `application_number`(`KR-20100000075-A`) 숫자부다.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from sdkb_paper.config import RAW_BQ, get_secret

FAMILY_MAP = RAW_BQ / "family_map.parquet"

# 한 출원(application)에 공개공보 A·등록공보 B1 이 따로 있어 publication 행이 여럿일 수 있다.
# 같은 출원이면 family_id 는 같으므로 DISTINCT 로 접는다.
FAMILY_SQL = """
SELECT DISTINCT
  REGEXP_EXTRACT(p.application_number, r'KR-(\\d+)-') AS bq_app,
  p.family_id
FROM `patents-public-data.patents.publications` AS p
WHERE p.country_code = 'KR'
  AND REGEXP_EXTRACT(p.application_number, r'KR-(\\d+)-') IN UNNEST(@apps)
"""


def _client():
    from google.cloud import bigquery

    get_secret("GOOGLE_APPLICATION_CREDENTIALS")  # 경로는 시크릿이다 (CLAUDE.md §1.7)
    return bigquery.Client()


def fetch_family(application_numbers: list[str], out: Path = FAMILY_MAP) -> pd.DataFrame:
    """KIPRIS 출원번호 -> DOCDB family_id (출원 1건에 1행). raw 에 저장한다(커밋하지 않는다)."""
    from google.cloud import bigquery

    client = _client()
    job = client.query(
        FAMILY_SQL,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ArrayQueryParameter("apps", "STRING", [a[2:] for a in application_numbers])
            ]
        ),
    )
    df = job.to_dataframe()
    df["application_number"] = "10" + df["bq_app"]
    df = df[["application_number", "family_id"]].astype(str).drop_duplicates()

    RAW_BQ.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    return df


def corpus_application_numbers() -> list[str]:
    """패밀리를 받아야 할 출원번호 = **두 말뭉치 ∪ G₀ 의 특허**.

    G₀(SIRP 1,000건)를 포함하는 이유: 델타 특허가 G₀ 특허와 **같은 패밀리**일 수 있다. 그때
    그 델타 특허는 새 발명이 아니라 G₀ 에 이미 있는 발명의 국내 중복 출원이다. G₀ 는 동결이라
    건드리지 않고 **델타 쪽을 뺀다** — before 는 한 트리플도 움직이지 않는다.
    """
    from sdkb_paper.preprocess.clean import g0_application_numbers
    from sdkb_paper.preprocess.profile import PERIODS

    apps: list[str] = []
    for _, delta_path, *_ in PERIODS.values():
        if delta_path.exists():
            apps.extend(pd.read_parquet(delta_path)["application_number"].tolist())
    apps.extend(g0_application_numbers())
    return sorted({a for a in apps if len(a) == 13})


def load_family(path: Path = FAMILY_MAP) -> dict[str, str]:
    """{출원번호: family_id}. 조인되지 않은 출원은 키가 없다 — 결측이 아니라 **미상**이고,
    미상은 dedup 하지 않는다(§4.5 동결 규칙 1). 파일이 없으면 예외 — 조용히 빈 값으로 넘어가면
    dedup 이 무효과가 되어 '수행했다'는 거짓 보고가 된다."""
    df = pd.read_parquet(path)
    return dict(zip(df["application_number"], df["family_id"].astype(str), strict=True))


def main() -> int:
    apps = corpus_application_numbers()
    df = fetch_family(apps)
    hit = df["application_number"].nunique()
    valid = df[df["family_id"] != "-1"]["application_number"].nunique()
    print(f"✓ family {len(df):,}행 → {FAMILY_MAP}")
    print(f"  조인 {hit:,}/{len(apps):,} ({hit / len(apps):.1%})"
          f" · family_id 유효 {valid:,} ({valid / len(apps):.1%})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
