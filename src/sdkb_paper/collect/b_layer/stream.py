"""검색 스트림의 결정적 순서 — 결정 A(타이블록)와 결정 C(k-way 합병).

**문제.** 서버 정렬은 `sortSpec=AD` 단일 필드라 **동일 출원일 내부 순서가 서버 정의**다
(PLAN-032 §2.5(1) 실측). §3의 표집 순서는 `(출원일, 출원번호)` 오름차순이므로 2차키를
클라이언트가 걸어야 한다. 그런데 타이 블록이 페이지 경계를 걸치면 **블록 전체를 확보하기 전에는
순서를 확정할 수 없다.**

**결정 A — 보류 후 정렬.** 페이지를 읽으며 마지막 출원일과 같은 날짜의 레코드를 버퍼에 보류하고,
다음 페이지에서 날짜가 진행되거나 스트림이 소진된 뒤에야 그 블록을 출원번호 오름차순으로
정렬해 방출한다. 그래서 방출 순서가 **페이지 크기·경계 위치와 무관**해진다(테스트 T1이 강제).

**결정 C — k-way 합병.** 21 IPC 스트림을 `(출원일, 출원번호)` 힙으로 합병해 전역 순서를 만들고,
같은 출원번호가 여러 스트림에 나타나면 **최초 1회만** 진행시킨다(나머지는 `dup_within_b`).
IPC 순회(스트림을 하나씩 소진)는 전역 순서를 깨므로 §3 위반이다 — 택하지 않았다.
"""
from __future__ import annotations

import heapq
from collections.abc import Callable, Iterable, Iterator

from sdkb_paper.collect.kipris_client import KiprisRecord

# 페이지 공급자: (ipc, page) -> 레코드 목록. 빈 목록이면 스트림 종료.
PageFetcher = Callable[[str, int], list[KiprisRecord]]


def sort_key(rec: KiprisRecord) -> tuple[str, str]:
    """§3 표집 순서의 정본 키. 둘 다 고정폭 숫자 문자열이라 사전순 = 수치순이다."""
    return (rec.application_date, rec.application_number)


def iter_stream(fetch: PageFetcher, ipc: str, *, start_page: int = 1) -> Iterator[KiprisRecord]:
    """단일 IPC 스트림을 `(출원일, 출원번호)` 오름차순으로 방출한다 (결정 A).

    `fetch` 가 호출 예산을 관장한다 — 예산 소진 시 빈 목록을 돌려주면 스트림이 끝난다.
    그 경우 **보류 중인 마지막 블록도 정렬해 방출한다**(잘라 버리면 앞부분이 유실된다).
    """
    pending: list[KiprisRecord] = []          # 아직 완결되지 않은 타이 블록
    page = start_page
    while True:
        items = fetch(ipc, page)
        if not items:
            break
        page += 1
        for rec in items:
            if pending and rec.application_date != pending[0].application_date:
                yield from sorted(pending, key=sort_key)
                pending = []
            pending.append(rec)
        # 페이지 말미의 블록은 다음 페이지까지 미완결일 수 있으므로 여기서 방출하지 않는다.
    yield from sorted(pending, key=sort_key)


def merge_streams(streams: Iterable[Iterator[KiprisRecord]]) -> Iterator[tuple[int, KiprisRecord]]:
    """k-way 합병 + 출원번호 dedup (결정 C).

    방출: `(seq, rec)` — `seq` 는 **1부터의 전역 표집 순번**이며 중복분에는 부여하지 않는다
    (중복도 원장에는 남아야 하므로 드라이버는 `merged_with_dups` 를 쓴다).
    """
    seq = 0
    for rec, dup in merged_with_dups(streams):
        if dup:
            continue
        seq += 1
        yield seq, rec


def merged_with_dups(
    streams: Iterable[Iterator[KiprisRecord]],
) -> Iterator[tuple[KiprisRecord, bool]]:
    """합병 결과를 `(rec, is_duplicate)` 로 전부 방출한다 — 중복도 원장에 남겨야 하기 때문이다.

    힙 원소는 `(정렬키, 스트림 index, rec, iterator)`. 스트림 index 를 2차 tie-break 로 넣어
    같은 키가 여러 스트림에 있어도 **비교가 rec 에 닿지 않고** 결정적으로 끝난다.
    """
    heap: list[tuple[tuple[str, str], int, KiprisRecord, Iterator[KiprisRecord]]] = []
    for i, it in enumerate(streams):
        first = next(it, None)
        if first is not None:
            heap.append((sort_key(first), i, first, it))
    heapq.heapify(heap)

    seen: set[str] = set()
    while heap:
        _, i, rec, it = heapq.heappop(heap)
        nxt = next(it, None)
        if nxt is not None:
            heapq.heappush(heap, (sort_key(nxt), i, nxt, it))
        dup = rec.application_number in seen
        if not dup:
            seen.add(rec.application_number)
        yield rec, dup
