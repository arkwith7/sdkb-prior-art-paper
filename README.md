# sdkb-prior-art-paper

**SDKB — 태스크 확장형 반도체 도메인 온톨로지 데이터셋.** 하나의 공유 T-Box가 전문가매칭·선행기술조사·
기술예측 세 뷰를 지탱하며, 이 데이터셋을 **핵심 태스크(선행기술 검색)로 증명하고, 진화 시 다른 태스크를
훼손하지 않음(다중 태스크 작동성)을 T-gate로 보증**한다. 투고 대상: *Advanced Engineering Informatics (AEI)*.

> **작업 정본은 [paper/논문_v0_9_SDKB_통합초안.md](paper/논문_v0_9_SDKB_통합초안.md)이고, 투고본은
> 그 파생물 [paper/submission/manuscript.md](paper/submission/manuscript.md)이다**(산문 소스
> `paper/manuscript/stage3_source.md` → `make submission-stage3`). 서명 수치의 최종
> 판정은 [01.code_spec/CANONICAL-INDEX.md](01.code_spec/CANONICAL-INDEX.md) §1, 진행 현황은
> [01.code_spec/STATUS.md](01.code_spec/STATUS.md), 라벨(RQ·H·C·S) 규약과 v0.9 전환의 전파 원장은
> [01.code_spec/RECONCILIATION-v09.md](01.code_spec/RECONCILIATION-v09.md). `paper/archive/` 의 구 원고
> (v0.5·v0.7)·그림·표는 **인용 금지**(구 커버리지/시계열/이식성 = S1/S2/S3 · C1 2차 재사용 증거).

> ⚠️ **private repo 유지.** KIPRIS 학술 자격으로 수집한 원문 데이터(특허 전문 claim/abstract)는 절대
> 커밋하지 않는다(`data/raw`·`data/interim`·전문 스냅샷은 gitignore). 커밋 가능한 것은 집계·메타데이터·
> 식별자·해시·재구축 절차뿐이다.

## 평가 에피소드와 판정 (모든 판단의 기준선)

산출물 평가는 네 에피소드로 수행되었고, 각 판정의 정본은 [paper/verdicts.yaml](paper/verdicts.yaml)
이다(`make verdicts` 가 원고 문구와의 정합을 강제한다).

| | 에피소드 | 무엇을 재는가 | 판정 |
|---|---|---|---|
| **EP1** | 표현 감사 | 공유 T-Box가 세 태스크 뷰를 표현하는가 (SHACL · CQ 31개) | 표현 범위 확인 (관측) |
| **EP2** | 게이트 판별력 | 형식 검증과 주 태스크 검사가 놓친 교차 태스크 결함을 T3가 잡는가 | 홀드아웃 45건에서 T3 단독 검출 12/45 · 단측 McNemar *p* = .0001 · 정상 델타 27건 위양성 0 |
| **EP3** | 통제된 자원 교체 | 문서·코드·설정을 동결하고 자원 번들만 교체했을 때 승인되는가 | L0–L3 전부 통과 · T1 실패(ΔR@100 −0.0293 · 95% CI [−0.0542, −0.0053]) → **승인 거부** |
| **EP4** | 검색 효용과 경계 | 온톨로지 보강이 강한 텍스트 기준선을 개선하는가 | 사전등록된 복합 예측은 두 분할 어느 쪽에서도 충족되지 않았고, 깊은 회수 개선은 두 분할에서 반복 관측 (+0.0534 · +0.0343) |

전달 점검(T4)은 승인식 밖에서 판정 1회를 수행하였으며 **전달을 확증하지 못했다** — 전달 부재인지
검정력 부족인지는 구분하지 못했다. 승인 안전성(변경 없는 파이프라인에서 O와 O′를 비교하는 검정)은
본 원고의 자원에서는 **미검정**이며, 별도 사전등록(PLAN-035)의 1회 실검정에서는 기각되었다.
제2 도메인 이식 시연(EP5)은 [PLAN-064](01.code_spec/plans/PLAN-064-second-domain-portability-and-aei-reframe.md)
에 설계되어 있고 **미착수**다.

"돌아간다"는 시연은 증거가 아니다 — 검정·효과크기·강건성·누출통제가 증거다.

## 빠른 시작

```bash
uv sync --all-extras          # 의존성 설치
cp .env.example .env          # KIPRIS_API_KEY · AWS/BEDROCK 시크릿 입력 (config.get_secret())
make vendor                   # 근간 온톨로지(SDKB) 스냅샷 가져오기  ← 최초 1회
make baseline                 # graph_v0(G₀) 조립
make test                     # 단위 테스트
make gate                     # 검증 게이트 L0–L3
make sig-check                # 서명 표류 검사 (CANONICAL-INDEX §1 정합)
```

## 근간 온톨로지 (SDKB) — 워크스페이스는 합치되 의존은 합치지 않는다

