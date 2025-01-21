from unittest.mock import patch

import pytest
import requests

from memory.client import add_memory

BASE_URL = "http://localhost:8000"


@pytest.fixture
def mock_post():
    with patch("requests.post") as mock:
        yield mock


def test_add_memory_success(mock_post):
    mock_response = mock_post.return_value
    mock_response.json.return_value = {"status": "success", "id": "123"}
    mock_response.status_code = 200

    content = "Sample memory content"
    tags = ["tag1", "tag2"]
    response = add_memory(content, tags)

    mock_post.assert_called_once_with(
        f"{BASE_URL}/add_memory", json={"content": content, "tags": tags}
    )
    assert response == {"status": "success", "id": "123"}


def test_add_memory_failure(mock_post):
    mock_response = mock_post.return_value
    mock_response.json.return_value = {
        "status": "error",
        "message": "Failed to add memory",
    }
    mock_response.status_code = 400

    content = "Sample memory content"
    tags = ["tag1", "tag2"]
    response = add_memory(content, tags)

    mock_post.assert_called_once_with(
        f"{BASE_URL}/add_memory", json={"content": content, "tags": tags}
    )
    assert response == {"status": "error", "message": "Failed to add memory"}
