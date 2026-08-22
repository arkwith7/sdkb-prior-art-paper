"""프로파일 분리의 회귀 계약 (PLAN-064 A-1 · SPEC-009 §3.9).

**이 파일이 지키는 것은 둘이다.** ① SDKB 프로파일은 기존 동결 리터럴과 한 값도 다르지 않다
(전사 검증) ② 다른 자원의 프로파일은 사전등록과 대조되지 않으면 로드되지 않는다.

**홀드아웃 A-Box(`ex-soda_brick.ttl`)를 열지 않는다** — 여기서 여는 순간 CQ 가 판정 대상에
맞춰졌다는 의심을 지울 수 없다. 아래 테스트는 개발 두 파일과 sha256 만 본다.
"""
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

import pytest

from sdkb_paper import config, profile as P
from sdkb_paper.validate import fault_inject as FI
from sdkb_paper.validate.cq_runner import _parse_meta, assert_disjoint, suite_predicates

HOLDOUT = "ex-soda_brick.ttl"


# --- T-1 전사 검증 ------------------------------------------------------------
def test_sdkb_profile_transcribes_frozen_constants():
    """`profiles/sdkb.yaml` 이 동결 리터럴의 전사임을 단언한다.

    프로파일 파일이 생기면 같은 값이 두 곳에 존재하게 되고 그것이 표류의 씨앗이다. yaml 오타는
    게이트 결과가 아니라 **여기서** 죽어야 한다.
    """
    p = P.load("sdkb")
    assert p.cq_suites == ("pa", "em", "tf", "core")
    assert p.l3_suites == ("pa",)
    assert p.t3_suites == ("em", "tf", "core")
    assert p.cq_targets == ("graph", "sidecar")
    assert p.cq_gate_target == "graph"
    assert p.cq_monotone == ("up", "down", "flat")
    assert p.cq_tau == 0.05 and p.cq_tau_grid == (0.0, 0.05, 0.10)
    assert p.strengths == (0.01, 0.05, 0.10)
    assert p.seed_rule == "sha256"
    assert p.has_t1_t2 is True
    assert p.namespaces["ont"] == "https://w3id.org/sdkb/ont/"
    assert p.cross_fault_predicates["F13"] == (
        "hasProcessExpertise", "hasEquipmentExperience", "hasMaterialExpertise", "hasSkill")
    assert p.cross_fault_predicates["F15"] == ("providedBy", "madeBy")


def test_config_constants_come_from_profile():
    """`config` 의 게이트 상수가 프로파일과 같은 값이어야 한다 — 파생이 끊기면 두 정본이 된다."""
    p = P.load("sdkb")
    assert config.CQ_SUITES == p.cq_suites
    assert config.L3_SUITES == p.l3_suites and config.T3_SUITES == p.t3_suites
    assert config.CQ_TAU == p.cq_tau and config.CQ_TAU_GRID == p.cq_tau_grid
    assert config.QUERIES_CQ == p.cq_dir and config.CQ_GEN_DIR == p.generation_dir


def test_profile_rejects_self_contradiction(tmp_path, monkeypatch):
    """L3 와 T3 가 겹치면 로드 시점에 죽는다 — 겹치면 T3 단독검출이 원리적으로 0 이다."""
    src = json.loads(json.dumps({}))  # noqa: F841  (yaml 을 손으로 만든다)
    bad = (P.PROFILES_DIR / "sdkb.yaml").read_text(encoding="utf-8").replace(
        "l3_suites: [pa]", "l3_suites: [pa, em]")
    f = tmp_path / "bad.yaml"
    f.write_text(bad, encoding="utf-8")
    monkeypatch.setattr(P, "PROFILES_DIR", tmp_path)
    P._CACHE.clear()
    with pytest.raises(P.ProfileError, match="겹친다"):
        P.load("bad")
    P._CACHE.clear()


# --- T-2 사전등록 핀 ----------------------------------------------------------
def test_brick_profile_pins_are_verified():
    """동결 자원의 sha256 이 디스크 실물과 일치해야 로드된다."""
    p = P.load("brick")
    rec = P.verify_prereg(p)
    assert rec["ok"] and rec["checked"] == 25      # T-Box 6 · A-Box 3 · CQ 15 · shape 1
    assert p.prereg["document"].endswith("PLAN-064-prereg.md")


