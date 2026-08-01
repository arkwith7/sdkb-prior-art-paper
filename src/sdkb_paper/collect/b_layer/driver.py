"""B층 수집 드라이버 — 오케스트레이션·예산·정지 (PLAN-032 §5.1·§5.5).

**게이트를 우회하는 경로를 만들지 않는다.** 서지상세 호출은 `run()` 안의 단 한 곳에서만
일어나고, 그 앞에 free·family 판정이 반드시 선다(테스트 T11 이 호출 그래프를 검사한다).

**정지:** detail 500 소진 · 채택 200 도달 · search 300 소진 — 셋 중 먼저.
`quota_hit` 은 발생 즉시 기록하고 중단한다 — **KIPRIS 의 할당초과 `resultCode` 실물은 아직
관측된 적이 없으므로**(§2.1 은 quota 미발생 로그였다) 메시지에 QUOTA/LIMIT 이 든 경우로
보수적으로 판정하고, 실제 코드를 처음 만나면 그 값을 기록해 이 규칙을 좁힌다.

**봉인:** 채택 건의 심사관 인용은 `B_QREL_SEALED` 로 직행하고 원장·보고서에는 건수만 남는다.
파일럿 단계에서 이 파일을 읽는 코드는 없다(PLAN-032 §1 성공기준 ⑤).
"""
from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from sdkb_paper.collect.b_layer import family as family_mod
from sdkb_paper.collect.b_layer import ledger as ledger_mod
from sdkb_paper.collect.b_layer import report as report_mod
from sdkb_paper.collect.b_layer.biblio import Biblio, parse_biblio
from sdkb_paper.collect.b_layer.screen import (
    Reason,
    ScreenContext,
    audit_verdict,
    leading_ipc,
    screen_detail,
    screen_family,
    screen_free,
)
from sdkb_paper.collect.b_layer.stream import iter_stream, merged_with_dups
from sdkb_paper.collect.kipris_client import KiprisRecord
from sdkb_paper.config import (
    B_ACCEPTED,
    B_BUDGET_REPORT,
    B_LAYER_CACHE,
    B_LAYER_DATE_FROM,
    B_LAYER_DATE_TO,
    B_LAYER_EXAMINATION_REJECTED,
    B_LAYER_IPC,
    B_LAYER_MAX_AUDIT,
    B_LAYER_MAX_DETAIL,
    B_LAYER_MAX_SEARCH,
    B_LAYER_REJECTED_STATUS,
    B_LAYER_TARGET,
    B_LAYER_PROFILE,
    B_LEDGER,
    B_QREL_SEALED,
    IR_SPLIT,
)


class BudgetExhausted(Exception):
    """캡 도달. 예외로 올려 **부분 결과를 저장한 채** 정지한다."""


@dataclass
class Budget:
    """4계정 분리 (§1 호출 회계 동결 · 섞으면 r 의 분모가 오염된다)."""

    max_search: int
    max_detail: int
    max_audit: int
    search: int = 0
    detail: int = 0
    audit: int = 0
    quota_hit: bool = False

    def spend(self, account: str) -> None:
        used, cap = getattr(self, account), getattr(self, f"max_{account}")
        if used >= cap:
            raise BudgetExhausted(account)
        setattr(self, account, used + 1)


@dataclass
class RunReport:
    accepted: int = 0
    stopped_by: str = ""
    budget: dict = field(default_factory=dict)
    rates: dict = field(default_factory=dict)
    reasons: dict = field(default_factory=dict)
    audit_false_negative: str = ""
    projected: dict = field(default_factory=dict)


def build_context() -> ScreenContext:
    apps, families = family_mod.load_a_layer_exclusions()
    return ScreenContext(
        frozen_ipc=B_LAYER_IPC,
        date_from=B_LAYER_DATE_FROM,
        date_to=B_LAYER_DATE_TO,
        a_layer_apps=apps,
        a_layer_families=families,
        rejected_status=B_LAYER_REJECTED_STATUS,
        examination_rejected=B_LAYER_EXAMINATION_REJECTED,
    )


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _row(
    rec: KiprisRecord,
    *,
    seq: int,
    stage: str,
    verdict: str,
    reason: Reason | str,
    detail_call_used: bool = False,
    family_id: str = "",
    family_method: str = "",
    bib: Biblio | None = None,
    page_no: int = 0,
    cache_key: str = "",
) -> ledger_mod.LedgerRow:
    return ledger_mod.LedgerRow(
        seq=seq,
        application_number=rec.application_number,
        application_date=rec.application_date,
        ipc_leading=leading_ipc(rec.ipc_number),
        ipc_all=rec.ipc_number,
        register_status=rec.register_status,
        stream_ipc=rec.query_ipc,
        page_no=page_no,
        cache_key=cache_key,
        stage=stage,
        verdict=verdict,
        reason=reason.value if isinstance(reason, Reason) else reason,
        detail_call_used=detail_call_used,
        family_id=family_id,
        family_method=family_method,
        # 인용 **건수**만 남긴다 — 식별자는 봉인 파일로 직행한다.
        examiner_citation_count=len(bib.examiner_citations) if bib else 0,
        npl_only=bool(bib and bib.npl_only),
        has_claim1=bool(bib and bib.claim1.strip()),
        fetched_at=_now(),
    )


