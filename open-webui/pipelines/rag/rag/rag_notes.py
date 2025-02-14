"""
title: Get Prompt Template Pipeline
author: Tim
date: 2025-01-20
version: 0.0.1
license:
description: Get prompt template.
requirements: requests, pydantic
"""

import logging
from functools import wraps
from typing import List, Optional

import requests
from pydantic import BaseModel

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
)


logger = logging.getLogger("rag_notes")
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


class Pipeline:
    class Valves(BaseModel):
        # List target pipeline ids (models) that this filter will be connected to.
        # If you want to connect this filter to all pipelines, you can set pipelines to ["*"]
        pipelines: List[str] = []

        # Assign a priority level to the filter pipeline.
        # The priority level determines the order in which the filter pipelines are executed.
        # The lower the number, the higher the priority.
        priority: int = 0
        document_count: int = 3
        pass

    def __init__(self):
        self.type = "filter"

        self.name = "RAG Filter"

        # self.valves = self.Valves(**{"pipelines": ["llama3.2:3b"]})
        self.valves = self.Valves(
            **{
                "pipelines": ["llama3.2:3b", "llama3.1:8b"],
            }
        )
        pass

    async def on_startup(self):
        # This function is called when the server is started.
        logger.info(f"on_startup:{__name__}")
        pass

    async def on_shutdown(self):
        # This function is called when the server is stopped.
        logger.info(f"on_shutdown:{__name__}")
        pass

    @log_function_call
    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        # This filter is applied to the form data before it is sent to the OpenAI API.
        logger.info(f"inlet:{__name__}")

        logger.info(body)
        logger.info(user)
        user_message = body["messages"][0]["content"]
        logger.info(f"Message count: {len(body['messages'])}")
        # user_message = get_last_user_message(body["messages"])
        logger.info(user_message)
        if len(body["messages"]) > 1:
            logger.info("More than one message, skipping RAG.")
            return body

        if not user_message.startswith(">"):
            logger.info("Not a prompt (does not start with '>'), skipping RAG.")
            return body

        response = requests.post(
            "http://pipelines-rag-svc:8000/prompt",
            json={"question": user_message},
        )
        if response.status_code == 200:
            prompt_response = response.json()
            logger.info(f"Prompt response: {prompt_response}")
            body["messages"][0]["content"] = prompt_response["prompt"]
            return body
        else:
            raise Exception(
                f"Failed to get prompt: {response.status_code} - {response.text}"
            )
