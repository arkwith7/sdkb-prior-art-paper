# S1 · 사전등록 동결 항목과 재현 자료

> 본문 §4·§5가 인용하는 사전등록 동결 항목, 재현에 필요한 산출물과 절차, 그리고 방법상의
> 미확인 사항이다. 동결 근거가 기록된 항목에는 사전등록 문서와 커밋 해시를 병기한다.

> **이 파일의 `§` 참조에 대하여.** 아래 본문은 v0.9 작업 정본에서 옮겨 온 것이므로 `§` 번호는
> 그 판의 절 번호이며 현행 본문의 절 번호와 다르다. 작업 정본은
> [논문_v0_9_SDKB_통합초안.md](../archive/논문_v0_9_SDKB_통합초안.md)이다.

---

# 부록 A. 사전등록 동결 항목

결과 확인 이전에 동결한 항목의 목록이다. 사전등록 문서와 커밋 해시가 기록된 항목은 그 근거를
함께 적는다.

- 데이터 버전과 커밋 해시 동결
- 특허·패밀리·NPL의 정확한 분모 검증 (2,534 / 2,321 / 2,211 / 584 구분)
- 학습/개발/테스트 기간과 식별자 동결
- 질의 인용·판단 간선 마스킹 테스트 통과
- 미래정보 특징 0건 확인
- 주 Dense 모델과 토큰화 규칙 동결
- 주 지표 Recall@100과 보조지표 동결
- \(\epsilon\), \(\delta\), 최소 하위집단 크기 동결
- low-overlap 정의 동결
- CQ 스위트 분할(CQ-PA / CQ-EM / CQ-TF / CQ-CORE) 및 버전 동결
- **L3·T3 검출 표면 배정 동결** (L3 = pa · T3 = em·tf·core · 서로소 ∧ 합집합 전량) — PLAN-022 · 커밋 `44f8022`
- **CQ 판정 규칙 버전과 \(\tau\) 동결** (v2 = 존재 ∧ 분포 · 극성 `# monotone:` 28개 · τ=0.05 · 격자 {0, 0.05, 0.10}) — PLAN-021
- **델타 유형과 면제 규칙 동결** (`generic` / `dedup` · 자동 검증 통과 시 분포 검사만 면제) — PLAN-022
- 결함 주입 유형·강도·반복수 동결 (교차 태스크 결함군 포함)
- 전문가 판정 표본설계와 평가척도 동결
- 테스트 qrel 접근권한과 개봉일 기록
- 트리플 서명 105,588 세대 정합 검증
- 난수 시드 고정 (분할·부트스트랩·hard negative 샘플링)

# 부록 B. 소프트웨어 산출물과 재현 절차

## B-1. 디렉터리 구조

```
/ontology
  tbox.ttl                  # 공유 코어 + 3태스크 뷰
  sdkb-patent.ttl           # 선행기술조사 모듈
  shapes/                   # SHACL shapes
/queries/cq  CQ01–CQ31.rq             # 스위트는 파일 헤더 `# suite:` · 조회 대상은 `# target:` (as-built)
                                      #   pa   = CQ09·10·16·26·27      (선행기술조사 · 주 태스크 · target=graph)
                                      #   pa   = CQ29·30·31            (청구항 층 · target=sidecar · 측정, 게이트 아님 §9.7)
                                      #   em   = CQ11·12·17·18·20·28   (전문가 매칭)
                                      #   tf   = CQ02·03·04·05·06      (기술예측)
                                      #   core = CQ01·07·08·13·14·15·19·21·22·23·24·25 (공유)
/data      G0-Core, G1, G2, claim-feature sidecar
/data/cq_generations  cq_<세대>.json  # 세대별 스위트 통과율 아티팩트 + waiver 로그 (표 6.6)
/qrels     dev/, test-sealed/        # test는 해시 고정 + 접근 로그
/splits    family_time/
/baselines bm25/, dense/, hybrid/, cpc_overlap/, ontology/
/src/sdkb_paper/analysis   metrics.py, bootstrap.py, subgroup.py, ablation.py, lang_recall.py
/src/sdkb_paper/validate   shacl_gate.py, reasoner_gate.py, cq_runner.py, vocab_coverage.py,
                           leakage_check.py, t1_noninferiority.py, t2_subgroup.py,
                           t3_cross_task_cq.py, t_gate.py
/faults    inject_faults.py           # 교차 태스크 결함군 포함 (미구현)
/ci        quality-gate.yml
/scripts   split_by_family_time.py, check_signatures.py
```

스위트 배정은 CQ 파일 헤더에 기록돼 있고(`# suite:`), 라벨이 없거나 허용값 밖이면 러너가 오류로 멈춘다 — 분모가 조용히 바뀌면 T3는 공허해지기 때문이다. 배정은 **T-gate 실행 이전에 동결**했다(PLAN-019 §4.1).

## B-2. CI quality-gate 배선

