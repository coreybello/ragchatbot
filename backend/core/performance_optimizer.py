"""
Performance optimization utilities for RAG Demo
Includes database optimization, caching, and monitoring
"""
import asyncio
import time
import functools
import logging
import psutil
import threading
from typing import Any, Callable, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy import text
from contextlib import asynccontextmanager
import json

from backend.core.config import get_settings
from backend.models.database import SessionLocal, engine

logger = logging.getLogger(__name__)

class PerformanceOptimizer:
    """Performance optimization and monitoring utilities"""
    
    def __init__(self):
        self.settings = get_settings()
        self.cache = {}
        self.cache_ttl = {}
        self.performance_metrics = {
            'api_calls': 0,
            'avg_response_time': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'db_queries': 0,
            'memory_usage': 0
        }
        self._start_monitoring()
    
    def _start_monitoring(self):
        """Start background performance monitoring"""
        def monitor():
            while True:
                try:
                    # Update memory usage
                    process = psutil.Process()
                    self.performance_metrics['memory_usage'] = process.memory_info().rss / 1024 / 1024  # MB
                    time.sleep(30)  # Monitor every 30 seconds
                except Exception as e:
                    logger.error(f"Monitoring error: {e}")
                    time.sleep(60)
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
        logger.info("✅ Performance monitoring started")
    
    def cache_result(self, key: str, result: Any, ttl_seconds: int = 3600):
        """Cache a result with TTL"""
        self.cache[key] = result
        self.cache_ttl[key] = datetime.now() + timedelta(seconds=ttl_seconds)
    
    def get_cached_result(self, key: str) -> Optional[Any]:
        """Get cached result if still valid"""
        if key not in self.cache:
            self.performance_metrics['cache_misses'] += 1
            return None
        
        if datetime.now() > self.cache_ttl[key]:
            # Cache expired
            del self.cache[key]
            del self.cache_ttl[key]
            self.performance_metrics['cache_misses'] += 1
            return None
        
        self.performance_metrics['cache_hits'] += 1
        return self.cache[key]
    
    def clear_expired_cache(self):
        """Clear expired cache entries"""
        now = datetime.now()
        expired_keys = [k for k, expiry in self.cache_ttl.items() if now > expiry]
        for key in expired_keys:
            del self.cache[key]
            del self.cache_ttl[key]
        
        if expired_keys:
            logger.info(f"Cleared {len(expired_keys)} expired cache entries")
    
    def timed_function(self, func_name: str = None):
        """Decorator to time function execution"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    execution_time = time.time() - start_time
                    self._record_timing(func_name or func.__name__, execution_time)
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    execution_time = time.time() - start_time
                    self._record_timing(func_name or func.__name__, execution_time)
            
            # Return appropriate wrapper based on function type
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def _record_timing(self, function_name: str, execution_time: float):
        """Record function execution time"""
        self.performance_metrics['api_calls'] += 1
        
        # Update rolling average
        current_avg = self.performance_metrics['avg_response_time']
        total_calls = self.performance_metrics['api_calls']
        new_avg = ((current_avg * (total_calls - 1)) + execution_time) / total_calls
        self.performance_metrics['avg_response_time'] = new_avg
        
        logger.debug(f"⏱️ {function_name}: {execution_time:.3f}s")
    
    async def optimize_database(self):
        """Optimize database performance with indexes and cleanup"""
        logger.info("🔧 Optimizing database performance...")
        
        db = SessionLocal()
        try:
            # Create indexes for better query performance
            optimizations = [
                # Index on queries table for timestamp-based queries
                "CREATE INDEX IF NOT EXISTS idx_queries_timestamp ON queries(timestamp DESC)",
                
                # Index on queries table for rating filtering
                "CREATE INDEX IF NOT EXISTS idx_queries_rating ON queries(rating)",
                
                # Index on documents table for active documents
                "CREATE INDEX IF NOT EXISTS idx_documents_active ON documents(is_active, upload_date DESC)",
                
                # Index on daily_metrics table for date range queries
                "CREATE INDEX IF NOT EXISTS idx_daily_metrics_date ON daily_metrics(date DESC)",
                
                # Composite index for query history with rating
                "CREATE INDEX IF NOT EXISTS idx_queries_timestamp_rating ON queries(timestamp DESC, rating)",
            ]
            
            for sql in optimizations:
                try:
                    db.execute(text(sql))
                    logger.info(f"✅ Created index: {sql.split('idx_')[1].split(' ')[0]}")
                except Exception as e:
                    logger.warning(f"Index creation skipped: {e}")
            
            db.commit()
            
            # Analyze tables for query planner optimization
            analyze_queries = [
                "ANALYZE queries",
                "ANALYZE documents", 
                "ANALYZE daily_metrics",
                "ANALYZE config"
            ]
            
            for sql in analyze_queries:
                try:
                    db.execute(text(sql))
                except Exception as e:
                    logger.warning(f"ANALYZE failed: {e}")
            
            # Clean up old queries (keep last 10000)
            cleanup_result = db.execute(text("""
                DELETE FROM queries 
                WHERE id NOT IN (
                    SELECT id FROM queries 
                    ORDER BY timestamp DESC 
                    LIMIT 10000
                )
            """))
            
            if cleanup_result.rowcount > 0:
                logger.info(f"🗑️ Cleaned up {cleanup_result.rowcount} old queries")
            
            db.commit()
            logger.info("✅ Database optimization completed")
            
        except Exception as e:
            logger.error(f"❌ Database optimization failed: {e}")
            db.rollback()
        finally:
            db.close()
    
    def get_performance_report(self) -> Dict:
        """Get current performance metrics"""
        cache_hit_rate = 0
        total_cache_requests = self.performance_metrics['cache_hits'] + self.performance_metrics['cache_misses']
        if total_cache_requests > 0:
            cache_hit_rate = (self.performance_metrics['cache_hits'] / total_cache_requests) * 100
        
        return {
            'timestamp': datetime.now().isoformat(),
            'api_calls': self.performance_metrics['api_calls'],
            'avg_response_time_ms': round(self.performance_metrics['avg_response_time'] * 1000, 2),
            'cache_hit_rate_percent': round(cache_hit_rate, 2),
            'cache_entries': len(self.cache),
            'memory_usage_mb': round(self.performance_metrics['memory_usage'], 2),
            'db_queries': self.performance_metrics['db_queries']
        }
    
    async def preload_models(self):
        """Preload and warm up models for better response times"""
        logger.info("🔥 Preloading models and warming up caches...")
        
        try:
            # Import and initialize core components
            from backend.core.llm_client import LLMClient
            from backend.core.vector_store import VectorStore
            
            # Warm up LLM client
            start_time = time.time()
            llm_client = LLMClient()
            llm_time = time.time() - start_time
            logger.info(f"✅ LLM client loaded in {llm_time:.2f}s")
            
            # Warm up vector store
            start_time = time.time()
            vector_store = VectorStore()
            vector_time = time.time() - start_time
            logger.info(f"✅ Vector store loaded in {vector_time:.2f}s")
            
            # Test search to warm up embeddings
            await vector_store.search("test query", limit=1)
            
            # Cache common configurations
            db = SessionLocal()
            try:
                from backend.models.database import Config
                configs = db.query(Config).all()
                for config in configs:
                    cache_key = f"config:{config.key}"
                    self.cache_result(cache_key, config.value, ttl_seconds=7200)  # 2 hours
                logger.info(f"✅ Cached {len(configs)} configuration values")
            finally:
                db.close()
            
            logger.info("🚀 Model preloading completed")
            
        except Exception as e:
            logger.error(f"❌ Model preloading failed: {e}")

# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer()

# Decorator for easy function timing
timed = performance_optimizer.timed_function

# Context manager for database optimization
@asynccontextmanager
async def optimized_db_session():
    """Context manager for optimized database sessions"""
    start_time = time.time()
    db = SessionLocal()
    try:
        yield db
        performance_optimizer.performance_metrics['db_queries'] += 1
    finally:
        db.close()
        execution_time = time.time() - start_time
        if execution_time > 0.5:  # Log slow queries
            logger.warning(f"🐌 Slow database operation: {execution_time:.3f}s")

async def startup_optimization():
    """Run optimization tasks on startup"""
    logger.info("🚀 Starting performance optimization...")
    
    try:
        # Run database optimization
        await performance_optimizer.optimize_database()
        
        # Preload models
        await performance_optimizer.preload_models()
        
        # Clear any expired cache
        performance_optimizer.clear_expired_cache()
        
        logger.info("✅ Startup optimization completed")
        
    except Exception as e:
        logger.error(f"❌ Startup optimization failed: {e}")

def get_system_metrics():
    """Get comprehensive system performance metrics"""
    try:
        process = psutil.Process()
        
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_usage_mb': process.memory_info().rss / 1024 / 1024,
            'memory_percent': process.memory_percent(),
            'disk_usage': psutil.disk_usage('/').percent,
            'open_files': len(process.open_files()),
            'connections': len(process.connections()),
            'threads': process.num_threads(),
            'performance_metrics': performance_optimizer.get_performance_report()
        }
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        return {'error': str(e)}