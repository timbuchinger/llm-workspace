import logging
import os
import uuid
from datetime import datetime
from functools import wraps
from typing import List, Optional

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
from fastapi import FastAPI
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from pinecone import Pinecone
from pydantic import BaseModel

load_dotenv()


class HealthCheckFilter(logging.Filter):
    def filter(self, record):
        return "/healthz" not in record.getMessage()


logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
)

logger = logging.getLogger("rag_notes_server")
logger.setLevel("DEBUG")
load_dotenv()
app = FastAPI()

logger.info("Server started.")


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


class MemoryAddRequest(BaseModel):
    memory: str
    tags: Optional[list[str]] = []
    collection: str


class MemorySearchRequest(BaseModel):
    query: str
    n_results: Optional[int] = 3
    collections: list[str]


class PineconeMemoryAddRequest(BaseModel):
    memory: str
    index: str


class PineconeMemorySearchRequest(BaseModel):
    query: str
    n_results: Optional[int] = 3
    index: str


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@log_function_call
@app.post("/add-memory")
async def add_memory(memory_request: MemoryAddRequest):
    logger.info(f"Adding memory: {memory_request.memory}")
    logger.info(f"Tags: {memory_request.tags}")
    logger.info(f"Collection: {memory_request.collection}")

    remote_db = chromadb.HttpClient(
        host=os.environ.get("CHROMA_HOST"),
        port=int(os.environ.get("CHROMA_PORT", 8000)),
        ssl=os.environ.get("CHROMA_USE_SSL", "false").lower() == "true",
        settings=Settings(
            anonymized_telemetry=False,
            chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider",
            chroma_client_auth_credentials=os.environ.get("CHROMA_AUTH_TOKEN"),
        ),
    )

    protocol = (
        "https"
        if os.environ.get("OLLAMA_USE_SSL", "false").lower() == "true"
        else "http"
    )

    logger.debug("Setting up embeddings...")
    embeddings = OllamaEmbeddings(
        model="nomic-embed-text",
        base_url=f"{protocol}://{os.environ.get('OLLAMA_HOST')}:{os.environ.get('OLLAMA_PORT', 11434)}",
    )

    logger.debug("Initializing vector stores for each collection...")

    store = Chroma(
        client=remote_db,
        collection_name=memory_request.collection,
        embedding_function=embeddings,
    )

    memory_embedding = embeddings.embed_query(memory_request.memory)

    chroma_collection = store._client.get_collection(memory_request.collection)

    chroma_collection.add(
        ids=[str(uuid.uuid4())],
        metadatas=[
            {"tags": ",".join(memory_request.tags), "date": datetime.now().isoformat()}
        ],
        documents=[memory_request.memory],
        embeddings=[memory_embedding],
    )

    return {"status": "ok"}


@log_function_call
@app.post("/search-similar")
async def get_prompt(search_request: MemorySearchRequest):
    logger.info(f"Search request: {search_request.query}")

    remote_db = chromadb.HttpClient(
        host=os.environ.get("CHROMA_HOST"),
        port=int(os.environ.get("CHROMA_PORT", 8000)),
        ssl=os.environ.get("CHROMA_USE_SSL", "false").lower() == "true",
        settings=Settings(
            anonymized_telemetry=False,
            chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider",
            chroma_client_auth_credentials=os.environ.get("CHROMA_AUTH_TOKEN"),
        ),
    )

    protocol = (
        "https"
        if os.environ.get("OLLAMA_USE_SSL", "false").lower() == "true"
        else "http"
    )

    logger.debug("Setting up embeddings...")
    embeddings = OllamaEmbeddings(
        model="nomic-embed-text",
        base_url=f"{protocol}://{os.environ.get('OLLAMA_HOST')}:{os.environ.get('OLLAMA_PORT', 11434)}",
    )

    logger.debug("Initializing vector stores for each collection...")
    vector_stores = []
    for collection in search_request.collections:
        store = Chroma(
            client=remote_db,
            collection_name=collection,
            embedding_function=embeddings,
        )
        vector_stores.append(store)

    logger.debug("Performing similarity search across all collections...")
    all_results = []
    for vector_store, collection in zip(vector_stores, search_request.collections):
        # Generate embedding for query using our configured embeddings function
        query_embedding = embeddings.embed_query(search_request.query)

        # Get collection and perform search directly with ChromaDB
        chroma_collection = store._client.get_collection(collection)
        query_results = chroma_collection.query(
            query_embeddings=[query_embedding],
            n_results=search_request.n_results,
            include=["metadatas", "documents", "distances"],
        )

        # Process each document from raw ChromaDB results
        for idx, (doc, metadata, distance) in enumerate(
            zip(
                query_results["documents"][0],
                query_results["metadatas"][0],
                query_results["distances"][0],
            )
        ):
            result = {
                "id": query_results["ids"][0][
                    idx
                ],  # Use Chroma's document ID for current index
                "content": doc,
                "score": float(distance),  # Convert numpy float to Python float
                "metadata": metadata,
                "source": collection,
            }
            all_results.append(result)
            logger.debug(
                f"Found document (id={query_results['ids'][0][idx]}) with score {distance} in collection {collection}"
            )

    # Sort by score (lower is better) and get top n results
    results = sorted(all_results, key=lambda x: x["score"])[: search_request.n_results]

    logger.info(
        f"Returning {len(results)} documents from {len(search_request.collections)} collections"
    )
    return {"documents": results}


