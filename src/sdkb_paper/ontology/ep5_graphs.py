"""EP5 그래프 조립 — D₀…D₅ · 델타 · 이행 조건 R/N · 합성 정상 델타 (PLAN-064 A-4 · SPEC-010 §6).

**이 모듈은 판정하지 않는다.** 판정에 들어갈 그래프를 결정적으로 만들 뿐이며, 무엇을 만들지는
전부 동결된 사전등록(PLAN-064-prereg)이 정한다. 여기서 새로 정한 것은 §6.3–§6.4 의 두 자리
(공백노드 처리 · (N) 의 범위)이고, 그 결정은 결과를 보기 전에 SPEC-010 에 적혔다.

**왜 조립기가 따로 필요한가.** SDKB 는 그래프가 하나(G₀)지만 EP5 는 **여섯 판의 T-Box 각각에
같은 A-Box 를 얹은** 그래프 여섯이 판정 대상이다. 조립을 드라이버 안에 두면 계보 판정과 결함
판정이 서로 다른 방식으로 그래프를 만들게 되고, 그 순간 두 판정을 같은 자로 읽을 수 없다.
"""
from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from pathlib import Path

from rdflib import BNode, Graph, Literal, Namespace, OWL, RDF, RDFS, URIRef

from sdkb_paper import config

BRICK = Namespace("https://brickschema.org/schema/Brick#")
EP5 = Namespace("https://w3id.org/sdkb/ep5/normal#")

# 계보는 v1.3.0 이후로 한정한다 — v1.2.1 → v1.3.0 은 변경이 아니라 재설계다(사전등록 §1.1).
VERSIONS: tuple[tuple[str, str], ...] = (
    ("d0", "1.3.0"), ("d1", "1.4.0"), ("d2", "1.4.1"),
    ("d3", "1.4.2"), ("d4", "1.4.3"), ("d5", "1.4.4"),
)
DEV_ABOX = ("ex-rice_brick.ttl", "ex-g36-combined-ahu-vav.ttl")
HOLDOUT_ABOX = ("ex-soda_brick.ttl",)
# 사전등록 §5 — 클래스·술어·shape 계수가 전부 같고 트리플만 움직이는 유일한 인접 쌍.
REAL_NORMAL_DELTA = ("d2", "d3")
SEED = 20260822


def tbox_path(label: str) -> Path:
    ver = dict(VERSIONS)[label]
    return config.EXTERNAL_BRICK / f"Brick-v{ver}.ttl"


def load_tbox(label: str) -> Graph:
    g = Graph()
    g.parse(tbox_path(label), format="turtle")
    return g


def assemble(label: str, abox: tuple[str, ...] = HOLDOUT_ABOX,
             extra: Graph | None = None) -> Graph:
    """D_n = T-Box_n + A-Box (+ 델타). **원본 파일은 읽기만 한다.**"""
    g = load_tbox(label)
    for a in abox:
        g.parse(config.EXTERNAL_BRICK / a, format="turtle")
    if extra is not None:
        for t in extra:
            g.add(t)
    return g


# --- 델타 그래프 (SPEC-010 §6.3) ---------------------------------------------

def _has_bnode(t) -> bool:
    return any(isinstance(x, BNode) for x in t)


@dataclass(frozen=True)
class Delta:
    added: Graph
    removed: Graph
    n_bnode_added: int
    n_bnode_removed: int

    def summary(self) -> dict:
        return {"n_added": len(self.added), "n_removed": len(self.removed),
                "n_bnode_added": self.n_bnode_added,
                "n_bnode_removed": self.n_bnode_removed}


def tbox_delta(old: str, new: str) -> Delta:
    """`Δ = triples(new) − triples(old)`. 공백노드를 담은 트리플은 **개수만 센다**.

    적재마다 공백노드 라벨이 달라지므로 차집합에 넣으면 델타가 실행마다 흔들린다 —
    SPEC-009 §4 각주가 정준 해시에 쓴 자를 그대로 쓴다.
    """
    go, gn = load_tbox(old), load_tbox(new)
    so = {t for t in go if not _has_bnode(t)}
    sn = {t for t in gn if not _has_bnode(t)}
    added, removed = Graph(), Graph()
    for t in sorted(sn - so):
        added.add(t)
    for t in sorted(so - sn):
        removed.add(t)
    return Delta(added, removed,
                 sum(1 for t in gn if _has_bnode(t)),
                 sum(1 for t in go if _has_bnode(t)))


# --- 이행 조건 R/N (SPEC-010 §6.4) -------------------------------------------

def _deprecated(tbox: Graph) -> set[URIRef]:
    return {s for s, _, o in tbox.triples((None, OWL.deprecated, None))
            if str(o).lower() in ("true", "1")}


