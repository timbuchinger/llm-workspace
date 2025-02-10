# Product Context

## Problem Statement
Users need to efficiently access and combine information from:
1. A static knowledge base (Notion exports)
2. Dynamic learned information (agent memories)

The system should provide this through a natural conversation interface while maintaining flexibility in LLM provider choice.

## User Experience Goals
- Natural conversation interface for all interactions
- Seamless integration of knowledge and memories
- Simple model selection at conversation start
- Real-time streaming responses
- Clean, intuitive chat UI
- Minimal authentication friction

## Core User Flows

### Authentication
1. User accesses system
2. Simple login form appears
3. Enter credentials
4. Redirect to chat interface

### Starting a Conversation
1. User selects LLM model from dropdown
2. Initiates chat with question/prompt
3. Agent processes request
4. Real-time streaming of response
5. Conversation history maintained

### Knowledge Retrieval
1. User asks question
2. Agent searches both vector stores in parallel
3. Combines relevant information
4. Generates coherent response
5. Streams response in real-time

### Memory Management
1. User can request to store new memories
2. User can query existing memories
3. User can request memory deletion
4. All through natural language commands

## User Personas

### Knowledge Worker
- Needs quick access to Notion knowledge base
- Values accurate information retrieval
- Appreciates conversation history
- May switch between different models

### System Administrator
- Manages user access via CLI
- Monitors system performance
- Tracks usage through LangFuse
- Maintains vector databases

## Key Features
- Dual vector store search
- Pluggable LLM providers
- Natural language memory management
- Real-time response streaming
- Basic authentication
- Conversation persistence
- System monitoring

## Success Metrics
- Search accuracy across both databases
- Response generation quality
- System response time
- User session duration
- Error rate
- User satisfaction

## Future Enhancements
- Mid-conversation model switching
- Provider-specific settings
- Enhanced memory management
- Advanced search capabilities
- Improved authentication options
- UI customization options
