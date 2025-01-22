import logging
import os
import sys
import uuid
from datetime import datetime
from typing import List

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request

# from llama_index import SimpleKeywordTableIndex
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from pydantic import BaseModel

load_dotenv()

logging.basicConfig(
    stream=sys.stderr,
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
)
logger = logging.getLogger("tools_memory")

app = FastAPI()
api_router = APIRouter()


async def log_request_info(request: Request):
    if request.method not in ("POST", "PUT", "PATCH"):
        return
    request_body = await request.json()

    logger.info(
        f"{request.method} request to {request.url} metadata\n"
        f"\tHeaders: {request.headers}\n"
        f"\tBody: {request_body}\n"
        f"\tPath Params: {request.path_params}\n"
        f"\tQuery Params: {request.query_params}\n"
        f"\tCookies: {request.cookies}\n"
    )


class Memory:
    """
    Represents a memory item to be stored in ChromaDB.
    """

    def __init__(
        self, content: str, tags: List[str] = None, date: datetime = datetime.now()
    ):
        self.content = content
        self.tags = tags if tags else ["default"]
        self.date = date


class MemoryRequest(BaseModel):
    content: str
    tags: List[str] = None


class QueryRequest(BaseModel):
    query: str


class TagsRequest(BaseModel):
    tags: List[str]


class MemoryTools:
    """
    A set of tools to manage memories stored in ChromaDB using LlamaIndex.
    """

    def __init__(self):

        ollama_use_ssl = os.getenv("OLLAMA_USE_SSL", "false").lower() == "true"
        ollama_protocol = "https" if ollama_use_ssl else "http"
        ollama_url = f"{ollama_protocol}://{os.getenv("OLLAMA_HOST")}:{os.getenv('OLLAMA_PORT', 11434)}"

        logger.info(f"Ollama URL: {ollama_url}")
        self.embedding = OllamaEmbedding(
            model_name="nomic-embed-text", base_url=ollama_url
        )

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

        self.chroma_collection = remote_db.get_collection("memories")

    def add_memory(self, memory: Memory):
        embedding = self.embedding.get_text_embedding(memory.content)
        self.chroma_collection.add(
            ids=[str(uuid.uuid4())],
            metadatas=[
                {"tags": ",".join(memory.tags), "date": memory.date.isoformat()}
            ],
            documents=[memory.content],
            embeddings=[embedding],
        )

    def delete_memory(self, content: str):
        self.chroma_collection.delete(where_document={"$and": content})

    def search_memory(self, query: str):
        embedding = self.embedding.get_query_embedding(query)
        # return self.chroma_collection.query(query_embeddings=embedding, n_results=3)

        response = []
        docs = self.chroma_collection.query(query_embeddings=embedding, n_results=3)
        for index, document in enumerate(docs["documents"]):
            response.append(docs["documents"][index])

        return response

    def retrieve_all(self):
        # return self.chroma_collection.get()
        response = []
        docs = self.chroma_collection.get()
        for index, document in enumerate(docs["documents"]):
            response.append(docs["documents"][index])

        return response

    def get_by_tag(self, tags: List[str]):
        docs = self.retrieve_all()

        response = []

        for index, document in enumerate(docs["documents"]):
            metadata = docs["metadatas"][index]
            # print(f"Document: {document}")
            # print(f"metadata: {metadata}")
            if any(i.strip() in metadata["tags"].split(",") for i in tags):
                # if bool(set(metadata["tags"].split(",").strip()) & set(tags)):
                response.append(document)
        return response


tools = MemoryTools()


@api_router.post("/add_memory")
def add_memory(memory_request: MemoryRequest):
    memory = Memory(content=memory_request.content, tags=memory_request.tags)
    try:
        tools.add_memory(memory)
        return {"message": "Memory added successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/delete_memory")
def delete_memory(content: str):
    try:
        tools.delete_memory(content)
        return {"message": "Memory deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/search_memory")
def search_memory(query_request: QueryRequest):
    try:
        results = tools.search_memory(query_request.query)
        return {"memories": results}
    except Exception as e:
        logger.exception(e, stack_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/retrieve_all")
def retrieve_all():
    try:
        return {"memories": tools.retrieve_all()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/get_by_tag")
def get_by_tag(tags_request: TagsRequest):
    try:
        results = tools.get_by_tag(tags_request.tags)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


app.include_router(api_router, dependencies=[Depends(log_request_info)])
