"""한국어 문체 검사기의 단위 테스트 (paper/STYLE-KO-ACADEMIC.md · scripts/style_check.py).

왜 뒤늦게 쓰는가 — 이 검사기는 2026-08-12 에 **차단 모드로 승격**했고(CLAUDE.md §2.3) 그 뒤로
모든 커밋이 여기를 지난다. 그런데 검사기 자신에게는 회귀 테스트가 없어서, 정규식 하나가 조용히
매치 0 이 되어도 출력은 "통과: 2개 파일" 로 같다. **차단 게이트가 무력해진 것과 위반이 없는 것을
구분할 수 없는 상태**였다. 영문 검사기를 신설하며 같은 공백이 드러나 함께 닫는다.

규격 v2 의 아홉 라벨(S3·T2·T3·T5·T6·T7·H1·V5·V6) 을 **잡는 쪽과 놓아주는 쪽 양방향으로** 고정한다.
특히 놓아주는 쪽 셋이 중요하다 — 언급 마스킹 · `style-ok` 면제 · V5 예외 합성어. 이 셋이 깨지면
검사기는 통과 불가능해지고, 통과 불가능한 게이트는 우회된다.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


sc = _load("style_check")

HEAD = "# 1. 서론\n\n"


def _codes(msgs: list[str]) -> list[str]:
    return [m.split("] ")[0].split("[")[-1] for m in msgs]


def _run(tmp_path: Path, body: str) -> list[str]:
    p = tmp_path / "stage3_source.md"
    p.write_text(body, encoding="utf-8")
    return sc.check_file(p)


# ───────── 잡아야 할 것 ─────────
def test_s3_sentence_over_ninety_visible_chars(tmp_path):
    long = ("게이트는 동결된 코퍼스 위에서 자원 델타를 심사하고 하위집단 안전성과 교차 태스크 "
            "비회귀를 함께 확인한 다음 그 결과를 사전 지정된 판정식에 따라 승인 여부로 보고한다.")
    assert sc.visible_len(long) > sc.MAX_SENT_CHARS
    assert "S3" in _codes(_run(tmp_path, HEAD + long + "\n"))


def test_t2_colloquial_and_metaphor_verbs(tmp_path):
    fails = _run(tmp_path, HEAD + "자원을 갈아 끼운 뒤 성능이 뒷걸음친다.\n")
    assert _codes(fails).count("T2") == 2
    assert "교체" in " ".join(fails) and "저하" in " ".join(fails)


def test_t3_banned_sentence_opener(tmp_path):
    assert "T3" in _codes(_run(tmp_path, HEAD + "그래서 게이트가 델타를 거부하였다.\n"))


def test_t5_claim_sentence_in_bold(tmp_path):
    fails = _run(tmp_path, HEAD + "**게이트가 델타를 거부하였다** 라고 보고한다.\n")
    assert "T5" in _codes(fails)


def test_t6_lexical_rules_reach_table_cells(tmp_path):
    """규격 v1 은 산문만 보았고, 그래서 위반이 표 안으로 몰렸다 — T6 이 그 사각지대다."""
    body = "| 항목 | 비고 |\n|---|---|\n| 자원 | 갈아 끼운다 |\n"
    assert "T2" in _codes(_run(tmp_path, HEAD + body))


def test_t7_contraction(tmp_path):
    assert "T7" in _codes(_run(tmp_path, HEAD + "검사가 완료됐다.\n"))


def test_h1_predicative_heading(tmp_path):
    assert "H1" in _codes(_run(tmp_path, "## 3.1 게이트는 델타를 거부한다\n\n본문이다.\n"))


def test_v5_task_translation_is_single(tmp_path):
    assert "V5" in _codes(_run(tmp_path, HEAD + "세 과제를 하나의 티박스로 표현한다.\n"))


def test_v6_table_numbering_must_be_sequential(tmp_path):
    body = "**표 1. 첫 표**\n\n본문이다.\n\n**표 3. 결번**\n\n본문이다.\n"
    assert "V6" in _codes(_run(tmp_path, HEAD + body))


# ───────── 놓아주어야 할 것 ─────────
def test_mention_in_quotes_is_not_use(tmp_path):
    """§0.8 말미 — 금지 문구를 ‘쓰지 않는다’의 꼴로 인용하는 것은 위반이 아니다."""
    assert _run(tmp_path, HEAD + "금지 문구 “뒷걸음친다” 는 쓰지 않는다.\n") == []


def test_exemption_comment(tmp_path):
    assert _run(tmp_path, HEAD + "자원을 갈아 끼운다. <!-- style-ok: 사전등록 인용 -->\n") == []


def test_v5_allowed_compounds_pass(tmp_path):
    """‘후속 과제’·‘과제 기반 평가’ 는 애초에 task 의 번역이 아니다 — 잡으면 오탐이다."""
    body = "후속 과제로 남긴다. 과제 기반 평가(task-based evaluation)를 함께 쓴다.\n"
    assert _run(tmp_path, HEAD + body) == []


def test_sequential_table_numbering_passes(tmp_path):
    body = "**표 1. 첫 표**\n\n본문이다.\n\n**표 2. 둘째 표**\n\n본문이다.\n"
    assert _run(tmp_path, HEAD + body) == []


def test_clean_prose_passes(tmp_path):
    assert _run(tmp_path, HEAD + "본 연구는 릴리스 게이트를 제안한다.\n") == []


# ───────── 규격과 검사기의 정합 ─────────
def test_running_example_requires_evidence_status(tmp_path):
    body = "> **예시 1 · 예시 그래프.** 본문이다.\n"
    assert "X1" in _codes(_run(tmp_path, HEAD + body))


def test_running_example_sequence_and_synthetic_status_pass(tmp_path):
    body = (
        "> **예시 1 · 예시 그래프 · 합성 설명.** 본문이다.\n\n"
        "> **예시 2 · 델타 통과 · 합성 실행.** 본문이다.\n"
    )
    assert _run(tmp_path, HEAD + body) == []


def test_synthetic_example_heading_rejects_empirical_verdict_words(tmp_path):
    body = "> **예시 1 · 승인 거부 · 합성 실행.** 본문이다.\n"
    assert "X2" in _codes(_run(tmp_path, HEAD + body))


def test_checker_targets_exclude_the_working_manuscript():
    """대상은 투고 파생본 계열뿐이다 — 정본·supplementary 는 감사 기록이므로 소급 적용하지 않는다."""
    source = (ROOT / "scripts" / "style_check.py").read_text(encoding="utf-8")
    assert "논문_v0_9" not in source
    assert "supplementary" not in source.split("설계 메모")[0]


def test_spec_document_declares_the_labels_the_checker_emits():
    spec = (ROOT / "paper" / "STYLE-KO-ACADEMIC.md").read_text(encoding="utf-8")
    for label in ("S3", "T2", "T3", "T5", "T6", "T7", "H1", "V5", "V6"):
        assert label in spec, f"규격에 {label} 선언이 없다"
