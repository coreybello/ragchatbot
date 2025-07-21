# RAGDDEMO MVP - Technical Specification & Audit Framework

## Project Definition

**What:** Self-hosted chatbot that answers IT support questions using PDF documentation with embedded screenshots.

**Why:** Replace expensive cloud APIs with a secure, offline solution that handles unlimited documents.

**Core Innovation:** Automatically extracts and displays screenshots from PDFs inline with text answers.

---

## MVP Feature Checklist

### Required Features (Must Work)
- [ ] **Chat Interface** - Users can type questions and see answers
- [ ] **Streaming Responses** - Real-time typing animation for bot responses
- [ ] **Suggested Questions** - Follow-up question suggestions after responses
- [ ] **Copy to Clipboard** - Copy bot responses with visual feedback
- [ ] **PDF Text Extraction** - Parse all text from PDF files
- [ ] **Image Extraction** - Extract embedded images from PDFs
- [ ] **Semantic Search** - Find relevant documentation based on natural language queries
- [ ] **Answer Generation** - Create coherent responses using local LLM
- [ ] **Image Display** - Show screenshots inline with text answers
- [ ] **Offline Operation** - Zero external API calls
- [ ] **User Feedback** - Rate responses as good/bad
- [ ] **Query History** - Track all queries and ratings
- [ ] **Knowledge Gap Analysis** - Identify poorly answered questions
- [ ] **Admin Dashboard** - Monitor metrics and manage documents
- [ ] **Admin Authentication** - Secure access to admin features
- [ ] **Configuration UI** - Adjust system prompt, model parameters, and pipeline settings

### Excluded Features (Don't Build Yet)
- ❌ OCR (text in images)
- ❌ User uploads in chat
- ❌ Slack/Teams integration
- ❌ Multi-language support
- ❌ Multi-user authentication (only admin auth for MVP)

---

## Technical Architecture

```
Frontend (React) → API (FastAPI) → Components:
                                  ├── Vector DB (ChromaDB)
                                  ├── LLM (Mistral 7B)
                                  ├── File Storage (Local)
                                  └── SQLite (Metrics/History)
```

---

## Technology Decisions (Fixed)

| Component | Choice | Why |
|-----------|--------|-----|
| **Frontend** | React with Tailwind CSS | Modern, responsive UI |
| **LLM** | Mistral 7B Instruct v0.2 GGUF Q4_K_M | Best quality/speed for CPU |
| **Embeddings** | BAAI/bge-base-en-v1.5 | Fast, 768-dim, good accuracy |
| **Vector DB** | ChromaDB | Simple, no separate service |
| **PDF Library** | PyMuPDF 1.23.8+ | Reliable image extraction |
| **Backend** | FastAPI | Async, auto-docs, SSE support |
| **Metrics DB** | SQLite | Lightweight, file-based |
| **LLM Runtime** | llama-cpp-python | CPU optimized |

---

## API Specification

### 1. Chat Endpoint (with Streaming)
```python
POST /api/chat
Content-Type: application/json

Request:
{
    "query": "How do I reset my password?",
    "conversation_id": "optional-session-id"
}

Response (Server-Sent Events stream):
data: {"type": "content", "content": "To reset your password"}
data: {"type": "content", "content": ", you need to navigate"}
data: {"type": "content", "content": " to the security settings."}
data: {"type": "sources", "sources": [{"document": "UserGuide.pdf", "page": 23}]}
data: {"type": "images", "images": ["settings.png", "security_tab.png"]}
data: {"type": "suggestions", "suggestions": ["How do I set up 2FA?", "Where can I see my login history?"]}
data: {"type": "done"}
```

### 2. User Feedback
```python
POST /api/feedback
Content-Type: application/json

Request:
{
    "message_id": "bot-1678886400000",
    "rating": "good"  // or "bad"
}

Response:
{
    "status": "success"
}
```

