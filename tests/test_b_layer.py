"""B층 수집 드라이버 회귀 테스트 T1–T11 (PLAN-032 §5.8 · 승인 2026-08-01).

**전부 고정 픽스처로 돈다 — KIPRIS·BigQuery 를 호출하지 않는다.**
T6(A층 교집합 0)·T7(결정성)·T10(봉인)이 실패하면 예외 없이 수집을 중단한다.
"""
from __future__ import annotations

import dataclasses
import json

import pytest

from sdkb_paper.collect.b_layer import driver as drv
from sdkb_paper.collect.b_layer import ledger as ledger_mod
from sdkb_paper.collect.b_layer import report as report_mod
from sdkb_paper.collect.b_layer.biblio import is_patent_document, parse_biblio
from sdkb_paper.collect.b_layer.report import estimate_rates, wilson
from sdkb_paper.collect.b_layer.screen import (
    Reason,
    ScreenContext,
    leading_ipc,
    screen_detail,
    screen_family,
    screen_free,
)
from sdkb_paper.collect.b_layer.stream import iter_stream, merged_with_dups, sort_key
from sdkb_paper.collect.kipris_client import KiprisRecord

# --- 픽스처 --------------------------------------------------------------

CTX = ScreenContext(
    frozen_ipc=frozenset({"H10B", "H01L", "C23C"}),
    date_from="20050101",
    date_to="20251231",
    a_layer_apps=frozenset({"1020100000001"}),
    a_layer_families=frozenset({"FAM_A"}),
    rejected_status="거절",
    examination_rejected=frozenset({"거절결정(일반)", "거절결정(재심사)"}),
)


def rec(app: str, date: str, *, ipc: str = "H10B 69/00|H01L 21/00", status: str = "거절",
        stream: str = "H10B") -> KiprisRecord:
    return KiprisRecord(
        application_number=app, applicant_name="", application_date=date,
        invention_title="t", ipc_number=ipc, abstract="a", open_date="", register_date="",
        register_status=status, query_applicant="", query_ipc=stream,
    )


def biblio_xml(*, citations=(("KR1020190085654 A", "Y"),), claim1="1. 반도체 장치.",
               status="거절결정(일반)") -> str:
    arts = "".join(
        f"<priorArtDocumentsInfo><documentsNumber>{n}</documentsNumber>"
        f"<examinerQuotationFlag>{f}</examinerQuotationFlag></priorArtDocumentsInfo>"
        for n, f in citations
    )
    claims = f"<claimInfo><claim>{claim1}</claim></claimInfo>" if claim1 else ""
    return (
        "<response><body><item>"
        f"<biblioSummaryInfoArray><biblioSummaryInfo><finalDisposal>{status}</finalDisposal>"
        "</biblioSummaryInfo></biblioSummaryInfoArray>"
        f"<claimInfoArray>{claims}</claimInfoArray>"
        f"<priorArtDocumentsInfoArray>{arts}</priorArtDocumentsInfoArray>"
        "</item></body></response>"
    )


def pager(pages: dict[str, list[list[KiprisRecord]]]):
    """IPC → 페이지 목록. 범위를 넘으면 빈 목록(=스트림 종료)."""
    def fetch(ipc: str, page: int) -> list[KiprisRecord]:
        seq = pages.get(ipc, [])
        return seq[page - 1] if 1 <= page <= len(seq) else []
    return fetch


def chunk(records: list[KiprisRecord], size: int) -> list[list[KiprisRecord]]:
    return [records[i:i + size] for i in range(0, len(records), size)]


# --- T1 타이블록이 페이지 경계를 걸쳐도 순서가 같다 -----------------------

def test_t1_tie_block_across_page_boundary_is_page_size_invariant():
    # 같은 출원일 5건이 서버가 준 순서(역순)로 온다 — 클라이언트가 출원번호로 다시 세워야 한다.
    same_day = [rec(f"102005000000{i}", "20050310") for i in (5, 3, 1, 4, 2)]
    stream = [rec("1020050000000", "20050101"), *same_day, rec("1020050000009", "20050401")]

    orders = []
    for size in (500, 50, 7, 3, 2):
        out = list(iter_stream(pager({"H10B": chunk(stream, size)}), "H10B"))
        orders.append([r.application_number for r in out])

    assert all(o == orders[0] for o in orders), "페이지 크기에 따라 순서가 갈렸다 — 결정 A 위반"
    assert orders[0] == sorted(orders[0]), "타이블록이 출원번호 오름차순이 아니다"


