# data/ — 최종 온톨로지 현황과 갱신 규율

> **이 디렉토리를 열었을 때 가장 먼저 읽는 문서.** "지금 무엇이 최종 온톨로지인가"와
> "향후 보강하면 무엇을 어떻게 갱신하는가"를 한 곳에 고정한다. **숫자는 여기에 다시 적지 않는다**
> — 숫자를 여러 곳에 복사한 것이 혼선의 원인이었다. 서명 수치의 정본은 아래 두 곳뿐이다.
>
> | 무엇 | 정본 위치 |
> |---|---|
> | **현재 그래프 서명(트리플·커버·게이트)** | [`MANIFEST.md` §3](MANIFEST.md) — `make baseline`·`make merge` 출력의 기록 |
> | **전 저장소 정본/중간/계획 판정** | [`../01.code_spec/CANONICAL-INDEX.md`](../01.code_spec/CANONICAL-INDEX.md) §1 |

---

## 1. 최종 온톨로지는 무엇인가 (파일 지도)

**정본은 "얼린 상류 스냅샷 + 코드"이고, 그래프 파일은 거기서 결정적으로 재생성되는 산출물이다.**
그래서 그래프 `.ttl` 은 gitignore 다 — 잃어버려도 `make` 로 똑같이 되살아난다. 최종의 *원천*은 커밋된다.

| 계층 | 최종 산출물 | 위치 | git | 재생성 |
|---|---|---|---|---|
| **최종의 원천 (동결·보존)** | 상류 SDKB 스냅샷 13파일 + `PROVENANCE.json`(sha256) | `external/sdkb/` | ✅ tracked | `make vendor` |
| **G₀ (baseline · H1 before)** | `graph_v0.ttl` | `processed/` | ⛔ ignore | `make baseline` |
| **G₁ (삼성·SK하이닉스 보강)** | `graph_v1.ttl` | `processed/` | ⛔ ignore | `make merge` |
| **G₂ (소부장 188사 · RQ3)** | `graph_v2.ttl` + 층별 `graph_v2_{equipment,material,component}.ttl` | `processed/` | ⛔ ignore | `make merge CORPUS=ksia-equipment` · `make ksia-strata` |
| **분석 산출 (논문 표·그림 원천)** | `h1_*.csv/md` · `h2_*.csv/md` · `robustness_*.md` | `processed/` | ⛔ ignore | `make h1` · `make h2` · `make robustness` |
| **수집 프로파일 (논문 표 4)** | `kipris_*.md` · `family_dedup.md` | `profiles/` | ✅ tracked | `make profile` |
| **게이트 픽스처** | `mini_graph.ttl` | `samples/` | ✅ tracked | 손유지(합성 3특허) |

> `processed/` 안에서 **무엇이 최종이고 무엇이 병합 전 입력·분할본인지**는
> [`processed/README.md`](processed/README.md) 가 파일별로 판정한다. `delta_*`·`graph_v1_{samsung,hynix,famdedup}`
> 는 최종이 **아니다**(중간·강건성 산출).

**중간·원문(커밋 안 함, 재배포 금지):** `raw/`(KIPRIS·BigQuery·DART 원문·캐시) · `interim/`(*.parquet) —
전부 gitignore. 학술 이용·비재배포 조건.

---

## 2. 향후 보강 시 갱신 규율 — "새 사본을 만들지 말고 최종을 다시 굳힌다"

보강(새 특허·벤더·규제·어휘)이 생기면 **아래 순서를 지키고, 새 그래프 이름을 만들지 않는다.**
G₀/G₁/G₂ 는 *같은 파일명*으로 재생성되고, 서명은 *같은 표*(MANIFEST §3)에서 갱신된다.
새 `graph_v3`·`graph_v1_new` 같은 이름이 생기는 순간 혼선이 재발한다.

```
① 상류 SDKB 에서 고친다 (이 저장소에서 우회 패치 금지 — 스냅샷 출처가 거짓이 된다)
② make vendor        # external/sdkb/ 재동결 + PROVENANCE.json sha256 재작성
③ make baseline      # graph_v0(G₀) 재생성 — H1 의 before
④ make merge [CORPUS=…]   # graph_v1 / graph_v2 재생성
⑤ make gate          # snapshot→L1→L2→L3, 통과 확인
⑥ make baseline 두 번 재실행해 graph_v0 바이트 동일 확인 (결정성 = H1 재현성)
⑦ 서명 갱신을 한 커밋으로: MANIFEST §1 이력표에 새 줄 + §3 서명 수정
                        + CANONICAL-INDEX.md §1 수정 + 이 파일 §1 지도가 바뀌면 반영
```

> **G₀ 는 동결이 기본이다.** ③④ 로 G₀ 가 움직이면 H1 이 재현되지 않는다. G₀ 를 바꾸는 보강은
> **사람 승인**이 있어야 하고(§0.1 규약), 바꾼 뒤에는 H1·H2 를 전면 재실행해 p 불변(또는 변화)을
> 보고한다. 규제·FTO 어휘 적재처럼 **개념 속성만 더하고 특허↔공정 엣지를 안 건드리는** 보강은
> C₀ 와 H1 p 를 불변으로 유지한다 — 그것을 서명에 명시한다(예: 44,192→44,202 재동결).

> **왜 그래프를 커밋하지 않는가.** `.ttl` 을 커밋하면 "디스크의 파일"과 "코드가 만드는 그래프"가
> 갈라져 또 하나의 정본 후보가 생긴다. 원천(스냅샷)만 커밋하고 그래프는 재생성함으로써
> **정본이 언제나 하나**가 되게 한다.

---

## 3. 이 디렉토리의 문서 지도

| 문서 | 역할 |
|---|---|
| `README.md` (이 파일) | 최종 온톨로지 지도 + 갱신 규율 |
| [`MANIFEST.md`](MANIFEST.md) | 수집·스냅샷·파생 그래프의 **이력과 서명**(§1 baseline · §2 수집 · §3 파생) — 서명 수치의 정본 |
| [`processed/README.md`](processed/README.md) | `processed/` 파일별 정본/중간 판정 |
| [`profiles/*.md`](profiles/) | 수집 코퍼스 기술통계(논문 표 4) — 코드 생성 |
