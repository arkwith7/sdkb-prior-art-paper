"""KSIA 소부장(장비·재료·부분품) → G₀ organization IRI 크로스워크 생성 (사전동결).

RQ3(외적 타당도)의 코퍼스는 **소부장 전체** 191사다 — 장비 94 · 재료 51 · 부분품 46.
매칭은 결정적이다: G₀ organization 노드의 prefLabel/altLabel/slug 를 정규화한 인덱스에
KSIA 국문·영문명(정규화)을 대조한다. 자동 매칭이 안 되는 소수는 수동 사전(MANUAL)으로
확정한다. match_key 는 런타임 필터와 **같은 함수**(clean.normalize_company_name)로 만든다.

산출: mappings/ksia_applicant_crosswalk.csv (커밋 대상 · 집계·메타데이터만).
  company_type 컬럼이 층별 H1(§4.6 · 표 5b)의 층화 키다 — 회사당 한 값(KSIA 업체구분).
"""
from __future__ import annotations

import csv
from collections import Counter

from rdflib import Graph
from rdflib.namespace import SKOS

from sdkb_paper.config import GRAPH_V0, KSIA_CROSSWALK, MAPPINGS
from sdkb_paper.preprocess.clean import normalize_company_name

KSIA_LIST = MAPPINGS / "ksia_member_industry_list_20260714.csv"

# 소부장 = 소재·부품·장비. KSIA 업체구분 원표기 → 층 라벨(그래프·논문에서 쓰는 짧은 이름).
CORPUS_TYPES = {"장비업체": "equipment", "재료업체": "material", "부분품업체": "component"}

# 수동 확정 — 정규화가 괄호 별칭·접미사 변이 때문에 놓친 위양성. 슬러그는 G₀ 실측.
# 장비사(2026-07-15)에 재료·부분품사(2026-07-16)를 추가한다. 값은 G₀ organization slug 다.
MANUAL: dict[str, str] = {
    "㈜아이씨디": "innovation_for_creative_devices",  # 영문명 괄호 (ICD CO.,LTD.)
    "주식회사 아이에스티이": "iste",                    # 접미사 Co.,Ltd.
    "한국알박㈜": "ulvac_korea",                       # STATUS.md 가 남긴 별개법인 Ulvac Korea
}


def lookup(idx: dict[str, str], *names: str) -> str | None:
    for n in names:
        k = normalize_company_name(n)
        if k and k in idx:
            return idx[k]
    return None


def build_index(g: Graph) -> tuple[dict[str, str], set[str]]:
    """G₀ organization 노드의 prefLabel/altLabel/slug → slug 인덱스, 유효 slug 집합.

    키는 **런타임 필터와 같은** normalize_company_name 이다(영숫자 + 한글 보존). 라틴만 남기던
    구현은 'SK스페셜티' → 'sk' 라는 2글자 조각을 만들어, SK머티리얼즈·스페셜티·실트론을 전부
    **다른 회사** sk_keyfoundry 로 잘못 병합했다(실측 2026-07-16). 한글을 보존하면 'sk스페셜티'
    로 구별돼 각자의 올바른 노드에 붙는다. 슬러그도 같은 함수로 정규화해 영문명 매칭을 살린다.
    """
    idx: dict[str, str] = {}
    for pred in (SKOS.prefLabel, SKOS.altLabel):
        for s, _, o in g.triples((None, pred, None)):
            su = str(s)
            if "/organization/" in su:
                slug = su.rsplit("/", 1)[1]
                for key in (normalize_company_name(str(o)), normalize_company_name(slug)):
                    if key:
                        idx.setdefault(key, slug)
    valid = {str(s).rsplit("/", 1)[1] for s in g.subjects() if "/organization/" in str(s)}
    return idx, valid


