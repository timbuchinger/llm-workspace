import os
from datetime import datetime
from typing import List

from fastapi import FastAPI, HTTPException

# from llama_index import SimpleKeywordTableIndex
from llama_index.embeddings.ollama import OllamaEmbedding

# from llama_index.vector_stores import ChromaVectorStore
from pydantic import BaseModel

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
        chroma_use_ssl = os.getenv("CHROMA_USE_SSL", "false").lower() == "true"
        chroma_protocol = "https" if chroma_use_ssl else "http"
        chroma_url = f"{chroma_protocol}://{os.getenv("CHROMA_URL")}:{os.getenv('CHROMA_PORT', 8000)}"

        ollama_use_ssl = os.getenv("OLLAMA_USE_SSL", "false").lower() == "true"
        ollama_protocol = "https" if ollama_use_ssl else "http"
        ollama_url = f"{ollama_protocol}://{os.getenv("OLLAMA_URL")}:{os.getenv('OLLAMA_PORT', 11434)}"

        if not chroma_url or not ollama_url:
            raise ValueError(
                "CHROMA_URL and OLLAMA_URL environment variables must be set."
            )

        embedding = OllamaEmbedding(model_name="nomic-text-embed", endpoint=ollama_url)
        # self.vector_store = ChromaVectorStore(
        #     endpoint=chroma_url, embedding_model=embedding
        # )
        # set collection
        # self.index = SimpleKeywordTableIndex(vector_store=self.vector_store)

    def add_memory(self, memory: Memory):
        documents = [
            {
                "content": memory.content,
                "metadata": {"tags": memory.tags, "date": memory.date.isoformat()},
            }
        ]
        self.index.insert(documents)

    def delete_memory(self, content: str):
        self.index.vector_store.delete(content=content)

    def search_memory(self, query: str):
        return self.index.query(query, top_k=3)

    def retrieve_all(self):
        return self.index.vector_store.get_all()

    def get_by_tag(self, tags: List[str]):
        return [
            doc
            for doc in self.retrieve_all()
            if any(tag.lower() in doc["metadata"]["tags"] for tag in tags)
        ]


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
