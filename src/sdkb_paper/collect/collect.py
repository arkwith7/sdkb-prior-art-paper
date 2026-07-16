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
from sdkb_paper.preprocess.clean import load_ksia_crosswalk

APPLICANTS = ["삼성전자주식회사", "에스케이하이닉스 주식회사"]
DATE_RANGE = "20100101~20251231"
OUT = RAW_KIPRIS / "patents_raw.parquet"
# C-2 소부장 G₂ (RQ3) · KSIA 소부장 188사(장비·재료·부분품). 질의어는 크로스워크의 match_key
# (법인격 표기를 걷어낸 핵심토큰)다 — ㈜넥스틴 대신 '넥스틴' 으로 질의해야 KIPRIS 의 (주)넥스틴
# 을 부분일치로 잡는다.
# 별도 parquet 에 저장한다: patents_raw.parquet(G₁·H1 의 원천)은 동결이라 건드리지 않는다.
KSIA_OUT = RAW_KIPRIS / "patents_ksia_equipment_raw.parquet"
# 청구항·초록 상세 (출원번호별). delta 후보만 조회한다 — 그래프에 들어갈 특허만 청구항이 필요하다.
KSIA_DETAILS = RAW_KIPRIS / "patents_ksia_equipment_details.parquet"

# PLAN-009 · 좌측절단 교정. H2 의 관측창을 기술의 부상 이전으로 되돌린다.
# **별도 파일로 받는다** — patents_raw.parquet 은 G₁ 과 H1 의 원천이고, G₁ 은 동결이다.
# 이 수집분은 H2 시계열에만 쓰이고 그래프에 병합되지 않는다 (PLAN-009 §2).
#
# 출원인명은 그대로 쓴다: KIPRIS 는 2005–09 출원도 **현재 사명**으로 색인·반환한다
# (실측 2026-07-13 — H01L 2005–09 하이닉스 1,944건이 전부 '에스케이하이닉스 주식회사').
# 사명 변천(주식회사 하이닉스반도체 → SK 편입 2012)은 검색식에 반영할 필요가 없다.
PERIODS = {
    "main": (DATE_RANGE, OUT),
    "extended": ("20050101~20091231", RAW_KIPRIS / "patents_2005_2009.parquet"),
}


def ipc_classes() -> list[str]:
    """룰 테이블의 코드 접두어 → 검색용 4자리 IPC 클래스."""
    rules = pd.read_csv(CODE_MAPPING)
    return sorted({str(c).replace(" ", "")[:4] for c in rules["code_prefix"]})


def ksia_applicants(smoke: bool) -> tuple[list[str], any]:
    """소부장 188사 질의어(match_key). smoke 면 넥스틴 1사만 — 규모 있는 순수 장비사라
    출원인명 매칭과 게이트를 실제로 때린다(파이프라인 관통 검증)."""
    cw = load_ksia_crosswalk()
    if smoke:
        cw = cw[cw["match_key"] == "넥스틴"]
    return cw["match_key"].tolist(), KSIA_OUT


def collect_details(application_numbers: list[str]) -> "pd.DataFrame":
    """delta 후보 출원번호의 초록+전체청구항을 상세 엔드포인트로 모은다(특허당 1회·캐시).

    청구항은 리스트 열로 담는다 — delta 가 청구항당 1트리플(ont:claimText)로 실체화한다.
    """
    client = KiprisClient()
    rows: list[dict] = []
    for i, appnum in enumerate(application_numbers, 1):
        d = client.detail(appnum)
        rows.append({"application_number": appnum, "abstract": d.abstract,
                     "claims": list(d.claims), "claim_count": d.claim_count})
        if i % 200 == 0:
            print(f"  상세 {i:,}/{len(application_numbers):,}", flush=True)
    df = pd.DataFrame(rows)
    KSIA_DETAILS.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(KSIA_DETAILS, index=False)
    got = int((df["claims"].apply(len) > 0).sum()) if len(df) else 0
    print(f"\n✓ 상세 {len(df):,}건 (청구항 보유 {got:,}) → {KSIA_DETAILS}")
    return df


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true",
                    help="관통 검증: samsung-hynix 는 클래스 1개 · ksia-equipment 는 넥스틴 1사")
    ap.add_argument("--details", action="store_true",
                    help="ksia-equipment: 서지 대신 델타 후보의 초록·청구항 상세를 수집한다")
    ap.add_argument("--corpus", choices=["samsung-hynix", "ksia-equipment"], default="samsung-hynix",
                    help="samsung-hynix=G₁(PLAN-002) · ksia-equipment=G₂ 소부장(RQ3 · PLAN-014 C-2)")
    ap.add_argument("--period", choices=sorted(PERIODS), default="main",
                    help="main=2010–2025 (G₁ 의 원천) · extended=2005–2009 (PLAN-009 · H2 전용)")
    args = ap.parse_args()

    if args.details:
        if args.corpus != "ksia-equipment":
            ap.error("--details 는 ksia-equipment 코퍼스에만 쓴다")
        from sdkb_paper.preprocess.profile import KSIA_DELTA
        cand = pd.read_parquet(KSIA_DELTA)
        # G₂ 에 실제로 들어갈 매핑 특허만 상세수집한다 — 게이트에서 탈락할 미매핑 특허의
        # 청구항을 긁는 것은 불필요한 API 호출이다(§ KIPRIS 규칙 준수).
        mapped = cand[(cand["n_process"] > 0) | (cand["n_device"] > 0)]
        appnums = mapped["application_number"].drop_duplicates().tolist()
        print(f"델타 매핑 특허 {len(appnums):,}건의 초록·청구항 상세 수집 (특허당 1회·캐시)")
        collect_details(appnums)
        return 0

    classes = ipc_classes()
    if args.corpus == "ksia-equipment":
        applicants, out = ksia_applicants(args.smoke)
        date_range = DATE_RANGE
    else:
        applicants = APPLICANTS
        date_range, out = PERIODS[args.period]
        if args.smoke:
            classes = ["G03F"]  # 규모가 작고 공정 룰이 확실한 클래스

    client = KiprisClient()
    rows: list[dict] = []
    for applicant in applicants:
        for ipc in classes:
            n = client.total_count(applicant, ipc, date_range)
            got = [r.__dict__ for r in client.search(applicant, ipc, date_range)]
            rows.extend(got)
            flag = "" if len(got) == n else f"  ⚠ totalCount={n} 와 불일치"
            print(f"  {applicant:16s} {ipc:5s} {len(got):>6,}건{flag}", flush=True)

    df = pd.DataFrame(rows)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    uniq = df["application_number"].nunique() if len(df) else 0
    print(f"\n✓ 원시 {len(df):,}행 (출원번호 고유 {uniq:,}) → {out}")
    print("  다음: preprocess (출원인 정확일치 필터 · 중복 제거 · 프로파일)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
