import logging
import os

import chromadb
import mcp.server.stdio
import mcp.types as types
from chromadb.config import Settings
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from langchain_ollama import OllamaEmbeddings
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


load_dotenv()


def initialize_embeddings():
    embeddings = OllamaEmbeddings(
        base_url=f"https://{os.environ.get('OLLAMA_URL')}", model="nomic-embed-text"
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
        port="443",
        ssl=True,
    )
    chroma_client.heartbeat()

    chroma_client.get_or_create_collection("langchain")

    vector_store = Chroma(
        client=chroma_client,
        collection_name="langchain",
        embedding_function=embeddings,
    )
    return vector_store


embeddings = initialize_embeddings()
vector_store = initialize_chroma_client(embeddings)
logger.info("Retrieved existing collection 'langchain'")


server = Server("mcp_chroma")

# Server command options
server.command_options = {
    "search_similar": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "num_results": {"type": "integer", "minimum": 1, "default": 5},
            "metadata_filter": {"type": "object", "additionalProperties": True},
            "content_filter": {"type": "string"},
        },
        "required": ["query"],
    },
}


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools for document operations."""
    return [
        types.Tool(
            name="search_similar",
            description="Search for semantically similar documents in the Chroma vector database",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "num_results": {"type": "integer", "minimum": 1, "default": 5},
                    "metadata_filter": {"type": "object", "additionalProperties": True},
                    "content_filter": {"type": "string"},
                },
                "required": ["query"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    """Handle document operations."""
    if not arguments:
        arguments = {}
    try:
        return await handle_search_similar(arguments)

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


async def handle_search_similar(arguments: dict) -> list[types.TextContent]:
    return handle_search_similar_sync(arguments)


def handle_search_similar_sync(arguments: dict) -> list[types.TextContent]:
    """Handle similarity search with retry logic"""
    query = arguments.get("query")
    num_results = arguments.get("num_results", 5)
    # metadata_filter = arguments.get("metadata_filter")
    # content_filter = arguments.get("content_filter")

    if not query:
        raise Exception("Missing query")

    try:

        query_params = {
            "query_texts": [query],
            "n_results": num_results,
            "include": ["documents", "metadatas", "distances"],
        }

        embeddings = OllamaEmbeddings(
            base_url=f"https://{os.environ.get('OLLAMA_URL')}", model="nomic-embed-text"
        )

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
            return [
                types.TextContent(
                    type="text",
                    text=f"* [SIM={score:3f}] [Content={res.page_content}] [Metadata={res.metadata}]",
                )
                for res, score in results
            ]

    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
        raise Exception(str(e))


async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp_chroma",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    print("found it")
    arguments = {"query": "AWS"}
    print(handle_search_similar_sync(arguments))