def test_t1b_pending_block_is_flushed_when_stream_ends():
    # 마지막 타이 블록을 버리면 앞부분이 유실된다.
    stream = [rec("1020050000002", "20050310"), rec("1020050000001", "20050310")]
    out = list(iter_stream(pager({"H10B": chunk(stream, 1)}), "H10B"))
    assert [r.application_number for r in out] == ["1020050000001", "1020050000002"]


# --- T2 k-way 합병 = 전량 정렬 -------------------------------------------

def test_t2_merge_equals_global_sort():
    a = [rec("1020050000003", "20050101"), rec("1020050000007", "20060101")]
    b = [rec("1020050000001", "20050201"), rec("1020050000009", "20070101")]
    c = [rec("1020050000005", "20050102")]
    merged = [r for r, dup in merged_with_dups([iter(a), iter(b), iter(c)]) if not dup]
    assert [sort_key(r) for r in merged] == sorted(sort_key(r) for r in a + b + c)


# --- T3 dedup: 세 스트림에 같은 출원번호 ----------------------------------

def test_t3_same_application_in_three_streams_counts_once():
    shared = rec("1020050000001", "20050101")
    streams = [iter([shared]), iter([shared]), iter([shared])]
    flags = [dup for _r, dup in merged_with_dups(streams)]
    assert flags == [False, True, True]


# --- T4 사유 코드 12종 · 경계 --------------------------------------------

def test_t4_free_reason_codes():
    assert screen_free(rec("1", "20100101", ipc="G06F 1/00"), CTX).reason is Reason.IPC_NOT_FROZEN
    assert screen_free(rec("1", "20041231"), CTX).reason is Reason.DATE_OUT_OF_WINDOW
    assert screen_free(rec("1", "20260101"), CTX).reason is Reason.DATE_OUT_OF_WINDOW
    assert screen_free(rec("1", "20100101", status="소멸"), CTX).reason is Reason.STATUS_NOT_REJECTED
    assert screen_free(rec("1020100000001", "20100101"), CTX).reason \
        is Reason.DUP_APPLICATION_A_LAYER
    assert screen_free(rec("1", "20100101"), CTX, is_duplicate=True).reason is Reason.DUP_WITHIN_B


def test_t4b_window_boundaries_are_inclusive():
    for date in ("20050101", "20251231"):
        assert screen_free(rec("1", date), CTX).passed


def test_t4c_empty_status_defers_to_detail_not_exclusion():
    # 결측을 "거절 아님"으로 처리하면 §3 포함 1이 조용히 좁아진다(PLAN-032 §2.5(4)).
    v = screen_free(rec("1", "20100101", status=""), CTX)
    assert v.passed and v.needs_detail and v.reason is Reason.STATUS_EMPTY


def test_t4d_detail_reason_codes():
    def bib(**kw):
        return parse_biblio(biblio_xml(**kw), "1")

    assert screen_detail(bib(citations=()), CTX).reason is Reason.NO_EXAMINER_CITATION
    assert screen_detail(bib(citations=(("Journal of Semiconductors 2019", "Y"),)), CTX).reason \
        is Reason.NPL_ONLY_CITATION
    assert screen_detail(bib(claim1=""), CTX).reason is Reason.CLAIM1_MISSING
    assert screen_detail(bib(), CTX).reason is Reason.OK
    # 출원인 인용(플래그 N)만 있으면 포함 2 미달이다 — 심사관 인용만 센다.
    assert screen_detail(bib(citations=(("KR1020190085654 A", "N"),)), CTX).reason \
        is Reason.NO_EXAMINER_CITATION
    # status_empty 로 넘어온 건은 행정상태까지 확정돼야 채택된다.
    assert screen_detail(bib(status="취하"), CTX, needs_status=True).reason \
        is Reason.STATUS_UNCONFIRMED
    assert screen_detail(bib(status="거절결정(재심사)"), CTX, needs_status=True).reason is Reason.OK


def test_t4e_leading_ipc_and_npl_rule():
    assert leading_ipc("H10B 69/00|H01L 21/8247") == "H10B"
    assert is_patent_document("KR 10-2019-0085654 A")
    assert is_patent_document("US20190348292 A1")
    assert not is_patent_document("Nature Electronics, vol.3, 2020")


