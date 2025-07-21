"""
Knowledge gap analysis API endpoints
"""
from fastapi import APIRouter, Depends
from typing import List
import json

from backend.models.database import get_db, Query
from backend.utils.auth import admin_required
from backend.models.database import SessionLocal

router = APIRouter()

@router.get("/analysis/gaps")
async def get_knowledge_gaps(
    current_user: dict = Depends(admin_required),
    db: SessionLocal = Depends(get_db)
):
    """
    Get queries that received bad ratings - indicating knowledge gaps
    """
    
    # Get all queries with bad ratings
    bad_queries = db.query(Query).filter(Query.rating == "bad").order_by(Query.timestamp.desc()).all()
    
    gaps = []
    for query in bad_queries:
        # Parse JSON fields safely
        try:
            sources = json.loads(query.response_sources) if query.response_sources else []
        except:
            sources = []
        
        gaps.append({
            "id": query.id,
            "timestamp": query.timestamp,
            "query": query.query,
            "response": {
                "content": query.response_content,
                "sources": sources
            }
        })
    
    return {
        "gaps": gaps,
        "total": len(gaps)
    }

@router.get("/analysis/patterns")
async def analyze_query_patterns(
    current_user: dict = Depends(admin_required),
    db: SessionLocal = Depends(get_db)
):
    """
    Analyze patterns in user queries to identify common themes
    """
    
    # Get all queries from last 30 days
    queries = db.query(Query).order_by(Query.timestamp.desc()).limit(1000).all()
    
    # Simple keyword analysis
    keyword_counts = {}
    common_words = ['password', 'email', 'vpn', 'printer', 'network', 'software', 'login', 'access', 'error', 'install']
    
    for query in queries:
        query_lower = query.query.lower()
        for word in common_words:
            if word in query_lower:
                keyword_counts[word] = keyword_counts.get(word, 0) + 1
    
    # Sort by frequency
    patterns = [
        {"keyword": word, "count": count, "percentage": round(count / len(queries) * 100, 1)}
        for word, count in sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
    ]
    
    return {
        "total_queries": len(queries),
        "patterns": patterns,
        "analysis_period": "Last 1000 queries"
    }

@router.get("/analysis/satisfaction")
async def analyze_satisfaction_trends(
    current_user: dict = Depends(admin_required),
    db: SessionLocal = Depends(get_db)
):
    """
    Analyze satisfaction trends over time
    """
    
    # Get rated queries
    rated_queries = db.query(Query).filter(Query.rating.isnot(None)).order_by(Query.timestamp.desc()).limit(500).all()
    
    # Calculate daily satisfaction
    daily_stats = {}
    
    for query in rated_queries:
        # Convert timestamp to date
        from datetime import datetime
        date = datetime.fromtimestamp(query.timestamp / 1000).strftime('%Y-%m-%d')
        
        if date not in daily_stats:
            daily_stats[date] = {'good': 0, 'bad': 0, 'total': 0}
        
        daily_stats[date][query.rating] += 1
        daily_stats[date]['total'] += 1
    
    # Calculate satisfaction percentages
    trends = []
    for date, stats in sorted(daily_stats.items()):
        satisfaction = (stats['good'] / stats['total'] * 100) if stats['total'] > 0 else 0
        trends.append({
            "date": date,
            "satisfaction_percent": round(satisfaction, 1),
            "total_ratings": stats['total'],
            "good_ratings": stats['good'],
            "bad_ratings": stats['bad']
        })
    
    return {
        "trends": trends[-30:],  # Last 30 days
        "overall_satisfaction": round(sum([t['satisfaction_percent'] for t in trends]) / len(trends), 1) if trends else 0,
        "total_rated_queries": len(rated_queries)
    }