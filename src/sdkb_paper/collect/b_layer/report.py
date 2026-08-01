"""`r` 추정과 데이터 프로파일 (PLAN-032 §5.7 · CLAUDE §4).

**Wilson 구간을 쓰는 이유.** `r` 은 3 %대일 수 있고(PLAN-029 §3.0 관측) 정규근사 구간은 그
영역에서 하한이 음수가 된다 — 통과율의 하한이 음수라는 보고는 그 자체로 결함이다.

세 비율을 함께 보고한다(결정 B):
    r_free   = free 통과 / 스크리닝 진입 후보
    r_family = family 통과 / family 판정 진입
    r        = 채택 / **소비된 서지상세 콜**       ← §8.1 산식의 r
감사(결정 E) 콜은 채택을 만들 수 없으므로 `r` 의 분모에서 제외한다 — 이 포함·제외는
결과를 보기 전에 고정됐다(PLAN-031 §8 항목 9).
"""
from __future__ import annotations

import json
import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from sdkb_paper.collect.b_layer.ledger import LedgerRow

Z95 = 1.959963984540054   # 표준정규 0.975 분위 (동결 상수 — scipy 의존을 만들지 않는다)
# 감사 행의 verdict (결정 E). 채택/기각과 섞이지 않도록 별도 어휘를 쓴다.
AUDIT_FALSE_NEGATIVE = "audit_false_negative"   # 무료 배제됐으나 실제로는 포함 1 만족
AUDIT_CONFIRMED = "audit_confirmed"             # 무료 배제가 옳았다


@dataclass(frozen=True)
class RateEstimate:
    numerator: int
    denominator: int
    point: float
    lo: float
    hi: float

    def __str__(self) -> str:
        return (f"{self.point:.4f} [{self.lo:.4f}, {self.hi:.4f}] "
                f"({self.numerator}/{self.denominator})")


def wilson(successes: int, trials: int, z: float = Z95) -> RateEstimate:
    """Wilson score 구간. 시행 0이면 점추정 0·구간 [0,1](= 아무것도 모른다)."""
    if trials <= 0:
        return RateEstimate(successes, trials, 0.0, 0.0, 1.0)
    p = successes / trials
    denom = 1 + z**2 / trials
    center = (p + z**2 / (2 * trials)) / denom
    half = z * math.sqrt(p * (1 - p) / trials + z**2 / (4 * trials**2)) / denom
    return RateEstimate(successes, trials, p, max(0.0, center - half), min(1.0, center + half))


def estimate_rates(rows: list[LedgerRow]) -> dict[str, RateEstimate]:
    """원장에서 세 비율을 산출한다. 감사 행(`stage='audit'`)은 전부 제외한다."""
    scored = [r for r in rows if r.stage != "audit"]
    free_entered = len(scored)
    free_passed = sum(1 for r in scored if r.stage in ("family", "detail"))
    family_entered = sum(1 for r in scored if r.stage in ("family", "detail"))
    family_passed = sum(1 for r in scored if r.stage == "detail")
    detail_calls = sum(1 for r in scored if r.detail_call_used)
    accepted = sum(1 for r in scored if r.verdict == "accepted")
    return {
        "r_free": wilson(free_passed, free_entered),
        "r_family": wilson(family_passed, family_entered),
        "r": wilson(accepted, detail_calls),
    }


def audit_false_negative_rate(rows: list[LedgerRow]) -> RateEstimate:
    """감사(결정 E)의 위음성률 — 무료 배제된 건 중 실제로는 §3 포함 1을 만족한 비율.

    위음성이 나와도 파일럿의 채택 집합은 재산출하지 않는다 — 측정하고 보고할 뿐이다(§6.1).
    """
    audits = [r for r in rows if r.stage == "audit"]
    return wilson(sum(1 for r in audits if r.verdict == AUDIT_FALSE_NEGATIVE), len(audits))


def reason_counts(rows: list[LedgerRow]) -> dict[str, int]:
    """사유 코드 분포 — 정렬해 결정적으로 만든다(보고서 diff 안정)."""
    return dict(sorted(Counter(r.reason for r in rows).items()))


def _dist(values: list[str], top: int = 10) -> list[tuple[str, int]]:
    """빈도 내림차순 · 동수는 값 오름차순 — 보고서가 재실행마다 같아야 한다."""
    return sorted(Counter(values).items(), key=lambda kv: (-kv[1], kv[0]))[:top]


