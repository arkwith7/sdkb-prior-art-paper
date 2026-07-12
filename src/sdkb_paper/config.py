"""프로젝트 공통 설정: 경로, 네임스페이스, 환경변수.

로컬에서는 .env, Colab에서는 Colab Secrets(userdata)를 사용한다.
"""
from __future__ import annotations

import os
from pathlib import Path

from rdflib import Namespace

# --- 경로 ---------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
RAW_KIPRIS = DATA / "raw" / "kipris"
RAW_BQ = DATA / "raw" / "bigquery"
INTERIM = DATA / "interim"
PROCESSED = DATA / "processed"
SAMPLES = DATA / "samples"
EXTERNAL_SDKB = DATA / "external" / "sdkb"   # 근간 온톨로지 스냅샷 (vendor.py 가 채운다)
QUERIES_CQ = ROOT / "queries" / "cq"
QUERIES_SHAPES = ROOT / "queries" / "shapes"
# L1 은 두 겹이다. 그래프 전체(레거시 SIRP 포함)에는 완화 제약, 이 논문이 병합하는 델타에는
# 개념 매핑(Process ∪ Device) ≥1 을 요구하는 엄격 제약. 게이트는 델타를 검증하는 것이지
# 상류가 남긴 데이터를 소급 처벌하는 것이 아니다.
SHAPES_GRAPH = QUERIES_SHAPES / "graph"
SHAPES_DELTA = QUERIES_SHAPES / "delta"
MAPPINGS = ROOT / "mappings"
IPC_MAPPING = MAPPINGS / "ipc_to_process.csv"   # IPC/CPC 접두어 -> SDKB 공정 IRI
FIGURES = ROOT / "paper" / "figures"

# vendoring 원본. 스냅샷을 갱신할 때만 쓰인다 — 분석/게이트는 EXTERNAL_SDKB 만 본다.
SDKB_HOME = Path(os.environ.get("SDKB_HOME", Path.home() / "Dev" / "sdkb"))

# baseline: 보강 전 그래프 (H1 의 "before")
GRAPH_V0 = PROCESSED / "graph_v0.ttl"

# --- 온톨로지 네임스페이스 ------------------------------------------------
# SDKB v1.0 실물과 일치 (semiconductor-knowledge-base). slash 네임스페이스 3분리:
#   ont:  TBox 어휘        ont:Patent, ont:Process, ont:realizesProcess …
#   data: ABox 인스턴스    data:subprocess/plasma_etch …
#   gov:  거버넌스 모듈    (이 논문에서는 사용하지 않음)
SDKB = Namespace("https://w3id.org/sdkb/")
ONT = Namespace("https://w3id.org/sdkb/ont/")
SDKB_DATA = Namespace("https://w3id.org/sdkb/data/")
GOV = Namespace("https://w3id.org/sdkb/gov/")

# 이 논문이 KIPRIS 에서 새로 만들어 넣는 특허 인스턴스의 IRI 접두어.
# TBox 는 SDKB 것을 그대로 쓰되(ont:Patent / ont:realizesProcess), 인스턴스는
# SDKB 의 data: 공간에 특허 서브트리를 새로 판다 — 상류 병합 시 충돌하지 않는다.
PATENT_NS = Namespace("https://w3id.org/sdkb/data/patent/")

# 네임스페이스 바인딩 헬퍼 (직렬화 시 prefix 를 SDKB 와 동일하게 유지)
NAMESPACES = {
    "sdkb": SDKB, "ont": ONT, "data": SDKB_DATA, "gov": GOV, "pat": PATENT_NS,
}


def bind_namespaces(g) -> None:
    """rdflib Graph 에 SDKB 표준 prefix 를 바인딩한다."""
    for prefix, ns in NAMESPACES.items():
        g.bind(prefix, ns)


def get_secret(name: str) -> str:
    """환경변수 → .env → Colab Secrets 순으로 시크릿을 찾는다."""
    val = os.environ.get(name)
    if val:
        return val
    try:  # .env (로컬)
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
        val = os.environ.get(name)
        if val:
            return val
    except ImportError:
        pass
    try:  # Colab Secrets
        from google.colab import userdata  # type: ignore

        return userdata.get(name)
    except ImportError:
        pass
    raise KeyError(f"secret '{name}' not found in env, .env, or Colab secrets")
