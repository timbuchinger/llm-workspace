"""
title: Get Prompt Template Pipeline (Pinecone)
author: Tim
date: 2025-01-20
version: 0.0.1
license:
description: Get prompt template using Pinecone for document retrieval.
requirements: requests, pydantic
"""

import logging
import os
import re
from functools import wraps
from typing import List, Optional, Tuple

import requests
from pydantic import BaseModel


def get_collections(user: Optional[dict]) -> Tuple[str, str]:
    """Extract location from user name brackets and return appropriate collection names."""
    if user and "name" in user:
        match = re.search(r"\[(.*?)\]", user["name"].lower())
        if match:
            location = match.group(1)
            return f"memories-{location}", f"notion-{location}"
    return "memories", "notion"


def get_pinecone_index(user: Optional[dict]) -> str:
    """Extract location from user name brackets and return appropriate collection names."""
    if user and "name" in user:
        match = re.search(r"\[(.*?)\]", user["name"].lower())
        if match:
            location = match.group(1)
            return location
    return "testing"


logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
)

logger = logging.getLogger("recall_pinecone")
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
        pipelines: List[str] = []
        priority: int = 0
        document_count: int = 5

    def __init__(self):
        self.type = "filter"
        self.name = "recall_pinecone"
        self.valves = self.Valves(**{"pipelines": ["*"]})

    async def on_startup(self):
        logger.info(f"on_startup:{__name__}")
        pass

    async def on_shutdown(self):
        logger.info(f"on_shutdown:{__name__}")
        pass

    @log_function_call
    async def outlet(self, body: dict, user: dict) -> dict:
        body["messages"][-1]["sources"] = [
            dict(
                document="testing",
                metadata={"source": "https://google.com"},
                source={"name": "Google"},
            )
        ]
        return body

    @log_function_call
    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        logger.info(f"inlet:{__name__}")
        logger.info(f"User: {user}")

        task = body["metadata"].get("task", "default_value")

        if task in ["tags_generation", "title_generation"]:
            logger.info("Skipping RAG for tags and title generation tasks.")
            return body

        logger.info(body)
        logger.info(user)
        user_message = body["messages"][0]["content"]
        logger.info(f"Message count: {len(body['messages'])}")
        logger.info(f"User message: {user_message}")

        if len(body["messages"]) > 1:
            logger.info("More than one message, skipping RAG.")
            return body

        if not user_message.startswith(">"):
            logger.info("Not a prompt (does not start with '>'), skipping RAG.")
            return body

        # Remove the '>' character from the start of the message
        user_message = user_message[1:]
        logger.info(f"Processed user message (removed '>'): {user_message}")

        request_json = {
            "query": user_message,
            "index": get_pinecone_index(user),
            "n_results": self.valves.document_count,
        }
        print(f"Request JSON: {request_json}")
        # Call the search-similar-pinecone endpoint
        response = requests.post(
            "http://recall-svc:8000/search-similar-pinecone",
            json=request_json,
        )

        if response.status_code == 200:
            data = response.json()
            documents = data.get("documents", [])

            if documents:
                # Read the prompt template
                current_dir = os.path.dirname(os.path.abspath(__file__))
                prompt_path = os.path.join(current_dir, "prompt.txt")

                with open(prompt_path, "r") as f:
                    prompt_template = f.read()

                # Format documents with XML tags
                formatted_docs = []
                for doc in documents:
                    formatted_doc = f"<source>\n<source_id>{doc['id']}</source_id>\n{doc['content']}\n</source>"
                    formatted_docs.append(formatted_doc)

                # Join all formatted documents with newlines
                combined_content = "\n\n".join(formatted_docs)
                logger.info(f"Combined content: {combined_content}")

                # Replace placeholders in the template
                logger.info(f"User message: {user_message}")
                final_prompt = prompt_template.replace("{{CONTEXT}}", combined_content)
                final_prompt = final_prompt.replace("{{QUERY}}", user_message)

                logger.info(f"Final prompt: {final_prompt}")

                body["messages"][0]["content"] = final_prompt
            else:
                # No results case
                current_dir = os.path.dirname(os.path.abspath(__file__))
                no_results_path = os.path.join(current_dir, "no_results_prompt.txt")

                with open(no_results_path, "r") as f:
                    no_results_template = f.read()

                # Replace placeholders with actual values
                index = list(get_pinecone_index(user))
                collections_str = index
                final_prompt = no_results_template.replace(
                    "{{COLLECTIONS}}", collections_str
                )
                final_prompt = final_prompt.replace(
                    "{{N_RESULTS}}", str(self.valves.document_count)
                )
                final_prompt = final_prompt.replace("{{QUERY}}", user_message)

                logger.info(f"Final prompt: {final_prompt}")

                body["messages"][0]["content"] = final_prompt
        else:
            raise Exception("Failed to query recall service.")

        return body
