"""델타 그래프 생성 — 매핑된 특허만 SDKB 어휘로 트리플화한다 (PLAN-002).

어휘는 전부 SDKB 실물에서 관찰한 것이다. 새 술어·클래스를 만들지 않는다 (CLAUDE.md §1.4).
  pat:kr_<출원번호>  a ont:Patent
    rdfs:label · ont:applicationNumber · ont:filingDate(xsd:date) · ont:publicationDate
    ont:patentOffice · ont:assignedTo(→ 기존 organization) · ont:hasIPC(→ ont:IPCSymbol)
    ont:realizesProcess / ont:concernsDevice   ← 룰 매핑 결과
    dcterms:source · dcterms:license · prov:wasGeneratedBy

두 가지를 넣지 **않는다**:
- **초록 원문.** KIPRIS 는 학술 이용·비재배포 조건이다 (CLAUDE.md §1.3). 텍스트 매칭은
  parquet(로컬)에서 하고, 그래프에는 결과 링크만 남긴다.
- **미매핑 특허.** 개념 링크가 없으면 델타 shape 를 통과할 수 없다. 우회로를 만들지 않고
  프로파일에 미매핑으로 보고한다.
"""
from __future__ import annotations

import pandas as pd
from rdflib import RDF, RDFS, XSD, Graph, Literal, URIRef
from rdflib.namespace import DCTERMS, SKOS

from sdkb_paper.config import ONT, PATENT_NS, PROCESSED, SDKB_DATA, bind_namespaces
from sdkb_paper.ontology.emerging import (
    DEFAULT_VARIANT,
    alias_labels,
    emerging_devices,
    load_aliases,
    load_combinations,
)
from sdkb_paper.ontology.mapping import load_code_mapping, map_codes_to_concepts
from sdkb_paper.preprocess.profile import DELTA as DELTA_PARQUET

PROV = URIRef("http://www.w3.org/ns/prov#")
PROV_ACTIVITY = URIRef("http://www.w3.org/ns/prov#Activity")
WAS_GENERATED_BY = URIRef("http://www.w3.org/ns/prov#wasGeneratedBy")

DELTA_TTL = PROCESSED / "delta_v1.ttl"
GRAPH_V1 = PROCESSED / "graph_v1.ttl"
DELTA_V2_TTL = PROCESSED / "delta_v2.ttl"
GRAPH_V2 = PROCESSED / "graph_v2.ttl"

# G₀ 에 이미 있는 조직 인스턴스를 재사용한다 — 새로 만들면 CQ08(출원인 포트폴리오)이 쪼개진다.
ORG = {
    "삼성전자주식회사": SDKB_DATA["organization/samsung_electronics"],
    "에스케이하이닉스 주식회사": SDKB_DATA["organization/sk_hynix"],
}
ACTIVITY = SDKB_DATA["activity/kipris_plan002_ingest"]
# C-2 소부장 G₂ (RQ3). 출원인은 preprocess 가 붙인 matched_slug(기존 G₀ organization 노드)로
# 해석한다 — 94사 전량이 이미 G₀ 에 있으므로 신규 노드를 만들지 않는다(정체성 재분열 없음).
ACTIVITY_KSIA = SDKB_DATA["activity/kipris_ksia_equipment_ingest"]
SOURCE = "KIPRIS Plus API (getAdvancedSearch)"
LICENSE = "KIPRIS terms — academic use, no redistribution of full text"


def _org_samsung(row) -> URIRef | None:
    return ORG.get(row.applicant_name)


def _org_ksia(row) -> URIRef | None:
    return SDKB_DATA[f"organization/{row.matched_slug}"]


def ipc_iri(code: str) -> URIRef:
    """'H10B 69/00' → data:ipc/H10B_69-00 (SDKB 의 기존 인코딩)."""
    return SDKB_DATA["ipc/" + code.strip().replace(" ", "_").replace("/", "-")]


