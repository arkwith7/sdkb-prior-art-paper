"""결함 주입 — 게이트 판별력(H1)의 직접 검정 입력 (원고 §4.10 · PLAN-020 W4).

정상 그래프(G₀)에 **통제된 결함**을 주입해 "어느 층이 이 결함을 잡는가"를 실측한다. 결함군은
원고 §4.10 표의 12종이며 세 층으로 설계돼 있다 — (i) 형식 검증(L0–L3)이 잡아야 할 것,
(ii) 게이트 태스크 성능(T1·T2)이 잡아야 할 의미 결함, (iii) **교차 태스크(T3)만 잡을 수 있는 것**.
마지막 2종(동의어 오병합·공유 계층 역전)이 L0–L3·T1·T2 를 통과하고 T3 에서만 걸리면 H1 지지다.

**오염 규율(사용자 요구 2026-07-28).** 이 모듈은 정본을 **절대 쓰지 않는다**. 입력 그래프는 읽기
전용으로 열고, 결함본은 `validate.quarantine` 이 발급한 격리 디렉터리에만 쓴다. 러너는 매
인스턴스 뒤 정본 해시를 재검증한다(`quarantine.verify_pristine`).

**결정성(F16).** 결함마다 `seed = hash(fault_key, strength, rep)` 로 고정하고, 후보 트리플은
정렬 후 표본한다 — 같은 (결함·강도·반복)은 언제 돌려도 같은 그래프를 낸다.

**강도.** 1%/5%/10% 는 **적격 단위 수 대비 비율**이며 `n = max(1, round(rate·N))` 이다. 하한 1 을
두는 이유는 Skill 12개·hasSubprocess 38개처럼 모수가 작은 축에서 1% 가 0 이 되어 "결함 없는
결함 주입"이 되는 것을 막기 위해서다. 이 규칙은 결과를 보기 전에 고정했다.

CLI: `python -m sdkb_paper.validate.fault_inject --list`
"""
from __future__ import annotations

import argparse
import hashlib
import random
from dataclasses import dataclass
from pathlib import Path

from pyoxigraph import DefaultGraph, NamedNode, Quad, RdfFormat, Store

from .. import config

