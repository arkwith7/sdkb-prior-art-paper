"""A-0 · 제2 도메인 후보(Brick Schema) 실측 — PLAN-064 §1.2 기준 K1–K4.

사전등록(PLAN-064-prereg.md) 발효 이전의 **후보 적격 확인**이며, 실험이 아니다. 출력은 전부
공개 릴리스 자산의 파싱 결과이고, 이 저장소의 자원·판정·수치는 하나도 건드리지 않는다.

  uv run python scripts/probe_brick_candidate.py --download <작업디렉터리>
  uv run python scripts/probe_brick_candidate.py <작업디렉터리>

첫 형태는 공개 릴리스에서 TTL 을 내려받은 뒤 측정하고, 두 번째는 이미 내려받은 것을 측정한다.
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
import urllib.request
from pathlib import Path

from rdflib import Graph, RDF, RDFS, OWL, Namespace

SH = Namespace("http://www.w3.org/ns/shacl#")
BRICK = Namespace("https://brickschema.org/schema/Brick#")

REL = "https://github.com/BrickSchema/Brick/releases/download/{v}/Brick.ttl"
RAW = "https://raw.githubusercontent.com/BrickSchema/Brick/v1.4.4/examples/{p}.ttl"
VERSIONS = ["v1.2.1", "v1.3.0", "v1.4.0", "v1.4.1", "v1.4.2", "v1.4.3", "v1.4.4"]
EXAMPLES = ["rice_brick", "soda_brick", "building_meter/building_meter",
            "submeter_hierarchies/main-and-submeter", "solar_array/solar_array",
            "g36/g36-combined-ahu-vav"]

# K3 — 하나의 어휘 위에 둘 이상의 사용 관점이 서는가. 관점별 어휘는 클래스 이름의 부분 문자열로
# 잡는다(Brick 은 클래스 이름 자체가 의미를 담는 명명 규약을 쓴다).
VIEWS = {
    "FDD(고장탐지·진단)": ("Alarm", "Status", "Command", "Fault", "Sensor"),
    "에너지 계량·보고": ("Meter", "Power", "Energy", "Electrical"),
    "공간·구역 점유": ("Zone", "Room", "Floor", "Space", "Occupancy", "Building"),
}


def fetch(url: str, dest: Path) -> None:
    if dest.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=300) as r:
        dest.write_bytes(r.read())


def schema_profile(path: Path) -> dict:
    g = Graph()
    g.parse(path, format="turtle")
    dep = {s for s in g.subjects(OWL.deprecated, None)
           if any(str(o).lower() in ("true", "1") for o in g.objects(s, OWL.deprecated))}
    return dict(
        triples=len(g),
        owl_class=len(set(g.subjects(RDF.type, OWL.Class))),
        objectproperty=len(set(g.subjects(RDF.type, OWL.ObjectProperty))),
        datatypeproperty=len(set(g.subjects(RDF.type, OWL.DatatypeProperty))),
        sh_nodeshape=len(set(g.subjects(RDF.type, SH.NodeShape))),
        sh_propertyshape=len(set(g.subjects(RDF.type, SH.PropertyShape))),
        shacl_predicates=len({p for p in set(g.predicates()) if str(p).startswith(str(SH))}),
        subclassof=len(list(g.triples((None, RDFS.subClassOf, None)))),
        deprecated_true=len(dep),
        classes=sorted(str(c) for c in g.subjects(RDF.type, OWL.Class)
                       if str(c).startswith(str(BRICK))),
    )


def abox_profile(path: Path) -> dict:
    g = Graph()
    g.parse(path, format="turtle")
    types = collections.Counter(
        str(o).replace(str(BRICK), "") for _, o in g.subject_objects(RDF.type)
        if str(o).startswith(str(BRICK)))
    views = {}
    for view, keys in VIEWS.items():
        hit = {t: c for t, c in types.items() if any(k in t for k in keys)}
        views[view] = dict(classes=len(hit), instances=sum(hit.values()))
    # "타입 단언"은 rdf:type 단언의 수이며, 한 주어가 여러 Brick 클래스를 가지면 여러 번 세어진다.
    return dict(triples=len(g),
                type_assertions=sum(types.values()),
                classes_used=len(types),
                views=views)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("workdir", type=Path)
    ap.add_argument("--download", action="store_true")
    args = ap.parse_args()
    work = args.workdir

    if args.download:
        for v in VERSIONS:
            fetch(REL.format(v=v), work / f"Brick-{v}.ttl")
        for p in EXAMPLES:
            fetch(RAW.format(p=p), work / f"ex-{Path(p).name}.ttl")

    print("== K1·K2 · 릴리스 계보와 SHACL 내장")
    prof = {}
    for v in VERSIONS:
        f = work / f"Brick-{v}.ttl"
        if not f.exists():
            print(f"   {v}: 없음 (--download 로 내려받는다)")
            continue
        prof[v] = schema_profile(f)
        p = prof[v]
        print(f"   {v}: 트리플 {p['triples']:,} · owl:Class {p['owl_class']:,} · "
              f"ObjectProperty {p['objectproperty']} · DatatypeProperty {p['datatypeproperty']} · "
              f"sh:NodeShape {p['sh_nodeshape']:,} · sh:PropertyShape {p['sh_propertyshape']} · "
              f"owl:deprecated=true {p['deprecated_true']}")

    print("\n== K1 · 세대 간 델타")
    vs = list(prof)
    for a, b in zip(vs, vs[1:]):
        A, B = set(prof[a]["classes"]), set(prof[b]["classes"])
        print(f"   {a} → {b}: 클래스 +{len(B - A)}/−{len(A - B)} · "
              f"ObjectProperty {prof[a]['objectproperty']}→{prof[b]['objectproperty']} · "
              f"DatatypeProperty {prof[a]['datatypeproperty']}→{prof[b]['datatypeproperty']} · "
              f"deprecated {prof[a]['deprecated_true']}→{prof[b]['deprecated_true']}")

    print("\n== K3·K4 · 공개 A-Box 와 태스크 뷰")
    ab = {}
    for p in EXAMPLES:
        f = work / f"ex-{Path(p).name}.ttl"
        if not f.exists():
            continue
        ab[p] = abox_profile(f)
        a = ab[p]
        print(f"   {Path(p).name}: 트리플 {a['triples']:,} · Brick 타입 단언 {a['type_assertions']:,} · "
              f"사용 클래스 {a['classes_used']}")
        for view, d in a["views"].items():
            print(f"      {view}: 클래스 {d['classes']}종 · 타입 단언 {d['instances']:,}")

    (work / "brick_probe.json").write_text(json.dumps(
        {"schema": {v: {k: x for k, x in p.items() if k != "classes"} for v, p in prof.items()},
         "abox": ab}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n기록: {work / 'brick_probe.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
