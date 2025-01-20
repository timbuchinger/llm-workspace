"""
title: RAG Filter Pipeline
author: Tim
date: 2025-01-20
version: 0.0.1
license: MIT
description: RAG filter pipeline.
requirements: requests, llama-index chromadb, chromadb
"""

from typing import List, Optional
from pydantic import BaseModel
import chromadb

# from schemas import OpenAIChatMessage
from utils.pipelines.main import get_last_user_message
from llama_index.vector_stores.chroma import ChromaVectorStore


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

        # Add your custom parameters here
        pass

    def __init__(self):
        # Pipeline filters are only compatible with Open WebUI
        # You can think of filter pipeline as a middleware that can be used to edit the form data before it is sent to the OpenAI API.
        self.type = "filter"

        # Optionally, you can set the id and name of the pipeline.
        # Best practice is to not specify the id so that it can be automatically inferred from the filename, so that users can install multiple versions of the same pipeline.
        # The identifier must be unique across all pipelines.
        # The identifier must be an alphanumeric string that can include underscores or hyphens. It cannot contain spaces, special characters, slashes, or backslashes.
        # self.id = "filter_pipeline"

        self.name = "RAG Filter"

        # self.valves = self.Valves(**{"pipelines": ["llama3.2:3b"]})
        self.valves = self.Valves(
            **{
                "pipelines": ["*"],
            }
        )
        pass

    async def on_startup(self):
        # This function is called when the server is started.
        print(f"on_startup:{__name__}")
        pass

    async def on_shutdown(self):
        # This function is called when the server is stopped.
        print(f"on_shutdown:{__name__}")
        pass

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        # This filter is applied to the form data before it is sent to the OpenAI API.
        print(f"inlet:{__name__}")

        print(body)
        print(user)
        user_message = get_last_user_message(body["messages"])
        print(user_message)

        remote_db = chromadb.HttpClient("http://localhost:8000")
        chroma_collection = remote_db.get_collection("langchain")
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

        prompt = """Based on the CONTEXT below, answer the user's QUESTION
        <CONTEXT>
        </CONTEXT>
        <QUESTION>
        {user_message}
        </QUESTION>"""

        print(f"Message count: {len(body['messages'])}")

        return body
