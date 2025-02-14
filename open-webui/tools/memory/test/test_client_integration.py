import os
from datetime import datetime
from typing import AsyncGenerator

import pytest
from memory.client import Tools


@pytest.mark.integration
class TestMemoryToolsIntegration:
    @pytest.mark.asyncio
    async def test_full_memory_lifecycle(self, memory_tools: Tools, server_url: str):
        # Verify server is accessible
        assert "BASE_URL" in os.environ
        assert os.environ["BASE_URL"] == server_url

        # 1. Add a memory
        content = "Integration test memory"
        tags = ["test", "integration"]
        add_result = await memory_tools.add_memory(content, tags)
        assert "successfully" in add_result.lower()
        # 2. Get all memories
        memories = await memory_tools.retrieve_all()
        assert content in memories

        # 3. Search for memory
        search_results = await memory_tools.search_memory("integration")
        assert content in search_results

        # 4. Get memory by tag
        tag_results = await memory_tools.get_by_tag(["test"])
        assert content in tag_results

        # 5. Delete memory
        delete_result = await memory_tools.delete_memory(content)
        assert "successfully" in delete_result.lower()

        # Verify deletion
        final_memories = await memory_tools.retrieve_all()
        assert not content in final_memories

    @pytest.mark.asyncio
    async def test_server_connection(self, memory_tools: Tools, server_url: str):
        """Test that the client can connect to the test server."""
        # Add a simple memory to verify connection
        result = await memory_tools.add_memory(
            "Server connection test", ["test", "connection"]
        )
        assert "successfully" in result.lower()

        # Clean up
        await memory_tools.delete_memory("Server connection test")
