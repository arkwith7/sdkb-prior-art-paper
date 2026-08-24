"""한정요소 투영 항 U2 (PLAN-075 §12.2 · 순위 함수의 `w_f2` 항 입력).

**왜 이 모듈이 있는가.** 상류가 발행한 `claim_features.parquet` 는 청구항 한정요소 1,306,191 행에
개념을 투영해 두었는데, 하류에 그것을 읽는 소비자가 없었다(메모리 `vendored-claim-features-has-no-consumer`
· D-51). 이 모듈이 그 통로다 — 코퍼스 문서 개념 가방(`concepts` 열)이 문서 전체를 하나로 뭉개는
것과 달리, 투영은 **독립항 한정요소 단위**로 개념을 보관한다.

정의(설계 §12.2 · PLAN-073 §10.4 ① ② ⑤ 승계):

    U2(q,d) = |C_ind(q) ∩ C_ind(d)| / |C_ind(q) ∪ C_ind(d)|

`C_ind(x)` = x 의 **독립항** 한정요소 개념의 합집합(축 접두 제거). 후보 U1·U3 을 쓰지 않는 이유는
PLAN-073 §10 이 실측했다 — U1 은 기존 항과 상관 0.829 로 중복이고, U3(피복률)은 크기 비정규화라
출처 밀도 편향에 가장 노출된다.

**식별자 정규화가 첫째 계약이다.** 투영은 `process:deposition`(축 접두 포함), 코퍼스는
`deposition`(접두 없음)이다. 접두를 떼면 투영의 122 종은 코퍼스 199 종의 부분집합이며 초과는
0 이다(PLAN-073 §10.2a). 이 정규화를 빠뜨리면 항이 **항상 0** 이 되어 조용히 실패한다.

**결측은 0 이 아니다.** 투영이 없는 문서에서는 `has(doc)` 가 False 를 돌려주고, 호출자가 그 항을
빼고 남은 가중을 재정규화한다(§12.2). dev 정답의 32.4 % 가 여기 해당하므로, 0 으로 채우면 없는
증거가 불리한 증거로 바뀐다.
"""
from __future__ import annotations

from functools import lru_cache

from .. import config

CLAIM_FEATURES = "claim_features.parquet"


def _slug(concept_id: str) -> str:
    """`process:deposition` → `deposition` (§12.2 ⑤ · 정규화는 접두 제거 하나)."""
    return concept_id.split(":", 1)[1] if ":" in concept_id else concept_id


class ProjectionIndex:
    """문서 → 독립항 한정요소 개념 집합. U2 만 제공한다(§12.2)."""

    def __init__(self, restrict_docs: set[str] | None = None) -> None:
        import pandas as pd

        path = config.EXTERNAL_SDKB / CLAIM_FEATURES
        df = pd.read_parquet(path, columns=["publication_id", "is_independent",
                                            "feature_concept"])
        df = df[df["is_independent"]]
        if restrict_docs is not None:
            df = df[df["publication_id"].isin(restrict_docs)]
        sets: dict[str, set[str]] = {}
        for doc, concepts in zip(df["publication_id"], df["feature_concept"], strict=True):
            if concepts is None:
                continue
            items = concepts.tolist() if hasattr(concepts, "tolist") else list(concepts)
            if not items:
                continue
            sets.setdefault(str(doc), set()).update(_slug(c) for c in items)
        self.sets: dict[str, frozenset[str]] = {d: frozenset(s) for d, s in sets.items() if s}

    def has(self, doc: str) -> bool:
        """투영을 보유하는가. False 면 호출자가 항을 빼고 재정규화한다(결측 ≠ 0)."""
        return doc in self.sets

    def concepts(self, doc: str) -> frozenset[str]:
        return self.sets.get(doc, frozenset())

    def u2(self, qid: str, doc: str) -> float:
        """독립항 한정요소 개념 합집합의 Jaccard. 한쪽이라도 없으면 0(호출자가 마스킹)."""
        a, b = self.sets.get(qid), self.sets.get(doc)
        if not a or not b:
            return 0.0
        inter = len(a & b)
        return inter / len(a | b) if inter else 0.0


@lru_cache(maxsize=1)
def load_projection() -> ProjectionIndex:
    """전 코퍼스 판(캐시). 후보를 좁힐 때는 `ProjectionIndex(restrict_docs=…)` 를 직접 쓴다."""
    return ProjectionIndex()
