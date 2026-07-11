from sdkb_paper.ontology.mapping import map_codes_to_concepts

TABLE = {
    "H01L21/311": ["sdkb:Etching"],
    "H01L21": ["sdkb:FrontEndProcess"],
    "G03F": ["sdkb:Lithography"],
}

def test_longest_prefix_wins():
    assert map_codes_to_concepts(["H01L21/31105"], TABLE) == ["sdkb:Etching"]

def test_fallback_to_shorter_prefix():
    assert map_codes_to_concepts(["H01L21/02"], TABLE) == ["sdkb:FrontEndProcess"]

def test_unmapped_code_returns_empty():
    assert map_codes_to_concepts(["B60W30/00"], TABLE) == []
