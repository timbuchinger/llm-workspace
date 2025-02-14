FROM python:3.12-slim-bookworm

WORKDIR /app

COPY pipelines/rag/requirements.txt requirements-pipelines.txt
COPY tools/memory/requirements.txt requirements-memory.txt

RUN pip install --no-cache-dir -r requirements-pipelines.txt
RUN pip install --no-cache-dir -r requirements-memory.txt
