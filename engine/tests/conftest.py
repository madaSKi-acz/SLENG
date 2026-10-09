"""
Purpose:  Shared pytest fixtures: a fake-voice engine in a temp folder and an HTTP test client.
Layer:    engine tests
Exports:  engine, client, sample_text fixtures
Depends:  pytest, fastapi.testclient, sleng
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sleng.adapters.http import create_app
from sleng.config import Settings
from sleng.container import Sleng

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def engine(tmp_path: Path) -> Iterator[Sleng]:
    sleng = Sleng(Settings(data_dir=tmp_path, fake=True))
    yield sleng
    sleng.close()


@pytest.fixture
def client(engine: Sleng) -> Iterator[TestClient]:
    with TestClient(create_app(engine)) as test_client:
        yield test_client


@pytest.fixture
def sample_text() -> str:
    return (REPO_ROOT / "data" / "sample_long.txt").read_text(encoding="utf-8")
