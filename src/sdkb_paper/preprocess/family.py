"""패밀리 단위 중복 제거 (§4.5 강건성 · 결과를 보기 전에 동결한 규칙).

출원번호 dedup(`clean.py::dedup`)은 같은 발명의 국내 분할·계속출원을 잡지 못한다. 여기서
DOCDB `family_id` 로 그것을 잡는다. **네 규칙은 결과를 보기 전에 못 박았다** (STATUS · PLAN-011):

1. **미상은 dedup 하지 않는다.** BQ 에 조인되지 않았거나 `family_id = '-1'` 인 출원은 각각
   고유 패밀리(`solo:<출원번호>`)로 둔다. 조인 실패를 이유로 특허를 지우면 dedup 이 아니라
   표본 삭제다.
2. **패밀리는 공유 id 의 연결성분이다.** BQ 는 한 출원에 family_id 를 둘 붙이기도 한다
   (말뭉치의 9.6%). id 하나로 그룹핑하면 같은 발명이 두 패밀리로 쪼개진다 — 공유 id 로
   이어지는 출원들을 union-find 로 묶어 **동치관계**를 복원한다.
3. **대표는 최소 출원일**, 동률이면 최소 출원번호. 시점을 논하는 논문이므로 가장 이른 출원을
   남긴다 (결정적 — 입력 순서에 무관).
4. **G₀ 우선.** 패밀리에 G₀ 특허가 하나라도 있으면 그 패밀리의 델타 특허는 전부 뺀다.
   G₀ 는 동결이라 한 트리플도 움직이지 않는다 — H1 의 before 는 불변이다.
"""
from __future__ import annotations

import pandas as pd


class _UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, x: str) -> str:
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            # 사전순 최소를 뿌리로 — 결정적이다(입력 순서에 무관).
            lo, hi = (ra, rb) if ra < rb else (rb, ra)
            self.parent[hi] = lo


def family_key(app: str, groups: dict[str, list[str]]) -> str:
    """출원번호 → 패밀리 키. 미상은 자기 자신만의 패밀리다 (규칙 1)."""
    ids = [i for i in groups.get(app, []) if i and i != "-1"]
    return "|".join(sorted(ids)) if ids else f"solo:{app}"


def family_keys(apps: list[str], fam: dict[str, str] | pd.DataFrame) -> dict[str, str]:
    """{출원번호: 패밀리 키}. 공유 family_id 로 이어지는 출원은 같은 키를 받는다 (규칙 2).

    fam 은 {출원번호: family_id} 딕셔너리이거나 (application_number, family_id) 프레임이다 —
    한 출원에 id 가 여럿이면 프레임으로 넘겨야 전부 반영된다.
    """
    if isinstance(fam, pd.DataFrame):
        pairs = [
            (str(a), str(i))
            for a, i in zip(fam["application_number"], fam["family_id"], strict=True)
        ]
    else:
        pairs = [(str(a), str(i)) for a, i in fam.items()]

    uf = _UnionFind()
    for app, fid in pairs:
        if fid and fid != "-1":
            uf.union(f"a:{app}", f"f:{fid}")  # 출원과 id 를 같은 성분에 넣는다

    seen = set(apps)
    return {
        app: (uf.find(f"a:{app}") if f"a:{app}" in uf.parent else f"solo:{app}") for app in seen
    }


def dedup_families(
    df: pd.DataFrame,
    fam: dict[str, str] | pd.DataFrame,
    g0_apps: set[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(패밀리 대표만 남긴 프레임, 제거된 프레임). 제거분도 보고 대상이다.

    df 는 `application_number` · `application_date` 를 갖는 말뭉치다. G₀ 는 건드리지 않는다 —
    g0_apps 가 주어지면 **G₀ 와 패밀리를 공유하는 델타 특허만** 뺀다 (규칙 4).
    """
    if df.empty:
        return df.copy(), df.copy()

    apps = [str(a) for a in df["application_number"]]
    keys = family_keys(apps + sorted(g0_apps or set()), fam)

    out = df.copy()
    out["family_key"] = [keys[str(a)] for a in out["application_number"]]

    if g0_apps:
        g0_keys = {keys[a] for a in g0_apps if not keys[a].startswith("solo:")}
        in_g0 = out["family_key"].isin(g0_keys)
    else:
        in_g0 = pd.Series(False, index=out.index)

    rest = out[~in_g0]
    # 규칙 3 — 최소 출원일, 동률이면 최소 출원번호. sort 후 first 라 결정적이다.
    order = rest.sort_values(["family_key", "application_date", "application_number"])
    rep = order.groupby("family_key", sort=False).head(1)

    kept = out.loc[out.index.isin(rep.index)]
    dropped = out.loc[~out.index.isin(rep.index)]
    dropped = dropped.assign(
        drop_reason=lambda d: d.index.map(lambda i: "g0_family" if in_g0.loc[i] else "family_dup")
    )
    return kept.drop(columns=["family_key"]), dropped
