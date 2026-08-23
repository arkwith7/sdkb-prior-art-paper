"""개념·공리 계기판 — 선언 · 실체화 · 작동 세 층을 한 페이지로 잰다 (2026-08-23 신설).

**왜 필요한가.** CLAUDE.md §0 은 *"온톨로지가 태스크를 표현한다"* 를 **선언 · 실체화 · 작동**
세 층으로 갈라 놓았지만, 그 세 층을 **함께 재는 산출물이 없었다.** 공리는 TTL 을 직접 훑어야
나오고, 실체화는 상류 리포트 안에 있고, 해소력은 코퍼스에서 세야 한다. 그래서 CR 을 열 때마다
같은 측정을 처음부터 다시 했고, *"공리 구현이 진척되고 있는가"* 라는 질문에 답할 자리가 없었다.
이 모듈이 그 자리다.

**무엇을 재고 무엇을 재지 않는가.** 재는 대상은 **동결 벤더 스냅샷**(`data/external/sdkb/`)과
**하류 코퍼스·점수식**이다 — 즉 *"논문이 실제로 소비하는 것"* 이지 상류 워킹트리가 아니다.
상류가 앞서 있으면 그 차이가 곧 **미도달**이며, 계기판은 그것을 드러내라고 있다(D-07·D-19 계열).

**읽기만 한다.** 코퍼스·qrel·게이트·통계 산출물을 하나도 쓰지 않는다. 봉인 분할을 열지 않는다 —
`claim_features` 는 문서 속성이지 정답이 아니다.

산출: `data/reports/concept_status.md`(사람) · `concept_status.json`(기계 · 다음 실행의 델타 기준).

    make concept-status
"""
from __future__ import annotations

import json
from collections import Counter
import pandas as pd
from rdflib import OWL, RDF, RDFS, Graph, URIRef

from .. import config

ONT = "https://w3id.org/sdkb/ont/"
OUT_MD = config.ROOT / "data" / "reports" / "concept_status.md"
OUT_JSON = config.ROOT / "data" / "reports" / "concept_status.json"

# T-Box 모듈. A-Box 는 여기서 읽지 않는다 — 공리는 T-Box 에만 산다.
# **7파일이다** — CLAUDE.md §0 이 기록한 "T-Box 7파일 1,577 트리플"과 같은 집합이어야
# 계기판의 값이 규약의 값과 대조된다. `*-instances.ttl` 은 A-Box 라 제외한다.
TBOX = ("sdkb-core.ttl", "sdkb-patent.ttl", "sdkb-foresight.ttl",
        "sdkb-commercialization.ttl", "sdkb-governance.ttl", "sdkb-governance-kr.ttl",
        "sdkb-rbv.ttl")

# **추론을 만드는** 공리만 센다. subClassOf·domain·range·label·comment 는 어휘 선언이지
# 공리가 아니다 — 그것들을 세면 계기판이 늘 녹색이 된다(그것이 지금까지의 착시다).
INFERENTIAL = {
    "owl:Restriction": OWL.Restriction,
    "owl:propertyChainAxiom": OWL.propertyChainAxiom,
    "owl:inverseOf": OWL.inverseOf,
    "owl:disjointWith": OWL.disjointWith,
    "owl:equivalentClass": OWL.equivalentClass,
    "owl:equivalentProperty": OWL.equivalentProperty,
    "owl:hasKey": OWL.hasKey,
    "owl:TransitiveProperty": OWL.TransitiveProperty,
    "owl:SymmetricProperty": OWL.SymmetricProperty,
    "owl:FunctionalProperty": OWL.FunctionalProperty,
    "owl:InverseFunctionalProperty": OWL.InverseFunctionalProperty,
    "owl:intersectionOf": OWL.intersectionOf,
    "owl:complementOf": OWL.complementOf,
}

# 선행기술 판단의 중심축 — T-Box 가 "중심축"이라 선언한 자리(`sdkb-patent.ttl:507`).
# **이 항목들이 추론 공리를 갖는가**가 이 계기판의 첫 질문이다.
AXIS_TERMS = ("Claim", "ClaimFeature", "PriorArtJudgment", "hasClaim", "hasFeature",
              "isIndependent", "dependsOnClaim", "dependsOnFeature", "featureConcept",
              "hasJudgment", "aboutClaim", "overPriorArt", "onGround", "overlappingFeature",
              "hasPriorArt", "hasPriorArtExaminer")

# 개념 노드의 출처 가운데 **특허·거절 원천**으로 셀 것. 하나라도 잡히면 계기판이 그것을 센다.
PATENT_SOURCE_HINTS = ("kipris", "rejection", "opinion", "sirp", "patent", "claim", "거절")