기존 `sig-check` 타깃 위에 게이트를 얹는다. 어느 단계든 실패하면 비영 종료로 머지를 차단한다. 다만 **공개 저장소 CI가 실제로 돌리는 범위는 L0–L3·린트·테스트·서명 정합까지**다 — 검색 산출물(코퍼스·색인·run)은 KIPRIS 비재배포 조건으로 커밋되지 않으므로 T1·T2는 원문 데이터를 보유한 환경에서 `make gate`로 실행하고 그 판정 보고서를 아티팩트로 남긴다. T3는 그래프만 있으면 되므로 데이터 없이도 재현된다.

```make
# Makefile (as-built) — make gate 하나가 L0→T3를 fail-fast로 관통한다
gate: gate-graph leakage tgate
gate-graph: l0 validate reason cq vocab      # L0 신선도·무결성 / L1 SHACL / L2 HermiT / L3 CQ
leakage:  python -m sdkb_paper.validate.leakage_check --split dev
tgate:    python -m sdkb_paper.validate.t_gate --split dev --baseline g0   # T1 + T2 + T3
cq-freeze: python -m sdkb_paper.validate.t3_cross_task_cq <graph> --freeze <세대>
sig-check: python scripts/check_signatures.py

# 결함 주입 (§4.10·§6.5 · H1) — 게이트의 판별력을 재는 실험. CI 상시 대상이 아니다.
faults-baseline: python -m sdkb_paper.analysis.faults --baseline   # 정본 봉인 + 기준선
faults-fc:       python -m sdkb_paper.analysis.faults --fc-cache   # FC 성분 1회 + P1 재현 검증
faults:          python -m sdkb_paper.analysis.faults --reps 3 --workers 10

# 판정 세분화 재판정 (§6.5.2) — 결함을 다시 주입하지 않는다. 새로 넣는 것은 정상 델타뿐.
faults-n03:      python -m sdkb_paper.analysis.faults --n03        # 완전중복 병합 9건
faults-rejudge:  python -m sdkb_paper.analysis.faults --rejudge    # 격리본 재판정 v1 vs v2 × τ
```

**판정 규칙은 인자가 아니라 동결값이다.** `config.CQ_TAU=0.05`·`config.CQ_TAU_GRID=(0, 0.05, 0.10)`이 코드에 있고, 극성은 각 `.rq` 헤더의 `# monotone:`이 정본이다. 라벨이 없거나 허용값이 아니면 러너가 **에러로 막는다** — 조용한 기본값을 두면 공백 탐색 질의의 정당한 개선이 회귀로 오판되기 때문이다(§6.5.2).

**CQ 실행 엔진 (as-built).** `cq_runner`는 pyoxigraph로 SPARQL을 실행한다. rdflib 인메모리는 G₀(23 MB)에서 CQ 28개에 150초가 걸려 결함 주입 108 인스턴스를 감당하지 못한다. 전환은 **두 엔진의 CQ별 결과 행 수가 28/28 전부 일치함을 확인한 뒤에만** 수행했으며(`--verify-engines`, 불일치 0건), `--engine rdflib`로 언제든 되돌릴 수 있다. 전환 후 2.4초다 — 상시 CI 게이트의 비용 장벽이 사라졌다.

**결함 주입의 오염 격리.** 결함 주입은 그래프를 고의로 훼손하므로 산출물이 정본으로 새면 연구 전체가 조용히 오염된다. `validate/quarantine.py`가 이를 물리적으로 막는다. (i) 실험 전 정본 산출물 전량의 sha256을 봉인하고 주입 대상 그래프는 별도 디렉터리에 실제로 복사한다. (ii) 결함 산출물은 `data/quarantine/<run>/<label>/` 밖에 쓰이지 않으며 디렉터리마다 결함 사양·시드·커밋을 담은 오염 스탬프가 찍힌다. (iii) 정본 경로를 읽는 진입점은 오염 경로·스탬프를 감지하면 즉시 예외를 던지고, 러너는 **매 인스턴스마다** 정본 해시를 재검증해 한 바이트라도 다르면 그 지점에서 중단한다. (iv) 배치 종료 시 격리본은 읽기전용으로 잠기고 감사 원장이 남는다. 격리 산출물은 저장소에 커밋되지 않는다.

ε·δ는 명령행 인자가 아니라 `config.T_EPSILON=0.02`·`config.T_DELTA=0.05`로 코드에 동결돼 있다 — 호출 시점에 마진을 바꿀 수 있으면 사전등록이 아니기 때문이다. `t_gate.py`는 승인식을 **곱**으로 계산하고 하나라도 0이면 비영 종료하며, 판정과 근거를 `tgate_report.json`으로 남긴다.

`t3_cross_task_cq.py`는 이전 정본의 태스크별 통과율을 세대 아티팩트(`data/cq_generations/cq_<세대>.json`)로 저장해 두고 현재 값과 비교하며, 하락 시 비영 종료한다. 스위트가 통째로 사라진 경우도 통과율 0으로 취급해 "CQ를 지워 통과시키는" 우회로를 막는다. waiver는 커밋 메시지의 명시적 토큰(`T3-WAIVER:`)으로만 허용하고 그 횟수를 로그(`data/cq_generations/waiver_log.jsonl`)로 남겨 논문(표 6.6)에 보고한다.

## B-3. 재현에 필요한 대조 항목

독립 재실행이 대조하여야 하는 항목이다.

