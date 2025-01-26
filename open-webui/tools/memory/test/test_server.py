from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from memory.server import app

client = TestClient(app)


@pytest.fixture
def mock_tools():
    with patch("memory.server.tools") as mock:
        yield mock


def test_healthcheck():
    response = client.get("/healthcheck")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_add_memory(mock_tools):
    mock_tools.add_memory = MagicMock()
    memory_request = {"content": "Test memory", "tags": ["tag1", "tag2"]}
    response = client.post("/add_memory", json=memory_request)
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Memory added successfully",
    }
    mock_tools.add_memory.assert_called_once()


def test_add_memory_exception(mock_tools):
    mock_tools.add_memory.side_effect = Exception("Test exception")
    memory_request = {"content": "Test memory", "tags": ["tag1", "tag2"]}
    response = client.post("/add_memory", json=memory_request)
    assert response.status_code == 500
    assert response.json() == {"detail": "Test exception"}


def test_delete_memory(mock_tools):
    mock_tools.delete_memory = MagicMock()
    response = client.delete("/delete_memory", params={"content": "Test memory"})
    assert response.status_code == 200
    assert response.json() == {"message": "Memory deleted successfully."}
    mock_tools.delete_memory.assert_called_once_with("Test memory")


def test_delete_memory_exception(mock_tools):
    mock_tools.delete_memory.side_effect = Exception("Test exception")
    response = client.delete("/delete_memory", params={"content": "Test memory"})
    assert response.status_code == 500
    assert response.json() == {"detail": "Test exception"}


def test_search_memory(mock_tools):
    mock_tools.search_memory.return_value = ["Test memory"]
    query_request = {"query": "Test query"}
    response = client.post("/search_memory", json=query_request)
    assert response.status_code == 200
    assert response.json() == {"memories": ["Test memory"]}
    mock_tools.search_memory.assert_called_once_with("Test query")


def test_search_memory_exception(mock_tools):
    mock_tools.search_memory.side_effect = Exception("Test exception")
    query_request = {"query": "Test query"}
    response = client.post("/search_memory", json=query_request)
    assert response.status_code == 500
    assert response.json() == {"detail": "Test exception"}


def test_retrieve_all(mock_tools):
    mock_tools.retrieve_all.return_value = ["Test memory"]
    response = client.get("/retrieve_all")
    assert response.status_code == 200
    assert response.json() == {"memories": ["Test memory"]}
    mock_tools.retrieve_all.assert_called_once()


def test_retrieve_all_exception(mock_tools):
    mock_tools.retrieve_all.side_effect = Exception("Test exception")
    response = client.get("/retrieve_all")
    assert response.status_code == 500
    assert response.json() == {"detail": "Test exception"}


def test_get_by_tag(mock_tools):
    mock_tools.get_by_tag.return_value = ["Test memory"]
    tags_request = {"tags": ["tag1"]}
    response = client.post("/get_by_tag", json=tags_request)
    assert response.status_code == 200
    assert response.json() == {"results": ["Test memory"]}
    mock_tools.get_by_tag.assert_called_once_with(["tag1"])


def test_get_by_tag_exception(mock_tools):
    mock_tools.get_by_tag.side_effect = Exception("Test exception")
    tags_request = {"tags": ["tag1"]}
    response = client.post("/get_by_tag", json=tags_request)
    assert response.status_code == 500
    assert response.json() == {"detail": "Test exception"}
    assert response.json() == {"detail": "Test exception"}