def _tbox_graph() -> tuple[Graph, dict[str, int]]:
    """T-Box 모듈을 한 그래프로 읽는다. 없는 파일은 건너뛰되 그 사실을 남긴다."""
    g = Graph()
    per_file: dict[str, int] = {}
    for name in TBOX:
        p = config.EXTERNAL_SDKB / name
        if not p.exists():
            per_file[name] = -1        # -1 = 스냅샷에 없음(있음/0 과 구별한다)
            continue
        before = len(g)
        g.parse(p, format="turtle")
        per_file[name] = len(g) - before
    return g, per_file


def declared(g: Graph, per_file: dict[str, int]) -> dict:
    """① 선언 층 — 어휘와 **추론 공리**를 갈라 센다."""
    axioms = {}
    for label, term in INFERENTIAL.items():
        if label in ("owl:TransitiveProperty", "owl:SymmetricProperty",
                     "owl:FunctionalProperty", "owl:InverseFunctionalProperty"):
            axioms[label] = sum(1 for _ in g.subjects(RDF.type, term))
        else:
            axioms[label] = sum(1 for _ in g.triples((None, term, None)))
    # SWRL 은 별도 이름공간이라 술어로 세지 않고 접두사 등장으로 센다.
    axioms["swrl:rule"] = sum(1 for s, p, o in g
                              if "swrl" in str(p).lower() or "swrl" in str(o).lower())

    axis = {}
    for name in AXIS_TERMS:
        u = URIRef(ONT + name)
        held = sorted({label for label, term in INFERENTIAL.items()
                       if (u, term, None) in g or (term is not None and (u, RDF.type, term) in g)})
        # 어휘 선언은 따로 — 공리가 없다는 것과 정의가 없다는 것은 다르다.
        declared_here = (u, RDF.type, None) in g
        axis[name] = {"declared": declared_here, "inferential_axioms": held}

    return {
        "tbox_files": per_file,
        "triples": len(g),
        "classes": sum(1 for _ in g.subjects(RDF.type, OWL.Class)),
        "object_properties": sum(1 for _ in g.subjects(RDF.type, OWL.ObjectProperty)),
        "datatype_properties": sum(1 for _ in g.subjects(RDF.type, OWL.DatatypeProperty)),
        "subclass_axioms": sum(1 for _ in g.triples((None, RDFS.subClassOf, None))),
        "inferential_axioms": axioms,
        "inferential_total": sum(axioms.values()),
        "prior_art_axis": axis,
        "prior_art_axis_with_axioms": sum(
            1 for v in axis.values() if v["inferential_axioms"]),
    }


