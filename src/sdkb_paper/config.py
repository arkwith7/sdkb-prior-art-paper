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
# IPC/CPC 접두어 -> SDKB 개념 IRI. 개념 축은 Process ∪ Device 이므로 공정 전용이 아니다 —
# axis 컬럼이 realizesProcess 와 concernsDevice 를 가른다.
CODE_MAPPING = MAPPINGS / "code_to_concept.csv"
# 신기술 인식 레이어 (PLAN-004). 신기술은 코드로도 이름으로도 잡히지 않는다 — GAA 전용 코드는
# 부여 0건이고, HBM 은 조합으로 잡히는 특허의 대다수가 명세에 이름을 쓰지 않는다.
# 두 파일은 **시계열을 보기 전에 동결**됐다 (외부 원천 = JEDEC · CPC 공식 스킴 원문).
TERM_ALIASES = MAPPINGS / "term_aliases.csv"          # 1층 · 별칭
EMERGING_CONCEPTS = MAPPINGS / "emerging_concepts.csv"  # 2층 · 조합 정의 (strict/base/loose)
SI_CONCEPTS = MAPPINGS / "si_concepts.csv"            # 분류체계 독립 정의 (PLAN-009 · 텍스트 전용)
DART_TERMS = MAPPINGS / "dart_terms.csv"     # DART 준거 용어 (PLAN-009 · 동결)
# H2′ 의 대조군: 기술의 **명칭** 키워드 (PLAN-010 · 동결). 명세 텍스트는 소급 재작성되지
# 않으므로 이 대조군은 **시점 유효**하다 — 분류코드가 무효였던 이유를 피해 간다.
NAME_BASELINE = MAPPINGS / "name_baseline.csv"
# H2 의 검증 사례 7건 (PLAN-006). 개념 시계열과 대조할 CPC 코드가 사례마다 하나씩 고정돼 있다.
# **시계열을 보기 전에 동결**됐다 — 사례 선정은 우리 데이터 분포가 아니라 SDKB 어휘 · CPC 공식
# 스킴 원문 · 외부 부상 근거(JEDEC 표준 · 양산 발표)만으로 이루어졌다. 커밋 해시가 사전등록이다.
H2_CASES = MAPPINGS / "h2_cases.csv"
# H1 의 두 번째 표본 집합: SemiKong Table 7 복원 **이전**의 공정 20개.
# 복원된 단계는 G₀ 에서 C₀(s)=0 이라 H1 에 유리하다 — 그 편향을 독자가 판별할 수 있도록
# 확장 49 와 병기 보고한다 (scripts/freeze_legacy_scope.py 가 커밋 스냅샷에서 생성).
LEGACY_SCOPE = MAPPINGS / "process_scope_legacy20.csv"
# C-2 소부장 G₂ (RQ3): KSIA 장비 94사 → 기존 G₀ organization 노드 크로스워크.
# 사전동결 CSV — 결과를 보기 전에 확정했다(h2_cases.csv 와 같은 규율). match_key 는 KIPRIS
# applicantName 정확일치 필터의 키다(clean.normalize_company_name 로 생성). 94사 전량이 기존
# G₀ 노드에 매핑되므로 신규 organization 노드는 만들지 않는다 — 정체성 재분열이 없다.
KSIA_CROSSWALK = MAPPINGS / "ksia_applicant_crosswalk.csv"
FIGURES = ROOT / "paper" / "figures"
TABLES = ROOT / "paper" / "tables"

# vendoring 원본. 스냅샷을 갱신할 때만 쓰인다 — 분석/게이트는 EXTERNAL_SDKB 만 본다.
SDKB_HOME = Path(os.environ.get("SDKB_HOME", Path.home() / "Dev" / "sdkb"))

# baseline: 보강 전 그래프 (H1 의 "before")
GRAPH_V0 = PROCESSED / "graph_v0.ttl"
# 보강 후 그래프 — 읽기 전용 소비자(explore 등)만 참조한다. 조립은 merge 가 한다.
GRAPH_V1 = PROCESSED / "graph_v1.ttl"  # G₁ 삼성·SK하이닉스 보강 후
GRAPH_V2 = PROCESSED / "graph_v2.ttl"  # G₂ KSIA 소부장 188사 보강 후

# 청구항 분해 중심축 데이터셋 (11.6M 트리플). 분석 그래프에 **병합하지 않는다** — H1 엣지
# 중립이고, rdflib 인메모리로 올리면 피크 15GB·4분이라 OOM 위험이다(실측 2026-07-23).
# pyoxigraph 온디스크 스토어로만 적재/질의한다. 소스는 상류 SDKB, 스토어는 여기서 결정적 재빌드.
CENTRAL_AXIS_SRC = SDKB_HOME / "ontology" / "sdkb-abox-claim-features.ttl"  # ABox 887MB
CENTRAL_AXIS_TBOX = SDKB_HOME / "ontology" / "sdkb-patent.ttl"              # 동반 TBox 22KB
CENTRAL_AXIS_STORE = PROCESSED / "central_axis.oxstore"                     # 온디스크 스토어(gitignore)
CENTRAL_AXIS_PROVENANCE = DATA / "external" / "sdkb-central-axis" / "PROVENANCE.json"  # 커밋 가능 핀

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
