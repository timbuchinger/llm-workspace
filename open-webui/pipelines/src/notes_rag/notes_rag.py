"""
title: RAG Filter Pipeline
author: Tim
date: 2025-01-20
version: 0.0.1
license: MIT
description: RAG filter pipeline.
requirements: llama-index, llama-index-embeddings-ollama, llama-index-vector-stores-chroma, chromadb, python-dotenv
"""

import logging
import os
from typing import List, Optional

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

# from llama_index.embeddings import OllamaEmbedding
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from pydantic import BaseModel

# from schemas import OpenAIChatMessage
# from utils.pipelines.main import get_last_user_message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
load_dotenv()


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
                "pipelines": ["llama3.2:3b", "llama3.1:8b"],
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
        user_message = body["messages"][0]["content"]
        # user_message = get_last_user_message(body["messages"])
        print(user_message)

        remote_db = chromadb.HttpClient(
            settings=Settings(
                anonymized_telemetry=False,
                chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider",
                chroma_client_auth_credentials=os.environ.get("CHROMA_AUTH_TOKEN"),
            ),
            host=os.environ.get("CHROMA_HOST"),
            port=int(os.environ.get("CHROMA_PORT", 8000)),
            ssl=os.environ.get("CHROMA_USE_SSL", "false").lower() == "true",
        )

        chroma_collection = remote_db.get_collection("langchain")
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

        protocol = (
            "https"
            if os.environ.get("OLLAMA_USE_SSL", "false").lower() == "true"
            else "http"
        )
        embed_model = OllamaEmbedding(
            model_name="nomic-embed-text",
            base_url=f"{protocol}://{os.environ.get('OLLAMA_URL')}:{os.environ.get('OLLAMA_PORT', 11434)}",
            # ollama_additional_kwargs={"mirostat": 0},
        )

        query_embedding = embed_model.get_query_embedding(
            "AWS and EKS"
        )  # user_message)
        results = chroma_collection.query(
            query_embeddings=query_embedding, n_results=3  # self.document_count
        )  # top_k)  #

        for result_id, result in enumerate(results["documents"][0]):
            print(f"Result {result_id + 1}:")
            if result_id == 0:
                document_text = result
            else:
                document_text += f"\n{result}"
            print(f"Document: {result}")
            print(f"Metadata: {results['metadatas'][0][result_id]}")
            print(f"Score: {results['distances'][0][result_id]}\n")

        with open(
            os.path.join(os.path.dirname(__file__), "notes_rag_prompt.txt"), "r"
        ) as file:
            template = file.read()

        template = template.replace("[DOCUMENT_TEXT]", document_text)
        template = template.replace("[USER_MESSAGE]", user_message)

        print(template)
        print("===================Prompt===================")
        print(template)
        print("============================================")

        print(f"Message count: {len(body['messages'])}")
        # raise Exception("Error")
        body["messages"][0]["content"] = template
        return body