def build_delta(df: pd.DataFrame, variant: str = DEFAULT_VARIANT,
                org_of=_org_samsung, activity: URIRef = ACTIVITY,
                activity_label: str = "KIPRIS Samsung/SK hynix ingest (PLAN-002)",
                details: dict | None = None) -> Graph:
    """룰 매핑 + 신기술 인식 레이어(PLAN-004)로 델타를 만든다.

    신기술 레이어는 **디바이스 축에만** 링크를 더한다 — 공정 축을 건드리지 않으므로 H1 의
    커버리지 수치는 변하지 않아야 한다(회귀 테스트로 고정).

    org_of 는 특허 행 → 출원인 organization IRI 해석기다. 삼성/하이닉스는 이름 사전으로,
    KSIA 소부장(G₂)은 preprocess 가 붙인 matched_slug 로 기존 G₀ 노드를 가리킨다.
    """
    g = Graph()
    bind_namespaces(g)
    g.add((activity, RDF.type, PROV_ACTIVITY))
    g.add((activity, RDFS.label, Literal(activity_label)))

    table = load_code_mapping()
    aliases = load_aliases(variant=variant)
    combos = load_combinations(variant=variant)

    # 별칭을 그래프에 실체화한다 — SDKB 의 라벨 설계(prefLabel@en 기준 · altLabel@ko 별칭)를
    # 신기술 개념에서도 성립시킨다. gaa_fet 은 altLabel 이 0개였고 hbm 은 영문 하나뿐이었다.
    for iri, term, lang in alias_labels(variant=variant):
        g.add((URIRef(iri), SKOS.altLabel, Literal(term, lang=lang)))

    for row in df.sort_values("application_number").itertuples():
        codes = [c.strip() for c in row.ipc_codes if c.strip()]
        hits = map_codes_to_concepts(codes, table)

        # 1층(별칭) + 2층(조합). 텍스트는 parquet 에만 있고 그래프에는 링크만 남는다 (§1.3).
        text = f"{row.invention_title or ''} {row.abstract or ''}"
        hits["device"] = sorted(set(hits["device"]) | set(emerging_devices(codes, text, aliases, combos)))

        if not (hits["process"] or hits["device"]):
            continue  # 미매핑은 델타에 넣지 않는다 — 게이트를 통과할 수 없다

        p = PATENT_NS[f"kr_{row.application_number}"]
        g.add((p, RDF.type, ONT.Patent))
        # 특허의 이름은 발명의 명칭이고, 인스턴스의 이름은 skos:prefLabel 이다 — rdfs:label 이
        # 아니다 (CLAUDE.md §1.4). 상류 SDKB 도 같은 결함이 있어 함께 고쳤다 (SDKB e0ef011).
        # 이걸 어기면 선행기술 질의가 제목 없이 IRI 만 돌려준다. KIPRIS 원문은 국문이다.
        g.add((p, SKOS.prefLabel, Literal(row.invention_title, lang="ko")))
        g.add((p, ONT.applicationNumber, Literal(row.application_number, datatype=XSD.string)))
        g.add((p, ONT.filingDate, Literal(row.application_date.date().isoformat(), datatype=XSD.date)))
        g.add((p, ONT.patentOffice, Literal("KR")))
        # 출처·라이선스는 dcterms 다. ont:source · ont:license 는 **우리가 발명한 술어**였고
        # (SDKB TBox 에 없다) 그래서 G₁ 의 ont: 술어가 53 → 55 로 부풀어 있었다 — 어휘를
        # 발명하지 않는다 (CLAUDE.md §1.4). 상류 특허 A-Box 도 dcterms 를 쓴다.
        g.add((p, DCTERMS.source, Literal(SOURCE, datatype=XSD.string)))
        g.add((p, DCTERMS.license, Literal(LICENSE, datatype=XSD.string)))
        g.add((p, WAS_GENERATED_BY, activity))

        if row.open_date:
            g.add((p, ONT.publicationDate, Literal(_iso(row.open_date), datatype=XSD.date)))
        org = org_of(row)
        if org is not None:
            g.add((p, ONT.assignedTo, org))

        # IP-R&D FTO 자기완결성: 초록 + 전체 청구항을 실체화한다(§1.3 — 그래프는 gitignore 라
        # 로컬 전용·비재배포). claimText 는 청구항당 1트리플(번호 보존), firstClaimText 는 청구항1.
        det = details.get(row.application_number) if details else None
        if det is not None:
            # 초록·청구항은 **plain 리터럴**(xsd:string)이다 — TBox range 가 xsd:string 이라
            # lang 태그(rdf:langString)를 붙이면 range 위반으로 HermiT 가 비일관 판정한다.
            # G₀ 의 SIRP abstractText/firstClaimText 도 lang 없는 plain 리터럴로 저장돼 있다.
            if det["abstract"]:
                g.add((p, ONT.abstractText, Literal(det["abstract"], datatype=XSD.string)))
            claims = list(det["claims"])
            if claims:
                g.add((p, ONT.firstClaimText, Literal(claims[0], datatype=XSD.string)))
                for c in claims:
                    g.add((p, ONT.claimText, Literal(c, datatype=XSD.string)))
            if det["claim_count"]:
                g.add((p, ONT.claimCount, Literal(int(det["claim_count"]), datatype=XSD.integer)))

        for code in codes:
            iri = ipc_iri(code)
            g.add((p, ONT.hasIPC, iri))
            g.add((iri, RDF.type, ONT.IPCSymbol))
            g.add((iri, SKOS.notation, Literal(code.strip())))

        for iri in hits["process"]:
            g.add((p, ONT.realizesProcess, URIRef(iri)))
        for iri in hits["device"]:
            g.add((p, ONT.concernsDevice, URIRef(iri)))
    return g


def _iso(yyyymmdd: str) -> str:
    s = str(yyyymmdd).strip()
    return f"{s[:4]}-{s[4:6]}-{s[6:8]}"


def main() -> int:
    import argparse

    from sdkb_paper.preprocess.profile import KSIA_DELTA

    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", choices=["samsung-hynix", "ksia-equipment"], default="samsung-hynix",
                    help="samsung-hynix=G₁(PLAN-002) · ksia-equipment=G₂ 소부장(RQ3 · PLAN-014 C-2)")
    args = ap.parse_args()

    if args.corpus == "ksia-equipment":
        from sdkb_paper.collect.collect import KSIA_DETAILS
        df = pd.read_parquet(KSIA_DELTA)
        details = None
        if KSIA_DETAILS.exists():
            dd = pd.read_parquet(KSIA_DETAILS)
            details = {r.application_number: {"abstract": r.abstract, "claims": r.claims,
                                             "claim_count": r.claim_count}
                       for r in dd.itertuples()}
        g = build_delta(df, org_of=_org_ksia, activity=ACTIVITY_KSIA,
                        activity_label="KIPRIS KSIA equipment ingest (RQ3 · PLAN-014 C-2)",
                        details=details)
        out = DELTA_V2_TTL
    else:
        df = pd.read_parquet(DELTA_PARQUET)
        g = build_delta(df)
        out = DELTA_TTL

    PROCESSED.mkdir(parents=True, exist_ok=True)
    g.serialize(out, format="turtle")
    n = len(set(g.subjects(RDF.type, ONT.Patent)))
    print(f"✓ 델타 특허 {n:,}건 · 트리플 {len(g):,} → {out}")
    print(f"  (델타 후보 {len(df):,}행 중 미매핑 제외 후 특허 {n:,}건 — 미매핑은 게이트 통과 불가)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