### 3. Metrics Dashboard
```python
GET /api/metrics

Response:
{
    "technical": [
        {"name": "Avg. Response Time", "value": "2.8s", "target": "<3s", "ok": true},
        {"name": "Search Accuracy", "value": "89%", "target": ">85%", "ok": true},
        {"name": "System Uptime", "value": "99.9%", "target": ">99%", "ok": true},
        {"name": "Memory Usage", "value": "15.1GB", "target": "<16GB", "ok": true}
    ],
    "user": {
        "questionsToday": 142,
        "satisfaction": 4.6,
        "fallbackRate": "8%"
    },
    "common_queries": [
        {"query": "how to reset password", "count": 45},
        {"query": "vpn setup guide", "count": 28}
    ]
}
```

### 4. Document Ingestion
```python
POST /api/ingest
Content-Type: multipart/form-data

Request:
- pdf_file: binary file data
- force_reprocess: boolean (optional)

Response:
{
    "status": "success",
    "document_id": 123,
    "chunks_created": 45,
    "images_extracted": 12
}
```

### 5. Document Management
```python
# List all documents
GET /api/documents

Response:
[
    {
        "id": 1,
        "name": "UserGuide_v1.2.pdf",
        "size": "2.3 MB",
        "date": "2023-10-26",
        "chunks": 156,
        "images": 42
    }
]

# Delete a document
DELETE /api/documents/{doc_id}

Response:
{
    "status": "success",
    "chunks_deleted": 156,
    "images_deleted": 42
}
```

### 6. Full Re-indexing
```python
POST /api/re-index

Response:
{
    "status": "processing",
    "message": "Re-indexing started",
    "job_id": "reindex-1678886400"
}
```

### 7. Configuration Management
```python
# Update system prompt
POST /api/config/prompt
Content-Type: application/json

Request:
{
    "prompt": "You are an IT support assistant..."
}

Response:
{
    "status": "success"
}

# Update pipeline configuration
POST /api/config/pipeline
Content-Type: application/json

Request:
{
    "chunk_size": 512,
    "chunk_overlap": 50
}

Response:
{
    "status": "success"
}

# Update model parameters (NEW)
POST /api/config/model
Content-Type: application/json

Request:
{
    "temperature": 0.7,
    "top_p": 1.0
}

Response:
{
    "status": "success"
}
```

### 8. Authentication
```python
POST /api/auth/login
Content-Type: application/json

Request:
{
    "password": "admin_password"
}

Response:
{
    "token": "jwt_token_here",
    "expires_in": 3600
}
```

### 9. Query History
```python
GET /api/history
Authorization: Bearer {token}

Response:
[
    {
        "id": "bot-1678886400000",
        "timestamp": 1678886400000,
        "query": "How to add a printer?",
        "response": {
            "content": "To add a printer...",
            "sources": [{"document": "PrinterGuide.pdf", "page": 5}],
            "images": ["printer_dialog.png"],
            "suggestions": ["How to share a printer?", "What if printer not found?"]
        },
        "rating": "good"
    }
]
```

### 10. Admin Dashboard Data (NEW)
```python
GET /api/admin/dashboard-data
Authorization: Bearer {token}

Response:
{
    "documents": [...],    // indexed documents
    "history": [...],      // recent queries
    "metrics": {...},      // current metrics
    "config": {
        "system_prompt": "...",
        "chunk_size": 512,
        "chunk_overlap": 50,
        "temperature": 0.7,
        "top_p": 1.0
    }
}
```

### 11. Static Image Server
```python
GET /images/{filename}

Response:
- Binary image data
- Content-Type: image/png or image/jpeg
```

---

## Database Schema

### SQLite Tables

```sql
-- Query history and metrics
CREATE TABLE queries (
    id TEXT PRIMARY KEY,
    timestamp INTEGER NOT NULL,
    query TEXT NOT NULL,
    response_content TEXT NOT NULL,
    response_sources TEXT,  -- JSON
    response_images TEXT,   -- JSON
    response_suggestions TEXT,  -- JSON (NEW)
    rating TEXT,  -- 'good', 'bad', or NULL
    response_time_ms INTEGER,
    chunks_retrieved INTEGER
);

-- Document metadata
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    upload_date TEXT NOT NULL,
    chunks_count INTEGER NOT NULL,
    images_count INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT 1
);

-- System configuration
CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Daily metrics for dashboard
CREATE TABLE daily_metrics (
    date TEXT PRIMARY KEY,
    total_queries INTEGER DEFAULT 0,
    good_ratings INTEGER DEFAULT 0,
    bad_ratings INTEGER DEFAULT 0,
    avg_response_time_ms INTEGER,
    unique_users INTEGER DEFAULT 0
);
```

