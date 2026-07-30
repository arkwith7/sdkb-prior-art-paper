# 이관 브리프 — CR-004R 상류 구현 (2026-07-30)

> **받는 곳:** `~/Dev/sdkb` 세션 · **보내는 곳:** `~/Dev/SKKU/sdkb-prior-art-paper`
> **정본 CR:** `/home/arkwith/Dev/SKKU/sdkb-prior-art-paper/upstream/CR-004-rejection-basis-structure.md`
> (하류 §0.1 규약상 CR 의 정본은 하류에 있다. 상류는 이 파일을 **읽고** 구현하며, 복사본을 만들지 않는다.)
>
> **상태: 1·2·3단계 완료·승인됨. 상류는 4단계(구현)부터 시작한다.**
> 단, 상류 CLAUDE.md §2 는 상류 자신의 게이트를 갖는다 — TBox·IRI 변경은 **상류에서 다시 승인**받는다.

---

## 1. 한 문단 요약

의견제출통지서 998건을 새로 수집해 거절근거 무라벨이 **600건 → 1건**이 됐다. 이 라벨을
`ont:RejectionReason`·`ont:PriorArtJudgment` 인스턴스로 실체화한다. **두 클래스는 T-Box 에 이미
선언돼 있고 A-Box 인스턴스가 0건**이므로, 이 작업은 새 구조를 만드는 것이 아니라 **선언된 빈
구조를 채우는 것**이다. 새 어휘가 필요한 곳은 조항 개체 7개와 술어 5개뿐이다.

## 2. 왜 상류가 이걸 해야 하는가 (§0 하류 표 기준)

- **SDKB-Match (PriorArt)** — 선행기술 검색의 상업적 가치는 "관련 문서 목록"이 아니라
  **"이 문헌이 어느 조항의 근거인가"**다. 현재 그래프는 그 질문에 답할 인스턴스가 없다.
- **sdkb-prior-art-paper** — 순위 함수의 `GroundCompatibility(w_r)` 항이 입력 없이 비활성이고,
  절제 A5(거절근거 제거) 손실이 구조적으로 `0.0000` 이다. T2 하위집단 축의 근거가 얇다.

## 3. 승인된 결정 (하류에서 확정 — 뒤집지 말 것)

| # | 결정 | 근거 |
|---|---|---|
| A | 조항 개체는 **항(項) 단위**로 발행. 호(號)는 개체로 만들지 않고 문자열 속성에 보존 | 가역성 — 나눴다 안 쓰는 건 공짜, 뭉쳤다 쪼개는 건 기존 IRI 의미 변경(금지) |
| B | **기존 개체 5개의 IRI·의미·notation 불변.** `Rejection_ClarityScope` 포함 | 하류가 핀한 것을 조용히 바꾸지 않는다 |
| C | **회차를 PriorArtJudgment IRI 에 넣지 않는다** | 넣으면 기존 635 IRI 가 전부 바뀐다. 회차는 RejectionReason 층에만 |
| D | 표 파싱 우선 · LLM 은 62문서 폴백으로 강등 | 결정성 (같은 원천 → 같은 그래프) |

## 4. 작업 목록

| # | 파일 | 작업 |
|---|---|---|
| 1 | `ontology/sdkb-patent.ttl` | 조항 개체 **7개** 추가 (CR §설계 2 표 — 법령 대조 완료본) |
| 2 | `ontology/sdkb-patent.ttl` | 술어 **5개** 추가: `reasonGround`·`groundClause`·`noticeRound`·`noticeType`·`noticeDate` (전부 domain = `ont:RejectionReason`) |
| 3 | `scripts/reextract_claim_judgments.py` | 입력에 의견제출통지서 txt union · 표 헤더 `거절이유가 있는 부분과 관련 법조항` 추가 · `_G29` → 전 조항 파서 · **`특허법시행령`/`시행규칙` 배제 필터** |
| 4 | `scripts/build_abox_claim_features.py` | RejectionReason 인스턴스 발행(현행 0건) · ground 매핑표 확장 · 회차/문서출처 속성 |
| 5 | `validation/` | SHACL: RejectionReason 은 `reasonGround` 1 · `groundClause` 1 · `noticeRound` ≥1 · `noticeType` ∈ {의견제출통지서, 거절결정서} |
| 6 | 생성기 산출 | 손실 리포트 — 파싱 실패 55문서 · 표 없음 7문서를 **건별로** |
| 7 | `CHANGELOG.md` | 어휘 추가 → 마이너 버전 bump · 하류 통보 |

