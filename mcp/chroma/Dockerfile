FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app
# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy
COPY src/ .
RUN rm -f mcp_chroma/.env

# RUN uv sync
RUN uv sync
#--frozen --no-install-project --no-dev

ENTRYPOINT ["uv", "run", "mcp_chroma"]

EXPOSE 8000
