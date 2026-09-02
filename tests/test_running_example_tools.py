"""PLAN-087 running-example generation and skim-path contracts."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_example_excerpt_is_derived_from_fixture():
    mod = _load("gen_example_excerpt")
    assert len(mod.required_triples()) == 9
    text = mod.render()
    assert "pat:1020130000004" in text
    assert "hasPriorArtExaminer" in text
    assert "expert/EXP_M01" in text


def test_skim_explicit_figure_reference_pattern():
    mod = _load("skim_outline")
    assert mod.FIG_REF_RE.search("이 절의 관찰 수준은 그림 3을 다시 참조한다.")
    assert not mod.FIG_REF_RE.search("그림을 별도로 두지 않는다.")
