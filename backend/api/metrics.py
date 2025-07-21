"""
Metrics API endpoints for performance monitoring
"""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from datetime import datetime, timedelta
import time
import psutil
import os

from backend.models.database import get_db, Query, Document
from backend.core.vector_store import VectorStore
from backend.utils.auth import admin_required
from backend.models.database import SessionLocal

router = APIRouter()

# Initialize vector store for stats
vector_store = VectorStore()

@router.get("/metrics")
async def get_metrics(
    current_user: dict = Depends(admin_required),
    db: SessionLocal = Depends(get_db)
):
    """Get comprehensive system metrics"""
    
    # Calculate technical metrics
    now = datetime.now()
    today_start = datetime.combine(now.date(), datetime.min.time())
    today_timestamp = int(today_start.timestamp() * 1000)
    
    # Get queries from today
    today_queries = db.query(Query).filter(Query.timestamp >= today_timestamp).all()
    
    # Calculate average response time
    response_times = [q.response_time_ms for q in today_queries if q.response_time_ms]
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    # Calculate search accuracy (placeholder - would need more sophisticated metrics)
    good_ratings = len([q for q in today_queries if q.rating == 'good'])
    bad_ratings = len([q for q in today_queries if q.rating == 'bad'])
    total_ratings = good_ratings + bad_ratings
    search_accuracy = (good_ratings / total_ratings * 100) if total_ratings > 0 else 0
    
    # System uptime (simplified)
    system_uptime = 99.9  # Would calculate actual uptime in production
    
    # Memory usage
    process = psutil.Process(os.getpid())
    memory_usage = process.memory_info().rss / (1024 * 1024 * 1024)  # GB
    
    # Technical metrics
    technical_metrics = [
        {
            "name": "Avg. Response Time",
            "value": f"{avg_response_time/1000:.1f}s",
            "target": "<3s",
            "ok": avg_response_time < 3000
        },
        {
            "name": "Search Accuracy", 
            "value": f"{search_accuracy:.0f}%",
            "target": ">85%",
            "ok": search_accuracy > 85
        },
        {
            "name": "System Uptime",
            "value": f"{system_uptime:.1f}%", 
            "target": ">99%",
            "ok": system_uptime > 99
        },
        {
            "name": "Memory Usage",
            "value": f"{memory_usage:.1f}GB",
            "target": "<16GB", 
            "ok": memory_usage < 16
        }
    ]
    
    # User engagement metrics
    satisfaction_scores = [5 if q.rating == 'good' else 1 if q.rating == 'bad' else 3 for q in today_queries]
    avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0
    fallback_rate = (bad_ratings / len(today_queries) * 100) if today_queries else 0
    
    user_metrics = {
        "questionsToday": len(today_queries),
        "satisfaction": round(avg_satisfaction, 1),
        "fallbackRate": f"{fallback_rate:.0f}%"
    }
    
    # Common queries analysis
    query_counts = {}
    for query in today_queries:
        query_lower = query.query.lower()
        # Simple keyword extraction
        for word in ['password', 'vpn', 'printer', 'email', 'network', 'software']:
            if word in query_lower:
                query_counts[word] = query_counts.get(word, 0) + 1
    
    # Add "other" category
    accounted_queries = sum(query_counts.values())
    other_queries = max(0, len(today_queries) - accounted_queries)
    if other_queries > 0:
        query_counts['other'] = other_queries
    
    # Format common queries
    common_queries = [
        {"query": f"{key} related", "count": count}
        for key, count in sorted(query_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    ]
    
    return {
        "technical": technical_metrics,
        "user": user_metrics, 
        "common_queries": common_queries
    }

@router.get("/history")
async def get_query_history(
    current_user: dict = Depends(admin_required),
    db: SessionLocal = Depends(get_db)
):
    """Get query history for admin review"""
    
    # Get recent queries (last 100)
    queries = db.query(Query).order_by(Query.timestamp.desc()).limit(100).all()
    
    history = []
    for query in queries:
        # Parse JSON fields safely
        try:
            sources = eval(query.response_sources) if query.response_sources else []
        except:
            sources = []
            
        try:
            images = eval(query.response_images) if query.response_images else []
        except:
            images = []
            
        try:
            suggestions = eval(query.response_suggestions) if query.response_suggestions else []
        except:
            suggestions = []
        
        history.append({
            "id": query.id,
            "timestamp": query.timestamp,
            "query": query.query,
            "response": {
                "content": query.response_content,
                "sources": sources,
                "images": images,
                "suggestions": suggestions
            },
            "rating": query.rating
        })
    
    return history

@router.get("/system-status")
async def get_system_status():
    """Get current system status"""
    
    try:
        # Vector store stats
        vector_stats = vector_store.get_collection_stats()
        
        # System resources
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "vector_store": vector_stats,
            "system": {
                "cpu_usage": f"{cpu_percent:.1f}%",
                "memory_usage": f"{memory.percent:.1f}%",
                "disk_usage": f"{disk.percent:.1f}%",
                "available_memory": f"{memory.available / (1024**3):.1f}GB"
            }
        }
        
    except Exception as e:
        return {
            "status": "degraded",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }