# Memory

```json
"memory": {
  "base_url": "http://localhost:3000/sse",
  "api_key": "None"
},
```

```bash
docker build -t memory -f Dockerfile .
docker run -it --rm -p 3001:3001 memory
```

{
  `entities`: [
    {
      `name`: `Tim`,
      `entityType`: `Person`,
      `observations`: []
    }
  ]
}
