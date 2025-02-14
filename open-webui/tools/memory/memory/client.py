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

import inspect
import logging
from functools import wraps
from typing import Any, Awaitable, Callable, Optional

import requests
from pydantic import BaseModel, Field

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
)
logger = logging.getLogger("tools_memory")
logger.setLevel("DEBUG")


def log_function_call(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        class_name = args[0].__class__.__name__ if args else ""
        method_name = func.__name__
        logger.info(
            f"Calling {class_name}.{method_name} with args={args[1:]} kwargs={kwargs}"
        )
        result = await func(*args, **kwargs)
        logger.info(f"{class_name}.{method_name} returned {result}")
        return result

    @wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        class_name = args[0].__class__.__name__ if args else ""
        method_name = func.__name__
        logger.info(
            f"Calling {class_name}.{method_name} with args={args[1:]} kwargs={kwargs}"
        )
        result = func(*args, **kwargs)
        logger.info(f"{class_name}.{method_name} returned {result}")
        return result

    if inspect.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


async def handle_excepton(
    exception: Exception, event_emitter: Callable[[dict], Any] = None
):
    logger.exception("Exception occurred while invoking tool")
    if event_emitter:
        await event_emitter(
            {
                "type": "status",
                "data": {
                    "description": "Exception occurred.",
                    "done": True,
                },
            }
        )
    # logger.error(f"Exception: {exception}")
    return {"status": "error", "message": str(exception)}


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


class Tools:
    class Valves(BaseModel):
        server_url: str = Field(
            default="http://tools-memory-svc:8000",
            description="The endpoint of the server to use.",
        )
        unpack_responses: bool = Field(
            default=True,
            description="Should the responses be unpacked from JSON to human-readable strings.",
        )

    class UserValves(BaseModel):
        chroma_collection: str = Field(
            default="memories",
            description="The name of the collection to use in ChromaDB.",
        )

    def __init__(self):

        self.citation = True
        self.valves = Tools.Valves()
        self.user_valves = Tools.UserValves()

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
        tags: list[str],
        __event_emitter__: Optional[Callable[[Any], Awaitable[None]]] = None,
    ) -> str:
        """
        Adds a memory to the server.

        Args:
            content (str): The content of the memory.
            tags (list): A list of tags associated with the memory.

        Returns:
            str: A message indicating success or failure, e.g.,
                 - On success: "Memory added successfully"
                 - On error: "Error message"
        """
        logger.debug("Adding memory")
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
        logger.debug("Adding memory")
        payload = {
            "content": content,
            "tags": tags,
            "chroma_collection_name": self.user_valves.chroma_collection,
        }
        logger.debug("Adding memory")
        try:
            response = requests.post(
                f"{self.valves.server_url}/add_memory", json=payload
            )
            response.raise_for_status()
            logger.debug(f"Server response: {str(response.json())}")
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Memory added.",
                            "done": True,
                        },
                    }
                )
            if self.valves.unpack_responses:
                logger.debug("Unpacking response")
                return response.json()["message"]
            else:
                logger.warning("Packing response")
                return response.json()
        except (requests.exceptions.RequestException, Exception) as e:
            await handle_excepton(e, __event_emitter__)

    @log_function_call
    async def delete_memory(
        self,
        content: str,
        __event_emitter__: Optional[Callable[[Any], Awaitable[None]]] = None,
    ) -> str:
        """
        Deletes a memory from the server.

        Args:
            content (str): The exact content of the memory to delete.

        Returns:
            str: A messageindicating success or failure:
                - On success: "Memory deleted successfully"
                - On failure: "Error message"
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
                f"{self.valves.server_url}/delete_memory",
                json={
                    "content": content,
                    "chroma_collection_name": self.user_valves.chroma_collection,
                },
            )
            response.raise_for_status()
            if self.valves.unpack_responses:
                return response.json()["message"]
            else:
                return response.json()
        except (requests.exceptions.RequestException, Exception) as e:
            await handle_excepton(e, __event_emitter__)

    @log_function_call
    async def search_memory(
        self,
        query: str,
        __event_emitter__: Optional[Callable[[Any], Awaitable[None]]] = None,
    ) -> str:
        """
        Searches for memories based on a query.

        Args:
            query (str): The query to search for.

        Returns:
            list: A list of matching memories in the format:
                  "ID: content (tags: tag1, tag2, etc) date"
                  or an empty string if no matches are found.
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

        payload = {
            "query": query,
            "chroma_collection_name": self.user_valves.chroma_collection,
        }
        try:
            response = requests.post(
                f"{self.valves.server_url}/search_memory", json=payload
            )
            response.raise_for_status()
            if self.valves.unpack_responses:
                output = ""
                for memory in response.json().get("memories", []):
                    output += f"{memory['id']}: {memory['content']} (tags: {memory['tags']}) {memory['date']}\n"
                return output
            else:
                return response.json()
        except (requests.exceptions.RequestException, Exception) as e:
            await handle_excepton(e, __event_emitter__)

    @log_function_call
    async def retrieve_all(
        self, __event_emitter__: Optional[Callable[[Any], Awaitable[None]]] = None
    ) -> str:
        """
        Retrieves all memories from the server.

        Returns:
            list: A list of all memories in the format:
                  "ID: content (tags: tag1, tag2, etc) date"
                  or an empty string if no memories are found.
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
            data = {"chroma_collection_name": self.user_valves.chroma_collection}
            response = requests.post(
                f"{self.valves.server_url}/retrieve_all", json=data
            )
            response.raise_for_status()
            if self.valves.unpack_responses:
                output = ""
                for memory in response.json().get("memories", []):
                    logger.debug(f"Memory: {memory}")
                    output += f"{memory['id']}: {memory['content']} (tags: {memory['tags']}) {memory['date']}\n"
                return output
            else:
                return response.json()
        except (requests.exceptions.RequestException, Exception) as e:
            await handle_excepton(e, __event_emitter__)

    @log_function_call
    async def get_by_tag(
        self,
        tags: list[str],
        __event_emitter__: Optional[Callable[[Any], Awaitable[None]]] = None,
    ) -> str:
        """
        Retrieves memories based on tags.

        Args:
            tags (list): A list of tags to filter by.

        Returns:
            list: A list of matching memories in the format:
                  "ID: content (tags: tag1, tag2, etc) date"
                  or an empty string if no matches are found.
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
        payload = {
            "tags": tags,
            "chroma_collection_name": self.user_valves.chroma_collection,
        }
        try:
            response = requests.post(
                f"{self.valves.server_url}/get_by_tag", json=payload
            )
            response.raise_for_status()
            if self.valves.unpack_responses:
                output = ""
                for memory in response.json().get("memories", []):
                    output += f"{memory['id']}: {memory['content']} (tags: {memory['tags']}) {memory['date']}\n"
                return output
            else:
                return response.json()
        except (requests.exceptions.RequestException, Exception) as e:
            await handle_excepton(e, __event_emitter__)
