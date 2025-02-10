# Technical Context

## Technology Stack
### Frontend
- Vue.js 3 with Composition API
- Pinia for state management
- WebSocket client for streaming
- TypeScript

### Backend
- FastAPI
- WebSockets for streaming
- JWT authentication
- LangGraph for agent orchestration
- LangChain for vector store integration
- LiteLLM for LLM provider management

### Database
- PostgreSQL for:
  - User management
  - Conversation history
  - System state
- Chroma for vector storage:
  - Notion knowledge base (read-only)
  - Agent memories (read-write)

### Infrastructure
- LangFuse for observability
- CLI tools for user management

## Development Setup
### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL
- Chroma DB
- LangFuse account
- LLM API keys (OpenAI, Anthropic, etc.)

### Environment Setup
```bash
# Backend
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn langchain langgraph chromadb psycopg2-binary python-jose[cryptography] python-multipart litellm langfuse

# Frontend
npm create vue@latest
cd frontend
npm install pinia vue-router @vueuse/core
```

### Configuration
Required environment variables:
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
CHROMA_NOTION_PATH=/path/to/notion/db
CHROMA_MEMORY_PATH=/path/to/memory/db

# Authentication
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256

# LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...

# Monitoring
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
```

## Dependencies
### Core Dependencies
- FastAPI: Web framework
- LangGraph: Agent orchestration
- LangChain: Vector store integration
- Chroma: Vector database
- PostgreSQL: Relational database
- LiteLLM: LLM provider management
- LangFuse: Observability

### Development Dependencies
- uvicorn: ASGI server
- pytest: Testing
- httpx: Async HTTP client
- Vue DevTools
- TypeScript

## Technical Constraints
- JWT for simple authentication
- No mid-conversation model switching initially
- Manual user management via CLI
- Read-only access to Notion vector store

## API Documentation
- FastAPI automatic docs at /docs
- WebSocket endpoint at /ws/chat
- REST endpoints:
  - /auth/login (POST)
  - /providers/list (GET)
  - /conversations (GET, POST)
  - /memories (GET, POST, DELETE)

## Build Process
```bash
# Backend
uvicorn main:app --reload

# Frontend
npm run dev
```

## Deployment
- Backend: uvicorn with gunicorn
- Frontend: Static file hosting
- Databases: Managed PostgreSQL and Chroma instances
- Environment variables for configuration

## Monitoring & Logging
- LangFuse for:
  - Request tracking
  - Response monitoring
  - Error logging
  - Performance metrics
  - Cost tracking

## Security Considerations
- JWT authentication
- CORS configuration
- Environment variable protection
- API key security
- No public registration
- Manual user management
