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
| 2026-07-11 | [semiconductor-knowledge-base](https://github.com/arkwith7/semiconductor-knowledge-base) (CDLA-Permissive-2.0) | `e64f90cc74ec` | TBox: core·patent·foresight / ABox: core-data | 229 노드, 268 엣지 → 3,201 트리플 | `graph_v0.ttl` |

- 파일별 sha256 과 원천(`semiconductor_v0_3.json`, sha256 `806600ab…`)은 `data/external/sdkb/PROVENANCE.json` 에 기록.
- **의도적 제외**: SDKB 의 SIRP 특허 ABox(`sdkb-abox-patents.ttl`, 거절특허 773건). baseline 을
  특허 0건 상태로 두어야 KIPRIS 보강의 H1 효과가 측정된다. SIRP 는 별도 비교군으로 쓴다.
- `graph_v0.ttl` 은 스냅샷에서 결정적으로 재생성되므로 커밋하지 않는다 (`make baseline`).

## 2. 특허 수집 (KIPRIS / BigQuery)

| 일시 | 소스 | 검색식/쿼리 | 건수 | 저장 파일 | 그래프 반영 버전 |
|---|---|---|---:|---|---|
| (예) 2026-08-01 | KIPRIS | AP=[삼성전자]*IPC=[H01L] | 12,345 | raw/kipris/samsung_h01l.parquet | graph_v1.ttl |