이 논문은 **SDKB**([semiconductor-knowledge-base](https://github.com/arkwith7/semiconductor-knowledge-base))를
재사용한다. **어휘를 새로 발명하지 않고** SDKB 실물(`data/external/sdkb/*.ttl`)을 그대로 쓴다. 온톨로지
자산(T-Box·CQ·SHACL·claim-feature sidecar·개념링크)은 C1의 근거이자 온톨로지 검색팔의 입력이며 —
**재사용하되 논문이 변경하지 않는다**(코퍼스는 파생 뷰). 의존은 한 방향뿐이다:

```
SDKB 원본 ──(사람이 make vendor)──> data/external/sdkb/ (얼린 스냅샷 + sha256) ──> 코퍼스 조립
```

런타임에 `~/Dev/sdkb`를 읽지 않는다. SDKB 결함은 **상류에서 고친다** — 우회 패치는 스냅샷 출처를
거짓으로 만든다. 출처·무결성은 `PROVENANCE.json`, 갱신 절차는 [data/MANIFEST.md](data/MANIFEST.md).

## IR 벤치마크 (핵심 태스크 = 선행기술 검색)

- **질의**: 거절특허 1,000 (전량 한국어) · **후보 코퍼스**: 40,552 (**다국어** — 한국어 96.8% ·
  영어 1,189 · 일본어 117) · **qrel 정답 2,321**
  (한국어 57%·영어 39%·일본어 2%). 질의밀도(회수가능 정답 ≥1) = 97.6%. as-built 정본 =
  [SPEC-007](01.code_spec/specs/SPEC-007-ir-corpus-asbuilt.md).
- **분모 규율**: 2,534(인용 엣지) ≠ 2,321(고유 정답) ≠ 2,211(노드도달) ≠ 584(판단연결). **혼용 금지.**
- **기술 스택**: Pyserini(BM25 nori + FAISS flat Dense + RRF) · parquet/pandas(메타데이터·후보필터) ·
  Titan Embed v2(임베딩). Bedrock 접근은 `config.get_secret()`. **질의 번역은 구현되어 있지 않다** —
  교차언어 회수의 경계는 번역 없이 측정한 값이다(원고 §6.2f 계열 · 탐색적 진단).

## 검증 게이트 — L0–L3 + T-gate

`make gate` — 게이트를 통과하지 못한 델타는 그래프에 병합되지 않는다(우회 경로 없음). CI가 매 push마다 동일 게이트를 실행한다.

- **L0** 신선도·무결성(sha256 vs PROVENANCE + 이행 증명) → **L1** SHACL(그래프 shape + 델타 shape 두 겹)
  → **L2** HermiT 논리 일관성 → **L3** CQ 28개(스위트 pa·em·tf·core) + 어휘 검증 커버리지.
- **T-gate** (v0.9 · 진화 안전성 C3 · **구현·실행됨** — `validate/t_gate.py` · `make tgate`):
  **T1** 검색 비열등(LB₉₅(ΔRecall@100) > −ε) · **T2** 하위집단 비회귀 방호(언어 KR/외국 포함) ·
  **T3** 교차 태스크 CQ 비회귀(em·tf·core). 계약 명세 =
  [SPEC-001](01.code_spec/specs/SPEC-001-validation-gate.md) §T-gate.
  **T4**(하류 생성 층 비회귀)는 설계와 판정 1회의 기록이며 승인식에는 편입하지 않았다.
- 게이트 대상은 **세 그래프 + 코퍼스**: G₀(측정·앵커) · G₁/G₂(4층 통과 후 분석) · mini_graph(엄격 delta) ·
  IR 코퍼스(누출 0·분할 결정성). 하나로는 게이트가 vacuous.
- **누출 통제**: 질의 인용 간선(`hasPriorArtExaminer`/`hasPriorArt`/`overPriorArt`) 마스킹 · 시점유효
  (공개일<cutoff) · 패밀리 분리 · `NoveltyScore` 등 정답 파생 피처 배제. `leakage_check`가 강제.
- **CQ 응답률·어휘 커버리지는 게이트가 아니라 측정이다**(`--min-pass 0` · `--min-cov 0`) —
  [SPEC-004](01.code_spec/specs/SPEC-004-cq-derivation-protocol.md). 채우려 CQ를 지어내지 않는다.

## 파이프라인

```
SDKB repo ──> vendor ──> data/external/sdkb/ ──> baseline ──> graph_v0.ttl (G₀ · 앵커)
             (스냅샷 고정)                       (조립)              │
KIPRIS API ──┐                                                     ▼
             ├─> corpus(sidecar 조인·번역·임베딩·분할·hard neg) ─> IR 코퍼스 ─> index(BM25+Dense)
BigQuery ────┘                                                     │
                                    retrieve(B0–B5·P0–P2) ─> eval(Recall/nDCG·부트스트랩·하위집단)
                                                            └─> gate(L0–L3 + T1·T2·T3) ─> figures
```

- **그림·표는 코드가 만든다** (`viz/figures.py` · `viz/concept.py` · 규격
  [paper/FIGURE-SPEC.md](paper/FIGURE-SPEC.md)). 수작업 금지. 개념 도식의 수치도
  `paper/figures/data/concept_values.json` 에서만 읽으며 그 파일은 `make figure-data` 가 산출물에서
  기계로 추출한다. 구 커버리지/시계열/이식성 그림·표는 `paper/archive/`(S-시리즈·인용 금지).
- **커밋은 사용자 요청 시에만.** 메시지는 어느 주장(C1/C2/C3)·가설을 진전시켰는지 밝힌다.

## 저장소 지도

| 무엇 | 어디 |
|---|---|
| 작업 규약 | [CLAUDE.md](CLAUDE.md) (v0.9 기조) |
| 정본 원고 | [paper/논문_v0_9_SDKB_통합초안.md](paper/논문_v0_9_SDKB_통합초안.md) |
| 정본 인덱스·현황·전파 원장 | [01.code_spec/](01.code_spec/) — `CANONICAL-INDEX.md` · `STATUS.md` · `RECONCILIATION-v09.md` |
| 계약(SPEC) | [01.code_spec/specs/](01.code_spec/specs/) — SPEC-001~007 |
| 용어집·실무 참조 | `GLOSSARY-{ONTOLOGY,SEMICONDUCTOR,STATISTICS}.md` · [REF-001](01.code_spec/REF-001-ip-rnd-domain-framework.md)(IP-R&D) |
| 구 패러다임(인용 금지) | `paper/archive/` · `01.code_spec/archive/` |
