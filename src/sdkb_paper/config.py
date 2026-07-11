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
QUERIES_CQ = ROOT / "queries" / "cq"
QUERIES_SHAPES = ROOT / "queries" / "shapes"
FIGURES = ROOT / "paper" / "figures"

# --- 온톨로지 네임스페이스 ------------------------------------------------
# TODO: 실제 SDKB 네임스페이스 IRI 로 교체 (기존 semiconductor-knowledge-base 와 일치시킬 것)
SDKB = Namespace("https://w3id.org/sdkb#")


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
