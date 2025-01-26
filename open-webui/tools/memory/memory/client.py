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
from functools import wraps
from typing import Any, Awaitable, Callable, Optional

import requests
from pydantic import BaseModel, Field

BASE_URL = "http://tools-memory-svc:8000"
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
)


logger = logging.getLogger("tools_memory")
logger.setLevel("DEBUG")


def log_function_call(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        class_name = args[0].__class__.__name__ if args else ""
        method_name = func.__name__
        logger.info(
            f"Calling {class_name}.{method_name} with args={args[1:]} kwargs={kwargs}"
        )
        result = func(*args, **kwargs)
        logger.info(f"{class_name}.{method_name} returned {result}")
        return result

    return wrapper


class Tools:
    class Valves(BaseModel):
        unpack_responses: bool = Field(
            default=True,
            description="Should the responses be unpacked from JSON to human-readable strings.",
        )

    def __init__(self):

        self.citation = True
        self.Valves = Tools.Valves

    # async def emit_event(self, description: str, done: bool) -> None:
    #     if __event_emitter__:
    #         await __event_emitter__(
    #             {
    #                 "type": "status",
    #                 "data": {
    #                     "description": description,
    #                     "done": done,
    #                 },
    #             }
    #         )

    @log_function_call
    async def add_memory(
        self,
        content: str,
        tags: list = [],
        __event_emitter__: Optional[Callable[[Any], Awaitable[None]]] = None,
    ) -> str:
        """
        Adds a memory to the server.

        Args:
            content (str): The content of the memory.
            tags (list): A list of tags associated with the memory.

        Returns:
            str: A message indicating success or failure, e.g.,
                 {"status": "success", "message": "Memory added successfully"} or
                 {"status": "error", "message": "Error message"}.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Adding memory...",
                        "done": False,
                    },
                }
            )
        payload = {"content": content, "tags": tags}
        try:
            response = requests.post(f"{BASE_URL}/add_memory", json=payload)
            response.raise_for_status()
            logger.info(f"Server response: {response.json()}")

            if self.valves.unpack_responses:
                return response.json()["message"]
            else:
                return response.json()
        except requests.exceptions.RequestException as e:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Request exception occurred.",
                            "done": True,
                        },
                    }
                )
            logger.error(f"exception: {e}")
            return {"status": "error", "message": str(e)}
        except Exception as e:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Exception occurred.",
                            "done": True,
                        },
                    }
                )

    @log_function_call
    async def delete_memory(
        self,
        content: str,
        __event_emitter__: Optional[Callable[[Any], Awaitable[None]]] = None,
    ) -> dict:
        """
        Deletes a memory from the server.

        Args:
            content (str): The exact content of the memory to delete.

        Returns:
            dict: A structured response indicating success or failure:
                - On success: {"status": "success", "message": "Memory deleted successfully"}
                - On failure: {"status": "error", "message": "Error message"}
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Deleting memory...",
                        "done": False,
                    },
                }
            )

        try:
            response = requests.delete(
                f"{BASE_URL}/delete_memory", params={"content": content}
            )
            response.raise_for_status()
            if self.valves.unpack_responses:
                return response.json()["message"]
            else:
                return response.json()
        except requests.exceptions.RequestException as e:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Request exception occurred.",
                            "done": True,
                        },
                    }
                )
            logger.error(f"exception: {e}")
            return {"status": "error", "message": str(e)}
        except Exception as e:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Exception occurred.",
                            "done": True,
                        },
                    }
                )
            return {"status": "error", "message": str(e)}

    @log_function_call
    async def search_memory(
        self,
        query: str,
        __event_emitter__: Optional[Callable[[Any], Awaitable[None]]] = None,
    ) -> list:
        """
        Searches for memories based on a query.

        Args:
            query (str): The query to search for.

        Returns:
            list: A list of matching memories in the format:
                  [{"id": int, "content": str, "tags": list, "timestamp": str}, ...]
                  or an empty list if no matches are found.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Searching memory...",
                        "done": False,
                    },
                }
            )

        payload = {"query": query}
        try:
            response = requests.post(f"{BASE_URL}/search_memory", json=payload)
            response.raise_for_status()
            if self.valves.unpack_responses:
                output = ""
                for memory in response.json().get("memories", []):
                    output += f"{memory["id"]}: {memory["content"]} (tags: {memory["tags"]}) {memory["timestamp"]}\n"
                return output
            else:
                return response.json()
        except requests.exceptions.RequestException as e:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Request exception occurred.",
                            "done": True,
                        },
                    }
                )
            logger.error(f"exception: {e}")
            return {"status": "error", "message": str(e)}
        except Exception as e:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Exception occurred.",
                            "done": True,
                        },
                    }
                )
            logger.error(f"exception: {e}")
            return {"status": "error", "message": str(e)}

    @log_function_call
    async def retrieve_all(
        self, __event_emitter__: Optional[Callable[[Any], Awaitable[None]]] = None
    ) -> list:
        """
        Retrieves all memories from the server.

        Returns:
            list: A list of all stored memories in the format:
                  [{"id": int, "content": str, "tags": list, "timestamp": str}, ...]
                  or an empty list if no memories exist.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Getting memory...",
                        "done": False,
                    },
                }
            )
        try:
            response = requests.get(f"{BASE_URL}/retrieve_all")
            response.raise_for_status()
            if self.valves.unpack_responses:
                output = ""
                for memory in response.json().get("memories", []):
                    output += f"{memory["id"]}: {memory["content"]} (tags: {memory["tags"]}) {memory["timestamp"]}\n"
                return output
            else:
                return response.json()
        except requests.exceptions.RequestException as e:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Request exception occurred.",
                            "done": True,
                        },
                    }
                )
            logger.error(f"exception: {e}")
            return {"status": "error", "message": str(e)}
        except Exception as e:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Exception occurred.",
                            "done": True,
                        },
                    }
                )
            logger.error(f"exception: {e}")
            return {"status": "error", "message": str(e)}

    @log_function_call
    async def get_by_tag(
        self,
        tags: list[str],
        __event_emitter__: Optional[Callable[[Any], Awaitable[None]]] = None,
    ) -> list:
        """
        Retrieves memories based on tags.

        Args:
            tags (list): A list of tags to filter by.

        Returns:
            list: A list of matching memories in the format:
                  [{"id": int, "content": str, "tags": list, "timestamp": str}, ...]
                  or an empty list if no matches are found.
        """
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "Getting memories by tag...",
                        "done": False,
                    },
                }
            )
        payload = {"tags": tags}
        try:
            response = requests.post(f"{BASE_URL}/get_by_tag", json=payload)
            response.raise_for_status()
            if self.valves.unpack_responses:
                output = ""
                for memory in response.json().get("memories", []):
                    output += f"{memory["id"]}: {memory["content"]} (tags: {memory["tags"]}) {memory["timestamp"]}\n"
                return output
            else:
                return response.json()
        except requests.exceptions.RequestException as e:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Request exception occurred.",
                            "done": True,
                        },
                    }
                )
            logger.error(f"exception: {e}")
            return {"status": "error", "message": str(e)}
        except Exception as e:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Exception occurred.",
                            "done": True,
                        },
                    }
                )
            logger.error(f"exception: {e}")
            return {"status": "error", "message": str(e)}