def test_prereg_mismatch_is_an_error_not_a_warning(tmp_path, monkeypatch):
    """핀이 어긋나면 판정을 시작하지 않는다 — 동결 밖 자원 위의 판정은 사전등록 무효다."""
    txt = (P.PROFILES_DIR / "brick.yaml").read_text(encoding="utf-8")
    broken = txt.replace('"queries/brick/shapes/delta.ttl": "',
                         '"queries/brick/shapes/delta.ttl": "0000', 1)
    (tmp_path / "b2.yaml").write_text(broken, encoding="utf-8")
    monkeypatch.setattr(P, "PROFILES_DIR", tmp_path)
    P._CACHE.clear()
    with pytest.raises(P.PreregMismatch):
        P.load("b2")
    P._CACHE.clear()


# --- T-3 CQ 파싱 --------------------------------------------------------------
def test_brick_cqs_parse_and_shared_header_is_read():
    """Brick CQ 15개가 파싱되고 `# shared: true` 가 버려지지 않는다."""
    p = P.load("brick")
    rqs = sorted(p.cq_dir.glob("*.rq"))
    assert len(rqs) == 15
    shared = 0
    for rq in rqs:
        _d, expect_min, suite, mono, target, extras = _parse_meta(rq.read_text("utf-8"), p)
        assert suite in p.cq_suites and mono in p.cq_monotone and target == "graph"
        assert expect_min == 1                      # 사전등록 §3 — 전량 1 로 동결
        if extras.get("shared") == "true":
            shared += 1
            assert suite == "core"                  # 공유 표기는 core 스위트에만 붙는다
    assert shared == 5


# --- T-4 술어 추출과 교집합 ----------------------------------------------------
def test_suite_predicates_match_prereg_table_and_are_nonempty():
    """사전등록 §4.1 표를 **단일 파서**가 재현하고, 교집합 검사가 공허하지 않다."""
    p = P.load("brick")
    got = {k: sorted(v) for k, v in suite_predicates(profile=p).items()}
    cal = json.loads(config.BRICK_CALIBRATION.read_text(encoding="utf-8"))
    assert got == {k: sorted(v) for k, v in cal["suite_predicates"].items()}
    rec = assert_disjoint("fdd", "space", profile=p)
    # **핵심** — 두 집합이 비어 있지 않아야 서로소가 의미를 갖는다.
    assert rec["n_a"] > 0 and rec["n_b"] > 0


def test_empty_extraction_fails_loudly(tmp_path):
    """접두어가 어긋나 술어를 하나도 못 세면 '통과'가 아니라 오류다.

    **이것이 이 작업에서 가장 중요한 회귀 계약이다.** 구 구현에서는 이 상황이 예외가 아니라
    `fdd ∩ space = ∅` 라는 **초록불**로 나왔다 — 빈 집합끼리의 교집합은 언제나 공집합이기
    때문이다. 스위트 라벨은 프로파일에 맞고 어휘만 낯선 CQ 로 그 상황을 정확히 재현한다.
    """
    for suite in ("pa", "em"):
        (tmp_path / f"{suite}.rq").write_text(
            f"# desc: 낯선 어휘\n# suite: {suite}\n# monotone: up\n# expect-min: 1\n"
            "PREFIX brick: <https://brickschema.org/schema/Brick#>\n"
            "SELECT ?s WHERE {{ ?s brick:hasPoint ?o }}\n", encoding="utf-8")
    p = P.load("sdkb")
    assert suite_predicates(tmp_path, p) == {"pa": set(), "em": set()}   # 구 구현의 초록불 자리
    with pytest.raises(ValueError, match="추출이 비었다"):
        assert_disjoint("pa", "em", cq_dir=tmp_path, profile=p)