def _alias_map(tbox: Graph) -> dict[URIRef, URIRef]:
    """폐기 항목 → 대체 항목. `brick:aliasOf` 와 `owl:equivalentClass` 를 함께 본다."""
    dep = _deprecated(tbox)
    out: dict[URIRef, URIRef] = {}
    for t in sorted(dep):
        for pred in (BRICK.aliasOf, OWL.equivalentClass):
            for o in tbox.objects(t, pred):
                if isinstance(o, URIRef) and o not in dep and o != t:
                    out.setdefault(t, o)
    return out


def _mitigation_rules(tbox: Graph) -> list[str]:
    """`brick:deprecationMitigationRule` 아래의 SPARQL CONSTRUCT 전문(실측 2건)."""
    SH = Namespace("http://www.w3.org/ns/shacl#")
    out = []
    for _s, _p, shape in tbox.triples((None, BRICK.deprecationMitigationRule, None)):
        for rule in tbox.objects(shape, SH.rule):
            for c in tbox.objects(rule, SH.construct):
                out.append(str(c))
    return sorted(set(out))


def migrate_abox(abox: Graph, tbox: Graph) -> tuple[Graph, dict]:
    """(N) 조건 — 공식 이행 재료로 A-Box 의 폐기 항목을 재작성한다.

    **치환이 아니라 추가다.** 구 항목을 지우면 그것은 이행이 아니라 손실이고, 어느 CQ 가
    끊겼는지 이행 탓인지 삭제 탓인지 가릴 수 없게 된다. 공식 매핑이 없어 재작성하지 못한
    항목은 **개수와 목록으로 남긴다** — 조용히 빠지면 (N) 이 무엇을 했는지 알 수 없다.
    """
    amap = _alias_map(tbox)
    dep = _deprecated(tbox)
    out = Graph()
    for t in abox:
        out.add(t)
    rewritten, used_dep = 0, set()
    for s, p, o in abox:
        for term, slot in ((p, "p"), (o, "o")):
            if not isinstance(term, URIRef) or term not in dep:
                continue
            used_dep.add(term)
            alias = amap.get(term)
            if alias is None:
                continue
            out.add((s, alias, o) if slot == "p" else (s, p, alias))
            rewritten += 1
    rules = _mitigation_rules(tbox)
    n_rule_triples = 0
    for q in rules:
        try:
            for t in abox.query(q):
                out.add(tuple(t))
                n_rule_triples += 1
        except Exception:                       # 규칙 전문이 CONSTRUCT 가 아니면 건너뛴다
            continue
    unmapped = sorted(str(t) for t in used_dep if t not in amap)
    return out, {"n_rules": len(rules), "n_rule_triples": n_rule_triples,
                 "n_rewritten": rewritten, "n_deprecated_used": len(used_dep),
                 "n_unmapped": len(unmapped), "unmapped": unmapped[:50]}


def lineage_graph(label: str, condition: str,
                  abox_files: tuple[str, ...] = HOLDOUT_ABOX) -> tuple[Graph, dict]:
    """계보 판정의 대상 그래프. `condition` 은 'R'(원본) 또는 'N'(이행 적용)."""
    tbox = load_tbox(label)
    abox = Graph()
    for a in abox_files:
        abox.parse(config.EXTERNAL_BRICK / a, format="turtle")
    info: dict = {}
    if condition == "N":
        abox, info = migrate_abox(abox, tbox)
    elif condition != "R":
        raise ValueError(f"이행 조건은 R 또는 N 이다: {condition!r}")
    g = tbox
    for t in abox:
        g.add(t)
    return g, info


# --- 합성 정상 델타 30 (사전등록 §5) -----------------------------------------
#
# 생성 규칙 넷을 seed 20260822 로 조합한다. **주 태스크·타 태스크 어느 CQ 의 경로도 끊지
# 않는 변경만** 만든다 — 그래서 전부 **추가**이며, 기존 트리플을 지우거나 바꾸지 않는다.
# 규칙 ①(재명명)조차 구 IRI 를 `owl:equivalentClass` 로 남기고 A-Box·CQ 가 쓰지 않는 클래스만
# 고른다. 위양성이 나온다면 그것은 게이트가 **무해한 변경을 거부했다**는 뜻이어야 한다.

NORMAL_RULES = ("R1_relabel_rename", "R2_partial_deprecation_map",
                "R3_comment_annotation", "R4_equivalent_alias")


