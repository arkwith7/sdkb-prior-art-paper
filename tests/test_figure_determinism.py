"""그림 SVG 의 바이트 결정성 회귀 테스트 (viz/figures._save).

**왜 필요한가.** matplotlib 은 기본값에서 `clipPath`·마커 id 를 실행마다 새 uuid salt 로
뽑고, 저장 시각을 `<dc:date>` 에 박는다. 그러면 좌표가 한 픽셀도 안 바뀐 재실행에서도
SVG 가 달라져 `git status` 가 "그림이 바뀌었다"고 거짓 보고한다 — 재현성 주장과 정면으로
부딪힌다. `figures.py` 는 `svg.hashsalt` 고정 + `metadata={"Date": None}` 로 이를 막는다.
이 테스트는 **그 두 방벽이 사라지면 실패한다.**

같은 프로세스 안의 2회 저장만 비교하지 않는다 — salt 가 uuid 로 돌아가도 한 프로세스
안에서는 같은 값이 유지되므로 회귀를 놓친다. 그래서 **별도 프로세스 2회**를 돌려 비교한다.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# 자식 프로세스에서 그림 하나를 그려 저장한다. figures 모듈을 import 하는 것이 요점 —
# salt 고정·메타데이터 제거가 그 import 의 부수효과이기 때문이다.
_CHILD = """
import sys
import matplotlib.pyplot as plt
from sdkb_paper.viz import figures

fig, ax = plt.subplots(figsize=(4, 3))
ax.plot([0, 1, 2], [0.1, 0.7, 0.4], marker="o")   # clipPath + 마커 id 를 만든다
ax.set_title("결정성")                              # 한글 글리프(path)도 포함
figures._save(fig, __import__("pathlib").Path(sys.argv[1]))
"""


def _render(out: Path) -> bytes:
    proc = subprocess.run(
        [sys.executable, "-c", _CHILD, str(out)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return out.read_bytes()


def test_svg_is_byte_identical_across_processes(tmp_path):
    first = _render(tmp_path / "a.svg")
    second = _render(tmp_path / "b.svg")
    assert first == second, "SVG 가 실행마다 달라진다 — svg.hashsalt 고정이 풀렸는지 확인"


def test_svg_carries_no_timestamp(tmp_path):
    svg = _render(tmp_path / "a.svg").decode("utf8")
    assert "dc:date" not in svg, "저장 시각이 박혔다 — _save 의 metadata={'Date': None} 확인"
