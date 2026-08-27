"""그림 라벨의 단일 원천 — 한국어와 영문을 한 자리에서 잇는다 (PLAN-082 · 그림 규격 F-v1).

**왜 이 모듈이 있는가.** 개념 도식의 글자는 그리기 코드 안에 한국어 리터럴로 박혀 있었다.
영문 투고본은 같은 그림을 영어로 요구하는데, 그리기 코드를 복제하면 **두 벌이 되어 다음
재측정에서 한쪽만 갱신된다.** 그래서 그리기 코드는 한 벌로 두고 **글자만 이 표에서 읽는다** —
`build_submission_en.py` 의 `TERMS`·`CELLS`·`CAPTIONS` 가 표·캡션에 대해 하는 일과 같다.

**항목은 문자열이 아니라 템플릿이다.** 라벨의 30 %가 수치를 보간하기 때문이다(실측: 한글
리터럴 189개 중 f-string 57개). 자리표시자는 `{키}` 이고 값은 `figdata.load()` 가 동결
JSON 에서 읽어 온다 — **수치는 이 표에도 코드에도 손으로 적히지 않는다**(CLAUDE.md §1-1 ·
규격 F6).

    T("overview.a1_title")                      → 현재 언어의 라벨
    T("layer.resource_body")                    → `{ep3.concepts_per_doc.before}` 등이 채워진다

**형식 지정자 셋만 쓴다.** `{키}` 그대로 · `{키:.4f}` 파이썬 형식 · `{키:sig}` 부호 명시
소수(본문 표기와 같은 유니코드 마이너스). 그 밖의 가공은 여기서 하지 않는다 — 가공이 늘면
표가 코드가 되고, 그러면 두 언어가 다시 갈린다.

**언어는 모듈 상태다.** 그림은 한 번에 한 언어로 생성되므로(`--lang`) 호출부 189곳에 인자를
꿰는 것보다 상태 하나가 정직하다. `set_lang()` 은 진입점에서만 부른다.
"""
from __future__ import annotations

import re
from typing import Any

from sdkb_paper.viz import figdata

LANGS = ("ko", "en")
_lang = "ko"
_values: dict[str, Any] | None = None

_PLACEHOLDER = re.compile(r"\{([a-z0-9_.]+)(?::([^}]*))?\}")


def set_lang(lang: str) -> None:
    if lang not in LANGS:
        raise ValueError(f"알 수 없는 언어: {lang} (허용: {LANGS})")
    global _lang
    _lang = lang


def lang() -> str:
    return _lang


def _sig(v: float, nd: int = 4) -> str:
    """부호를 명시한 소수 표기. 음수는 유니코드 마이너스로 — 본문 표기와 같게 맞춘다."""
    s = f"{abs(v):.{nd}f}"
    return f"+{s}" if v >= 0 else f"−{s}"


def values() -> dict[str, Any]:
    """동결 수치 + 파생값. 파생은 **여기 한 자리**에만 둔다 — 그림마다 계산하면 갈린다."""
    global _values
    if _values is None:
        v = dict(figdata.load())
        v["ep3.ratio"] = v["ep3.concepts_per_doc.after"] / v["ep3.concepts_per_doc.before"]
        v["cq.t3_total"] = v["cq.em"] + v["cq.tf"] + v["cq.core"]
        v["ceiling.pool_pct"] = v["ceiling.pool_ratio"] * 100
        v["ep3.t3_suites_head"] = str(v["ep3.t3_suites"]).split("—")[0].strip()
        _values = v
    return _values


def render(template: str, **extra: Any) -> str:
    """템플릿의 자리표시자를 동결 수치로 채운다."""
    src = values()

    def sub(m: re.Match[str]) -> str:
        key, spec = m.group(1), m.group(2)
        if key in extra:
            val = extra[key]
        elif key in src:
            val = src[key]
        elif key in MARKS:
            return MARKS[key][_lang]
        else:
            raise KeyError(f"라벨 템플릿의 자리표시자를 찾을 수 없다: {{{key}}}")
        if spec == "sig":
            return _sig(float(val))
        return format(val, spec) if spec else str(val)

    return _PLACEHOLDER.sub(sub, template)


def ko_of(key: str, **extra: Any) -> str:
    """같은 슬롯의 **한국어** 라벨. 상자가 없는 자리에서 폭의 경계로 쓴다 —
    한국어판이 눈으로 검수를 마친 동결 기준선이므로, 영문은 그 폭을 넘지 않아야 한다."""
    return render(LABELS[key]["ko"], **extra)


def T(key: str, **extra: Any) -> str:
    """현재 언어의 라벨을 동결 수치로 채워 돌려준다."""
    if key not in LABELS:
        raise KeyError(f"라벨 표에 없는 키: {key}")
        # 키를 지어내지 않는다 — 없는 키는 표에 먼저 등재한다.
    entry = LABELS[key]
    if _lang not in entry:
        raise KeyError(f"라벨 {key} 에 '{_lang}' 이 없다")
    return render(entry[_lang], **extra)


