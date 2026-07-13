"""삼성전자·SK하이닉스 특허 수집 (PLAN-002).

수집 범위는 세 축의 곱이다.

  출원인   삼성전자주식회사 · 에스케이하이닉스 주식회사
           (KIPRIS `applicant` 는 부분일치라 계열사가 섞여 나온다. 정확일치 필터는 preprocess.)
  IPC     **룰 테이블에서 파생한다** (`code_to_concept.csv` 의 4자리 접두어).
           룰과 수집 범위가 어긋날 수 없게 하기 위해서다 — 룰 없는 코드를 수집하면 게이트에서
           전량 탈락하고, 룰 있는 코드를 안 수집하면 커버리지가 이유 없이 비는다.
  기간     출원일 2010–2025 (PLAN-002 에서 확정. 결과를 본 뒤 바꾸지 않는다.)

산출: data/raw/kipris/patents_raw.parquet  (커밋하지 않는다)
"""
from __future__ import annotations

import argparse

import pandas as pd

from sdkb_paper.collect.kipris_client import KiprisClient
from sdkb_paper.config import CODE_MAPPING, RAW_KIPRIS

APPLICANTS = ["삼성전자주식회사", "에스케이하이닉스 주식회사"]
DATE_RANGE = "20100101~20251231"
OUT = RAW_KIPRIS / "patents_raw.parquet"


def ipc_classes() -> list[str]:
    """룰 테이블의 코드 접두어 → 검색용 4자리 IPC 클래스."""
    rules = pd.read_csv(CODE_MAPPING)
    return sorted({str(c).replace(" ", "")[:4] for c in rules["code_prefix"]})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true", help="클래스 1개만 (파이프라인 관통 검증용)")
    args = ap.parse_args()

    classes = ipc_classes()
    if args.smoke:
        classes = ["G03F"]  # 규모가 작고 공정 룰이 확실한 클래스

    client = KiprisClient()
    rows: list[dict] = []
    for applicant in APPLICANTS:
        for ipc in classes:
            n = client.total_count(applicant, ipc, DATE_RANGE)
            got = [r.__dict__ for r in client.search(applicant, ipc, DATE_RANGE)]
            rows.extend(got)
            flag = "" if len(got) == n else f"  ⚠ totalCount={n} 와 불일치"
            print(f"  {applicant:16s} {ipc:5s} {len(got):>6,}건{flag}", flush=True)

    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)
    uniq = df["application_number"].nunique() if len(df) else 0
    print(f"\n✓ 원시 {len(df):,}행 (출원번호 고유 {uniq:,}) → {OUT}")
    print("  다음: preprocess (출원인 정확일치 필터 · 중복 제거 · 프로파일)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
