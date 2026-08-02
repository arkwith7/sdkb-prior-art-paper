"""CR-008 봉인 이관의 규율 강제 — PLAN-031 §11.3·§11.4 회귀 테스트.

이관 파일은 **식별자 집합**이지 채점표가 아니다. 이 테스트가 지키는 것은 셋이다.

  1. 검색 파이프라인(`src/`)의 어떤 코드도 이 파일을 읽지 않는다 (§11.4-1)
  2. 파일이 질의–인용 대응을 흘리지 않는다 — 질의 출원번호가 한 건도 등장하지 않는다 (§11.2)
  3. 파일이 결정적으로 재생성된다 — 514행 · 사전순 · sha256 불변 (§11.3)
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
HANDOFF = ROOT / "upstream" / "handoff" / "CR-008-b-cited-ids.txt"
SEALED_QREL = ROOT / "data" / "processed" / "ir" / "qrel_b_sealed.parquet"

# §11.3 동결값. 파일이 바뀌면 이 상수가 아니라 사전등록을 먼저 본다.
EXPECTED_ROWS = 514
EXPECTED_SHA256 = "9d0a7c0fc97547a67018556504d32d0b3ac8e22d2761f98e342ab3158c4b2dff"


def test_no_src_code_reads_the_handoff_file():
    """§11.4-1 — 이 경로를 참조하는 코드가 `src/` 아래에 있으면 실패한다."""
    needles = ("CR-008-b-cited-ids", "upstream/handoff")
    offenders = [
        str(p.relative_to(ROOT))
        for p in (ROOT / "src").rglob("*.py")
        if any(n in p.read_text(encoding="utf-8", errors="ignore") for n in needles)
    ]
    assert offenders == [], (
        "이관 파일을 참조하는 파이프라인 코드가 있다 — 봉인 규율 위반(PLAN-031 §11.4-1): "
        f"{offenders}"
    )


def test_handoff_shape_is_frozen():
    """§11.3 — 1줄 1건 · 사전순 정렬 · 514행 · 빈 줄 없음."""
    lines = HANDOFF.read_text(encoding="utf-8").split("\n")
    assert lines[-1] == "", "파일은 개행으로 끝난다"
    ids = lines[:-1]
    assert len(ids) == EXPECTED_ROWS
    assert all(x.strip() == x and x for x in ids), "빈 줄·양끝 공백 금지"
    assert ids == sorted(ids), "사전순 정렬이 아니다 — 원본 행 순서가 대응을 흘린다"
    assert len(set(ids)) == EXPECTED_ROWS, "중복 행이 있다 — 집합이 아니다"


def test_handoff_sha256_is_stable():
    """이관 후 파일은 바뀌지 않는다(§11.3 말미)."""
    digest = hashlib.sha256(HANDOFF.read_bytes()).hexdigest()
    assert digest == EXPECTED_SHA256


def test_handoff_carries_no_query_identifier():
    """§11.2 — 질의 출원번호가 단 한 건도 파일에 등장하지 않는다."""
    pd = pytest.importorskip("pandas")
    if not SEALED_QREL.exists():
        pytest.skip("봉인 qrel 이 로컬에 없다 (gitignore 대상)")

    text = HANDOFF.read_text(encoding="utf-8")
    queries = {
        str(x) for x in pd.read_parquet(SEALED_QREL, columns=["application_number"])["application_number"]
    }
    leaked = sorted(q for q in queries if q in text)
    assert leaked == [], f"질의 식별자가 이관 파일에 새어 나갔다: {leaked[:5]}"