@log_function_call
@app.post("/search-similar-pinecone")
async def get_prompt_pinecone(search_request: PineconeMemorySearchRequest):
    logger.info(f"Search request: {search_request.query}")

    # Initialize Pinecone client
    api_key = os.environ.get("PINECONE_API_KEY")
    pinecone_client = Pinecone(api_key=api_key)
    pinecone_host = f"https://{search_request.index}{os.environ.get('PINECONE_HOST')}"
    logger.info(f"Connecting to Pinecone at {pinecone_host}")
    logger.info(f"API key: {api_key}")
    pinecone_index = pinecone_client.Index(
        search_request.index,
        host=pinecone_host,
    )
    # Get embeddings using existing Ollama setup
    protocol = (
        "https"
        if os.environ.get("OLLAMA_USE_SSL", "false").lower() == "true"
        else "http"
    )

    logger.debug("Setting up embeddings...")
    embeddings = OllamaEmbeddings(
        model="nomic-embed-text",
        base_url=f"{protocol}://{os.environ.get('OLLAMA_HOST')}:{os.environ.get('OLLAMA_PORT', 11434)}",
    )

    # Generate embedding for query
    query_embedding = embeddings.embed_query(search_request.query)

    def format_result(match, namespace):
        # Start with base result structure
        result = {
            "id": match.id,
            "score": float(match.score) if match.score is not None else 1.0,
            "source": namespace,  # Include source namespace
        }

        # Handle metadata carefully
        if match.metadata:
            # Add content from text field if it exists
            if "text" in match.metadata:
                result["content"] = match.metadata["text"]

            # Build metadata object only with fields that exist
            metadata = {}
            for field in [
                "title",
                "summary",
                "last_modified",
                "chunk_number",
                "total_chunks",
                "embedding_model",
                "embedding_provider",
                "notion_id",
            ]:
                if field in match.metadata and match.metadata[field]:
                    metadata[field] = match.metadata[field]

            # Only include metadata if we have any
            if metadata:
                result["metadata"] = metadata

            # If no content was found in text field, check other potential fields
            if "content" not in result:
                # Look for content in alternative fields
                content_fields = ["content", "body", "text", "description"]
                for field in content_fields:
                    if field in match.metadata and match.metadata[field]:
                        result["content"] = match.metadata[field]
                        break
                # If still no content, use empty string
                if "content" not in result:
                    result["content"] = ""
        else:
            # Handle case with no metadata
            result["content"] = ""
            result["metadata"] = {}

        return result

    try:
        # Get list of all namespaces in index
        stats = pinecone_index.describe_index_stats()
        namespaces = list(stats.namespaces.keys())

        logger.info(f"Found {len(namespaces)} namespaces: {namespaces}")

        # Search across all namespaces
        all_results = []
        namespace_counts = {}

        for namespace in namespaces:
            logger.info(f"Querying namespace {namespace}")
            try:
                results = pinecone_index.query(
                    namespace=namespace,
                    vector=query_embedding,
                    top_k=search_request.n_results,
                    include_metadata=True,
                )

                namespace_results = results.matches
                namespace_counts[namespace] = len(namespace_results)
                logger.info(
                    f"Found {len(namespace_results)} results in namespace {namespace}"
                )
                all_results.extend((match, namespace) for match in namespace_results)

            except Exception as e:
                logger.error(f"Error querying namespace {namespace}: {e}")
                continue

        # Sort by score (higher is better) and get top N results
        all_results.sort(
            key=lambda x: x[0].score if x[0].score is not None else 0.0, reverse=True
        )
        top_results = all_results[: search_request.n_results]

        # Format results
        formatted_results = [format_result(match, ns) for match, ns in top_results]

        logger.info(
            f"Returning {len(formatted_results)} documents from {len(namespaces)} namespaces. "
            f"Results per namespace: {namespace_counts}"
        )
        return {"documents": formatted_results}

    except Exception as e:
        logger.error(f"Error querying Pinecone: {e}")
        return {"documents": []}


@log_function_call
@app.post("/add-memory-pinecone")
async def add_memory_pinecone(memory_request: PineconeMemoryAddRequest):
    logger.info(f"Adding memory: {memory_request.memory}")

    # Initialize Pinecone client
    api_key = os.environ.get("PINECONE_API_KEY")
    pinecone_client = Pinecone(api_key=api_key)
    pinecone_host = f"https://{memory_request.index}{os.environ.get('PINECONE_HOST')}"
    logger.info(f"Connecting to Pinecone at {pinecone_host}")
    pinecone_index = pinecone_client.Index(
        memory_request.index,
        host=pinecone_host,
    )

    # Get embeddings using existing Ollama setup
    protocol = (
        "https"
        if os.environ.get("OLLAMA_USE_SSL", "false").lower() == "true"
        else "http"
    )

    logger.debug("Setting up embeddings...")
    embeddings = OllamaEmbeddings(
        model="nomic-embed-text",
        base_url=f"{protocol}://{os.environ.get('OLLAMA_HOST')}:{os.environ.get('OLLAMA_PORT', 11434)}",
    )

    try:
        # Generate embedding for memory
        memory_embedding = embeddings.embed_query(memory_request.memory)

        # Create unique ID and timestamp
        doc_id = str(uuid.uuid4())
        current_time = datetime.now().isoformat()

        # Insert into Pinecone
        pinecone_index.upsert(
            vectors=[
                {
                    "id": doc_id,
                    "values": memory_embedding,
                    "metadata": {
                        "text": memory_request.memory,
                        "date_added": current_time,
                    },
                }
            ],
            namespace="openwebui",
        )

        logger.info(f"Successfully added memory with ID: {doc_id}")
        return {"status": "ok", "id": doc_id}

    except Exception as e:
        logger.error(f"Error adding memory to Pinecone: {e}")
        return {"status": "error", "message": str(e)}
