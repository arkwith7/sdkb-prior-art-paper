from sdkb_paper.config import SAMPLES
from sdkb_paper.validate.cq_runner import run_cqs

def test_all_cqs_pass_on_sample():
    results = run_cqs(SAMPLES / "mini_graph.ttl")
    assert results, "CQ 파일이 없음"
    failed = [r.name for r in results if not r.passed]
    assert not failed, f"failed CQs: {failed}"
