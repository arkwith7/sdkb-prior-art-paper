"""투고 파생본 검사기의 신설 규칙 단위 테스트 (CLAUDE.md §2.3 · D7–D9 + §0.8 SEAL·SYSTEM_LABELS).

왜 이 테스트가 있는가 — 이 셋은 **검사기를 전부 통과하던 위반**을 잡으려고 만든 규칙이다
(초록 303단어 · 키워드 10개 · 죽은 절 참조 8건). 규칙이 조용히 무력해지면 같은 일이 반복되므로,
**잡아야 할 것을 잡는가**와 **잡지 말아야 할 것을 놓아주는가**를 둘 다 고정한다.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


sc = _load("submission_check")

HEAD = "# A Task-Extensible Ontology\n\n## Abstract\n\n"


def _write(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "manuscript.md"
    p.write_text(body, encoding="utf-8")
    return p


def _codes(fails: list[str]) -> list[str]:
    return [f.split("] ")[0].split("[")[-1] for f in fails]


# ── D7 · 영문 초록 단어수 ────────────────────────────────────────────────
def test_d7_flags_overlong_abstract(tmp_path):
    body = HEAD + " ".join(["word"] * 251) + "\n"
    assert "D7" in _codes(sc.check_file(_write(tmp_path, body), tmp_path))


def test_d7_passes_at_limit_and_stops_at_keywords(tmp_path):
    # 상한 정확히 250 은 통과. Keywords 행 이후는 초록이 아니므로 세지 않는다.
    body = HEAD + " ".join(["word"] * 250) + "\n\n**Keywords:** " + " ".join(["kw"] * 99) + "\n"
    assert "D7" not in _codes(sc.check_file(_write(tmp_path, body), tmp_path))


# ── D8 · 키워드 개수 ─────────────────────────────────────────────────────
@pytest.mark.parametrize("sep", ["; ", ", "])
def test_d8_flags_too_many_keywords(tmp_path, sep):
    kws = sep.join(f"k{i}" for i in range(8))
    body = HEAD + "short abstract\n\n**Keywords:** " + kws + "\n"
    assert "D8" in _codes(sc.check_file(_write(tmp_path, body), tmp_path))


def test_d8_passes_at_limit(tmp_path):
    kws = "; ".join(f"k{i}" for i in range(7))
    body = HEAD + "short abstract\n\n**Keywords:** " + kws + "\n"
    assert "D8" not in _codes(sc.check_file(_write(tmp_path, body), tmp_path))


# ── D9 · 절 참조 도달성 ──────────────────────────────────────────────────
def test_d9_flags_reference_to_removed_section(tmp_path):
    body = HEAD + "본문\n\n# 4. 산출물\n\n## 4.5 승인 규칙\n\n승인 규칙은 §4.9 에 있다.\n"
    fails = sc.check_file(_write(tmp_path, body), tmp_path)
    assert "D9" in _codes(fails)
    assert "§4.9" in " ".join(fails)


def test_d9_accepts_live_reference(tmp_path):
    body = HEAD + "본문\n\n# 4. 산출물\n\n## 4.5 승인 규칙\n\n승인 규칙은 §4.5 에 있다.\n"
    assert "D9" not in _codes(sc.check_file(_write(tmp_path, body), tmp_path))


def test_d9_ignores_claude_md_clause_and_bibliography(tmp_path):
    """§1-2 는 규약 조항이고, 참고문헌의 § 904 는 법령 조항이다 — 둘 다 이 원고의 절이 아니다."""
    body = (
        HEAD + "본문\n\n# 4. 산출물\n\n## 4.5 승인 규칙\n\n"
        "사후 수정은 §1-2 가 금지한다.\n\n"
        "# 참고문헌\n\nUSPTO. MPEP § 904: How to search.\n"
    )
    assert "D9" not in _codes(sc.check_file(_write(tmp_path, body), tmp_path))


# ── 표 셀 치환의 수치 불변 보장 ──────────────────────────────────────────
def test_cell_fix_rejects_measurement_change(monkeypatch):
    """표 문구는 고쳐도 되지만 **수치는 못 바꾼다** — 사유 없는 수치 변경은 실패(rc 2)."""
    b3 = _load("build_submission_stage3")
    line = "| **P1** | 0.4849 | 0.4556 |"
    monkeypatch.setattr(b3, "CELL_FIXES", [("| **P1** |", "| **P1** | 0.4949 | 0.4556 |", None)])
    with pytest.raises(SystemExit) as e:
        b3.apply_cell_fixes([line])
    assert e.value.code == 2


def test_cell_fix_allows_section_renumber_without_reason(monkeypatch):
    """§4.9 → §4.5 는 재번호이지 수치 변경이 아니다 — 사유 없이 통과해야 한다."""
    b3 = _load("build_submission_stage3")
    lines = ["| **DP2** | 승인 | §4.9 설계 시점 | 2026-08-01 |"]
    monkeypatch.setattr(b3, "CELL_FIXES", [("| **DP2** |", None, None)])
    b3.apply_cell_fixes(lines)
    assert "§4.5 설계 시점" in lines[0] and "2026-08-01" in lines[0]


def test_cell_fix_fails_on_ambiguous_anchor(monkeypatch):
    b3 = _load("build_submission_stage3")
    monkeypatch.setattr(b3, "CELL_FIXES", [("| **X** |", "| **X** | new |", None)])
    with pytest.raises(SystemExit) as e:
        b3.apply_cell_fixes(["| **X** | a |", "| **X** | b |"])
    assert e.value.code == 2


# ── §0.8 문구 사전 · SEAL · SYSTEM_LABELS ────────────────────────────────
def test_verdicts_yaml_seal_and_system_label_rules_bite():
    """규칙이 yaml 에 살아 있고, 허용형/금지형을 실제로 가르는가."""
    yaml = pytest.importorskip("yaml")
    import re

    cfg = yaml.safe_load((ROOT / "paper" / "verdicts.yaml").read_text(encoding="utf-8"))
    v = cfg["verdicts"]

    seal = [re.compile(p) for p in v["SEAL"]["forbidden"]]
    seal_ex = [re.compile(p) for p in v["SEAL"]["exempt_line"]]
    bare = "이 에피소드는 봉인 분할을 1회 개봉해 두 번 수행했다."
    ledgered = "봉인 1회 개봉 — 누출 0, 그러나 열람 원장은 5행이다."
    assert any(r.search(bare) for r in seal) and not any(r.search(bare) for r in seal_ex)
    assert any(r.search(ledgered) for r in seal_ex)      # 원장을 밝히면 허용

    labels = [re.compile(p) for p in v["SYSTEM_LABELS"]["forbidden"]]
    assert any(r.search("| **P1 (주 시스템)** | 0.4849 |") for r in labels)
    assert any(r.search("**P0** Text+Ontology(사전 지정 주 시스템)") for r in labels)
    assert not any(r.search("**P1** +ClaimFeature(부차 구성)") for r in labels)
