"""온톨로지 뷰어 — 도메인 축(공정·소자) 중심의 점진 확장 그래프.

G₁ 413,749 · G₂ 429,353 트리플이다. 통째로 그리면 브라우저가 멈춘다. 그래서 **아무것도
미리 굽지 않고** 세 단계로 나눠 라이브 SPARQL 로 계산한다.

  L1 `domain_map`   공정 계층(Process→SubProcess) + 소자 축. 노드 ~83. 초기 화면.
  L1 `people_map`   역량을 다리로 둔 인력·문제 축(전문가 매칭 뷰).
  L1 `priorart_map` 선행기술조사 축 — 개념 · IPC 서브클래스(집계) · 거절유형(C2 의 검색 팔).
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
    "CitedPatent": {"ko": "인용 선행기술", "color": "#79c0ff"},
    "RejectionType": {"ko": "거절 유형", "color": "#f0883e"},
    # 집계 노드 — 그래프의 개체가 아니라 problemCategory 를 묶은 것이다.
    "ProblemCategory": {"ko": "문제 범주(집계)", "color": "#8250df"},
    # 집계 노드 — IPC 서브클래스는 그래프에 노드가 없다(IPCSymbol 의 notation 앞 4자리다).
    "IPCSubclass": {"ko": "IPC 서브클래스(집계)", "color": "#1f6feb"},
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


# ── 선행기술조사 축 ──────────────────────────────────────────────────
# C2(핵심증명)의 무대다. 검색이 실제로 타는 두 팔 — **개념 링크(ConceptOverlap)** 와
# **IPC** — 을 한 화면에 놓는다(§6.4 실측: 이득 본체는 ConceptOverlap+IPC).
#
# 세 축을 함께 그린다.
#   개념       Process·SubProcess·Device·Material·Skill 중 특허 링크가 있는 것(실측 80).
#   IPC        서브클래스(notation 앞 4자리)는 그래프에 노드가 없다 — `ipc:` 집계 노드다.
#   거절유형   RejectionType 중 `rejectedFor` 로 실제 쓰인 것만(선언 5 · 사용 2).
#
# qrel(정답 인용) 간선은 **그리되 정답지임을 화면에 밝힌다** — 검색 파이프라인에서는
# 마스킹되는 간선이다(CLAUDE.md §1.4 누출 통제). 화면에 있다고 검색이 쓰는 것이 아니다.
IPC_PREFIX = "ipc:"

_IPC_MIN_PATENTS = 20  # 서브클래스 203종 중 ≥20건만 그린다(43종) — 나머지는 note 로 밝힌다
_IPC_TOP_PER_CONCEPT = 2  # 개념당 상위 공동출현 IPC — 625쌍 전부는 hairball 이다
_QREL_TOP = 60  # qrel 개념→개념 흐름 상위(자기순환 제외)

# 개념 링크 술어 — 검색 팔이 쓰는 네 술어다(실측: realizesProcess 4,174 · involvesMaterial
# 2,068 · concernsSkill 1,994 · concernsDevice 430). involvesProcess 는 G₀ 에서 특허에 0건.
_CONCEPT_UNION = """{ ?p ont:realizesProcess ?c } UNION { ?p ont:concernsDevice ?c }
  UNION { ?p ont:involvesMaterial ?c } UNION { ?p ont:concernsSkill ?c }"""

_PA_CONCEPTS = _PREFIX + f"""
SELECT ?c ?cls ?label ?def (COUNT(DISTINCT ?p) AS ?n) WHERE {{
  VALUES ?cls {{ ont:Process ont:SubProcess ont:Device ont:Material ont:Skill }}
  ?c a ?cls ; skos:prefLabel ?label .
  OPTIONAL {{ ?c skos:definition ?def }}
  {_CONCEPT_UNION}
}} GROUP BY ?c ?cls ?label ?def
"""

# 질의(거절특허) 쪽 건수만 따로 — 후보 코퍼스와 섞으면 "질의 밀도"가 보이지 않는다.
_PA_QUERY_COUNTS = _PREFIX + f"""
SELECT ?c (COUNT(DISTINCT ?p) AS ?n) WHERE {{
  ?p a ont:RejectedPatent .
  {_CONCEPT_UNION}
}} GROUP BY ?c
"""

_PA_IPC = _PREFIX + """
SELECT ?sub (COUNT(DISTINCT ?p) AS ?n) WHERE {
  ?p ont:hasIPC ?ipc . ?ipc skos:notation ?not .
  BIND(SUBSTR(REPLACE(?not, " ", ""), 1, 4) AS ?sub)
} GROUP BY ?sub
"""

_PA_REJECTION = _PREFIX + """
SELECT ?t ?label (COUNT(DISTINCT ?p) AS ?n) WHERE {
  ?p ont:rejectedFor ?t . ?t skos:prefLabel ?label .
} GROUP BY ?t ?label
"""

_PA_REJ_CONCEPT = _PREFIX + f"""
SELECT ?t ?c (COUNT(DISTINCT ?p) AS ?n) WHERE {{
  ?p ont:rejectedFor ?t .
  {_CONCEPT_UNION}
}} GROUP BY ?t ?c
"""

_PA_CONCEPT_IPC = _PREFIX + f"""
SELECT ?c ?sub (COUNT(DISTINCT ?p) AS ?n) WHERE {{
  {_CONCEPT_UNION}
  ?p ont:hasIPC ?ipc . ?ipc skos:notation ?not .
  BIND(SUBSTR(REPLACE(?not, " ", ""), 1, 4) AS ?sub)
}} GROUP BY ?c ?sub
"""

# 질의 특허의 개념 → 그 질의의 심사관 인용(정답)의 개념. 공정·소자 축으로만 — 재료·역량까지
# 넣으면 쌍이 폭발한다(실측 realizesProcess 만으로 248쌍).
_PA_QREL_FLOW = _PREFIX + """
SELECT ?a ?b (COUNT(DISTINCT ?q) AS ?n) WHERE {
  ?q ont:hasPriorArtExaminer ?g .
  { ?q ont:realizesProcess ?a } UNION { ?q ont:concernsDevice ?a }
  { ?g ont:realizesProcess ?b } UNION { ?g ont:concernsDevice ?b }
} GROUP BY ?a ?b
"""

_priorart_cache: dict[str, dict] = {}


def priorart_map(graph_key: str) -> dict:
    """L1(선행기술조사 축) — 개념 · IPC 서브클래스(집계) · 거절유형.

    노드 크기는 **그 개념·분류에 걸린 특허 수**(질의 1,000 + 인용 후보 3,034 합산)다.
    질의 쪽 건수는 `queries` 로 따로 실어 툴팁에서 분리해 보인다.
    """
    if graph_key in _priorart_cache:
        return _priorart_cache[graph_key]

    qcounts = {r[0]["value"]: int(r[1]["value"]) for r in run_query(graph_key, _PA_QUERY_COUNTS).rows}

    nodes: list[dict] = []
    concept_ids: set[str] = set()
    for c, cls, label, definition, n in run_query(graph_key, _PA_CONCEPTS).rows:
        cid = c["value"]
        if cid in concept_ids:  # 한 개념이 두 클래스를 가질 수 있다 — 처음 것만 그린다
            continue
        concept_ids.add(cid)
        cls_name = cls["value"].removeprefix(ONT)
        nodes.append(
            {
                "id": cid,
                "cls": cls_name,
                "axis_ko": _axis_ko(cls_name),
                "label": label["value"],
                "definition": definition["value"] if definition else None,
                "patents": int(n["value"]),
                "queries": qcounts.get(cid, 0),
            }
        )

    # IPC 서브클래스 집계. 상한 미달분은 감추되 **몇 개를 감췄는지 말한다.**
    ipc_rows = [(r[0]["value"], int(r[1]["value"])) for r in run_query(graph_key, _PA_IPC).rows]
    kept_ipc = {sub for sub, n in ipc_rows if n >= _IPC_MIN_PATENTS}
    for sub, n in ipc_rows:
        if sub not in kept_ipc:
            continue
        nodes.append(
            {
                "id": IPC_PREFIX + sub,
                "cls": "IPCSubclass",
                "axis_ko": _axis_ko("IPCSubclass"),
                "label": sub,
                "definition": None,
                "patents": n,
                "derived": True,
                "derived_note": f"IPC 서브클래스 집계 — 이 분류의 특허 {n}건 (그래프의 개체가 아니다)",
            }
        )

    # 거절유형 — 라벨이 ko·en 두 개다. 한국어를 고른다.
    rej: dict[str, tuple[str, int]] = {}
    for t, label, n in run_query(graph_key, _PA_REJECTION).rows:
        tid = t["value"]
        if tid not in rej or label.get("lang") == "ko":
            rej[tid] = (label["value"], int(n["value"]))
    for tid, (label, n) in rej.items():
        nodes.append(
            {
                "id": tid,
                "cls": "RejectionType",
                "axis_ko": _axis_ko("RejectionType"),
                "label": label,
                "definition": None,
                "patents": n,
                "queries": n,
            }
        )

    ids = {n["id"] for n in nodes}
    edges: list[dict] = []

    # (1) 공정 계층 뼈대 — 도메인 축과 같은 골격이라야 두 지도가 같은 세계로 읽힌다.
    for src, dst in run_query(graph_key, _DOMAIN_EDGES).rows:
        if src["value"] in ids and dst["value"] in ids:
            edges.append({"src": src["value"], "dst": dst["value"], "pred": "hasSubprocess"})

    # (2) 거절유형 → 개념
    for t, c, n in run_query(graph_key, _PA_REJ_CONCEPT).rows:
        if t["value"] in ids and c["value"] in ids:
            edges.append(
                {"src": t["value"], "dst": c["value"], "pred": "rejectedFor", "weight": int(n["value"])}
            )

    # (3) 개념 ↔ IPC 공동출현 — 개념당 상위 _IPC_TOP_PER_CONCEPT 개만(625쌍 전부는 못 읽는다)
    by_concept: dict[str, list[tuple[str, int]]] = {}
    for c, sub, n in run_query(graph_key, _PA_CONCEPT_IPC).rows:
        if c["value"] in ids and sub["value"] in kept_ipc:
            by_concept.setdefault(c["value"], []).append((sub["value"], int(n["value"])))
    ipc_pairs_total = sum(len(v) for v in by_concept.values())
    for cid, pairs in by_concept.items():
        for sub, n in sorted(pairs, key=lambda x: -x[1])[:_IPC_TOP_PER_CONCEPT]:
            edges.append(
                {"src": cid, "dst": IPC_PREFIX + sub, "pred": "hasIPC", "weight": n}
            )

    # (4) qrel 흐름(질의 개념 → 정답 개념). 정답지다 — 검색 시에는 마스킹된다.
    flow = [
        (r[0]["value"], r[1]["value"], int(r[2]["value"]))
        for r in run_query(graph_key, _PA_QREL_FLOW).rows
        if r[0]["value"] in ids and r[1]["value"] in ids
    ]
    self_loops = sum(1 for a, b, _ in flow if a == b)
    for a, b, n in sorted((f for f in flow if f[0] != f[1]), key=lambda x: -x[2])[:_QREL_TOP]:
        edges.append({"src": a, "dst": b, "pred": "qrelFlow", "weight": n})

    dropped_ipc = len(ipc_rows) - len(kept_ipc)
    _priorart_cache[graph_key] = out = {
        "mode": "priorart",
        "nodes": nodes,
        "edges": edges,
        "truncated": bool(dropped_ipc or self_loops or ipc_pairs_total > len(by_concept) * _IPC_TOP_PER_CONCEPT),
        "note": (
            "⚠ 붉은 점선은 <b>정답지</b>(hasPriorArtExaminer)를 개념 단위로 집계한 흐름이다 — "
            "검색 파이프라인에서는 마스킹되는 간선이며(누출 통제), 여기 보인다고 검색이 쓰는 것이 아니다. "
            f"IPC 서브클래스는 특허 {_IPC_MIN_PATENTS}건 이상만 그렸다(감춘 것 {dropped_ipc}종). "
            f"개념↔IPC 는 개념당 상위 {_IPC_TOP_PER_CONCEPT}개, qrel 흐름은 상위 {_QREL_TOP}쌍"
            f"(동일 개념 자기순환 {self_loops}쌍 제외). 노드 크기 = 걸린 특허 수(질의+후보)."
        ),
    }
    return out


_IPC_PATENTS = _PREFIX + """
SELECT ?p ?label ?cls WHERE {{
  VALUES ?cls {{ ont:RejectedPatent ont:CitedPatent }}
  ?p a ?cls ; skos:prefLabel ?label ; ont:hasIPC ?ipc .
  ?ipc skos:notation ?not .
  FILTER(STRSTARTS(REPLACE(?not, " ", ""), "{sub}"))
}} LIMIT {limit}
"""


def expand_ipc(graph_key: str, sub: str, limit: int = _EXPAND_LIMIT) -> dict:
    """IPC 집계 노드를 열면 그 서브클래스의 특허(질의·인용)가 나온다."""
    safe = "".join(ch for ch in sub if ch.isalnum())
    rows = run_query(graph_key, _IPC_PATENTS.format(sub=safe, limit=limit + 1)).rows
    truncated = len(rows) > limit
    hub = IPC_PREFIX + sub
    nodes, edges, seen = [], [], set()
    for p, label, cls in rows[:limit]:
        pid = p["value"]
        if pid in seen:
            continue
        seen.add(pid)
        cls_name = cls["value"].removeprefix(ONT)
        nodes.append(
            {
                "id": pid,
                "cls": cls_name,
                "axis_ko": _axis_ko(cls_name),
                "label": label["value"],
                "definition": None,
                "patents": 0,
            }
        )
        edges.append({"src": hub, "dst": pid, "pred": "hasIPC"})
    return {"mode": "expand", "nodes": nodes, "edges": edges, "truncated": truncated}
