import logging
import os
import sys
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from functools import wraps
from typing import List

import chromadb
from chromadb.config import Settings

# from custom_logging_filter import HealthCheckFilter
from dotenv import load_dotenv
from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Response,
    status,
)

# from llama_index import SimpleKeywordTableIndex
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from pydantic import BaseModel, Field

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))


class HealthCheckFilter(logging.Filter):
    def filter(self, record):
        return "/healthz" not in record.getMessage()


logging.basicConfig(
    stream=sys.stderr,
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
)
logger = logging.getLogger("tools_memory")
# logger.addFilter(HealthCheckFilter())


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


class HealthCheck:
    def __init__(self):
        self._ready = False
        self._db_initialized = False
        # Add more initialization flags as needed

    @property
    def ready(self):
        return self._ready and self._db_initialized

    def set_db_status(self, status: bool):
        self._db_initialized = status

    def mark_ready(self):
        self._ready = True


health_check = HealthCheck()


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Database initialization
#     engine = create_async_engine("your_database_url")

#     try:
#         # Test database connection
#         async with engine.connect() as conn:
#             await conn.execute(text("SELECT 1"))
#         health_check.set_db_status(True)
#     except Exception as e:
#         print(f"Database initialization failed: {e}")
#         health_check.set_db_status(False)

#     # Mark the application as ready after all initializations
#     health_check.mark_ready()

#     yield

#     # Cleanup
#     await engine.dispose()


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


class Memory(BaseModel):
    """
    Represents a memory item to be stored in ChromaDB.
    """

    id: str | None = None
    content: str
    tags: List[str]
    date: datetime

    def __init__(
        self, content: str, tags: List[str] = None, date: datetime = datetime.now()
    ):
        super().__init__(content=content, tags=tags if tags else [], date=date)

    def __str__(self):
        truncated_content = (
            self.content if len(self.content) <= 20 else self.content[:20] + "..."
        )
        return (
            f"Memory(content={truncated_content}, tags={self.tags}, date={self.date})"
        )


class MemoryRequest(BaseModel):
    content: str = Field(..., min_length=1)
    tags: List[str] = None
    chroma_collection_name: str


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    chroma_collection_name: str


class DeleteRequest(BaseModel):
    content: str
    chroma_collection_name: str


class TagsRequest(BaseModel):
    tags: List[str]
    chroma_collection_name: str

    # def __init__(self, tags: List[str], chroma_collection_name: str):
    #     super().__init__(tags=tags, chroma_collection_name=chroma_collection_name)


class GetAllRequest(BaseModel):
    chroma_collection_name: str


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
        health_check.set_db_status(True)
        health_check.mark_ready()

    def get_chroma_collection(self, chroma_collection_name: str):
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

        # collection = os.environ.get("CHROMA_COLLECTION")
        # if not collection:
        #     raise ValueError("CHROMA_COLLECTION environment variable is not set")
        # # self.chroma_collection = remote_db.get_or_create_collection(collection)
        return remote_db.get_collection(chroma_collection_name)

    @log_function_call
    def add_memory(self, memory: Memory, chroma_collection_name: str):
        logger.info(f"Adding memory: {memory}")
        embedding = self.embedding.get_text_embedding(memory.content)
        chroma_collection = self.get_chroma_collection(chroma_collection_name)
        chroma_collection.add(
            ids=[str(uuid.uuid4())],
            metadatas=[
                {"tags": ",".join(memory.tags), "date": memory.date.isoformat()}
            ],
            documents=[memory.content],
            embeddings=[embedding],
        )

    @log_function_call
    def delete_memory(self, content: str, chroma_collection_name: str):
        chroma_collection = self.get_chroma_collection(chroma_collection_name)
        chroma_collection.delete(where={"document": content})

    @log_function_call
    def search_memory(self, query: str, chroma_collection_name: str) -> List[Memory]:
        embedding = self.embedding.get_query_embedding(query)
        chroma_collection = self.get_chroma_collection(chroma_collection_name)

        response = []
        try:
            docs = chroma_collection.query(query_embeddings=embedding, n_results=3)
            for index, document in enumerate(docs["documents"][0]):
                response.append(
                    Memory(
                        content=document,
                        tags=docs["metadatas"][0][index]["tags"].split(","),
                        date=datetime.fromisoformat(
                            docs["metadatas"][0][index]["date"]
                        ),
                    )
                )
        except Exception as e:
            logger.exception(f"Error querying ChromaDB: {e}")
            raise HTTPException(status_code=500, detail="Error querying ChromaDB")
        return response

    @log_function_call
    def retrieve_all(self, chroma_collection_name: str) -> List[Memory]:
        chroma_collection = self.get_chroma_collection(chroma_collection_name)
        response = []
        try:
            docs = chroma_collection.get()
            for index, document in enumerate(docs["documents"]):
                response.append(
                    Memory(
                        content=document,
                        tags=docs["metadatas"][index]["tags"].split(","),
                        date=datetime.fromisoformat(docs["metadatas"][index]["date"]),
                    )
                )
        except Exception as e:
            logger.exception(f"Error querying ChromaDB: {e}")
            raise HTTPException(status_code=500, detail="Error querying ChromaDB")
        return response

    @log_function_call
    def get_by_tag(self, tags: List[str], chroma_collection_name: str):
        # chroma_collection = self.get_chroma_collection(chroma_collection)
        docs = self.retrieve_all(chroma_collection_name)

        response = []

        for doc in docs:
            logger.debug(f"Checking tags: {doc.tags}")
            if any(i.strip() in doc.tags for i in tags):
                response.append(doc)
        return response


tools = MemoryTools()


@api_router.get("/healthz")
async def healthz(response: Response):
    # return {"status": "ok"}
    if not health_check.ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "unavailable",
            "details": {
                "ready": health_check._ready,
                "database": health_check._db_initialized,
            },
        }

    return {"status": "ok"}


@log_function_call
@api_router.post("/add_memory")
def add_memory(memory_request: MemoryRequest):
    memory = Memory(content=memory_request.content, tags=memory_request.tags)
    try:
        tools.add_memory(memory, memory_request.chroma_collection_name)
        return {"status": "success", "message": "Memory added successfully"}
    except Exception as e:
        logger.exception(e, stack_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@log_function_call
@api_router.delete("/delete_memory")
def delete_memory(delete_request: DeleteRequest):
    try:
        tools.delete_memory(
            delete_request.content, delete_request.chroma_collection_name
        )
        return {"status": "success", "message": "Memory deleted successfully"}
    except Exception as e:
        logger.exception(e, stack_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@log_function_call
@api_router.post("/search_memory")
def search_memory(query_request: QueryRequest):
    try:
        results = tools.search_memory(
            query_request.query, query_request.chroma_collection_name
        )
        return {"memories": results}
    except Exception as e:
        logger.exception(e, stack_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@log_function_call
@api_router.post("/retrieve_all")
def retrieve_all(get_all_request: GetAllRequest):
    try:
        return {"memories": tools.retrieve_all(get_all_request.chroma_collection_name)}
    except Exception as e:
        logger.exception(e, stack_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@log_function_call
@api_router.post("/get_by_tag")
def get_by_tag(tags_request: TagsRequest):
    try:
        results = tools.get_by_tag(
            tags_request.tags, tags_request.chroma_collection_name
        )
        return {"memories": results}
    except Exception as e:
        logger.exception(e, stack_info=True)
        raise HTTPException(status_code=500, detail=str(e))


app.include_router(api_router, dependencies=[Depends(log_request_info)])
