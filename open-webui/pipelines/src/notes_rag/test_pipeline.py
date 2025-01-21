import asyncio
import json

import pytest

import notes_rag
from notes_rag.notes_rag import Pipeline

# from .notes_rag import Pipeline


def test_pipeline():

    body = json.loads(
        '{"stream": true, "model": "qwen2.5:3b", "messages": [{"role": "user", "content": "What is Azure?"}], "metadata": {"user_id": "1626c025-08dd-4b89-a9d5-2571c77b36b1", "chat_id": "96b67da6-5e9f-418d-8ef8-62bcd8ac053b", "message_id": "f50f4f7c-c79e-496d-bd31-d35994bca904", "session_id": "KkwKkkDOEP74CXRNAAAH", "tool_ids": ["memory"], "files": null, "features": {"web_search": false}}, "options": {}}'
    )
    user = json.loads(
        '{"id": "1626c025-08dd-4b89-a9d5-2571c77b36b1", "email": "timbuchinger@gmail.com", "name": "Tim", "role": "admin"}'
    )
    pipeline = Pipeline()
    body = asyncio.run(pipeline.inlet(body, user))

    pass
