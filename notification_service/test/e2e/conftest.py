from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from src.app import app
from src.domain.connection_hub import ConnectionHub


@pytest.fixture
def client() -> Iterator[TestClient]:
    app.state.connection_hub = ConnectionHub()
    with TestClient(app) as test_client:
        yield test_client
