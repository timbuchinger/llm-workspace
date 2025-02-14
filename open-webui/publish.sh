#!/bin/bash
mc cp pipelines/rag/rag/rag_notes.py storage/llm-pipelines/rag_notes.py

mc cp pipelines/rag/requirements.txt storage/llm-servers/pipelines-rag/requirements.txt
mc cp pipelines/rag/rag/logging.yaml storage/llm-servers/pipelines-rag/logging.yaml
mc cp pipelines/rag/rag/notes_rag_prompt.txt storage/llm-servers/pipelines-rag/notes_rag_prompt.txt
mc cp pipelines/rag/rag/server.py storage/llm-servers/pipelines-rag/server.py

mc cp tools/memory/requirements.txt storage/llm-servers/tools-memory/requirements.txt
mc cp tools/memory/memory/logging.yaml storage/llm-servers/tools-memory/logging.yaml
mc cp tools/memory/memory/server.py storage/llm-servers/tools-memory/server.py

read -p "Do you want to restart the LLM servers? (Y/n): " answer
answer=${answer:-Y}

if [[ $answer =~ ^[Yy]$ ]]; then
  echo "Restarting servers..."
  kubectl rollout restart deployment tools-memory-deployment -n open-webui
  kubectl rollout restart deployment pipelines-rag-deployment -n open-webui
else
  echo "Servers not restarted."
fi

read -p "Do you want to restart the Open-WebUI pipeline server? (Y/n): " answer
answer=${answer:-Y}

if [[ $answer =~ ^[Yy]$ ]]; then
  echo "Restarting servers..."
  kubectl rollout restart deployment open-webui-pipelines -n open-webui
else
  echo "Servers not restarted."
fi