# Model Context - Memory

```bash
uv run mcp_memory_python
```

```bash
npx @modelcontextprotocol/inspector uv run mcp_memory_python
npx @modelcontextprotocol/inspector -e KEY=value -e KEY2=$VALUE2 build/index.js arg1 arg2
```

## Integration in Claude

```json
{
  "mcpServers": {
    "chroma": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/git/repo/llm-workspace/mcp/memory_python/",
        "run",
        "mcp_memory_python"
      ],
      "env": [
        "MONGO_URI": "mongodb://test:test@localhost:27017/"
      ]
    }
  }
}
```

```json
{
  `entities`: [
    {
      `name`: `Tim`,
      `entityType`: `Person`,
      `observations`: []
    }
  ]
}
```

```json
{
  "entities": [
    {
      "name": "Tim",
      "entityType": "Person",
      "observations": []
    }
  ]
}
```
