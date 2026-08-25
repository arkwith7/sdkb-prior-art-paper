#!/usr/bin/env python3
"""scripts/build_submission_en.py — 영문 투고본을 **한국어 파생본에서 조립한다** (CLAUDE.md §2.3).

**왜 손으로 번역하지 않는가.** 원고에는 표 12개와 그림 8개가 있고, 그 안의 수치는 전부 실행된
코드의 출력이다(§1-1). 영문본을 통째로 다시 타자하면 **수치를 손으로 옮겨 적게 되고**, 그것이
정확히 `build_submission_stage3.py` 가 막으려고 존재하는 실패 양상이다. 그래서 같은 규율을 한
단계 더 적용한다 — **산문은 사람이 영문으로 쓰고, 표와 그림은 한국어 파생본에서 복사한 뒤
라벨만 치환한다.**

배선:

    paper/manuscript/en_source.md      영문 산문 (사람이 쓴다 · {{TABLE:n}} · {{FIGURE:n}} 지시자)
      + paper/submission/manuscript.md 한국어 파생본 (표·그림·캡션의 복사 원본)
      → paper/submission/en/manuscript.md

지시자:

    {{TABLE:7}}      한국어 파생본의 `**표 7. …**` 캡션과 뒤따르는 표를 가져와 라벨을 치환한다
    {{FIGURE:3}}     `![그림 3. …](경로)` 와 뒤따르는 `**그림 3.** …` 설명을 가져와 치환한다

**수치 불변을 기계가 강제한다.** 치환 전후의 수치 토큰이 하나라도 달라지면 실패한다(rc 2).
절 번호(`§4.5`)는 수치로 세지 않는다 — 재번호는 수치 변경이 아니기 때문이다. 이 규칙은
`build_submission_stage3.py` 의 `measurements()` 와 같은 정의를 쓴다.

**용어 치환은 목록으로만 한다.** `TERMS` 는 (한국어, 영문) 쌍이며 **긴 것부터** 적용한다.
치환 후에도 한글이 남으면 그 자리를 전부 보고하고 실패한다 — 조용히 한글이 섞인 영문 표를
내보내는 것이 이 스크립트가 막아야 할 유일한 실패다.

CLI:
    uv run python scripts/build_submission_en.py            # 조립
    uv run python scripts/build_submission_en.py --check    # 조립 결과가 디스크와 같은지만 본다
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROSE = ROOT / "paper" / "manuscript" / "en_source.md"
KOREAN = ROOT / "paper" / "submission" / "manuscript.md"
# **본문이 완성되기 전까지는 초안 경로로 낸다.** `paper/submission/**` 는 `submission_check` 의
# 대상이고, 절이 아직 없는 원고는 D9(절 참조 도달성)에서 정당하게 실패한다. 미완성 산출물을
# 검사 대상 트리에 두고 게이트를 빨갛게 만들면, 다음 세션은 그 빨강을 정상으로 여기게 된다.
# 본문 번역이 끝나면 이 경로를 `paper/submission/en/manuscript.md` 로 바꾼다 — 그때 D2·D3·D7·
# D8·D9 와 링크 검사가 영문 원고에도 걸린다.
TARGET = ROOT / "paper" / "manuscript" / "en_draft.md"

TABLE_RE = re.compile(r"\{\{TABLE:(\d+)\}\}")
FIGURE_RE = re.compile(r"\{\{FIGURE:(\d+)\}\}")

# 수치 토큰 — 절 번호는 뺀다(§4.9 → §4.5 는 재번호이지 수치 변경이 아니다).
NUMERIC = re.compile(r"\d+(?:[.,]\d+)*")
SECTION_TOKEN = re.compile(r"§\s?\d+(?:\.\d+)*")
HANGUL = re.compile(r"[가-힣]")


def fail(msg: str) -> None:
    print(f"[en] 실패 — {msg}", file=sys.stderr)
    raise SystemExit(2)


def measurements(text: str) -> list[str]:
    return NUMERIC.findall(SECTION_TOKEN.sub("", text))


# ── 셀·캡션 번역 ─────────────────────────────────────────────────────────────
# **왜 용어 치환이 아니라 셀 사전인가.** 표 셀에는 한국어 문장이 들어 있어 단어 치환으로는
# 번역되지 않는다. 게다가 부분 문자열 치환은 `대표`·`지표` 를 `대Table`·`지Table` 로 망가뜨린다
# (첫 구현에서 실제로 그랬다). 그래서 **셀 전체를 키로 하는 사전**을 쓰고, 사전에 없는 셀에
# 한글이 남으면 실패한다. 사전은 사람이 쓰고 기계는 **수치가 변하지 않았음만** 보증한다.
#
# 캡션 도입어(`**표 7.` · `![그림 3.` · `**그림 3.**`)는 형태가 고정되어 있으므로 정규식으로
# 처리한다 — 사전에 넣으면 캡션 문장 전체를 키로 잡아야 해서 유지되지 않는다.
# 캡션은 산문이다 — 사전 키로 잡으면 유지되지 않는다. 그래서 **영문 캡션은 사람이 쓰고**,
# 기계는 그 캡션의 수치가 한국어 캡션과 같은지만 본다. 표는 `T<n>`, 그림은 `F<n>` 키다.
CAPTIONS: dict[str, str] = {
    "F1alt": "Figure 1. Study overview — two artifacts and one evaluation environment, the release "
             "approval procedure, and what the four episodes measure.",
    "F1": "**Figure 1.** Study overview. The top band is artifact A1, a resource placing three task "
          "views on one shared T-Box; the middle band is artifact A2, the release gate that reviews "
          "a resource change before it ships; the bottom band is evaluation environment E1, the "
          "four episodes and what each measures. The middle band reads left to right, and a failed "
          "stage stops the ones behind it. T4, shown dashed, is not part of the approval rule "
          "(§3.5.1).",
    "T1": "**Table 1. Position relative to prior work — the contribution is the combination and the "
          "experimental design, not primacy.**",
    "F2alt": "Figure 2. The indicator structure of the three layers and the three misalignments "
             "observed between them.",
    "F2": "**Figure 2.** Cross-layer metric misalignment. The left side shows the indicator "
          "structure of the resource, retrieval, and generation layers; the right side shows what "
          "was actually observed between them. The number on each arrow at the left corresponds to "
          "the numbered observation at the right, and (ii) alone points not to the next layer but "
          "to a different unit within the same layer, the number of documents reviewed. "
          "Observation (i) is presented in §5.3, (ii) in §5.4.3, and (iii) in §3.5.1 and §6.5; the "
          "interpretation is in §6.1.",
    "T2": "**Table 2. Stages of design science research and how they were carried out in this "
          "study.**",
    "T3": "**Table 3. Evaluation episodes — EP is a new label and does not collide with the "
          "preregistration labels.**",
    "F3alt": "Figure 3. Three task views on one shared T-Box and the channels of cross-task "
             "coupling.",
    "F6alt": "Figure 6. The five evaluation episodes mapped onto the terms of the acceptance rule, "
             "with the verdict for each term.",
    "F6": "**Figure 6.** Evaluation episodes mapped onto the terms of the acceptance rule. Rows are "
          "episodes and columns are terms of the rule; only the leftmost column is the resource "
          "rather than the gate. The symbol in each cell is the verdict and the line beneath it the "
          "evidence. A blank cell means that the episode did not examine that term. T4 is marked "
          "with an asterisk because it is not part of the acceptance rule.",
    "T11": "**Table 11. Decision stability — the point at which each verdict switches under the "
           "frozen thresholds.**",
    "T12": "**Table 12. Core design principles DP1–DP4.**",
    "T13": "**Table 13. Nine deficits in validation strength and generalizability — every remedy "
           "is the object of a new preregistration.**",
    "T10": "**Table 10. Release-lineage verdicts on engineering ontology 2 — confined to "
           "the formal layers and the cross-task layer.** d0–d5 are releases v1.3.0, v1.4.0, "
           "v1.4.1, v1.4.2, v1.4.3, and v1.4.4; migration condition R places the original instances "
           "unchanged and N places them after applying the official migration rules. Because the "
           "acceptance rule is not completed, `accept` is not recorded in any row and only partial "
           "acceptance remains.",
    "T9": "**Table 9. Subgroups and ablation in the first confirmatory split** (test, 198 queries, "
          "family R@100, query-level paired bootstrap with 10,000 resamples; `Difference` in the "
          "ablation row is the **removal loss** (full − ablated; positive = layer contribution); "
          "Holm m=8; all 17 rows are in S5).",
    "T8": "**Table 8. Retrieval performance in the two confirmatory splits (2 panels) — the "
          "baseline is the Text Hybrid (B3) of each panel; Δ and the win/loss/tie counts summarize "
          "the original sample paired per query, and the 95% confidence intervals and two-sided "
          "*p* values come from a query-level paired bootstrap with 10,000 resamples.**",
    "F7alt": "Figure 7. System by metric — improvement in deep recall and no improvement in "
             "top-of-ranking ordering.",
    "F7": "**Figure 7.** System by metric. (a) the primary metric family Recall@100; (b) the "
          "difference of each auxiliary metric against B3 with 95% confidence intervals. Ontology "
          "reranking retrieves more known positives within a review depth of 100 but does not "
          "improve the ordering quality of the top 20.",
    "T7": "**Table 7. Retrieval performance when only the resource bundle is substituted (test, 198 "
          "queries, family Recall@100).**",
    "T6": "**Table 6. The preregistered evaluation checks and their verdicts — the evidence and the "
          "full text are in Section 5 and in supplementary S5.**",
    "T5": "**Table 5. Control roles of the comparison configurations — the response each must show "
          "when only the resource is substituted.**",
    "F5alt": "Figure 5. Correspondence between the procedure of prior-art search in practice and "
             "the configuration of this experiment, and the two places where it fails.",
    "F5": "**Figure 5.** Correspondence between practice and the experimental configuration. The "
          "left column lists the stages of practice and the right column the configuration of this "
          "experiment at each stage. The two notes in the right margin mark where the correspondence "
          "fails, and the band at the bottom states the premise under which the numbers of this "
          "section hold.",
    "T4": "**Table 4. The 31 competency questions by purpose — the gate denominator is 28 and the "
          "representation-audit denominator is 31.**",
    "F4alt": "Figure 4. The order of the acceptance procedure, the handling of each unmet term, and "
             "the actual verdicts in the controlled resource substitution.",
    "F4": "**Figure 4.** The T-gate procedure and the actual verdicts. The left column is the order "
          "of the acceptance procedure and reads downward. The middle column is the handling when a "
          "term is not met, and the right column is the verdict each term actually produced in the "
          "controlled resource substitution (§5.3). The right column shows that a change passing "
          "every formal layer was rejected on one performance condition.",
    "F3": "**Figure 3.** The shared T-Box and three task views. The three boxes at the top give the "
          "main classes of each view, a representative competency question, the A-Box evidence, and "
          "the status of that view in this paper. The three channels in the middle are vocabulary "
          "used by two or more views, and the dashed lines from each channel show the two views it "
          "joins. The box at the bottom gives the shared core and the number of competency "
          "questions per suite that the gate observes. That the three views are not exclusive "
          "modules is why the cross-task regression of §1 can occur.",
}

# 셀 사전 — 한국어 셀 **전체**를 키로 하는 완전 일치 치환. 부분 문자열 치환을 쓰지 않는 이유는
# `대표`·`지표` 가 `대Table`·`지Table` 로 망가지기 때문이다(첫 구현에서 실제로 그랬다).
# 지표·게이트·라벨 이름(L0–L3 · T1–T4 · Recall@100 · P0★ · B3 · EP1–EP4)은 이미 라틴 문자이며
# 바꾸면 다른 것을 가리키므로 사전에 없다. 숫자만 든 셀도 없다 — 손대지 않는다.
CELLS: dict[str, str] = {
    # ── 표 13 · 결손 아홉 ───────────────────────────────────────────────────
    "결손": "Deficit",
    "현 상태 (보고 위치)": "Current state (where reported)",
    "해소하는 측정": "Measurement that removes it",
    "실제 자원 변경의 거부 사례가 1회": "Only 1 rejection of a real resource change",
    "통제된 자원 교체 1회에서 T1 미충족에 따른 승인 거부 (§5.3)":
        "Acceptance refused on an unmet T1 in 1 controlled resource substitution (§5.3)",
    "자격 있는 델타 3–5건을 순차 투입하고 판정의 분포를 보고":
        "Submit 3–5 eligible deltas in sequence and report the distribution of verdicts",
    "승인된 변경의 사후 안전성 미검정": "Post-acceptance safety of an approved change not tested",
    "심사한 델타가 승인되지 않아 비교가 성립하지 않았다 (§6.5)":
        "The adjudicated delta was not accepted, so the comparison did not arise (§6.5)",
    "승인된 델타를 릴리스한 뒤 다음 세대의 봉인 분할에서 재측정":
        "Release an accepted delta and re-measure on the sealed split of the next generation",
    "교차 태스크 검출의 임계 민감성": "Threshold sensitivity of cross-task detection",
    "τ=0.05에서 T3 단독 검출 12/45이나 τ=0.10에서는 4/45, τ=0.00에서는 17/45 (§5.2)":
        "At τ=0.05 detection by T3 alone is 12/45, at τ=0.10 it is 4/45, and at τ=0.00 it is 17/45 "
        "(§5.2)",
    "τ 격자 전반의 검출률·위양성률 곡선을 사전등록하고 동시 보고":
        "Preregister and report jointly the detection-rate and false-positive curves across the τ "
        "grid",
    "임계 셋의 실무적 근거 부재": "No practical basis for the three thresholds",
    "ε=0.02·δ=0.05·τ=0.05는 동결한 규범적 선택이며 보정을 거치지 않았다 (§3.5)":
        "ε=0.02, δ=0.05, and τ=0.05 are frozen normative choices and were not calibrated (§3.5)",
    "재색인 반복의 회수 변동폭 측정과 실무자 허용 한계 조사":
        "Measure recall variation across repeated reindexing and survey practitioner tolerance",
    "승인 게이트를 완전히 평가할 수 있는 자원의 부재":
        "No resource on which the acceptance gate can be evaluated in full",
    "**부분 해소** — 형식 층과 교차 태스크 층은 제2 공학 온톨로지에서 동일 절차로 판정하였다 (§4.6 · §5.5). 게이트 전체의 평가는 릴리스 델타 계보와 하류 태스크 벤치마크를 동시에 갖춘 자원을 요구하나, 본 연구의 자원은 뒤의 것만 제2 자원은 앞의 것만 갖추었다":
        "**partly removed** — the formal layers and the cross-task layer were adjudicated on "
        "engineering ontology 2 with the same procedure (§4.6 · §5.5). Evaluating the whole gate "
        "requires a resource that holds both a release delta lineage and a downstream task "
        "benchmark, whereas our resource holds only the latter and resource 2 only the former",
    "두 조건을 동시에 갖춘 자원의 확보, 또는 제2 자원의 태스크 벤치마크를 구축한 뒤 T1·T2를 적용":
        "Obtain a resource holding both conditions, or build a task benchmark on resource 2 and "
        "then apply T1 and T2",
    "질의 언어와 정답 언어의 불일치": "Mismatch between query language and ground-truth language",
    "질의는 전량 한국어이고 알려진 양성의 41%는 비한국어 (§6.5)":
        "The queries are entirely Korean and 41% of known positives are non-Korean (§6.5)",
    "질의 측 번역 구성을 추가하여 언어별 회수를 분해 재측정":
        "Add a query-side translation configuration and re-measure recall decomposed by language",
    "강한 다국어 기준선의 부재": "No strong multilingual baseline",
    "**부분 해소** — 다국어 융합 기준선을 별도 사전등록으로 추가하였고 기준선 강도는 유의하게 변하지 않았다 (§4.3 · §5.4.3 · 표 8). 다만 두 인코더가 같은 백본 계열이므로 **계열 다양성은 미달성**":
        "**partly removed** — a multilingual fusion baseline was added under a separate "
        "preregistration and baseline strength did not change significantly (§4.3 · §5.4.3 · "
        "Table 8). The two encoders share a backbone family, however, so **family diversity was "
        "not achieved**",
    "계열이 다른 인코더를 포함한 재평가": "Re-evaluate including an encoder from a different family",
    "전문가 관련성 판정 미수행": "Expert relevance judgment not performed",
    "프로토콜은 동결하였으나 판정은 수행하지 않았다 (§4.4). 취약도는 판정 전환 최소 건수로 계량하고 외생 라벨 병합으로 **부분 축소**하였다 (§5.4.1)":
        "The protocol was frozen but the judgment was not performed (§4.4). The vulnerability was "
        "quantified by the minimum number of judgment reversals and **partly reduced** by merging "
        "exogenous labels (§5.4.1)",
    "상위 미인용 후보의 **표적 표본**에 대한 2인 가림 독립 판정과 κ 보고":
        "2-rater blinded independent judgment on a **targeted sample** of highly ranked uncited "
        "candidates, with κ reported",
    "결함 명세의 자원 간 이전": "Transfer of the fault specification between resources",
    "제2 도메인의 홀드아웃 모델에서 포함관계 역전 결함의 주입 후보가 0건이어서 21건 중 9건이 판정에 이르지 못하였다 (§5.5)":
        "In domain 2 the holdout model had 0 injection sites for the containment-inversion fault, "
        "so 21 faults yielded 9 without a verdict (§5.5)",
    "대상 자원의 술어 방향을 실측하고 그 관습에 맞추어 결함 명세를 재정의한 뒤 새 사전등록으로 재판정":
        "Measure the predicate direction of the target resource, redefine the fault specification "
        "for that convention, and adjudicate again under a new preregistration",
    # ── 표 11 · 결정 안정성 ─────────────────────────────────────────────────
    "조건": "Condition",
    "동결 임계": "Frozen threshold",
    "관측": "Observed",
    "판정": "Verdict",
    "판정이 전환되는 지점": "Switching point",
    "T1 · 검색 비열등": "T1 · retrieval non-inferiority",
    "미충족": "not met",
    "충족": "met",
    "ε > 0.0542 이어야 충족으로 바뀐다": "becomes met only if ε > 0.0542",
    "T2 · 하위집단 안전": "T2 · subgroup safety",
    "최대 하락 = +0.0401": "maximum drop = +0.0401",
    "δ ≤ 0.0401 이면 미충족으로 바뀐다": "becomes not met if δ ≤ 0.0401",
    "T3 · 교차 태스크 검출 (EP2 분포 검사)": "T3 · cross-task detection (EP2 distribution check)",
    "τ = 0.05 (사전 지정)": "τ = 0.05 (prespecified)",
    "T3 단독 검출 17/45 · *p* < .0001": "detection by T3 alone 17/45 · *p* < .0001",
    "T3 단독 검출 12/45 · *p* < .0001": "detection by T3 alone 12/45 · *p* < .0001",
    "T3 단독 검출 4/45 · *p* = .3438": "detection by T3 alone 4/45 · *p* = .3438",
    "사전 동결 격자 안의 평가": "evaluation within the frozen grid",
    "T4 · 하류 생성 층": "T4 · downstream generation layer",
    "ε_T4 > 0.0205 이어야 충족으로 바뀐다": "becomes met only if ε_T4 > 0.0205",
    # ── 표 12 · 코어 설계원리 ───────────────────────────────────────────────
    "설계원리": "Design principle",
    "근거 (실측)": "Evidence (measured)",
    "설계 시점": "Design time",
    "확인 시점": "Confirmation time",
    "등급": "Grade",
    "**층별 검증** — 온톨로지 내부 품질과 하류 태스크 성능은 **별도 층에서** 평가한다":
        "**Layered validation** — internal ontology quality and downstream task performance are "
        "evaluated **at separate layers**",
    "§5.3 — 문서당 개념 1.545 → 3.779(2.4배)인데 교체 대상 구성(P1)의 Recall@100 은 −0.0293 · **성립한 자원 델타는 1건**":
        "§5.3 — concepts per document rose 1.545 → 3.779 (2.4×) while the substituted configuration "
        "(P1) shows Recall@100 −0.0293 · **1 established resource delta**",
    "확인이 먼저": "Confirmation first",
    "**경험적 지지** (확인 선행)": "**empirically supported** (confirmation preceded)",
    "**한 층 아래 승인** — 자원 변경은 자원 지표가 아니라 **다음 사용 층의 비회귀 결과**로 승인한다":
        "**Acceptance one layer below** — a resource change is accepted on **the non-regression "
        "result of the next layer of use**, not on resource indicators",
    "§5.3 — 형식 검증 L0–L3 를 **전부 통과한** 델타를 성능 조건 T1 이 거부(Accept = 0)":
        "§5.3 — a delta that **passed all** of L0–L3 was rejected by the performance condition T1 "
        "(Accept = 0)",
    "**§3.5 설계 시점**": "**§3.5, at design time**",
    "**사전 설계 · 실증 지지**": "**designed in advance and empirically supported**",
    "**교차 태스크 감시** — 공유 T-Box 에서는 **주 태스크 성능만으로** 변경을 승인하지 않는다":
        "**Cross-task monitoring** — on a shared T-Box, a change is not accepted on **primary-task "
        "performance alone**",
    "**§3.5 설계 시점**(T3)": "**§3.5, at design time** (T3)",
    "§5.2 — 교차 결함을 T3 만 단독 검출(12/45 · 단측 *p*=.0001) · §5.4.2 — 음성 대조군(A8) 제거가 검색 성능을 0.0316 저하시켰고(제거 손실 +0.0316), 다만 **§5.4.1 두 번째 분할에서는 0.0000 으로 서로 달랐다** · §5.5 — 제2 도메인에서는 판정이 가능한 12건에서 단독 검출 0 (근거를 늘리지 않는다)":
        "§5.2 — a cross-task fault detected by T3 alone (12/45, one-sided *p*=.0001) · §5.4.2 — "
        "removing the negative control (A8) degraded retrieval performance by 0.0316 (removal loss "
        "+0.0316), while **§5.4.1 the second split gave 0.0000 and the two differed** · §5.5 — in "
        "domain 2 the 12 adjudicable faults gave 0 detections by the cross-task condition alone "
        "(this does not extend the evidence)",
    "**사전 설계 · 실증 지지** — 근거는 결함주입 T3 단독 검출이 진다. A8 근거는 **두 표본에서 서로 달랐음을 그대로 적는다**(경쟁 설명 §6.5)":
        "**designed in advance and empirically supported** — the evidence rests on detection by T3 "
        "alone in fault injection. For the A8 evidence we state **that the two samples differed** "
        "(competing explanations in §6.5)",
    "**통제된 자원 교체** — 문서집합·모델·가중치를 고정하고 **자원 번들만 교체**해야 온톨로지 중심 자원 변경의 효과가 판별된다":
        "**Controlled resource substitution** — the effect of an ontology-centered resource change "
        "is identified only by fixing documents, model, and weights and **substituting the resource "
        "bundle alone**",
    "§3.2 · §5.3 — T-Box 가 한 번도 바뀌지 않아 승인 안전성을 **원리적으로 측정할 수 없었다** · 두 조건이 처음 성립한 뒤에야 판정이 나왔다 · **성립 사례는 1건**":
        "§3.2 · §5.3 — the T-Box never changed, so acceptance safety **could not be measured in "
        "principle** · a verdict followed only after the two conditions first held · **1 "
        "established case**",
    "**경험적 지지** (확인 선행 · 방법론적 요구사항)":
        "**empirically supported** (confirmation preceded; a methodological requirement)",
    # ── 표 10 · 제2 자원의 릴리스 계보 판정 ─────────────────────────────────
    "인접 쌍": "Adjacent pair",
    "이행": "Migration",
    "Δ 추가": "Δ added",
    "Δ 제거": "Δ removed",
    "**실패**": "**fail**",
    "통과": "pass",
    # ── 표 9 · 하위집단과 절제 ──────────────────────────────────────────────
    "집단/제거 계층": "Subgroup / removed layer",
    "질의 수": "Queries",
    "qrel 수": "qrel",
    "제안법 R@100": "Proposed R@100",
    "차이": "Difference",
    "정답 전량 한국어": "All positives Korean",
    "정답에 외국어 포함": "Positives include a foreign language",
    "**-Expert layer (A8, 음성 대조군)**": "**-Expert layer (A8, negative control)**",
    "**[+0.0105,+0.0560]** (p=0.002·Holm 유의)":
        "**[+0.0105,+0.0560]** (p=0.002, significant after Holm)",
    # ── 표 8 · 두 확증 분할의 검색 성능 ──────────────────────────────────────
    "시스템": "System",
    "승/패/동": "Win/loss/tie",
    "Text+Ontology (P0★ · 사전지정 주)": "Text+Ontology (P0★, prespecified primary)",
    "다국어 융합 기준선 (B★ · 탐색적)": "Multilingual fusion baseline (B★, exploratory)",
    "서지 조건 모사 기준선 (B10 · 탐색적)": "Bibliographic-condition baseline (B10, exploratory)",
    # ── 표 7 · 자원 번들 교체 ────────────────────────────────────────────────
    "시스템 (test 198질의 · family R@100)": "System (test, 198 queries, family R@100)",
    "O (교정 전)": "O (before correction)",
    "O′ (교정 후)": "O′ (after correction)",
    "B0·B2·B3 텍스트 · B4 분류": "B0, B2, B3 text; B4 classification",
    "불변": "unchanged",
    "0 (텍스트를 변경하지 않았으므로)": "0 (the text side was not changed)",
    "**B5 온톨로지 단독**": "**B5 ontology-only**",
    "**P1 (교체 대상 구성)**": "**P1 (the substituted configuration)**",
    "§5.4.1 (패널 A · B)": "§5.4.1 (panels A and B)",
    "[S5](../supplementary/S5-submission-full-v2.md) 부록 A":
        "[S5](../../supplementary/S5-submission-full-v2.md), Appendix A",
    # ── 표 6 · 사전등록된 평가 점검 ──────────────────────────────────────────
    "평가 점검": "Evaluation check",
    "결과를 보기 전에 동결한 예측": "Prediction frozen before results were seen",
    "사전등록별 판정 기록 · 첫 확증 분할(A)":
        "Verdict recorded per preregistration · first confirmatory split (A)",
    "사전등록별 판정 기록 · 두 번째 확증 분할(B)":
        "Verdict recorded per preregistration · second confirmatory split (B)",
    "근거": "Evidence",
    "**점검 1 · 검색 유용성**": "**Check 1 · retrieval utility**",
    "확증": "Confirmatory",
    "온톨로지 보강 검색은 최강 텍스트 기준선보다 **Recall@100 과 nDCG@20 이 모두** 높고, 그 개선폭은 질의–정답의 어휘 중첩이 **낮은** 집단에서 더 크다":
        "Ontology-enriched retrieval exceeds the strongest text baseline on **both Recall@100 and "
        "nDCG@20**, and the improvement is larger in the subgroup with **low** lexical overlap "
        "between query and positives",
    "**부분 지지 — 주 지표에 한정** (R@100 은 P1 에서 유의 개선 · nDCG 조항 미충족 · 사전 지정 주 구성 비유의 · 저중첩 조건 반증)":
        "**supported for the primary metric only** (R@100 improved significantly on P1; the nDCG "
        "clause was not met; the prespecified primary configuration did not reach significance; the "
        "low-overlap clause was contradicted)",
    "**미지지** (R@100 은 개선되나 nDCG 조항이 깨졌다 · 주 구성 비유의)":
        "**not supported** (R@100 improved but the nDCG clause was not met; the primary "
        "configuration did not reach significance)",
    "**점검 2 · 계층 특이성**": "**Check 2 · layer specificity**",
    "게이트 태스크와 무관한 전문가 매칭 전용 계층(`Skill`·`ExpertCase`·`Mitigation`)의 제거는 검색 성능을 **유의하게 바꾸지 않는다**":
        "Removing the expert-matching-only layers (`Skill`, `ExpertCase`, `Mitigation`), which are "
        "unrelated to the gate task, **does not change retrieval performance significantly**",
    "**기각 → 교차 태스크 의존성 관측** (제거가 검색을 유의하게 악화)":
        "**rejected — an observed cross-task dependency** (removal degraded retrieval "
        "significantly)",
    '**재현되지 않음 — 판정 불가** (같은 절제의 값이 0.0000 · "영향 없음"과 "뺄 것이 없음"을 가르지 못한다)':
        "**not reproduced; no verdict can be issued** (the same ablation gave 0.0000, which does "
        "not separate no effect from nothing to remove)",
    "**점검 3 · 전달**": "**Check 3 · transfer**",
    "확증 평가 (게이트 조건 T4)": "Confirmatory evaluation (gate condition T4)",
    "검색 구성만 교체하고 생성기를 고정하였을 때 **인용 정확도가 떨어지지 않고 환각률이 오르지 않는다**(마진 동결)":
        "With only the retrieval configuration replaced and the generator fixed, **citation accuracy "
        "does not decrease and the hallucination rate does not increase** (margin frozen)",
    "*(탐색적 평가 — 평가 절차 동결이 목적 · 판정 없음)*":
        "*(exploratory evaluation — the purpose was to freeze the procedure; no verdict)*",
    "**판정 1회 = 실패 — 전달을 확증하지 못했다** (점추정은 제안 구성이 앞서나 신뢰구간 하한이 마진보다 낮았다 · 원인 미구분)":
        "**1 verdict issued, failed — we could not confirm transfer** (the point estimate favored the "
        "proposed configuration, but the lower bound fell below the margin; the cause is not "
        "separated)",
    # ── 표 5 · 비교 구성의 통제상 역할 ───────────────────────────────────────
    "구성": "Configuration",
    "통제상 역할": "Control role",
    "요구되는 관측": "Required observation",
    "BM25(B0) · Dense(B2) · CPC/IPC(B4)": "BM25 (B0), Dense (B2), CPC/IPC (B4)",
    "통제 무결성 대조군": "Control-integrity reference",
    "자원만 교체한 두 조건에서 순위가 동일하여야 한다. 달라지면 통제가 성립하지 않는다":
        "The rankings must be identical across the two conditions in which only the resource was "
        "substituted; if they differ, the control does not hold",
    "Text Hybrid(B3)": "Text Hybrid (B3)",
    "음성 대조군": "Negative control",
    "온톨로지 자원의 변경에 반응하지 않아야 한다":
        "It must not respond to a change in the ontology resource",
    "Ontology-only(B5)": "Ontology-only (B5)",
    "노출 대조군": "Exposure reference",
    "자원 변경에 가장 직접 반응하는 구성이다":
        "It is the configuration that responds most directly to a resource change",
    "Text+Ontology(P0) · +ClaimFeature(P1)": "Text+Ontology (P0), +ClaimFeature (P1)",
    "하류 센서": "Downstream sensor",
    "조건 T1의 판정이 이 두 구성에서 산출된다":
        "The verdict of condition T1 is produced on these two configurations",
    # ── 표 4 · 역량질문 구분 ─────────────────────────────────────────────────
    "구분": "Group",
    "개수": "Count",
    "용도": "Purpose",
    "G0 통과": "G0 pass",
    "L3 주 태스크 스위트 (pa)": "L3 primary-task suite (pa)",
    "선행기술조사 태스크의 기능 검증": "Functional validation of the prior-art search task",
    "T3 스위트 (em 6 · tf 5 · core 12)": "T3 suites (em 6, tf 5, core 12)",
    "다른 태스크와 공유 코어의 비회귀": "Non-regression of the other tasks and the shared core",
    "**게이트 관찰 소계**": "**Gate-observed subtotal**",
    "승인식의 판정 분모": "Denominator of the acceptance rule",
    "사이드카 청구항 질의 (CQ29–31)": "Sidecar claim queries (CQ29–31)",
    "청구항 수준 측정 전용 · 승인식 미편입":
        "Claim-level measurement only; not part of the acceptance rule",
    "**표현 감사 전량**": "**Representation audit, all**",
    "EP1 표현 감사의 분모": "Denominator of the EP1 representation audit",
    # ── 표 2 · 설계과학연구 단계 ──────────────────────────────────────────────
    "단계": "Stage",
    "본 연구의 실행": "How it was carried out here",
    "절": "Section",
    "문제 식별": "Problem identification",
    "형식 검증을 통과한 변경 이후의 태스크 성능 회귀":
        "Task performance regressed after a change that passed formal validation",
    "목표 정의": "Objective definition",
    "승인 조건을 한 층 아래 태스크에서 확인":
        "Verify the acceptance condition on the task one layer below",
    "설계·개발": "Design and development",
    "산출물 A1(SDKB)과 A2(T-gate)": "Artifacts A1 (SDKB) and A2 (the T-gate)",
    "1차 평가": "Evaluation round 1",
    "초기 결함주입에서 게이트 판별력이 **기각**":
        "Discriminative power of the gate was **rejected** in the initial fault injection",
    "설계 개선": "Design revision",
    "L3와 T3의 관찰 범위 분리": "Separation of the observation scopes of L3 and T3",
    "재평가": "Re-evaluation",
    "판정한 적 없는 홀드아웃 결함 45건으로 다시 측정하였다":
        "Measured again with 45 previously unadjudicated holdout faults",
    "실제 개정 기반 통제 평가": "Controlled evaluation on a real revision",
    "자원의 실제 개정에 대한 게이트의 거부(Accept = 0)":
        "The gate rejected a real revision of the resource (Accept = 0)",
    "이식 판정": "Port verdict",
    "제2 공학 온톨로지에 형식 층과 교차 태스크 층을 이식하여 동일 절차로 판정":
        "Ported the formal layers and the cross-task layer to engineering ontology 2 and "
        "adjudicated with the same procedure",
    "설계지식": "Design knowledge",
    "코어 원리 DP1–DP4 · 범위 원리 DP5·DP6·DP7":
        "Core principles DP1–DP4 and scope principles DP5, DP6, and DP7",
    # ── 표 3 · 평가 에피소드 ─────────────────────────────────────────────────
    "에피소드": "Episode",
    "묻는 것": "Question",
    "판정 방식": "How it is adjudicated",
    "지위": "Status",
    "결과": "Results",
    "**표현 감사**": "**Representation audit**",
    "세 태스크의 어휘·관계·CQ가 자원에 **실재하는가**":
        "Do the vocabulary, relations, and CQs of the three tasks **exist** in the resource?",
    "계수와 CQ 통과 여부 (결정론적)": "Counts and CQ pass/fail (deterministic)",
    "관측 사실": "Observed fact",
    "**게이트 판별력**": "**Discriminative power of the gate**",
    "의도적으로 주입한 결함을 게이트가 **검출하는가**, 정상 변경을 **거부하지는 않는가**":
        "Does the gate **detect** deliberately injected faults without **rejecting** sound changes?",
    "아직 판정한 적 없는 홀드아웃 결함 · 사전 지정한 세 조건":
        "Previously unadjudicated holdout faults and three prespecified conditions",
    "게이트 판별력에 대한 홀드아웃 산출물 평가 (확증 점검 목록에는 포함되지 않는다 · §4.5)":
        "Holdout artifact evaluation of the gate (not part of the confirmatory checks · §4.5)",
    "**통제된 자원 교체**": "**Controlled resource substitution**",
    "문서집합·설정을 고정하고 **자원만 교체하였을 때** 게이트의 판정은 무엇인가":
        "With documents and settings fixed and **only the resource replaced**, what is the verdict?",
    "사전등록된 승인식(T1·T2·T3)의 적용":
        "Application of the preregistered acceptance rule (T1, T2, T3)",
    "별도 사전등록 아래의 판정": "Verdict under a separate preregistration",
    "**검색 효용과 경계**": "**Retrieval utility and its boundary**",
    "온톨로지 보강이 강한 텍스트 기준선을 **개선하는가, 어디까지인가**":
        "Does ontology enrichment **improve** a strong text baseline, and **how far**?",
    "봉인 분할에 대한 사전등록된 확증 평가 — 모든 접근을 열람 원장에 기록 (비중복 확증 분할 둘)":
        "Preregistered confirmatory evaluation on sealed splits — all accesses were recorded in the "
        "access ledger (two non-overlapping confirmatory splits)",
    "확증 + 탐색적 진단": "Confirmatory plus exploratory diagnosis",
    "**이식 판정**": "**Port verdict**",
    "형식 층과 교차 태스크 층이 **자원을 바꾸어도 동일하게 작동하는가**":
        "Do the formal layers and the cross-task layer **behave the same on a different resource**?",
    "별도 사전등록 아래 홀드아웃 결함 21건과 실제 릴리스 계보 10판정 (승인식은 완성되지 않는다 · T1·T2 미이식)":
        "21 holdout faults and 10 verdicts on the real release lineage under a separate "
        "preregistration (the acceptance rule is not completed · T1 and T2 not ported)",
    # ── 표 1 · 관련연구 대비 위치 ────────────────────────────────────────────
    "연구 흐름": "Research strand",
    "대표 문헌": "Representative work",
    "남는 공백": "Remaining gap",
    "본 연구의 확장": "What this study adds",
    "특허 선행기술 검색과 그래프 활용":
        "Patent prior-art retrieval and the use of graphs",
    "그래프가 성능을 위한 입력 표현에 머물러, 그래프 자체의 변경 통제는 다루지 않는다":
        "The graph serves as an input representation for performance; controlling change in the "
        "graph itself is not addressed",
    "질의 인용 간선 마스킹과 시점·패밀리 분리 위에서, 검색 성능을 자원 변경의 승인 조건으로 "
    "사용하고 그 결합의 **성능 상한**까지 보고":
        "On top of query-citation masking and time/family separation, retrieval performance becomes "
        "an approval condition for resource change, and the **performance ceiling** of that "
        "coupling is reported",
    "온톨로지 품질·진화 검증": "Ontology quality and evolution validation",
    "변경이 온톨로지를 훼손하는가만 보고, 태스크를 훼손하는가는 보지 않는다":
        "Asks only whether a change damages the ontology, not whether it damages a task",
    "형식 검증 위에 3조건 태스크 게이트와 비열등 병합 규칙":
        "A 3-condition task gate and a non-inferiority merge rule on top of formal validation",
    "과제 기반 평가와 다운스트림 평가": "Task-based and downstream evaluation",
    "온톨로지를 비교·선택하는 **기준** 또는 완성 이후의 사후 비교로 사용되었다":
        "Used as a **criterion** for comparing and selecting ontologies, or as a post-hoc "
        "comparison once construction is finished",
    "같은 태스크 성능을 릴리스 **전** 승인식의 항으로 사용":
        "The same task performance becomes a term in the approval rule applied **before** release",
    "자원 지표를 유용성의 대리로 쓰는 관행":
        "The practice of treating resource indicators as proxies for utility",
    "어긋남이 상관 분석 수준에서 보고될 뿐 **통제된 사례와 그에 대한 결정**은 드물다":
        "The mismatch is reported at the level of correlation; **a controlled case and a decision "
        "taken on it** are rare",
    "자원 번들만 교체한 두 조건에서의 통제된 확인과 **승인 판정**(§5.3)":
        "Controlled confirmation in two conditions differing only in the resource bundle, and an "
        "**approval verdict** (§5.3)",
    "공학 정보학의 의미 표현·검증과 응용":
        "Semantic representation, validation and application in engineering informatics",
    "표현의 표준화·구조 준수·응용 성능은 제시되나 **변경의 승인 규칙**은 다루지 않는다":
        "Standardized representation, structural conformance and application performance are "
        "shown; **a rule for approving change** is not addressed",
    "사용 가능성이 아니라 **변경 수용 가능성**을 판정하고 실제 심사 기록을 제시(§5.3)":
        "Judges **whether a change may be accepted** rather than whether the resource is usable, "
        "and reports an actual review (§5.3)",
    "공유 그래프의 교차 도메인 활용": "Cross-domain use of a shared graph",
    "도메인 사이의 영향을 **관찰**하는 데 머문다":
        "Stops at **observing** influence between domains",
    "같은 영향을 승인 조건인 **교차 태스크 비회귀**로 집행":
        "Enforces the same influence as an approval condition — **cross-task non-regression**",
}

TABLE_CAP = re.compile(r"^\*\*표 (\d+)\.")
FIG_IMG = re.compile(r"^!\[그림 (\d+)\.[^\]]*\]\((.*)\)\s*$")
FIG_CAP = re.compile(r"^\*\*그림 (\d+)\.\*\*")


def translate_line(line: str) -> str:
    m = TABLE_CAP.match(line)
    if m:
        return CAPTIONS.get(f"T{m.group(1)}", line)
    m = FIG_IMG.match(line)
    if m:
        # alt 텍스트는 캡션을 재사용하지 않는다 — 같은 문장을 두 번 실으면 수치도 두 번 세어져
        # 불변 검사가 정당하게 실패한다(첫 구현에서 실제로 그랬다). 한국어 alt 가 담는 것은
        # 그림 번호와 짧은 제목이므로 영문도 그렇게 둔다.
        alt = CAPTIONS.get(f"F{m.group(1)}alt")
        if alt is None:
            fail(f"FIGURE {m.group(1)} 의 alt 텍스트가 CAPTIONS 에 없다 — 'F{m.group(1)}alt' 키")
        # 영문본은 한 단계 깊은 곳에 있다(`paper/submission/en/`) — 상대 경로를 그대로 옮기면
        # 그림이 죽는다. 깊이 차이는 배선이 알고 있으므로 사람이 세지 않는다.
        src = m.group(2)
        if src.startswith("../") and not src.startswith("../../"):
            src = "../" + src
        return f"![{alt}]({src})"
    m = FIG_CAP.match(line)
    if m:
        return CAPTIONS.get(f"F{m.group(1)}", line)
    if line.lstrip().startswith("|"):
        return "|".join(CELLS.get(p.strip(), p) for p in line.split("|"))
    return CELLS.get(line.strip(), line)


def translate(text: str) -> str:
    """그림 설명 문단은 캡션 한 줄로 접는다 — 영문 캡션이 그 문단을 대신한다."""
    lines = text.split("\n")
    out: list[str] = []
    folding = False
    for ln in lines:
        m = FIG_CAP.match(ln)
        if m:
            folding = True
            out.append(translate_line(ln))
            continue
        if folding:
            if not ln.strip():
                folding = False
                out.append(ln)
            continue                      # 한국어 설명의 나머지 행은 버린다
        out.append(translate_line(ln))
    return "\n".join(out)


def block_from_korean(korean: list[str], head_re: re.Pattern[str], kind: str, n: int) -> list[str]:
    """캡션 행부터 그 표(또는 그림 설명)까지만 가져온다.

    빈 줄 둘을 경계로 삼던 첫 구현은 표 하나를 요청했는데 다음 절 전체를 끌고 왔다. 경계는
    **구조**로 잡는다 — 표는 `|` 로 시작하는 연속 행이고, 그림 설명은 `**그림 n.**` 으로
    시작하는 한 문단이다.
    """
    starts = [i for i, ln in enumerate(korean) if head_re.match(ln)]
    if len(starts) != 1:
        fail(f"{kind} {n} 앵커가 {len(starts)}건 — 한국어 파생본에서 정확히 한 번 걸려야 한다")
    i = starts[0]
    out = [korean[i]]
    j = i + 1
    # 캡션이 여러 줄인 표가 있다(표 9). 캡션 줄바꿈은 조판 사정이고 구조가 아니므로, 표·그림
    # 본체가 시작되기 전까지의 연속 산문 줄은 **캡션 한 줄로 접는다**. 접지 않고 남겨 두면
    # 영문 캡션이 첫 줄만 대체하고 나머지 한국어 줄이 그대로 남아 수치가 두 번 세어진다.
    while (j < len(korean) and korean[j].strip()
           and not korean[j].lstrip().startswith(("|", "!["))):
        out[0] = out[0].rstrip() + " " + korean[j].strip()
        j += 1
    while j < len(korean) and not korean[j].strip():      # 캡션과 본체 사이의 빈 줄 하나
        out.append(korean[j])
        j += 1
    if kind == "TABLE":
        while j < len(korean) and korean[j].lstrip().startswith("|"):
            out.append(korean[j])
            j += 1
        if not any(ln.lstrip().startswith("|") for ln in out):
            fail(f"TABLE {n} 캡션 뒤에 표가 없다 — 앵커를 확인할 것")
    else:
        cap = re.compile(rf"^\*\*그림 {n}\.\*\*")
        while j < len(korean) and not cap.match(korean[j]):
            if korean[j].strip():
                fail(f"FIGURE {n} 이미지 뒤에 설명 문단이 바로 오지 않는다")
            out.append(korean[j])
            j += 1
        while j < len(korean) and korean[j].strip():
            out.append(korean[j])
            j += 1
    while out and not out[-1].strip():
        out.pop()
    return out


def build() -> str:
    if not PROSE.exists():
        fail(f"영문 산문 소스 부재 — {PROSE}")
    if not KOREAN.exists():
        fail(f"복사 원본 부재 — {KOREAN} (먼저 `make submission-stage3`)")
    korean = KOREAN.read_text(encoding="utf-8").split("\n")
    out = PROSE.read_text(encoding="utf-8")

    copied = 0
    residue: list[str] = []

    def render(kind: str, n: int) -> str:
        nonlocal copied
        if kind == "TABLE":
            head = re.compile(rf"^\*\*표 {n}\.")
        else:
            head = re.compile(rf"^!\[그림 {n}\.")
        block = "\n".join(block_from_korean(korean, head, kind, n))
        moved = translate(block)
        before, after = measurements(block), measurements(moved)
        if before != after:
            fail(f"{kind} {n} 치환에서 수치가 달라졌다 — {before} → {after}")
        for ln_no, line in enumerate(moved.split("\n"), 1):
            if HANGUL.search(line):
                residue.append(f"{kind} {n} L{ln_no}: {line.strip()[:110]}")
        copied += 1
        return moved

    out = TABLE_RE.sub(lambda m: render("TABLE", int(m.group(1))), out)
    out = FIGURE_RE.sub(lambda m: render("FIGURE", int(m.group(1))), out)

    # 참고문헌은 이미 영문 APA 다 — 다시 타자하면 서지가 갈린다(D-38 의 실패 형태).
    if "{{BIB}}" in out:
        starts = [i for i, ln in enumerate(korean) if ln.strip() == "# 참고문헌"]
        if len(starts) != 1:
            fail(f"참고문헌 표제가 {len(starts)}건 — 하나여야 한다")
        bib = "\n".join(korean[starts[0] + 1:]).strip()
        n_refs = sum(1 for ln in bib.split("\n") if ln.strip() and not ln.startswith("#"))
        out = out.replace("{{BIB}}", bib)
        print(f"[en] 참고문헌 {n_refs}행 복사")

    if residue:
        print("[en] 치환되지 않은 한글 — TERMS 에 추가하거나 산문으로 옮길 것:", file=sys.stderr)
        for r in residue:
            print(f"      {r}", file=sys.stderr)
        fail(f"한글 잔존 {len(residue)}행")

    print(f"[en] 복사한 표·그림 {copied}개 · 원본 {KOREAN.relative_to(ROOT)}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="조립 결과가 디스크와 같은지만 확인")
    args = ap.parse_args()

    text = build()
    if args.check:
        if not TARGET.exists() or TARGET.read_text(encoding="utf-8") != text:
            fail(f"{TARGET.relative_to(ROOT)} 이 산문 소스와 어긋난다 — 다시 조립할 것")
        print("[en] 대조 통과")
        return 0
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(text, encoding="utf-8")
    print(f"[en] 생성: {TARGET.relative_to(ROOT)} ({len(text):,}자)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
