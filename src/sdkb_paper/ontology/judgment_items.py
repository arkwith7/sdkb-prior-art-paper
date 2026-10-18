"""심사 이력 집계 정보 — 논증층에서 요소 유형별 집계를 파생한다 (PLAN-096 R6 · D3).

**이것은 최종 판단 지식이 아니다**(사용자 2026-10-17). 지금 만드는 것은 요소 유형별 **집계**뿐이고,
"원문 판단 근거 → 적용 가능한 요소·조건 → 참고할 검색 행동 → 적용 한계" 의 연결은 사례 카드(`case_cards`)로
확인한 뒤에만 지식으로 승격한다. 근거가 부족한 연결을 검색 규칙으로 만들지 않는다.

파생 규칙(결과 전 고정)
  원천     `config.PILOT_ARGUMENT_TTL`(별도 고정 자산) — 사용 술어는 `vendor_pilot.ALLOWED_PREDICATES` 만
  출원     판단이 가리키는 청구항 `rej_<출원번호>_c<n>` → 문서 `kr_<출원번호>`
  분리     **train 분할의 출원만** 쓴다 · 그 출원의 패밀리가 dev·test·test_b 질의의 패밀리와 겹치면 뺀다
  요소 유형 판단 대상 청구항의 한정요소 개념(`claim_features.feature_concept` · 주 스냅샷에 이미 있음)
  집계     요소 유형마다 — 판단 수 · 출원 수 · 근거(§29① 신규성 / §29② 진보성) 비율 · 범위(청구항 전체 /
           부가 한정) 비율 · 논거(설계변경 / 예측가능 효과) 비율 · 공지기술 의존 비율 ·
           인용 문헌 IPC 메인그룹 상위 5(비율)
  최소 지지 출원 수 ≥ MIN_APPLICATIONS 인 요소 유형만 항목이 된다
  넣지 않음 문헌 식별자 · 출원·통지서 식별자 · 인용 문헌 언어 분포(사용자 결정) · 좌표 · 판단 간 관계
A3·A4 는 이 함수가 만든 **같은 항목 파일**을 읽는다(`KnowledgeView`).
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from .. import config

MIN_APPLICATIONS = 5
TOP_IPC = 5
PA = "https://w3id.org/sdkb/ontology/priorart#"   # 술어 이름공간은 로컬 이름으로만 비교한다
LABEL = "심사 이력 집계 정보"


def _local(u) -> str:
    s = str(u)
    return s.rsplit("#", 1)[-1].rsplit("/", 1)[-1]


def extract_judgments(ttl: Path | None = None) -> list[dict]:
    """판단마다 구조 필드만 뽑는다. 쓰지 않는 술어(좌표·관계)는 읽지 않는다."""
    import rdflib

    g = rdflib.Graph()
    g.parse(str(ttl or config.PILOT_ARGUMENT_TTL), format="turtle")
    by_local = defaultdict(list)
    for s, p, o in g:
        by_local[_local(p)].append((s, o))
    jclaims, ground, scope, support = defaultdict(set), defaultdict(set), {}, {}
    for s, o in by_local["judgesClaim"]:
        jclaims[s].add(_local(o))
    for s, o in by_local["onGround"]:
        ground[s].add(_local(o))
    for s, o in by_local["judgmentScope"]:
        scope[s] = _local(o)
    for s, o in by_local["supportedBy"]:
        support[s] = o
    rat, ck, docs = defaultdict(set), {}, defaultdict(set)
    for s, o in by_local["hasRationale"]:
        rat[s].add(_local(o))
    for s, o in by_local["reliesOnCommonKnowledge"]:
        ck[s] = str(o).lower() == "true"
    for s, o in by_local["includesDocument"]:
        docs[s].add(str(o))
    out = []
    for j in sorted(jclaims, key=str):
        ev = support.get(j)
        apps = sorted({c.split("_")[1] for c in jclaims[j] if c.startswith("rej_")})
        out.append({"jid": hashlib.sha256(str(j).encode()).hexdigest()[:12],
                    "claims": sorted(jclaims[j]), "apps": [f"kr_{a}" for a in apps],
                    "ground": sorted(ground.get(j, ())), "scope": scope.get(j),
                    "rationale": sorted(rat.get(ev, ())), "common_knowledge": bool(ck.get(ev, False)),
                    "doc_iris": sorted(docs.get(ev, ()))})
    return out


def _main_group(code: str) -> str | None:
    from ..retrieval.boolean_emulator import norm_ipc

    n = norm_ipc(code)
    return n.split("/", 1)[0] if n else None


def build_items(judgments: list[dict]) -> tuple[dict, dict]:
    """(항목, 분리·계수 기록). 결정적 — 같은 입력이면 같은 sha."""
    import pandas as pd

    split = pd.read_parquet(config.IR_SPLIT, columns=["doc_id", "split", "family_id"])
    sp = dict(zip(split.doc_id, split.split))
    fam = dict(zip(split.doc_id, split.family_id))
    eval_fams = set(split.loc[split.split != "train", "family_id"])
    cf = pd.read_parquet(config.EXTERNAL_SDKB / "claim_features.parquet",
                         columns=["claim_id", "side", "feature_concept"])
    cf = cf[cf.side == "rej"]
    concepts_by_claim: dict[str, set] = defaultdict(set)
    for cid, fc in zip(cf.claim_id, cf.feature_concept):
        if fc is not None and len(fc):
            concepts_by_claim[cid].update(fc)
    corp = pd.read_parquet(config.IR_CORPUS, columns=["iri", "ipc"])
    ipc_by_iri = {i: [m for m in (_main_group(x) for x in (v if v is not None else [])) if m]
                  for i, v in zip(corp.iri, corp.ipc)}

    rec = Counter()
    agg: dict[str, dict] = defaultdict(lambda: {"j": 0, "apps": set(), "ground": Counter(), "scope": Counter(),
                                                "rat": Counter(), "ck": 0, "ipc": Counter(), "j_docs": 0})
    for j in judgments:
        rec["judgments"] += 1
        if not j["apps"] or any(sp.get(a) != "train" for a in j["apps"]):
            rec["dropped_not_train"] += 1
            continue
        if any(fam.get(a) in eval_fams for a in j["apps"]):
            rec["dropped_eval_family"] += 1
            continue
        cs = set().union(*(concepts_by_claim.get(c, set()) for c in j["claims"]))
        if not cs:
            rec["dropped_no_concept"] += 1
            continue
        rec["used"] += 1
        ipcs = sorted({m for d in j["doc_iris"] for m in ipc_by_iri.get(d, [])})
        for c in cs:
            a = agg[c]
            a["j"] += 1
            a["apps"].update(j["apps"])
            a["ground"].update(j["ground"])
            a["scope"][j["scope"]] += 1
            a["rat"].update(j["rationale"])
            a["ck"] += int(j["common_knowledge"])
            if ipcs:
                a["j_docs"] += 1
                a["ipc"].update(ipcs)
    items = {}
    for c in sorted(agg):
        a = agg[c]
        if len(a["apps"]) < MIN_APPLICATIONS:
            rec["concepts_below_support"] += 1
            continue
        n = a["j"]
        g = sum(a["ground"].values()) or 1
        items[c] = {
            "element_type": c, "judgments": n, "applications": len(a["apps"]),
            "ground_share": {"novelty_29_1": round(a["ground"].get("Ground_29_1", 0) / g, 3),
                             "inventive_step_29_2": round(a["ground"].get("Ground_29_2", 0) / g, 3)},
            "scope_share": {"whole_claim": round(a["scope"].get("ScopeWholeClaim", 0) / n, 3),
                            "added_limitation": round(a["scope"].get("ScopeAddedLimitation", 0) / n, 3)},
            "rationale_share": {"design_choice": round(a["rat"].get("RationaleDesignChoice", 0) / n, 3),
                                "predictable_effect": round(a["rat"].get("RationalePredictableEffect", 0) / n, 3)},
            "common_knowledge_share": round(a["ck"] / n, 3),
            "cited_ipc_main_groups": [{"ipc": k, "share": round(v / a["j_docs"], 3)}
                                      for k, v in sorted(a["ipc"].items(), key=lambda x: (-x[1], x[0]))[:TOP_IPC]],
        }
    rec["items"] = len(items)
    return items, dict(rec)


def items_sha(items: dict) -> str:
    return hashlib.sha256(json.dumps(items, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


class KnowledgeView:
    """한 질의에 보이는 항목 — A3 블록과 A4 도구가 **같은 내용**을 내도록 한 곳에서 만든다."""

    def __init__(self, items: dict, query_concepts):
        self.items = {c: items[c] for c in sorted(set(query_concepts)) if c in items}

    def list_types(self) -> dict:
        return {"element_types": [{"element_type": c, "applications": v["applications"]}
                                  for c, v in self.items.items()]}

    def history(self, element_type: str) -> dict:
        it = self.items.get(element_type)
        return {"label": LABEL, **it} if it else {"error": f"no examination history for {element_type!r}"}

    def block_text(self) -> str:
        if not self.items:
            return ""
        return "\n".join(json.dumps({"label": LABEL, **v}, ensure_ascii=False, sort_keys=True)
                         for v in self.items.values())

    def all_items(self) -> dict:
        """수정 A4 의 의무 최초 조회 응답 — A3 블록과 같은 항목 전부(빈 목록이면 항목 0)."""
        return {"label": LABEL, "element_types": [dict(v) for v in self.items.values()]}

    def content_set(self) -> set[str]:
        return {json.dumps(v, sort_keys=True, ensure_ascii=False) for v in self.items.values()}


def query_concepts(doc_id: str) -> set[str]:
    """질의 청구항 1항의 한정요소 개념(주 스냅샷 claim_features · 질의 자신의 판단은 쓰지 않는다)."""
    import pandas as pd

    cf = pd.read_parquet(config.EXTERNAL_SDKB / "claim_features.parquet",
                         columns=["claim_id", "side", "feature_concept"])
    cid = f"rej_{doc_id.split('_', 1)[1]}_c1"
    rows = cf[(cf.side == "rej") & (cf.claim_id == cid)]
    return {c for fc in rows.feature_concept if fc is not None for c in fc}


def case_cards(judgments: list[dict], items: dict, k: int = 4) -> list[dict]:
    """사례 카드 — 구조 필드만으로 연결을 적고, 원문 고리는 '사람 확인 필요' 로 남긴다.

    고르는 규칙(결과 전 고정): 사용된 train 판단 가운데 (§29②·설계변경) (§29②·예측가능 효과)
    (§29②·공지기술) (§29①) 네 칸에서 jid 사전순 첫 판단.
    """
    import pandas as pd

    split = pd.read_parquet(config.IR_SPLIT, columns=["doc_id", "split"])
    train = set(split.loc[split.split == "train", "doc_id"])
    cf = pd.read_parquet(config.EXTERNAL_SDKB / "claim_features.parquet",
                         columns=["claim_id", "side", "feature_concept"])
    cf = cf[cf.side == "rej"]
    cb = defaultdict(set)
    for cid, fc in zip(cf.claim_id, cf.feature_concept):
        if fc is not None and len(fc):
            cb[cid].update(fc)
    corp = pd.read_parquet(config.IR_CORPUS, columns=["iri", "ipc", "lang"])
    ipc_by_iri = {i: sorted({m for m in (_main_group(x) for x in (v if v is not None else [])) if m})
                  for i, v in zip(corp.iri, corp.ipc)}
    slots = [("29_2 · design_choice", lambda j: "Ground_29_2" in j["ground"] and "RationaleDesignChoice" in j["rationale"]),
             ("29_2 · predictable_effect", lambda j: "Ground_29_2" in j["ground"] and "RationalePredictableEffect" in j["rationale"]),
             ("29_2 · common_knowledge", lambda j: "Ground_29_2" in j["ground"] and j["common_knowledge"]),
             ("29_1 · novelty", lambda j: "Ground_29_1" in j["ground"])]
    pool = sorted((j for j in judgments if j["apps"] and all(a in train for a in j["apps"])), key=lambda j: j["jid"])
    cards = []
    for name, pred in slots[:k]:
        j = next((x for x in pool if pred(x) and any(cb.get(c) for c in x["claims"])), None)
        if j is None:
            cards.append({"slot": name, "found": False})
            continue
        cs = sorted(set().union(*(cb.get(c, set()) for c in j["claims"])))
        cited = [{"ipc_main_groups": ipc_by_iri.get(d, []), "in_corpus": d in ipc_by_iri} for d in j["doc_iris"]]
        cards.append({
            "slot": name, "found": True, "jid": j["jid"], "application": j["apps"], "claims": j["claims"],
            "ground": j["ground"], "scope": j["scope"], "rationale": j["rationale"],
            "common_knowledge": j["common_knowledge"], "n_cited": len(j["doc_iris"]), "cited": cited,
            "element_types": cs, "element_types_with_item": [c for c in cs if c in items],
            "link_1_original_rationale": "사람 확인 필요 — 통지서 원문(상류 결정 2026-10-09: LLM 전송 금지)",
            "link_2_applicable_elements": "구조 필드로만 — 판단 대상 청구항의 한정요소 개념(청구항 단위 · 요소 단위 아님)",
            "link_3_search_behavior": "미확정 — 근거 고리 1 확인 전에는 검색 규칙으로 만들지 않는다",
            "link_4_limits": "청구항 단위 결합이라 어느 요소가 어느 문헌에 대응했는지 모른다(좌표 FAIL 로 미사용)",
        })
    return cards


def main(argv=None) -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=config.PILOT_DIR / "judgment_items.json")
    a = ap.parse_args(argv)
    js = extract_judgments()
    items, rec = build_items(js)
    cards = case_cards(js, items)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    payload = {"label": LABEL, "status": "집계 정보 — 판단 지식으로 확정되지 않음(PLAN-096 D3)",
               "rule": {"min_applications": MIN_APPLICATIONS, "top_ipc": TOP_IPC, "split": "train only",
                        "family_exclusion": "dev·test·test_b 질의 패밀리"},
               "source_sha256": json.loads(config.PILOT_PROVENANCE.read_text(encoding="utf-8"))
               ["files"]["sdkb-abox-argument.ttl"]["sha256"] if config.PILOT_PROVENANCE.exists() else None,
               "counts": rec, "items_sha256": items_sha(items), "items": items}
    a.out.write_text(json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    (a.out.parent / "case_cards.json").write_text(json.dumps(cards, ensure_ascii=False, indent=1) + "\n",
                                                  encoding="utf-8")
    print(f"✓ {LABEL} {len(items)} 항목 · sha {items_sha(items)[:16]} · 계수 {rec}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
