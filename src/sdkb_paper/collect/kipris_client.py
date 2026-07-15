"""KIPRIS Plus 고급검색 수집기 (PLAN-002).

계약은 실물 응답으로 확인한 것이다 (2026-07-13):
  ENDPOINT  patUtiModInfoSearchSevice/getAdvancedSearch
  파라미터   applicant · ipcNumber · applicationDate(YYYYMMDD~YYYYMMDD) · numOfRows(≤500)
            · pageNo · patent/utility · ServiceKey
  응답      <item> 아래 applicationNumber(하이픈 없음) · applicationDate(YYYYMMDD)
            · applicantName · inventionTitle · ipcNumber('|' 구분) · astrtCont
            · openDate · registerDate · registerStatus

주의
- `applicant` 는 **부분일치**다. '삼성전자주식회사' 로 질의해도 삼성디스플레이가 섞여 나온다.
  applicantName 정확일치 필터는 preprocess 의 책임이다 (수집기는 가져오기만 한다).
- **CPC 는 응답에 없다 — IPC 만 온다.**

모든 응답을 sqlite 에 캐시한다. 재실행해도 API 를 다시 때리지 않는다(증분 수집).
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

_BASE = "http://plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchSevice"
ENDPOINT = f"{_BASE}/getAdvancedSearch"
# 서지상세: 출원번호 1건당 **초록 + 전체 청구항(claimCount 포함)**. getAdvancedSearch 는 청구항을
# 주지 않는다 — IP-R&D FTO 자기완결성을 위해 청구항 전문이 필요해 이 엔드포인트를 쓴다 (RQ3).
# 인증은 ServiceKey 다(accessKey 는 INVALID_REQUEST_PARAMETER_ERROR).
DETAIL_ENDPOINT = f"{_BASE}/getBibliographyDetailInfoSearch"
PAGE_SIZE = 500  # 실측 상한 (500 초과 요청은 500 으로 잘린다)
REQUEST_INTERVAL_SEC = 0.2
MAX_RETRIES = 4


@dataclass(frozen=True)
class KiprisRecord:
    application_number: str
    applicant_name: str
    application_date: str  # YYYYMMDD
    invention_title: str
    ipc_number: str  # '|' 구분
    abstract: str
    open_date: str
    register_date: str
    register_status: str
    query_applicant: str  # 출처 추적 — 어느 질의가 이 행을 가져왔는가
    query_ipc: str


class KiprisClient:
    def __init__(self, cache_db: Path | None = None, api_key: str | None = None):
        self.api_key = api_key or get_secret("KIPRIS_API_KEY")
        RAW_KIPRIS.mkdir(parents=True, exist_ok=True)
        self.cache = sqlite3.connect(cache_db or RAW_KIPRIS / "kipris_cache.sqlite")
        self.cache.execute(
            "CREATE TABLE IF NOT EXISTS responses ("
            " key TEXT PRIMARY KEY, params TEXT,"
            " fetched_at TEXT DEFAULT CURRENT_TIMESTAMP, body TEXT)"
        )
        self.session = requests.Session()

    def _get(self, params: dict, endpoint: str = ENDPOINT) -> str:
        key_src = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        key = hashlib.sha256(key_src.encode()).hexdigest()
        row = self.cache.execute("SELECT body FROM responses WHERE key=?", (key,)).fetchone()
        if row:
            return row[0]

        last: Exception | None = None
        for attempt in range(MAX_RETRIES):
            try:
                resp = self.session.get(
                    endpoint, params={**params, "ServiceKey": self.api_key}, timeout=60
                )
                resp.raise_for_status()
                # 실패 응답을 캐시하면 재실행해도 에러가 되돌아온다 — 성공만 캐시한다.
                code = _result_code(resp.text)
                if code != "00":
                    raise RuntimeError(f"KIPRIS resultCode={code}")
                self.cache.execute(
                    "INSERT OR REPLACE INTO responses (key, params, body) VALUES (?,?,?)",
                    (key, key_src, resp.text),
                )
                self.cache.commit()
                time.sleep(REQUEST_INTERVAL_SEC)
                return resp.text
            except (requests.RequestException, RuntimeError) as e:
                last = e
                time.sleep(2**attempt)
        raise RuntimeError(f"KIPRIS 요청 실패: {key_src}") from last

    def _params(self, applicant: str, ipc: str, date_range: str, rows: int, page: int) -> dict:
        return {
            "applicant": applicant,
            "ipcNumber": ipc,
            "applicationDate": date_range,
            "numOfRows": rows,
            "pageNo": page,
            "patent": "true",
            "utility": "false",
        }

    def total_count(self, applicant: str, ipc: str, date_range: str) -> int:
        body = self._get(self._params(applicant, ipc, date_range, 1, 1))
        el = ET.fromstring(body).find(".//totalCount")
        return int(el.text) if el is not None and el.text else 0

    def search(self, applicant: str, ipc: str, date_range: str) -> Iterator[KiprisRecord]:
        """출원인 × IPC × 출원일 범위로 전 페이지를 순회한다."""
        page = 1
        while True:
            body = self._get(self._params(applicant, ipc, date_range, PAGE_SIZE, page))
            items = _parse(body, applicant, ipc)
            if not items:
                return
            yield from items
            page += 1

    def detail(self, application_number: str) -> PatentDetail:
        """출원번호 1건의 초록 + 전체 청구항. 응답은 캐시된다(재실행 무호출)."""
        body = self._get({"applicationNumber": application_number}, endpoint=DETAIL_ENDPOINT)
        return _parse_detail(body, application_number)


@dataclass(frozen=True)
class PatentDetail:
    application_number: str
    abstract: str
    claims: tuple[str, ...]  # 청구항 전문, 번호순 (선두 번호 보존: "1. …")
    claim_count: int         # KIPRIS claimCount — claims 길이보다 크면 미적재 신호


def _parse_detail(body: str, application_number: str) -> PatentDetail:
    root = ET.fromstring(body)
    # 네임스페이스·중첩 방어: 태그 끝으로 판별한다. <claim> 은 순서대로, <claimCount>·<astrtCont> 는 첫 값.
    claims = tuple(
        (e.text or "").strip()
        for e in root.iter()
        if e.tag.endswith("claim") and (e.text or "").strip()
    )
    abstract = next((e.text.strip() for e in root.iter()
                     if e.tag.endswith("astrtCont") and (e.text or "").strip()), "")
    cc = next((e.text for e in root.iter()
               if e.tag.endswith("claimCount") and (e.text or "").strip()), None)
    return PatentDetail(application_number, abstract, claims,
                        int(cc) if cc and cc.isdigit() else len(claims))


def _result_code(body: str) -> str:
    el = ET.fromstring(body).find(".//resultCode")
    return (el.text or "").strip() if el is not None and el.text else "??"


def _text(item: ET.Element, tag: str) -> str:
    el = item.find(tag)
    return (el.text or "").strip() if el is not None and el.text else ""


def _parse(body: str, applicant: str, ipc: str) -> list[KiprisRecord]:
    return [
        KiprisRecord(
            application_number=_text(item, "applicationNumber"),
            applicant_name=_text(item, "applicantName"),
            application_date=_text(item, "applicationDate"),
            invention_title=_text(item, "inventionTitle"),
            ipc_number=_text(item, "ipcNumber"),
            abstract=_text(item, "astrtCont"),
            open_date=_text(item, "openDate"),
            register_date=_text(item, "registerDate"),
            register_status=_text(item, "registerStatus"),
            query_applicant=applicant,
            query_ipc=ipc,
        )
        for item in ET.fromstring(body).iter("item")
    ]
