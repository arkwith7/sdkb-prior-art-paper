# 용어 대장 — 한국어 초안 → 영문 투고본 전환의 고정 사전

> **이 파일의 목적.** 초안은 한국어로 쓰고 최종본은 영어로 낸다. 그 사이에서 **뜻이 바뀌는 자리는
> 어려운 단어가 아니라 용어 표류**다 — 같은 개념을 한국어에서 두세 가지로 부르면 영문에서 서로 다른
> 단어로 갈리고, 갈린 뒤에는 되돌릴 방법이 없다. 그래서 **영문 확정어를 초안 단계에서 못박는다.**
>
> **적용 범위(현재).** §2 배경과 연구 공백 + §2가 처음 쓰고 뒤 장이 반복하는 교차 용어.
> §5·§1·§7·§6 은 이 대장이 검증된 뒤 순차 확대한다.
>
> **이 파일은 원고가 아니다.** 판정·수치·라벨을 하나도 바꾸지 않으며 CLAUDE.md §2.2(원고 기조 변경)
> 대상이 아니다. 다만 **아래 D절(판정 문구)만은 §0.8·`verdicts.yaml`과 짝이므로 그 조항의 규율을
> 따른다** — 영문 열의 확정은 사용자 승인 사항이다.

---

## 0. 세 가지 등급 — 무엇을 바꿔도 되고 무엇을 못 바꾸나

| 등급 | 대상 | 규칙 |
|---|---|---|
| **불변** | 라벨(H3·H5·T1–T4·L0–L3·EP1–EP4·DP1–DP6·DRQ·RQ·A1–A8·B0–B5·P0–P2·S1–S5) · 지표명(Recall@100·nDCG@20·MRR·McNemar·Holm·95% CI) · 기호(ε·δ·η) | **한국어에서도 영어에서도 그대로 쓴다.** 쉬운 말로 바꾸면 다른 것을 가리킨다 |
| **고정** | 아래 A–C 표의 "영문 확정어" | 초안에서 한국어 표현이 흔들려도 **영문은 이 열 하나로만** 옮긴다 |
| **자유** | 설명 문장·예시·연결어 | 쉬운 쪽으로 마음껏 고쳐 쓴다 |

---

## A. §2.1 — 선행기술 검색의 평가와 정답의 성질

| 쉬운 한국어 (본문에서 쓰는 말) | 한국어 정식 용어 (첫 등장 1회 병기) | **영문 확정어** | 주의 |
|---|---|---|---|
| 앞선 기술을 찾는 일 | 선행기술 검색 | **prior art search** | 시스템·순위 산출을 가리킬 때만 `prior art retrieval`. 두 말을 한 문단에서 섞지 않는다 |
| 상위 K건 안에 얼마나 건졌는가 | 회수율 | **Recall@K** | 불변 |
| 같은 발명의 다른 나라 출원을 한 건으로 세기 | 패밀리 단위 | **family-level** | `family_id`(DOCDB)와 구분해 쓴다 |
| 심사관이 실제로 든 문헌 | 심사관 인용 | **examiner citation** | |
| 출원인이 스스로 적어 낸 문헌 | 출원인 인용 | **applicant citation** | 둘을 `citation` 하나로 합치지 않는다 — 생성 과정이 다르다 |
| 실제로 관측된 "맞다" 신호 | 관측된 양성 | **observed positive** | |
| 인용되지 않았을 뿐 아닌 것은 아님 | 미관측 | **unobserved** | ⚠ 현재 원고는 `미관측(unknown)`으로 병기 — **`unknown`을 버리고 `unobserved`로 통일 권고**(D-1) |
| 심사관 기록에 기댄 불완전한 정답 | 심사관 검증 약한 정답 | **examiner-validated weak ground truth** | 이미 원고에 병기됨 |
| "맞다"만 있고 "아니다"가 없는 채점표 | 양성 전용 qrel | **positive-only qrel** | |
| 적합성 판단 목록 | qrel | **relevance judgments (qrel)** | 불변 표기 |
| 아니라고 판정된 문헌의 집합 | 판정된 비적합 집합 | **judged non-relevant set** | bpref 배제 근거의 핵심어 |
| 서로 다른 언어 사이를 건너는 검색 | 교차언어 검색 | **cross-lingual retrieval** | ⚠ 코퍼스의 성질은 **multilingual**, 검색 행위는 **cross-lingual**. 현행 한국어는 둘을 옳게 나눠 쓰고 있으나 영문에서 둘 다 `multilingual`로 무너지기 쉽다(D-2) |
| 언어에 매이지 않는 개념 식별자 | 언어중립 개념 IRI | **language-neutral concept IRI** | |
| 세 번째 길 | 제3의 통로 | **third pathway** | `channel`·`route`로 흔들지 않는다 |
| 미리 세운 가설이 아니라 살펴본 결과 | 탐색적 진단 | **exploratory diagnosis** | C절 `exploratory`와 같은 말 |

