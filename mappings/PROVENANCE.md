# `code_to_concept.csv` 의 출처

## 코드 제목 (`code_title`)

`scheme = CPC-2026.01` 인 행의 `code_title` 은 **CPC 공식 스킴 원문 그대로**다.
원천: `https://www.uspto.gov/web/patents/classification/cpc/html/cpc-<SUBCLASS>.html`
(2026-07-12 취득, 16개 서브클래스: H10P H10B H10D H10W H10K H10F H10H H10N G11C H01L H01J C23C G03F C09K C23F H05H).
CPC 는 이 층위에서 IPC 와 동일하다.

> **요약 모델을 거치지 않는다.** 조사 과정에서 한 웹 요약이 `H10P 95/041 = DUV lithography`,
> `H10P 95/042 = EUV lithography` 라는 그룹을 보고했으나, 스킴 HTML 을 직접 파싱한 결과
> **그런 그룹은 존재하지 않았다**(H10P 95/04 는 평탄화). 날조된 제목으로 룰을 쓰면 그 룰에
> 근거한 모든 수치가 무효가 된다. 그래서 제목은 스킴 원문에서만 가져온다.

`scheme = IPC-2013` 인 두 행(`H01L21/8247`, `H01L27/108`)은 **폐지된 코드**다. 현행 CPC 스킴에 없고
IPC 2013.01 마스터파일에 있다 (`https://www.wipo.int/classifications/data/ipc/ITSupport_and_download_area/20130101/MasterFiles/ipc_scheme_20130101.zip`).
KIPRIS 가 구형 특허에 그대로 부여해 두었으므로 룰이 필요하다.

## 개념 IRI (`concept_iri`)

SDKB 스냅샷(`data/external/sdkb/`)에 실재하는 인스턴스만 쓴다. 새 어휘를 발명하지 않는다.
공정 개념은 SemiKong Appendix A Table 7(arXiv:2411.13802), 소자 개념은 Wikidata 가 원천이다.

## 축 (`axis`)

`process` → 병합 시 `ont:realizesProcess`, `device` → `ont:concernsDevice`.
소자 분류 코드(H10B·H10D·G11C)를 공정으로 보내지 않는다 — 그것은 근거 없는 매핑이다.

### 후공정(H10W)의 축 배정 규칙 (2026-07-13 확정)

H10W 는 패키지·배선을 담는데, 같은 서브클래스 안에 *구조*와 *제조공정*이 섞여 있다.
축을 우리가 임의로 판단하지 않는다 — **CPC 스킴 자신이 각 메인그룹 아래 `/01 Manufacture or
treatment` 서브그룹을 두어 경계를 그어 놓았고**, 그 경계를 따른다.

하위 개념(subprocess) 선택에는 규칙을 하나 더 둔다:

> **코드가 SDKB 개념 정의(`skos:definition`)에 등장하는 단어를 명시할 때만 하위 개념으로 보낸다.
> 애매하거나 여러 하위에 걸치면 상위 우산 개념(`process/back_end`)으로 보낸다.**

SDKB 의 후공정 개념 세 개는 `skos:broader` 없이 평면이라(`Back-End Processes` ·
`Packaging` · `Advanced Packaging`), 규칙 없이 배정하면 같은 성격의 특허가 임의로 흩어져
단계별 카운트(H1)가 희석된다. 실제 정의:

| 개념 | SDKB `skos:definition` |
|---|---|
| `subprocess/packaging` | Die attach, **wire bonding**, **flip-chip bonding**, **encapsulation** |
| `subprocess/advanced_packaging` | **TSV**, **wafer-level packaging**, **3D integration** |
| `process/back_end` | (우산) interconnect, passivation, thinning, test, dicing and packaging |

이 규칙에 따라 `H10W72/01`(패키지 내 접속 제조)은 `advanced_packaging` 이 아니라
`packaging` 이다 — 정의가 die attach·wire bonding·flip-chip 을 명시하기 때문이다.
`H10W76/01`(용기·실링)과 `H10W95`(잔여 패키징 공정)는 어느 정의에도 걸리지 않으므로
우산 개념으로 보낸다.

## 룰이 없는 코드