def main() -> int:
    g = Graph()
    g.parse(GRAPH_V0, format="turtle")
    idx, valid_slugs = build_index(g)

    members = [
        r for r in csv.DictReader(open(KSIA_LIST, encoding="utf-8-sig"))
        if r["업체구분"] in CORPUS_TYPES
    ]

    rows, unresolved = [], []
    for r in members:
        ko, en = r["업체명(국문)"], r["업체명(영문)"]
        if ko in MANUAL:
            slug, kind = MANUAL[ko], "manual"
        else:
            slug = lookup(idx, ko, en)
            kind = "auto" if slug else None
        if not slug or slug not in valid_slugs:
            unresolved.append((r["업체구분"], ko, en))
            continue
        rows.append({
            "idx": r["idx"], "name_ko": ko, "name_en": en, "org_slug": slug,
            "match_key": normalize_company_name(ko), "match_kind": kind,
            "company_type": CORPUS_TYPES[r["업체구분"]],
        })

    # match_key 는 런타임 필터 키다 — 같은 키를 갖는 두 행은 filter_and_tag_ksia 가 구분할 수
    # 없다(dict(zip(match_key, org_slug)) 가 뒤 행으로 덮어쓴다). 그래서 크로스워크는 **match_key
    # 당 한 행**이어야 한다. 붕괴되는 것은 법인격 표기만 다른 동일 회사(엠케이프리시젼㈜/주식회사),
    # KSIA 원본의 중복 등재(원익머트리얼즈 2회), 한 회사가 두 업체구분에 걸친 경우(VAD=부분품·장비)다.
    # 결정적으로 한 행만 남기고(정렬 후 첫 행) 접힌 행을 로그한다 — §5.3 에 한계로 자인한다.
    rows.sort(key=lambda x: (x["company_type"], x["org_slug"], x["idx"]))
    seen: dict[str, dict] = {}
    collapsed: list[tuple[dict, dict]] = []
    for r in rows:
        if r["match_key"] in seen:
            collapsed.append((r, seen[r["match_key"]]))
        else:
            seen[r["match_key"]] = r
    rows = list(seen.values())

    with open(KSIA_CROSSWALK, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "idx", "name_ko", "name_en", "org_slug", "match_key", "match_kind", "company_type"])
        w.writeheader()
        w.writerows(rows)

    by_type = Counter(r["company_type"] for r in rows)
    print(f"소부장 {len(members)}사 등재 → 크로스워크 {len(rows)}행 "
          f"(auto {sum(r['match_kind'] == 'auto' for r in rows)} · "
          f"manual {sum(r['match_kind'] == 'manual' for r in rows)})")
    print(f"  층별: {dict(by_type)}")
    if unresolved:
        print(f"미해소 {len(unresolved)} (G₀ 에 organization 노드 없음):")
        for t, ko, en in unresolved:
            print(f"    [{t}] {ko}  ({en})")
    if collapsed:
        print(f"match_key 중복 접힘 {len(collapsed)} (같은 필터 키 → 한 행 유지):")
        for dropped, kept in collapsed:
            print(f"    drop [{dropped['company_type']}] {dropped['name_ko']}({dropped['org_slug']}) "
                  f"→ keep [{kept['company_type']}] {kept['name_ko']}({kept['org_slug']})")

    # match_key 는 위에서 유일하다. 서로 다른 match_key 가 같은 slug 를 가리키면 그건 서로 다른
    # 회사를 한 G₀ 노드로 잘못 병합한 것이다 — 이건 접으면 안 되고 오류로 멈춘다(SK 오매칭류).
    dup_slug = {s: c for s, c in Counter(r["org_slug"] for r in rows).items() if c > 1}
    empty_key = [r["name_ko"] for r in rows if not r["match_key"]]
    print(f"고유 org_slug: {len({r['org_slug'] for r in rows})} · "
          f"고유 match_key: {len({r['match_key'] for r in rows})} · 총 {len(rows)}행")
    if dup_slug:
        print("  🛑 서로 다른 회사가 한 G₀ 노드로 병합됨(오매칭):", dup_slug)
    if empty_key:
        print("  🛑 빈 match_key:", empty_key)
    return 1 if (dup_slug or empty_key) else 0


if __name__ == "__main__":
    raise SystemExit(main())
