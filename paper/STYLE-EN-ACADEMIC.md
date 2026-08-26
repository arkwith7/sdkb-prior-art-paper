# 영문 학술 논문 문체 규격 v1.1 (`Results in Engineering` 투고용 · 2026-08-22 초안 · 2026-08-26 S5 개정)

> **이 문서의 자리.** [STYLE-KO-ACADEMIC.md](STYLE-KO-ACADEMIC.md) v2 가 한국어 산문 소스
> (`paper/manuscript/stage3_source.md`)의 어체를 정하듯, 이 문서는 **영문 산문 소스**
> (`paper/manuscript/en_source.md`)의 어체와 **국문 논지의 영문 재진술 규칙**을 정한다.
> **번역 규칙이 아니다 (2026-08-26 개정 · 사용자 승인)** — 영문 원고는 국문을 문단 단위로 옮긴
> 것이 아니라 **같은 논지·판정·수치를 영어 학술 관행으로 다시 진술한 것**이며, 그 경계를 긋는
> 것이 S5 다.
> 용어의 확정어는 [glossary.md](glossary.md)(용어 대장)가 정본이며, 이 문서는 그 대장을
> **문장 수준**으로 확장한다 — 낱말이 맞아도 구문이 다르면 주장 강도가 바뀌기 때문이다.
>
> **적용 범위는 한국어 규격과 같다 — "내용 보존 + 표현 재구성".** 수치·판정·기여·장 구성은 이
> 규격으로 바꾸지 않으며, 바꿀 수 있는 것은 **그 내용을 문장으로 세우는 방식**뿐이다. 표·그림·캡션은 `scripts/build_submission_en.py` 가 한국어 파생본에서
> 복사하고 `TERMS` 로 치환하므로 **영문 산문에서 다시 타자하지 않는다**(CLAUDE.md §1-1).
>
> **강제 대상 (기계 검사 `make style-check-en`)** — `paper/manuscript/en_source.md` ·
> `paper/submission/en/**/*.md`. 검사기는 `scripts/style_check_en.py`.

---

## 0. 왜 별도 규격인가 — 한국어 규격이 영어에서 깨지는 자리

한국어 규격 v2 의 규칙 아홉은 대부분 영어에도 그대로 성립한다(길이 상한 · 은유 금지 · 볼드 제한 ·
소제목 명사구 · 번호 연번). 그러나 셋은 **언어가 바뀌면 방향이 뒤집힌다.**

| 한국어에서 | 영어에서 | 이유 |
|---|---|---|
| 주어 생략 금지(T4) → "본 연구는"으로 통일 | **`we` 를 쓴다** (not "this study") | AEI 를 포함한 Elsevier 공학 저널은 1인칭 복수를 허용하며, "this study shows" 연쇄는 피동·명사화를 부르고 주어–행위 대응을 흐린다 |
| 단문 연쇄 금지(T1) → 연결어로 잇는다 | **짧은 문장을 허용한다** (≤ 25 단어) | 영어는 주어-동사가 앞에 오므로 단문이 도치로 읽히지 않는다. 한국어에서 90자로 자른 문장을 영어에서 다시 합치면 종속절이 중첩된다 |
| 격식 문어 종결(~하였다) | **시제로 역할을 가른다** | 한 일(과거) · 결과/표가 보이는 것(현재) · 주장·원리(현재) · 후속 과제(미래/조건) |

그리고 **판정 강도**는 양쪽 모두에서 가장 세지기 쉬운 자리다. 한국어 "부분 지지"를 *partial
support* 로, "확증하지 못했다"를 *did not transfer* 로 옮기는 순간 `verdicts.yaml` 위반이 된다
(§4).

---

## 1. 구조 규칙 (S)

**S1 · 문단 = topic sentence → evidence → so-what.** 한국어 S1 과 동일. 첫 문장만 이어 읽어도
절의 논리가 따라가야 한다. 영어에서는 topic sentence 가 **주어 + 타동사 + 목적어**의 능동문이어야
한다. *"It was observed that recall decreased"* 는 topic sentence 가 아니다 — *"The substitution
reduced recall"* 이다.

