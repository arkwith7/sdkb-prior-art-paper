# PLAN-066 산출물 — 리포 반영 안내

> **아카이빙 2026-08-23.** 이 안내가 가리키는 파일 다섯은 전부 리포에 반영이 끝났다(커밋 `50ccb8c`).
> 반영 완료 후의 전달 안내이므로 루트에서 내렸다 — 열린 항목은 [`plans/OPEN-ITEMS.md`](../plans/OPEN-ITEMS.md) O-2·O-3.

아래 경로 그대로 `sdkb-prior-art-paper/` 루트에 두면 된다. 신설 4 + 기존 파일 패치 1.

| 파일 | 종류 | 내용 |
|---|---|---|
| `paper/glossary-terms.yaml` | 신설 | 첫 등장 규율의 기계 정본 — 용어 31항(부류 ㈎㈏㈐ · 정의 위치 · 약어 · 금지 동의어·다의어) |
| `scripts/check_glossary.py` | 신설 | 검사기 G1–G5 · `--warn` · `--inventory` · `--strict-g4` · 면제 `<!-- glossary-ok: 사유 -->` |
| `tests/test_check_glossary.py` | 신설 | 12건 — 의도적 위반 6(G1×2·G2·G4·G5) · 허용 5 · 정본 스키마 1 |
| `01.code_spec/plans/PLAN-066-terminology-first-mention.md` | 신설 | 계획 · 실측 · B 단계 편입 순서와 예산 · DoD · 부속 A(§3.0 문안) · 부속 B(§4.5 지표 표) |
| `patch-d-glossary-check.diff` | 패치 | `Makefile`(`glossary-check`·`glossary-inventory` 타깃) · `paper/STYLE-KO-ACADEMIC.md`(V1·V2 기계 검사 표기 · V1-a 신설) · `paper/glossary.md`(§J 추가) |

적용 순서:

```bash
git checkout -b plan-066-glossary
cp -r paper scripts tests 01.code_spec .          # 신설 4 파일
git apply patch-d-glossary-check.diff             # 기존 3 파일
uv run pytest -q tests/test_check_glossary.py     # 12 passed
uv run ruff check scripts/check_glossary.py tests/test_check_glossary.py
make glossary-inventory                           # 실측 대장 — PLAN-066 §1·glossary.md §J.3 과 대조
```

검증 결과(2026-08-22 · 공개 리포 main `fff745d` 클론에서 실측):
- `pytest tests/test_check_glossary.py` 12 passed · ruff 통과
- `make glossary-check` → 경고 모드 · 파생본 위반 25건(G1 24 · G5 1) · 경고 7건(G4) ·
  산문 소스 포함 두 파일 합계 50건/14건
- 전체 `uv run pytest -q` 에서 실패한 17건·에러 13건은 전부 `test_baseline_integration`·`test_ep5`·
  `test_profile` 등 **vendor 데이터·EP5 산출물 부재**에 의한 것으로 이 산출물과 무관하다(얕은 클론).

주의:
- `glossary-terms.yaml` 의 한국어 정식 용어(예: 맥니마 검정 · 판정 비적합 기반 선호도 · 정답 비참조
  분석)는 **제안**이다. 확정은 사용자 승인이며, glossary.md A–I 의 영문 확정어와 충돌하면 그쪽이 우선한다.
- 검사기는 `--warn` 으로 시작한다. 차단 승격은 PLAN-066 §4 의 조건(위반 0 실측) 뒤에만.
- 부속 A 의 §3.0 문안은 `style_check.check_file` 로 S3·T2·T3·T7 통과를 확인했다. 절 번호 `3.0` 은
  저장소 관행에 맞춰 바꿔도 된다(검사기는 번호를 보지 않는다).