---

## B. §2.2 — 온톨로지 품질과 진화 검증

| 쉬운 한국어 | 한국어 정식 용어 | **영문 확정어** | 주의 |
|---|---|---|---|
| 온톨로지가 답할 수 있어야 하는 질문 목록 | 역량질문(CQ) | **competency question (CQ)** | 약어표에 있음 |
| 검사 항목을 먼저 쓰고 온톨로지를 만드는 방식 | 테스트 주도 온톨로지 개발 | **test-driven ontology development** | |
| 구조가 규칙에 맞는지 보는 검사 | 구조 제약 검증 | **structural constraint validation** | SHACL은 불변 |
| 무엇이 어떠했는지 **적어 두는** 평가 틀 | 사후 기술 평가 틀 | **descriptive evaluation framework** | ⚠ **`post hoc`를 쓰지 않는다** — 그 말은 이 논문에서 "결과를 본 뒤 고치는 것"(§1-2)을 뜻한다(D-3) |
| 다 만든 뒤에 견주어 보는 것 | 사후 비교 | **retrospective comparison** | 같은 이유로 `post hoc comparison` 금지 |
| 온톨로지가 바뀌는 것을 다루는 연구 | 온톨로지 변화 관리 | **ontology change management** | |
| 온톨로지가 자랄 때 그 변경을 검사하는 일 | 온톨로지 진화 검증 | **ontology evolution validation** | |
| 내보내기 **전에** 받아들일지 정하는 검사 | 릴리스 전 승인 게이트 | **pre-release acceptance gate** | ⚠ `approval`이 아니라 **acceptance** — 승인식 `Accept(ΔG)`와 같은 말이어야 한다 |
| 쓰는 일에서의 성능 | 하류 태스크 성능 | **downstream task performance** | |
| 돌아간다는 것을 보여 주기 | 시연 | **demonstration** | |
| **"쓸 수 있는가"가 아니라 "바꿔도 되는가"** | — | **"can it be used?" vs "may it be changed?"** | 논문의 캐치프레이즈 · 영문에서도 한 쌍으로 유지 |
| 신선도·구조·논리·기능 네 가지 검사 | 형식 검증 L0–L3 | **formal validation (L0–L3)** | `verification`으로 흔들지 않는다 |

---

## C. §2.3 — 자원 지표의 대표성 · 평가 층 · 통제된 교체

