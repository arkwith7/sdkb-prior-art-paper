# sdkb-prior-art-paper

**SDKB — 태스크 확장형 반도체 도메인 온톨로지 데이터셋.** 하나의 공유 T-Box가 전문가매칭·선행기술조사·
기술예측 세 뷰를 지탱하며, 이 데이터셋을 **핵심 태스크(선행기술 검색)로 증명하고, 진화 시 다른 태스크를
훼손하지 않음(다중 태스크 작동성)을 T-gate로 보증**한다. 투고 대상: *Advanced Engineering Informatics (AEI)*.

> **정본 원고는 [paper/논문_v0_9_SDKB_통합초안.md](paper/논문_v0_9_SDKB_통합초안.md).** 서명 수치의 최종
> 판정은 [01.code_spec/CANONICAL-INDEX.md](01.code_spec/CANONICAL-INDEX.md) §1, 진행 현황은
> [01.code_spec/STATUS.md](01.code_spec/STATUS.md), 라벨(RQ·H·C·S) 규약과 v0.9 전환의 전파 원장은
> [01.code_spec/RECONCILIATION-v09.md](01.code_spec/RECONCILIATION-v09.md). `paper/archive/` 의 구 원고
> (v0.5·v0.7)·그림·표는 **인용 금지**(구 커버리지/시계열/이식성 = S1/S2/S3 · C1 2차 재사용 증거).

> ⚠️ **private repo 유지.** KIPRIS 학술 자격으로 수집한 원문 데이터(특허 전문 claim/abstract)는 절대
> 커밋하지 않는다(`data/raw`·`data/interim`·전문 스냅샷은 gitignore). 커밋 가능한 것은 집계·메타데이터·
> 식별자·해시·재구축 절차뿐이다.

## 세 주장 (모든 판단의 기준선)

| | 주장 | 증거 | 상태 |
|---|---|---|---|
| **C1 · 자원** | 공유 T-Box가 세 태스크를 표현(정합성·완전성 검증 데이터셋) | 도달성 사다리·CQ 28·SHACL·어휘 커버리지 | 지지 (관측) |
| **C3 · 진화안전** | 다중 태스크 작동성 — T-gate(T1·T2·T3)로 상호 간섭 없이 작동 | 결함주입·McNemar·음성대조군 | 미측정 (T-gate 미구현) |
| **C2 · 핵심증명** | 선행기술 검색에서 온톨로지 보강이 텍스트 기준선을 (조건부) 개선 | Recall@100·nDCG·ablation·부트스트랩 | 미측정 (IR 하네스 구축 예정) |

확증 가설은 **H1–H5** (RQ1 검증게이트→H1·H2=C3 · RQ2 검색유용성→H3=C2 · RQ3 계층기여·특이성→H4·H5=C2).
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

- **질의**: 거절특허 1,000 (한국어) · **후보 코퍼스**: G1/G2 ~40k (한국어) · **qrel 정답 2,321**
  (한국어 57%·영어 39%·일본어 2%). 질의밀도(회수가능 정답 ≥1) = 97.6%. as-built 정본 =
  [SPEC-007](01.code_spec/specs/SPEC-007-ir-corpus-asbuilt.md).
- **분모 규율**: 2,534(인용 엣지) ≠ 2,321(고유 정답) ≠ 2,211(노드도달) ≠ 584(판단연결). **혼용 금지.**
- **기술 스택**: Pyserini(BM25 nori + FAISS flat Dense + RRF) · parquet/pandas(메타데이터·후보필터) ·
  Titan Embed v2(임베딩) · Claude Haiku 4.5(질의 번역 · temp=0·동결). Bedrock 접근은 `config.get_secret()`.

## 검증 게이트 — L0–L3 + T-gate

`make gate` — 게이트를 통과하지 못한 델타는 그래프에 병합되지 않는다(우회 경로 없음). CI가 매 push마다 동일 게이트를 실행한다.

- **L0** 신선도·무결성(sha256 vs PROVENANCE + 이행 증명) → **L1** SHACL(그래프 shape + 델타 shape 두 겹)
  → **L2** HermiT 논리 일관성 → **L3** CQ 28개(스위트 pa·em·tf·core) + 어휘 검증 커버리지.
- **T-gate** (v0.9 · 진화 안전성 C3 · **미구현**): **T1** 검색 비열등(LB₉₅(ΔRecall@100) > −ε) · **T2**
  하위집단 안전성(언어 KR/외국 포함) · **T3** 교차 태스크 CQ 비회귀(em·tf·core). 계약 명세 =
  [SPEC-001](01.code_spec/specs/SPEC-001-validation-gate.md) §T-gate.
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

- **그림·표는 코드가 만든다** (`viz/figures.py`). 수작업 금지. v0.9 C2/C3 그림·표는 IR 하네스 구축 후
  생성된다(현재 미산출). 구 커버리지/시계열/이식성 그림·표는 `paper/archive/`(S-시리즈·인용 금지).
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