def run(
    *,
    fetch_page: Callable[[str, int], list[KiprisRecord]],
    fetch_detail: Callable[[str], str],
    resolve_family: Callable[[str], str | None],
    ctx: ScreenContext,
    budget: Budget,
    ledger_path: Path = B_LEDGER,
    target: int = B_LAYER_TARGET,
    page_of: dict[str, int] | None = None,
    detail_key: Callable[[str], str] | None = None,
) -> tuple[RunReport, list[dict]]:
    """수집 본체. 의존은 전부 주입받는다 — 테스트가 API 없이 전 경로를 돈다.

    `page_of`·`detail_key` 는 재현 좌표(어느 페이지에서 왔는가 · 어느 캐시 키인가)를 원장에
    남기기 위한 것이고 판정에는 관여하지 않는다.

    반환: (보고서, 채택 레코드) — 채택 레코드는 호출자가 `B_ACCEPTED`/`B_QREL_SEALED` 로 가른다.
    """
    page_of = page_of if page_of is not None else {}
    detail_key = detail_key or (lambda _app: "")
    resumed = ledger_mod.load(ledger_path)
    state = ledger_mod.replay_state(resumed)
    budget.detail = state.detail_calls
    budget.audit = state.audit_calls

    accepted_records: list[dict] = []
    # 감사 대기(무료 배제분 · 순번 앞에서부터). **재개 시 원장에서 복원한다** — 복원하지 않으면
    # 이미 판정된 건은 `seen` 이라 다시 큐에 들지 않아 감사가 조용히 누락된다.
    audited: list[tuple[int, KiprisRecord]] = _pending_audits(resumed)
    stopped_by = ""
    search_exhausted = False

    def budgeted_page(ipc: str, page: int) -> list[KiprisRecord]:
        """검색 예산은 **드라이버가** 집행한다 — CLI 배선에 맡기면 회계가 검증되지 않는다(T9)."""
        nonlocal search_exhausted
        try:
            budget.spend("search")
        except BudgetExhausted:
            search_exhausted = True
            return []          # 스트림을 정상 종료시킨다(보류 블록은 방출된다)
        return fetch_page(ipc, page)

    streams = [iter_stream(budgeted_page, ipc) for ipc in sorted(ctx.frozen_ipc)]
    try:
        for rec, dup in merged_with_dups(streams):
            if state.accepted >= target:
                stopped_by = "target_reached"
                break
            if rec.application_number in state.seen_applications:
                continue          # 재개: 이미 판정된 건은 다시 콜을 쓰지 않는다
            seq = 0 if dup else state.last_seq + 1
            if not dup:
                state.last_seq = seq
            state.seen_applications.add(rec.application_number)

            page_no = page_of.get(rec.application_number, 0)
            free = screen_free(rec, ctx, is_duplicate=dup)
            if not free.passed:
                ledger_mod.append(ledger_path, _row(
                    rec, seq=seq, stage="free", verdict="rejected", reason=free.reason,
                    page_no=page_no))
                if free.reason is Reason.STATUS_NOT_REJECTED:
                    audited.append((seq, rec))     # 감사 표본(결정 E) — 순번 앞에서부터
                continue

            fam = resolve_family(rec.application_number)
            fam_verdict = screen_family(fam, ctx)
            if not fam_verdict.passed:
                ledger_mod.append(ledger_path, _row(
                    rec, seq=seq, stage="family", verdict="rejected", reason=fam_verdict.reason,
                    page_no=page_no, family_id=fam or "",
                    family_method="unresolved" if fam is None else "docdb-app"))
                continue

            budget.spend("detail")
            bib = parse_biblio(fetch_detail(rec.application_number), rec.application_number)
            det = screen_detail(bib, ctx, needs_status=free.reason is Reason.STATUS_EMPTY)
            ledger_mod.append(ledger_path, _row(
                rec, seq=seq, stage="detail",
                verdict="accepted" if det.passed else "rejected", reason=det.reason,
                detail_call_used=True, page_no=page_no, cache_key=detail_key(rec.application_number),
                family_id=fam or "", family_method="docdb-app", bib=bib))
            if det.passed:
                state.accepted += 1
                accepted_records.append({
                    "seq": seq,
                    "application_number": rec.application_number,
                    "application_date": rec.application_date,
                    "ipc_leading": leading_ipc(rec.ipc_number),
                    "register_status": rec.register_status,
                    "claim1": bib.claim1,
                    "abstract": rec.abstract,
                    "invention_title": rec.invention_title,
                    "family_id": fam or "",
                    "examiner_citations": list(bib.examiner_citations),   # → 봉인 파일로만
                })
        else:
            stopped_by = stopped_by or ("budget_search" if search_exhausted
                                        else "streams_exhausted")
    except BudgetExhausted as e:
        stopped_by = f"budget_{e.args[0]}"
    except _QuotaHit:
        budget.quota_hit = True
        stopped_by = "quota_hit"

    stopped_by = _run_audit(
        audited, fetch_detail, detail_key, ctx, budget, ledger_path, stopped_by)

    rows = ledger_mod.load(ledger_path)
    rates = report_mod.estimate_rates(rows)
    report = RunReport(
        accepted=state.accepted,
        stopped_by=stopped_by,
        budget=asdict(budget),
        rates={k: str(v) for k, v in rates.items()},
        reasons=report_mod.reason_counts(rows),
        audit_false_negative=str(report_mod.audit_false_negative_rate(rows)),
        projected=report_mod.projected_budget(rates, target),
    )
    return report, accepted_records


