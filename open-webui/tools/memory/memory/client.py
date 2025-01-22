"""
title: Memory
authors: Tim
description:
author_url:
funding_url:
version: 0.0.1
license:
requirements: requests
"""

import requests

BASE_URL = "http://localhost:8000"


class Tools:

    def __init__(self):
        self.citation = True
        pass

    def add_memory(self, content: str, tags: list = []) -> str:
        """
        Adds a memory to the server.
        :param content The content of the memory.
        :param tags A list of tags associated with the memory.
        :returns A message indicating success or failure.
        """
        payload = {"content": content, "tags": tags}
        response = requests.post(f"{BASE_URL}/add_memory", json=payload)
        return response.json().get("message")

    # def delete_memory(content: str):
    #     """
    #     Deletes a memory from the server.
    #     :param content The content of the memory to delete.
    #     :returns The response from the server.
    #     """
    #     response = requests.delete(f"{BASE_URL}/delete_memory", params={"content": content})
    #     return response.json()

    def search_memory(self, query: str):
        """
        Searches for memories based on a query.
        :param query The query to search for.
        :return A list of memories.
        """
        payload = {"query": query}
        response = requests.post(f"{BASE_URL}/search_memory", json=payload)

        return response.json().get("memories")

    def retrieve_all(self) -> list[str]:
        """
        Retrieves all memories.
        :return A list of memories.
        """
        response = requests.get(f"{BASE_URL}/retrieve_all")
        return response.json().get("memories")

    def get_by_tag(self, tags: list):
        """
        Retrieves memories by tags.
        :param tags A list of tags to search for.
        :return A list of memories.
        """
        payload = {"tags": tags}
        response = requests.post(f"{BASE_URL}/get_by_tag", json=payload)
        return response.json()
