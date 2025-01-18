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
        base_url=f"http://{os.environ.get('OLLAMA_URL')}:{int(os.environ.get('OLLAMA_PORT', 11434))}",  # TODO: Make protocol configurable
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
        ssl=False,  # TODO: Make configurable
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


server.command_options = {
    "search_similar": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "num_results": {"type": "integer", "minimum": 1, "default": 5},
            # "metadata_filter": {"type": "object", "additionalProperties": True},
            # "content_filter": {"type": "string"},
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
                    # "metadata_filter": {"type": "object", "additionalProperties": True},
                    # "content_filter": {"type": "string"},
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
            base_url=f"https://{os.environ.get('OLLAMA_URL')}:{int(os.environ.get('OLLAMA_PORT', 11434))}",
            model="nomic-embed-text",
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


def main():
    logger.info("Server is starting up")

    # client = MongoClient(MONGO_URI)
    # db = client[DATABASE_NAME]

    # if ENTITIES_COLLECTION not in db.list_collection_names():
    #     logger.info("Creating entities collection")
    #     db.create_collection(ENTITIES_COLLECTION)

    # if RELATIONS_COLLECTION not in db.list_collection_names():
    #     logger.info("Creating relations collection")
    #     db.create_collection(RELATIONS_COLLECTION)

    # async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
    #     await server.run(
    #         read_stream,
    #         write_stream,
    #         InitializationOptions(
    #             server_name="mcp_memory",
    #             server_version="0.1.0",
    #             capabilities=server.get_capabilities(
    #                 notification_options=NotificationOptions(),
    #                 experimental_capabilities={},
    #             ),
    #         ),
    #     )

    transport = "sse"
    if transport == "sse":
        logger.info("Using SSE transport")

        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route

        sse = SseServerTransport("/messages/")

        async def handle_sse(request):
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await server.run(
                    streams[0], streams[1], server.create_initialization_options()
                )

        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=handle_sse),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        import uvicorn

        # from fastapi import HTTPException, Request
        # async def validate_bearer_token(request: Request):
        #     auth_header = request.headers.get("Authorization")
        #     if auth_header is None or not auth_header.startswith("Bearer "):
        #         raise HTTPException(status_code=401, detail="Invalid or missing token")
        #     token = auth_header.split(" ")[1]
        #     # Add your token validation logic here
        #     if token != "your_expected_token":
        #         raise HTTPException(status_code=401, detail="Invalid token")
        # starlette_app.add_middleware(validate_bearer_token)
        port = os.environ.get("SSE_PORT", 8000)
        logger.info(f"Starting uvicorn on port {port}")
        uvicorn.run(starlette_app, host="0.0.0.0", port=int(port))
    else:
        logger.info("Using stdio transport")
        from mcp.server.stdio import stdio_server

        async def arun():
            async with stdio_server() as streams:
                await server.run(
                    streams[0], streams[1], server.create_initialization_options()
                )

        anyio.run(arun)

    return 0


# async def main():
#     async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
#         await server.run(
#             read_stream,
#             write_stream,
#             InitializationOptions(
#                 server_name="mcp_chroma",
#                 server_version="0.1.0",
#                 capabilities=server.get_capabilities(
#                     notification_options=NotificationOptions(),
#                     experimental_capabilities={},
#                 ),
#             ),
#         )


# if __name__ == "__main__":
#     print("found it")
#     arguments = {"query": "AWS"}
#     print(handle_search_similar_sync(arguments))
