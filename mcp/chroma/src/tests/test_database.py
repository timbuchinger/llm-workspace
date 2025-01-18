import asyncio
import json

import mcp_chroma.server
from dotenv import load_dotenv
from mcp_chroma import server

load_dotenv()


def test_list_tools():
    tools = asyncio.run(server.list_tools())
    assert len(tools) == 1


def test_create_entity():
    name = "search_similar"
    s = """{
            "query": "Tell me about AWS and EKS",
            "num_results": 5
            }"""
    args = json.loads(s)

    server = mcp_chroma.server
    result = asyncio.run(server.handle_call_tool(name, args))
    text = result[0].text
    assert (
        text
        == '{"name": "entity1", "entity_type": "tool", "observations": ["observation3", "observation4"]}'
    )

    # assert 1 == setup_database[ENTITIES_COLLECTION].count_documents({})