def _contrast_table(label: str, b_values: list[str], a_values: list[str] | None) -> list[str]:
    """B층 분포 표. A층 값이 없으면 **0으로 채우지 않고 열을 빼고 사유를 밝힌다.**

    A층 주분류는 상류 `rejected_patents_meta.parquet` 에만 있고, 이 저장소는 런타임에
    `~/Dev/sdkb` 를 읽지 않는다(CLAUDE §0.1). 없는 값을 0으로 적으면 "A층에 없다"는
    거짓 보고가 된다 — 없으면 없다고 쓴다.
    """
    if not a_values:
        return [
            f"| {label} | B층 |", "|---|---:|",
            *[f"| {k} | {n:,} |" for k, n in _dist(b_values)],
            "",
            f"> A층 {label} 분포는 이 표에 없다 — 상류 원본에만 있고 런타임 상류 접근을 하지 "
            "않기 때문이다(CLAUDE §0.1). 대조는 vendor 된 값이 생긴 뒤 별도로 붙인다.",
        ]
    a_map = dict(_dist(a_values, top=1000))
    return [
        f"| {label} | B층 | A층 |", "|---|---:|---:|",
        *[f"| {k} | {n:,} | {a_map.get(k, 0):,} |" for k, n in _dist(b_values)],
    ]


def write_profile(
    rows: list[LedgerRow],
    accepted: list[dict],
    path: Path,
    *,
    a_layer_years: list[str] | None = None,
    a_layer_ipc: list[str] | None = None,
    budget: dict | None = None,
) -> Path:
    """§4 데이터 프로파일 — 구조·형태·기술통계·사용목적 + **A층 대조**(PLAN-031 §4 보고 의무).

    수기 기입 없이 코드가 만든다(CLAUDE §1-7). 파일럿 단계이므로 **정답 언어분포는 싣지 않는다** —
    그것을 세려면 봉인 qrel 을 열어야 하기 때문이다(§1 성공기준 ⑤). 본수집 후 별도로 산출한다.
    """
    rates = estimate_rates(rows)
    years = [a["application_date"][:4] for a in accepted]
    ipcs = [a["ipc_leading"] for a in accepted]
    lines = [
        "# B층 파일럿 수집 프로파일 (PLAN-032 §5.6 · 자동 생성)",
        "",
        "> 이 파일은 `sdkb_paper.collect.b_layer` 가 생성한다. 수기 수정 금지(CLAUDE §1-7).",
        "> **봉인 규율:** 정답(심사관 인용) 식별자·언어분포는 여기에 없다 — 봉인 파일을 열지 않았다.",
        "",
        "## 1. 구조",
        "",
        "| 산출물 | 키 | 원천 |",
        "|---|---|---|",
        "| 스크리닝 원장 (JSONL) | `application_number` | KIPRIS `getAdvancedSearch` 응답 |",
        "| 채택 레코드 (parquet) | `application_number` | + `getBibliographyDetailInfoSearch` |",
        "| 봉인 qrel (parquet) | `application_number` × 인용 | 서지상세 `priorArtDocumentsInfo` |",
        "",
        "## 2. 형태",
        "",
        f"- 스크리닝 후보 {len(rows):,}행 · 채택 {len(accepted):,}건",
        f"- 고유 출원번호 {len({r.application_number for r in rows}):,}",
        f"- 출원일 범위 {min(years) if years else '—'} ~ {max(years) if years else '—'} (채택분)",
        "",
        "## 3. 기술통계",
        "",
        "### 3.1 비율 (Wilson 95 % CI · 결정 B)",
        "",
        "| 지표 | 값 [95 % CI] (분자/분모) |",
        "|---|---|",
        *[f"| `{k}` | {v} |" for k, v in rates.items()],
        "",
        "### 3.2 사유 코드 분포 (동결 12종)",
        "",
        "| 코드 | 건수 |",
        "|---|---:|",
        *[f"| `{k}` | {v:,} |" for k, v in reason_counts(rows).items()],
        "",
        "### 3.3 채택분 분포와 A층 대조 (PLAN-031 §4 보고 의무)",
        "",
        *_contrast_table("출원연도", years, a_layer_years),
        "",
        *_contrast_table("주분류 IPC", ipcs, a_layer_ipc),
        "",
        "> 분포가 다르므로 **기존 test 결과와 직접 비교하지 않는다** — B층은 자체 완결적 확증이다.",
        "",
        "## 4. 호출 회계 (4계정 분리 · §1 동결)",
        "",
        f"```json\n{json.dumps(budget or {}, ensure_ascii=False, indent=2, sort_keys=True)}\n```",
        "",
        "## 5. 사용 목적",
        "",
        "- 채택 레코드 → B층 질의 (H3·H4·H5 재확증 · PLAN-031 §4)",
        "- 봉인 qrel → 최종 1회 개봉 시의 정답 (그 전까지 읽지 않는다)",
        "- `r` → 본수집 예산 확정 (§8.1 `총콜 ≈ 200/r + 200`)",
        "- 감사 위음성률 → 무료 배제 가정의 검증 (결정 E · 규칙은 바꾸지 않는다)",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def projected_budget(rates: dict[str, RateEstimate], target: int) -> dict[str, float]:
    """§8.1 산식 `총콜 ≈ target/r + target`. r=0 이면 추정 불가로 표시한다."""
    r = rates["r"].point
    if r <= 0:
        return {"detail_calls": float("inf"), "notice_calls": float(target),
                "total": float("inf")}
    return {"detail_calls": target / r, "notice_calls": float(target),
            "total": target / r + target}
