from mcp.server.fastmcp import FastMCP

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