다음은 **의도적으로 미매핑**이다. 대응하는 SDKB 개념이 없기 때문이며,
억지로 매핑하지 않고 커버리지 공백으로 보고한다.

| 코드 | 공식 제목 | 왜 매핑하지 않는가 |
|---|---|---|
| H10P 72/00 | Handling or holding of wafers, substrates or devices | 웨이퍼 핸들링은 SemiKong Table 7 의 공정 모듈이 아니다 (장비/자동화) |
| H10D 62/00 · 64/00 | Semiconductor bodies/regions · Electrodes of devices | 소자의 *부분*이지 소자 *유형*이 아니다 |
| H10D 30/67 | Thin-film transistors [TFT] | SDKB Device 에 TFT 개념이 없다 |
| H10W 10 · 15 · 29 · 40 · 42 · 44 · 46 · 78 · 90 · 99 | 격리영역 · 매몰도핑 · 방열 · 보호 · 정렬마크 · 패키지 구성 등 | 대응 개념이 없거나 소자의 *부분*이다. 특히 **H10W 90(Configurations of stacked chips)을 `device/hbm` 으로 보내지 않는다** — 적층 일반이지 HBM 이 아니다 |
| H10W 72/30 · 72/40 · 72/60 · 72/90 | 다이어태치·이방성도전접착제·스트랩·본드패드 | 대응 개념 없음 |
| (BGA) | — | `device/bga` 에 대응하는 깨끗한 코드가 H10W 에 없다 |
| H10K · H10H · H10F | OLED · LED · 광전 소자 | SDKB 의 반도체 공정 도메인 밖 |

> **HBM 과 EUV/DUV 는 IPC 로 매핑되지 않는다.** 둘 다 코드 접두어로 갈리지 않고 명세 텍스트
> (별칭)로만 잡힌다(`map_text_to_concepts`). H2 의 대표 사례가 여기 걸리므로, 이 사실은
> 논문에서 **한계가 아니라 논지**다 — 코드 단위 시계열이 놓치는 신호를 개념 단위가 잡는다.

> **2026-07-13 정정.** 위 표에 있던 `H10W 20/00`("배선 구조는 공정도 소자도 아니다") 행을
> 삭제했다. 그 판단은 SDKB 에 배선 개념이 없던 시점의 것이고, PLAN-001 §3.5 가 SemiKong
> Table 7 의 후공정 그룹(Metallization · Interconnect Patterning · Advanced Packaging)을
> 복원하면서 근거가 소멸했다. 룰 16개를 추가했다(공정 9 · 소자 7).

---

# 신기술 인식 레이어의 출처 (PLAN-004 · 2026-07-13 동결)

`term_aliases.csv`(1층 별칭)와 `emerging_concepts.csv`(2층 조합 정의)의 근거다.
**두 파일은 시계열을 보기 전에 동결됐다** — 커밋 해시가 사전등록(pre-registration)의 증거다.
대상 기술과 정의식은 우리 데이터 분포가 아니라 **외부 원천**에서 왔다 (CLAUDE.md §1.2).

## 왜 이 레이어가 필요한가 (실측)

| 사실 | 값 |
|---|---|
| GAA 전용 코드(`H10D30/6735`·`H10D30/501`)를 받은 삼성·SK하이닉스 특허 | **0건** |
| HBM — 명세에 이름을 쓴 특허 | 32건 |
| HBM — 조합 정의(base)로 잡히는 특허 | **209건** (그중 이름을 쓴 것은 **4건**) |
| FinFET — 코드 135건 · 텍스트 36건 | **교집합 2건** (두 경로가 거의 겹치지 않는다) |
| SDKB 의 `device/gaa_fet` altLabel | **0개** (`device/hbm` 은 영문 1개뿐) |

신기술은 **코드로도 이름으로도 잡히지 않는다.** 이것이 H2 의 장애물이자 H2 의 논지
("코드 단위는 늦다")에 대한 관측 증거다.

## 코드 제목 (verbatim · CPC 2026.01 공식 스킴 HTML 직접 파싱)

요약 모델을 거치지 않았다 (이 문서 상단의 원칙).

