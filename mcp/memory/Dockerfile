FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

COPY src/ .

RUN uv build

ENTRYPOINT ["uv", "run", "mcp_memory"]

EXPOSE 8000
