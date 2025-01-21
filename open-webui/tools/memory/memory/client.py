import requests

BASE_URL = "http://localhost:8000"


def add_memory(content: str, tags: list = None):
    """
    Adds a memory to the server.
    """
    payload = {"content": content, "tags": tags}
    response = requests.post(f"{BASE_URL}/add_memory", json=payload)
    return response.json()


def delete_memory(content: str):
    """
    Deletes a memory from the server.
    """
    response = requests.delete(f"{BASE_URL}/delete_memory", params={"content": content})
    return response.json()


def search_memory(query: str):
    """
    Searches for memories based on a query.
    """
    payload = {"query": query}
    response = requests.post(f"{BASE_URL}/search_memory", json=payload)
    return response.json()


def retrieve_all():
    """
    Retrieves all memories.
    """
    response = requests.get(f"{BASE_URL}/retrieve_all")
    return response.json()


def get_by_tag(tags: list):
    """
    Retrieves memories by tags.
    """
    payload = {"tags": tags}
    response = requests.post(f"{BASE_URL}/get_by_tag", json=payload)
    return response.json()
