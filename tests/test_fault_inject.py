"""결함주입·격리 장치의 계약 (PLAN-020 W4).

여기서 지키는 명제는 셋이다.
1. **결정성** — 같은 (결함·강도·반복)은 언제나 같은 그래프를 낸다. 깨지면 매트릭스가 재현 불가다.
2. **오염 격리** — 결함 산출물은 격리 밖으로 못 나가고, 정본이 변하면 즉시 잡힌다.
3. **판정 산술** — McNemar·강도 하한·검출 요약이 조용히 관대해지지 않는다.
"""
from __future__ import annotations

import json

import pytest
from pyoxigraph import NamedNode, Quad, Store

from sdkb_paper.analysis import faults as FA
from sdkb_paper.validate import fault_inject as FI
from sdkb_paper.validate import quarantine as Q

ONT = FI.ONT
SKOS = FI.SKOS


def _toy() -> Store:
    """공정 2·하위공정 1·특허 2 의 최소 그래프. 결함 함수가 실제로 무언가를 지우는지 본다."""
    s = Store()
    def q(a, b, c):
        s.add(Quad(NamedNode(a), NamedNode(b), NamedNode(c)))
    rdft = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
    for i in (1, 2):
        q(f"{ONT}p{i}", rdft, f"{ONT}Process")
        s.add(Quad(NamedNode(f"{ONT}p{i}"), NamedNode(SKOS + "prefLabel"),
                   NamedNode(f"{ONT}label{i}")))
    q(f"{ONT}sp1", rdft, f"{ONT}SubProcess")
    q(f"{ONT}p1", f"{ONT}hasSubprocess", f"{ONT}sp1")
    for i in (1, 2):
        q(f"{ONT}doc{i}", rdft, f"{ONT}Patent")
        q(f"{ONT}doc{i}", f"{ONT}realizesProcess", f"{ONT}p{i}")
        s.add(Quad(NamedNode(f"{ONT}doc{i}"), NamedNode(f"{ONT}filingDate"),
                   NamedNode(f"{ONT}d{i}")))
    return s


# --- 1. 결정성 ---------------------------------------------------------------
def test_seed_is_stable_across_processes():
    """PYTHONHASHSEED 에 의존하면 재현이 깨진다 — sha256 고정 시드여야 한다."""
    assert FI.seed_for("F05", 0.05, 1) == FI.seed_for("F05", 0.05, 1)
    assert FI.seed_for("F05", 0.05, 1) != FI.seed_for("F05", 0.05, 2)
    assert FI.seed_for("F05", 0.05, 1) == 3609992646  # 값 자체를 못 박는다


@pytest.mark.parametrize("key", ["F02", "F05", "F06", "F12"])
def test_same_seed_same_graph(key):
    """같은 시드는 같은 결과 — 두 번 주입해 트리플 집합이 일치해야 한다."""
    def run():
        s = _toy()
        FI.BY_KEY[key].inject(s, 0.5, 7)
        return sorted(f"{q.subject} {q.predicate} {q.object}" for q in s)
    assert run() == run()


def test_strength_floor_is_one_unit():
    """모수가 작을 때 1% 가 0 이 되면 '결함 없는 결함 주입'이 된다 — 하한 1."""
    assert FI._n(0.01, 12) == 1
    assert FI._n(0.10, 38) == 4
    assert FI._n(0.05, 0) == 0        # 후보가 없으면 0 (없는 것을 만들어내지 않는다)


# --- 2. 결함이 실제로 무언가를 바꾸는가 ---------------------------------------
def test_f02_removes_required_property():
    s = _toy()
    before = len(list(s.quads_for_pattern(None, NamedNode(f"{ONT}filingDate"), None, None)))
    stats = FI.BY_KEY["F02"].inject(s, 1.0, 1)
    after = len(list(s.quads_for_pattern(None, NamedNode(f"{ONT}filingDate"), None, None)))
    assert stats["n_affected"] == before and after == 0


def test_f12_inverts_hierarchy_without_changing_edge_count():
    """계층 역전은 링크 **수**를 바꾸지 않는다 — 그래서 구조 검증이 못 잡는다(H1 의 전제)."""
    s = _toy()
    pred = NamedNode(f"{ONT}hasSubprocess")
    before = {(str(q.subject), str(q.object)) for q in s.quads_for_pattern(None, pred, None, None)}
    FI.BY_KEY["F12"].inject(s, 1.0, 1)
    after = {(str(q.subject), str(q.object)) for q in s.quads_for_pattern(None, pred, None, None)}
    assert len(before) == len(after)
    assert after == {(o, sub) for sub, o in before}


def test_f10_disguises_gold_edge_as_concept_link():
    """qrel 누출은 술어 이름 검사를 통과한다 — 그래서 '개념 자리에 문서'를 봐야 한다."""
    s = _toy()
    s.add(Quad(NamedNode(f"{ONT}doc1"), NamedNode(f"{ONT}hasPriorArtExaminer"),
               NamedNode(f"{ONT}doc2")))
    FI.BY_KEY["F10"].inject(s, 1.0, 1)
    hit = list(s.quads_for_pattern(NamedNode(f"{ONT}doc1"),
                                  NamedNode(f"{ONT}realizesProcess"),
                                  NamedNode(f"{ONT}doc2"), None))
    assert hit, "정답 간선이 개념 링크로 위장되지 않았다 — F10 이 표적을 못 만든다"


