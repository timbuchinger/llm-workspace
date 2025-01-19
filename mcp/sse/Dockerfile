FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
RUN apt-get update && apt-get install -y curl
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
SHELL ["/bin/bash", "--login" , "-c"]

RUN nvm install 22
RUN npm install -y npx

ENV UV_LINK_MODE=copy
COPY src/ .
RUN rm -f mcp_sse/.env

RUN uv sync
RUN uv tool install mcp-proxy
mcp-proxy http://localhost:8080/sse
ENTRYPOINT ["npx", "-y", "supergateway", "--stdio", "uv", "run", "mcp_sse"]
EXPOSE 8000