| 쉬운 한국어 | 한국어 정식 용어 | **영문 확정어** | 주의 |
|---|---|---|---|
| 다른 성과를 간접적으로 나타내는 값 | 대리 지표 — 본문에서는 문맥에 맞게 `자원 지표`로 풀어 씀 | **proxy metric** | `surrogate`로 흔들지 않는다 |
| 대신 잴 수 있는가 | — | **stand in for** | |
| 어휘·링크·해상도를 보는 층 | 자원 층 | **resource layer** | §1.1에서 도입 |
| 순위를 재는 층 | 검색 층 | **retrieval layer** | |
| 찾은 문헌으로 답을 만드는 층 | 생성 층 | **generation layer** | |
| 층마다 지표가 **어긋난다** | 층간 지표 불일치 | **cross-layer metric misalignment** | ⚠ 명사는 `misalignment` 하나로 고정. 동사로 풀 때만 `diverge`(D-4) |
| 자원 자체만 보는 평가 | 내재적 평가 | **intrinsic evaluation** | 짝은 `extrinsic` |
| 온톨로지를 실제 일에 꽂아 결과로 재는 평가 | 과제 기반 평가 | **task-based (application-based) evaluation** | 이미 원고에 병기됨 |
| 여러 온톨로지 중 하나를 **고르는 잣대** | — | **selection criterion** | 계보 3단계의 1단 |
| 승인식 안의 한 항 | 승인식의 항 | **term in the acceptance rule** | 수식의 term |
| 문서·설정을 다 고정하고 **자원만 갈아 끼우기** | 통제된 자원 교체 | **controlled resource substitution** | **DP4의 이름** — 흔들면 설계원리 표가 깨진다 |
| 성능이 떨어지지 않았는지 보는 검사 | 비열등성 검정 | **non-inferiority test** | T1의 정의 |
| 다른 갈래가 뒷걸음치지 않았는지 | 교차 태스크 비회귀 | **cross-task non-regression** | T3의 정의 |

---

## D. 교차 용어 — §2가 처음 쓰고 뒤 장이 반복한다

| 쉬운 한국어 | 한국어 정식 용어 | **영문 확정어** | 주의 |
|---|---|---|---|
| 온톨로지를 실제로 **쓰는 일** | 하류 태스크 | **downstream task** | ⚠ 원고 전반에서 "쓰는 일/쓰는 쪽"으로 반복 — 영문은 이 한 단어로만(D-5) |
| 결과를 보기 전에 정해 둔 검사 | 확증 | **confirmatory** | |
| 정해 두지 않고 살펴본 것 | 탐색 | **exploratory** | |
| 시작 전에 적어서 커밋해 둔 것 | 사전등록 | **preregistration** | |
| 최종 비교 전까지 열지 않는 것 | 봉인 / 개봉 | **sealed / unsealing** | |
| 평가 규칙·임계를 못박는 것 | 동결 | **freeze (frozen)** | |
| 데이터셋 판본을 해시로 붙잡는 것 | 고정 | **pin (pinned)** | ⚠ §4.3이 이미 둘을 구분한다 — 영문에서 합치지 않는다 |
| 검색 층의 이득이 생성 층으로 옮겨가는지 | 전달 | **transfer** | C2′의 이름 · `propagation` 금지 |
| 같은 실험을 다른 방식으로 **읽어내기** | 판독 | **readout** | "두 번째 벤치마크가 아니다"의 근거어 |
| 재정렬 방식이 만드는 한계 | 천장 | **ceiling** | 첫 등장에 정의 1회: *재순위화가 후보 집합을 넓히지 못해 생기는 상한* |
| 해상도를 달리해 층층이 적은 도달성 표 | 도달성 사다리 | **reachability ladder** | 은유 유지 · 첫 등장에 위 정의를 반드시 붙인다 |
| 방해문서까지 포함한 검색 대상 전체 | 후보 모집단 | **candidate pool** | 방해문서 = `distractors` |
| 표현할 수 있는 범위 | 표현 범위 | **representational scope** | |
| 실제 성능이 검증된 정도 | 과제 검증 깊이 | **task-level validation depth** | ⚠ 위와 **한 쌍으로만** 등장 — 논문의 방어선 |
| 게이트에 맞춰 온톨로지가 기우는 것 | 게이트 유발 표류 | **gate-induced drift** | §8.4 |

---

## E. 판정 문구 — 영문 전환에서 가장 세지기 쉬운 자리

> **이 절은 CLAUDE.md §0.8·`paper/verdicts.yaml`의 영문 대응이다.** 아래 영문 열은 **초안(제안)**
> 이며 확정에는 사용자 승인이 필요하다. 승인되면 `verdicts.yaml`에 영문 열로 옮긴다.

