"""특허 → 문제원자 추출 (§G1 Phase C · C2).

특허 제목+초록을 Bedrock Haiku 로 파싱해 "이 특허가 푸는 문제"(FailureMode·RootCause)를 추출한다.
목적: 특허를 문제 공간에 연결하는 데이터층(선행기술 설명 + 하류 매칭 substrate). 매칭 성능은
만들지 않는다 — **전문가 매칭 뷰에 외부 정답이 없기 때문이다**(A-Box 는 전량 합성 ·
CLAUDE.md §0.0.2·§0.0.3). 파일럿(2026-07-22)에서 추출수율 89% 실증.

- **어휘 발명 0**: 기존 ont:FailureMode 25 · ont:RootCause 20 개념에 정렬한다(delta 가
  ont:exhibitsFailureMode / ont:relatedToTopic 로 실체화 — 둘 다 SDKB TBox 에 이미 있는 술어).
  기존에 없는 결함은 canonical="none" · raw 만 남긴다(신규 개념 채택은 사람 — §1 날조 금지).
- **결정성**: temperature 0 + sqlite 캐시(키에 모델 포함). 실패는 지어내지 않고 None(정직 결측).
- **egress**: 초록 전문이 Bedrock 으로 나간다(KIPRIS 비재배포 · 사용자 승인 2026-07-22).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from sdkb_paper.collect.collect import SH_DETAILS
from sdkb_paper.config import INTERIM, RAW_KIPRIS, ROOT
from sdkb_paper.preprocess.profile import DELTA

# Bedrock 자격증명·모델 ID 를 .env 에서 os.environ 으로 올린다(boto3 가 환경에서 읽는다).
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

# 기존 SDKB ont:FailureMode / ont:RootCause 개념 slug (data/external/sdkb 실측 · 정렬 타깃).
# 여기 없는 결함모드는 canonical="none" 으로 두고 raw 만 보존한다 — 신규 개념 채택은 상류에서 사람이.
FAILURE_MODES = [
    "bowing", "bridging", "cdu", "delamination", "dishing", "erosion", "footing", "haze",
    "hillock", "ler", "line_width_variation", "microtrenching", "overlay_error", "particle",
    "pattern_collapse", "pinhole", "residue", "scratches", "scumming", "seam",
    "sidewall_angle_deviation", "step_coverage_issue", "stress_induced_crack", "undercut", "void",
]
ROOT_CAUSES = [
    "alignment_error", "charging", "electrostatic_discharge", "equipment_aging",
    "gas_flow_instability", "humidity_variation", "mask_defect", "material_contamination",
    "metal_interdiffusion", "oxidation", "particle_contamination", "polymer_buildup",
    "poor_adhesion", "precursor_depletion", "rf_power_variation", "slurry_instability",
    "stress_mismatch", "temperature_drift", "thickness_nonuniformity", "vacuum_leak",
]

OUT = INTERIM / "patent_problems.jsonl"
CACHE = RAW_KIPRIS / "problem_extract_cache.sqlite"
MODEL = os.getenv("AWS_BEDROCK_MODEL_HAIKU", "")

SYSTEM = (
    "너는 반도체 제조공정 특허 분석 전문가다. 특허의 제목과 초록을 읽고 이 특허가 해결하려는 "
    "기술적 문제를 반도체 공정 결함(failure mode)·근본원인(root cause) 관점에서 추출한다. "
    "특허는 대개 어떤 결함/문제를 줄이거나 없애는 방법·구조를 제안한다. 명확한 결함/문제가 "
    "없으면 solves_problem=false 로 정직하게 답하라. 지어내지 마라.\n"
    "아래 표준 어휘 중 가장 가까운 것을 failure_mode/root_cause 에 slug 로 고르되, 해당 없으면 "
    "\"none\". 자유서술(_raw)은 항상 한글로 채운다.\n"
    f"FailureMode: {FAILURE_MODES}\n"
    f"RootCause: {ROOT_CAUSES}\n"
    "JSON 객체만 출력(설명 금지):\n"
    '{"solves_problem": true|false, "problem_ko": "문제 한 줄", '
    '"failure_mode_raw": "자유서술 결함(한글)", "failure_mode": "<slug|none>", '
    '"root_cause_raw": "자유서술 원인(한글, 없으면 빈문자열)", "root_cause": "<slug|none>"}'
)

_CLIENT = None
_LOCK = threading.Lock()  # 하나의 sqlite 연결을 16 스레드가 공유 — 접근을 직렬화한다


def _client():
    global _CLIENT
    if _CLIENT is None:
        import boto3
        _CLIENT = boto3.client("bedrock-runtime", region_name=os.getenv("AWS_REGION", "us-east-1"))
    return _CLIENT


def _cache() -> sqlite3.Connection:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(CACHE, check_same_thread=False)
    c.execute("CREATE TABLE IF NOT EXISTS c (k TEXT PRIMARY KEY, v TEXT)")
    return c


def _key(text: str) -> str:
    return hashlib.sha256(f"{MODEL}\n{text}".encode()).hexdigest()


def _bedrock_json(user: str) -> dict | None:
    """Bedrock converse → JSON 객체. 스로틀은 백오프, 그 외 실패는 None(정직 결측)."""
    import time
    cli = _client()
    for attempt in range(6):
        try:
            r = cli.converse(
                modelId=MODEL, system=[{"text": SYSTEM}],
                messages=[{"role": "user", "content": [{"text": user}]}],
                inferenceConfig={"temperature": 0, "maxTokens": 512})
            txt = r["output"]["message"]["content"][0]["text"]
            i, j = txt.find("{"), txt.rfind("}")
            return json.loads(txt[i:j + 1]) if i != -1 and j > i else None
        except Exception as e:  # noqa: BLE001 — 스로틀만 재시도, 그 외는 결측 보고
            if "Throttl" in type(e).__name__ or "Throttl" in str(e):
                time.sleep(min(2 ** attempt * 0.5, 16))
                continue
            return None
    return None


def extract_one(appnum: str, title: str, abstract: str, cache: sqlite3.Connection) -> dict | None:
    user = f"제목: {title}\n초록: {abstract[:1800]}"
    k = _key(user)
    with _LOCK:
        row = cache.execute("SELECT v FROM c WHERE k=?", (k,)).fetchone()
    if row:
        return json.loads(row[0])
    out = _bedrock_json(user)  # 네트워크 호출은 락 밖에서 — 병렬 유지
    if out is not None:
        with _LOCK:
            cache.execute("INSERT OR REPLACE INTO c (k,v) VALUES (?,?)", (k, json.dumps(out, ensure_ascii=False)))
            cache.commit()
    return out


def load_patents() -> pd.DataFrame:
    """병합 특허 24,179 의 (출원번호·제목·초록). 초록=상세엔드포인트(SH_DETAILS)."""
    d = pd.read_parquet(DELTA)[["application_number", "invention_title"]]
    s = pd.read_parquet(SH_DETAILS)[["application_number", "abstract"]]
    return s.merge(d, on="application_number", how="left")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="스모크: 앞 N건만")
    ap.add_argument("--workers", type=int, default=int(os.getenv("LLM_WORKERS", "16")))
    args = ap.parse_args()

    if not MODEL:
        ap.error("AWS_BEDROCK_MODEL_HAIKU 미설정 — .env 확인 (Bedrock 필요)")

    df = load_patents()
    if args.limit:
        df = df.head(args.limit)
    OUT.parent.mkdir(parents=True, exist_ok=True)

    done = set()
    if OUT.exists():
        for line in OUT.open():
            done.add(json.loads(line)["application_number"])
    todo = df[~df["application_number"].isin(done)]
    print(f"추출 대상 {len(todo):,} / 전체 {len(df):,} (기처리 {len(done):,}) · {args.workers}-way Bedrock")

    cache = _cache()
    rows = list(todo.itertuples(index=False))

    def work(r):
        return r.application_number, extract_one(r.application_number, r.invention_title or "", r.abstract or "", cache)

    n = fail = 0
    with OUT.open("a") as fh, ThreadPoolExecutor(max_workers=args.workers) as ex:
        for appnum, ext in ex.map(work, rows):
            n += 1
            if ext is None:
                fail += 1
                continue
            fh.write(json.dumps({"application_number": appnum, **ext}, ensure_ascii=False) + "\n")
            if n % 500 == 0:
                print(f"  {n:,}/{len(rows):,} (실패 {fail})", flush=True)
    print(f"✓ 추출 {n - fail:,} · 실패 {fail} (정직 결측 — 지어내지 않음) → {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