def test_normal_deltas_are_not_faults():
    """정상 델타는 결함 목록에 섞이면 안 된다 — 위양성 분모가 오염된다."""
    assert {f.key for f in FI.NORMALS}.isdisjoint({f.key for f in FI.FAULTS})
    assert all(f.expected == "none" for f in FI.NORMALS)


# --- 3. 오염 격리 ------------------------------------------------------------
def test_quarantine_path_is_always_contaminated(tmp_path, monkeypatch):
    monkeypatch.setattr(Q, "QUARANTINE", tmp_path / "quarantine")
    inside = Q.QUARANTINE / "run" / "F01" / "graph.ttl"
    assert Q.is_contaminated(inside)
    with pytest.raises(Q.ContaminationError):
        Q.assert_pristine(inside)


def test_stamp_marks_sibling_files_contaminated(tmp_path, monkeypatch):
    """격리 트리 밖이어도 오염 스탬프가 있으면 오염이다(복사해 빼돌려도 딱지가 따라간다)."""
    monkeypatch.setattr(Q, "QUARANTINE", tmp_path / "q")
    d = tmp_path / "elsewhere"
    d.mkdir()
    (d / "graph.ttl").write_text("x")
    assert not Q.is_contaminated(d / "graph.ttl")
    (d / Q.STAMP_NAME).write_text(json.dumps({"contaminated": True}))
    assert Q.is_contaminated(d / "graph.ttl")


def test_pristine_violation_is_raised_not_returned(tmp_path, monkeypatch):
    """정본이 변하면 조용히 목록만 돌려주면 안 된다 — 실험이 계속되면 오염이 번진다."""
    target = tmp_path / "graph_v0.ttl"
    target.write_text("original")
    manifest = tmp_path / "PRISTINE.json"
    monkeypatch.setattr(Q, "PRISTINE_MANIFEST", manifest)
    monkeypatch.setattr(Q.config, "ROOT", tmp_path)
    monkeypatch.setattr(Q, "protected_paths", lambda profile=None: [target])
    monkeypatch.setattr(Q, "BACKUP", tmp_path / "backup")
    Q.seal(backup=(target,))
    assert Q.verify_pristine() == []
    target.write_text("tampered")
    with pytest.raises(Q.PristineViolation):
        Q.verify_pristine(strict=True)


def test_backup_is_a_real_copy(tmp_path, monkeypatch):
    """해시만 적어두는 것은 백업이 아니다 — 복원할 실물이 있어야 한다."""
    target = tmp_path / "graph_v0.ttl"
    target.write_text("original")
    monkeypatch.setattr(Q, "PRISTINE_MANIFEST", tmp_path / "PRISTINE.json")
    monkeypatch.setattr(Q.config, "ROOT", tmp_path)
    monkeypatch.setattr(Q, "protected_paths", lambda profile=None: [target])
    monkeypatch.setattr(Q, "BACKUP", tmp_path / "backup")
    Q.seal(backup=(target,))
    assert (tmp_path / "backup" / "graph_v0.ttl").read_text() == "original"


# --- 4. 판정 산술 ------------------------------------------------------------
def test_mcnemar_counts_discordant_pairs_only():
    """일치쌍은 검정력에 기여하지 않는다 — b/c 만 센다."""
    r = FA.mcnemar([(True, True)] * 10 + [(False, True)] * 8 + [(True, False)] * 1)
    assert (r["b"], r["c"], r["n_discordant"]) == (1, 8, 9)
    assert r["test"] == "exact binomial"      # 9 < 25 → 정확검정
    assert r["p"] < 0.05


def test_mcnemar_no_discordance_is_not_significant():
    r = FA.mcnemar([(True, True)] * 20)
    assert r["p"] == 1.0 and r["n_discordant"] == 0


def test_summary_separates_false_positives_from_detection():
    """정상 델타(N*)가 결함 검출률에 섞이면 H1 판정이 오염된다."""
    def inst(key, layer, cross=False):
        return {"fault": key, "label": key, "expected": "x", "cross_task": cross,
                "strength": 0.1, "rep": 0,
                "detected": {L: (L == layer) for L in FA.LAYERS}, "first_layer": layer}
    s = FA.summarize([inst("F11", "T3", True), inst("F12", "T3", True),
                      inst("N01", None), inst("N02", "T1")])
    assert s["n_instances"] == 2                      # 정상 델타는 결함 수에서 빠진다
    assert s["h1"]["n_t3_only"] == 2
    assert s["false_positive"] == {"n_normal": 2, "n_rejected": 1, "rate": 0.5,
                                   "rejected": [{"fault": "N02", "strength": 0.1,
                                                 "layer": "T1"}]}