| 한국어 판정 문구 (§0.8 허용형) | **영문 제안** | 쓰면 안 되는 영문 |
|---|---|---|
| 부분 지지 — 주 지표에 한정 | **supported for the primary metric only** | ~~partial support~~ (영어에서 더 긍정적으로 읽힌다) |
| 미지지 | **not supported** | ~~rejected~~ / ~~refuted~~ |
| 재현되지 않음 — 판정 불가 | **not reproduced; no verdict can be issued** | ~~failed to replicate~~ (실패의 원인을 단정한다) |
| 전달을 확증하지 못했다 | **we could not confirm transfer** | ~~did not transfer~~ / ~~no transfer~~ |
| 전달 부재인지 검정력 부족인지 미구분 | **absence of transfer and insufficient power are not distinguished** | ~~inconclusive~~ 단독 사용 |
| 원인은 미구분 | **the cause is not separated (resource vs. scoring function)** | ~~unclear~~ / ~~unknown~~ |
| 승인된 변경의 안전성은 미검정 | **the safety of accepted changes was not tested** | ~~the gate guarantees safety~~ |
| 자원 지표가 개선되고 형식 검증을 통과한 변경이 성능을 떨어뜨릴 수 있다 | **a change that improves resource-side metrics and passes all formal validation can still degrade task performance** | ~~resource metrics do not represent task performance~~ (무조건 일반형) |
| 사전 지정 주 구성 / 부차 구성 | **prespecified primary configuration / secondary configuration** | ~~main system~~ (P1을 주 시스템이라 부르지 않는다) |
| 교체 대상 구성 (EP3의 P1) | **the configuration under substitution** | ~~main system~~ / ~~primary configuration~~ |

---

## F. 문장 규칙 넷 — §2 재작성의 명세

용어를 고정해도 문장 구조가 흔들리면 번역에서 뜻이 갈린다. §2를 다시 쓸 때 아래 넷을 지킨다.

1. **한 문장에 주장 하나.** 문헌 둘을 역접으로 이어 붙이지 않는다. (현행 §2.2의 Zaveri–Flouris
   문장은 "however"를 어디 놓느냐에 따라 비판 대상이 달라진다.)
2. **주어를 적는다.** "이 축은"·"그 자리다"·"그것이"처럼 참조 대상이 문맥에만 있는 지시어는
   명사로 되살린다 — 영문에서는 번역자가 그 명사를 지어내게 된다.
3. **중점(·) 나열은 관계어로 푼다.** "어휘 결합·의미 표현·인용망 활용"은 한국어에서는 압축이지만
   영어에서는 and인지 or인지, 같은 층위인지를 판단해야 한다. 셋 이상 나열은 문장으로 풀거나 표로 뺀다.
4. **은유는 늘리지 말고 정의를 붙인다.** 층·어긋남·천장·사다리·함정·건초더미는 설득력의 원천이므로
   유지하되, **첫 등장에서 문자 그대로의 뜻을 한 번** 적는다.

---

## G. 확정이 필요한 결정 다섯 (D-1 ~ D-5)

| | 사안 | 권고 | 영향 |
|---|---|---|---|
| **D-1** | `미관측`의 영문 — `unknown`(현행 병기) vs `unobserved` | **unobserved**로 통일 | §2.1 · §4.3 · §8.2 |
| **D-2** | `다국어`(코퍼스)와 `교차언어`(검색)의 분리 | **multilingual / cross-lingual 분리 유지** | §2.1 · §6.4.4 · §8.2 |
| **D-3** | `사후 기술`의 영문 — `post hoc`을 쓰지 않음 | **descriptive / retrospective** | §2.2 · §2.3 |
| **D-4** | `어긋남`의 영문 — misalignment vs divergence | 명사는 **misalignment** 하나 | §1.3 DRQ3′ · §7.5 · DP1 |
| **D-5** | `쓰는 일`의 영문 | **downstream task** 하나로 | 원고 전반 |

---

## H. 시범 영역 — 대장이 실제로 작동하는지의 검증 (2026-08-15 · §2 재작성 후)

> 목적은 영문 초안을 만드는 것이 아니라 **대장의 빈칸을 찾는 것**이다. 아래 두 문단을 옮기는 동안
> 새로 필요해진 항목은 `교체 대상 구성` 하나였고, E절에 추가했다.

