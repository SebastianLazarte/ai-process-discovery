"""Integration fixtures.

The suite runs against SQLite by default. When DATABASE_URL is set (the `test-postgres`
CI job), the very same tests run against PostgreSQL.
"""

import os
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.db import build_engine
from app.llm.provider import LLMProvider
from app.llm.providers.fake import FakeLLMProvider
from app.main import create_app
from app.models.persistence import Base


@pytest.fixture
def database_url(tmp_path: Path) -> Iterator[str]:
    url = os.environ.get("DATABASE_URL") or f"sqlite:///{tmp_path / 'test.sqlite'}"
    engine = build_engine(url)
    Base.metadata.drop_all(engine)
    engine.dispose()
    yield url


@pytest.fixture
def make_client(database_url: str) -> Iterator[Callable[[LLMProvider], TestClient]]:
    clients: list[TestClient] = []

    def _make(provider: LLMProvider) -> TestClient:
        settings = Settings(database_url=database_url, llm_provider="fake", log_level="WARNING")
        client = TestClient(create_app(settings, provider))
        client.__enter__()
        clients.append(client)
        return client

    yield _make
    for client in clients:
        client.__exit__(None, None, None)


@pytest.fixture
def fake_provider() -> FakeLLMProvider:
    return FakeLLMProvider()


@pytest.fixture
def client(
    make_client: Callable[[LLMProvider], TestClient], fake_provider: FakeLLMProvider
) -> TestClient:
    return make_client(fake_provider)
