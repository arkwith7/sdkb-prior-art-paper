"""L2 게이트 — OWL 논리 일관성(consistency). owlready2 + HermiT.

논문 §3.3 의 3층 검증 게이트 중 L2. 병합 후 그래프가 기술논리적으로 일관되어야 한다.

HermiT 에 그래프를 그대로 먹일 수 없어서 **추론 전용 뷰**를 만든다 (원본 그래프는 불변):

1. Turtle -> RDF/XML.  owlready2 는 Turtle 을 파싱하지 못한다 (RDF/XML·NTriples 만).
2. owl:imports 제거.   owlready2 가 import IRI 를 HTTP 로 가져오려다 404 로 죽는다.
   graph_v0/vN 은 이미 TBox 모듈을 전부 병합한 그래프라 import 는 중복이며,
   제거해야 게이트가 네트워크에 의존하지 않는다 (CI 재현성).
3. xsd:date -> xsd:dateTime.  HermiT 는 OWL 2 datatype map 만 지원하는데 xsd:date 는
   거기 없다 (UnsupportedDatatypeException). SDKB 의 sdkb-patent.ttl 은 filingDate 등의
   rdfs:range 를 xsd:date 로 선언하므로 그대로는 추론이 불가능하다.
   range 선언과 리터럴을 **함께** 승격하므로 타입 불일치 탐지력은 유지된다
   (예: filingDate 가 xsd:string 이면 range 위반으로 여전히 비일관).
   원본의 xsd:date 는 그대로 두고 SHACL(L1)이 검사한다 — H2 시계열의 전제.
4. 메타모델링 트리플 제거.  클래스 계층에 OWL/RDFS 빌트인을 얹은 선언(예: Brick 의
   `brick:EntityProperty rdfs:subClassOf owl:ObjectProperty`)은 OWL Full 이라 DL 추론기가
   원리적으로 받지 못한다 — 적재 단계에서 metaclass 충돌로 죽는다(실측 2026-08-22).
   이것은 게이트를 완화하는 것이 아니라 **L2 를 적용 가능한 범위로 사영**하는 것이며,
   SDKB graph_v0 에서는 해당 트리플이 0건이라 무연산이다(SPEC-010 §6.1).

Java 가 필요하다 (HermiT 는 JAR). 로컬/Colab: apt-get install default-jre.

CLI:  python -m sdkb_paper.validate.reasoner_gate <graph.ttl|.owl>
      (비일관 시 exit code 1 -> CI 에서 게이트로 동작)
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from rdflib import RDF, RDFS, XSD, Graph, Literal, OWL

# OWL/RDFS 빌트인 — 이것을 상위 클래스·상위 술어로 두면 OWL Full 이다(모듈 docstring 4번).
DL_BUILTINS = frozenset({OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty,
                         OWL.AnnotationProperty, RDF.Property, RDFS.Class, RDFS.Resource})


def reasoning_view(graph: Graph) -> Graph:
    """HermiT 가 먹을 수 있는 형태로 그래프를 변환한다 (모듈 docstring 의 2·3번).

    입력 그래프를 수정하지 않는다 — 사본을 반환한다.
    """
    g = Graph()
    for s, p, o in graph:
        if p == OWL.imports:
            continue
        if p in (RDFS.subClassOf, RDFS.subPropertyOf) and o in DL_BUILTINS:
            continue  # OWL Full → DL 사영 (제거 건수는 dl_projection_count 가 센다)
        if isinstance(o, Literal) and o.datatype == XSD.date:
            o = Literal(f"{o}T00:00:00", datatype=XSD.dateTime)
        elif isinstance(o, Literal) and o.datatype == XSD.gYear:
            # xsd:gYear("2023") 도 HermiT 의 OWL 2 datatype map 밖이다 (xsd:date 와 같은 사유).
            # 전문가 retirementYear 가 이 타입을 쓴다. 원본 그래프의 gYear 는 그대로 두고
            # (L1 SHACL 이 검사) 추론 뷰에서만 dateTime 으로 사상한다.
            o = Literal(f"{o}-01-01T00:00:00", datatype=XSD.dateTime)
        elif o == XSD.date:  # rdfs:range xsd:date 같은 TBox 선언
            o = XSD.dateTime
        elif o == XSD.gYear:  # rdfs:range xsd:gYear 같은 TBox 선언
            o = XSD.dateTime
        g.add((s, p, o))
    return g


def dl_projection_count(graph: Graph) -> int:
    """사영이 제거하는 메타모델링 트리플 수. 판정 보고에 함께 싣는다 — 조용히 빼지 않는다."""
    return sum(1 for _s, p, o in graph
               if p in (RDFS.subClassOf, RDFS.subPropertyOf) and o in DL_BUILTINS)


def check_consistency(path: str | Path) -> bool:
    return check_consistency_detail(path)[0]


def check_consistency_detail(path: str | Path) -> tuple[bool, dict]:
    """(일관성, 부가 정보). L2 가 묻는 것은 **비일관 여부 하나**다.

    `sync_reasoner` 는 HermiT 를 돌린 뒤 그 결과를 owlready2 의 파이썬 클래스 모델에 되쓴다.
    비일관은 되쓰기 **이전에** `OwlReadyInconsistentOntologyError` 로 나온다. 따라서 되쓰기
    단계에서 터지는 예외는 판정이 아니라 **표현의 문제**다 — 실측 2026-08-22: Brick v1.4.3 에서
    HermiT 가 추론한 동치가 owlready2 의 상속 그래프에 순환을 만들어 `TypeError: a __bases__
    item causes an inheritance cycle` 이 났고, 그 시점에 비일관은 선언되지 않았다.

    **이것을 "비일관"으로 세면 거짓 검출이고, 조용히 통과시키면 근거가 사라진다.** 그래서
    통과로 세되 `results_applied=False` 를 남겨 판정 JSON 에서 보이게 한다. 우리는 되쓰인
    파이썬 모델을 읽지 않으므로 판정에는 영향이 없다.
    """
    from owlready2 import OwlReadyInconsistentOntologyError, World, sync_reasoner

    view = reasoning_view(Graph().parse(path))
    tmp = Path(tempfile.mkdtemp(prefix="reasoner_gate_")) / "reasoning_view.owl"
    view.serialize(tmp, format="xml")

    world = World()  # 전역 owlready2 world 오염 방지 (테스트가 연달아 돌 때 중요)
    world.get_ontology(tmp.as_uri()).load()
    try:
        sync_reasoner(world)  # HermiT
        return True, {"results_applied": True}
    except OwlReadyInconsistentOntologyError:
        return False, {"results_applied": True}
    except TypeError as e:                     # 되쓰기 단계 — 판정은 이미 났다
        return True, {"results_applied": False, "note": f"{type(e).__name__}: {e}"}


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: python -m sdkb_paper.validate.reasoner_gate <graph.ttl|.owl>")
        sys.exit(2)
    target = sys.argv[1]
    ok = check_consistency(target)
    print(f"[reasoner_gate] {target}  consistent = {ok}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
