import logging
import os
from typing import List, Optional

import chromadb
import uvicorn
from chromadb.config import Settings
from dotenv import load_dotenv
from fastapi import FastAPI

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
app = FastAPI()

from pydantic import BaseModel


class PromptQuery(BaseModel):
    question: str


@app.post("/prompt")
async def read_prompt(query: PromptQuery):
    # user_message = get_last_user_message(body["messages"])
    print(query.question)

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

    chroma_collection = remote_db.get_collection("langchain")
    # vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

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

    query_embedding = embed_model.get_query_embedding("AWS and EKS")  # user_message)
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
    template = template.replace("[USER_MESSAGE]", question)

    print("===================Prompt===================")
    print(template)
    print("============================================")

    # print(f"Message count: {len(body['messages'])}")
    # raise Exception("Error")
    # body["messages"][0]["content"] = template
    # return body
    return {"prompt": template}


# return {
#     "prompt": f"CONTEXT:\nThe deployment date to AWS will be Friday January 31st, 2025.\nQUESTION:\n{question}"
# }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
