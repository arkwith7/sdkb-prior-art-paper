"""선행기술 검색(IR) 시연 패널 — 뷰어에서 "온톨로지가 검색을 어떻게 바꾸는가"를 보인다.

**이 모듈은 새 실험을 하지 않는다.** M4에서 이미 산출된 것만 읽어 재구성한다:
- `runs/hybrid_b3_rrf.txt` (텍스트 기준선 B3) · `IR_CORPUS`(질의 원문·개념·IPC) ·
  `QREL_EXAMINER`(심사관 정답) · `IR_SPLIT`(분할) · `IR_FAMILY_MAP`(family 접기).
- 재랭크는 **실험과 같은 함수**(`analysis.ontology_eval.component_cache`/`rerank_from_cache`)를
  같은 동결 가중치(`SELECTED_ALPHA`/`SELECTED_W`)로 호출한다 — 화면 수치 = 논문 수치.

**봉인 규율(§1-3):** dev 분할만 노출한다. test 질의는 어떤 경로로도 반환하지 않는다.
FeatureCoverage(P1)는 유료 임베딩 캐시가 필요해 이 패널에서 제외한다 — P0★는 concept+ipc 이므로
표시되는 세 항(Concept·Path·Ipc)이 P0★ 점수의 입력 전량이다.

읽기 전용. 최초 요청 시 1회 적재·계산 후 프로세스 수명 동안 캐시한다(수십 초).
"""
from __future__ import annotations

from .. import config

SPLIT = "dev"          # 봉인 규율 — 이 값을 test 로 바꾸지 말 것
TOP_N = 20             # 나란히 보여줄 상위 순위 깊이
K_MAIN = 100           # 주지표 Recall@K (family 수준)


def _load_b3_for(qids: set[str]) -> dict[str, list[str]]:
    """B3 run 파일을 dev 질의만 남기고 스트리밍 적재(전량 적재 시 메모리 과다)."""
    from ..retrieval.hybrid import RUN_B3

    pairs: dict[str, list[tuple[int, str]]] = {}
    with open(RUN_B3, encoding="utf-8") as f:
        for line in f:
            p = line.split()
            if len(p) < 4 or p[0] not in qids:
                continue
            pairs.setdefault(p[0], []).append((int(p[3]), p[2]))
    return {q: [d for _, d in sorted(v)] for q, v in pairs.items()}


