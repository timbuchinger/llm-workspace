# System Patterns

## API Architecture

### Endpoint Patterns
1. **Health Check**
   ```python
   @app.get("/healthz")
   async def healthz():
       return {"status": "ok"}
   ```

2. **Memory Search**
   ```python
   @app.post("/search-similar")
   async def get_prompt(search_request: MemorySearchRequest):
   ```

### Data Models
1. **Memory Addition**
   ```python
   class MemoryAddRequest(BaseModel):
       memory: str
       tags: Optional[list[str]] = []
   ```

2. **Memory Search**
   ```python
   class MemorySearchRequest(BaseModel):
       query: str
       n_results: Optional[int] = 3
       collections: list[str]
   ```

## Logging Patterns

### Function Call Logging
```python
@log_function_call
def function():
    # Automatically logs:
    # - Function entry with args/kwargs
    # - Function return value
```

### Health Check Filtering
```python
class HealthCheckFilter(logging.Filter):
    def filter(self, record):
        return "/healthz" not in record.getMessage()
```

## ChromaDB Integration

### Client Configuration
```python
remote_db = chromadb.HttpClient(
    settings=Settings(
        anonymized_telemetry=False,
        chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider",
        chroma_client_auth_credentials=os.environ.get("CHROMA_AUTH_TOKEN"),
    ),
    host=os.environ.get("CHROMA_HOST"),
    port=int(os.environ.get("CHROMA_PORT", 8000)),
    ssl=os.environ.get("CHROMA_USE_SSL", "false").lower() == "true",
)
```

### Collection Management
- Collection-based organization
- Query operations with embeddings
- Metadata handling

## Embedding Generation

### Ollama Integration
1. Protocol selection based on SSL configuration
2. Base URL construction from environment
3. Model specification (nomic-embed-text)
4. Query embedding generation

## RAG Pipeline

### Search Flow
1. Generate query embedding
2. Execute similarity search
3. Process search results
4. Apply RAG prompt template
5. Return augmented context

### Result Processing
1. Document extraction
2. Metadata handling
3. Distance scoring
4. Context assembly

## Error Handling

### Patterns
1. Environment validation
2. API error responses
3. Logging error contexts
4. Client connection handling

## Security Patterns

### Authentication
1. ChromaDB token authentication
2. SSL configuration options
3. Environment-based security settings

### Environment Management
1. Dotenv loading
2. Secure credential handling
3. SSL toggle mechanisms

## Development Patterns

### Code Organization
1. Server module structure
2. Model definitions
3. Utility decorators
4. Configuration management

### Testing Patterns
1. Health check validation
2. API endpoint testing
3. Integration testing considerations
4. Error case handling