# ═══════════════════════════════════════════════════════════════════════════
# 추출 칸의 번역 — 그림 3 전용 (PLAN-082 §3.5-③)
# ═══════════════════════════════════════════════════════════════════════════
# 그림 3 은 S5 표 3 의 **한국어 칸을 기계로 추출해** 그린다(`figdata` 의 `cast="cells"`).
# 영문판에는 추출할 원천이 없다 — supplementary 는 감사 기록이라 영문화 대상이 아니다
# (CLAUDE.md §8.1). 그러므로 이 셋만은 **번역**이며, `build_submission_en.py` 의 `CELLS`
# 와 같은 형태를 쓴다: **한국어 칸 전체를 키로 하는 완전 일치 치환.**
#
# 조립기의 `CELLS` 를 그대로 공유하지 못한 이유는 실측이다 — 겹치는 항이 **0개**다.
# 표 3 은 파생본에서 그림 3 으로 대체되어 조립기가 그 칸을 다룰 일이 없었기 때문이다.
# 그래서 복제하되 **두 표의 교집합이 어긋나면 실패시킨다**(`tests/test_figure_labels.py`).
CELL_TRANSLATIONS: dict[str, str] = {
    "전문가 매칭": "Expert matching",
    "선행기술조사": "Prior-art search",
    "기술예측": "Technology foresight",
    "비식별·생성 인스턴스": "De-identified·synthetic instances",
    "거절특허 1,000 · 심사관 인용 2,534 · claim sidecar":
        "1,000 rejected patents · 2,534 examiner citations · claim sidecar",
    "G1·G2 시계열": "G1·G2 time series",
    "표현 타당성 + **음성 대조군**(§5.12) · 성능 미평가":
        "Representational validity + **negative control** · performance not evaluated",
    "**주 정량 검증** (Recall@K·nDCG·게이트)":
        "**Primary quantitative validation** (Recall@K·nDCG·gate)",
    "2차 재사용 증거 (§7.4)": "Evidence of secondary reuse",
    # 역량질문 번호 칸 — 번호는 라벨이라 옮기지 않고 괄호의 한국어만 옮긴다.
    "09·10·22·27 (+29–31 측정)": "09·10·22·27 (+29–31 measurement)",
    "01–08·23–26": "01–08·23–26",
    "11·12·15–18·20·28": "11·12·15–18·20·28",
}


def cell(raw: str) -> str:
    """추출한 칸을 현재 언어로. 표에 없는 한글 칸은 **조용히 지나가지 않는다.**"""
    if _lang == "ko":
        return raw
    if raw in CELL_TRANSLATIONS:
        return CELL_TRANSLATIONS[raw]
    if re.search(r"[가-힣]", raw):
        raise KeyError(f"번역되지 않은 추출 칸: {raw!r} — CELL_TRANSLATIONS 에 등재할 것")
    return raw


# ═══════════════════════════════════════════════════════════════════════════
# 판정 기호 — 그림 안에서 색보다 앞서는 부호다 (규격 F1 · 단색 인쇄 안전)
# ═══════════════════════════════════════════════════════════════════════════
MARKS: dict[str, dict[str, str]] = {
    "mark.pass": {"ko": "통과", "en": "Pass"},
    "mark.fail": {"ko": "거부", "en": "Reject"},
    "mark.none": {"ko": "·", "en": "·"},
    "mark.obs": {"ko": "감사", "en": "Audit"},
    "mark.unconf": {"ko": "미확증", "en": "Not confirmed"},
}