| 코드 | 공식 제목 |
|---|---|
| H10B 80/00 | Assemblies of multiple devices comprising at least one memory device covered by this subclass |
| H10W 20/00 | Interconnections in chips, wafers or substrates |
| H10W 20/20 | Interconnections within wafers or substrates, e.g. through-silicon vias [TSV] |
| H10W 20/211 | {Through-semiconductor vias, e.g. TSVs} |
| H10W 20/023 | {the interconnections being through-semiconductor vias} |
| H10W 20/40 | Interconnections external to wafers or substrates, e.g. back-end-of-line [BEOL] metallisations … |
| H10W 90/00 | Package configurations |
| H10D 30/62 | Fin field-effect transistors [FinFET] |
| H10D 30/6735 | {having gates fully surrounding the channels, e.g. gate-all-around} |
| H10D 30/501 | {FETs having stacked nanowire, nanosheet or nanoribbon channels} |
| H01L 25/065 | the devices being of a type provided for in group H10D 89/00 |
| H01L 25/0657 | {Stacked arrangements of devices} |

**H10B 80/00 의 WARNING (verbatim):**
> Group H10B 80/00 is incomplete pending reclassification of documents from group H10W 90/00.
> Groups H10W 90/00 and H10B 80/00 should be considered in order to perform a complete search.

## 조합 정의가 이 제목들에서 나온 방식

- **HBM(base) = (H10B80 ∨ H10W90) ∧ (H10W20/20 ∨ H10W20/211 ∨ H10W20/023)**
  적층 메모리 어셈블리 ∧ TSV. TSV 쪽은 **제목이 TSV 를 명시한 코드만** 넣었다 —
  `H10W20` 전체는 "배선 일반"(BEOL·레이아웃 포함)이라 TSV 가 아니다.
  H10W90 을 적층 집합에 넣는 것은 위 WARNING 의 지시다(우리 판단이 아니다).
- **GAA(base) = H10D30/6735 ∨ H10D30/501.** 두 코드 모두 우리 코퍼스에서 0건이다 —
  그래서 GAA 는 1층(별칭)이 담당한다. "적층 나노시트 채널 FET = GAA 구현"은 우리 해석이
  아니라 `H10D30/501` 의 제목이 직접 말하는 것이다.

> **위 §"매핑하지 않는 코드" 표의 H10W90 항목과 충돌하지 않는다.** 그 표는
> "H10W90 **단독으로** `device/hbm` 을 부여하지 않는다"는 규칙이고, 지금도 유효하다.
> 조합 정의는 H10W90 **∧ TSV** 일 때만 HBM 을 부여한다 — 적층 일반은 여전히 HBM 이 아니다.

## 별칭의 출처

- HBM 계열: **JEDEC JESD235**(HBM/HBM2/HBM2E) · **JESD238**(HBM3/HBM3E) 의 표준 명칭.
- GAA 계열: CPC `H10D30/6735`·`H10D30/501` 의 제목이 명명한 용어(gate-all-around ·
  nanosheet · nanoribbon) + 삼성 3nm 공정의 **MBCFET**(Multi-Bridge Channel FET).
- 국문 별칭은 **SDKB 의 라벨 설계**(prefLabel@en 기준 · altLabel@ko 별칭, 실측 en 630 / ko 428)를
  따른다. 신기술 개념만 이 체계에서 비어 있었으므로(`gaa_fet` altLabel 0개), base 별칭을
  `skos:altLabel`(언어 태그 포함)로 **G₁ 에 실체화**한다. G₀ 는 건드리지 않는다.
- `나노와이어`/`nanowire` 는 **loose 변이 전용**이다. 스킴은 나노시트와 같은 그룹에 두지만,
  명세의 "나노와이어"가 채널이 아닌 구조를 가리킬 수 있어 정밀도 위험이 있다.

## 민감도 변이 (§4.5 — 사전 정의)

| 개념 | strict | base | loose |
|---|---:|---:|---:|
| HBM | 74건 | **209건** | 1,018건 |
| GAA (코드) | 0건 | 0건 | 135건(FinFET 포함 시) |

결론이 정의에 민감하면 **그 사실 자체를 보고한다.**
