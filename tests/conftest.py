import pytest

from resrun.builder import ResrunBuilder


@pytest.fixture
def builder() -> ResrunBuilder:
    return ResrunBuilder()


@pytest.fixture
def base_config() -> dict:
    return {
        "repos": [
            {"path": "/home/test/repo1", "id": "repo1", "default": True},
            {"path": "/home/test/repo2", "id": "repo2"},
        ]
    }
