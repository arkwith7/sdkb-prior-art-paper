"""테스트 전역 설정 — 봉인 열람 원장은 시험 실행으로 오염되지 않는다 (PLAN-076 §9).

**왜 필요한가.** A층 접근을 원장에 남기도록 배선한 결과, `make test` 가 도는 것만으로도
`seal_access.jsonl` 이 자란다(실측: 한 번의 검증 실행에서 12행). 원장은 이제 버전관리
대상이므로 그대로 두면 **테스트가 감사 기록을 고쳐 쓰는** 셈이 되고, 판독의 기록과 배관
검사의 부산물이 한 파일에서 섞인다.

**그래서 세션 동안 원장을 임시 경로로 돌린다.** 기록 기제 자체는 이 우회로 검증되지 않는
것이 아니라, `test_seal_wiring.py` 가 **자기 임시 원장**으로 따로 검증한다 — 무엇이
기록되는지는 거기서 보고, 여기서는 실물 원장을 건드리지 않는 것만 보장한다.
**B층 봉인의 거부 기본값은 이 우회와 무관하다** — 거부는 기록 이전 단계에서 일어난다.
"""
from __future__ import annotations

import pytest

from sdkb_paper import config


@pytest.fixture(autouse=True)
def _isolate_seal_ledger(tmp_path_factory, monkeypatch):
    monkeypatch.setattr(
        config, "SEAL_ACCESS_LOG",
        tmp_path_factory.mktemp("seal") / "seal_access.jsonl")
