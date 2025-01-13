# Model Context - Memory

```bash
uv run mcp_memory_python
```

```bash
npx @modelcontextprotocol/inspector uv run mcp_chroma
```

## Integration in Claude

```json
{
  "mcpServers": {
    "chroma": {
      "command": "uv",
      "args": [
        "--directory",
        "~/git/llm-workspace/mcp/memory_python/",
        "run",
        "mcp_memory_python"
      ]
    }
  }
}
```
