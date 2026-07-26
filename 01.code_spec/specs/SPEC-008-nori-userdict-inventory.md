# SPEC-008 · nori 사용자사전 as-built 인벤토리 (토큰화 어휘 · 측정 기반)

| | |
|---|---|
| 지지하는 것 | **C2 핵심증명**(BM25 토큰화 정확성 = 검색 기준선 유효성의 전제) / 논문 §4.5·§5.3 · PLAN-018 F13 |
| 정본(측정 대상) | `data/processed/ir/userdict_sdkb.txt` (nori `UserDictionary` · gitignore) |
| 원천 | 벤더 스냅샷 `data/external/sdkb/*.ttl` + 동결 매핑 `mappings/*.csv` + 코퍼스 `ir_corpus_v09.parquet` |
| 빌더 | `src/sdkb_paper/retrieval/userdict.py` (`make userdict`) |
| 재측정 | §7 스크립트 |

> **이 문서는 "어떤 반도체 도메인 용어가 형태소 분석기 사용자사전으로 정의됐는가"의 정본 기록이다.**
> PLAN-018 §6.1 이 실증한 nori OOV 파편화(질의 '플라즈마'→[플라] vs 문서 '플라즈마 식각'→[플라,식각])는
> 질의-문서 토큰을 어긋나게 해 BM25 매칭을 훼손한다. 사용자사전은 그 정확성 요건(F13)이자 **재현
> 가능한 스펙**이다. SPEC-006/007 규율(출처·건수·서명·재측정·표층형 표본)을 따른다.
>
> **동결·누출 규율:** 어휘 원천·수확 규칙은 PLAN-018 §6.2.1 표(U1–U8)로 **결과(Recall)를 보기 전
> 동결**됐다. 코퍼스 수확은 문서-특정이 아닌 **도메인-일반**(df≥30)만 채택해 인용쌍 정보를 담지
> 않는다(누출 가드). 회사명·특허제목·인명은 배제한다(U2). **모든 수치는 2026-07-26 측정값**이며 파일이
> 정본이다(문서와 어긋나면 실물이 옳다 · CLAUDE.md §1.1).

---

## 1. 서명

| 자원 | 표층형 수 | 파일 | sha256(앞16) |
|---|---:|---|---|
| **nori 사용자사전** | **275** (한글 137 · 영문 138) | `data/processed/ir/userdict_sdkb.txt` | `b301bd47d4ed0109` |

- 특허 전문에서 수확한 표층형을 포함하므로 파일은 gitignore(license_restricted 코퍼스 파생). 커밋되는
  것은 이 SPEC(집계·서명·표본)뿐. 재생성: `make userdict`.

---

## 2. 원천별 기여 (U1–U6 · 실측)

| 원천 | 규율 | 표층형(원·중복제거 전) |
|---|---|---:|
| **A · 온톨로지 통제어휘** | 도메인 클래스 14종 prefLabel(en)+altLabel(ko·en) · 회사명/제목/인명 배제(U2) | 423 |
| **B · 동결 매핑 CSV** | term_aliases·si_concepts·dart_terms 표층형(정규식 메타 제거·U3) | 58 |
| **C · 코퍼스 수확** | Kiwi {SL,NNG}·df≥30·nori 파편화·고유명 배제(U4–U6) | 85 |
| 다어절 제외 | 공백 포함 = nori 단일토큰 불가(U7) | −277 |
| **합집합(최종)** | 세 원천 dedup · 공백없는 표층형 · 길이≥2 · 정렬 | **275** |

- **원천별 수는 중복제거·다어절제거 전 원(原) 집계**다. 최종 275 는 세 원천 합집합에서 공백 포함
  다어절 277 개(주로 A 의 영문 복합명 'ball grid array'·'physical vapor deposition' 등)를 제외한 결과.
- 코퍼스 수확 상한(HARVEST_MAX=2000) 초과 절단: **0건**(채택 85 ≪ 2000 · 무언절단 없음).
- **누출 대칭 검증(실측):** 회사명 토큰(삼성·하이닉스·㈜) 0건 — U2 배제 작동. `git check-ignore` 통과(파일 미커밋).

---

## 3. 동결 파라미터 (PLAN-018 §6.2.1 U1–U8 · 재게시)