---

## Directory Structure

```
ragdemo/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI app initialization
│   │   ├── auth.py           # Authentication endpoints
│   │   ├── chat.py           # Chat endpoints with SSE
│   │   ├── admin.py          # Admin endpoints
│   │   ├── metrics.py        # Metrics endpoints
│   │   └── analysis.py       # Knowledge gap analysis
│   ├── core/
│   │   ├── pdf_processor.py  # PDF text/image extraction
│   │   ├── embeddings.py     # Text embedding logic
│   │   ├── vector_store.py   # ChromaDB operations
│   │   ├── llm_client.py     # Mistral inference with streaming
│   │   ├── suggestions.py    # Generate follow-up questions
│   │   └── config.py         # Settings management
│   ├── models/
│   │   └── database.py       # SQLite models
│   └── utils/
│       ├── auth.py           # JWT token handling
│       ├── metrics.py        # Metrics calculation
│       └── streaming.py      # SSE utilities
├── frontend/
│   ├── src/
│   │   ├── App.jsx           # Main React app
│   │   ├── components/       # React components
│   │   └── index.css         # Tailwind styles
│   └── package.json
├── data/
│   ├── pdfs/                 # Source PDFs
│   ├── images/               # Extracted images
│   ├── chunks/               # JSON chunk files
│   ├── chroma/               # Vector DB storage
│   └── ragdemo.db            # SQLite database
├── models/
│   └── mistral-7b-q4.gguf    # LLM model file
├── prompts/
│   └── system_prompt.txt     # Current system prompt
└── scripts/
    ├── ingest.py             # Batch PDF processing
    ├── init_db.py            # Database initialization
    └── test_pipeline.py      # Integration tests
```

---

## Implementation Details

### Frontend Integration Points

Based on your updated React frontend, here are the specific backend requirements:

1. **Streaming Responses**
   - Implement Server-Sent Events (SSE) for chat endpoint
   - Stream content chunks as they're generated
   - Send metadata (sources, images, suggestions) after content

2. **Suggestion Generation**
   - Generate 3-4 contextual follow-up questions
   - Based on the current query and response content
   - Return in the streaming response

3. **Knowledge Gap Analysis**
   - Track queries with "bad" ratings
   - Provide endpoint to analyze patterns
   - Support creating documentation tasks

4. **Model Configuration**
   - Store temperature and top_p settings
   - Apply dynamically to LLM generation
   - Persist in config database

### Backend Implementation

