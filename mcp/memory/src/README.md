# Model Context - Memory

```bash
uv run mcp_memory
```

```bash
npx @modelcontextprotocol/inspector uv run mcp_memory
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
        "/path/to/git/repo/llm-workspace/mcp/memory/",
        "run",
        "mcp_memory"
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
  `contents`: [
    `Lives in a cave`,
    `Likes long walks on the beach`
  ],
  `entity_name`: `Someone`
}
```
