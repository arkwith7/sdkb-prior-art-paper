"""용어 첫 등장 검사기의 단위 테스트 (paper/glossary-terms.yaml · STYLE V1·V2 · PLAN-066).

왜 이 테스트가 있는가 — A-5 에서 `verdicts.yaml` 의 키 오타(`allowed` → `composite_allowed`)를
검사기가 **한 번도 읽지 않은 채** 통과시킨 일이 있었다. 같은 일을 막기 위해 **잡아야 할 것을
잡는가**(의도적 위반 샘플 G1·G2·G4·G5)와 **잡지 말아야 할 것을 놓아주는가**(정의 선행 · 약어표 ·
백틱 언급 · 면제 주석)를 둘 다 고정한다. 실제 정본(`paper/glossary-terms.yaml`)은 읽기만 하며
스키마가 깨지면 여기서 먼저 실패한다.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


cg = _load("check_glossary")

SPEC = {
    "version": 1,
    "meta": {
        "targets": ["manuscript.md"],
        "body_start": r"^# 1\. ",
        "body_end": r"^# 참고문헌",
        "definition_form": r"{ko}\**\s*\(\s*{en}",
    },
    "terms": [
        {"id": "holdout", "category": "concept", "ko": "홀드아웃", "en": "hold-out", "define_in": "§3"},
        {"id": "mrr", "category": "standard", "ko": "평균 역순위", "en": "mean reciprocal rank",
         "abbr": "MRR", "abbr_pattern": r"MRR(@K?\d*)?", "define_in": "§4.5"},
        {"id": "suite-em", "category": "identifier", "ko": "전문가 매칭 스위트", "en": "expert-matching suite",
         "abbr": "em", "abbr_pattern": r"(?<![A-Za-z])em(?=[·,)\s])", "define_in": "§3.1"},
        {"id": "negative-control", "category": "concept", "ko": "음성 대조군", "en": "negative control",
         "synonyms_forbidden": ["음성대조군"], "define_in": "§4.4"},
        {"id": "ci", "category": "standard", "ko": "지속 통합", "en": "continuous integration", "abbr": "CI",
         "define_in": "§3",
         "forbid_patterns": [{"pattern": r"(?<![%\d]\s)(?<![%\d])CI(에서|에|의)\s", "message": "CI 다의어"}]},
    ],
}

FRONT = "# 제목\n\n## Abstract\n\nhold-out 과 MRR 이 초록에 먼저 나온다 — 기점 이전이므로 세지 않는다.\n\n"


def _codes(msgs: list[str]) -> list[str]:
    return [m.split("] ")[0].split("[")[-1] for m in msgs]


def _run(tmp_path: Path, body: str, strict_g4: bool = False):
    p = tmp_path / "manuscript.md"
    p.write_text(FRONT + body, encoding="utf-8")
    return cg.check_file(p, SPEC, strict_g4)


# ───────── 잡아야 할 것 ─────────
def test_g1_missing_definition(tmp_path):
    fails, _, rows = _run(tmp_path, "# 1. 서론\n\n홀드아웃 결함으로 판별력을 잰다.\n\n# 참고문헌\n")
    assert "G1" in _codes(fails)
    assert [r for r in rows if r["id"] == "holdout"][0]["status"] == "정의 없음"


def test_g1_definition_after_use(tmp_path):
    body = ("# 1. 서론\n\n홀드아웃 결함을 쓴다.\n\n# 3. 산출물\n\n"
            "**홀드아웃(hold-out)** 은 판정식 동결 전에 보지 않은 결함이다.\n\n# 참고문헌\n")
    fails, _, rows = _run(tmp_path, body)
    assert "G1" in _codes(fails)
    assert [r for r in rows if r["id"] == "holdout"][0]["status"] == "정의가 뒤에"


def test_g2_abbr_before_definition(tmp_path):
    body = ("# 1. 서론\n\n보조 지표는 MRR@K 이다.\n\n## 4.5 지표\n\n"
            "평균 역순위(mean reciprocal rank, MRR)를 쓴다.\n\n# 참고문헌\n")
    fails, _, _ = _run(tmp_path, body)
    assert "G2" in _codes(fails)


def test_g4_identifier_in_prose_is_warning_by_default(tmp_path):
    body = "# 1. 서론\n\n세 스위트(em·tf·core)를 관찰한다.\n\n# 참고문헌\n"
    fails, warns, _ = _run(tmp_path, body)
    assert "G4" in _codes(warns) and "G4" not in _codes(fails)
    fails_s, warns_s, _ = _run(tmp_path, body, strict_g4=True)
    assert "G4" in _codes(fails_s)


def test_g4_identifier_in_table_is_allowed(tmp_path):
    body = "# 1. 서론\n\n| 스위트 | CQ |\n|---|---|\n| em | 8 |\n\n# 참고문헌\n"
    _, warns, _ = _run(tmp_path, body)
    assert "G4" not in _codes(warns)


def test_g5_synonym_and_polysemy(tmp_path):
    body = ("# 1. 서론\n\n음성 대조군(negative control)을 둔다. 음성대조군은 30건이다. "
            "서명 검사는 CI에서 실행한다.\n\n# 참고문헌\n")
    fails, _, _ = _run(tmp_path, body)
    assert _codes(fails).count("G5") == 2


# ───────── 놓아주어야 할 것 ─────────
def test_definition_first_then_abbr_passes(tmp_path):
    body = ("# 1. 서론\n\n**홀드아웃(hold-out)** 결함을 쓴다. 이후 홀드아웃 45건이다.\n\n"
            "## 4.5 지표\n\n평균 역순위(mean reciprocal rank, MRR)를 쓴다. MRR@10 도 보고한다.\n\n# 참고문헌\n")
    fails, _, rows = _run(tmp_path, body)
    assert fails == []
    assert all(r["status"] in ("적합", "미사용") for r in rows)


def test_abstract_and_nomenclature_are_not_the_origin(tmp_path):
    body = ("## 약어표\n\n| MRR | 평균 역순위 |\n\n# 1. 서론\n\n"
            "평균 역순위(mean reciprocal rank, MRR)를 쓴다.\n\n# 참고문헌\n")
    fails, _, _ = _run(tmp_path, body)
    assert fails == []


def test_backtick_mention_is_not_use(tmp_path):
    body = "# 1. 서론\n\n파일 `cq_em.sparql` 과 `MRR` 열은 언급이다.\n\n# 참고문헌\n"
    fails, warns, _ = _run(tmp_path, body)
    assert fails == [] and warns == []


def test_exemption_comment(tmp_path):
    body = "# 1. 서론\n\n홀드아웃 결함을 쓴다. <!-- glossary-ok: §3 이관 전 임시 -->\n\n# 참고문헌\n"
    fails, _, _ = _run(tmp_path, body)
    assert fails == []


def test_bibliography_is_out_of_scope(tmp_path):
    body = "# 1. 서론\n\n본문.\n\n# 참고문헌\n\nVoorhees, E. MRR@K in TREC. 홀드아웃.\n"
    fails, _, _ = _run(tmp_path, body)
    assert fails == []


# ───────── 정본 스키마 ─────────
def test_real_spec_loads_and_terms_are_well_formed():
    spec = yaml.safe_load((ROOT / "paper" / "glossary-terms.yaml").read_text(encoding="utf-8"))
    assert spec["version"] == 1
    ids = [t["id"] for t in spec["terms"]]
    assert len(ids) == len(set(ids)), "id 중복"
    for t in spec["terms"]:
        assert t["category"] in ("concept", "standard", "identifier"), t["id"]
        assert t["ko"] and t["en"], t["id"]
        cg.Term.from_dict(t)  # 알 수 없는 키는 버리고, 필수 키가 없으면 여기서 터진다
        cg.compile_term(cg.Term.from_dict(t), spec["meta"]["definition_form"])  # 정규식이 컴파일되는가
