"""
Server-Sent Events streaming utilities
"""
import json
import asyncio
from typing import AsyncGenerator, Dict, Any

async def generate_stream_response(query: str, context: str, llm_client, vector_store) -> AsyncGenerator[str, None]:
    """
    Generate streaming response with proper SSE formatting
    
    Args:
        query: User query
        context: Retrieved context
        llm_client: LLM client for generation
        vector_store: Vector store for retrieval
        
    Yields:
        SSE formatted data chunks
    """
    
    try:
        # Start with thinking indicator
        yield format_sse_data("status", {"status": "thinking"})
        await asyncio.sleep(0.1)
        
        # Retrieve relevant chunks
        chunks = await vector_store.search(query, limit=5)
        
        # Build context and extract metadata
        sources = []
        images = []
        
        for chunk in chunks:
            sources.append({
                "document": chunk['document'],
                "page": chunk['page']
            })
            images.extend(chunk.get('images', []))
        
        # Stream content generation
        yield format_sse_data("status", {"status": "generating"})
        
        full_response = ""
        async for token in llm_client.generate_stream(query, context):
            full_response += token
            yield format_sse_data("content", {"content": token})
            await asyncio.sleep(0.01)
        
        # Send metadata
        yield format_sse_data("sources", {"sources": sources})
        yield format_sse_data("images", {"images": list(set(images))})
        
        # Generate and send suggestions
        from backend.core.suggestions import generate_suggestions
        suggestions = await generate_suggestions(query, chunks)
        yield format_sse_data("suggestions", {"suggestions": suggestions})
        
        # Signal completion
        yield format_sse_data("done", {"status": "complete"})
        
    except Exception as e:
        yield format_sse_data("error", {"error": str(e)})

def format_sse_data(event_type: str, data: Dict[Any, Any]) -> str:
    """
    Format data for Server-Sent Events
    
    Args:
        event_type: Type of event (content, sources, images, etc.)
        data: Data payload
        
    Returns:
        Formatted SSE string
    """
    
    # Add event type to data
    data["type"] = event_type
    
    # Format as SSE
    return f"data: {json.dumps(data)}\\n\\n"

def create_heartbeat_generator(interval: float = 30.0) -> AsyncGenerator[str, None]:
    """
    Generate periodic heartbeat messages to keep connection alive
    
    Args:
        interval: Heartbeat interval in seconds
        
    Yields:
        Heartbeat SSE messages
    """
    
    async def heartbeat():
        while True:
            yield format_sse_data("heartbeat", {"timestamp": asyncio.get_event_loop().time()})
            await asyncio.sleep(interval)
    
    return heartbeat()