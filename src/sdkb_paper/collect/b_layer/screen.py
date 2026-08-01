"""포함·배제 판정 — **순수 함수. I/O 없음.** (PLAN-031 §3 · PLAN-032 §5.4)

`reason` 코드는 **동결**이다. 사후에 코드를 늘려 분모를 재정의하는 것이 CLAUDE §1-2 가 금하는
바로 그것이다. 새 코드가 필요하면 코드가 아니라 사전등록을 먼저 고친다.

세 단계는 비용 오름차순이며 **순서가 규칙의 일부**다(PLAN-032 §5.1):
  free   검색 응답만으로 — 포함 1·4·5 · 배제 2 (KIPRIS 콜 0)
  family BigQuery DOCDB — 배제 1 (KIPRIS 콜 0)
  detail 서지상세 1콜 — 포함 2·3 · 배제 3·4 · `status_empty` 확정
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from sdkb_paper.collect.b_layer.biblio import Biblio
from sdkb_paper.collect.kipris_client import KiprisRecord


class Reason(str, Enum):
    """동결 사유 코드 12종 (PLAN-032 §5.4). 값은 원장에 그대로 기록된다."""

    # free
    IPC_NOT_FROZEN = "ipc_not_frozen"
    DATE_OUT_OF_WINDOW = "date_out_of_window"
    STATUS_NOT_REJECTED = "status_not_rejected"
    STATUS_EMPTY = "status_empty"                  # 배제가 아니라 **detail 로 이월**
    DUP_APPLICATION_A_LAYER = "dup_application_a_layer"
    DUP_WITHIN_B = "dup_within_b"
    # family
    FAMILY_OVERLAP_A_LAYER = "family_overlap_a_layer"
    FAMILY_UNDECIDABLE = "family_undecidable"
    # detail
    NO_EXAMINER_CITATION = "no_examiner_citation"
    NPL_ONLY_CITATION = "npl_only_citation"
    CLAIM1_MISSING = "claim1_missing"
    STATUS_UNCONFIRMED = "status_unconfirmed"
    # 채택
    OK = "ok"


@dataclass(frozen=True)
class ScreenContext:
    """드라이버가 1회 구축하는 불변 판정 맥락. 전부 `config` 의 동결값에서 온다."""

    frozen_ipc: frozenset[str]
    date_from: str
    date_to: str
    a_layer_apps: frozenset[str]
    a_layer_families: frozenset[str]
    rejected_status: str
    examination_rejected: frozenset[str]


@dataclass(frozen=True)
class Verdict:
    reason: Reason
    passed: bool          # 다음 단계로 진행하는가 (detail 단계에서는 = 채택)
    needs_detail: bool = False   # free 단계에서만: 행정상태를 서지상세로 확정해야 하는가


def leading_ipc(ipc_number: str) -> str:
    """주분류 = 응답 `ipcNumber` 의 **선두** 코드의 섹션+클래스+서브클래스 4자.

    예: `H10B 69/00|H01L 21/8247` → `H10B` (PLAN-032 §2.5(3) 실측 형식).
    """
    head = ipc_number.split("|", 1)[0].strip()
    return head.replace(" ", "")[:4].upper()


def screen_free(rec: KiprisRecord, ctx: ScreenContext, *, is_duplicate: bool = False) -> Verdict:
    """검색 응답만으로 내리는 판정. **순서가 곧 사유의 우선순위**이며 결정적이다."""
    if is_duplicate:
        return Verdict(Reason.DUP_WITHIN_B, False)
    if leading_ipc(rec.ipc_number) not in ctx.frozen_ipc:
        return Verdict(Reason.IPC_NOT_FROZEN, False)
    if not (ctx.date_from <= rec.application_date <= ctx.date_to):
        return Verdict(Reason.DATE_OUT_OF_WINDOW, False)
    if rec.application_number in ctx.a_layer_apps:
        return Verdict(Reason.DUP_APPLICATION_A_LAYER, False)
    status = rec.register_status.strip()
    if not status:
        # 결측을 "거절 아님"으로 처리하지 않는다(PLAN-032 §2.5(4)) — detail 로 확정한다.
        return Verdict(Reason.STATUS_EMPTY, True, needs_detail=True)
    if status != ctx.rejected_status:
        return Verdict(Reason.STATUS_NOT_REJECTED, False)
    return Verdict(Reason.OK, True)


def screen_family(family_id: str | None, ctx: ScreenContext) -> Verdict:
    """배제 1. `family_id is None` = DOCDB 미조인 = **판정 불능 → 보수적 배제**(§8 항목 8).

    r 이 소폭 낮아지는 대가로 A/B 패밀리 누출 위험을 0으로 만든다. **r 을 본 뒤 되돌리지 않는다.**
    """
    if family_id is None:
        return Verdict(Reason.FAMILY_UNDECIDABLE, False)
    if family_id in ctx.a_layer_families:
        return Verdict(Reason.FAMILY_OVERLAP_A_LAYER, False)
    return Verdict(Reason.OK, True)


def screen_detail(bib: Biblio, ctx: ScreenContext, *, needs_status: bool = False) -> Verdict:
    """서지상세 1콜로 내리는 최종 판정. `passed=True` 가 곧 **채택**이다."""
    if needs_status and bib.examination_status not in ctx.examination_rejected:
        return Verdict(Reason.STATUS_UNCONFIRMED, False)
    if not bib.examiner_citations:
        return Verdict(Reason.NO_EXAMINER_CITATION, False)
    if bib.npl_only:
        return Verdict(Reason.NPL_ONLY_CITATION, False)
    if not bib.claim1.strip():
        return Verdict(Reason.CLAIM1_MISSING, False)
    return Verdict(Reason.OK, True)


def audit_verdict(bib: Biblio, ctx: ScreenContext) -> bool:
    """감사(결정 E): 무료 배제된 건이 실제로는 §3 포함 1을 만족하는가 = **위음성인가**.

    감사 결과가 어떻든 **파일럿 중 판정 규칙을 바꾸지 않는다** — 측정하고 보고할 뿐이다
    (PLAN-032 §6.1). 규칙 변경이 필요하면 별도 승인을 받는다.
    """
    return bib.examination_status in ctx.examination_rejected
