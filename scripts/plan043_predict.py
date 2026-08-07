"""PLAN-043 §3 — CR-013 검증기준 ③④⑤ 의 예측값을 **결과 보기 전에** 재산출한다.

왜 필요한가. 하류가 CR-013 §6 에 적은 ⑤(고유 (doc,concept) 쌍 106,496 → 105,293)는
ⓑ 를 **순수 제거**로 가정한 값이다. 상류 회신(§2·§4)은 `high k` 를 제거가 아니라
`material:dielectric` 으로 **재지정**했으므로 그 예측은 무효다. 재지정판으로 다시 계산한다.

모의 적용은 **현 자산 위에서만** 돈다 — 새 사전을 읽지 않는다. 두 줄의 변경을
`concept_links.parquet`(적용기 산출)과 코퍼스 `concepts` 열(그래프 ∪ 적용기)에 각각 반영한다.

  ⓐ 단독 표면형 `hf` → `material:hf_acid` 행 **제거**
  ⓑ 표면형 `high k` 행의 개념을 `material:hfO2` → `material:dielectric` **재지정**
  ⓒ A-Box `involvesMaterial → hf_acid` 링크 34 → 15 (상류 실측 · 회신 §3)

산출: data/profiles/plan043_prediction.md (커밋). 실행:
    uv run python scripts/plan043_predict.py
"""
from __future__ import annotations

import pathlib

import pandas as pd
from pyoxigraph import RdfFormat, Store

from sdkb_paper import config

SDKB_HOME = pathlib.Path.home() / "Dev" / "sdkb"
OUT = config.ROOT / "data" / "profiles" / "plan043_prediction.md"

CONCEPT_PROPS = ["realizesProcess", "involvesProcess", "concernsDevice",
                 "involvesMaterial", "concernsSkill", "exhibitsFailureMode"]
MAT = "https://w3id.org/sdkb/data/material/"
ONT = "https://w3id.org/sdkb/ont/"


def _graph_docs(paths: list[pathlib.Path], slug: str) -> set[str]:
    store = Store()
    for p in paths:
        with open(p, "rb") as fh:
            store.bulk_load(fh, format=RdfFormat.TURTLE)
    out: set[str] = set()
    for prop in CONCEPT_PROPS:
        q = f"SELECT ?p WHERE {{ ?p <{ONT}{prop}> <{MAT}{slug}> }}"
        out |= {r["p"].value.rsplit("/", 1)[-1] for r in store.query(q)}
    return out


