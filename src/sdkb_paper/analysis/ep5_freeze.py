"""EP5 기준 세대 D₀ 동결 — **이 실행이 홀드아웃 A-Box 를 처음 연다** (PLAN-064 A-4).

D₀ = Brick v1.3.0 T-Box + `ex-soda_brick.ttl`(홀드아웃 3,774 트리플). 이후의 모든 T3 판정은
이 세대 대비 회귀로 정의되므로, 동결 없이 도는 결함 판정은 기준선이 없는 판정이다.

**사전등록 §3 의 D₀ 와 이름이 같지만 다른 그래프다** — 그쪽은 개발 A-Box 위의 보정용
(53,871 트리플)이고 이쪽은 판정용이다(SPEC-010 §6.5). 산출물에는 A-Box 목록을 함께 남긴다.
"""
from __future__ import annotations

import json

from sdkb_paper import config
from sdkb_paper import profile as _profile
from sdkb_paper.ontology import ep5_graphs as EG
from sdkb_paper.validate import quarantine as Q
from sdkb_paper.validate.t3_cross_task_cq import freeze_generation, generation_path


def main() -> int:
    prof = _profile.load("brick")            # sha256 동결 대조가 여기서 강제된다
    gp = config.PROCESSED / "ep5" / "d0.ttl"
    gp.parent.mkdir(parents=True, exist_ok=True)
    g = EG.assemble("d0", EG.HOLDOUT_ABOX)
    g.serialize(gp, format="turtle")
    # 봉인은 판정 이전에 건다 — 결함주입이 정본을 오염시키는 사고를 막는 유일한 장치다.
    # 백업은 뜨지 않는다(Brick TTL 은 공개 릴리스에서 재생성 가능하며 sha256 이 동결돼 있다).
    sealed = Q.seal(backup=(), profile=prof)
    rec = freeze_generation(gp, "d0", against=None, profile=prof)
    out = generation_path("d0", prof)
    print(f"[ep5-freeze] D₀ = Brick v1.3.0 + {list(EG.HOLDOUT_ABOX)} → {len(g):,} 트리플")
    print(f"             세대 아티팩트 {out.relative_to(config.ROOT)}")
    print(f"             봉인 {sealed['n_files']}건 → {Q.manifest_path(prof).name}")
    print(f"             스위트 {json.dumps(rec['suites'], ensure_ascii=False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
