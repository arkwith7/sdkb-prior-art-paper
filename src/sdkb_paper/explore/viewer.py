"""온톨로지 뷰어 — 도메인 축(공정·소자) 중심의 점진 확장 그래프.

G₁ 413,749 · G₂ 429,353 트리플이다. 통째로 그리면 브라우저가 멈춘다. 그래서 **아무것도
미리 굽지 않고** 세 단계로 나눠 라이브 SPARQL 로 계산한다.

  L1 `domain_map`   공정 계층(Process→SubProcess) + 소자 축. 노드 ~83. 초기 화면.
  L2 `expand`       개념 하나의 1-hop 이웃(특허·장비·재료·역량·통제). 상한 있음.
  L3 `detail`       노드 하나의 속성 전량. 사이드 패널·툴팁의 원천.

상한에 걸리면 **말한다**(`truncated`). 조용히 자르면 "이게 전부"로 읽히는데, 그건
사전 잘림 사건에서 이미 한 번 오답을 만든 실수다.
"""
from __future__ import annotations

from sdkb_paper.explore.store import run_query

ONT = "https://w3id.org/sdkb/ont/"
SKOS = "http://www.w3.org/2004/02/skos/core#"

_PREFIX = f"""PREFIX ont: <{ONT}>
PREFIX skos: <{SKOS}>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""

# 축별 표시 정보. 색은 프런트가 쓰고, 설명은 툴팁의 '범주' 줄이 된다.
AXES = {
    "Process": {"ko": "공정 그룹", "color": "#4493f8"},
    "SubProcess": {"ko": "하위 공정", "color": "#3fb950"},
    "Device": {"ko": "소자·제품", "color": "#e5487f"},
    "Material": {"ko": "재료", "color": "#d29922"},
    "Equipment": {"ko": "장비", "color": "#a371f7"},
    "EquipmentClass": {"ko": "장비 클래스", "color": "#8957e5"},
    "Skill": {"ko": "역량", "color": "#39c5cf"},
    "FailureMode": {"ko": "불량 모드", "color": "#f85149"},
    "Problem": {"ko": "실무 문제", "color": "#db6d28"},
    "Expert": {"ko": "전문가", "color": "#2ea043"},
    "Patent": {"ko": "특허", "color": "#7d8590"},
    "RejectedPatent": {"ko": "거절 특허", "color": "#6e7681"},
    "Organization": {"ko": "조직", "color": "#bf8700"},
    "Vendor": {"ko": "공급사", "color": "#9e6a03"},
    "TechnologyControl": {"ko": "수출통제", "color": "#da3633"},
    # 집계 노드 — 그래프의 개체가 아니라 problemCategory 를 묶은 것이다.
    "ProblemCategory": {"ko": "문제 범주(집계)", "color": "#8250df"},
}

# L2 확장에서 따라갈 관계. 리터럴 술어는 그래프가 아니라 속성 패널로 간다.
_EXPAND_LIMIT = 60
_MAX_NODES = 400

# 상주 그래프는 런타임에 불변이므로 L1 은 그래프당 한 번만 계산한다(G₂ 첫 호출 ~1s → 이후 0ms).
_domain_cache: dict[str, dict] = {}


def _axis_ko(cls: str) -> str:
    return AXES.get(cls, {}).get("ko", cls)


# ── L1: 도메인 축 지도 ──────────────────────────────────────────────
# 노드와 특허 집계를 **나눈다.** 한 질의에 COUNT(DISTINCT) 를 OPTIONAL·UNION 과 함께 두면
# G₁ 에서 4초가 걸렸다(실측). 나누면 두 질의 모두 인덱스를 그대로 타서 수십 ms 다.
_DOMAIN_NODES = _PREFIX + """
SELECT ?iri ?cls ?label ?def WHERE {
  VALUES ?cls { ont:Process ont:SubProcess ont:Device }
  ?iri a ?cls ; skos:prefLabel ?label .
  OPTIONAL { ?iri skos:definition ?def }
}
"""

_DOMAIN_COUNTS = _PREFIX + """
SELECT ?iri (COUNT(DISTINCT ?p) AS ?n) WHERE {
  { ?p ont:realizesProcess ?iri } UNION { ?p ont:concernsDevice ?iri }
} GROUP BY ?iri
"""

_DOMAIN_EDGES = _PREFIX + """
SELECT ?src ?dst WHERE { ?src a ont:Process ; ont:hasSubprocess ?dst }
"""


def domain_map(graph_key: str) -> dict:
    """L1 — 공정 계층과 소자 축. 노드 크기는 그 개념을 실현하는 특허 수다."""
    if graph_key in _domain_cache:
        return _domain_cache[graph_key]
    counts = {
        r[0]["value"]: int(r[1]["value"]) for r in run_query(graph_key, _DOMAIN_COUNTS).rows
    }
    nodes, edges = [], []
    for iri, cls, label, definition in run_query(graph_key, _DOMAIN_NODES).rows:
        cls_name = cls["value"].removeprefix(ONT)
        nodes.append(
            {
                "id": iri["value"],
                "cls": cls_name,
                "axis_ko": _axis_ko(cls_name),
                "label": label["value"],
                "definition": definition["value"] if definition else None,
                "patents": counts.get(iri["value"], 0),
            }
        )
    for src, dst in run_query(graph_key, _DOMAIN_EDGES).rows:
        edges.append({"src": src["value"], "dst": dst["value"], "pred": "hasSubprocess"})

    # 소자 축에는 공정으로 가는 직접 엣지가 없다 — 특허가 매개한다. 없는 링크를 그리지 않고
    # 그 사실을 그대로 알린다(확장에서 특허를 거쳐 보면 된다).
    _domain_cache[graph_key] = out = {
        "mode": "domain",
        "nodes": nodes,
        "edges": edges,
        "truncated": False,
        "note": "소자 축은 공정과 직접 연결되지 않는다 — 특허가 매개한다. 노드를 열어 확인하라.",
    }
    return out


# ── L2: 개념 1-hop 확장 ────────────────────────────────────────────
_EXPAND = _PREFIX + """
SELECT ?other ?cls ?label ?pred ?dir WHERE {{
  {{
    <{iri}> ?pred ?other . BIND("out" AS ?dir)
    ?other a ?cls ; skos:prefLabel ?label .
  }} UNION {{
    ?other ?pred <{iri}> . BIND("in" AS ?dir)
    ?other a ?cls ; skos:prefLabel ?label .
  }}
}} LIMIT {limit}
"""


def expand(graph_key: str, iri: str, limit: int = _EXPAND_LIMIT) -> dict:
    """L2 — 한 노드의 이웃. 리터럴은 빼고 IRI 이웃만(속성은 detail 이 준다)."""
    rows = run_query(graph_key, _EXPAND.format(iri=iri, limit=limit + 1)).rows
    truncated = len(rows) > limit
    nodes, edges, seen = [], [], set()
    for other, cls, label, pred, direction in rows[:limit]:
        oid = other["value"]
        cls_name = cls["value"].removeprefix(ONT)
        if oid not in seen:
            seen.add(oid)
            nodes.append(
                {
                    "id": oid,
                    "cls": cls_name,
                    "axis_ko": _axis_ko(cls_name),
                    "label": label["value"],
                    "definition": None,
                    "patents": 0,
                }
            )
        p = pred["value"].rsplit("/", 1)[-1].rsplit("#", 1)[-1]
        edges.append(
            {"src": iri, "dst": oid, "pred": p}
            if direction["value"] == "out"
            else {"src": oid, "dst": iri, "pred": p}
        )
    return {"mode": "expand", "nodes": nodes, "edges": edges, "truncated": truncated}


# ── L3: 노드 상세 ─────────────────────────────────────────────────
_DETAIL = _PREFIX + """
SELECT ?pred ?val ?vlabel WHERE {{
  <{iri}> ?pred ?val .
  OPTIONAL {{ ?val skos:prefLabel ?vlabel }}
}}
"""


def detail(graph_key: str, iri: str) -> dict:
    """L3 — 노드의 속성 전량. 툴팁·속성 패널이 여기서 나온다."""
    label, classes, definition = None, [], None
    alt: list[str] = []
    props: list[dict] = []
    for pred, val, vlabel in run_query(graph_key, _DETAIL.format(iri=iri)).rows:
        p = pred["value"]
        short = p.rsplit("/", 1)[-1].rsplit("#", 1)[-1]
        v = val["value"]
        if short == "prefLabel" and label is None:
            label = v
        elif short == "altLabel":
            alt.append(v)
        elif short == "definition":
            definition = v
        elif short == "type":
            classes.append(v.removeprefix(ONT))
        else:
            props.append(
                {
                    "pred": short,
                    "value": v,
                    "label": vlabel["value"] if vlabel else None,
                    "is_iri": val["type"] == "uri",
                }
            )
    cls = next((c for c in classes if c in AXES), classes[0] if classes else "")
    return {
        "iri": iri,
        "label": label or iri.rsplit("/", 1)[-1],
        "cls": cls,
        "axis_ko": _axis_ko(cls),
        "classes": classes,
        "definition": definition,
        "alt_labels": alt,
        "props": sorted(props, key=lambda x: x["pred"]),
    }


# ── 인력·문제 축 ────────────────────────────────────────────────────
# 공정·소자 축과 별개의 지도다. 여기의 관측 단위는 역량(Skill)이다 — 전문가와 실무문제가
# 모두 역량을 통해 붙기 때문이고(hasSkill 92 · requiresSkill 152), 그래서 역량이 다리다.
# 문제 226개를 그대로 뿌리면 읽히지 않으므로 `ont:problemCategory` 로 묶은 **집계 노드**를
# 쓴다. 집계 노드는 그래프의 개체가 아니므로 `cat:` 접두사로 구분해 표시한다.
CATEGORY_PREFIX = "cat:"

_SKILL_NODES = _PREFIX + """
SELECT ?iri ?label ?def (COUNT(DISTINCT ?e) AS ?experts) (COUNT(DISTINCT ?p) AS ?problems) WHERE {
  ?iri a ont:Skill ; skos:prefLabel ?label .
  OPTIONAL { ?iri skos:definition ?def }
  OPTIONAL { ?e a ont:Expert ; ont:hasSkill ?iri }
  OPTIONAL { ?p a ont:Problem ; ont:requiresSkill ?iri }
} GROUP BY ?iri ?label ?def
"""

_FAILURE_NODES = _PREFIX + """
SELECT ?iri ?label ?def (COUNT(DISTINCT ?p) AS ?problems) WHERE {
  ?iri a ont:FailureMode ; skos:prefLabel ?label .
  OPTIONAL { ?iri skos:definition ?def }
  OPTIONAL { ?p a ont:Problem ; ont:exhibitsFailureMode ?iri }
} GROUP BY ?iri ?label ?def
"""

_CATEGORY_NODES = _PREFIX + """
SELECT ?cat (COUNT(DISTINCT ?p) AS ?problems) WHERE {
  ?p a ont:Problem ; ont:problemCategory ?cat .
} GROUP BY ?cat
"""

_CATEGORY_SKILL = _PREFIX + """
SELECT ?cat ?skill (COUNT(DISTINCT ?p) AS ?n) WHERE {
  ?p a ont:Problem ; ont:problemCategory ?cat ; ont:requiresSkill ?skill .
} GROUP BY ?cat ?skill
"""

_people_cache: dict[str, dict] = {}


def people_map(graph_key: str) -> dict:
    """L1(인력·문제 축) — 역량을 다리로 둔 지도.

    역량 노드는 **전문가 수**로, 문제 범주 노드는 **문제 수**로 크기를 준다.
    둘의 불균형이 그대로 보이는 것이 이 지도의 쓸모다(실측: Defect Analysis 는
    문제 113건에 전문가 11명, Plasma Diagnostics·Gas Chemistry 는 전문가 0명).
    """
    if graph_key in _people_cache:
        return _people_cache[graph_key]

    nodes, edges = [], []
    for iri, label, definition, experts, problems in run_query(graph_key, _SKILL_NODES).rows:
        nodes.append(
            {
                "id": iri["value"],
                "cls": "Skill",
                "axis_ko": _axis_ko("Skill"),
                "label": label["value"],
                "definition": definition["value"] if definition else None,
                "patents": int(experts["value"]),  # 크기 = 보유 전문가 수
                "experts": int(experts["value"]),
                "problems": int(problems["value"]),
            }
        )
    for iri, label, definition, problems in run_query(graph_key, _FAILURE_NODES).rows:
        nodes.append(
            {
                "id": iri["value"],
                "cls": "FailureMode",
                "axis_ko": _axis_ko("FailureMode"),
                "label": label["value"],
                "definition": definition["value"] if definition else None,
                "patents": int(problems["value"]),
                "problems": int(problems["value"]),
            }
        )
    for cat, problems in run_query(graph_key, _CATEGORY_NODES).rows:
        nodes.append(
            {
                "id": CATEGORY_PREFIX + cat["value"],
                "cls": "ProblemCategory",
                "axis_ko": _axis_ko("ProblemCategory"),
                "label": cat["value"].replace("_", " "),
                "definition": None,
                "patents": int(problems["value"]),
                "problems": int(problems["value"]),
                "derived": True,  # 그래프의 개체가 아니라 problemCategory 집계다
            }
        )
    for cat, skill, n in run_query(graph_key, _CATEGORY_SKILL).rows:
        edges.append(
            {
                "src": CATEGORY_PREFIX + cat["value"],
                "dst": skill["value"],
                "pred": "requiresSkill",
                "weight": int(n["value"]),
            }
        )

    _people_cache[graph_key] = out = {
        "mode": "people",
        "nodes": nodes,
        "edges": edges,
        "truncated": False,
        "note": (
            "문제 범주는 ont:problemCategory 집계 노드다(그래프의 개체가 아니다). "
            "역량 노드 크기는 보유 전문가 수 — 문제는 많은데 작은 노드가 인력 공백이다."
        ),
    }
    return out


_CATEGORY_PROBLEMS = _PREFIX + """
SELECT ?p ?label WHERE {{
  ?p a ont:Problem ; ont:problemCategory "{cat}" ; skos:prefLabel ?label .
}} LIMIT {limit}
"""


def expand_category(graph_key: str, cat: str, limit: int = _EXPAND_LIMIT) -> dict:
    """집계 노드를 열면 그 범주의 실무문제가 나온다."""
    safe = cat.replace('"', "").replace("\\", "")
    rows = run_query(graph_key, _CATEGORY_PROBLEMS.format(cat=safe, limit=limit + 1)).rows
    truncated = len(rows) > limit
    hub = CATEGORY_PREFIX + cat
    nodes, edges = [], []
    for p, label in rows[:limit]:
        nodes.append(
            {
                "id": p["value"],
                "cls": "Problem",
                "axis_ko": _axis_ko("Problem"),
                "label": label["value"],
                "definition": None,
                "patents": 0,
            }
        )
        edges.append({"src": hub, "dst": p["value"], "pred": "problemCategory"})
    return {"mode": "expand", "nodes": nodes, "edges": edges, "truncated": truncated}