```python
# chat.py - Streaming chat endpoint
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from datetime import datetime
import json
import asyncio

router = APIRouter()

async def generate_stream(query: str, db):
    """Generate streaming response with content, sources, and suggestions."""
    # Start response
    start_time = datetime.now()
    message_id = f"bot-{int(datetime.now().timestamp() * 1000)}"
    
    # RAG pipeline processing
    chunks = await retrieve_relevant_chunks(query)
    
    # Stream content generation
    async for text_chunk in llm_stream_generate(query, chunks):
        yield f"data: {json.dumps({'type': 'content', 'content': text_chunk})}\n\n"
    
    # Send metadata
    sources = extract_sources(chunks)
    images = extract_images(chunks)
    suggestions = await generate_suggestions(query, chunks)
    
    yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
    yield f"data: {json.dumps({'type': 'images', 'images': images})}\n\n"
    yield f"data: {json.dumps({'type': 'suggestions', 'suggestions': suggestions})}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    # Store in database
    response_time_ms = (datetime.now() - start_time).total_seconds() * 1000
    store_query_record(db, message_id, query, sources, images, suggestions, response_time_ms)

@router.post("/chat")
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    return StreamingResponse(
        generate_stream(request.query, db),
        media_type="text/event-stream"
    )

# suggestions.py - Generate follow-up questions
async def generate_suggestions(query: str, context_chunks: List[Dict]) -> List[str]:
    """Generate 3-4 contextual follow-up questions."""
    prompt = f"""
    Based on this Q&A exchange, suggest 3-4 follow-up questions the user might ask next.
    
    User asked: {query}
    Context: {summarize_chunks(context_chunks)}
    
    Return only the questions, one per line.
    """
    
    suggestions = await llm_generate(prompt, temperature=0.8, max_tokens=200)
    return [q.strip() for q in suggestions.split('\n') if q.strip()][:4]

# analysis.py - Knowledge gap analysis
@router.get("/api/analysis/gaps")
async def get_knowledge_gaps(db: Session = Depends(get_db)):
    """Return queries that received bad ratings."""
    bad_queries = db.query(Query).filter(Query.rating == "bad").order_by(Query.timestamp.desc()).all()
    
    gaps = []
    for query in bad_queries:
        gaps.append({
            "id": query.id,
            "timestamp": query.timestamp,
            "query": query.query,
            "response": {
                "content": query.response_content,
                "sources": json.loads(query.response_sources or "[]")
            }
        })
    
    return {"gaps": gaps, "total": len(gaps)}

# Model configuration with validation
@router.post("/api/config/model")
async def update_model_config(config: ModelConfig, db: Session = Depends(get_db)):
    """Update LLM generation parameters."""
    # Validate ranges
    if not 0 <= config.temperature <= 2:
        raise HTTPException(400, "Temperature must be between 0 and 2")
    if not 0 <= config.top_p <= 1:
        raise HTTPException(400, "Top-p must be between 0 and 1")
    
    # Store in database
    update_config(db, "temperature", str(config.temperature))
    update_config(db, "top_p", str(config.top_p))
    
    # Update global LLM settings
    llm_client.update_parameters(
        temperature=config.temperature,
        top_p=config.top_p
    )
    
    return {"status": "success"}
```

```python
# streaming.py - SSE utilities
import asyncio
from typing import AsyncGenerator

async def llm_stream_generate(query: str, context: List[Dict]) -> AsyncGenerator[str, None]:
    """Stream LLM generation token by token."""
    prompt = build_prompt(query, context)
    
    # Get model parameters from config
    config = get_current_config()
    
    # Stream tokens
    for token in llm.generate_stream(
        prompt,
        temperature=config.get("temperature", 0.7),
        top_p=config.get("top_p", 1.0),
        max_tokens=1500
    ):
        yield token
        await asyncio.sleep(0.01)  # Small delay for smooth streaming
```

---

## Security Considerations

1. **Admin Authentication**
   - Use bcrypt for password hashing
   - JWT tokens with 1-hour expiration
   - Refresh tokens for extended sessions
   - Rate limiting on login attempts

2. **File Security**
   - Validate PDF uploads (file type, size limits)
   - Sanitize filenames
   - Virus scanning for uploaded files
   - Read-only access to image directory

3. **API Security**
   - Rate limiting: 10 requests/minute for chat
   - Input validation on all endpoints
   - SQL injection prevention via ORM
   - XSS prevention in markdown rendering
   - CORS properly configured

4. **Configuration Security**
   - Validate all configuration changes
   - Audit log for admin actions
   - Secure storage of sensitive configs

---

## Performance Optimizations

1. **Streaming Optimizations**
   - Use async generators for efficient streaming
   - Buffer management for smooth delivery
   - Connection timeout handling

2. **Caching Strategy**
   - Cache common queries for 1 hour
   - Cache metrics calculations for 5 minutes
   - Cache suggestion generations
   - Use Redis for production caching

3. **Database Optimizations**
   - Index on queries.timestamp for history
   - Index on queries.rating for metrics
   - Index on queries.query for gap analysis
   - Periodic cleanup of old queries (>90 days)

4. **LLM Optimizations**
   - Model quantization (Q4_K_M)
   - Batch processing where possible
   - Context window management
   - Temperature/top_p tuning for speed

---

## Frontend Features Implementation

