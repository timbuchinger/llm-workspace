# Project Brief

## Overview
A vector-enabled agent system that interfaces with two Chroma databases: one for read-only access to Notion exports and another for read-write access to agent memories. The agent will perform semantic search across both databases to answer user queries.

## Core Requirements
- Dual vector database integration (Chroma)
  - Read-only Notion knowledge base
  - Read-write agent memories
- Vue.js frontend with chat interface
- FastAPI backend
- LangGraph for agent orchestration
- Pluggable LLM providers via LiteLLM
- JWT authentication for small user base
- WebSocket support for streaming responses
- LangFuse monitoring integration

## Project Goals
- Create an intelligent agent that can leverage both static knowledge and learned memories
- Provide a seamless chat interface for all interactions
- Enable flexible LLM provider selection
- Maintain high observability with LangFuse
- Support multiple users with basic authentication

## Scope
### In Scope
- Basic chat interface with model selection
- Vector search across both databases
- Memory management through natural language
- User authentication with JWT
- CLI tools for user management
- WebSocket streaming support
- Basic error handling and monitoring

### Out of Scope
- Self-service user registration
- Password reset functionality
- Mid-conversation model switching (initial version)
- Provider-specific settings management
- Token usage tracking

## Success Criteria
- Agent can effectively search both vector databases
- Users can select different LLM providers
- Real-time streaming of responses works reliably
- Basic authentication system functions
- LangFuse monitoring provides useful insights

## Timeline
Phase 1: Basic End-to-End POC (2-3 days)
- Simple working system with basic functionality

Phase 2: Authentication & Data Persistence (1-2 days)
- User management and conversation history

Phase 3: Vector Store Integration (2-3 days)
- Full database integration and memory management

Phase 4: Multi-LLM Support (1-2 days)
- LiteLLM integration and model selection

Phase 5: Monitoring & Polish (2-3 days)
- LangFuse integration and final improvements

Total Timeline: 8-13 days for working MVP

## Key Stakeholders
- Project maintainers
- End users requiring access to Notion knowledge base
- System administrators managing user access
