"""서명 수치 표류 검사 — 원고·문서가 CANONICAL-INDEX §1 과 정합한지 검증한다.

CANONICAL-INDEX.md §1 의 "트리플 (정본)" 행을 파싱해 정본 서명(G0/G1/G2)을 얻고,
낡은 서명(HISTORICAL_SIGNATURES)이 검사 대상 문서에 '현재 값'으로 남아 있으면 실패한다.

의도적 이력 서술은 예외로 둔다 — 다음 중 하나면 그 줄은 검사하지 않는다:
  (1) 줄에 `구 <서명>` 표기가 있는 경우 (예: "정본 · 구 868,669")
  (2) "확정 이력" 으로 시작하는 블록 내부 (빈 줄까지)
  (3) 줄에 `<!-- sig-history -->` 마커가 있는 경우 (원고의 진화 서사 문단용)

사용: uv run python scripts/check_signatures.py   (CI quality-gate 의 한 스텝)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANONICAL = ROOT / "01.code_spec" / "CANONICAL-INDEX.md"
BASELINE_TEST = ROOT / "tests" / "test_baseline_integration.py"

# 검사 대상: 서명 수치를 '현재 값'으로 인용하는 문서
# (STATUS.md 는 서사 정본이라 구 서명 보존이 설계 — 제외.
#  구 원고 v0.5/v0.7 은 paper/archive/ 로 이관됨 — 동결 이력이라 검사 제외.)
TARGETS = [
    ROOT / "paper" / "논문_v0_9_SDKB_통합초안.md",   # v0.9 정본 원고
    ROOT / "README.md",
    ROOT / "data" / "DATASET-CARD.md",
]

# 재동결·교정 이전의 낡은 서명 — 새 세대 확정 시 직전 세대를 여기에 추가한다.
HISTORICAL_SIGNATURES = [
    # 2026-08-15 vendor(상류 0a7ff15 · PLAN-050 · +43 은 전부 T-Box 주석) 이전의 네 세대.
    # 115,076·118,808·119,208 은 문서에 '현재 값'으로 등장한 적이 없으나, 재등장하면 그것도
    # 표류이므로 함께 내린다. 세대별 실측은 tests/test_baseline_integration.py 가 보유한다.
    "115,095", "115,076", "118,808", "119,208",
    # 2026-08-05 G₀ 재조립(상류 39855bb · CR-008·CR-009·CR-004R 반영 · 105,713 → 115,095) 이전.
    # PLAN-035 두 팔(D-23)이 이 세대 위에서 측정됐다 — O′ 팔의 서명이다.
    "105,713",
    # 2026-08-01 G₀ 재조립(상류 2839afb · CR-007 반영 · 105,588 → 105,713) 이전.
    # v0.9 §6 의 모든 결과가 이 세대 위에서 측정됐으므로 원고의 인용은 `<!-- sig-history -->`
    # 로 예외 처리한다 — 수치를 새 세대로 갈아끼우면 실제로 돌린 자원과 달라진다(CLAUDE.md §1-1).
    "105,588",
    "49,307", "868,669", "434,342",   # 2026-07-23 동결 해제(커밋 3429d66) 이전
    "49,210", "44,221", "44,202", "44,192", "43,814", "413,340", "418,738",
]

HISTORY_MARKER = "<!-- sig-history -->"


def canonical_signatures() -> list[str]:
    text = CANONICAL.read_text(encoding="utf-8")
    m = re.search(r"\*\*트리플 \(정본\)\*\*\s*\|([^|]+)\|([^|]+)\|([^|]+)\|", text)
    if not m:
        sys.exit("CANONICAL-INDEX §1 에서 '트리플 (정본)' 행을 찾지 못했다 — 표 형식 변경 여부 확인.")
    return [re.sub(r"[^\d,]", "", g).strip() for g in m.groups()]


def anchor_signature() -> str | None:
    """G₀ 정본 서명의 **외부 정박점** — 통합 테스트가 디스크에서 실측해 고정한 값.

    왜 필요한가 (2026-08-20 · 실제로 새어 나간 표류를 막는다). 이 검사기는 CANONICAL-INDEX §1 을
    읽어 *다른 문서가 §1 과 맞는가*만 보았다. 즉 §1 자체가 낡으면 **전원이 사이좋게 틀린 채
    통과**한다. 실제로 그랬다 — 디스크의 G₀ 는 2026-08-15 vendor 로 119,251 이 되었는데 §1 ·
    DATASET-CARD · MANIFEST 는 115,095 세대에 머물러 있었고, 이 검사기는 5일 동안 녹색이었다.

    정박점을 `tests/test_baseline_integration.py` 의 `SNAPSHOT_OBSERVATIONS["current"]` 로 둔다.
    그 값은 `test_baseline_signature` 가 **실제 graph_v0.ttl 을 파싱해** 대조하므로, 디스크와
    어긋나면 테스트가 먼저 실패한다. 여기서 26 MB 를 다시 파싱하지 않는 이유는 이 검사기가 매
    커밋 도는 게이트이기 때문이다 — 느린 검사는 꺼지고, 꺼진 검사는 없는 검사다.
    """
    m = re.search(r'"current":\s*\{"triples":\s*(\d+)', BASELINE_TEST.read_text(encoding="utf-8"))
    return f"{int(m.group(1)):,}" if m else None


def exempt_lines(lines: list[str]) -> set[int]:
    """이력 서술로 간주해 검사에서 제외할 줄 번호(1-기반)."""
    exempt: set[int] = set()
    in_history_block = False
    for i, line in enumerate(lines, 1):
        if "확정 이력" in line:
            in_history_block = True
        if in_history_block:
            exempt.add(i)
            if not line.strip():
                in_history_block = False
        if HISTORY_MARKER in line:
            exempt.add(i)
    return exempt


def main() -> int:
    canon = canonical_signatures()
    print(f"정본 서명 (CANONICAL-INDEX §1): G0={canon[0]} · G1={canon[1]} · G2={canon[2]}\n")
    failed = False

    # §1 자체가 디스크와 어긋나지 않는가 — 문서끼리만 대조하면 전원이 함께 낡는다.
    anchor = anchor_signature()
    if anchor is None:
        print("[warn] 정박점을 읽지 못했다 — tests/test_baseline_integration.py 의 "
              "SNAPSHOT_OBSERVATIONS 형식 변경 여부 확인\n")
    elif anchor != canon[0]:
        failed = True
        print(f"[FAIL] CANONICAL-INDEX §1 의 G₀ 서명 {canon[0]} 이 디스크 정박점 {anchor} 과 다르다.\n"
              f"       정박점은 tests/test_baseline_integration.py 의 "
              f'SNAPSHOT_OBSERVATIONS["current"] 이며, 그 값은 실제 graph_v0.ttl 로 검증된다.\n'
              f"       §1 을 갱신하고 직전 세대를 HISTORICAL_SIGNATURES 에 내릴 것.\n")
    else:
        print(f"[ok]   CANONICAL-INDEX §1 G₀ = 디스크 정박점 {anchor}\n")
    manuscripts_seen = 0

    for target in TARGETS:
        if not target.exists():
            continue
        lines = target.read_text(encoding="utf-8").splitlines()
        rel = target.relative_to(ROOT)
        skip = exempt_lines(lines)

        stale_hits = []
        for i, line in enumerate(lines, 1):
            if i in skip:
                continue
            for sig in HISTORICAL_SIGNATURES:
                if sig in line and not re.search(rf"구\s*{re.escape(sig)}", line):
                    stale_hits.append((sig, i))
        if stale_hits:
            failed = True
            print(f"[FAIL] {rel} — 낡은 서명 {len(stale_hits)}건 (현재 값으로 인용):")
            for sig, ln in stale_hits:
                print(f"       L{ln}: {sig}")
        else:
            print(f"[ok]   {rel}")

        if target.name.startswith("논문"):
            manuscripts_seen += 1
            text = "\n".join(lines)
            if not any(s in text for s in canon):
                print("       ⚠ 정본 서명(G0/G1/G2)이 원고에 한 건도 없음 — 재산출 미반영 가능성")

    if manuscripts_seen == 0:
        print("[warn] 검사할 원고 파일이 없음 — TARGETS 갱신 필요")

    if failed:
        print("\n서명 표류 검출 — CANONICAL-INDEX §1 기준으로 갱신하거나, 의도적 이력 서술이면")
        print("해당 줄에 `구 <서명>` 표기 또는 `<!-- sig-history -->` 마커를 붙일 것.")
        return 1
    print("\n서명 정합 ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
