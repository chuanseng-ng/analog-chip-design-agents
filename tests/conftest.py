"""Shared pytest fixtures: import the repo's standalone tool scripts as modules.

The tools (``tools/qor_trends.py``, ``tools/export_ides.py``, and the memory-keeper
``distill.py``) are run as scripts in production, not installed as a package, so the
tests load them by path via importlib and expose them as fixtures.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _load(name: str, relpath: str):
    path = REPO_ROOT / relpath
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="session")
def qor_trends():
    return _load("qor_trends", "tools/qor_trends.py")


@pytest.fixture(scope="session")
def export_ides():
    return _load("export_ides", "tools/export_ides.py")


@pytest.fixture(scope="session")
def distill():
    return _load("distill", "plugins/infrastructure/skills/memory-keeper/distill.py")


@pytest.fixture(scope="session")
def run_pipeline():
    return _load("run_pipeline", "tests/e2e/run_pipeline.py")


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES


def write_experiences(memory_dir: Path, domain: str, records: list[dict]) -> Path:
    """Write records as JSONL to ``<memory_dir>/<domain>/experiences.jsonl``."""
    import json

    d = memory_dir / domain
    d.mkdir(parents=True, exist_ok=True)
    path = d / "experiences.jsonl"
    with path.open("w") as fh:
        for rec in records:
            fh.write(json.dumps(rec) + "\n")
    return path
