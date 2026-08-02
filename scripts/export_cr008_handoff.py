"""CR-008 봉인 이관 파일 생성 — 인용 문헌 **식별자 집합만** 상류로 내보낸다.

사전등록: `01.code_spec/plans/PLAN-031-b-layer-second-confirmation-split.md` §11 (🔒 동결).

  내보내는 것   : 봉인 qrel 의 `examiner_citations` **고유값 집합** (순서 없는 집합)
  내보내지 않는 것: 질의–인용 대응(어느 질의가 무엇을 인용했는가) · 인용 순번 · 인용 등급 ·
                   질의별 인용 개수 · 질의 출원번호

**왜 이 스크립트가 `src/` 밖에 있는가.** §11.4-1 이 "이 파일을 검색 파이프라인의 어떤 단계도
읽지 않는다"를 회귀 테스트로 강제한다(`tests/test_handoff_seal_discipline.py`). 생성기를 `src/`
안에 두면 그 테스트가 실패해야 옳고, 예외를 뚫으면 규율이 무의미해진다. 그래서 이관은
**파이프라인이 아니라 일회성 사람 조작**으로 남긴다.

정렬은 유니코드 코드포인트 오름차순이다 — 원본 행 순서(질의 순서)가 대응을 흘리는 것을 막는다.

사용: uv run python scripts/export_cr008_handoff.py [--check]
      --check 는 파일을 쓰지 않고 기존 파일과 일치하는지만 검사한다(재현성 확인용).
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SEALED_QREL = ROOT / "data" / "processed" / "ir" / "qrel_b_sealed.parquet"
OUT = ROOT / "upstream" / "handoff" / "CR-008-b-cited-ids.txt"

# §11.3 동결: 514행. 행수가 달라지면 봉인 파일이 바뀐 것이므로 멈춘다.
EXPECTED_ROWS = 514


def build() -> str:
    df = pd.read_parquet(SEALED_QREL, columns=["examiner_citations"])
    ids = sorted({str(x) for x in df["examiner_citations"]})

    if len(ids) != EXPECTED_ROWS:
        raise SystemExit(
            f"고유 식별자 {len(ids)}건 — 동결값 {EXPECTED_ROWS}건과 다르다. "
            "봉인 qrel 이 바뀌었다면 이관이 아니라 사전등록부터 다시 본다(PLAN-031 §11)."
        )
    if any("\n" in x or "\r" in x for x in ids):
        raise SystemExit("식별자에 줄바꿈이 있다 — 1줄 1건 규약이 깨진다.")

    return "\n".join(ids) + "\n"


def main() -> int:
    text = build()
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()

    if "--check" in sys.argv:
        if not OUT.exists():
            print(f"FAIL: {OUT} 없음")
            return 1
        same = OUT.read_text(encoding="utf-8") == text
        print(f"{'OK' if same else 'FAIL'}: {OUT.name} · sha256 {digest}")
        return 0 if same else 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(f"{OUT} · {EXPECTED_ROWS}행 · sha256 {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