**§2.1 두 번째 문단**

> **Examiner citations are not ground truth; they are observed positives.** A cited document is a
> "relevant" signal that was actually observed during institutional examination. A document that was
> not cited, by contrast, is not "irrelevant" — it is *unobserved*. Examiner citations and applicant
> citations differ both in how they are produced and in what they mean (Alcácer & Gittelman, 2006),
> and the examiner's own search is bounded by time, classification, and jurisdiction (USPTO, 2023).
> Recall@K therefore measures how many of the *known* positives were retrieved, not the full extent
> of legal relevance. We refer to this ground truth as **examiner-validated weak ground truth**, or a
> **positive-only qrel**. Metrics that are more robust to unjudged documents are recommended for
> evaluations with incomplete judgments (Buckley & Voorhees, 2004; Büttcher et al., 2007), but those
> metrics presuppose a **judged non-relevant set**, which our resource does not have — so we do not
> use them (§5.5).

**§2.3 두 번째 문단**

> **What we observed suggests that the answer may be no.** Holding the document collection, retrieval
> configuration, weights, splits, and evaluation set all fixed, and substituting only the ontology, a
> change that improved resource-side metrics 2.4-fold significantly reduced retrieval recall for **the
> configuration under substitution**. The change passed all four layers of formal validation, yet was
> rejected by the performance condition (§6.3). We call this phenomenon — a metric at one layer failing
> to stand in for performance at the next — **cross-layer metric misalignment**.

**확인된 것 셋.** ① 한국어 문장을 쪼개 두면 영문에서 접속사 배치를 판단할 일이 없어진다(F절 규칙 1).
② `미관측 → unobserved`·`대리 지표 → proxy metric`처럼 대장에 있는 말은 옮길 때 선택지가 생기지 않는다.
③ **판정 강도는 대장이 없으면 반드시 세진다** — "그렇지 않을 수 있다"를 *the answer is no* 로 옮기고
싶어지는 자리가 실제로 나왔고, E절이 그것을 막았다.

---

## I. 진행 상태와 다음 단계

| | 단계 | 상태 |
|---|---|---|
| 1 | A–G 승인 (E절 판정 문구 · G절 결정 다섯) | **완료** 2026-08-15 |
| 2 | **§2 재작성** | **완료** — 층 언어 정리 · §2.3 순서 역전 · 약어 풀네임 · 문장 분할 |
| 3 | **시범 영역**(H절) | **완료** — 대장 빈칸 1건(`교체 대상 구성`) 발견·보충 |
| 4 | **§5 재작성** | **완료** — 도입에 "절마다 온톨로지의 자리" 안내 · §5.1 성립 전제 선치 · §5.2 "남는 신호 셋" · §5.3 \(w_h\)=0 선치 |
| 5 | **§1 재작성** | **완료** — DSR·CQ·층 셋 영문 병기(첫 등장) · 문장 분할 · §1.6 축약 |
| 6 | **§7 재작성** | **완료** — 용어 표류 교정(운용 타당성 → 과제 검증 깊이) · `천장` 정의 1회 · 긴 문단 분할 |
| 7 | §6 (수치·판정 문장) | **마지막** — E절이 확정된 뒤에만 |

**분량 규율(2026-08-15 확정 · 사용자 승인).** D6(−40%)은 **협상하지 않는다.** 가독성 작업으로 늘어난
분량은 **아직 손대지 않은 장의 중복 서술에서 회수**한다(§2·§5 작업 시 §6–§8에서 회수 완료).
**사실은 하나도 지우지 않는다** — 회수 대상은 다른 절이 이미 말한 것을 다시 말하는 문장뿐이다.

> **현재 여유는 16자다**(74,596 / 74,612). §1·§7 작업은 **먼저 회수하고 그다음 쓰는** 순서로 한다.

**편집·검증 경로.** 편집은 `paper/manuscript/stage3_source.md` → 조립 `make submission-stage3` →
검사 `make verdicts` + `make submission-check`(둘 다 차단) + `make sig-check`. 파생본
`paper/submission/manuscript.md`를 직접 고치지 않는다.
