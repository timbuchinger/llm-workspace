import logging
import os
from datetime import datetime
import sys
from typing import List
import uuid
from fastapi import FastAPI, HTTPException
import chromadb

from chromadb.config import Settings

# from llama_index import SimpleKeywordTableIndex
from llama_index.embeddings.ollama import OllamaEmbedding

from llama_index.vector_stores.chroma import ChromaVectorStore
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
)
logger = logging.getLogger("tools_memory")

app = FastAPI()


class Memory:
    """
    Represents a memory item to be stored in ChromaDB.
    """

    def __init__(self, content: str, tags: List[str] = None):
        self.content = content
        self.tags = tags if tags else ["default"]
        self.date = datetime.now()


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
        # chroma_use_ssl = os.getenv("CHROMA_USE_SSL", "false").lower() == "true"
        # chroma_protocol = "https" if chroma_use_ssl else "http"
        # chroma_url = f"{chroma_protocol}://{os.getenv("CHROMA_URL")}:{os.getenv('CHROMA_PORT', 8000)}"

        ollama_use_ssl = os.getenv("OLLAMA_USE_SSL", "false").lower() == "true"
        ollama_protocol = "https" if ollama_use_ssl else "http"
        ollama_url = f"{ollama_protocol}://{os.getenv("OLLAMA_HOST")}:{os.getenv('OLLAMA_PORT', 11434)}"

        # if not ollama_url:
        #     raise ValueError(
        #         "CHROMA_HOST and OLLAMA_HOST environment variables must be set."
        #     )
        logger.info(f"Ollama URL: {ollama_url}")
        self.embedding = OllamaEmbedding(
            model_name="nomic-embed-text", base_url=ollama_url
        )
        # self.vector_store = ChromaVectorStore()
        # self.vector_store = ChromaVectorStore(
        #     chroma_collection="memories",
        #     host=os.getenv("CHROMA_URL"),
        #     port=os.getenv("CHROMA_PORT", "8000"),
        #     ssl=chroma_use_ssl,
        #     embedding_model=embedding,
        # )
        # print(os.environ.get("CHROMA_HOST"))
        # print(os.environ.get("CHROMA_PORT"))
        # print(os.environ.get("CHROMA_USE_SSL"))
        # print(os.environ.get("CHROMA_AUTH_TOKEN"))
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
        # remote_db.create_collection("memories")
        self.chroma_collection = remote_db.get_collection("memories")

        # self.index = SimpleKeywordTableIndex(vector_store=self.vector_store)

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
        self.chroma_collection.delete(where_document={"equals": content})

    def search_memory(self, query: str):
        embedding = self.embedding.get_query_embedding(query)
        return self.chroma_collection.query(query_embeddings=embedding, n_results=3)

    def retrieve_all(self):
        return self.chroma_collection.get()

    def get_by_tag(self, tags: List[str]):
        docs = self.retrieve_all()
        # print(docs)
        # for index, test in enumerate(docs):
        #     if "tags" in docs["metadatas"][index]:
        #         if any(
        #             tag.lower() in docs["metadatas"][index]["tags"].split(",")
        #             for tag in tags
        #         ):
        #             print("found match")
        #             print(docs["documents"][index])

        for index, document in enumerate(docs["documents"]):
            metadata = docs["metadatas"][index]
            print(f"Document: {document}")
            print(f"metadata: {metadata}")
            for i in metadata:
                print(i)
            # if any(item == "tags" for item in metadata):
            #     print("Found tags")
            if any(tag.lower() in metadata["tags"] for tag in tags):
                print("Found match")

        # return [
        #     doc
        #     for doc in self.retrieve_all()
        #     if any(tag.lower() in doc["metadata"]["tags"] for tag in tags)
        # ]


tools = MemoryTools()


@app.post("/add_memory")
def add_memory(memory_request: MemoryRequest):
    memory = Memory(content=memory_request.content, tags=memory_request.tags)
    try:
        tools.add_memory(memory)
        return {"message": "Memory added successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/delete_memory")
def delete_memory(content: str):
    try:
        tools.delete_memory(content)
        return {"message": "Memory deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search_memory")
def search_memory(query_request: QueryRequest):
    try:
        results = tools.search_memory(query_request.query)
        return {"results": results}
    except Exception as e:
        logger.exception(e, stack_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/retrieve_all")
def retrieve_all():
    try:
        return {"memories": tools.retrieve_all()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/get_by_tag")
def get_by_tag(tags_request: TagsRequest):
    try:
        results = tools.get_by_tag(tags_request.tags)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
