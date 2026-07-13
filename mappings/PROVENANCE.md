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
