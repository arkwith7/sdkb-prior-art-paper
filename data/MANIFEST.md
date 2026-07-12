# 데이터 매니페스트

raw 데이터는 git 에 커밋하지 않는다. 모든 수집은 아래 표에 기록해 재현 가능하게 유지한다.

## 1. 근간 온톨로지 스냅샷 (baseline)

이 논문의 baseline 은 SDKB(semiconductor-knowledge-base)를 **특정 커밋에 얼려서** 가져온
`data/external/sdkb/` 스냅샷이다. 살아있는 워킹트리를 참조하지 않는다 — baseline 이 움직이면
H1(보강 전/후 커버리지 비교)이 재현되지 않기 때문이다.

주의: SDKB 의 `sdkb-core.ttl` / `sdkb-core-data.ttl` 은 SDKB repo 의 **.gitignore 대상(빌드 산출물)**
이다. git 에 없으므로 submodule/pip 로는 가져올 수 없고, SDKB 쪽에서 `make owl convert` 로 생성한
결과를 복사해야 한다. 갱신 절차:

```bash
cd $SDKB_HOME && make owl convert   # 산출물 재생성
cd -                                # 논문 repo 로
make vendor                         # 스냅샷 갱신 (+ PROVENANCE.json 재작성)
make baseline                       # graph_v0 재조립
# -> 아래 표에 새 줄 추가하고 한 커밋으로 묶는다
```

| 일시 | 소스 | 커밋 | 가져온 것 | 규모 | 산출 그래프 |
|---|---|---|---|---:|---|
| 2026-07-11 | [semiconductor-knowledge-base](https://github.com/arkwith7/semiconductor-knowledge-base) (CDLA-Permissive-2.0) | `e64f90cc74ec` | TBox: core·patent·foresight / ABox: core-data (SIRP 제외) | 3,201 트리플 | (폐기) |
| 2026-07-12 | 〃 | `4fca29c3f6e2` | TBox: core·patent·foresight / ABox: core-data + **SIRP 특허 1,000건** | 24,566 트리플 | `graph_v0.ttl` |

**G₀ 정의 변경 (2026-07-12).** 이전 스냅샷은 SIRP 특허 ABox 를 의도적으로 제외해 baseline 을
특허 0건으로 두었다. 그러면 모든 공정 단계에서 C₀(s)=0 이 되어 **H1 이 기각될 수 없는 자명한
가설**이 된다. G₀ 는 "현행 SDKB"여야 한다. 새 baseline 의 서명:

| 항목 | 값 |
|---|---:|
| 트리플 | 26,676 |
| 공정 단계 (H1 의 관측 단위) | 20 (Process 8 + SubProcess 12) |
| 디바이스 (H2 의 개념 축에 포함) | 31 |
| 특허 (SIRP 거절특허) | 1,000 |
| 출원일 보유 특허 | 1,000 (100%) |
| 출원인(Organization) | 351 |
| **커버된 공정 단계 C₀** | **16 / 20** |
| **커버리지 공백** | **4 / 20** |
| 최근 5년(2021–) 출원 전무 개념 (CQ06) | **29 / 51** |
| CQ 응답률 (8개) | **100%** |

**출원인 상위 (SIRP 는 다출원인 코퍼스다)**: SK hynix 128 · **Samsung Electronics 75** ·
Semiconductor Energy Lab 42 · TSMC 29 · Applied Materials 26 · Toshiba 28 · LAM 19.
→ 삼성 특허를 수집할 때 **출원번호 기준 중복 제거가 필수**다. 이 75건이 이미 G₀ 에 있다.

- 상류에서 **출원일이 정정되었다**: SDKB 의 `filing_date` 는 출원일이 아니라 공개일이었다
  (KIPRIS 대조로 확인). SDKB 커밋 `4fca29c` 에서 KIPRIS 권위 원천으로 재수집·교체했다.
  이 정정 없이는 H2 시계열이 1~2년 밀린다.
- SIRP 는 **1,000건**이다. 초기 코호트 스냅샷이 773건이었고 GT 페어가 그 시점에 동결되어 있다 —
  이전 표의 "773건"은 그 혼동이었다.
- 파일별 sha256 은 `data/external/sdkb/PROVENANCE.json` 에 기록.
- `graph_v0.ttl` 은 스냅샷에서 결정적으로 재생성되므로 커밋하지 않는다 (`make baseline`).

## 2. 특허 수집 (KIPRIS / BigQuery)

| 일시 | 소스 | 검색식/쿼리 | 건수 | 저장 파일 | 그래프 반영 버전 |
|---|---|---|---:|---|---|
| (예) 2026-08-01 | KIPRIS | AP=[삼성전자]*IPC=[H01L] | 12,345 | raw/kipris/samsung_h01l.parquet | graph_v1.ttl |
