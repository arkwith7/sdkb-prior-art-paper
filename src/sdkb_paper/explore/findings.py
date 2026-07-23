"""구축현황 서명 + 논문 주요 발견의 라이브 재현.

여기의 모든 수치는 상주 그래프에 대한 **실시간 SPARQL** 로 계산된다 — 하드코딩이 아니다.
그래서 이 패널은 "논문 §6 의 숫자가 실제 그래프에서 재현된다"는 증거를 겸한다.
논문 정본 대비 검산용 기대값은 EXPECTED 에 둔다(어긋나면 대시보드가 경고).
"""
from __future__ import annotations

from sdkb_paper.explore.store import load, run_query, scalar

ONT = "PREFIX ont: <https://w3id.org/sdkb/ont/>\n"
SKOS = "PREFIX skos: <http://www.w3.org/2004/02/skos/core#>\n"

# 논문 정본(v0.5) 서명 — G₀ 만 불변식으로 검사한다. 나머지는 참고.
EXPECTED = {
    "v0": {"triples": 49307, "steps": 49, "covered": 20, "patent": 1000, "device": 34},
}

_COUNTS = {
    "process": ONT + "SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s a ont:Process }",
    "subprocess": ONT + "SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s a ont:SubProcess }",
    "device": ONT + "SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s a ont:Device }",
    "patent": ONT + "SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s a ont:Patent }",
    "organization": ONT + "SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s a ont:Organization }",
    "expert": ONT + "SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { ?s a ont:Expert }",
}

# 단계(Process ∪ SubProcess) 중 특허가 realizesProcess 로 직접 붙은 것 = 커버.
_COVERED = ONT + """
SELECT (COUNT(DISTINCT ?step) AS ?n) WHERE {
  VALUES ?t { ont:Process ont:SubProcess }
  ?step a ?t .
  ?p a ont:Patent ; ont:realizesProcess ?step .
}"""

_STEP_LIST = ONT + SKOS + """
SELECT ?level ?label (COUNT(DISTINCT ?p) AS ?n) WHERE {
  VALUES (?t ?level) { (ont:Process "process") (ont:SubProcess "subprocess") }
  ?step a ?t ; skos:prefLabel ?label .
  OPTIONAL { ?p a ont:Patent ; ont:realizesProcess ?step . }
} GROUP BY ?level ?label ORDER BY DESC(?n) ?label"""


def signature(key: str) -> dict:
    """대시보드 카드용 그래프 서명. G₀ 는 정본과 대조해 drift 를 표시한다."""
    store = load(key)
    counts = {name: scalar(key, q) for name, q in _COUNTS.items()}
    steps = counts["process"] + counts["subprocess"]
    covered = scalar(key, _COVERED)
    sig = {
        "triples": len(store),
        "steps": steps,
        "process": counts["process"],
        "subprocess": counts["subprocess"],
        "covered": covered,
        "gap": steps - covered,
        "device": counts["device"],
        "patent": counts["patent"],
        "organization": counts["organization"],
        "expert": counts["expert"],
    }
    exp = EXPECTED.get(key)
    if exp:
        drift = {k: {"got": sig[k], "expected": v} for k, v in exp.items() if sig.get(k) != v}
        sig["drift"] = drift  # 비어 있으면 정본과 일치
    return sig


def coverage_steps(key: str) -> dict:
    """공정 단계별 커버 특허수 — H1 커버리지 패널의 before/after 막대 원천."""
    res = run_query(key, _STEP_LIST)
    steps = [
        {
            "level": r[0]["value"] if r[0] else "",
            "label": r[1]["value"] if r[1] else "",
            "patents": int(r[2]["value"]) if r[2] else 0,
        }
        for r in res.rows
    ]
    covered = sum(1 for s in steps if s["patents"] > 0)
    return {"total": len(steps), "covered": covered, "gap": len(steps) - covered, "steps": steps}


def _cq_rows(key: str, cq_text: str) -> int:
    return len(run_query(key, cq_text).rows)


def findings() -> dict:
    """논문 핵심 발견 3축을 세 그래프에서 라이브로 재현한다.

    - H1 공정 커버리지 (§6.3): 커버 단계 20 → 26 …
    - RQ2 선행기술 후보 (§5.3, CQ10): 8 → 90 (11.3배)
    - FTO 청구항 준비 (§6.6, CQ27): G₂ 에만 실체화
    """
    from sdkb_paper.config import QUERIES_CQ

    cq10 = (QUERIES_CQ / "CQ10_prior_art_candidates_by_concept.rq").read_text(encoding="utf-8")
    cq27 = (QUERIES_CQ / "CQ27_fto_claim_readiness.rq").read_text(encoding="utf-8")

    axes = {}
    for key in ("v0", "v1", "v2"):
        try:
            load(key)
        except FileNotFoundError:
            continue
        cov = coverage_steps(key)
        axes[key] = {
            "coverage_covered": cov["covered"],
            "coverage_total": cov["total"],
            "prior_art_cq10": _cq_rows(key, cq10),
            "fto_cq27_rows": _cq_rows(key, cq27),
        }
    return {
        "axes": axes,
        "claims": {
            "h1": "커버 단계: G₀ 20 → G₁ 26 (§6.3, Wilcoxon p=4.77e-07)",
            "rq2": "선행기술 후보(CQ10): G₀ 8 → G₁ 90, 11.3배 (§5.3 RQ2 직접 증거)",
            "fto": "FTO 청구항(CQ27): 청구항은 G₂ 에만 실체화 — 배터리가 코퍼스를 판별",
        },
    }
