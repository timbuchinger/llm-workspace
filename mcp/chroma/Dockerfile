FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

COPY src/ .
RUN rm -f mcp_chroma/.env

RUN uv build

ENTRYPOINT ["uv", "run", "mcp_chroma"]

EXPOSE 8000
