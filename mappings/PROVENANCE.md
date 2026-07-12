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

## 룰이 없는 코드

SIRP 1,000건에서 다음은 **의도적으로 미매핑**이다. 대응하는 SDKB 개념이 없기 때문이며,
억지로 매핑하지 않고 커버리지 공백으로 보고한다.

| 코드 | 공식 제목 | 왜 매핑하지 않는가 |
|---|---|---|
| H10P 72/00 | Handling or holding of wafers, substrates or devices | 웨이퍼 핸들링은 SemiKong Table 7 의 공정 모듈이 아니다 (장비/자동화) |
| H10D 62/00 · 64/00 | Semiconductor bodies/regions · Electrodes of devices | 소자의 *부분*이지 소자 *유형*이 아니다 |
| H10D 30/67 | Thin-film transistors [TFT] | SDKB Device 에 TFT 개념이 없다 |
| H10W 20/00 | Interconnections in chips, wafers or substrates | 배선 *구조*는 공정도 소자도 아니다 |
| H10K · H10H · H10F | OLED · LED · 광전 소자 | SDKB 의 반도체 공정 도메인 밖 |