# ═══════════════════════════════════════════════════════════════════════════
# 라벨 표 — 키는 `<그림>.<슬롯>`
# ═══════════════════════════════════════════════════════════════════════════
# **산출물 라벨은 두 언어가 같다 — `ART-1`·`ART-2`·`E1` (2026-08-27 · 사용자 승인).**
# 구 표기 `A1`·`A2` 는 **절제 조건 `A1`–`A8` 과 기호가 겹쳐** 같은 기호가 산출물과 절제를
# 동시에 가리켰다 — 같은 사고로 폐기된 S-시리즈의 경로다. 영문은 외부 교정이 먼저 풀었고
# (2026-08-26) 국문을 그다음 날 맞췄다. 셋째 띠는 그림만 `A3` 이라 부르고 본문은 `E1` 이라
# 불러 온 **기존 불일치**였으며 이때 함께 해소했다.
LABELS: dict[str, dict[str, str]] = {
    # 공통 ───────────────────────────────────────────────────────────────────
    "common.status_prefix": {"ko": "지위 · {status}", "en": "Status · {status}"},

    # ── 그림 1 · 연구 개요도 ─────────────────────────────────────────────────
    "overview.a1_title": {
        "ko": "ART-1 · SDKB 데이터셋 — 공유 T-Box 하나 위의 세 태스크 뷰",
        "en": "ART-1 · SDKB dataset — three task views on one shared T-Box"},
    "overview.core_head": {"ko": "공유 코어 어휘", "en": "Shared core vocabulary"},
    "overview.core_body": {
        "ko": "Process · Material · Equipment · Organization · 분류기호",
        "en": "Process · Material · Equipment · Organization · classification"},
    "overview.view_match": {"ko": "전문가 매칭", "en": "Expert matching"},
    "overview.view_priorart": {"ko": "선행기술조사", "en": "Prior-art search"},
    "overview.view_foresight": {"ko": "기술예측", "en": "Foresight"},
    "overview.quant_target": {"ko": "정량 검증 대상", "en": "Quantitatively validated"},
    "overview.delta_title": {"ko": "자원 변경 ΔG", "en": "Resource change ΔG"},
    "overview.delta_body": {
        "ko": "상류 교정 · 어휘 확장\n새 A-Box 유입",
        "en": "Upstream fix · vocabulary\nnew A-Box"},
    "overview.a2_title": {
        "ko": "ART-2 · 릴리스 승인 게이트 — 앞 단계가 실패하면 뒤를 실행하지 않는다",
        "en": "ART-2 · Release acceptance gate — a failed stage stops the ones behind it"},
    "overview.stage_l0l3": {"ko": "L0–L3", "en": "L0–L3"},
    "overview.stage_l0l3_body": {
        "ko": "신선도 · 구조 · 논리\n주 태스크 CQ",
        "en": "Freshness · structure\nlogic · primary CQ"},
    "overview.stage_index": {"ko": "누출 차단 색인", "en": "Leakage-blocked index"},
    "overview.stage_index_body": {
        "ko": "금지 간선 마스킹\n시점 · 패밀리 분리",
        "en": "Edge masking\ntime · family split"},
    "overview.stage_t12": {"ko": "T1 · T2", "en": "T1 · T2"},
    "overview.stage_t12_body": {
        "ko": "검색 비열등성\n하위집단 안전성",
        "en": "Non-inferiority\nsubgroup safety"},
    "overview.stage_t3": {"ko": "T3", "en": "T3"},
    "overview.stage_t3_body": {
        "ko": "다른 태스크 CQ\n비회귀", "en": "Other tasks' CQ\nnon-regression"},
    "overview.stage_verdict": {"ko": "판정", "en": "Verdict"},
    "overview.stage_verdict_body": {"ko": "승인\n또는 거부", "en": "Accept\nor reject"},
    "overview.t4_note": {
        "ko": "T4 · 하류 생성 층 비회귀 — 설계와 판정 1회 · 승인식 미편입",
        "en": "T4 · Downstream generation non-regression — designed, one verdict, not in the rule"},
    "overview.a3_title": {
        "ko": "E1 · 다층 평가 벤치마크 — 다섯 평가 에피소드와 각각의 측정 대상",
        "en": "E1 · Multi-layer benchmark — five episodes and what each measures"},
    "overview.ep_target": {"ko": "측정 대상 · {target}", "en": "Measures · {target}"},
    "overview.ep1_title": {"ko": "EP1 · 표현 감사", "en": "EP1 · Representation audit"},
    "overview.ep1_target": {"ko": "ART-1 자원", "en": "ART-1 resource"},
    "overview.ep1_body": {
        "ko": "세 태스크 어휘와 CQ 가\n자원에 실재하는가",
        "en": "Are the three task vocabularies\nand CQs present in the resource"},
    "overview.ep2_title": {"ko": "EP2 · 게이트 판별력", "en": "EP2 · Gate discrimination"},
    "overview.ep2_target": {"ko": "ART-2 게이트", "en": "ART-2 gate"},
    "overview.ep2_body": {
        "ko": "홀드아웃 결함 {ep2.t3_only} 를 T3 가 단독 검출\n"
              "정상 델타 오거부 {ep2.false_positive}",
        "en": "T3 alone detects {ep2.t3_only} holdout faults\n"
              "false rejections {ep2.false_positive}"},
    "overview.ep3_title": {"ko": "EP3 · 통제된 자원 교체", "en": "EP3 · Resource substitution"},
    "overview.ep3_target": {"ko": "ΔG → ART-2 판정", "en": "ΔG → ART-2 verdict"},
    "overview.ep3_body": {
        "ko": "자원만 교체 → T1 {mark.fail}\n승인 = 0",
        "en": "Resource only → T1 {mark.fail}\nAccept = 0"},
    "overview.ep4_title": {"ko": "EP4 · 검색 이득의 범위", "en": "EP4 · Scope of the gain"},
    "overview.ep4_target": {"ko": "T1 의 주 지표", "en": "Primary metric of T1"},
    "overview.ep4_body": {
        "ko": "질의 {ep4.n_queries} · 확증 분할 둘\nfamily Recall@100",
        "en": "{ep4.n_queries} queries · two splits\nfamily Recall@100"},
    "overview.ep5_title": {"ko": "EP5 · 제2 자원 이식", "en": "EP5 · Port to a 2nd resource"},
    "overview.ep5_target": {
        "ko": "ART-2 절차의 자원 비의존성", "en": "ART-2 · resource independence"},
    "overview.ep5_body": {
        "ko": "형식 층·T3 코드 변경 없이 실행\n"
              "관찰면 {ep5.observable}/{ep5.cq_total} · 명세 재접지 필요",
        "en": "Formal layers and T3 ran\nunchanged · surface "
              "{ep5.observable}/{ep5.cq_total}\nspecification regrounded"},
    # ── 그림 2 · 층간 지표 불일치 ────────────────────────────────────────────
    "layer.tag_resource": {"ko": "자원 층", "en": "Resource layer"},
    "layer.tag_retrieval": {"ko": "검색 층", "en": "Retrieval layer"},
    "layer.tag_generation": {"ko": "생성 층", "en": "Generation layer"},
    "layer.title_resource": {"ko": "자원 지표", "en": "Resource indicators"},
    "layer.title_retrieval": {"ko": "검색 지표", "en": "Retrieval metrics"},
    "layer.title_generation": {"ko": "생성 지표", "en": "Generation metrics"},
    "layer.body_resource": {
        "ko": "문서당 개념 {ep3.concepts_per_doc.before} → {ep3.concepts_per_doc.after}"
              " ({ep3.ratio:.1f}배)\n"
              "개념 어휘 {ep3.concept_vocab.before} → {ep3.concept_vocab.after}\n"
              "형식 검증 L0–L3 전부 {mark.pass}",
        "en": "Concepts per document {ep3.concepts_per_doc.before} →"
              " {ep3.concepts_per_doc.after} ({ep3.ratio:.1f}×)\n"
              "Concept vocabulary {ep3.concept_vocab.before} → {ep3.concept_vocab.after}\n"
              "L0–L3 all {mark.pass}"},
    "layer.body_retrieval": {
        "ko": "family Recall@100 (부차 구성)\n"
              "{ep4.p1_gain.delta:sig} [{ep4.p1_gain.lb95:sig}, {ep4.p1_gain.ub95:sig}]\n"
              "질의 {ep4.n_queries} · 확증 분할",
        "en": "family Recall@100 (secondary)\n"
              "{ep4.p1_gain.delta:sig} [{ep4.p1_gain.lb95:sig}, {ep4.p1_gain.ub95:sig}]\n"
              "{ep4.n_queries} queries · confirmatory split"},
    "layer.body_generation": {
        "ko": "인용 정확도 · 환각률\n검색팔만 교체 · 생성기 고정\n마진 ε = {t4.eps} 사전 동결",
        "en": "Citation accuracy · hallucination\nRetrieval arm only · generator fixed\n"
              "Margin ε = {t4.eps} frozen"},
    "layer.arrow_1": {
        "ko": "다음 층에서 승인 여부를 확인한다",
        "en": "Acceptance is decided at the next layer"},
    "layer.arrow_3": {
        "ko": "다음 층으로 전달되는지 확인한다",
        "en": "Whether it transfers to the next layer"},
    "layer.obs1_head": {
        "ko": "자원 지표 개선 · 검색 지표 저하",
        "en": "Resource indicators up · retrieval down"},
    "layer.obs1_body": {
        "ko": "자원만 교체한 두 팔에서 교체 대상 구성의 회수가 저하되었다.\n"
              "ΔRecall@100 = {ep3.p1.delta:sig} · 95% CI "
              "[{ep3.p1.ci_lo:sig}, {ep3.p1.ci_hi:sig}] → T1 {mark.fail} · 승인 = 0\n"
              "온톨로지 단독 팔은 오히려 향상되었다 "
              "({ep3.b5.before:.4f} → {ep3.b5.after:.4f}) — 원인은 미구분",
        "en": "With only the resource replaced, recall of the substituted configuration fell.\n"
              "ΔRecall@100 = {ep3.p1.delta:sig} · 95% CI "
              "[{ep3.p1.ci_lo:sig}, {ep3.p1.ci_hi:sig}] → T1 {mark.fail} · Accept = 0\n"
              "The ontology-only arm improved "
              "({ep3.b5.before:.4f} → {ep3.b5.after:.4f}) — cause not separated"},
    "layer.obs1_status": {
        "ko": "개봉 분할 · 승인 규칙의 적용",
        "en": "Unsealed split · acceptance rule applied"},
    "layer.obs2_head": {
        "ko": "주 지표 개선 · 검토 건수 불변",
        "en": "Primary metric up · review count flat"},
    "layer.obs2_body": {
        "ko": "같은 이득을 검토 건수 단위로 환산하면 중앙 감소율이 "
              "{effort.median_reduction_pct:.1f}%이다.\n"
              "질의별 승·무·패는 {effort.win_tie_loss}로 균형에 가깝다.\n"
              "재순위화는 후보 풀 밖의 문헌을 회수하지 못한다.",
        "en": "Converted into documents reviewed, the median reduction is "
              "{effort.median_reduction_pct:.1f}%.\n"
              "Win/tie/loss per query is {effort.win_tie_loss}, close to balanced.\n"
              "Reranking cannot recover documents outside the candidate pool."},
    "layer.obs2_status": {"ko": "탐색적 기술통계", "en": "Exploratory descriptive"},
    "layer.obs3_head": {
        "ko": "점추정의 우위 · 비열등 판정의 실패",
        "en": "Point estimate ahead · non-inferiority not met"},
    "layer.obs3_body": {
        "ko": "인용 정확도의 점추정은 온톨로지를 포함한 팔이 앞섰다"
              "({t4.citation_precision.delta:sig}).\n"
              "그러나 95% CI 하한이 {t4.citation_precision.lb95:sig} 로 마진 "
              "−{t4.eps} 를 초과하여 T4 판정은 실패이다.\n"
              "전달의 부재인지 검정력의 부족인지는 미구분이다.",
        "en": "On citation accuracy the arm with the ontology led on the point estimate "
              "({t4.citation_precision.delta:sig}).\n"
              "The 95% CI lower bound {t4.citation_precision.lb95:sig} passed the margin "
              "−{t4.eps}, so the T4 verdict failed.\n"
              "Absence of transfer is not distinguished from insufficient power."},
    "layer.obs3_status": {"ko": "확증 · 판정 1회", "en": "Confirmatory · one verdict"},
    "layer.conclusion": {
        "ko": "세 관측을 관통하는 명제 — 자원 지표가 개선되고 형식 검증을 통과한 변경도 "
              "다음 층의 성능을 보장하지 않는다.",
        "en": "One proposition runs through all three — a change that improves resource "
              "indicators and passes formal validation does not guarantee the next layer."},
    # ── 그림 3 · 공유 T-Box와 세 태스크 뷰 ───────────────────────────────────
    "tbox.cq_prefix": {"ko": "대표 역량질문 · {cq}", "en": "Representative CQ · {cq}"},
    "tbox.abox_prefix": {"ko": "A-Box · {abox}", "en": "A-Box · {abox}"},
    "tbox.status_head": {"ko": "본 논문의 지위", "en": "Status in this paper"},
    "tbox.channel_title": {
        "ko": "교차 태스크 결합 통로 — 공유 어휘가 두 뷰를 잇는다",
        "en": "Cross-task coupling channels — shared vocabulary joins two views"},
    "tbox.channel_class": {"ko": "분류 기호", "en": "Classification symbols"},
    "tbox.core_title": {
        "ko": "공유 코어 T_core — 세 뷰가 함께 서는 자리",
        "en": "Shared core T_core — where the three views meet"},
    "tbox.core_counts": {
        "ko": "게이트가 관찰하는 역량질문 {cq.total}개 — 주 태스크 {cq.pa} · "
              "전문가 매칭 {cq.em} · 기술예측 {cq.tf} · 공유 코어 {cq.core}",
        "en": "{cq.total} competency questions observed by the gate — primary task {cq.pa} · "
              "expert matching {cq.em} · foresight {cq.tf} · shared core {cq.core}"},
    "tbox.core_note": {
        "ko": "둘 이상의 뷰를 잇는 역량질문은 공유 코어에 귀속한다",
        "en": "A question joining two or more views belongs to the shared core"},

    # ── 그림 4 · T-gate 절차와 실제 판정 ─────────────────────────────────────
    "gate.col_procedure": {"ko": "승인 절차", "en": "Acceptance procedure"},
    "gate.col_unmet": {"ko": "미충족 시의 처리", "en": "Handling when unmet"},
    "gate.col_verdict": {
        "ko": "통제된 자원 교체에서의 판정",
        "en": "Verdict in the controlled substitution"},
    "gate.row_delta": {"ko": "자원 변경 ΔG", "en": "Resource change ΔG"},
    "gate.row_formal": {
        "ko": "L0–L3 · 형식·기능 검증\n주 태스크 역량질문 {cq.pa}개",
        "en": "L0–L3 · formal and functional\n{cq.pa} primary-task questions"},
    "gate.rule_formal": {
        "ko": "최신 상태·구조 제약·논리 일관·필수 응답 가운데\n하나라도 어긋나면 즉시 거부",
        "en": "Freshness, structure, logic or required response —\nany one unmet rejects at once"},
    "gate.detail_formal": {"ko": "전부 통과", "en": "All passed"},
    "gate.row_index": {"ko": "누출 차단 검색 색인", "en": "Leakage-blocked index"},
    "gate.rule_index": {
        "ko": "금지 간선 마스킹·시점 유효·패밀리 분리.\n누출 감사가 0이 아니면 T1 판정은 무효이다",
        "en": "Edge masking, time validity, family separation.\n"
              "A non-zero leakage audit voids the T1 verdict"},
    "gate.detail_index": {"ko": "위반 0", "en": "0 violations"},
    "gate.row_t1": {"ko": "T1 · 검색 비열등성", "en": "T1 · Retrieval non-inferiority"},
    "gate.rule_t1": {
        "ko": "회수의 95% 신뢰구간 하한이 허용 폭 ε = {gate.epsilon} 를\n초과하여 저하되면 거부",
        "en": "Reject if the 95% CI lower bound of recall falls\nbeyond the margin ε = {gate.epsilon}"},
    "gate.detail_t1": {
        "ko": "ΔRecall@100 {ep3.p1.delta:sig} · 95% CI [{ep3.p1.ci_lo:sig}, {ep3.p1.ci_hi:sig}]",
        "en": "ΔRecall@100 {ep3.p1.delta:sig} · 95% CI [{ep3.p1.ci_lo:sig}, {ep3.p1.ci_hi:sig}]"},
    "gate.row_t2": {"ko": "T2 · 하위집단 안전성", "en": "T2 · Subgroup safety"},
    "gate.rule_t2": {
        "ko": "한 집단이라도 δ = {gate.delta} 이상 저하되면 거부.\n"
              "질의 수가 과소한 집단은 차단에 쓰지 않는다",
        "en": "Reject if any subgroup drops by δ = {gate.delta} or more.\n"
              "Subgroups with too few queries do not block"},
    "gate.detail_t2": {
        "ko": "최대 하락 +{ep3.t2_max_drop:.4f}", "en": "Max drop +{ep3.t2_max_drop:.4f}"},
    "gate.row_t3": {
        "ko": "T3 · 교차 태스크 역량질문 비회귀\n다른 태스크와 공유 코어 {cq.t3_total}개",
        "en": "T3 · Cross-task CQ non-regression\n{cq.t3_total} in other tasks and shared core"},
    "gate.rule_t3": {
        "ko": "다른 태스크의 통과율이 하나라도 저하되면 거부.\n예외는 명시적 waiver 로만 허용한다",
        "en": "Reject if any other task's pass rate falls.\n"
              "The only exception is an explicit waiver"},
    "gate.detail_t3": {"ko": "{ep3.t3_suites_head}", "en": "{ep3.t3_suites_head}"},
    "gate.row_merge": {"ko": "병합·릴리스", "en": "Merge and release"},
    "gate.footer": {
        "ko": "승인식은 곱이므로 한 항이라도 미충족이면 승인은 0이다. "
              "이 사례의 승인 결과는 거부이며 미충족 조건은 T1 하나이다. "
              "T4 는 이 식에 포함되지 않는다.",
        "en": "The rule is a product, so one unmet term makes acceptance 0. "
              "Here the result is a rejection and T1 is the only unmet condition. "
              "T4 is not part of the rule."},
    # ── 그림 5 · 실무 흐름과 실험 구성의 대응 ────────────────────────────────
    "flow.col_practice": {
        "ko": "선행기술조사 실무의 절차", "en": "Prior-art search in practice"},
    "flow.col_experiment": {"ko": "본 실험의 구성", "en": "Configuration of this experiment"},
    "flow.task_claims": {
        "ko": "대상 출원의 청구항을 읽는다", "en": "Read the claims of the application"},
    "flow.title_claims": {"ko": "독립항 전문 추출", "en": "Extract the independent claims"},
    "flow.body_claims": {
        "ko": "질의 본문 · claims_independent", "en": "Query text · claims_independent"},
    "flow.task_query": {
        "ko": "검색식을 세운다 — 키워드와 서지 조건",
        "en": "Build a search query — keywords and bibliographic filters"},
    "flow.title_query": {"ko": "질의 표현 1종 고정", "en": "One query representation, fixed"},
    "flow.body_query": {
        "ko": "4종을 준비하였으나 비교는 실행하지 않았다",
        "en": "Four were prepared; the comparison was not run"},
    "flow.task_search": {
        "ko": "특허 데이터베이스를 검색한다", "en": "Search the patent database"},
    "flow.title_search": {
        "ko": "어휘 · 의미 · 개념의 세 경로", "en": "Three paths: lexical, dense, concept"},
    "flow.body_search": {
        "ko": "BM25(nori) · Dense(Titan v2) · 개념 단독",
        "en": "BM25 (nori) · Dense (Titan v2) · concept only"},
    "flow.task_fuse": {
        "ko": "결과를 합쳐 후보 목록을 만든다", "en": "Fuse the results into a candidate list"},
    "flow.title_fuse": {"ko": "순위 융합과 후보 풀", "en": "Rank fusion and candidate pool"},
    "flow.body_fuse": {
        "ko": "reciprocal rank fusion 상수 {flow.rrf_c} → 상위 {flow.pool_depth:,}건",
        "en": "reciprocal rank fusion constant {flow.rrf_c} → top {flow.pool_depth:,}"},
    "flow.task_review": {
        "ko": "후보를 순차로 검토한다", "en": "Review the candidates in order"},
    "flow.title_review": {"ko": "온톨로지 재순위화", "en": "Ontology reranking"},
    "flow.body_review": {
        "ko": "풀 안에서만 재정렬 — 후보를 확대하지 않는다",
        "en": "Reorders within the pool — the pool is not enlarged"},
    "flow.task_reach": {
        "ko": "심사관이 인용할 문헌에 도달한다",
        "en": "Reach the documents an examiner would cite"},
    "flow.title_reach": {
        "ko": "family Recall@100 으로 채점", "en": "Scored by family Recall@100"},
    "flow.body_reach": {
        "ko": "정답은 심사관 인용", "en": "Ground truth is the examiner citation"},
    "flow.gap_baseline": {
        "ko": "주 기준선에 융합되지 않음\n분류 신호 단독의 회수는 {flow.b4_r100:.3f}",
        "en": "Not fused into the\nprimary baseline\n"
              "classification alone\nrecalls {flow.b4_r100:.3f}"},
    "flow.gap_pool": {
        "ko": "풀 밖은 회수되지 않음\n정답의 {ceiling.pool_pct:.1f}%만 풀 안에 있다\n"
              "({ceiling.pool_hits}/{ceiling.edges} · 문서 단위 · 탐색적)",
        "en": "Outside the pool\nnothing is recovered\n"
              "only {ceiling.pool_pct:.1f}% lie inside\n"
              "({ceiling.pool_hits}/{ceiling.edges} · document\nunit · exploratory)"},
    "flow.premise": {
        "ko": "전제 · 질의 특허는 이미 온톨로지에 등재되어 있다. 자유 텍스트 질의를 개념에 "
              "연결하는 적용기는 이후 세대에서 구현되었으며 본 장의 수치에 포함되지 않는다.",
        "en": "Premise · the query patent is already registered in the ontology. The linker "
              "that attaches concepts to free-text queries came in a later generation and is "
              "not included in these numbers."},

    # ── 그림 6 · 평가 에피소드 × 승인식 구성요소 ─────────────────────────────
    "matrix.col_resource": {"ko": "자원 ART-1", "en": "Resource ART-1"},
    "matrix.col_resource_sub": {"ko": "표현 감사", "en": "Representation audit"},
    "matrix.col_formal_sub": {"ko": "형식 · 기능", "en": "Formal · functional"},
    "matrix.col_t1_sub": {"ko": "검색 비열등성", "en": "Non-inferiority"},
    "matrix.col_t2_sub": {"ko": "하위집단", "en": "Subgroups"},
    "matrix.col_t3_sub": {"ko": "교차 태스크", "en": "Cross-task"},
    "matrix.col_t4_sub": {"ko": "생성 층", "en": "Generation layer"},
    "matrix.head_episode": {"ko": "평가 에피소드", "en": "Evaluation episode"},
    "matrix.head_verdict": {"ko": "판정 요약", "en": "Verdict summary"},
    "matrix.ep1_name": {"ko": "표현 감사", "en": "Representation audit"},
    "matrix.ep1_status": {"ko": "관측 사실", "en": "Observed fact"},
    "matrix.ep1_cell": {
        "ko": "역량질문 {cq.total}개\n세 태스크 어휘",
        "en": "{cq.total} questions\nthree task vocabularies"},
    "matrix.ep1_verdict": {
        "ko": "세 태스크의 어휘·관계·역량질문이 자원에 실재한다.\n"
              "다만 표현 범위는 검색 준비도와 동일하지 않다.",
        "en": "The vocabularies, relations and questions of the three tasks are present.\n"
              "Representational scope is not the same as retrieval readiness."},
    "matrix.ep2_name": {"ko": "게이트 판별력", "en": "Gate discrimination"},
    "matrix.ep2_status": {"ko": "홀드아웃 확증", "en": "Holdout confirmatory"},
    "matrix.ep2_cell_l3": {"ko": "주 태스크 CQ\n검출", "en": "Primary-task CQ\ndetection"},
    "matrix.ep2_cell_t3": {"ko": "교차 결함\n단독 검출", "en": "Cross-task fault\nT3 alone"},
    "matrix.ep2_verdict": {
        "ko": "교차 태스크 결함은 T3 가 단독으로 검출하였고 정상 델타의\n"
              "오거부는 {ep2.false_positive} 이다 (단측 McNemar p = {ep2.mcnemar_p:.4f}).",
        "en": "T3 alone detected the cross-task faults, and false rejections among\n"
              "sound deltas are {ep2.false_positive} (one-sided McNemar p = {ep2.mcnemar_p:.4f})."},
    "matrix.ep3_name": {"ko": "통제된 자원 교체", "en": "Resource substitution"},
    "matrix.ep3_status": {"ko": "별도 사전등록", "en": "Separate preregistration"},
    "matrix.ep3_cell_resource": {
        "ko": "문서당 개념\n{ep3.concepts_per_doc.before} → {ep3.concepts_per_doc.after}",
        "en": "Concepts per doc\n{ep3.concepts_per_doc.before} → {ep3.concepts_per_doc.after}"},
    "matrix.ep3_cell_formal": {"ko": "전부 통과", "en": "All passed"},
    "matrix.ep3_cell_t1": {"ko": "ΔR@100\n{ep3.p1.delta:sig}", "en": "ΔR@100\n{ep3.p1.delta:sig}"},
    "matrix.ep3_cell_t2": {
        "ko": "최대 하락\n+{ep3.t2_max_drop:.4f}", "en": "Max drop\n+{ep3.t2_max_drop:.4f}"},
    "matrix.ep3_cell_t3": {
        "ko": "CQ {cq.t3_total}개\n통과율 유지", "en": "{cq.t3_total} CQs\npass rate held"},
    "matrix.ep3_verdict": {
        "ko": "자원 지표가 개선되고 형식 검증을 통과한 변경을 성능 조건\n"
              "하나가 차단하였다. 승인식은 곱이므로 승인 결과는 거부이다.",
        "en": "One performance condition blocked a change that improved the resource\n"
              "indicators and passed formal validation. The rule is a product, so it is a rejection."},
    "matrix.ep4_name": {"ko": "검색 이득의 범위", "en": "Scope of the gain"},
    "matrix.ep4_status": {"ko": "확증 · 분할 둘", "en": "Confirmatory · two splits"},
    "matrix.ep4_cell_t1": {
        "ko": "A {ep4.p1_gain.delta:sig}\nB {ep4b.p1_gain.delta:sig}",
        "en": "A {ep4.p1_gain.delta:sig}\nB {ep4b.p1_gain.delta:sig}"},
    "matrix.ep4_cell_t2": {"ko": "국소 회귀\n없음", "en": "No local\nregression"},
    "matrix.ep4_cell_t4": {
        "ko": "하한 {t4.citation_precision.lb95:sig}\n마진 −{t4.eps} 초과",
        "en": "Lower bound {t4.citation_precision.lb95:sig}\npast margin −{t4.eps}"},
    "matrix.ep4_verdict": {
        "ko": "깊은 회수의 개선은 두 확증 분할에서 반복 관측되었다.\n"
              "사전등록된 복합 기준의 동시 충족은 두 분할에서 확인되지 않았다.",
        "en": "Deep recall improved in both confirmatory splits.\n"
              "The preregistered composite prediction held in neither split."},
    "matrix.ep5_name": {"ko": "제2 자원 이식", "en": "Port to a 2nd resource"},
    "matrix.ep5_status": {"ko": "별도 사전등록", "en": "Separate preregistration"},
    "matrix.ep5_cell_formal": {
        "ko": "코드 변경 없이 실행\n정상 델타 오거부 {ep5.false_positive}",
        "en": "Ran without code change\nfalse rejections {ep5.false_positive}"},
    "matrix.ep5_cell_t3": {
        "ko": "관찰면 {ep5.observable}/{ep5.cq_total}\n불일치 쌍 {ep5.discordant}",
        "en": "Surface {ep5.observable}/{ep5.cq_total}\ndiscordant {ep5.discordant}"},
    "matrix.ep5_verdict": {
        "ko": "형식 층과 교차 태스크 층의 절차는 자원을 바꾸어도 실행되었다.\n"
              "동결한 결함 명세는 그 자원의 표현 관습에 재접지가 필요하였다.",
        "en": "The formal and cross-task layers ran on a different resource.\n"
              "The frozen fault specification had to be regrounded on its conventions."},
    "matrix.reading": {
        "ko": "가로로 읽으면 한 에피소드가 승인식의 어느 항을 검증하였는지 보이고, 세로로 "
              "읽으면 같은 항이 다른 실험에서 낸 판정이 보인다.\n"
              "EP3 행에서는 형식 검증을 전부 통과한 변경이 T1 에서 거부되었고, EP4 행에서는 "
              "T1 을 통과한 구성이 T4 에서 비열등을 보이지 못하였다.\n"
              "* T4 는 승인식에 포함되지 않는다 — 설계와 판정 1회의 기록이다.",
        "en": "Read across for what one episode examined; read down for how the same term "
              "was judged in different experiments.\n"
              "In the EP3 row a change passing every formal layer was rejected at T1; in the "
              "EP4 row a configuration passing T1 did not show non-inferiority at T4.\n"
              "* T4 is not part of the acceptance rule — it is a design and one verdict."},

    # ── 그림 7 · 시스템 × 지표 (데이터 플롯) ─────────────────────────────────
    "irmetrics.panel_a": {
        "ko": "(a) 주지표 — 깊은 회수", "en": "(a) Primary metric — deep recall"},
    "irmetrics.panel_b": {
        "ko": "(b) 보조지표까지 — 상위 정밀도는 오르지 않는다",
        "en": "(b) With auxiliary metrics — top precision does not rise"},
    "irmetrics.ylabel": {
        "ko": "Δ vs B3 (텍스트 기준선)", "en": "Δ vs B3 (text baseline)"},
    "irmetrics.legend_p0": {
        "ko": "P0★ (사전지정 주)", "en": "P0★ (prespecified primary)"},
    "matrix.ep3_cell_ratio_mark": {"ko": "{ep3.ratio:.1f}배", "en": "{ep3.ratio:.1f}×"},
    "irmetrics.p0_short": {"ko": "P0★\n+온톨로지", "en": "P0★\n+Ontology"},
}