## 5. 입력 데이터 (이미 수집돼 있음 · 재수집 불필요)

```
~/Dev/paper_data/data/processed/opinion_notices/
    _index.json     출원 1,000 키 · 문서 확보 999 · docs[].sendNumber = 회차 판별 키
    txt/            1,155건 · 텍스트층 존재(OCR 불필요) · 본문 평균 7,000자
    pdf/            1,155건
~/Dev/paper_data/data/processed/rejection_decisions/structured/   979건 (기존)
```

⚠ **수집 API 함정 (재수집이 필요해질 경우).** `IntermediateDocumentOPService`(의견제출통지) ·
`IntermediateDocumentREService`(거절결정) 두 서비스 모두 **검색 오퍼레이션
`advancedSearchInfo` 는 0건을 반환**한다. 출원번호 직접 조회 **`pdfInfoV2` 만 작동**한다.
2026-05 에 475건이 0으로 나온 원인이 이것이었다.

## 6. 목표 수치 (2단계 실측 위에서 확정 — 이하로 떨어지면 회귀)

| 기준 | 값 | 분모 |
|---|---|---|
| 청구항 × 조항 연결 | **≥ 95%** (실측 95.5%) | 출원 999 |
| PriorArtJudgment 조립 | **≥ 70%** (실측 71.7%) | **제29조 근거 보유 921건** — 999 아님 |
| RejectionReason 커버 출원 | **≥ 950** | 999 |
| 조항 2종 이상 출원의 인스턴스 | **≥ 2** | 접힘 해소의 직접 증거 |
| 기존 PriorArtJudgment IRI | **635개 전부 존속** | 회귀 보호 |
| 교차태스크 CQ (em·tf·core) | 통과율 하락 **0** | T3 |

## 7. 함정 셋 (미리 알림)

1. **`ontology/sdkb-abox-claim-features.ttl` 은 하류 스냅샷에 포함돼 있지 않다.**
   상류가 인스턴스를 채워도 하류가 vendor 하지 않으면 G0 는 계속 0건이다. → 하류가
   `ontology/vendor.py` 목록에 추가하는 **별도 작업**을 한다. 상류는 이것을 기다리지 않아도 된다.
2. **조항을 본문 어디서든 잡으면 안 된다.** 제63조(통지 근거조항)·제47조 안내문구·제2조가
   전부 오검출된다. 반드시 `[심사결과]` 표의 `관련 법조항` 칸에서만 읽는다.
   (본문 전체 기준 제47조 645건 → 표 칸 기준 3건)
3. **`특허법 시행령 제6조제2호` 는 항상 제45조에 부수한다.** 별도 근거가 아니다.
   법령명 필터 없이 파싱하면 "제6조 50건"이라는 유령 조항이 생긴다.

## 8. 하류가 상류 완료 후 할 일 (상류는 하지 않는다)

`vendor.py` 목록 갱신 → `make vendor` → D-06 검증치 재측정(A5 제거손실 ≠ 0 · T2 n≥20 집단 ≥ 4)
→ PLAN-031 §5.1 탐색 결과 재산출.

## 9. 상류 세션 시작 프롬프트 (그대로 붙여넣기)

```
하류(sdkb-prior-art-paper)에서 CR-004R 이 승인돼 넘어왔다.
이관 브리프: /home/arkwith/Dev/SKKU/sdkb-prior-art-paper/upstream/HANDOFF-CR-004.md
정본 CR:    /home/arkwith/Dev/SKKU/sdkb-prior-art-paper/upstream/CR-004-rejection-basis-structure.md

두 파일을 읽고, 우리 CLAUDE.md §2 절차에 따라 4단계(구현) 착수 전
TBox·IRI 변경에 대한 승인을 나에게 요청하라. 하류에서 확정된 결정 A~D 는 뒤집지 않는다.
```