# --- T5 판정 불능은 배제 -------------------------------------------------

def test_t5_family_undecidable_is_excluded():
    assert screen_family(None, CTX).reason is Reason.FAMILY_UNDECIDABLE
    assert not screen_family(None, CTX).passed
    assert screen_family("FAM_A", CTX).reason is Reason.FAMILY_OVERLAP_A_LAYER
    assert screen_family("FAM_NEW", CTX).passed


def test_t5b_map_lookup_matches_resolve_semantics(tmp_path, monkeypatch):
    """지도 조회는 `resolve_families` 와 **같은 규약**이어야 한다 — 미조인은 `None`.

    BigQuery 는 호출하지 않는다. 캐시 parquet 가 있으면 무조회로 재생되는 것도 함께 잰다
    (조회 1회 원칙 · 파일럿 도중 지도가 바뀌면 배제 1의 판정이 흔들린다).
    """
    import pandas as pd

    from sdkb_paper.collect.b_layer import family as family_mod

    cache = tmp_path / "kr_family_map.parquet"
    pd.DataFrame({"bq_app": ["20050000001"], "family_id": ["FAM_1"]}).to_parquet(cache)

    def _no_bq(*_a, **_k):
        raise AssertionError("캐시가 있는데 BigQuery 를 호출했다")

    monkeypatch.setattr("sdkb_paper.collect.bq_family_ir._client", _no_bq)
    kr_map = family_mod.load_kr_family_map(cache)

    assert family_mod.resolve_from_map("1020050000001", kr_map) == "FAM_1"
    assert family_mod.resolve_from_map("1020050000002", kr_map) is None   # 미조인 = 판정 불능
    assert family_mod.resolve_from_map("US20190348292", kr_map) is None   # 비-KR 형식


# --- 드라이버 픽스처 ------------------------------------------------------

@pytest.fixture
def scenario():
    """채택 2 · 각 사유 최소 1건이 나오는 최소 시나리오."""
    records = [
        rec("1020050000001", "20050101"),                        # 채택
        rec("1020050000002", "20050102", status="소멸"),          # status_not_rejected → 감사 표본
        rec("1020050000003", "20050103", ipc="G06F 1/00"),       # ipc_not_frozen
        rec("1020100000001", "20050104"),                        # dup_application_a_layer
        rec("1020050000005", "20050105"),                        # family_overlap
        rec("1020050000006", "20050106"),                        # family_undecidable
        rec("1020050000007", "20050107"),                        # no_examiner_citation
        rec("1020050000008", "20050108"),                        # 채택
    ]
    families = {
        "1020050000001": "FAM_1", "1020050000005": "FAM_A", "1020050000006": None,
        "1020050000007": "FAM_7", "1020050000008": "FAM_8",
    }
    details = {
        "1020050000001": biblio_xml(),
        "1020050000002": biblio_xml(status="소멸"),
        "1020050000007": biblio_xml(citations=()),
        "1020050000008": biblio_xml(citations=(("US20190348292 A1", "Y"),)),
    }
    calls = {"detail": 0}

    def fetch_detail(app: str) -> str:
        calls["detail"] += 1
        return details[app]

    return records, families, fetch_detail, calls


def run_scenario(tmp_path, scenario, *, name="ledger.jsonl", max_detail=500, records=None):
    recs, families, fetch_detail, calls = scenario
    recs = records if records is not None else recs
    budget = drv.Budget(max_search=10, max_detail=max_detail, max_audit=50)
    report, accepted = drv.run(
        fetch_page=pager({"H10B": chunk(recs, 3)}),
        fetch_detail=fetch_detail,
        resolve_family=lambda app: families.get(app),
        ctx=CTX, budget=budget, ledger_path=tmp_path / name, target=200,
    )
    return report, accepted, budget, calls


# --- T6 A층 교집합 0 ------------------------------------------------------

def test_t6_no_intersection_with_a_layer(tmp_path, scenario):
    _report, accepted, _b, _c = run_scenario(tmp_path, scenario)
    apps = {a["application_number"] for a in accepted}
    fams = {a["family_id"] for a in accepted}
    assert apps & CTX.a_layer_apps == set(), "A층 출원번호가 B층에 섞였다"
    assert fams & CTX.a_layer_families == set(), "A층 패밀리가 B층에 섞였다"
    assert apps == {"1020050000001", "1020050000008"}


