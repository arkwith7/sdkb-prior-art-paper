from sdkb_paper.ontology.mapping import map_codes_to_concepts

# concept_iri 는 SDKB 실물 인스턴스 IRI (data:process/… , data:subprocess/…).
# 매핑 결과가 그대로 ont:realizesProcess 의 객체가 되므로, 존재하지 않는 IRI 를 쓰면
# SHACL 게이트의 sh:class ont:Process 에서 걸린다.
ETCH = "https://w3id.org/sdkb/data/process/etch"
PLASMA_ETCH = "https://w3id.org/sdkb/data/subprocess/plasma_etch"
LITHOGRAPHY = "https://w3id.org/sdkb/data/process/lithography"

TABLE = {
    "H01L21/311": [PLASMA_ETCH],
    "H01L21": [ETCH],
    "G03F": [LITHOGRAPHY],
}


def test_longest_prefix_wins():
    assert map_codes_to_concepts(["H01L21/31105"], TABLE) == [PLASMA_ETCH]


def test_fallback_to_shorter_prefix():
    assert map_codes_to_concepts(["H01L21/02"], TABLE) == [ETCH]


def test_unmapped_code_returns_empty():
    assert map_codes_to_concepts(["B60W30/00"], TABLE) == []
