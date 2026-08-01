"""스크리닝 원장 — append-only JSONL · 1행 = 1후보 (PLAN-032 §5.4).

원장은 **재현 좌표이자 재개 상태**다. 두 규율이 걸린다.

1. **봉인(CLAUDE §1-4 · PLAN-032 §1 성공기준 ⑤).** 원장은 인용문헌 *식별자* 를 담지 않는다 —
   건수와 NPL 여부만 담는다. 정답 식별자는 `B_QREL_SEALED` 로 직행하며 파일럿 단계에서
   어떤 코드도 그 파일을 읽지 않는다. `FORBIDDEN_FIELDS` 가 이를 코드로 강제한다.
2. **결정성.** `fetched_at` 을 뺀 나머지는 동일 캐시로 재실행하면 바이트 동일해야 한다(테스트 T7).
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

# 원장에 절대 들어오면 안 되는 이름 — 들어오면 봉인이 깨진다. 테스트 T10 이 값 패턴까지 본다.
FORBIDDEN_FIELDS = frozenset({
    "examiner_citations", "citations", "prior_art", "qrel", "ground_truth", "cited_doc_id",
})
# 결정성 비교에서 제외하는 열(시각만).
VOLATILE_FIELDS = frozenset({"fetched_at"})


@dataclass(frozen=True)
class LedgerRow:
    seq: int                       # 전역 표집 순번 (1부터 · 중복분은 0)
    application_number: str
    application_date: str
    ipc_leading: str
    ipc_all: str
    register_status: str
    stream_ipc: str
    page_no: int
    cache_key: str                 # 원응답 캐시 키 (재현 좌표)
    stage: str                     # free · family · detail · audit
    verdict: str                   # accepted · rejected · audited
    reason: str                    # Reason 동결 코드
    detail_call_used: bool
    family_id: str = ""
    family_method: str = ""        # docdb-app · unresolved
    examiner_citation_count: int = 0
    npl_only: bool = False
    has_claim1: bool = False
    fetched_at: str = ""

    def __post_init__(self) -> None:
        assert_sealed({f.name: None for f in fields(self)})


@dataclass
class ResumeState:
    """원장 재생으로 복원되는 진행 상태 — 중단 후 재개의 유일한 근거."""

    last_seq: int = 0
    accepted: int = 0
    detail_calls: int = 0
    audit_calls: int = 0
    seen_applications: set[str] = field(default_factory=set)


def assert_sealed(payload: dict) -> dict:
    """원장에 나갈 payload 가 봉인 규율을 지키는지 확인한다 — **쓰기 직전 마지막 관문**.

    현재 스키마에서는 통과가 자명하다. 이 가드가 있는 이유는 **미래의 편집** 때문이다 —
    누군가 인용 식별자를 원장에 담으면 파일이 만들어지기 전에 실패해야 한다.
    """
    violated = sorted(set(payload) & FORBIDDEN_FIELDS)
    if violated:
        raise ValueError(f"원장 봉인 위반: {violated} — 인용 식별자는 봉인 파일로만 나간다")
    return payload


def append(path: Path, row: LedgerRow) -> None:
    """1행 append. 원자성은 줄 단위 flush 로 확보한다 — 중단 시 마지막 줄만 잃는다."""
    payload = assert_sealed(asdict(row))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        fh.flush()


def load(path: Path) -> list[LedgerRow]:
    """원장 재생. 마지막 줄이 잘려 있으면(중단) 버린다 — 조용히 넘어가지 않고 개수로 드러난다."""
    if not path.exists():
        return []
    rows: list[LedgerRow] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(LedgerRow(**json.loads(line)))
        except (json.JSONDecodeError, TypeError):
            break
    return rows


def replay_state(rows: list[LedgerRow]) -> ResumeState:
    state = ResumeState()
    for row in rows:
        state.last_seq = max(state.last_seq, row.seq)
        state.seen_applications.add(row.application_number)
        if row.stage == "audit":
            state.audit_calls += 1
        elif row.detail_call_used:
            state.detail_calls += 1
        if row.verdict == "accepted":
            state.accepted += 1
    return state


def comparable(rows: list[LedgerRow]) -> list[dict]:
    """결정성 비교용 정규화 — 시각만 뺀다(테스트 T7)."""
    return [
        {k: v for k, v in asdict(r).items() if k not in VOLATILE_FIELDS}
        for r in rows
    ]
