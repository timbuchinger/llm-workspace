# Model Context - Chroma

```bash
uv run mcp_chroma
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
        "~/git/llm-workspace/mcp/chroma/",
        "run",
        "mcp_chroma"
      ]
    }
  }
}
```