class IRDemo:
    """dev 질의에 대한 B3 vs P0★ 비교를 제공한다(1회 계산 후 상주)."""

    def __init__(self) -> None:
        import pandas as pd

        from ..analysis.metrics import load_qrel
        from ..analysis.ontology_eval import (
            SELECTED_ALPHA,
            SELECTED_W,
            component_cache,
            rerank_from_cache,
        )
        from ..collect.bq_family_ir import load_family_map
        from ..retrieval.candidate import CandidateMask
        from ..retrieval.ontology_rerank import OntologyFeatures

        self.alpha = SELECTED_ALPHA
        self.w = SELECTED_W

        sp = pd.read_parquet(config.IR_SPLIT)
        dev = set(sp.loc[sp["split"] == SPLIT, "doc_id"].astype(str))

        qrel_all = load_qrel()
        self.qrel = {q: p for q, p in qrel_all.items() if q in dev and p}
        self.fam = load_family_map()

        qids = sorted(self.qrel)
        self.feats = OntologyFeatures()
        mask = CandidateMask()
        b3 = _load_b3_for(set(qids))

        # 실험과 동일한 캐시·재랭크 — 여기서 수치가 갈리면 그것이 결함이다.
        self.cache = component_cache(self.feats, mask, b3, qids)
        self.run_b3 = rerank_from_cache(self.cache, 0.0, (1.0, 0.0, 0.0))
        self.run_p0 = rerank_from_cache(self.cache, self.alpha, self.w)

        # 코퍼스 경량 메타(텍스트 제외 — 원문은 요청 시 필터 조회)
        meta = pd.read_parquet(
            config.IR_CORPUS,
            columns=["doc_id", "title", "lang", "concepts", "ipc",
                     "filing_date", "publication_date"],
        )
        self.meta = {
            str(r.doc_id): {
                "title": r.title or "",
                "lang": r.lang or "",
                "concepts": _list(r.concepts),
                "ipc": _list(r.ipc),
                "filing_date": _date(r.filing_date),
                "publication_date": _date(r.publication_date),
            }
            for r in meta.itertuples(index=False)
        }

        # 질의 원문(청구항·초록)은 dev 질의 197건만 보관한다. 전 코퍼스 텍스트를 상주시키지 않고,
        # pyarrow `filters=` 로 지연 조회하지도 않는다 — 후자는 워커 스레드에서 segfault 한다.
        qset = set(qids)
        txt = pd.read_parquet(config.IR_CORPUS, columns=["doc_id", "abstract", "claims_independent"])
        txt = txt[txt["doc_id"].astype(str).isin(qset)]
        self.qtext = {
            str(r.doc_id): {
                "abstract": str(r.abstract or ""),
                "claims_independent": str(r.claims_independent or ""),
            }
            for r in txt.itertuples(index=False)
        }
        del txt

    # --- 지표 ------------------------------------------------------------
    def _recall(self, ranked: list[str], gold: set[str], k: int = K_MAIN) -> float:
        """family 수준 Recall@k (fold-then-cut — analysis.metrics 와 같은 규약)."""
        gold_f = {self.fam.get(d, d) for d in gold}
        seen, folded = set(), []
        for d in ranked:
            f = self.fam.get(d, d)
            if f not in seen:
                seen.add(f)
                folded.append(f)
        top = set(folded[:k])
        return len(top & gold_f) / len(gold_f) if gold_f else 0.0

    # --- API -------------------------------------------------------------
    def queries(self) -> dict:
        """dev 질의 목록 — 개선폭(Δ Recall@100) 내림차순."""
        rows = []
        for qid, gold in self.qrel.items():
            r_b3 = self._recall(self.run_b3.get(qid, []), gold)
            r_p0 = self._recall(self.run_p0.get(qid, []), gold)
            m = self.meta.get(qid, {})
            rows.append({
                "qid": qid,
                "title": m.get("title", ""),
                "n_gold": len(gold),
                "n_concepts": len(m.get("concepts", [])),
                "r100_b3": round(r_b3, 4),
                "r100_p0": round(r_p0, 4),
                "delta": round(r_p0 - r_b3, 4),
            })
        rows.sort(key=lambda r: (-r["delta"], -r["r100_p0"], r["qid"]))
        n_up = sum(1 for r in rows if r["delta"] > 0)
        n_dn = sum(1 for r in rows if r["delta"] < 0)
        return {
            "split": SPLIT, "k": K_MAIN, "alpha": self.alpha, "w": list(self.w),
            "n_queries": len(rows), "n_improved": n_up, "n_degraded": n_dn,
            "mean_b3": round(sum(r["r100_b3"] for r in rows) / max(len(rows), 1), 4),
            "mean_p0": round(sum(r["r100_p0"] for r in rows) / max(len(rows), 1), 4),
            "queries": rows,
        }

    def detail(self, qid: str, top_n: int = TOP_N) -> dict:
        """한 질의의 전 과정 — 질의 원문 · 항별 점수 · B3↔P0★ 순위 · 정답 이동."""
        if qid not in self.qrel:
            raise ValueError(f"dev 분할의 질의가 아니다(또는 정답 0건): {qid}")
        rows = self.cache.get(qid, [])
        wc, wh, wi = self.w
        terms = {
            d: {"text_norm": tn, "concept": c, "path": p, "ipc": ic,
                "ont": wc * c + wh * p + wi * ic,
                "score": (1.0 - self.alpha) * tn + self.alpha * (wc * c + wh * p + wi * ic)}
            for d, tn, c, p, ic in rows
        }
        rank_b3 = {d: i + 1 for i, d in enumerate(self.run_b3.get(qid, []))}
        rank_p0 = {d: i + 1 for i, d in enumerate(self.run_p0.get(qid, []))}
        gold = self.qrel[qid]
        qm = self.meta.get(qid, {})
        qcon = set(qm.get("concepts", []))

        def card(d: str) -> dict:
            m = self.meta.get(d, {})
            t = terms.get(d, {})
            return {
                "doc_id": d, "title": m.get("title", ""), "lang": m.get("lang", ""),
                "publication_date": m.get("publication_date", ""),
                "shared_concepts": sorted(qcon & set(m.get("concepts", []))),
                "ipc": m.get("ipc", [])[:6],
                "rank_b3": rank_b3.get(d), "rank_p0": rank_p0.get(d),
                "is_gold": d in gold,
                "concept": round(t.get("concept", 0.0), 4),
                "path": round(t.get("path", 0.0), 4),
                "ipc_sim": round(t.get("ipc", 0.0), 4),
                "text_norm": round(t.get("text_norm", 0.0), 4),
                "score": round(t.get("score", 0.0), 4),
            }

        texts = self.qtext.get(qid, {})
        return {
            "split": SPLIT, "k": K_MAIN, "alpha": self.alpha, "w": list(self.w),
            "pool_size": len(rows),
            "query": {
                "doc_id": qid, "title": qm.get("title", ""), "lang": qm.get("lang", ""),
                "filing_date": qm.get("filing_date", ""),
                "concepts": qm.get("concepts", []), "ipc": qm.get("ipc", []),
                "abstract": texts.get("abstract", ""),
                "claims_independent": texts.get("claims_independent", ""),
            },
            "r100_b3": round(self._recall(self.run_b3.get(qid, []), gold), 4),
            "r100_p0": round(self._recall(self.run_p0.get(qid, []), gold), 4),
            "top_b3": [card(d) for d in self.run_b3.get(qid, [])[:top_n]],
            "top_p0": [card(d) for d in self.run_p0.get(qid, [])[:top_n]],
            "gold": sorted(
                (card(d) for d in gold),
                key=lambda c: (c["rank_p0"] is None, c["rank_p0"] or 10**9),
            ),
        }


def _date(v) -> str:
    """결측 공개일(4,492건)은 빈 문자열로 — 'nan' 이 화면에 날짜처럼 보이면 안 된다."""
    s = str(v or "")[:10]
    return "" if s in ("", "nan", "NaT", "None") else s


def _list(v) -> list[str]:
    if v is None:
        return []
    return [str(x) for x in (v.tolist() if hasattr(v, "tolist") else v)]


_DEMO: IRDemo | None = None


def demo() -> IRDemo:
    global _DEMO
    if _DEMO is None:
        _DEMO = IRDemo()
    return _DEMO


def ready() -> bool:
    """필요한 산출물이 모두 있는가(없으면 탭을 비활성으로 안내)."""
    from ..retrieval.hybrid import RUN_B3

    return all(p.exists() for p in (RUN_B3, config.IR_CORPUS, config.QREL_EXAMINER,
                                    config.IR_SPLIT, config.IR_FAMILY_MAP))
