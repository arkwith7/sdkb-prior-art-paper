"""검색 시스템 조립 — B4·B5 독립팔 + P0★ 결합 재랭크 (PLAN-018 §3·§7.3 M4).

각 시스템 = run(순위) 생성 레시피. 텍스트 기준선(B0–B3)은 이미 bm25/dense/hybrid 가 만든다.
여기서는 온톨로지팔을 조립한다:

- **B4 (CPC/IPC):** IPC 접두 계층 유사도로 후보를 순위(IPC 주·CPC 희소). 독립 비교팔.
- **B5 (Ontology-only):** 개념겹침·경로만으로 순위(텍스트 0). 온톨로지팔의 정직한 회수 상한.
- **P0★ (결합 제안·ablation 기저):** B3 상위 풀을 `(1−α)·T̃ext + α·[w_c·Concept + w_h·Path + w_i·Ipc]`
  로 재랭크(M4-2). ablation 은 이 P0★ 에서 항/축을 끄고 ΔRecall 을 잰다(analysis/ablation).

- **경계(PLAN-018 §2):** run 만 만든다 — qrel 미열람. F10 후보 마스크(candidate)로 시점·family 위반 제거.
- **결정성(F16):** 동점은 doc_id 사전순으로 깬다.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .candidate import CandidateMask
from .ontology_rerank import OntologyFeatures, _query_features

# 축 그룹 (ablation A2/A3/A8 · 원고 §5.4). concept 어휘에 실재하는 클래스만.
AXES_PROCESS_DEVICE = frozenset({"Process", "SubProcess", "Device"})            # A2
AXES_MATERIAL_EQUIP_FAILURE = frozenset({"Material", "Equipment", "EquipmentClass",
                                         "EquipmentModel", "FailureMode"})       # A3
AXES_EXPERT = frozenset({"Skill"})                                              # A8 음성대조군
ALL_AXES = frozenset({"Process", "SubProcess", "Device", "Material", "Equipment",
                      "EquipmentClass", "EquipmentModel", "FailureMode", "Skill",
                      "RootCause", "Mitigation", "Parameter", "Metrology", "TechnologyNode"})

POOL_K = 1000   # B3 재랭크 풀 깊이 (P0★ 는 이 안에서 재정렬)


@dataclass(frozen=True)
class OntoConfig:
    """온톨로지 순위함수 구성 (P0★ + ablation 토글)."""
    alpha: float = 0.5            # 텍스트↔온톨로지 혼합
    w_c: float = 1.0              # ConceptOverlap
    w_h: float = 0.0              # PathSim
    w_i: float = 0.0              # IpcSim
    # PLAN-075 §12.1 — 관계 항 `w_r` 은 **신설**이다. 기존 `w_h`(축 Wu-Palmer)를 재활용하지
    # 않는 이유는 원고 §6 의 절제 A6 이 그 이름으로 판정을 기록했기 때문이다: 같은 이름 아래
    # 내용을 바꾸면 그 판정이 소급 오염된다.
    w_r: float = 0.0              # RelSim (개념 관계 그래프 · PLAN-075)
    w_f2: float = 0.0             # ProjCov (독립항 한정요소 투영 U2 · PLAN-075)
    keep_axes: frozenset = field(default=ALL_AXES)   # 개념 축 필터(A2/A3/A8)
    use_path: bool = True         # A6: False → 경로항 제거
    use_ipc: bool = True          # A1: False → 분류항 제거
    use_rel: bool = True          # False → 관계항 제거
    use_proj: bool = True         # False → 투영항 제거

    def label(self) -> str:
        """두 신설 항이 0 이면 **기존 문자열을 그대로** 낸다 — run 파일 경로가 바뀌면
        PLAN-075 §7 ⑤(가중 0 → 기존 P1 run 과 바이트 동일)가 경로에서부터 깨진다."""
        base = (f"a{self.alpha}_c{self.w_c}_h{self.w_h}_i{self.w_i}"
                f"_ax{len(self.keep_axes)}_p{int(self.use_path)}_i{int(self.use_ipc)}")
        if self.w_r:
            base += f"_r{self.w_r}"
        if self.w_f2:
            base += f"_f2{self.w_f2}"
        return base


def _filter_concepts(feats: OntologyFeatures, cs: frozenset[str], keep: frozenset) -> frozenset:
    if keep is ALL_AXES or keep == ALL_AXES:
        return cs
    return frozenset(c for c in cs if feats.axis.get(c, "") in keep)


def renormalize(weights: dict[str, float], available: dict[str, bool]) -> dict[str, float]:
    """측정 불가한 항을 **0 으로 채우지 않고 빼고**, 남은 가중에 그 몫을 비례 배분한다.

    왜 0 이 아닌가(PLAN-075 §12.2 · 사용자 승인) — dev 정답의 32.4 % 에 한정요소 투영이 없다.
    그 쌍에서 항을 0 으로 적으면 *"증거가 없다"* 가 *"나쁘다"* 로 바뀌어 정답 셋 중 하나가
    조용히 뒤로 밀린다. 출제되지 않은 문항을 0점 처리하지 않고 만점 기준에서 빼는 것과 같다.

    남는 항이 하나도 없으면(전부 결측) 원래 가중을 그대로 돌려준다 — 그 쌍은 어차피 전 항이
    0 이므로 재정규화가 순위를 바꾸지 않는다.
    """
    total = sum(weights.values())
    kept = {k: v for k, v in weights.items() if available.get(k, True)}
    s_kept = sum(kept.values())
    if not kept or s_kept <= 0 or total <= 0:
        return dict(weights)
    scale = total / s_kept
    return {k: (kept[k] * scale if k in kept else 0.0) for k in weights}


def _onto_score(feats: OntologyFeatures, qrow: int, drow: int, cfg: OntoConfig) -> float:
    """P0★ 온톨로지 항 = w_c·Concept + w_h·Path + w_i·Ipc (구성별 토글)."""
    qc = _filter_concepts(feats, feats.concepts[qrow], cfg.keep_axes)
    dc = _filter_concepts(feats, feats.concepts[drow], cfg.keep_axes)
    # 관계 항(§12.2)은 측정 불가할 때 0 이 아니라 재정규화로 빠진다. 두 신설 가중이 0 이면
    # `renormalize` 는 항등이므로 기존 P0★ 점수는 바이트 단위로 보존된다.
    w = {"c": cfg.w_c, "h": cfg.w_h if cfg.use_path else 0.0,
         "i": cfg.w_i if cfg.use_ipc else 0.0, "r": cfg.w_r if cfg.use_rel else 0.0}
    if w["r"]:
        w = renormalize(w, {"r": feats.has_rel(qc) and feats.has_rel(dc)})
    s = 0.0
    if w["c"]:
        s += w["c"] * feats.concept_overlap(qc, dc)
    if w["h"]:
        s += w["h"] * feats.path_sim(qc, dc)
    if w["i"]:
        s += w["i"] * feats.ipc_sim(feats.ipc[qrow], feats.ipc[drow])
    if w["r"]:
        s += w["r"] * feats.rel_sim(qc, dc)
    return s


# --- P0★ 재랭크 (B3 풀) -----------------------------------------------------
def rerank_p0(
    base_run: dict[str, list[str]],
    feats: OntologyFeatures,
    mask: CandidateMask,
    cfg: OntoConfig,
    pool_k: int = POOL_K,
    k: int = 1000,
) -> dict[str, list[str]]:
    """B3 상위 pool_k 를 P0★ 점수로 재랭크. 새 문서 도입 없음(§3.1 재랭크 의미)."""
    qrows = _query_features(feats)
    out: dict[str, list[str]] = {}
    for qid, ranked in base_run.items():
        qrow = qrows.get(qid)
        # F10 마스크 후 상위 pool_k 만 재랭크 대상
        pool = [d for d in ranked if mask.is_allowed(qid, d)][:pool_k]
        m = len(pool)
        if qrow is None or m == 0:
            out[qid] = pool[:k]
            continue
        scored = []
        for rank0, d in enumerate(pool):
            drow = feats.row.get(d)
            text_norm = 1.0 - (rank0 / (m - 1)) if m > 1 else 1.0   # 선형 rank-norm [0,1]
            ont = _onto_score(feats, qrow, drow, cfg) if drow is not None else 0.0
            s = (1.0 - cfg.alpha) * text_norm + cfg.alpha * ont
            scored.append((s, d))
        scored.sort(key=lambda x: (-x[0], x[1]))     # 동점 doc_id 사전순(F16)
        out[qid] = [d for _, d in scored[:k]]
    return out


# --- B4 IPC/CPC 독립팔 ------------------------------------------------------
def build_b4(
    feats: OntologyFeatures, mask: CandidateMask,
    qids: list[str] | None = None, k: int = 1000,
) -> dict[str, list[str]]:
    """IPC 접두 계층 유사도로 후보 순위(독립팔). 후보 = IPC 접두 공유 ∩ D_q."""
    qrows = _query_features(feats)
    targets = qids or list(qrows)
    out: dict[str, list[str]] = {}
    for qid in targets:
        qrow = qrows.get(qid)
        if qrow is None:
            out[qid] = []
            continue
        q_ipc = feats.ipc[qrow]
        cand = feats.ipc_candidates(q_ipc)
        scored = []
        for drow in cand:
            d = feats.doc_ids[drow]
            if not mask.is_allowed(qid, d):
                continue
            s = feats.ipc_sim(q_ipc, feats.ipc[drow])
            if s > 0:
                scored.append((s, d))
        scored.sort(key=lambda x: (-x[0], x[1]))
        out[qid] = [d for _, d in scored[:k]]
    return out


# --- B5 Ontology-only 독립팔 ------------------------------------------------
def build_b5(
    feats: OntologyFeatures, mask: CandidateMask, cfg: OntoConfig | None = None,
    qids: list[str] | None = None, k: int = 1000,
) -> dict[str, list[str]]:
    """개념겹침(+경로)만으로 순위(텍스트 0). 후보 = 개념 정확공유 ∩ D_q."""
    cfg = cfg or OntoConfig(alpha=1.0, w_c=1.0, w_h=0.0, w_i=0.0, use_ipc=False)
    qrows = _query_features(feats)
    targets = qids or list(qrows)
    out: dict[str, list[str]] = {}
    for qid in targets:
        qrow = qrows.get(qid)
        if qrow is None:
            out[qid] = []
            continue
        qc_all = feats.concepts[qrow]
        cand = feats.concept_candidates(qc_all)
        scored = []
        for drow in cand:
            d = feats.doc_ids[drow]
            if not mask.is_allowed(qid, d):
                continue
            s = _onto_score(feats, qrow, drow, cfg)
            if s > 0:
                scored.append((s, d))
        scored.sort(key=lambda x: (-x[0], x[1]))
        out[qid] = [d for _, d in scored[:k]]
    return out
