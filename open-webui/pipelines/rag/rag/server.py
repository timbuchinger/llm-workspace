import logging
import os
from functools import wraps
from typing import Optional

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
from fastapi import FastAPI

# from llama_index.embeddings import OllamaEmbedding
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
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


class PromptQuery(BaseModel):
    question: str


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@log_function_call
@app.post("/prompt")
async def get_prompt(query: PromptQuery, n_results: Optional[int] = 3):
    # user_message = get_last_user_message(body["messages"])
    logger.info(query.question)

    question = query.question

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

    chroma_collection = remote_db.get_collection("notion")
    # vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    protocol = (
        "https"
        if os.environ.get("OLLAMA_USE_SSL", "false").lower() == "true"
        else "http"
    )
    logger.debug("Setting up embeddings...")
    embed_model = OllamaEmbedding(
        model_name="nomic-embed-text",
        base_url=f"{protocol}://{os.environ.get('OLLAMA_HOST')}:{os.environ.get('OLLAMA_PORT', 11434)}",
        # ollama_additional_kwargs={"mirostat": 0},
    )

    logger.debug("Getting query embedding...")
    query_embedding = embed_model.get_query_embedding(question)
    results = chroma_collection.query(
        query_embeddings=query_embedding, n_results=n_results
    )

    document_text = ""
    logger.info("Search results:")
    for result_id, result in enumerate(results["documents"][0]):
        logger.info(f"Result {result_id + 1}:")
        document_text += (
            f"\nDocumentID: {results['ids'][0][result_id]}\nContent: {result}"
        )
        logger.info(f"Document: {result}")
        logger.info(f"Metadata: {results['metadatas'][0][result_id]}")
        logger.info(f"Score: {results['distances'][0][result_id]}\n")

    logger.info("Loading prompt template...")
    with open(
        os.path.join(os.path.dirname(__file__), "notes_rag_prompt.txt"), "r"
    ) as file:
        template = file.read()

    template = template.replace("[DOCUMENT_TEXT]", document_text)
    template = template.replace("[USER_MESSAGE]", question)

    logger.info("===================Prompt===================")
    logger.info(template)
    logger.info("============================================")

    return {"prompt": template}
