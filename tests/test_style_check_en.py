"""영문 문체 검사기의 단위 테스트 (paper/STYLE-EN-ACADEMIC.md · scripts/style_check_en.py).

왜 이 테스트가 있는가 — 이 검사기는 **정규식 표 셋**(T7 구어·은유 · V 판정 강도 · T8 철자)으로
서 있고, 그 표의 오탐·누락은 조용하다. 위반이 0 으로 보이는 통과와 패턴이 한 번도 매치되지
않아 0 인 통과는 출력이 같다. `verdicts.yaml` 의 키 오타를 검사기가 한 번도 읽지 않은 채
통과시킨 일(PLAN-064 A-5)이 같은 종류의 사고였다.

그래서 셋을 고정한다 — **잡아야 할 것을 잡는가**(규격 §8 의 열한 라벨 전부) · **놓아주어야 할
것을 놓아주는가**(언급 마스킹 · 표 · 코드 펜스 · 참고문헌 · 면제 주석) · **경고와 위반의 구분이
유지되는가**(T1·T4·T8 은 경고여야 하며 차단 승격 시 갑자기 실패로 바뀌면 안 된다).
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


sce = _load("style_check_en")

HEAD = "# 1. Introduction\n\n"


def _codes(msgs: list[str]) -> list[str]:
    return [m.split("] ")[0].split("[")[-1] for m in msgs]


def _run(tmp_path: Path, body: str) -> tuple[list[str], list[str]]:
    p = tmp_path / "en_source.md"
    p.write_text(body, encoding="utf-8")
    fails: list[str] = []
    warns: list[str] = []
    sce.check_file(p, fails, warns)
    return fails, warns


# ───────── 잡아야 할 것 — 규격 §8 의 위반 라벨 ─────────
def test_s3_sentence_over_thirty_words(tmp_path):
    long = ("We evaluate the release gate on a frozen corpus and report the outcome for every "
            "subgroup and for every competency question suite before the sealed relevance "
            "judgments are opened exactly once.")
    fails, _ = _run(tmp_path, HEAD + long + "\n")
    assert "S3" in _codes(fails)
    assert len(re.findall(r"[A-Za-z][A-Za-z'’\-]*", long)) > sce.MAX_SENT_WORDS


def test_t3_impersonal_passive(tmp_path):
    fails, _ = _run(tmp_path, HEAD + "It was found that the gate rejected the delta.\n")
    assert "T3" in _codes(fails)


def test_t6_intensifier(tmp_path):
    fails, _ = _run(tmp_path, HEAD + "The result is clearly stronger.\n")
    assert "T6" in _codes(fails)


def test_t6_significant_without_statistical_context(tmp_path):
    """‘significantly’ 는 통계 맥락이 없을 때만 위반이다 — 있으면 정상 보고다."""
    bad, _ = _run(tmp_path, HEAD + "The ontology arm was significantly better.\n")
    assert "T6" in _codes(bad)
    ok, _ = _run(tmp_path, HEAD + "The ontology arm was significantly better (p = 0.01).\n")
    assert ok == []


def test_t7_banned_lexicon(tmp_path):
    fails, _ = _run(tmp_path, HEAD + "We swap in the new resource bundle.\n")
    assert "T7" in _codes(fails)
    assert "substitute" in fails[0]


def test_t9_contraction(tmp_path):
    fails, _ = _run(tmp_path, HEAD + "We don't report that number.\n")
    assert "T9" in _codes(fails)


def test_v_verdict_strength(tmp_path):
    """§4 금지열 — `verdicts.yaml` 이 한국어만 보므로 영문은 이 표가 유일한 방어선이다."""
    fails, _ = _run(tmp_path, HEAD + "The check received partial support from the data.\n")
    assert "V" in _codes(fails)
    fails2, _ = _run(tmp_path, HEAD + "The finding did not transfer to the generation layer.\n")
    assert "V" in _codes(fails2)


def test_h1_finite_and_interrogative_headings(tmp_path):
    fails, _ = _run(tmp_path, "## 3.1 The gate is discriminative\n\nBody text here.\n")
    assert "H1" in _codes(fails)
    fails_q, _ = _run(tmp_path, "## 3.1 What does the gate detect?\n\nBody text here.\n")
    assert "H1" in _codes(fails_q)


def test_t5_claim_sentence_in_bold(tmp_path):
    fails, _ = _run(tmp_path, HEAD + "**The gate is discriminative** and we report it.\n")
    assert "T5" in _codes(fails)


# ───────── 경고여야 하는 것 — 차단으로 새지 않는가 ─────────
def test_t8_british_spelling_is_warning_only(tmp_path):
    fails, warns = _run(tmp_path, HEAD + "We recorded the judgement of the examiner.\n")
    assert "T8" in _codes(warns) and fails == []


def test_t1_this_study_repetition_is_warning_only(tmp_path):
    body = "This study reports the gate. The present study also reports the transfer check.\n"
    fails, warns = _run(tmp_path, HEAD + body)
    assert "T1" in _codes(warns) and "T1" not in _codes(fails)


def test_t4_of_chain_is_warning_only(tmp_path):
    body = "We report the effect of the substitution of the bundle of concepts here.\n"
    fails, warns = _run(tmp_path, HEAD + body)
    assert "T4" in _codes(warns) and "T4" not in _codes(fails)


# ───────── 놓아주어야 할 것 ─────────
def test_backtick_and_quote_mentions_are_not_use(tmp_path):
    """언급은 사용이 아니다 — 금지어를 ‘쓰지 않는다’고 적는 문장까지 잡으면 규격을 못 쓴다."""
    fails, _ = _run(tmp_path, HEAD + "The column `haystack` is a name, and we avoid "
                                     "the phrase \"partial support\" in prose.\n")
    assert fails == []


def test_table_rows_escape_length_and_bold_rules(tmp_path):
    body = "| Metric | Note |\n|---|---|\n| Recall | **The gate is fine** |\n"
    fails, _ = _run(tmp_path, HEAD + body)
    assert "S3" not in _codes(fails) and "T5" not in _codes(fails)


def test_table_rows_still_get_lexical_rules(tmp_path):
    """표는 길이·볼드에서만 면제된다 — 어휘 규칙까지 면제하면 v1 의 사각지대가 재발한다."""
    body = "| Step | Note |\n|---|---|\n| Resource | We swap in the bundle |\n"
    fails, _ = _run(tmp_path, HEAD + body)
    assert "T7" in _codes(fails)


def test_code_fence_is_out_of_scope(tmp_path):
    fails, _ = _run(tmp_path, HEAD + "```\nWe don't lint code blocks here at all.\n```\n")
    assert fails == []


def test_bibliography_is_out_of_scope(tmp_path):
    body = "Body text.\n\n# References\n\nSmith, J. We don't count this sentence.\n"
    fails, _ = _run(tmp_path, HEAD + body)
    assert fails == []


def test_exemption_comment_on_line_and_on_paragraph(tmp_path):
    inline, _ = _run(tmp_path, HEAD + "We swap in the bundle. <!-- style-ok: quoted -->\n")
    assert inline == []
    block, _ = _run(tmp_path, HEAD + "<!-- style-ok: legacy -->\nWe swap in the bundle.\n")
    assert block == []


def test_clean_prose_passes(tmp_path):
    fails, warns = _run(tmp_path, HEAD + "We evaluate the gate on a frozen corpus.\n")
    assert fails == [] and warns == []


# ───────── Highlights (J) ─────────
def test_j_highlights_count_and_length(tmp_path):
    p = tmp_path / "highlights.md"

    p.write_text("# Highlights\n\n- one\n- two\n", encoding="utf-8")
    few: list[str] = []
    sce.check_highlights(p, few)
    assert "J" in _codes(few)

    p.write_text("# Highlights\n\n- a\n- b\n- c\n- " + "x" * 90 + "\n", encoding="utf-8")
    long: list[str] = []
    sce.check_highlights(p, long)
    assert "J" in _codes(long)

    p.write_text("# Highlights\n\n- alpha\n- beta\n- gamma\n", encoding="utf-8")
    ok: list[str] = []
    sce.check_highlights(p, ok)
    assert ok == []


# ───────── 규격과 검사기의 정합 ─────────
def test_every_pattern_table_compiles():
    """표가 커지면 오타 난 정규식 하나가 조용히 매치 0 이 된다 — 컴파일을 강제한다."""
    for table in (sce.BANNED_LEXICON, sce.VERDICT_FORBIDDEN_EN):
        assert table, "패턴 표가 비어 있다"
        for pattern, hint in table:
            re.compile(pattern)
            assert hint.strip(), pattern


def test_spec_document_declares_the_labels_the_checker_emits():
    """규격 §8 이 선언한 라벨과 검사기가 실제로 내는 라벨이 갈리면 통과가 근거가 되지 못한다."""
    spec = (ROOT / "paper" / "STYLE-EN-ACADEMIC.md").read_text(encoding="utf-8")
    section8 = spec.split("## 8.")[1].split("## 9.")[0]
    for label in ("S3", "T1", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "H1", "V", "J"):
        assert re.search(rf"\b{label}\b", section8), f"규격 §8 에 {label} 선언이 없다"
