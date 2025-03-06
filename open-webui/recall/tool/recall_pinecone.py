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
import re
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


def get_pinecone_index(user: Optional[dict]) -> str:
    """Extract location from user name brackets and return appropriate collection names."""
    if user and "name" in user:
        match = re.search(r"\[(.*?)\]", user["name"].lower())
        if match:
            location = match.group(1)
            return location
    return "testing"


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
            default="http://recall-svc:8000",
            description="The endpoint of the server to use.",
        )
        unpack_responses: bool = Field(
            default=True,
            description="Should the responses be unpacked from JSON to human-readable strings.",
        )

    def __init__(self):
        self.citation = True
        self.valves = Tools.Valves()

    @log_function_call
    async def add_memory(
        self,
        memory: str,
        __user__: dict,
        __event_emitter__: Optional[Callable[[Any], Awaitable[None]]] = None,
    ) -> str:
        """
        Adds a memory to the server.

        Args:
            memory (str): The content of the memory.
            __user__ (dict): User information for determining the index.
            __event_emitter__ (Optional[Callable]): Event emitter for status updates.

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
        payload = {"memory": memory, "index": get_pinecone_index(__user__)}
        logger.debug("Adding memory")
        try:
            response = requests.post(
                f"{self.valves.server_url}/add-memory-pinecone", json=payload
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