# --- T7 결정성 -----------------------------------------------------------

def test_t7_determinism_ledger_identical_except_timestamp(tmp_path, scenario):
    run_scenario(tmp_path, scenario, name="a.jsonl")
    run_scenario(tmp_path, scenario, name="b.jsonl")
    a = ledger_mod.comparable(ledger_mod.load(tmp_path / "a.jsonl"))
    b = ledger_mod.comparable(ledger_mod.load(tmp_path / "b.jsonl"))
    assert a == b


# --- T8 재개 -------------------------------------------------------------

def test_t8_resume_reaches_same_final_ledger(tmp_path, scenario):
    run_scenario(tmp_path, scenario, name="full.jsonl")
    full = ledger_mod.comparable(ledger_mod.load(tmp_path / "full.jsonl"))

    # 앞 3행만 남기고 중단된 상태를 만든 뒤 재실행한다.
    partial = (tmp_path / "part.jsonl")
    partial.write_text(
        "\n".join((tmp_path / "full.jsonl").read_text(encoding="utf-8").splitlines()[:3]) + "\n",
        encoding="utf-8")
    run_scenario(tmp_path, scenario, name="part.jsonl")
    assert ledger_mod.comparable(ledger_mod.load(partial)) == full


def test_t8b_truncated_last_line_is_dropped(tmp_path):
    path = tmp_path / "t.jsonl"
    path.write_text('{"seq": 1, "application_number": "1", "application_date": "20050101",'
                    '"ipc_leading": "H10B", "ipc_all": "H10B", "register_status": "거절",'
                    '"stream_ipc": "H10B", "page_no": 1, "cache_key": "", "stage": "free",'
                    '"verdict": "rejected", "reason": "ipc_not_frozen", "detail_call_used": false}\n'
                    '{"seq": 2, "applicat', encoding="utf-8")
    assert len(ledger_mod.load(path)) == 1


# --- T9 예산 회계 ---------------------------------------------------------

def test_t9_detail_calls_match_ledger_and_cap_stops(tmp_path, scenario):
    _report, _accepted, budget, calls = run_scenario(tmp_path, scenario)
    rows = ledger_mod.load(tmp_path / "ledger.jsonl")
    assert budget.detail == sum(1 for r in rows if r.detail_call_used)
    # 감사 콜은 detail 계정에 들지 않는다 — r 의 분모에서 제외되기 때문이다(결정 E).
    assert calls["detail"] == budget.detail + budget.audit
    assert budget.audit == sum(1 for r in rows if r.stage == "audit")


def test_t9b_detail_cap_stops_run(tmp_path, scenario):
    report, _accepted, budget, _calls = run_scenario(tmp_path, scenario, max_detail=1)
    assert budget.detail == 1
    assert report.stopped_by == "budget_detail"


def test_t9c_search_cap_ends_streams_without_losing_pending(tmp_path, scenario):
    # 단일 스트림으로 좁혀 캡을 정확히 1페이지에 건다(여러 스트림이면 앞 스트림이 캡을 먹는다).
    ctx = dataclasses.replace(CTX, frozen_ipc=frozenset({"H10B"}))
    recs, families, fetch_detail, _calls = scenario
    budget = drv.Budget(max_search=1, max_detail=500, max_audit=50)
    report, _accepted = drv.run(
        fetch_page=pager({"H10B": chunk(recs, 3)}), fetch_detail=fetch_detail,
        resolve_family=lambda app: families.get(app), ctx=ctx, budget=budget,
        ledger_path=tmp_path / "s.jsonl", target=200)
    rows = ledger_mod.load(tmp_path / "s.jsonl")
    assert budget.search == 1
    assert report.stopped_by == "budget_search"
    # 1페이지 3건이 전부 판정됐다 — 보류 블록을 버렸다면 마지막 건이 사라진다.
    assert {r.application_number for r in rows if r.stage != "audit"} == {
        "1020050000001", "1020050000002", "1020050000003"}


# --- T10 봉인 -------------------------------------------------------------