**S2 · 한 문장 = 한 명제, 종속절 ≤ 1.** 한국어 S2 와 동일. 관계절(which/that)과 분사구를 한
문장에 함께 두지 않는다.

**S3 · 문장 길이 상한 30 단어, 권고 25.** — *기계 검사 대상.* 서지 인용 `(Lupu & Hanbury, 2013)`,
수식, 괄호 안의 기호·수치는 길이에서 제외한다(한국어 S3 의 원어 병기 제외와 같은 이유).

**S4 · 전개 순서는 general → specific.** 한국어 S4 와 동일.

**S5 · 한국어 한 절 = 영어 한 절** (2026-08-26 개정 · 사용자 승인 · 구 규칙은 *"한 문단 = 한
문단"*). **문단 단위의 잠금을 푼다** — 영문은 국문을 옮긴 것이 아니라 **같은 논지를 영어 학술
관행으로 다시 진술한 것**이므로, 문단의 분합과 전개 순서는 영어의 요구를 따른다.

**왜 바꾸는가.** 구 규칙이 실제로 지키던 것은 문단 수가 아니라 셋이었다 —
① `{{TABLE:n}}`·`{{FIGURE:n}}` 의 자리 ② 절 참조(§)의 D9 도달성 ③ 산문 수치의 국문 대조.
**이 셋은 전부 절 단위로 지켜진다.** 실측(2026-08-26)으로 `build_submission_en.py` 는 문단
대응을 **검사하지 않고**(표·그림 블록의 수치 불변만 강제하며), `style_check_en` 도 S5 를 보지
않는다(§8). 즉 문단 잠금은 **기계가 지키던 것이 아니라 사람이 지키던 것**이었고, 그 대가로
영문 산문이 한국어의 문단 리듬을 그대로 이고 다녔다.

**절 단위로 지키는 것 셋 — 이것이 S5 의 실체다.**

1. 국문 §X 에 있는 `{{TABLE:n}}`·`{{FIGURE:n}}` 는 영문 §X 에도 **빠짐없이** 있다.
2. 국문 §X 가 인용하는 `§` 참조는 영문 §X 에서도 도달 가능하다(D9).
3. 국문 §X 산문의 수치 집합과 영문 §X 산문의 수치 집합이 같다(§9-2 `numdiff` · 절 단위).

**푸는 것과 풀지 않는 것을 가른다.** 문단의 분합·순서·연결은 자유이나, **국문에 없는 판정·수치·
주장을 영문에서 만들지 않는다.** 이것은 문체 규칙이 아니라 CLAUDE.md §1-1·§1-2 이며 이 개정의
대상이 아니다. 영문 고유의 문장은 **연결·로드맵·정의의 자리에서만** 허용된다.

---

## 2. 어체 규칙 (T)

**T1 · 주어는 `we` / the artifact / the result.** 연구 주체는 `we`, 산출물은 그 이름(`the gate`,
`SDKB`, `T3`), 결과는 측정 대상(`family Recall@100`)이다. *this paper / this study / the present
work* 는 절 도입의 로드맵 문장(*This section describes …*)에서만 쓴다. — *기계 검사: 본문에서
`this study`·`the present study` 가 문단당 1회를 넘으면 경고.*

**T2 · 시제 규약.**

| 내용 | 시제 | 예 |
|---|---|---|
| 수행한 절차·실험 | simple past | *We froze the thresholds before unsealing.* |
| 표·그림이 지금 보여주는 것 | simple present | *Table 7 reports the swap result.* |
| 결과로 성립하는 주장·설계원리 | simple present | *A change that passes every formal layer can still reduce recall.* |
| 판정 기록의 인용 | simple past + 사전등록 명시 | *Under the first preregistration the verdict was "supported for the primary metric only".* |
| 후속 과제 | conditional / future | *Separating the two causes would require df weighting.* |

**T3 · 피동은 행위자가 무의미할 때만.** *was frozen* · *was sealed* · *is reported in* 은 허용한다.
*It was found that* · *It can be seen that* · *It should be noted that* 는 금지한다. — *기계 검사
대상.*

**T4 · 명사화를 동사로 되돌린다.** 한국어 "~의 수행" · "~의 확인" · "~의 도출" 은 영어에서
`perform/confirm/derive` 로 푼다. *the performance of the evaluation of* 같은 of-사슬 금지 —
*기계 검사: `of ... of ... of` 3중 연쇄 경고.*

**T5 · 볼드는 정의된 용어의 최초 등장에만.** 한국어 T5 와 동일. — *기계 검사: 볼드 안에 finite
verb(is/are/was/were/does/can/…)가 있으면 주장 문장이다.*

**T6 · 강조 부사 금지.** *clearly · obviously · significantly(통계 의미 아닐 때) · very · quite ·
extremely · importantly · interestingly · remarkably · notably*. 통계적 유의를 말할 때의
*significantly* 는 `p` 또는 CI 가 같은 문장에 있을 때만 허용한다. — *기계 검사 대상.*

**T7 · 은유·구어 금지 — 한국어 T2 의 영문 대응.** 한국어 규격이 금지한 은유는 영어에서도 쓰지
않는다. 한국어에서 이미 학술어로 치환되었으므로 영문은 그 치환어를 옮기면 된다. 아래는 영어에서
새로 생기기 쉬운 구어이다. — *기계 검사 대상.*

| 금지 | 치환 |
|---|---|
| break / breaks (a task, a path) | degrade · impair · disrupt |
| kill / dies | eliminate · is removed |
| catch (a fault) | detect |
| grab / pull (documents) | retrieve |
| swap in / swap out / plug in | substitute · replace · apply |
| blow up / explode (a metric) | increase sharply |
| leak / leaks (as verb for regression) | propagate — *leakage* 는 qrel 누출의 고정어이므로 회귀에 쓰지 않는다 |
| ceiling (undefined) | **reranking ceiling** — 첫 등장에 정의 1회 후 허용 |
| ladder | reachability by observation level |
| haystack | large candidate pool |
| readout | evaluation · analysis |
| instrument (for an evaluation) | evaluation procedure · measurement |
| sanity check | preliminary check |
| resolution (뜻이 넷) | concept density · observation level · matching unit · check granularity |

**T8 · 철자·구두점.** **미국식 철자**로 통일한다(*analyze, behavior, modeling, center*). AEI 는
둘 다 받지만 한 원고 안의 혼용은 데스크 지적 사항이다. 옥스퍼드 콤마를 쓴다. 소수점은 `.`,
천 단위 `,`. 음수는 `−`(U+2212), 범위는 `–`(en dash). — *기계 검사: 영국식 철자 목록 경고.*

**T9 · 축약형 금지.** *don't · can't · it's · we've*. — *기계 검사 대상.*

---

## 3. 한국어 → 영어 구문 전환표 (C)

용어 대장(glossary.md)이 **낱말**을 고정한다면 이 표는 **구문**을 고정한다. 한국어 규격 v2 가 만든
문장 패턴마다 영어 대응 패턴을 하나씩 둔다. 번역자(사람이든 LLM이든)는 이 표 밖의 구문을 만들지
않는다.

| # | 한국어 패턴 (규격 v2) | 영어 패턴 | 비고 |
|---|---|---|---|
| C1 | 본 연구는 X를 제안한다 | **We propose X.** | *This paper proposes* 는 로드맵 문장에서만 |
| C2 | 본 논문은 이 현상을 **X(x-y)** 라 정의한다 | **We call this phenomenon *X*.** / **We define *X* as …** | 볼드는 한국어와 같은 자리 1회 |
| C3 | X는 Y가 아니라 Z이다 | **X is Z, not Y.** | 긍정을 앞에. *X is not Y; it is Z* 는 강조가 필요할 때만 |
| C4 | ~로 나타났다 / ~가 관측되었다 | **We observed …** / **X showed …** | *It was observed that* 금지(T3) |
| C5 | ~가 요구된다 | **X requires …** / **X must …** | *is required* 는 행위자가 규범(저널·규정)일 때만 |
| C6 | 첫째·둘째·셋째 (세 항목) | **First, … Second, … Third, …** 또는 세 문장 | 중점(·) 나열은 and/or 로 관계를 명시 |
| C7 | A·B·C (중점 나열) | **A, B, and C** | 같은 층위인지 먼저 판단. 아니면 문장으로 푼다 |
| C8 | ~에 한정된다 / ~로 한정한다 | **is confined to** / **we restrict … to** | *limited* 는 한계(limitation)의 뜻과 충돌하므로 범위에는 쓰지 않는다 |
| C9 | 다만 / 반면 | **However,** / **By contrast,** | 문장 첫머리. 한국어 T3 의 표준 연결어에 대응 |
| C10 | 따라서 / 요컨대 | **Therefore,** / **In short,** | *So* · *Thus* 문두 금지 |
| C11 | ~는 …의 증거가 아니다 | **X is not evidence of Y.** | *does not prove* 로 세우지 않는다 |
| C12 | 본 연구는 X를 주장하지 않는다 | **We do not claim X.** | 한국어의 방어 서술은 영어에서 **한 문장**으로 줄인다 |
| C13 | X는 결과 확인 이전에 동결하였다 | **X was frozen before unsealing.** | `frozen`·`sealed`·`pinned` 는 대장 D절 고정어 |
| C14 | 사전등록된 | **preregistered** (한 단어) | *pre-registered* 혼용 금지 |
| C15 | 홀드아웃 | **holdout** | *held-out* 은 형용사 자리에서만 |
| C16 | 두 분할에서 반복 관측됐다 | **was observed in both splits** | *replicated* 금지 — 통계적 재현을 단정한다(§4) |
| C17 | 가르지 못하였다 / 구분하지 못하였다 | **does not separate A from B** / **we could not distinguish A from B** | *cannot tell* 금지 |
| C18 | 지위. (§5 각 절의 소문단) | **Status.** | 소제목 대신 run-in bold 유지 |
| C19 | ①②③ 열거 | **(i) (ii) (iii)** | 원문자는 영어 조판에서 깨진다 |
| C20 | §5.3 / 표 7 / 그림 4 | **Section 5.3 / Table 7 / Fig. 4** | 문장 첫머리에서는 *Figure 4*; 절 참조 `§` 기호는 영문에서도 허용하되 한 원고에서 한 방식 |

---

## 4. 판정 강도 규칙 (V) — `verdicts.yaml` 의 영문 대응

> **이 절이 이 규격의 존재 이유다.** 한국어 §0.8 문구 사전은 한국어 문장만 본다. 영문에서는 같은
> 판정이 더 세게 읽히는 관용구가 따로 있다. 아래 허용/금지는 glossary.md E절과 일치하며, 확정 시
> `verdicts.yaml` 에 `en:` 열로 옮긴다. **영문 열의 확정은 사용자 승인 사항이다.**

| 대상 | 허용 (영문) | 금지 (영문) |
|---|---|---|
| H3 합성 | *The preregistered composite prediction held in neither split; deep recall improved in both.* | ~~partially supported~~ · ~~replicated~~ · ~~confirmed in both splits~~ |
| H3 분할 A 기록 | *supported for the primary metric only* | ~~partial support~~ |
| H3 분할 B 기록 | *not supported* | ~~rejected~~ · ~~refuted~~ · ~~failed~~ |
| H5 | *rejected — an observed cross-task dependency* / *not reproduced; no verdict can be issued* | ~~failed to replicate~~ · ~~dynamic task coupling~~ · ~~entanglement~~ |
| H2 | *the safety of accepted changes was not tested* | ~~the gate guarantees~~ · ~~ensures safety~~ · ~~proves safe~~ |
| T4 | *we could not confirm transfer* · *absence of transfer and insufficient power are not distinguished* | ~~did not transfer~~ · ~~no transfer~~ · ~~RAG performance~~ · ~~inconclusive~~(단독) |
| P0/P1 | *the prespecified primary configuration did not reach significance; the secondary configuration improved in both splits* | ~~the main system~~ · ~~+0.0534 improvement~~(구성 미표기) |
| 자원 교체 | *a change that improves resource-side metrics and passes all formal validation can still degrade task performance* · *the cause (resource vs. scoring function) is not separated* | ~~resource metrics do not represent task performance~~ (무조건 일반형) · ~~proves that~~ |
| 봉인 | *all accesses were recorded in the access ledger* | ~~unsealed once~~ (원장 없이) |
| 효과 일반 | *improved* · *reduced* · *was observed* | ~~robust~~ · ~~consistent~~ · ~~strong evidence~~ · ~~clearly shows~~ · ~~demonstrates conclusively~~ |
| 한계 | *we did not* · *was not tested* · *remains untested* | ~~beyond the scope~~ (회피 관용구) · ~~future work will~~ (미래 단정) |

**헤징의 위치.** 영어는 헤지를 **동사**에 둔다(*may degrade* · *can still reduce*). 부사
헤지(*possibly · perhaps · arguably*)는 쓰지 않는다. 조건부 주장은 **if/when 절을 앞에** 둔다:
*When documents, code, and settings are frozen, substituting the resource bundle reduced recall.*

— *기계 검사: 위 금지 열을 정규식으로 본다(`VERDICT_FORBIDDEN_EN`).*

---

## 5. 소제목 규칙 (H)

**H1 · 소제목은 명사구, Title Case 가 아닌 Sentence case.** 한국어 H1 과 동일. 서술형·의문형 금지.
— *기계 검사: 제목이 finite verb 를 포함하거나 `?` 로 끝나면 위반.*

| 서술형 (금지) | 명사구형 |
|---|---|
| Why the negative control failed | Rejection of the negative control and cross-task dependency |
| Metrics diverge across layers | Cross-layer metric misalignment |
| How far does the gain reach? | Boundary of the retrieval gain |

**H2 · 장 제목의 고정 영문.** 한국어 파생본과 1:1 로 대응해야 D9 가 같은 결과를 낸다.

| 한국어 | 영문 |
|---|---|
| 1. 서론 | 1. Introduction |
| 2. 배경과 연구 공백 | 2. Background and research gap |
| 3. 산출물 — SDKB 데이터셋과 T-gate | 3. Artifacts — the SDKB dataset and the T-gate |
| 4. 평가 설계 | 4. Evaluation design |
| 5. 평가 결과 (EP1–EP4) | 5. Evaluation results (EP1–EP4) |
| 6. 논의 · 설계지식 · 결론 | 6. Discussion, design knowledge, and conclusion |
| 약어표 | Nomenclature |
| AI 사용 고지 | Declaration of generative AI use |
| 참고문헌 | References |

---

## 6. AEI 투고 규정 (J) — 협상 대상이 아니다

| 항목 | 규정 | 검사 |
|---|---|---|
| 초록 | ≤ 250 단어 · 한 문단 · 인용·약어 정의 없음 | `submission_check` D7 |
| 키워드 | ≤ 7 | D8 |
| Highlights | 3–5 불릿 · 각 ≤ 85자(공백 포함) · `paper/submission/en/highlights.md` | `style_check_en` |
| 서지 | APA 7 (Elsevier "Name–Year") · DOI 포함 | `build_submission_stage3` BIB 고정 |
| 그림 | 벡터(SVG→PDF/EPS) · 캡션은 본문 아래 · 색만으로 의미 전달 금지 | FIGURE-SPEC.md |
| 데이터 가용성 | 별도 절(§6.6) + Declarations 파일 | `paper/submission/en/declarations.md` |
| 생성형 AI 고지 | Elsevier 정책 문구 — 본문 작성 보조 범위와 검증 책임 명시 | 고정 문단(§5 H2) |

---

## 7. 이 저장소에서의 예외 (규격보다 우선한다)

1. **판정 문구는 §4 와 glossary.md E절이 우선한다.** 어체를 이유로 판정 문구를 고치지 않는다.
2. **표 셀·캡션은 영문 산문에서 고치지 않는다.** `build_submission_en.py` 의 `TERMS` 로만 치환한다.
   치환어는 glossary.md 의 "영문 확정어" 열과 일치해야 한다.
3. **수식·코드·식별자·서지는 검사 대상이 아니다.**
4. **언급은 사용이 아니다.** 금지어를 *"we do not use the term X"* 형태로 인용하는 것은 위반이
   아니며, 검사기는 따옴표·백틱 안을 세지 않는다.
5. **행 단위 면제** — `<!-- style-ok: reason -->`. 사유 없는 면제는 두지 않는다.

---

## 8. 검사기가 보는 것과 보지 못하는 것

`scripts/style_check_en.py`(= `make style-check-en`)는 **S3 · T1(경고) · T3 · T4(경고) · T5 · T6 ·
T7 · T8(경고) · T9 · H1 · V(금지 판정 문구) · J(Highlights 길이)** 를 본다. **S1 · S2 · S4 · S5 ·
T2 · C1–C20 은 사람이 지킨다.** 검사기 통과는 필요조건이지 충분조건이 아니다.

**차단으로 승격했다 (2026-08-26 · PLAN-080 A-⑤ · 사용자 승인).** 경고 모드였던 이유는 영문
본문이 완성되기 전이었기 때문이고, 승격 시점 실측은 **위반 0 건**이다(산문 소스 · 조립 산출물 ·
cover-letter · declarations · highlights). 이제 *"영문 문체 검사 통과"* 를 근거로 쓸 수 있다.

**두 가지 배제를 명시한다 — 둘 다 규격이 이미 요구하던 것이고 구현만 없었다.**

| 배제 | 근거 | 구현 |
|---|---|---|
| S3 의 길이에서 **서지 인용·수식·괄호 속 기호와 수치**를 뺀다 | 위 §1 의 S3 본문 | `countable_words()` |
| **표·그림 캡션**은 길이(S3)·볼드(T5)의 대상이 아니다 · 어휘 규칙(T6·T7·T9·V)은 그대로 적용한다 | 캡션은 산문이 아니라 라벨이다 — 한국어 검사기가 같은 자리에서 하는 일과 같다 | 캡션 분기 |

**캡션 배제가 필요해진 시점은 산출 경로 승격이다.** 그전까지 캡션은 검사 대상 트리 밖의 초안
파일에만 있었고, `paper/submission/en/` 으로 옮기면서 처음으로 검사에 들어왔다.

---

## 9. 회귀 점검 — 전환이 내용을 손상시키지 않았는가

번역 커밋마다 아래 넷을 확인한다.

1. **절 대응** — 국문 §X 의 표·그림 지시자와 `§` 참조가 영문 §X 에 전부 있는가(S5 의 셋).
   **문단 수는 세지 않는다**(2026-08-26 개정).
2. **수치 불변** — `build_submission_en.py` 가 표·그림에서 강제한다. 산문 안의 수치는 아래
   `numdiff` 와 같은 방식으로 한국어 산문과 대조하되 **대조 단위는 절**이다(§번호·표/그림 번호·
   라벨 기호 제외). **국문 §X 에 없는 수치가 영문 §X 에 나타나면 그것은 문체 위반이 아니라
   §1-1 위반이다.**
3. **판정 강도** — §4 금지 열 0건. 영문에서 새로 생긴 *replicated · robust · demonstrates* 를 특히
   본다.
4. **용어 단일성** — 같은 개념에 영문 둘이 쓰이지 않았는가(`downstream task` 하나 · `misalignment`
   하나 · `unobserved` 하나). glossary.md G절 결정 D-1~D-5 를 그대로 적용한다.

---

## 부록 A. 한국어 v2 ↔ 영문 v1 규칙 대응표

| 한국어 v2 | 영문 v1 | 관계 |
|---|---|---|
| S1 문단 구조 | S1 | 동일 |
| S2 한 문장 한 명제 | S2 | 동일 |
| S3 90자 | S3 30단어 | 단위 변환 |
| S4 일반→구체 | S4 | 동일 |
| — | S5 절 대응 | 신설 (영문 재진술 전용 · 2026-08-26 문단 → 절) |
| T1 격식 문어체 | T2 시제 규약 | **역할 변경** — 종결어미 대신 시제 |
| T2 은유·구어 금지 | T7 | 동일 + 영어 구어 추가 |
| T3 문두 접속어 | C9·C10 | 구문표로 이관 |
| T4 주어 생략 금지 | T1 `we` | **방향 반전** |
| T5 볼드 제한 | T5 | 동일 |
| T6 표·캡션·제목에도 적용 | §7-2 | 경로 동일 (`TERMS`) |
| T7 축약형 금지 | T9 | 동일 |
| V1–V6 용어·번호 | glossary.md + S5 | 대장으로 이관 |
| H1 명사구 제목 | H1 | 동일 + Sentence case |
| §0.8 판정 문구 | §4 V | **영문 대응 신설** |
