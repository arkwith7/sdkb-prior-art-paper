"""델타 그래프 생성 — 매핑된 특허만 SDKB 어휘로 트리플화한다 (PLAN-002).

어휘는 전부 SDKB 실물에서 관찰한 것이다. 새 술어·클래스를 만들지 않는다 (CLAUDE.md §1.4).
  pat:kr_<출원번호>  a ont:Patent
    rdfs:label · ont:applicationNumber · ont:filingDate(xsd:date) · ont:publicationDate
    ont:patentOffice · ont:assignedTo(→ 기존 organization) · ont:hasIPC(→ ont:IPCSymbol)
    ont:realizesProcess / ont:concernsDevice   ← 룰 매핑 결과
    ont:source · ont:license · prov:wasGeneratedBy

두 가지를 넣지 **않는다**:
- **초록 원문.** KIPRIS 는 학술 이용·비재배포 조건이다 (CLAUDE.md §1.3). 텍스트 매칭은
  parquet(로컬)에서 하고, 그래프에는 결과 링크만 남긴다.
- **미매핑 특허.** 개념 링크가 없으면 델타 shape 를 통과할 수 없다. 우회로를 만들지 않고
  프로파일에 미매핑으로 보고한다.
"""
from __future__ import annotations

import pandas as pd
from rdflib import RDF, RDFS, XSD, Graph, Literal, URIRef
from rdflib.namespace import SKOS

from sdkb_paper.config import ONT, PATENT_NS, PROCESSED, SDKB_DATA, bind_namespaces
from sdkb_paper.ontology.mapping import load_code_mapping, map_codes_to_concepts
from sdkb_paper.preprocess.profile import DELTA as DELTA_PARQUET

PROV = URIRef("http://www.w3.org/ns/prov#")
PROV_ACTIVITY = URIRef("http://www.w3.org/ns/prov#Activity")
WAS_GENERATED_BY = URIRef("http://www.w3.org/ns/prov#wasGeneratedBy")

DELTA_TTL = PROCESSED / "delta_v1.ttl"
GRAPH_V1 = PROCESSED / "graph_v1.ttl"

# G₀ 에 이미 있는 조직 인스턴스를 재사용한다 — 새로 만들면 CQ08(출원인 포트폴리오)이 쪼개진다.
ORG = {
    "삼성전자주식회사": SDKB_DATA["organization/samsung_electronics"],
    "에스케이하이닉스 주식회사": SDKB_DATA["organization/sk_hynix"],
}
ACTIVITY = SDKB_DATA["activity/kipris_plan002_ingest"]
SOURCE = "KIPRIS Plus API (getAdvancedSearch)"
LICENSE = "KIPRIS terms — academic use, no redistribution of full text"


def ipc_iri(code: str) -> URIRef:
    """'H10B 69/00' → data:ipc/H10B_69-00 (SDKB 의 기존 인코딩)."""
    return SDKB_DATA["ipc/" + code.strip().replace(" ", "_").replace("/", "-")]


def build_delta(df: pd.DataFrame) -> Graph:
    g = Graph()
    bind_namespaces(g)
    g.add((ACTIVITY, RDF.type, PROV_ACTIVITY))
    g.add((ACTIVITY, RDFS.label, Literal("KIPRIS Samsung/SK hynix ingest (PLAN-002)")))

    table = load_code_mapping()
    for row in df.sort_values("application_number").itertuples():
        codes = [c.strip() for c in row.ipc_codes if c.strip()]
        hits = map_codes_to_concepts(codes, table)
        if not (hits["process"] or hits["device"]):
            continue  # 미매핑은 델타에 넣지 않는다 — 게이트를 통과할 수 없다

        p = PATENT_NS[f"kr_{row.application_number}"]
        g.add((p, RDF.type, ONT.Patent))
        g.add((p, RDFS.label, Literal(row.invention_title)))
        g.add((p, ONT.applicationNumber, Literal(row.application_number, datatype=XSD.string)))
        g.add((p, ONT.filingDate, Literal(row.application_date.date().isoformat(), datatype=XSD.date)))
        g.add((p, ONT.patentOffice, Literal("KR")))
        g.add((p, ONT.source, Literal(SOURCE, datatype=XSD.string)))
        g.add((p, ONT.license, Literal(LICENSE, datatype=XSD.string)))
        g.add((p, WAS_GENERATED_BY, ACTIVITY))

        if row.open_date:
            g.add((p, ONT.publicationDate, Literal(_iso(row.open_date), datatype=XSD.date)))
        org = ORG.get(row.applicant_name)
        if org is not None:
            g.add((p, ONT.assignedTo, org))

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
    df = pd.read_parquet(DELTA_PARQUET)
    g = build_delta(df)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    g.serialize(DELTA_TTL, format="turtle")
    n = len(set(g.subjects(RDF.type, ONT.Patent)))
    print(f"✓ 델타 특허 {n:,}건 · 트리플 {len(g):,} → {DELTA_TTL}")
    print(f"  (델타 후보 {len(df):,}건 중 미매핑 {len(df)-n:,}건은 넣지 않았다 — 게이트 통과 불가)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
