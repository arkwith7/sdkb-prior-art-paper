"""부록 B(주장–증거 매트릭스) ↔ §6.3(가설 판정표) 정합 (PLAN-024 §4 · N12).

N5e 에서 드러난 결함은 "표 6.6 의 값이 틀렸다"가 아니라 **같은 사실이 두 곳에 살면서 한쪽만
갱신됐다**는 것이었다. 부록 B 는 심사자가 §6 보다 먼저 보는 요약표라 같은 표류가 더 비싸다.
사람이 두 표를 눈으로 맞추는 절차를 남기지 않고 기계가 강제한다.

1. §6.3 에 판정이 있는 가설이 부록 B 에서 "미실험"이면 실패.
2. 부록 B 상태 열에 소수점 수치가 있으면 실패 — 수치의 집은 §6.3 하나다(PLAN-024 §3).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

PAPER = Path(__file__).resolve().parents[1] / "paper" / "archive" / "논문_v0_9_SDKB_통합초안.md"

# §6.3 판정 열이 아직 비어 있음을 뜻하는 표기 — 이것이 있으면 "판정 없음"으로 센다.
PLACEHOLDERS = ("[지지/기각", "[실험 후 기입]", "[기입]")


def _section(text: str, start: str, end: str | None) -> str:
    """[start, end) 구간. `end=None` 이면 문서 끝까지 — 마지막 절을 잡을 때 쓴다."""
    i = text.index(start)
    j = text.index(end, i) if end is not None else len(text)
    return text[i:j]


def _rows(section: str) -> list[list[str]]:
    """마크다운 표의 데이터 행만 셀 리스트로. 헤더·구분선 제외."""
    out = []
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c) <= {"-", ":"} for c in cells) or not any(cells):
            continue
        out.append(cells)
    return out


def _norm(label: str) -> str:
    """'H3 조건부' → 'H3'. 조건부 행은 같은 가설의 하위 조항이다."""
    m = re.match(r"(H\d[′″]?)", label)
    return m.group(1) if m else label


@pytest.fixture(scope="module")
def paper() -> str:
    if not PAPER.exists():  # pragma: no cover - 원고 경로 변경 시 조용히 통과시키지 않는다
        pytest.fail(f"정본 원고를 찾지 못했다: {PAPER}")
    return PAPER.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def verdicts(paper: str) -> dict[str, str]:
    """§6.3 판정표 → {가설: 판정}. 자리표시자 판정은 담지 않는다."""
    sec = _section(paper, "## 6.3 가설 판정표", "## 6.4")
    got: dict[str, str] = {}
    for cells in _rows(sec):
        m = re.match(r"\*\*(H\d[′″]?)\*\*", cells[0])
        if not m or len(cells) < 4:
            continue
        verdict = cells[-1]
        if any(p in verdict for p in PLACEHOLDERS):
            continue
        got[m.group(1)] = verdict
    return got


@pytest.fixture(scope="module")
def appendix_b(paper: str) -> list[tuple[str, str, str]]:
    """부록 B → [(가설, 주장문, 상태)]. 가설 라벨이 없는 행은 제외."""
    # v2.0 재구성(PLAN-033)에서 부록 B 는 축약본이 되고 부록 A·C–H 는 supplementary 로
    # 이동해, 이제 문서의 마지막 절이다 — 끝 앵커를 두지 않는다.
    sec = _section(paper, "# 부록 B.", None)
    out = []
    for cells in _rows(sec):
        if len(cells) < 3:
            continue
        m = re.search(r"\((H\d[^)]*)\)", cells[0])
        if not m:
            continue
        out.append((_norm(m.group(1)), cells[0], cells[2]))
    return out


def test_section_63_has_verdicts(verdicts):
    """전제가 무너지면(파싱 실패) 아래 두 테스트가 조용히 공허해진다."""
    assert {"H1", "H3", "H4", "H5"} <= set(verdicts), f"§6.3 파싱 결과가 빈약하다: {verdicts}"


def test_appendix_b_has_hypothesis_rows(appendix_b):
    labels = {h for h, _, _ in appendix_b}
    assert {"H1", "H2", "H3", "H4", "H5"} <= labels, f"부록 B 파싱 결과가 빈약하다: {labels}"


def test_no_unexperimented_row_for_a_judged_hypothesis(verdicts, appendix_b):
    """§6.3 이 판정한 가설을 부록 B 가 '미실험'이라 부르면 안 된다 (N12 의 결함 그 자체)."""
    stale = [(h, claim, status) for h, claim, status in appendix_b
             if h in verdicts and "미실험" in status]
    assert not stale, (
        "부록 B 가 §6.3 의 판정을 부정한다 — 한쪽만 갱신된 표류다:\n"
        + "\n".join(f"  {h}: {claim!r} 상태={status!r} (§6.3 판정={verdicts[h]!r})"
                    for h, claim, status in stale))


def test_appendix_b_status_carries_no_decimal_numbers(appendix_b):
    """상태 열은 판정어와 §6 참조만 담는다 — 수치를 복사하면 두 번째 진실이 생긴다.

    주장 열(첫 칸)의 자원 수치("노드 도달성 95.3%")는 대상이 아니다. 표류가 생기는 곳은
    실험 결과를 옮겨 적는 상태 열이다.
    """
    # 절 참조(§6.3·표 6.6)는 수치가 아니라 주소다 — 검사 전에 제거한다.
    def _strip_refs(s: str) -> str:
        return re.sub(r"[§표]\s*\d+(\.\d+)*", "", s)

    offenders = [(h, status) for h, _, status in appendix_b
                 if re.search(r"\d\.\d", _strip_refs(status))]
    assert not offenders, (
        "부록 B 상태 열에 수치가 들어갔다 — 수치의 집은 §6.3 하나다 (PLAN-024 §3):\n"
        + "\n".join(f"  {h}: {status!r}" for h, status in offenders))