def instantiated() -> dict:
    """② 실체화 층 — 개념이 어디서 왔고, 한정요소에 얼마나 붙었는가."""
    out: dict = {}

    kg_path = config.EXTERNAL_SDKB / "semiconductor_v0_3.json"
    if kg_path.exists():
        kg = json.loads(kg_path.read_text(encoding="utf-8"))
        src = Counter(str((n.get("provenance") or {}).get("source")) for n in kg["nodes"])
        # **출처 블록만** 본다. 노드 전체를 훑으면 `lexicon_profile: patent-text`(CR-007)
        # 같은 프로파일 표기가 "특허 유래"로 잡혀 13건이 거짓 양성이 된다 — 실측으로 확인했다.
        blob = {n["id"]: json.dumps(n.get("provenance") or {}, ensure_ascii=False).lower()
                for n in kg["nodes"]}
        from_patent = sorted(nid for nid, b in blob.items()
                             if any(h in b for h in PATENT_SOURCE_HINTS))
        out["concepts"] = {
            "nodes": len(kg["nodes"]),
            "axes": dict(Counter(n["type"] for n in kg["nodes"]).most_common()),
            "provenance_sources": dict(src.most_common()),
            "from_patent_or_rejection": len(from_patent),
            "from_patent_or_rejection_ids": from_patent[:20],
            "synonyms": len(kg.get("synonyms", [])),
            "synonyms_by_lang": dict(
                Counter(str(s.get("lang")) for s in kg.get("synonyms", [])).most_common()),
        }

    cm_path = config.SDKB_CONCEPT_MAP
    if cm_path.exists():
        cm = json.loads(cm_path.read_text(encoding="utf-8"))
        prof = cm["profiles"]["patent-text"]
        ko = {e["surface"] for e in prof["entries"]
              if any("가" <= ch <= "힣" for ch in e["surface"])}
        out["dictionary"] = {
            "schema_version": cm.get("schema_version"),
            "surfaces": len({e["surface"] for e in prof["entries"]}),
            "surfaces_hangul": len(ko),
            "surfaces_lang_ko": len({e["surface"] for e in prof["entries"]
                                     if e["lang"] == "ko"}),
            "concepts_covered": len({e["concept_id"] for e in prof["entries"]}),
            "blocked_by_rule": dict(
                Counter(b["rule_id"] for b in prof["blocked"]).most_common()),
        }

    cf_path = config.EXTERNAL_SDKB / "claim_features.parquet"
    if cf_path.exists():
        cf = pd.read_parquet(cf_path, columns=["feature_concept", "is_independent"])
        n = len(cf)
        has = cf["feature_concept"].apply(lambda v: bool(len(v)) if v is not None else False)
        ind = cf["is_independent"].astype(bool)
        distinct = set()
        for v in cf["feature_concept"]:
            if v is not None:
                distinct.update(str(x) for x in v)
        out["claim_features"] = {
            "features": int(n),
            "with_concept": int(has.sum()),
            "concept_zero_pct": round(100.0 * (1 - has.mean()), 2),
            "independent_features": int(ind.sum()),
            "independent_concept_zero_pct": round(
                100.0 * (1 - has[ind].mean()), 2) if int(ind.sum()) else None,
            "distinct_concepts": len(distinct),
        }
    else:
        out["claim_features"] = {"vendored": False}

    # 심사관 판단(PriorArtJudgment)은 사이드카 TTL 에 사는데 그것은 벤더 제외 대상이다.
    # **없다는 사실 자체가 지표다** — 중심축의 하류 전달이 어디서 끊기는지 보여준다(D-07).
    prov = json.loads((config.EXTERNAL_SDKB / "PROVENANCE.json").read_text(encoding="utf-8"))
    vendored = {f["file"] for f in prov.get("files", [])}
    out["judgment_axis_vendored"] = {
        "claim_features_ttl": "sdkb-abox-claim-features.ttl" in vendored,
        "projection_parquet": cf_path.exists(),
        "note": "판단 인스턴스(PriorArtJudgment)는 사이드카 TTL 에만 있고 투영 parquet 에는 "
                "한정요소만 담긴다 — 하류는 판단을 직접 셀 수 없다.",
    }
    out["snapshot"] = {"source_commit": prov.get("source_commit"),
                       "vendored_at": prov.get("vendored_at")}
    return out


def operative() -> dict:
    """③ 작동 층 — 검색이 실제로 무엇을 쓰는가. 공리가 들어갈 항이 있는가."""
    from ..analysis import results_table as rt
    from ..retrieval.systems import OntoConfig

    out: dict = {}
    if config.IR_CORPUS.exists():
        df = pd.read_parquet(config.IR_CORPUS, columns=["doc_id", "concepts"])
        sizes = df["concepts"].apply(lambda v: len(v) if v is not None else 0)
        seen: Counter = Counter()
        for v in df["concepts"]:
            for c in (v if v is not None else []):
                seen[str(c)] += 1
        out["corpus"] = {
            "docs": int(len(df)),
            "concepts_per_doc_mean": round(float(sizes.mean()), 3),
            "docs_with_zero_concepts": int((sizes == 0).sum()),
            "distinct_concepts_in_corpus": len(seen),
            "top_concepts": [[k.rsplit("/", 1)[-1], v] for k, v in seen.most_common(10)],
        }

    cfg = OntoConfig()
    wc, wh, wi, wf = rt.P1_W4
    out["scoring"] = {
        "P0_star": {"alpha": cfg.alpha, "w_concept": cfg.w_c, "w_path": cfg.w_h,
                    "w_ipc": cfg.w_i},
        "P1": {"tau": rt.P1_TAU, "alpha": rt.P1_ALPHA, "w_concept": wc, "w_path": wh,
               "w_ipc": wi, "w_feature_coverage": wf},
        # 계기판의 핵심 한 줄 — 공리에서 유도된 항은 **식에 존재하지 않는다.**
        "axiom_derived_terms": 0,
        "note": "FeatureCoverage 는 한정요소 원문의 임베딩 코사인이고 IPC 는 분류코드다. "
                "온톨로지 고유 항은 개념 Jaccard 하나이며 df 무가중이다.",
    }
    return out


def collect() -> dict:
    g, per_file = _tbox_graph()
    return {"declared": declared(g, per_file),
            "instantiated": instantiated(),
            "operative": operative()}


