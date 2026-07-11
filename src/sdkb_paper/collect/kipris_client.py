"""KIPRIS Plus Open API 수집기.

설계 원칙
- 모든 응답은 로컬 SQLite 캐시에 저장 → 재실행 시 API 를 다시 때리지 않음 (증분 수집)
- 재시도(backoff) 내장, 무제한 자격이어도 서버 예의상 요청 간격 유지
- 원시 XML 을 그대로 캐시하고, 파싱은 별도 단계로 분리 (파서 버그 시 재수집 불필요)

주의: ENDPOINT/파라미터 명은 발급받은 API 명세(활용 신청한 서비스)에 맞춰
반드시 확인·조정할 것. 아래 값은 특허 검색용 대표 서비스 기준의 골격이다.
"""
from __future__ import annotations

import hashlib
import sqlite3
import time
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import requests

from sdkb_paper.config import RAW_KIPRIS, get_secret

BASE_URL = "http://plus.kipris.or.kr/kipo-api/kipi"
# TODO: 활용 신청한 서비스명으로 확인 (예: 특허실용신안 검색 서비스)
SEARCH_ENDPOINT = f"{BASE_URL}/patUtiModInfoSearchSevice/getAdvancedSearch"

DEFAULT_ROWS = 100  # 페이지당 건수 (명세 허용 최대치로 조정)
REQUEST_INTERVAL_SEC = 0.2
MAX_RETRIES = 5


@dataclass
class KiprisRecord:
    """파싱된 특허 1건 (필요 필드만 우선 정의, 명세 보고 확장)."""

    application_number: str
    title: str
    applicant: str
    application_date: str  # YYYYMMDD
    ipc: str
    abstract: str


class KiprisClient:
    def __init__(self, cache_db: Path | None = None, api_key: str | None = None):
        self.api_key = api_key or get_secret("KIPRIS_API_KEY")
        RAW_KIPRIS.mkdir(parents=True, exist_ok=True)
        self.cache = sqlite3.connect(cache_db or RAW_KIPRIS / "kipris_cache.sqlite")
        self.cache.execute(
            "CREATE TABLE IF NOT EXISTS responses ("
            " key TEXT PRIMARY KEY, url TEXT, params TEXT,"
            " fetched_at TEXT DEFAULT CURRENT_TIMESTAMP, body TEXT)"
        )
        self.session = requests.Session()

    # --- 저수준: 캐시 우선 GET -------------------------------------------
    def _get(self, url: str, params: dict) -> str:
        key_src = url + "?" + "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        key = hashlib.sha256(key_src.encode()).hexdigest()
        row = self.cache.execute("SELECT body FROM responses WHERE key=?", (key,)).fetchone()
        if row:
            return row[0]

        last_err: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                resp = self.session.get(
                    url, params={**params, "ServiceKey": self.api_key}, timeout=30
                )
                resp.raise_for_status()
                body = resp.text
                self.cache.execute(
                    "INSERT OR REPLACE INTO responses (key, url, params, body) VALUES (?,?,?,?)",
                    (key, url, key_src, body),
                )
                self.cache.commit()
                time.sleep(REQUEST_INTERVAL_SEC)
                return body
            except requests.RequestException as e:  # 지수 백오프 재시도
                last_err = e
                time.sleep(2**attempt)
        raise RuntimeError(f"KIPRIS request failed after {MAX_RETRIES} retries") from last_err

    # --- 고수준: 검색 페이지네이션 ----------------------------------------
    def search(self, query: str, max_pages: int | None = None) -> Iterator[KiprisRecord]:
        """검색식으로 전 페이지 순회하며 레코드를 yield.

        query 예 (명세 확인 후 조정):
            'AP=[삼성전자]*IPC=[H01L]' 류의 KIPRIS 검색식
        """
        page = 1
        while True:
            body = self._get(
                SEARCH_ENDPOINT,
                {"word": query, "numOfRows": DEFAULT_ROWS, "pageNo": page},
            )
            items = self._parse_items(body)
            if not items:
                break
            yield from items
            page += 1
            if max_pages and page > max_pages:
                break

    @staticmethod
    def _parse_items(xml_body: str) -> list[KiprisRecord]:
        """응답 XML → 레코드. 태그명은 실제 응답 샘플을 보고 맞출 것."""
        root = ET.fromstring(xml_body)
        records: list[KiprisRecord] = []
        for item in root.iter("item"):

            def txt(tag: str) -> str:
                el = item.find(tag)
                return (el.text or "").strip() if el is not None else ""

            records.append(
                KiprisRecord(
                    application_number=txt("applicationNumber"),
                    title=txt("inventionTitle"),
                    applicant=txt("applicantName"),
                    application_date=txt("applicationDate"),
                    ipc=txt("ipcNumber"),
                    abstract=txt("astrtCont"),
                )
            )
        return records


def collect_to_parquet(query: str, out_name: str, max_pages: int | None = None) -> Path:
    """검색 결과를 parquet 로 저장하고 MANIFEST 갱신을 잊지 말 것."""
    import pandas as pd

    client = KiprisClient()
    df = pd.DataFrame([r.__dict__ for r in client.search(query, max_pages=max_pages)])
    out = RAW_KIPRIS / f"{out_name}.parquet"
    df.to_parquet(out, index=False)
    print(f"saved {len(df)} records -> {out}")
    return out
