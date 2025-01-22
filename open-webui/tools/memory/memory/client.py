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

import logging
import sys
from typing import Any, Callable
import requests

import inspect
from functools import wraps

BASE_URL = "http://localhost:8000"

logging.basicConfig(
    stream=sys.stderr,
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
)
logger = logging.getLogger("tools_memory")


class EventEmitter:
    def __init__(self, event_emitter: Callable[[dict], Any] = None):
        self.event_emitter = event_emitter

    async def emit(self, description="Unknown state", status="in_progress", done=False):
        if self.event_emitter:
            await self.event_emitter(
                {
                    "type": "status",
                    "data": {
                        "status": status,
                        "description": description,
                        "done": done,
                    },
                }
            )


def decorator(func):
    def wrap(*args, **kwargs):
        # Log the function name and arguments
        logger.debug(f"Calling {func.__name__} with args: {args}, kwargs: {kwargs}")

        # Call the original function
        result = func(*args, **kwargs)

        # Log the return value
        logger.debug(f"{func.__name__} returned: {result}")

        # Return the result
        return result

    return wrap


def dump_args(func):
    """
    Decorator to print function call details.

    This includes parameters names and effective values.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        func_args = inspect.signature(func).bind(*args, **kwargs).arguments
        func_args_str = ", ".join(map("{0[0]} = {0[1]!r}".format, func_args.items()))
        logger.debug(f"{func.__module__}.{func.__qualname__} ( {func_args_str} )")
        return func(*args, **kwargs)

    return wrapper


class Tools:

    def __init__(self):
        self.citation = True
        pass

    @decorator
    def add_memory(self, content: str, tags: list = []) -> str:
        """
        Adds a memory for the user.
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

    @decorator
    def search_memory(self, query: str):
        """
        Searches for memories for the user based on a query.
        :param query The query to search for.
        :return A list of memories for the user that match the search query.
        """
        payload = {"query": query}
        response = requests.post(f"{BASE_URL}/search_memory", json=payload)

        return f"List of memories: {response.json().get('memories')}"

    @decorator
    def retrieve_all(self) -> list[str]:
        """
        Retrieves all memories for the user.
        :return A list of memories. The memories should be presented to the user as a bulleted list, unless they have asked for the memories to be summarized.
        """
        response = requests.get(f"{BASE_URL}/retrieve_all")
        return f"List of memories: {response.json().get('memories')}"

    @decorator
    def get_by_tag(self, tags: list):
        """
        Retrieves memories by tags for the user.
        :param tags A list of tags to search for.
        :return A list of memories.
        """
        payload = {"tags": tags}
        response = requests.post(f"{BASE_URL}/get_by_tag", json=payload)
        return f"List of memories: {response.json().get('memories')}"