ONT = str(config.ONT)
SKOS = "http://www.w3.org/2004/02/skos/core#"
RDF_TYPE = NamedNode("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
RDFS_SUBCLASS = NamedNode("http://www.w3.org/2000/01/rdf-schema#subClassOf")

# 코퍼스가 문서 피처로 읽는 개념 술어 (corpus.assemble.CONCEPT_PROPS 와 같은 목록)
CONCEPT_PROPS = ("realizesProcess", "involvesProcess", "concernsDevice",
                 "involvesMaterial", "concernsSkill", "exhibitsFailureMode")
DOC_TYPES = ("Patent", "RejectedPatent", "CitedPatent")

STRENGTHS = (0.01, 0.05, 0.10)   # 원고 §4.10 동결


def ont(name: str) -> NamedNode:
    return NamedNode(ONT + name)


def skos(name: str) -> NamedNode:
    return NamedNode(SKOS + name)


def load(path: Path, workdir: Path) -> Store:
    """그래프를 격리 작업공간의 스토어로 적재한다(정본 파일은 읽기만 한다)."""
    store = Store(path=str(workdir / "store"))
    with open(path, "rb") as fh:
        store.bulk_load(fh, format=RdfFormat.TURTLE)
    return store


def dump(store: Store, out: Path) -> Path:
    """Turtle 은 데이터셋(명명그래프)을 못 담으므로 기본 그래프만 명시해 덤프한다."""
    store.dump(str(out), RdfFormat.TURTLE, from_graph=DefaultGraph())
    return out


def _sorted_quads(store: Store, s=None, p=None, o=None) -> list[Quad]:
    """결정적 순회 — 트리플 문자열 정렬. pyoxigraph 반복 순서에 의존하지 않는다."""
    return sorted(store.quads_for_pattern(s, p, o, None),
                  key=lambda q: (str(q.subject), str(q.predicate), str(q.object)))


def _subjects_of_type(store: Store, cls: str) -> list[Quad]:
    """해당 클래스 인스턴스의 rdf:type 쿼드(주어와 **명명그래프**를 함께 들고 다닌다).

    합집합 스토어에서는 추가 트리플이 어느 명명그래프에 들어가는지가 중요하다 — 기본 그래프에
    떨어지면 `GRAPH ?g` 로 도는 뷰 추출이 그 결함을 못 본다.
    """
    return _sorted_quads(store, None, RDF_TYPE, ont(cls))


def _n(rate: float, total: int) -> int:
    """강도 → 적용 단위 수. 하한 1(모수가 작아도 결함이 실제로 들어가게)."""
    return 0 if total == 0 else max(1, round(rate * total))


def _sample(rng: random.Random, items: list, rate: float) -> list:
    k = min(len(items), _n(rate, len(items)))
    return rng.sample(items, k) if k else []


# --- 결함 12종 ----------------------------------------------------------------
# 각 함수: (store, rate, rng) -> stats dict. store 를 제자리에서 변형한다.

def f01_stale_artifact(store: Store, rate: float, rng: random.Random) -> dict:
    """L0 표적 — 그래프 내용은 그대로 두고 **산출물을 낡게** 만든다.

    실제 되돌리기는 러너가 파일 mtime 을 입력보다 이전으로 되돌려 수행한다(파일시스템 사실이라
    트리플로 표현할 수 없다). 여기서는 결함 사실만 선언한다.
    """
    return {"mutation": "none(graph)", "file_level": "backdate_mtime", "n_affected": 1}


def f02_missing_required(store: Store, rate: float, rng: random.Random) -> dict:
    """L1 표적 — 필수 서지 속성(filingDate) 제거."""
    quads = _sorted_quads(store, None, ont("filingDate"), None)
    hit = _sample(rng, quads, rate)
    for q in hit:
        store.remove(q)
    return {"predicate": "filingDate", "n_candidates": len(quads), "n_affected": len(hit)}


def f03_logic_contradiction(store: Store, rate: float, rng: random.Random) -> dict:
    """L2 표적 — 클래스 계층에 순환을 만들고 문서에 상호배타적 타입을 동시 부여한다.

    ⚠️ as-built: SDKB TBox 에는 `owl:disjointWith`·카디널리티 제약이 **하나도 없다**(실측
    2026-07-28). 따라서 이 주입이 L2 에서 검출되지 않아도 그것은 주입 실패가 아니라 **TBox 의
    논리 표면이 비어 있다는 관측**이다 — 결과를 그대로 보고한다(CLAUDE.md §1-2).
    """
    classes = sorted({q.object.value
                      for q in store.quads_for_pattern(None, RDFS_SUBCLASS, None, None)
                      if isinstance(q.object, NamedNode)})
    pairs = _sample(rng, classes, rate)
    for c in pairs:                      # A ⊑ B 가 이미 있는 곳에 B ⊑ A 를 더해 순환을 만든다
        for q in _sorted_quads(store, None, RDFS_SUBCLASS, NamedNode(c)):
            store.add(Quad(NamedNode(c), RDFS_SUBCLASS, q.subject, q.graph_name))
    docs = _sample(rng, _subjects_of_type(store, "Patent"), rate)
    for d in docs:                       # 문서에 개념 클래스 타입을 동시 부여(타입 모순 시도)
        store.add(Quad(d.subject, RDF_TYPE, ont("Process"), d.graph_name))
    return {"n_class_cycles": len(pairs), "n_type_conflicts": len(docs),
            "n_affected": len(pairs) + len(docs),
            "caveat": "TBox 에 disjointWith·카디널리티 제약 0 — L2 검출 표면 자체가 좁다"}


def f04_cq_path_deleted(store: Store, rate: float, rng: random.Random) -> dict:
    """L3 표적 — CQ 필수 경로(개념 라벨) 삭제. 다수 CQ 가 skos:prefLabel 을 요구한다."""
    concepts = _subjects_of_type(store, "Process") + _subjects_of_type(store, "SubProcess")
    hit = _sample(rng, sorted(concepts, key=str), rate)
    n = 0
    for c in hit:
        for q in _sorted_quads(store, c.subject, skos("prefLabel"), None):
            store.remove(q)
            n += 1
    return {"n_concepts": len(hit), "n_labels_removed": n, "n_affected": len(hit)}


def f05_concept_misalignment(store: Store, rate: float, rng: random.Random) -> dict:
    """T1 표적 — 의미 정렬 오류. 문서→공정 링크의 대상을 무관한 공정으로 재배선."""
    quads = _sorted_quads(store, None, ont("realizesProcess"), None)
    targets = sorted({q.object.value for q in quads if hasattr(q.object, "value")})
    hit = _sample(rng, quads, rate)
    for q in hit:
        other = [t for t in targets if t != getattr(q.object, "value", None)]
        if not other:
            continue
        store.remove(q)
        store.add(Quad(q.subject, q.predicate, NamedNode(rng.choice(other)), q.graph_name))
    return {"predicate": "realizesProcess", "n_candidates": len(quads), "n_affected": len(hit)}


def f06_hierarchy_flatten(store: Store, rate: float, rng: random.Random) -> dict:
    """T1(+일부 L3) 표적 — 공정 하위계층 평탄화. hasSubprocess 를 끊어 층을 무너뜨린다."""
    quads = _sorted_quads(store, None, ont("hasSubprocess"), None)
    hit = _sample(rng, quads, rate)
    for q in hit:
        store.remove(q)
    return {"predicate": "hasSubprocess", "n_candidates": len(quads), "n_affected": len(hit)}


def f07_rejection_shuffle(store: Store, rate: float, rng: random.Random) -> dict:
    """T1·T2 표적 — 판단 문맥 치환. 거절근거(rejectedFor) 대상을 질의 간에 섞는다."""
    quads = _sorted_quads(store, None, ont("rejectedFor"), None)
    hit = _sample(rng, quads, rate)
    objs = [q.object for q in hit]
    rng.shuffle(objs)
    for q, o in zip(hit, objs):
        store.remove(q)
        store.add(Quad(q.subject, q.predicate, o, q.graph_name))
    return {"predicate": "rejectedFor", "n_candidates": len(quads), "n_affected": len(hit)}


def f08_metadata_deleted(store: Store, rate: float, rng: random.Random) -> dict:
    """T1(약한 신호) 표적 — 분류코드·출원인 메타데이터 삭제."""
    n = 0
    for pred in ("hasCPC", "hasIPC", "assignedTo"):
        quads = _sorted_quads(store, None, ont(pred), None)
        for q in _sample(rng, quads, rate):
            store.remove(q)
            n += 1
    return {"predicates": ["hasCPC", "hasIPC", "assignedTo"], "n_affected": n}


def f09_temporal_leak(store: Store, rate: float, rng: random.Random) -> dict:
    """누출 감사 표적 — 질의 이후 공개된 문서에서만 얻을 수 있는 개념 링크를 질의에 삽입.

    질의(RejectedPatent)에 그 질의의 **심사관 정답 문서**가 가진 개념을 복사해 붙인다. 정답을
    보지 않고는 만들 수 없는 링크이므로 시점·정답 양쪽으로 오염된 피처다.
    """
    queries = _subjects_of_type(store, "RejectedPatent")
    hit = _sample(rng, queries, rate)
    n = 0
    for q in hit:
        golds = [x.object for x in _sorted_quads(store, q.subject, ont("hasPriorArtExaminer"), None)]
        for g in golds[:1]:
            for prop in CONCEPT_PROPS:
                for c in _sorted_quads(store, g, ont(prop), None):
                    store.add(Quad(q.subject, ont(prop), c.object, q.graph_name))
                    n += 1
    return {"n_queries": len(hit), "n_links_added": n, "n_affected": len(hit)}


def f10_qrel_leak(store: Store, rate: float, rng: random.Random) -> dict:
    """누출 감사 표적 — 정답 인용 간선 자체를 **개념 링크로 위장**해 검색 피처에 복원한다.

    `hasPriorArtExaminer` 의 대상 문서를 `realizesProcess` 의 객체로 붙인다. 술어 이름 기반
    검사는 통과하므로, 이 결함을 잡으려면 "개념 자리에 문서가 들어왔는가"를 봐야 한다(G-1).
    """
    quads = _sorted_quads(store, None, ont("hasPriorArtExaminer"), None)
    hit = _sample(rng, quads, rate)
    for q in hit:
        store.add(Quad(q.subject, ont("realizesProcess"), q.object, q.graph_name))
    return {"n_candidates": len(quads), "n_affected": len(hit),
            "disguise": "hasPriorArtExaminer → realizesProcess"}


def f11_synonym_merge(store: Store, rate: float, rng: random.Random) -> dict:
    """**교차결함(T3 표적)** — 유사 Skill/Material 개념을 강제 병합.

    B 를 가리키던 모든 참조를 A 로 돌리고 B 의 자체 트리플을 지운다. 검색에는 무해하거나 오히려
    유리할 수 있다(개념 겹침이 늘어난다) — 그래서 T1 이 못 잡고 T3(전문가매칭 CQ)만 잡아야 한다.
    """
    merged = []
    for cls in ("Skill", "Material"):
        items = _subjects_of_type(store, cls)
        k = min(len(items) // 2, _n(rate, len(items)))
        pool = list(items)
        rng.shuffle(pool)
        for i in range(k):
            a, b = pool[2 * i].subject, pool[2 * i + 1].subject
            for q in _sorted_quads(store, None, None, b):        # 참조를 A 로 이전
                store.remove(q)
                store.add(Quad(q.subject, q.predicate, a, q.graph_name))
            for q in _sorted_quads(store, b, None, None):        # B 자체 소멸
                store.remove(q)
            merged.append({"class": cls, "kept": a.value, "removed": b.value})
    return {"n_merges": len(merged), "merges": merged, "n_affected": len(merged)}


def f12_hierarchy_inversion(store: Store, rate: float, rng: random.Random) -> dict:
    """**교차결함(T3 표적)** — 공유 계층의 부모–자식 역전(hasSubprocess 방향 뒤집기).

    상하위가 뒤집혀도 링크 수는 그대로라 구조 검증은 통과한다. 기술예측·전문가매칭 CQ 가
    계층 방향에 의존하면 T3 에서 걸린다.
    """
    quads = _sorted_quads(store, None, ont("hasSubprocess"), None)
    hit = _sample(rng, quads, rate)
    for q in hit:
        store.remove(q)
        store.add(Quad(q.object, q.predicate, q.subject, q.graph_name))
    return {"predicate": "hasSubprocess", "n_candidates": len(quads), "n_affected": len(hit)}


# --- 정상 델타 (위양성률 분모 · 결함이 아니다) --------------------------------
# 게이트가 **거부하면 안 되는** 변경이다. 여기서 거부가 나오면 그것이 위양성이다.

def n01_real_merge_subdelta(store: Store, rate: float, rng: random.Random) -> dict:
    """실제 병합 이력에서 온 무해 부분델타 — G₁ 에만 있는 트리플의 층화 부분집합을 G₀ 에 더한다.

    ⚠️ **T1·T2 에 대해서는 구조적으로 공허하다**(주입 전 실측으로 확인): 검색이 보는 뷰는
    G₀∪G₁∪G₂ 이고 이 트리플들은 **이미 G₁ 에 있다** — 합집합이 변하지 않으므로 성능층은
    아무것도 보지 못한다. 그래서 형식층(L0–L3·T3)의 위양성만 이 델타로 재고, 성능층은
    N02(의미보존 보강)로 잰다. 사전 설계(PLAN-020 §4-다)에서 이 공허성을 발견해 분모를
    둘로 나눴다 — 결과를 보고 바꾼 것이 아니다.
    """
    from .. import config as _c

    src = Store()
    with open(_c.GRAPH_V1, "rb") as fh:
        src.bulk_load(fh, format=RdfFormat.TURTLE)
    new_q = [q for q in src if not store.quads_for_pattern(q.subject, q.predicate, q.object, None)]
    new_q.sort(key=lambda q: (str(q.subject), str(q.predicate), str(q.object)))
    hit = _sample(rng, new_q, rate)
    for q in hit:
        store.add(Quad(q.subject, q.predicate, q.object))
    return {"source": "graph_v1 델타", "n_candidates": len(new_q), "n_affected": len(hit)}


def n02_label_preserving(store: Store, rate: float, rng: random.Random) -> dict:
    """의미보존 보강 — 기존 prefLabel 을 altLabel 로 복제한다(SDKB 가 실제로 하는 종류의 보강).

    의미를 바꾸지 않으므로 어느 층도 거부하면 안 된다. N01 과 달리 합집합에도 **새로운**
    트리플이라 T1·T2 가 실제로 판정에 참여한다.
    """
    quads = _sorted_quads(store, None, skos("prefLabel"), None)
    hit = _sample(rng, quads, rate)
    for q in hit:
        store.add(Quad(q.subject, skos("altLabel"), q.object, q.graph_name))
    return {"predicate": "skos:altLabel(복제)", "n_candidates": len(quads),
            "n_affected": len(hit)}


@dataclass(frozen=True)
class FaultSpec:
    key: str
    label: str          # 원고 §4.10 결함군 이름
    expected: str       # 원고가 예상한 검출층 (사전 예측 — 결과로 고치지 않는다)
    cross_task: bool    # H1 직접 검정 대상(교차결함)인가
    fn: object

    def inject(self, store: Store, rate: float, seed: int) -> dict:
        return self.fn(store, rate, random.Random(seed))


FAULTS: tuple[FaultSpec, ...] = (
    FaultSpec("F01", "신선도·무결성", "L0", False, f01_stale_artifact),
    FaultSpec("F02", "구조(필수 속성 누락)", "L1", False, f02_missing_required),
    FaultSpec("F03", "논리(순환·타입 모순)", "L2", False, f03_logic_contradiction),
    FaultSpec("F04", "기능(CQ 경로 삭제)", "L3", False, f04_cq_path_deleted),
    FaultSpec("F05", "의미 정렬 오류", "T1", False, f05_concept_misalignment),
    FaultSpec("F06", "계층 평탄화", "T1(+L3)", False, f06_hierarchy_flatten),
    FaultSpec("F07", "판단 문맥 치환", "T1·T2", False, f07_rejection_shuffle),
    FaultSpec("F08", "메타데이터 삭제", "T1(약)", False, f08_metadata_deleted),
    FaultSpec("F09", "시간 누출", "L0/누출감사", False, f09_temporal_leak),
    FaultSpec("F10", "qrel 누출", "누출감사", False, f10_qrel_leak),
    FaultSpec("F11", "동의어 오병합(교차)", "T3", True, f11_synonym_merge),
    FaultSpec("F12", "공유 계층 역전(교차)", "T3", True, f12_hierarchy_inversion),
)

NORMALS: tuple[FaultSpec, ...] = (
    FaultSpec("N01", "정상 델타(실제 병합 부분집합)", "none", False, n01_real_merge_subdelta),
    FaultSpec("N02", "정상 델타(의미보존 보강)", "none", False, n02_label_preserving),
)

BY_KEY = {f.key: f for f in FAULTS + NORMALS}


def seed_for(key: str, rate: float, rep: int) -> int:
    """(결함·강도·반복) → 고정 시드. 언제 돌려도 같은 결함 그래프가 나온다.

    파이썬 내장 `hash()` 는 프로세스마다 문자열 해시가 달라져(PYTHONHASHSEED) 재현이 깨진다 —
    sha256 을 쓴다.
    """
    h = hashlib.sha256(f"{key}|{rate:.4f}|{rep}".encode()).digest()
    return int.from_bytes(h[:4], "big")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="결함군 목록과 예상 검출층")
    args = ap.parse_args()
    if args.list:
        print(f"{'키':<5} {'결함군':<24} {'예상 검출층':<14} 교차")
        for f in FAULTS:
            print(f"{f.key:<5} {f.label:<24} {f.expected:<14} {'★' if f.cross_task else ''}")
        print()
        for f in NORMALS:
            print(f"{f.key:<5} {f.label:<24} {'(거부되면 위양성)':<14}")
        print(f"\n강도 {STRENGTHS} · n = max(1, round(rate·N))")


if __name__ == "__main__":
    main()