def test_t10_ledger_never_carries_citation_identifiers(tmp_path, scenario):
    run_scenario(tmp_path, scenario)
    raw = (tmp_path / "ledger.jsonl").read_text(encoding="utf-8")
    for line in raw.splitlines():
        row = json.loads(line)
        assert not (set(row) & ledger_mod.FORBIDDEN_FIELDS)
        # 값 패턴 검사: 어떤 열에도 특허 공개번호 꼴 문자열이 없어야 한다.
        for key, value in row.items():
            if key in ("application_number", "cache_key"):
                continue
            assert not is_patent_document(str(value)), f"{key} 에 인용 식별자로 보이는 값"


def test_t10b_sealed_guard_rejects_citation_field():
    # 미래에 누구든 인용 식별자를 원장에 담으면 파일이 만들어지기 전에 실패해야 한다.
    with pytest.raises(ValueError, match="봉인 위반"):
        ledger_mod.assert_sealed({"seq": 1, "examiner_citations": ["KR1020190085654 A"]})
    assert ledger_mod.assert_sealed({"seq": 1, "examiner_citation_count": 3})


# --- T11 게이트 우회 불가 -------------------------------------------------

def test_t11_detail_is_never_called_before_free_and_family_pass(tmp_path, scenario):
    recs, families, _fetch, _calls = scenario
    seen_order: list[str] = []

    def tracing_detail(app: str) -> str:
        seen_order.append(app)
        return biblio_xml()

    budget = drv.Budget(max_search=10, max_detail=500, max_audit=0)   # 감사 끄고 본류만 본다
    drv.run(fetch_page=pager({"H10B": chunk(recs, 3)}), fetch_detail=tracing_detail,
            resolve_family=lambda app: families.get(app), ctx=CTX, budget=budget,
            ledger_path=tmp_path / "g.jsonl", target=200)

    # free·family 에서 걸러진 건은 서지상세를 **한 번도** 보지 않았어야 한다.
    blocked = {"1020050000002", "1020050000003", "1020100000001",
               "1020050000005", "1020050000006"}
    assert blocked & set(seen_order) == set(), "게이트를 우회해 서지상세를 호출했다"


# --- 보고 (r 추정) --------------------------------------------------------

def test_rates_exclude_audit_rows_from_denominator(tmp_path, scenario):
    run_scenario(tmp_path, scenario)
    rows = ledger_mod.load(tmp_path / "ledger.jsonl")
    rates = estimate_rates(rows)
    detail_calls = sum(1 for r in rows if r.detail_call_used)
    assert rates["r"].denominator == detail_calls
    assert rates["r"].numerator == sum(1 for r in rows if r.verdict == "accepted")


def test_wilson_lower_bound_never_negative():
    est = wilson(3, 100)
    assert est.lo > 0 and est.lo < est.point < est.hi
    assert wilson(0, 0).hi == 1.0


# --- 프로파일 (§4 데이터 프로파일 의무) -----------------------------------

def test_profile_is_deterministic_and_never_opens_sealed_qrel(tmp_path, scenario):
    _report, accepted, budget, _calls = run_scenario(tmp_path, scenario)
    rows = ledger_mod.load(tmp_path / "ledger.jsonl")
    args = dict(a_layer_years=["2005", "2006", "2006"], budget=dataclasses.asdict(budget))
    first = report_mod.write_profile(rows, accepted, tmp_path / "p1.md", **args).read_text("utf-8")
    second = report_mod.write_profile(rows, accepted, tmp_path / "p2.md", **args).read_text("utf-8")
    assert first == second, "프로파일이 재실행마다 달라진다 — 사전 순서가 비결정적이다"
    # 인용 식별자가 프로파일에 새어나오면 봉인이 깨진다.
    for token in ("KR1020190085654", "US20190348292"):
        assert token not in first
    assert "출원연도 | B층 | A층" in first        # A층 값이 있으면 대조 열이 붙는다


def test_profile_states_missing_a_layer_ipc_instead_of_zero(tmp_path, scenario):
    _report, accepted, _b, _c = run_scenario(tmp_path, scenario)
    text = report_mod.write_profile(
        ledger_mod.load(tmp_path / "ledger.jsonl"), accepted, tmp_path / "p.md",
        a_layer_ipc=None).read_text("utf-8")
    # 없는 값을 0으로 적으면 "A층에 없다"는 거짓 보고가 된다.
    assert "주분류 IPC | B층 |" in text
    assert "CLAUDE §0.1" in text