- 트리플 서명 105,588 세대 검증 (`check_signatures.py`)
- 라이선스 매니페스트 (§3.2 큐레이션 소스 표와 일치)
- 난수 시드 고정 (분할·부트스트랩·hard negative 샘플링)
- `g:qrels-test` 해시 고정 및 봉인 해제 시점 기록
- 메타데이터 전용 배포 범위 확인 (KIPRIS 조건)
- 3모드(Oracle-free / Citation-assisted / GT-assisted) 결과 분리 저장
- CQ 스위트 버전과 결함 주입 실험 버전의 대응 기록 (판정 규칙 v1/v2 · 표 6.6 규칙 열 · 표 6.5v2)
- 결함 주입 전후 정본 해시 무결성 (`data/PRISTINE.json` · 격리 원장)
- CQ 엔진 대조 결과(oxigraph ↔ rdflib 28/28 일치)
- FC 캐시의 동결 P1 run 재현(top-100 197/197)

# 부록 C. 미확인 사항 (Caveats)

- **CQ 판정 세분화는 수행됐으나 청구항 수준 분해는 미실행.** 존재 검사를 분포 검사로 강화하는 세분화는 2026-07-28 수행했고(판정 v2 · §6.5.2), T3 검출은 0/108 → 34/108로 회복됐다. 그러나 선행기술 CQ의 **청구항 수준 분해**는 여전히 미실행이며, 더 중요하게는 세분화가 H1′을 되살리지 못했다 — 원인이 판정 해상도가 아니라 **L3와 T3의 검출 표면이 포개져 있다**는 데 있기 때문이다. 층 정의 분리는 결과를 본 뒤 바꿀 수 없으므로 차기 사전등록으로 이월했다.
- **분포 검사는 정당한 중복 제거를 회귀로 오판한다(2026-07-28 실측).** 완전 중복 개체 병합(정상 델타 N03)이 τ=0.05에서 1/9, τ=0에서 3/9 거부됐다(§6.5.2). 중복이 만들던 허수 조합 행이 사라지는 것을 행 수만 보는 판정이 구분하지 못한다. τ를 올리면 검출력이 55→18로 무너지므로 처방은 마진 조정이 아니라 델타 유형 선언이다(미실행).
- **L2(추론 게이트)에 검출 표면이 거의 없다(2026-07-28 실측).** SDKB T-Box에 `owl:disjointWith`·카디널리티 제약·함수적 속성이 **하나도 없다**. 논리 결함을 주입해도 OWL 의미론상 모순이 되지 않아 HermiT는 일관이라고 답한다. 결함 주입 9건 중 L2 검출은 0건이었고 1건은 L1이 잡았다(§6.5). 형식 검증 4층 중 L2는 현재 자원에서 사실상 비어 있는 층이다.
- **T1의 실효 민감도가 낮다(2026-07-28 실측).** T1은 결함본 P1을 정상 B3와 비교하므로, 결함이 온톨로지 이득(+0.042)을 전부 소진하고 추가로 \(\varepsilon=0.02\)를 넘겨야 발화한다. 개념 정렬 10% 오류에서 이득은 +0.032로 줄었을 뿐 T1은 통과했다(§6.5). 마진 재설정은 사전등록 변경이므로 별도 절차가 필요하다.
- **누출 감사 G-3은 누출에 특이적이지 않다(2026-07-28 실측).** 개념 병합 결함이 G-3을 상승시켜 누출 층에서 0.67 비율로 검출됐으나 실제 누출이 아니다(§6.5). G-1(문서를 개념 자리에 넣었는가)은 특이도가 확인됐다.
- **결함 주입의 위양성 분모 한계.** 정상 델타 N01(실제 병합 델타의 부분집합)은 그 트리플이 이미 G₁에 있어 **T1·T2에 대해 구조적으로 공허**하다(합집합 뷰가 변하지 않는다). 성능층의 위양성은 N02(의미보존 보강)로만 측정했다. 미공개 실제 보강분을 홀드아웃해 재는 것이 더 강한 설계이며, 그런 홀드아웃이 없다는 것이 현재 자원의 제약이다.
- **지표 관례 두 가지가 원고 §5.1의 예고와 다르다.** qrel이 전량 등급 1이어서 nDCG@20은 **이진 이득**, bpref는 **retrieved-as-judged** 관례로 계산했다(§5.1·§6.2 고지). 등급형 평가는 §5.5 전문가 판정 확보가 선결 조건이다.
- **검색 파이프라인은 단일 언어 질의 처리로 동결되어 있다(2026-07-28 측정·갱신).** 번역 계층을 두지 않으므로 교차언어 회수는 다국어 임베딩과 언어중립 개념 IRI 두 통로에만 의존한다. 그 결과는 §6.2f에 정답 언어별로 분해해 실측 보고했다(어휘 검색의 영어 정답 회수 0/334 · 최종 시스템의 비한국어 정답 회수 5%). 번역·개념 보강·후보 생성을 요인으로 하는 개선 실험은 F8·F13 동결을 변경하므로 **별도 사전등록**으로만 가능하다(§9.1 · PLAN-019).