def _cq_referenced_locals(cq_dir: Path) -> set[str]:
    names: set[str] = set()
    for rq in sorted(cq_dir.glob("*.rq")):
        text = rq.read_text(encoding="utf-8")
        for tok in text.replace("<", " ").replace(">", " ").split():
            if tok.startswith("brick:"):
                names.add(tok.split(":", 1)[1].strip(".;,()[]"))
    return names


def _abox_used(abox: Graph) -> set[URIRef]:
    used = {p for _s, p, _o in abox}
    used |= {o for _s, _p, o in abox if isinstance(o, URIRef)}
    return used


def synthetic_normal_deltas(label: str = "d0", n: int = 30, seed: int = SEED,
                            cq_dir: Path | None = None,
                            abox_files: tuple[str, ...] = HOLDOUT_ABOX) -> list[dict]:
    """정상 델타 n 건. 같은 seed 에서 **같은 트리플 집합**을 낸다(결정적)."""
    cq_dir = cq_dir or (config.ROOT / "queries" / "brick" / "cq")
    tbox = load_tbox(label)
    abox = Graph()
    for a in abox_files:
        abox.parse(config.EXTERNAL_BRICK / a, format="turtle")
    reserved = _cq_referenced_locals(cq_dir)
    used = _abox_used(abox)
    dep = _deprecated(tbox)
    amap = _alias_map(tbox)

    classes = sorted(s for s in tbox.subjects(RDF.type, OWL.Class)
                     if isinstance(s, URIRef) and str(s).startswith(str(BRICK))
                     and s not in dep and s not in used
                     and str(s)[len(str(BRICK)):] not in reserved)
    dep_used = sorted(t for t in used if t in dep and t in amap)
    rng = random.Random(seed)

    def _make(rule: str, i: int) -> tuple[Graph, dict] | None:
        """재료가 없으면 **None 을 낸다** — 조용히 다른 규칙으로 새지 않는다."""
        g = Graph()
        if rule == "R1_relabel_rename":
            if not classes:
                return None
            src = classes[rng.randrange(len(classes))]
            new_iri = URIRef(str(src) + "_v2")
            label_ = tbox.value(src, RDFS.label) or Literal(str(src)[len(str(BRICK)):])
            g.add((new_iri, RDF.type, OWL.Class))
            g.add((new_iri, RDFS.label, label_))          # S-D1 (델타 shape) 충족
            g.add((new_iri, OWL.equivalentClass, src))    # 구 IRI 를 살려 둔다
            return g, {"class": str(src), "renamed_to": str(new_iri)}
        if rule == "R2_partial_deprecation_map":
            if not dep_used:
                return None
            term = dep_used[rng.randrange(len(dep_used))]
            g.add((term, OWL.equivalentClass, amap[term]))
            return g, {"deprecated": str(term), "alias": str(amap[term])}
        if rule == "R3_comment_annotation":
            if not classes:
                return None
            src = classes[rng.randrange(len(classes))]
            g.add((src, RDFS.comment,
                   Literal(f"EP5 정상 델타 {i:02d} — 주석 추가(경로 불변)", lang="ko")))
            return g, {"class": str(src)}
        if not classes:
            return None
        src = classes[rng.randrange(len(classes))]
        alias = EP5[f"Alias{i:02d}"]
        g.add((alias, RDF.type, OWL.Class))
        g.add((alias, RDFS.label, Literal(f"EP5 alias {i:02d}")))
        g.add((alias, OWL.equivalentClass, src))
        return g, {"class": str(src), "alias": str(alias)}

    out: list[dict] = []
    for i in range(n):
        want = NORMAL_RULES[i % len(NORMAL_RULES)]
        made, rule, subbed = None, want, None
        for cand in (want, *[r for r in NORMAL_RULES if r != want]):
            made = _make(cand, i)
            if made is not None:
                rule = cand
                subbed = None if cand == want else want
                break
        if made is None:
            raise RuntimeError("정상 델타를 만들 재료가 하나도 없다 — 자원을 확인하라")
        g, detail = made
        rec = {"id": f"N{i:02d}", "rule": rule, "delta": g, "n_triples": len(g),
               "detail": detail, "digest": _digest(g)}
        if subbed:
            # **대체를 기록한다.** 규칙 ②는 d0 에서 재료가 0 이다(폐기 항목 중 기계 매핑을
            # 가진 것이 없다 — 실측). 라벨만 R2 로 두고 내용은 다른 규칙이면 그 표는 거짓이다.
            rec["substituted_from"] = subbed
        out.append(rec)
    return out


def _digest(g: Graph) -> str:
    h = hashlib.sha256()
    for t in sorted(f"{s} {p} {o}" for s, p, o in g if not _has_bnode((s, p, o))):
        h.update(t.encode())
    return h.hexdigest()[:16]
