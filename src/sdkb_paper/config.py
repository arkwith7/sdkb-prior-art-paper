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

# --- IR 벤치마크 코퍼스 (v0.9 · PLAN-017 M1) ------------------------------
# 통합 문서 코퍼스와 심사관 qrel. 특허 전문(abstract/claim)을 담으므로 license_restricted →
# data/processed/* 는 gitignore, `make corpus` 로 로컬 재생성한다(CLAUDE.md §1.4·§1.5).
# 커밋되는 것은 프로파일(집계·서명)과 MANIFEST 뿐. 청구항 본문 = sidecar featureText 재구성이
# 정본, firstClaimText(원문 claim1) 병기 (PLAN-017 §7 M1 확정).
IR_DIR = PROCESSED / "ir"
IR_CORPUS = IR_DIR / "ir_corpus_v09.parquet"          # 통합 문서 코퍼스
QREL_EXAMINER = IR_DIR / "qrel_examiner.parquet"      # 심사관 인용 qrel (등급1)
IR_PROFILE = DATA / "profiles" / "ir_corpus_v09.md"   # §4 데이터 프로파일 (커밋 가능)

# --- IR 검색 하네스 (v0.9 · PLAN-018 계층 B) ------------------------------
# 색인·순위·산출물 경로. index/run 은 대용량·재생성 가능 → gitignore.
IR_INDEX_DIR = IR_DIR / "index"                        # Lucene(BM25) · FAISS 색인
IR_RUNS_DIR = IR_DIR / "runs"                          # 시스템별 순위 산출(run 파일)
IR_USERDICT = IR_DIR / "userdict_sdkb.txt"             # nori 사용자사전 (SDKB 어휘 시드 · F13)
# 개념→축(axis)·TBox 계층 지도 (M4 온톨로지팔 입력 · PLAN-018 §7.3 M4-3/M4-4). 벤더 TTL 의
# `a ont:X`·subClassOf 에서 결정적 추출 — 커밋 가능(집계·식별자·해시만). concept_axis.py 생성.
IR_CONCEPT_AXIS = IR_DIR / "concept_axis.parquet"
# claim-feature sidecar (P1/P2 · PLAN-018 §7.5). central_axis.oxstore 에서 추출한 특허별 청구항 피처
# (doc_id·claim·is_independent·featureText·seq). **featureText=KIPRIS 원문 → gitignore·재생성**.
IR_FEATURE_SIDECAR = IR_DIR / "feature_sidecar.parquet"
# featureText Titan 임베딩 캐시(P1 FeatureCoverage). 텍스트해시→벡터 sqlite · gitignore.
IR_FEATURE_EMB_CACHE = IR_INDEX_DIR / "feature_titan_cache.sqlite"
# DOCDB family_id 지도 (B2 · F1 family-level 주지표). doc_id→family_id, raw(비커밋).
# 원천은 BigQuery patents-public-data — 공개번호/출원번호 조인. 미조인은 fallback=자기자신(비율 보고).
IR_FAMILY_MAP = RAW_BQ / "ir_family_map.parquet"
# Dense(B2 · F12 Titan Embed v2). 임베딩 캐시(텍스트해시→벡터)·FAISS flat 색인 · gitignore.
IR_DENSE_CACHE = IR_INDEX_DIR / "dense_titan_cache.sqlite"
IR_DENSE_DIM = 1024                                    # Titan v2 지원 256/512/1024 중 최대(동결)
# 거절근거 법조 라벨 (원고 §5.2·§6.4 하위집단 **전용** · 순위 입력 아님). vendor.py 가 상류
# rejected_patents_meta 에서 식별자+법조만 파생해 얼린다 — 원문 0열이라 커밋 가능.
# TTL 스냅샷은 §1×n|§2×m 을 Rejection_Inventiveness 하나로 접어 신규성 축을 잃는다(상류 결함).
REJECTION_BASIS = EXTERNAL_SDKB / "rejection_basis.csv"
# F11 어휘중첩 동결 임계(원고 §5.3). dev Q1 을 low-overlap 경계로 얼린 기록 — analysis/overlap.py.
IR_OVERLAP_THRESHOLD = IR_DIR / "overlap_threshold.json"
# 결정성 시드 (F16 사전등록): 분할·부트스트랩·hard-neg 샘플링 전역 시드.
SEED = 20260726

# 시점 분할 산출물(B8). doc_id→split(train/dev/test) · family-disjoint. gitignore(파생·재생성).
IR_SPLIT = IR_DIR / "split.parquet"
# 봉인된 test qrel(F9 사전등록). 최종 비교 전까지 열지 않는다 — 개발은 dev 로만.
IR_QREL_TEST_SEALED = IR_DIR / "qrel_test_sealed.parquet"
# ── F9 사전등록 동결 (2026-07-27 · 데이터감사 후 확정 · 테스트 개봉 전) 🔒 ──────────────
# 질의(거절특허 1,000)를 filingDate 순 60/20/20 로 나누되 **family 단위**(family-disjoint)로 배정한다.
# family 대표일 = 그 family 질의들의 최소 출원일 · 동률은 family_id 사전순(결정적). 경계는 데이터
# 감사 결과이지 자의 선택이 아니다(정확히 600/200/200 로 떨어졌다). CLAUDE 규칙 #3: 결과 보고 불변.
F9_SPLIT_FRACTIONS = (0.60, 0.20, 0.20)                       # train / dev / test
F9_BOUNDARY_TRAIN_DEV = "2016-11-21"                          # train ≤ 경계 < dev
F9_BOUNDARY_DEV_TEST = "2021-07-21"                           # dev ≤ 경계 < test


def java_home() -> str:
    """pyserini(JVM) 부팅용 JAVA_HOME 을 확정한다 (PLAN-018 E1).

    장비에 JRE 만 있고 javac(JDK) 가 없으면 pyjnius 자동탐지가 실패한다. 환경변수
    JAVA_HOME 이 있으면 존중하고, 없으면 libjvm.so 를 담은 표준 경로를 탐지해 설정한다.
    하드코딩이 아니라 탐지 — 실패 시 명시적 예외로 사용자에게 알린다(CLAUDE §1.9 정신).
    """
    env = os.environ.get("JAVA_HOME")
    if env and (Path(env) / "lib" / "server" / "libjvm.so").exists():
        return env
    for cand in (
        "/usr/lib/jvm/java-21-openjdk-amd64",
        "/usr/lib/jvm/default-java",
    ):
        if (Path(cand) / "lib" / "server" / "libjvm.so").exists():
            os.environ["JAVA_HOME"] = cand
            return cand
    raise RuntimeError(
        "JAVA_HOME 미확정: libjvm.so 를 담은 JDK/JRE 경로를 찾지 못했다. "
        "JAVA_HOME 환경변수를 명시하라 (PLAN-018 §9 E1)."
    )

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