def main() -> None:
    links = pd.read_parquet(config.IR_CONCEPT_LINKS)
    corpus = pd.read_parquet(config.IR_CORPUS, columns=["doc_id", "concepts"])
    ids = set(corpus.doc_id)

    # --- ① 적용기 층 (검증기준 ③④⑤) ---------------------------------------
    base_pairs = len(links[["doc_id", "concept_id"]].drop_duplicates())

    new = links[~((links.surface == "hf") & (links.concept_id == "material:hf_acid"))].copy()
    hk = (new.surface == "high k") & (new.concept_id == "material:hfO2")
    new.loc[hk, ["concept_id", "slug", "rule_id", "confidence", "ambiguous"]] = [
        "material:dielectric", "dielectric", "T2-ALIAS-REASSIGN", 0.8, False]
    new_pairs = len(new[["doc_id", "concept_id"]].drop_duplicates())

    def d(cid: str) -> int:
        return links[links.concept_id == cid].doc_id.nunique()

    def a(cid: str) -> int:
        return new[new.concept_id == cid].doc_id.nunique()

    # 순수 제거판(무효가 된 구 예측)의 재현 — 방법이 같은지 확인하는 대조
    pure = links[~(
        ((links.surface == "hf") & (links.concept_id == "material:hf_acid"))
        | ((links.surface == "high k") & (links.concept_id == "material:hfO2")))]
    pure_pairs = len(pure[["doc_id", "concept_id"]].drop_duplicates())

    hk_docs = set(links[links.surface == "high k"].doc_id)
    had_diel = set(links[links.concept_id == "material:dielectric"].doc_id)
    hfo2_other = set(links[(links.concept_id == "material:hfO2")
                           & (links.surface != "high k")].doc_id)
    hf_docs = set(links[links.surface == "hf"].doc_id)
    acid_other = set(links[(links.concept_id == "material:hf_acid")
                           & (links.surface != "hf")].doc_id)

    # --- ② 코퍼스 union 층 (그래프 ∪ 적용기) --------------------------------
    old_ttl = [config.EXTERNAL_SDKB / "sdkb-abox-patents.ttl",
               config.EXTERNAL_SDKB / "sdkb-abox-prior-art.ttl",
               config.EXTERNAL_SDKB / "sdkb-core-data.ttl"]
    new_ttl = [SDKB_HOME / "ontology" / "sdkb-abox-patents.ttl",
               SDKB_HOME / "ontology" / "sdkb-abox-prior-art.ttl"]
    g_hf = _graph_docs(old_ttl, "hf_acid") & ids
    g_hfo2 = _graph_docs(old_ttl, "hfO2") & ids
    g_diel = _graph_docs(old_ttl, "dielectric") & ids
    g_hf_new = _graph_docs(new_ttl, "hf_acid") & ids

    union_pairs = int(sum(len(c) for c in corpus.concepts if c is not None))
    u_before = {
        "hf_acid": len(set(links[links.concept_id == "material:hf_acid"].doc_id) | g_hf),
        "hfO2": len(set(links[links.concept_id == "material:hfO2"].doc_id) | g_hfo2),
        "dielectric": len(had_diel | g_diel),
    }
    u_after = {
        "hf_acid": len(set(new[new.concept_id == "material:hf_acid"].doc_id) | g_hf_new),
        "hfO2": len(set(new[new.concept_id == "material:hfO2"].doc_id) | g_hfo2),
        "dielectric": len(set(new[new.concept_id == "material:dielectric"].doc_id) | g_diel),
    }
    union_after = union_pairs + sum(u_after[k] - u_before[k] for k in u_before)

    L = [
        "# PLAN-043 예측값 — CR-013 재지정판 (결과 보기 전 산출)",
        "",
        f"생성: `scripts/plan043_predict.py` · 입력 `{config.IR_CONCEPT_LINKS.name}`"
        f"(행 {len(links):,}) · `{config.IR_CORPUS.name}`(행 {len(corpus):,})",
        "",
        "## 1. 적용기 층 — 검증기준 ③④⑤",
        "",
        "| # | 기준 | 전 | **후(예측)** | 델타 |",
        "|---|---|---:|---:|---:|",
        f"| ③ | `material:hf_acid` 문서 | {d('material:hf_acid'):,} | "
        f"**{a('material:hf_acid'):,}** | {a('material:hf_acid') - d('material:hf_acid'):,} |",
        f"| ④ | `material:hfO2` 문서 | {d('material:hfO2'):,} | "
        f"**{a('material:hfO2'):,}** | {a('material:hfO2') - d('material:hfO2'):,} |",
        f"| ⑤ | 고유 (doc,concept) 쌍 | {base_pairs:,} | **{new_pairs:,}** | "
        f"{new_pairs - base_pairs:,} |",
        f"| — | `material:dielectric` 문서 | {d('material:dielectric'):,} | "
        f"**{a('material:dielectric'):,}** | {a('material:dielectric') - d('material:dielectric'):,} |",
        f"| — | 적용기 링크 행 | {len(links):,} | **{len(new):,}** | {len(new) - len(links):,} |",
        "",
        "### 1.1 ⑤ 의 분해 — 세 항이 전부다",
        "",
        f"- 단독 `hf` 로만 `hf_acid` 를 얻던 문서 **−{len(hf_docs - acid_other):,}** "
        f"(표면형 `hf` 문서 {len(hf_docs):,} 중 {len(hf_docs & acid_other):,} 는 "
        "`불산`·`hydrofluoric acid` 로 유지)",
        f"- `high k` 로만 `hfO2` 를 얻던 문서 **−{len(hk_docs - hfo2_other):,}** "
        f"(`high k` 문서 {len(hk_docs):,} 중 {len(hk_docs & hfo2_other):,} 는 "
        "`hfo2`·`hafnium oxide` 로 유지)",
        f"- `high k` 로 `dielectric` 을 **새로 얻는** 문서 **+{len(hk_docs - had_diel):,}** "
        f"({len(hk_docs & had_diel):,} 는 이미 보유)",
        f"- 합 **{new_pairs - base_pairs:,}** → **{new_pairs:,}**",
        "",
        "### 1.2 무효가 된 구 예측의 재현 (방법 동일성 확인)",
        "",
        f"`high k` 를 **재지정 없이 제거**하면 {base_pairs:,} → **{pure_pairs:,}** "
        f"({pure_pairs - base_pairs:,}). CR-013 §6 이 적은 105,293 과 일치하므로, "
        "달라진 것은 모의 적용의 방법이 아니라 **상류가 고른 ⓑ 의 형태**다.",
        "",
        "## 2. 코퍼스 union 층 — 그래프 ∪ 적용기 (`concepts` 열)",
        "",
        "코퍼스의 `concepts` 는 A-Box 그래프 링크와 적용기 링크의 **합집합**이다"
        "(`concept_link.apply_to_corpus:132`). 그래서 ⑤ 와 다른 수이며, 상류 A-Box 정리"
        "(회신 §3 · 링크 34 → 15)가 여기에만 나타난다.",
        "",
        "| 개념 | union 문서 전 | **후(예측)** | 그래프 링크 문서 |",
        "|---|---:|---:|---:|",
        f"| `hf_acid` | {u_before['hf_acid']:,} | **{u_after['hf_acid']:,}** | "
        f"{len(g_hf):,} → {len(g_hf_new):,} |",
        f"| `hfO2` | {u_before['hfO2']:,} | **{u_after['hfO2']:,}** | {len(g_hfo2):,} (불변) |",
        f"| `dielectric` | {u_before['dielectric']:,} | **{u_after['dielectric']:,}** | "
        f"{len(g_diel):,} (불변) |",
        "",
        f"**코퍼스 union (doc,concept) 쌍 {union_pairs:,} → 예측 {union_after:,}** "
        f"({union_after - union_pairs:,}).",
        "",
        "> `hf_acid` 의 union 이 ③ 의 적용기 값보다 큰 이유는 상류가 남긴 A-Box 링크 "
        f"{len(g_hf_new)} 건 중 {len(g_hf_new - set(new[new.concept_id == 'material:hf_acid'].doc_id))} "
        "건이 적용기 사후 집합 밖에 있기 때문이다. 어느 쪽도 오류가 아니다 — 잣대가 둘이다.",
        "",
        "## 3. 이 파일의 지위",
        "",
        "**결과를 보기 전에 적은 예측이다.** 재조립이 이 값과 어긋나면 상류가 회신문 "
        "이외의 것도 바꾼 것이므로 그 자리에서 멈추고 원인을 묻는다(CR-013 §6).",
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    print(f"\n✓ {OUT}")


if __name__ == "__main__":
    main()