def _delta(cur: float | int | None, prev: float | int | None) -> str:
    if prev is None or cur is None or cur == prev:
        return ""
    d = cur - prev
    return f" ({'+' if d > 0 else ''}{d:g})"


def render(cur: dict, prev: dict | None) -> str:
    p = prev or {}
    d, i, o = cur["declared"], cur["instantiated"], cur["operative"]
    pd_, pi, po = p.get("declared", {}), p.get("instantiated", {}), p.get("operative", {})
    L = []
    add = L.append

    add("# 개념·공리 계기판 — 선언 · 실체화 · 작동\n")
    add("> 생성: `make concept-status`. **손으로 고치지 않는다**(CLAUDE.md §1-1·§1-7).")
    add("> 재는 대상은 **동결 벤더 스냅샷과 하류 코퍼스·점수식** — 즉 논문이 실제로 소비하는")
    add("> 것이다. 상류가 앞서 있으면 그 차이가 곧 **미도달**이며, 그것을 드러내는 것이 이 표의")
    add("> 목적이다. 괄호 안은 직전 실행 대비 델타다.\n")
    snap = i.get("snapshot", {})
    add(f"스냅샷 `{str(snap.get('source_commit'))[:12]}` · 벤더 시각 {snap.get('vendored_at')}\n")

    add("## ① 선언 — 어휘는 있는가, **추론 공리**는 있는가\n")
    add("| | 값 |")
    add("|---|---:|")
    add(f"| T-Box 트리플 | {d['triples']:,}{_delta(d['triples'], pd_.get('triples'))} |")
    add(f"| 클래스 | {d['classes']}{_delta(d['classes'], pd_.get('classes'))} |")
    add(f"| ObjectProperty / DatatypeProperty | {d['object_properties']} / "
        f"{d['datatype_properties']} |")
    add(f"| `rdfs:subClassOf` (어휘 선언) | {d['subclass_axioms']} |")
    add(f"| **추론 공리 합계** | **{d['inferential_total']}"
        f"{_delta(d['inferential_total'], pd_.get('inferential_total'))}** |")
    add("")
    add("추론 공리 내역 — `subClassOf`·`domain`·`range` 는 어휘 선언이므로 세지 않는다.\n")
    add("| 공리 | 수 |")
    add("|---|---:|")
    for k, v in d["inferential_axioms"].items():
        prev_v = (pd_.get("inferential_axioms") or {}).get(k)
        add(f"| `{k}` | {v}{_delta(v, prev_v)} |")
    add("")
    n_axis = len(d["prior_art_axis"])
    add(f"**선행기술 판단 중심축 {n_axis}항 가운데 추론 공리를 가진 것: "
        f"{d['prior_art_axis_with_axioms']} / {n_axis}"
        f"{_delta(d['prior_art_axis_with_axioms'], pd_.get('prior_art_axis_with_axioms'))}**\n")
    add("| 항목 | 어휘 선언 | 추론 공리 |")
    add("|---|:--:|---|")
    for name, v in d["prior_art_axis"].items():
        ax = ", ".join(f"`{a}`" for a in v["inferential_axioms"]) or "**없음**"
        add(f"| `ont:{name}` | {'있음' if v['declared'] else '없음'} | {ax} |")
    add("")

    add("## ② 실체화 — 개념은 어디서 왔고, 한정요소에 얼마나 붙었는가\n")
    c = i.get("concepts", {})
    if c:
        pc = pi.get("concepts", {})
        add("| | 값 |")
        add("|---|---:|")
        add(f"| 개념 노드 | {c['nodes']}{_delta(c['nodes'], pc.get('nodes'))} |")
        add(f"| **특허·거절 원천에서 유도된 개념** | **{c['from_patent_or_rejection']}"
            f"{_delta(c['from_patent_or_rejection'], pc.get('from_patent_or_rejection'))}** |")
        add(f"| 동의어 (ko / 전체) | {c['synonyms_by_lang'].get('ko', 0)} / {c['synonyms']} |")
        add("")
        add("개념 출처 분포 — " + " · ".join(
            f"{k} {v}" for k, v in c["provenance_sources"].items()) + "\n")
    dic = i.get("dictionary", {})
    if dic:
        pdic = pi.get("dictionary", {})
        add("| 표면형 사전 (`patent-text`) | 값 |")
        add("|---|---:|")
        add(f"| 표면형 | {dic['surfaces']}{_delta(dic['surfaces'], pdic.get('surfaces'))} |")
        add(f"| 한글 표면형 / `lang=ko` | {dic['surfaces_hangul']} / {dic['surfaces_lang_ko']} |")
        add(f"| 표면형을 가진 개념 | {dic['concepts_covered']} |")
        add("| 차단 | " + (", ".join(f"{k} {v}" for k, v in dic["blocked_by_rule"].items())
                           or "0") + " |")
        add("")
    cf = i.get("claim_features", {})
    if cf.get("features"):
        pcf = pi.get("claim_features", {})
        add("| 한정요소 (중심축 투영) | 값 |")
        add("|---|---:|")
        add(f"| 한정요소 | {cf['features']:,} |")
        add(f"| 개념이 붙은 것 | {cf['with_concept']:,} |")
        add(f"| **개념 0개 비율** | **{cf['concept_zero_pct']} %"
            f"{_delta(cf['concept_zero_pct'], pcf.get('concept_zero_pct'))}** |")
        add(f"| 독립항 한정요소 개념 0개 비율 | {cf['independent_concept_zero_pct']} %"
            f"{_delta(cf['independent_concept_zero_pct'], pcf.get('independent_concept_zero_pct'))} |")
        add(f"| 등장한 고유 개념 | {cf['distinct_concepts']} / {c.get('nodes', '—')} |")
        add("")
    ja = i.get("judgment_axis_vendored", {})
    add(f"판단 축 전달 — 사이드카 TTL 벤더 {'예' if ja.get('claim_features_ttl') else '**아니오**'} · "
        f"투영 parquet {'도착' if ja.get('projection_parquet') else '**미도착**'}. {ja.get('note','')}\n")

    add("## ③ 작동 — 검색이 실제로 무엇을 쓰는가\n")
    co = o.get("corpus", {})
    if co:
        pco = po.get("corpus", {})
        add("| | 값 |")
        add("|---|---:|")
        add(f"| 코퍼스 문서 | {co['docs']:,} |")
        add(f"| 문서당 개념 (평균) | {co['concepts_per_doc_mean']}"
            f"{_delta(co['concepts_per_doc_mean'], pco.get('concepts_per_doc_mean'))} |")
        add(f"| 개념 0개 문서 | {co['docs_with_zero_concepts']:,} |")
        add(f"| 코퍼스에 등장한 고유 개념 | {co['distinct_concepts_in_corpus']}"
            f"{_delta(co['distinct_concepts_in_corpus'], pco.get('distinct_concepts_in_corpus'))} |")
        add("")
    sc = o["scoring"]
    p1 = sc["P1"]
    add("| 순위 함수 항 | 가중 |")
    add("|---|---:|")
    add(f"| 개념 Jaccard (온톨로지 고유 · df 무가중) | {p1['w_concept']} |")
    add(f"| 경로(PathSim) | {p1['w_path']} |")
    add(f"| IPC 분류코드 | {p1['w_ipc']} |")
    add(f"| FeatureCoverage (한정요소 원문 임베딩 코사인) | {p1['w_feature_coverage']} |")
    add(f"| **공리에서 유도된 항** | **{sc['axiom_derived_terms']}** |")
    add("")
    add(f"{sc['note']}\n")
    add("---\n")
    add("**읽는 규칙.** 이 표는 진척을 재는 것이지 판정을 바꾸지 않는다(§1-2·§1-3). "
        "원고의 수치·판정은 이 파일과 무관하게 그대로다. 값이 움직였다면 그것은 **새 자원**의 "
        "관측이며, 태스크 효과는 새 사전등록 아래 새로 검정한다(§2.1).")
    return "\n".join(L) + "\n"


def main() -> int:
    cur = collect()
    prev = json.loads(OUT_JSON.read_text(encoding="utf-8")) if OUT_JSON.exists() else None
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(render(cur, prev), encoding="utf-8")
    OUT_JSON.write_text(json.dumps(cur, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    d, i, o = cur["declared"], cur["instantiated"], cur["operative"]
    print(f"✓ {OUT_MD.relative_to(config.ROOT)}")
    print(f"  선언   추론 공리 {d['inferential_total']} · 중심축 공리 보유 "
          f"{d['prior_art_axis_with_axioms']}/{len(d['prior_art_axis'])}")
    print(f"  실체화 개념 {i['concepts']['nodes']}(특허·거절 유래 "
          f"{i['concepts']['from_patent_or_rejection']}) · 한정요소 개념 0개 "
          f"{i['claim_features'].get('concept_zero_pct')} %")
    print(f"  작동   고유 개념 {o['corpus']['distinct_concepts_in_corpus']} · "
          f"공리 유도 항 {o['scoring']['axiom_derived_terms']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