class _QuotaHit(Exception):
    """KIPRIS 일일 할당 소진. 예산 캡과 구분해 기록한다(§2.1 관측 승격)."""


_QUOTA_HINTS = ("QUOTA", "LIMIT", "EXCEED")


def raise_if_quota(exc: Exception) -> None:
    """클라이언트 예외가 할당초과로 보이면 `_QuotaHit` 로 승격한다.

    보수적이다 — 판정이 애매하면 그대로 올려 실패시킨다. 조용히 계속하면 원장이
    "후보가 없었다"로 읽혀 r 이 왜곡된다.
    """
    if any(h in str(exc).upper() for h in _QUOTA_HINTS):
        raise _QuotaHit(str(exc)) from exc


def _pending_audits(rows: list[ledger_mod.LedgerRow]) -> list[tuple[int, KiprisRecord]]:
    """재개 시 원장에서 감사 대기열을 복원한다.

    `status_not_rejected` 로 무료 배제됐고 아직 감사 행이 없는 건이 대상이다. 원장은 판정에
    필요한 필드를 전부 갖고 있으므로 최소 레코드를 되세워 쓴다 — 검색을 다시 돌리지 않는다.
    """
    done = {r.application_number for r in rows if r.stage == "audit"}
    return [
        (r.seq, KiprisRecord(
            application_number=r.application_number, applicant_name="",
            application_date=r.application_date, invention_title="", ipc_number=r.ipc_all,
            abstract="", open_date="", register_date="", register_status=r.register_status,
            query_applicant="", query_ipc=r.stream_ipc))
        for r in rows
        if r.stage == "free" and r.reason == Reason.STATUS_NOT_REJECTED.value
        and r.application_number not in done
    ]


def _run_audit(
    audited: list[tuple[int, KiprisRecord]],
    fetch_detail: Callable[[str], str],
    detail_key: Callable[[str], str],
    ctx: ScreenContext,
    budget: Budget,
    ledger_path: Path,
    stopped_by: str,
) -> str:
    """결정 E — `status_not_rejected` 배제분 앞에서부터 50건의 위음성 감사.

    **`r` 의 분모에 들지 않는다**(별도 계정 `audit`). 결과가 어떻든 채택 집합은 재산출하지 않는다.
    """
    for seq, rec in sorted(audited, key=lambda pair: pair[0])[:budget.max_audit]:
        try:
            budget.spend("audit")
        except BudgetExhausted:
            break
        bib = parse_biblio(fetch_detail(rec.application_number), rec.application_number)
        false_negative = audit_verdict(bib, ctx)
        ledger_mod.append(ledger_path, _row(
            rec, seq=seq, stage="audit",
            verdict=report_mod.AUDIT_FALSE_NEGATIVE if false_negative
            else report_mod.AUDIT_CONFIRMED,
            reason=Reason.STATUS_NOT_REJECTED, detail_call_used=False,
            cache_key=detail_key(rec.application_number), bib=bib))
    return stopped_by