### Copy to Clipboard
- Implemented client-side
- Visual feedback with checkmark icon
- 2-second confirmation display

### Tooltips
- Information icons for configuration options
- Hover-triggered explanations
- Help users understand settings

### Confirmation Modals
- Critical actions require confirmation
- Consistent modal design
- Clear warning messages

### Knowledge Gap Analysis
- Dedicated tab for bad responses
- Actionable insights
- Task creation workflow (future feature)

---

## Testing Checklist

### Unit Tests
- [ ] PDF extraction handles multi-column layouts
- [ ] Image extraction preserves quality
- [ ] Streaming response generation
- [ ] Suggestion generation quality
- [ ] Authentication token generation/validation
- [ ] Configuration validation
- [ ] Metrics calculation accuracy

### Integration Tests
- [ ] Full chat flow with streaming
- [ ] Document upload and indexing
- [ ] Admin login and operations
- [ ] Configuration changes persist
- [ ] Knowledge gap identification
- [ ] Copy functionality works
- [ ] Suggestion selection triggers new query

### Frontend Tests
- [ ] Streaming animation displays correctly
- [ ] Copy to clipboard works across browsers
- [ ] Tooltips appear on hover
- [ ] Confirmation modals prevent accidental actions
- [ ] Dark mode styling complete
- [ ] Responsive design on mobile
- [ ] Tab navigation smooth

---

## MVP Success Criteria

1. **Functional Requirements**
   - [ ] Process 50+ PDF documents
   - [ ] Answer questions with 90%+ accuracy
   - [ ] Display relevant screenshots
   - [ ] Response time under 5 seconds
   - [ ] Stream responses smoothly
   - [ ] Generate helpful follow-up questions
   - [ ] Track user satisfaction via ratings
   - [ ] Identify knowledge gaps

2. **Technical Requirements**
   - [ ] Run on CPU-only server
   - [ ] Use less than 32GB RAM
   - [ ] No external API calls
   - [ ] Support 10+ concurrent users
   - [ ] 99% uptime
   - [ ] Sub-100ms streaming latency

3. **User Experience**
   - [ ] Intuitive chat interface
   - [ ] Clear source citations
   - [ ] Inline image display
   - [ ] Smooth streaming responses
   - [ ] Helpful suggestions
   - [ ] Easy configuration for admins
   - [ ] Knowledge gap insights

---

## Development Commands

```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python scripts/init_db.py

# Frontend setup
cd frontend
npm install
npm run build

# Development mode
# Terminal 1: Backend
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
npm start

# Production deployment
docker-compose up -d

# Ingest documents
python scripts/ingest.py --pdf-dir ./data/pdfs

# Run tests
pytest backend/tests/
npm test
```

---

## Environment Variables

```bash
# .env file
DATABASE_URL=sqlite:///./data/ragdemo.db
MODEL_PATH=./models/mistral-7b-q4.gguf
CHROMA_PERSIST_DIR=./data/chroma
IMAGE_DIR=./data/images
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=1
ADMIN_PASSWORD_HASH=$2b$12$... # bcrypt hash
LOG_LEVEL=INFO
MAX_UPLOAD_SIZE_MB=50
CHUNK_SIZE=512
CHUNK_OVERLAP=50
DEFAULT_TEMPERATURE=0.7
DEFAULT_TOP_P=1.0
SUGGESTION_COUNT=4
STREAMING_CHUNK_SIZE=10  # characters per stream chunk
```

---

## Next Steps After MVP

1. **Enhanced Features**
   - OCR for scanned documents
   - Multi-language support
   - Voice input/output
   - Export chat history
   - Batch document processing UI

2. **Integrations**
   - Slack/Teams bots
   - Email ingestion
   - Confluence sync
   - Active Directory auth
   - Webhook notifications

3. **Advanced Analytics**
   - Query clustering
   - Automatic gap detection
   - Performance trends
   - User behavior analysis
   - A/B testing framework

4. **Scaling Features**
   - Multi-model support
   - GPU acceleration option
   - Distributed processing
   - Caching layer (Redis)
   - Load balancing