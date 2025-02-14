import logging
import os

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from langchain_ollama import OllamaEmbeddings
from mcp.server.fastmcp import FastMCP

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
        base_url=f"{protocol}://{os.environ.get('OLLAMA_HOST')}:{int(os.environ.get('OLLAMA_PORT', 11434))}",  # TODO: Make protocol configurable
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


embeddings = initialize_embeddings()
vector_store = initialize_chroma_client(embeddings)
logger.info("Retrieved existing collection 'langchain'")

mcp = FastMCP("mcp_sse")


# from mcp.server.fastmcp import FastMCP
# from mcp.transport.sse import SSEConfig, SSETransport

# # Configure SSE transport
# sse_config = SSEConfig(host="0.0.0.0", port=8000)
# transport = SSETransport(config=sse_config)

# # Create an MCP server with SSE transport
# mcp = FastMCP("mcp_sse", transport=transport)


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


@mcp.tool()
def search_similar(query: str) -> str:
    """Search for similar items"""
    num_results = 5
    # metadata_filter = arguments.get("metadata_filter")
    # content_filter = arguments.get("content_filter")

    if not query:
        raise Exception("Missing query")

    try:

        embeddings = initialize_embeddings()

        embedding_vector = embeddings.embed_query(query)
        logger.info("Embedding vector: " + str(embedding_vector))
        results = vector_store.similarity_search_by_vector_with_relevance_scores(
            embedding=embedding_vector, k=num_results
        )

        if not results or len(results) == 0:
            return [
                type.TextContent(
                    type="text", text="No documents found matching query: " + query
                )
            ]
        else:
            combined_text = " ".join([result[0].page_content for result in results])
            return combined_text

    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
        raise Exception(str(e))
    # return f"Searching for items similar to {query}"


def main():
    # mcp.run(transport="sse")
    mcp.run(transport="stdio")