def main() -> int:
    ap = argparse.ArgumentParser(description="B층 파일럿 수집 (PLAN-032)")
    ap.add_argument("--target", type=int, default=B_LAYER_TARGET)
    ap.add_argument("--max-detail", type=int, default=B_LAYER_MAX_DETAIL)
    ap.add_argument("--max-search", type=int, default=B_LAYER_MAX_SEARCH)
    ap.add_argument("--max-audit", type=int, default=B_LAYER_MAX_AUDIT)
    ap.add_argument("--dry-run", action="store_true",
                    help="BigQuery 스캔량만 추정하고 종료 (KIPRIS 호출 0)")
    args = ap.parse_args()

    import pandas as pd

    from sdkb_paper.collect.kipris_client import KiprisClient

    ctx = build_context()
    if args.dry_run:
        family_mod.load_kr_family_map(dry_run=True)
        print(f"A층 배제: 출원번호 {len(ctx.a_layer_apps):,} · 패밀리 {len(ctx.a_layer_families):,}")
        return 0

    client = KiprisClient(cache_db=B_LAYER_CACHE)
    budget = Budget(max_search=args.max_search, max_detail=args.max_detail,
                    max_audit=args.max_audit)
    # 패밀리 지도는 **수집 시작 전 1회** 적재한다 — 후보별 조회는 파라미터와 무관한 5.22 GB 를
    # 매번 다시 스캔하고(dry-run 실측), 조회 횟수에 예산 계정이 없어 상한이 없다.
    kr_map = family_mod.load_kr_family_map()
    print(f"KR 패밀리 지도 {len(kr_map):,}건 적재")

    page_of: dict[str, int] = {}

    def fetch_page(ipc: str, page: int) -> list[KiprisRecord]:
        # 검색 예산은 `run()` 이 집행한다 — 여기서 또 세면 이중 계상이 된다.
        try:
            _total, items = client.search_ipc(ipc, B_LAYER_DATE_FROM, B_LAYER_DATE_TO, page=page)
        except RuntimeError as e:
            raise_if_quota(e)
            raise
        for item in items:
            page_of.setdefault(item.application_number, page)
        return items

    def fetch_detail(app: str) -> str:
        try:
            return client.detail_raw(app)
        except RuntimeError as e:
            raise_if_quota(e)
            raise

    def resolve_family(app: str) -> str | None:
        return family_mod.resolve_from_map(app, kr_map)

    report, accepted = run(
        fetch_page=fetch_page, fetch_detail=fetch_detail, resolve_family=resolve_family,
        ctx=ctx, budget=budget, target=args.target, page_of=page_of,
        detail_key=lambda app: KiprisClient.cache_key({"applicationNumber": app})[1],
    )

    if accepted:
        df = pd.DataFrame(accepted)
        # 봉인: 인용 식별자는 별도 파일로만 나간다. 채택 파일에서는 열 자체를 지운다.
        qrel = df[["application_number", "examiner_citations"]].explode("examiner_citations")
        B_QREL_SEALED.parent.mkdir(parents=True, exist_ok=True)
        qrel.to_parquet(B_QREL_SEALED, index=False)
        B_ACCEPTED.parent.mkdir(parents=True, exist_ok=True)
        df.drop(columns=["examiner_citations"]).to_parquet(B_ACCEPTED, index=False)

    # §4 데이터 프로파일 — A층 대조는 `split.parquet` + 원장에서 만든다(봉인 파일은 열지 않는다).
    split = pd.read_parquet(IR_SPLIT, columns=["filing_date"])
    report_mod.write_profile(
        ledger_mod.load(B_LEDGER), accepted, B_LAYER_PROFILE,
        a_layer_years=[str(d)[:4] for d in split["filing_date"]],
        a_layer_ipc=None, budget=asdict(budget),   # A층 주분류는 상류 원본에만 있다(§0.1)
    )

    B_BUDGET_REPORT.parent.mkdir(parents=True, exist_ok=True)
    B_BUDGET_REPORT.write_text(
        json.dumps(asdict(report), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(asdict(report), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
