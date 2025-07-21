"""
Chat API endpoints with Server-Sent Events streaming
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from datetime import datetime
import json
import asyncio
import uuid

from backend.models.database import get_db, Query
from backend.core.llm_client import LLMClient
from backend.core.vector_store import VectorStore
from backend.core.suggestions import generate_suggestions
from backend.utils.streaming import generate_stream_response
from backend.models.database import SessionLocal

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    conversation_id: str = None

class FeedbackRequest(BaseModel):
    message_id: str
    rating: str  # 'good' or 'bad'

# Initialize components
llm_client = LLMClient()
vector_store = VectorStore()

@router.post("/chat")
async def chat_stream(request: ChatRequest, db: SessionLocal = Depends(get_db)):
    """
    Stream chat response using Server-Sent Events
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    # Generate unique message ID
    message_id = f"bot-{int(datetime.now().timestamp() * 1000)}"
    start_time = datetime.now()
    
    async def generate():
        try:
            # Retrieve relevant chunks from vector store
            chunks = await vector_store.search(request.query, limit=5)
            
            # Build context for LLM
            context = ""
            sources = []
            images = []
            
            for chunk in chunks:
                context += f"CHUNK {chunk['id']} [Source: {chunk['document']}, Page: {chunk['page']}]\\n"
                context += f"Text: {chunk['text']}\\n"
                if chunk['images']:
                    context += f"Images: {', '.join(chunk['images'])}\\n"
                    images.extend(chunk['images'])
                context += "\\n"
                
                sources.append({
                    "document": chunk['document'],
                    "page": chunk['page']
                })
            
            # Stream content generation
            full_response = ""
            async for token in llm_client.generate_stream(request.query, context):
                full_response += token
                yield f"data: {json.dumps({'type': 'content', 'content': token})}\\n\\n"
                await asyncio.sleep(0.01)  # Small delay for smooth streaming
            
            # Generate suggestions
            suggestions = await generate_suggestions(request.query, chunks)
            
            # Send metadata
            yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\\n\\n"
            yield f"data: {json.dumps({'type': 'images', 'images': list(set(images))})}\\n\\n"
            yield f"data: {json.dumps({'type': 'suggestions', 'suggestions': suggestions})}\\n\\n"
            yield f"data: {json.dumps({'type': 'done'})}\\n\\n"
            
            # Store in database
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            query_record = Query(
                id=message_id,
                timestamp=int(datetime.now().timestamp() * 1000),
                query=request.query,
                response_content=full_response,
                response_sources=json.dumps(sources),
                response_images=json.dumps(list(set(images))),
                response_suggestions=json.dumps(suggestions),
                response_time_ms=int(response_time),
                chunks_retrieved=len(chunks)
            )
            db.add(query_record)
            db.commit()
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\\n\\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

@router.post("/feedback")
async def submit_feedback(request: FeedbackRequest, db: SessionLocal = Depends(get_db)):
    """Submit user feedback for a chat response"""
    
    if request.rating not in ['good', 'bad']:
        raise HTTPException(status_code=400, detail="Rating must be 'good' or 'bad'")
    
    # Find the query record
    query_record = db.query(Query).filter(Query.id == request.message_id).first()
    if not query_record:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Update rating
    query_record.rating = request.rating
    db.commit()
    
    return {"status": "success"}