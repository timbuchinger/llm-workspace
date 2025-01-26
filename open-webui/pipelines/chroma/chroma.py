"""
title: Chroma Pipeline
author: Tim
date: 2025-01-19
version: 1.0
license:
description: A pipeline for retrieving relevant information from ChromaDB.
requirements: chromadb, langchain-chroma, langchain-ollama, pydantic==2.7.4, python-dotenv
"""

# requirements: chromadb<0.6.0, langchain-chroma==0.2.0, langchain-ollama==0.2.2, pydantic==2.7.4
import logging
import os
from typing import Generator, Iterator, List, Union

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_ollama.llms import OllamaLLM

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

load_dotenv()


def initialize_embeddings():
    protocol = (
        "https"
        if os.environ.get("OLLAMA_USE_SSL", "false").lower() == "true"
        else "http"
    )
    embeddings = OllamaEmbeddings(
        base_url=f"{protocol}://{os.environ.get('OLLAMA_HOST')}:{os.environ.get('OLLAMA_PORT', 11434)}",
        model="nomic-embed-text",
    )
    return embeddings


def initialize_chroma_client(embeddings: Embeddings) -> Chroma:

    chroma_client = chromadb.HttpClient(
        settings=Settings(
            anonymized_telemetry=False,
            chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider",
            chroma_client_auth_credentials=os.environ.get("CHROMA_AUTH_TOKEN"),
        ),
        host=os.environ.get("CHROMA_HOST"),
        port=int(os.environ.get("CHROMA_PORT", 8000)),
        ssl=os.environ.get("CHROMA_USE_SSL", "false").lower() == "true",
    )
    chroma_client.heartbeat()

    chroma_client.get_or_create_collection("notion")

    vector_store = Chroma(
        client=chroma_client,
        collection_name="notion",
        embedding_function=embeddings,
    )
    return vector_store


class Pipeline:
    def __init__(self):
        self.vector_store = None
        self.embeddings = None
        pass

    async def on_startup(self):
        logger.info(f"on_startup:{__name__}")
        self.embeddings = initialize_embeddings()
        self.vector_store = initialize_chroma_client(self.embeddings)
        pass

    async def on_shutdown(self):
        logger.info(f"on_shutdown:{__name__}")
        pass

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:

        logger.info(f"Messages: {messages}")
        logger.info(f"User message: {user_message}")
        logger.info(f"Model ID: {model_id}")
        logger.info(f"Body: {body}")

        try:

            embeddings = initialize_embeddings()

            embedding_vector = embeddings.embed_query(user_message)
            logger.info("Embedding vector: " + str(embedding_vector))
            results = (
                self.vector_store.similarity_search_by_vector_with_relevance_scores(
                    embedding=embedding_vector, k=3  # num_results
                )
            )

            if not results or len(results) == 0:
                return ("No documents found matching query: " + user_message,)
            else:
                context = "\n".join(
                    f"* [SIM={score:.3f}] [Content={res.page_content}] [Metadata={res.metadata}]"
                    for res, score in results
                )

                template = """
                INSTRUCTIONS:
                Answer the users QUESTION using the DOCUMENT text below.
                Keep your answer ground in the facts of the DOCUMENT.
                If the DOCUMENT doesn’t contain the facts to answer the QUESTION return NONE

                DOCUMENT:
                {document_text}

                QUESTION:
                {users_question}"""

                logger.info(f"Template:\n{template}")

                # from_messages
                prompt = ChatPromptTemplate.from_template(template)

                model = OllamaLLM(
                    base_url=f"http://{os.environ.get('OLLAMA_HOST')}:{os.environ.get('OLLAMA_PORT', 11434)}",
                    model="llama3.1:8b",
                )

                chain = prompt | model

                response = chain.invoke(
                    {"document_text": context, "users_question": user_message}
                )
                logger.info(f"Response:\n{response}")
                return response

        except Exception as e:
            logger.error(f"Search error: {str(e)}", exc_info=True)
            raise Exception(str(e))
