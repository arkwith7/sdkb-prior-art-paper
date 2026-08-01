"""신규 출원번호 → DOCDB simple family (결정 D · PLAN-032 §5.0·§5.2).

**왜 새 함수인가.** `bq_family_ir.build_family_map()` 은 입력이 `IR_CORPUS` 의 `doc_id` 로
고정돼 있어(`bq_family_ir.py:121`) B층 *후보* 의 신규 출원번호를 풀지 못한다. 같은 `APP_SQL`
(KR 출원번호 → family_id)을 임의 목록에 재사용하되 **기존 함수는 건드리지 않는다** — 그것은
IR 코퍼스 40,552 문서의 패밀리 지도를 만든 산출물이고, 고치면 주지표의 재현 좌표가 흔들린다.

**A층 쪽 배제 집합은 조회하지 않는다.** `split.parquet` 이 1,000행 전부에 `family_id` 를 갖고
있고 해상도가 docdb-app 998 / fallback-self 2(고유 패밀리 959)다 — 이미 저장소 안에 있다.

**미조인은 `self:` 가 아니라 `None` 이다.** `bq_family_ir` 은 미조인 문서에 자기 자신을 패밀리로
주지만(코퍼스 dedup 용), B층에서는 미조인 = **판정 불능 = 보수적 배제**(PLAN-031 §8 항목 8)라
타입으로 구분해야 조용히 통과하는 일이 없다.
"""
from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from sdkb_paper.config import B_LAYER_KR_FAMILY_MAP, IR_SPLIT

# KIPRIS 출원번호는 13자리(`10` + 11자리), BQ 는 앞 `10` 이 없다 — `bq_family_ir.py:139` 와 동일 규약.
_KR_APP_LEN = 13


def load_a_layer_exclusions(split_path: Path = IR_SPLIT) -> tuple[frozenset[str], frozenset[str]]:
    """A층 1,000건의 (출원번호 집합, 패밀리 집합) — 배제 2·1의 좌변.

    `doc_id` 는 `kr_1019970082313` 형식이므로 접두 `kr_` 를 떼면 KIPRIS 출원번호다.
    """
    df = pd.read_parquet(split_path, columns=["doc_id", "family_id"])
    apps = {d.split("_", 1)[1] for d in df["doc_id"].astype(str) if "_" in d}
    families = set(df["family_id"].astype(str))
    return frozenset(apps), frozenset(families)


# KR 전량 지도. `APP_SQL` 과 **같은 테이블·같은 키·같은 dedup 규칙**이고 `IN UNNEST(@apps)`
# 만 없다 — 그 조건은 스캔량을 줄이지 못하므로(파라미터 무관 5.22 GB 고정) 후보별 조회는
# 같은 값을 수백 번 다시 사는 것이다. 사전순 최소는 `MIN()` 으로 서버에서 집행한다.
KR_MAP_SQL = """
SELECT
  REGEXP_EXTRACT(application_number, r'KR-(\\d+)-') AS bq_app,
  MIN(family_id) AS family_id
FROM `patents-public-data.patents.publications`
WHERE country_code = 'KR'
  AND family_id IS NOT NULL AND family_id != '-1'
  AND REGEXP_EXTRACT(application_number, r'KR-(\\d+)-') IS NOT NULL
GROUP BY bq_app
"""


def load_kr_family_map(
    cache: Path = B_LAYER_KR_FAMILY_MAP, *, refresh: bool = False, dry_run: bool = False
) -> dict[str, str]:
    """KR 출원번호(11자리) → family_id 전량 지도. **BigQuery 조회는 1회뿐이다.**

    적재분은 `cache` 에 parquet 로 남고 재실행은 무조회로 같은 값을 돌려준다 = 재현 좌표.
    `refresh=True` 로만 다시 조회한다 — 파일럿 도중 지도가 바뀌면 배제 1의 판정이 흔들린다.
    """
    if cache.exists() and not refresh:
        df = pd.read_parquet(cache)
        return dict(zip(df["bq_app"].astype(str), df["family_id"].astype(str), strict=True))

    from sdkb_paper.collect.bq_family_ir import _client, _dry_run, _run

    client = _client()
    if dry_run:
        scanned = _dry_run(client, KR_MAP_SQL, [])
        print(f"[dry-run] KR 패밀리 지도 1회 적재 · 스캔 {scanned/1e9:.2f} GB "
              f"· 추정비용 ${scanned/1e12*6.25:.4f}")
        return {}

    df = _run(client, KR_MAP_SQL, []).dropna().astype(str)
    cache.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(cache, index=False)
    return dict(zip(df["bq_app"], df["family_id"], strict=True))


def resolve_from_map(app: str, kr_map: dict[str, str]) -> str | None:
    """지도 조회. 미조인은 `None`(= 판정 불능 = 보수적 배제) — `resolve_families` 와 동일 규약."""
    if len(app) != _KR_APP_LEN or not app.isdigit():
        return None
    return kr_map.get(app[2:])


def resolve_families(
    app_numbers: Sequence[str], *, dry_run: bool = False
) -> dict[str, str | None]:
    """KR 출원번호 → DOCDB family_id. 미조인은 `None`(= 판정 불능).

    배치 1회로 전량 조회한다 — BigQuery 는 KIPRIS 예산과 무관하고, 호출을 쪼개면 스캔량만 는다.
    `dry_run` 은 스캔 바이트만 출력하고 전부 `None` 을 돌려준다(비용 사전 보고용).
    """
    from google.cloud import bigquery

    from sdkb_paper.collect.bq_family_ir import APP_SQL, _client, _dry_run, _run

    targets = sorted({a for a in app_numbers if len(a) == _KR_APP_LEN and a.isdigit()})
    unresolved: dict[str, str | None] = dict.fromkeys(app_numbers)
    if not targets:
        return unresolved

    params = [bigquery.ArrayQueryParameter("apps", "STRING", [a[2:] for a in targets])]
    client = _client()
    if dry_run:
        scanned = _dry_run(client, APP_SQL, params)
        print(f"[dry-run] B층 패밀리 조회 {len(targets):,}건 · 스캔 {scanned/1e9:.2f} GB "
              f"· 추정비용 ${scanned/1e12*6.25:.4f}")
        return unresolved

    df = _run(client, APP_SQL, params)
    # 한 출원번호에 family_id 가 여럿이면 사전순 최소 — `bq_family_ir` 과 동일한 결정성 규약.
    app_map = (
        df.dropna().astype(str).sort_values("family_id")
        .drop_duplicates("bq_app").set_index("bq_app")["family_id"].to_dict()
    )
    for app in targets:
        unresolved[app] = app_map.get(app[2:])
    return unresolved