| # | 항목 | 값 |
|---|---|---|
| U1 | 도메인 클래스 14종 | Process·SubProcess·Device·Material·Equipment·EquipmentClass·EquipmentModel·FailureMode·RootCause·Mitigation·Skill·Parameter·Metrology·TechnologyNode |
| U2 | 배제 클래스 | Patent·CitedPatent·RejectedPatent·Expert·**Organization·Vendor** |
| U5 | 수확 채택 | df≥**30** ∧ nori 파편화 ∧ ¬고유명 |
| U6 | 수확 상한 | df 내림차순 **2000** |
| U7 | 출력 | nori UserDictionary · 공백없는 1줄1항 · UTF-8 |

---

## 4. 표층형 표본 (검증 가능성 · 실측)

- **온톨로지(A) 한국어 표본:** ArF 포토레지스트 · CCD 이미지 센서 · EUV 포토레지스트 · P램 ·
  가스 케미스트리 · 건식 식각 · 건식식각 · 결함 분석 (도메인 재료·소자·공정·스킬 표층형).
- **코퍼스 수확(C) 표본(df 상위):** 플라즈마 · 구조체 · 어드레스 · 타겟 · 소오스 · 가장자리 · 각각 · 일단.
  → **의도한 OOV 외래어 '플라즈마'(§6.1 파편화 사례)를 정확히 포착.** '소오스'(source 표기변이)·'타겟'·
  '어드레스'·'구조체' 등 도메인 외래어도 회수.

> **정직한 한계(수확 잡음):** df≥30 도메인-일반 필터는 '각각·일단·가장자리' 같은 **비도메인 상용어**도
> 함께 채택한다(nori 가 이들을 파편화하기 때문). 검색 영향은 무해하다 — 이런 상용어는 IDF 가 낮아
> 순위 기여가 미미하고, 질의·문서에 **대칭** 적용돼 편향을 만들지 않는다. 정밀 도메인 필터링은 사전등록
> 밖 사후조정이 되므로 하지 않는다(CLAUDE §1.2·1.3). 수확어 전량은 사용자사전 파일에서 직접 검증한다.

---

## 5. 누출 안전 논증 (왜 코퍼스 수확이 qrel 누출이 아닌가)

- 수확 채택 하한 **df≥30**(≈40k 중)은 표층형을 **문서-특정에서 도메인-일반으로 강제**한다. 30개 이상
  문서에 등장하는 명사·외래어는 "어느 문서가 어느 질의의 선행기술인가"(인용 엣지)에 대한 정보를 담지
  않는다 — BM25 IDF 를 전체 코퍼스(정답 포함)로 계산하는 것과 같은 성격이며, 사전 항목은 IDF 보다도
  정보량이 적다(단지 "이것은 한 단어다"라는 토큰화 사실).
- **정답 유래 표층형 직접 배제(U2·U5c):** 특허 제목 토큰·회사명·Kiwi NNP(고유명)를 수확에서 제외.
- **대칭 적용:** 질의·문서·전 시스템(B0–P2)에 동일 사전 — 특정 팔에 유리하게 편향하지 않는다(F13·ablation 밖).

---

## 6. 알려진 한계

- **다어절 표층형(공백 포함) 미수용:** nori UserDictionary 는 공백 없는 연속 표층형만 단일 토큰화한다.
  '물리 기상 증착' 같은 다어절 큐레이션어는 제외되나, 공백제거 변이('물리기상증착')가 altLabel 에
  이미 존재해 실질 손실은 작다(제외 건수 §2 보고).
- **영문 표층형:** 한글 없는 순영문어는 사용자사전에서 제외(standard analyzer 담당·U4 한글 필터). 온톨로지
  영어 prefLabel 중 영문 단독어는 nori 사전이 아니라 영어 색인 팔에서 처리.
- **Kiwi 의존:** 수확 후보생성기가 Kiwi 이므로 Kiwi 버전이 수확 집합에 영향. 버전 고정으로 결정성 확보(§8).

---

## 7. 재측정 (이 문서의 모든 수치)

```bash
make userdict     # = python -m sdkb_paper.retrieval.userdict (JAVA_HOME 필요)
```
```python
from sdkb_paper.retrieval import userdict
stats = userdict.build()      # UserDictStats: from_ontology/from_mappings/from_corpus/total_terms/sha256_16
# 파일 서명
import hashlib; from sdkb_paper import config
hashlib.sha256(config.IR_USERDICT.read_bytes()).hexdigest()[:16]
```
값이 바뀌면 이 SPEC를 같은 커밋에서 갱신한다(CLAUDE.md 데이터 프로파일 의무). 코퍼스 서명(SPEC-007
`ec5ea51b`)·벤더 스냅샷·Kiwi/nori 버전이 입력이며, 이들이 고정되면 산출은 결정적이다.