# --- T-5 개발 행 수 -----------------------------------------------------------
def test_brick_dev_rows_match_calibration():
    """개발 A-Box 의 CQ 행 수가 보정 기록과 같다 — 코드와 기록이 갈라지면 사전등록이 흔들린다."""
    rdflib = pytest.importorskip("rdflib")
    p = P.load("brick")
    d0 = config.EXTERNAL_BRICK / "Brick-v1.3.0.ttl"
    if not d0.exists():
        pytest.skip("Brick T-Box 는 gitignore 다 — 재생성 후에만 돈다")
    g = rdflib.Graph()
    g.parse(d0, format="turtle")
    for a in ("ex-rice_brick.ttl", "ex-g36-combined-ahu-vav.ttl"):
        assert a != HOLDOUT
        g.parse(config.EXTERNAL_BRICK / a, format="turtle")
    cal = json.loads(config.BRICK_CALIBRATION.read_text(encoding="utf-8"))
    assert len(g) == cal["graph_triples"]
    for rq in sorted(p.cq_dir.glob("*.rq")):
        assert len(list(g.query(rq.read_text("utf-8")))) == cal["cq"][rq.name]["rows"], rq.name


# --- T-6 결정성 ---------------------------------------------------------------
def _canon(store) -> tuple[str, int]:
    """공백노드 **불변** 정준 해시.

    직렬화 바이트도 트리플 집합도 실행마다 다르다 — 적재가 공백노드에 새 라벨을 주기 때문이다
    (실측 2026-08-22). 결함 조작이 바꾸는 것은 전부 명명 노드 사이의 간선이므로, 공백노드를
    담은 트리플은 개수만 세고 나머지를 정렬해 해시하면 조작에 민감하면서 재현 가능하다.
    """
    named, n_b = [], 0
    for q in store:
        terms = (str(q.subject), str(q.predicate), str(q.object))
        if any(t.startswith("_:") for t in terms):
            n_b += 1
            continue
        named.append("\t".join(terms))
    named.sort()
    return hashlib.sha256("\n".join(named).encode()).hexdigest(), n_b


def test_seed_rules_are_profile_values():
    """SDKB 는 sha256, EP5 는 사전등록 §4.2 의 선형식 — 규칙 자체가 프로파일 값이다."""
    assert FI.seed_for("F11", 0.05, 0) == FI.seed_for("F11", 0.05, 0, P.load("sdkb"))
    b = P.load("brick")
    assert b.seed_for("X2", 0.05, 1) == 20260822 + 200 + 1
    assert b.seed_for("X3", 1, 1) == 20260822 + 300 + 1
    # **강도가 식에 없다** — 같은 (결함·반복)의 세 강도는 같은 시드를 공유한다(사전등록 그대로).
    assert b.seed_for("X4", 0.05, 2) == b.seed_for("X4", 0.20, 2)


def test_sdkb_fault_injection_is_deterministic():
    """같은 (결함·강도·반복)은 언제 돌려도 같은 그래프 — 매트릭스 재현의 전제(F16)."""
    if not config.GRAPH_V0.exists():
        pytest.skip("graph_v0 는 gitignore 다 — `make baseline` 후에만 돈다")

    def run():
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            store = FI.load(config.GRAPH_V0, ws)
            FI.BY_KEY["F12"].inject(store, 0.05, FI.seed_for("F12", 0.05, 0))
            return _canon(store)

    assert run() == run()


# --- T-7 부분 판정 스키마 ------------------------------------------------------
def test_partial_acceptance_is_not_acceptance():
    """`accept` 는 null 이고 `Accept_partial` 은 별도 키다 — 부분 승인을 승인이라 부르지 않는다."""
    from sdkb_paper.validate.t_gate import accept, accept_partial

    assert accept_partial(True, True) is True
    assert accept_partial(True, False) is False
    # 승인식은 그대로다 — T1·T2 를 참으로 채워 승인을 만들지 않는다.
    assert accept(True, True, True, True) is True
    assert accept(True, False, True, True) is False


def test_t3only_refuses_profiles_that_have_t1_t2():
    """T1·T2 가 있는 자원에서 부분 판정을 내는 것은 우회로다 — 막는다."""
    from sdkb_paper.validate.t_gate import run_t3only

    with pytest.raises(ValueError, match="t3only"):
        run_t3only(config.GRAPH_V0, profile=P.load("sdkb"))
