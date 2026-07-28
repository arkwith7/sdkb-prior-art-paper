import pytest

from sdkb_paper.config import CENTRAL_AXIS_STORE, SAMPLES
from sdkb_paper.validate.cq_runner import run_cqs


def test_all_cqs_pass_on_sample():
    # 게이트 대상만 본다 — 사이드카 스토어는 gitignore(1.8GB) 라 신규 클론에 없을 수 있고,
    # mini_graph 의 델타 검증에 청구항 층은 무관하다(PLAN-023 §1).
    results = run_cqs(SAMPLES / "mini_graph.ttl", targets=("graph",))
    assert results, "CQ 파일이 없음"
    failed = [r.name for r in results if not r.passed]
    assert not failed, f"failed CQs: {failed}"


@pytest.mark.skipif(not CENTRAL_AXIS_STORE.exists(),
                    reason="사이드카 스토어 없음 (make 로 빌드 · gitignore)")
def test_sidecar_cqs_are_non_vacuous():
    """청구항 CQ 는 대상 그래프와 무관하게 사이드카를 조회한다 — 비공허가 전제다."""
    results = run_cqs(SAMPLES / "mini_graph.ttl", targets=("sidecar",))
    assert results, "사이드카 CQ 가 없다"
    assert all(r.rows > 0 for r in results), [(r.name, r.rows) for r in results]


def test_missing_sidecar_store_is_an_error(monkeypatch):
    """조용히 건너뛰면 분모가 소리 없이 바뀐다 — 그래서 에러다 (PLAN-023 §3-1)."""
    from sdkb_paper.validate import cq_runner

    monkeypatch.setattr(cq_runner, "CENTRAL_AXIS_STORE", SAMPLES / "no_such_store")
    with pytest.raises(FileNotFoundError, match="사이드카 스토어 없음"):
        run_cqs(SAMPLES / "mini_graph.ttl", targets=("sidecar",))
