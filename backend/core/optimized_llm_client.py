"""
Optimized LLM client with async processing, connection pooling, and caching
Performance improvements for Mistral 7B inference
"""
import asyncio
import threading
from typing import AsyncGenerator, Optional, Dict, Any
import logging
import time
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from contextlib import asynccontextmanager

from llama_cpp import Llama

from backend.core.config import get_settings
from backend.models.database import get_config_value, SessionLocal
from backend.core.performance_optimizer import performance_optimizer, timed

logger = logging.getLogger(__name__)

class OptimizedLLMClient:
    """High-performance LLM client with optimizations and caching"""
    
    def __init__(self):
        self.settings = get_settings()
        self.model = None
        self.model_lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="llm-worker")
        self.response_cache = {}
        self.config_cache = {}
        self.is_loading = False
        self._preload_model()
    
    def _preload_model(self):
        """Preload model in background thread"""
        def load_model():
            try:
                logger.info(f"🔥 Preloading optimized model from: {self.settings.model_path}")
                
                with self.model_lock:
                    self.model = Llama(
                        model_path=self.settings.model_path,
                        n_ctx=4096,  # Context window
                        n_threads=6,  # Optimized thread count
                        n_gpu_layers=0,  # CPU only for consistency
                        verbose=False,
                        use_mmap=True,  # Memory mapping for faster loading
                        use_mlock=True,  # Lock memory to prevent swapping
                        n_batch=512,  # Batch size for processing
                        rope_freq_base=10000.0,  # RoPE frequency base
                        rope_freq_scale=1.0,  # RoPE frequency scaling
                    )
                
                # Warm up model with a test generation
                test_prompt = "[INST] Hello [/INST]"
                _ = self.model(test_prompt, max_tokens=5, temperature=0.1)
                
                logger.info("✅ Optimized Mistral model loaded and warmed up")
                
            except Exception as e:
                logger.error(f"❌ Failed to preload model: {e}")
                self.model = None
        
        # Start loading in background
        load_thread = threading.Thread(target=load_model, daemon=True)
        load_thread.start()
    
    def _get_cache_key(self, query: str, context: str, params: Dict) -> str:
        """Generate cache key for responses"""
        content = f"{query}:{context}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    @asynccontextmanager
    async def _get_model_config(self):
        """Get model configuration with caching"""
        # Check cache first
        cache_key = "model_config"
        cached_config = performance_optimizer.get_cached_result(cache_key)
        
        if cached_config:
            yield cached_config
            return
        
        # Get from database
        db = SessionLocal()
        try:
            config = {
                'temperature': float(get_config_value(db, "temperature", "0.7")),
                'top_p': float(get_config_value(db, "top_p", "1.0")),
                'system_prompt': get_config_value(
                    db, 
                    "system_prompt", 
                    "You are an IT support assistant. Answer using only the provided documentation."
                )
            }
            
            # Cache for 5 minutes
            performance_optimizer.cache_result(cache_key, config, ttl_seconds=300)
            yield config
            
        finally:
            db.close()
    
    def _build_optimized_prompt(self, query: str, context: str, system_prompt: str) -> str:
        """Build optimized prompt with better formatting"""
        # Truncate context if too long to prevent memory issues
        max_context_length = 3000
        if len(context) > max_context_length:
            context = context[:max_context_length] + "... [truncated]"
        
        prompt = f"""<s>[INST] {system_prompt}

Context:
{context}

User Query: {query}

Provide a helpful and accurate response based on the context provided. [/INST]"""
        
        return prompt
    
    async def _wait_for_model(self, timeout: float = 30.0) -> bool:
        """Wait for model to be loaded"""
        start_time = time.time()
        while self.model is None and (time.time() - start_time) < timeout:
            await asyncio.sleep(0.1)
        return self.model is not None
    
    @timed("llm_generation")
    async def generate_stream(self, query: str, context: str) -> AsyncGenerator[str, None]:
        """Generate streaming response with optimizations"""
        
        # Wait for model to be loaded
        if not await self._wait_for_model():
            raise RuntimeError("Model not loaded within timeout")
        
        # Get configuration
        async with self._get_model_config() as config:
            temperature = config['temperature']
            top_p = config['top_p']
            system_prompt = config['system_prompt']
        
        # Check cache for identical requests
        cache_key = self._get_cache_key(query, context[:500], {  # Use truncated context for cache
            'temperature': temperature,
            'top_p': top_p
        })
        
        cached_response = performance_optimizer.get_cached_result(cache_key)
        if cached_response:
            logger.debug(f"Cache hit for query: {query[:50]}...")
            # Stream cached response
            for token in cached_response['tokens']:
                yield token
                await asyncio.sleep(0.01)  # Simulate streaming
            return
        
        prompt = self._build_optimized_prompt(query, context, system_prompt)
        
        # Generate tokens in executor to avoid blocking
        def generate_tokens():
            with self.model_lock:
                return self.model(
                    prompt,
                    max_tokens=1500,
                    temperature=temperature,
                    top_p=top_p,
                    echo=False,
                    stream=True,
                    stop=["</s>", "[/INST]", "User:", "Query:"],
                    repeat_penalty=1.1,  # Prevent repetition
                    top_k=40,  # Limit vocabulary
                )
        
        # Run generation in thread pool
        loop = asyncio.get_event_loop()
        
        try:
            token_generator = await loop.run_in_executor(self.executor, generate_tokens)
            
            # Stream tokens and collect for caching
            full_response = ""
            cached_tokens = []
            
            for token_data in token_generator:
                if 'choices' in token_data and len(token_data['choices']) > 0:
                    token = token_data['choices'][0]['text']
                    if token:
                        full_response += token
                        cached_tokens.append(token)
                        yield token
                        # Adaptive delay based on token length
                        await asyncio.sleep(0.005 if len(token) < 5 else 0.01)
            
            # Cache successful responses
            if full_response.strip() and len(cached_tokens) > 3:
                performance_optimizer.cache_result(
                    cache_key,
                    {'tokens': cached_tokens, 'full_response': full_response},
                    ttl_seconds=3600  # Cache for 1 hour
                )
                
        except Exception as e:
            logger.error(f"Error in stream generation: {e}")
            yield f"I apologize, but I encountered an error generating the response: {str(e)}"
    
    @timed("llm_generation_complete")
    async def generate(self, query: str, context: str) -> str:
        """Generate complete response with optimizations"""
        
        # Wait for model to be loaded
        if not await self._wait_for_model():
            raise RuntimeError("Model not loaded within timeout")
        
        # Get configuration
        async with self._get_model_config() as config:
            temperature = config['temperature']
            top_p = config['top_p']
            system_prompt = config['system_prompt']
        
        # Check cache
        cache_key = self._get_cache_key(query, context[:500], {
            'temperature': temperature,
            'top_p': top_p
        })
        
        cached_response = performance_optimizer.get_cached_result(cache_key)
        if cached_response:
            logger.debug(f"Cache hit for complete generation: {query[:50]}...")
            return cached_response['full_response']
        
        prompt = self._build_optimized_prompt(query, context, system_prompt)
        
        # Generate complete response
        loop = asyncio.get_event_loop()
        
        def generate_complete():
            with self.model_lock:
                return self.model(
                    prompt,
                    max_tokens=1500,
                    temperature=temperature,
                    top_p=top_p,
                    echo=False,
                    stream=False,
                    stop=["</s>", "[/INST]", "User:", "Query:"],
                    repeat_penalty=1.1,
                    top_k=40,
                )
        
        try:
            result = await loop.run_in_executor(self.executor, generate_complete)
            
            if 'choices' in result and len(result['choices']) > 0:
                response = result['choices'][0]['text'].strip()
                
                # Cache successful responses
                if response and len(response) > 10:
                    performance_optimizer.cache_result(
                        cache_key,
                        {'full_response': response},
                        ttl_seconds=3600
                    )
                
                return response
            
        except Exception as e:
            logger.error(f"Error in complete generation: {e}")
            
        return "I apologize, but I couldn't generate a response. Please try again."
    
    def update_parameters(self, temperature: float, top_p: float):
        """Update model generation parameters and clear cache"""
        # Clear config cache to force reload
        cache_key = "model_config"
        if cache_key in performance_optimizer.cache:
            del performance_optimizer.cache[cache_key]
            del performance_optimizer.cache_ttl[cache_key]
        
        logger.info(f"Model parameters updated: temperature={temperature}, top_p={top_p}")
    
    async def reload_model(self):
        """Reload the model with current configuration"""
        try:
            logger.info("🔄 Reloading optimized model...")
            
            # Stop current operations
            with self.model_lock:
                old_model = self.model
                self.model = None
            
            # Clean up old model
            if old_model:
                del old_model
            
            # Reload in background
            self._preload_model()
            
            # Wait for new model to load
            if await self._wait_for_model(timeout=60):
                logger.info("✅ Model reloaded successfully")
            else:
                logger.error("❌ Model reload timeout")
                
        except Exception as e:
            logger.error(f"Failed to reload model: {e}")
            raise
    
    def get_model_stats(self) -> Dict:
        """Get model performance statistics"""
        return {
            'model_loaded': self.model is not None,
            'model_path': self.settings.model_path,
            'cache_size': len(performance_optimizer.cache),
            'executor_threads': self.executor._max_workers,
            'memory_usage_mb': performance_optimizer.performance_metrics['memory_usage']
        }
    
    async def benchmark_generation(self, query: str, context: str, iterations: int = 5) -> Dict:
        """Benchmark generation performance"""
        times = []
        cache_hits = 0
        
        for i in range(iterations):
            # Clear cache for fair benchmarking (except first iteration)
            if i > 0:
                cache_key = self._get_cache_key(query, context[:500], {'temperature': 0.7, 'top_p': 1.0})
                if cache_key in performance_optimizer.cache:
                    del performance_optimizer.cache[cache_key]
                    del performance_optimizer.cache_ttl[cache_key]
            
            start_time = time.time()
            response = await self.generate(query, context)
            end_time = time.time()
            
            if response and "error" not in response.lower():
                times.append(end_time - start_time)
            else:
                logger.warning(f"Benchmark iteration {i} failed")
        
        if times:
            return {
                'query': query[:50] + "...",
                'iterations': len(times),
                'avg_time_s': round(sum(times) / len(times), 3),
                'min_time_s': round(min(times), 3),
                'max_time_s': round(max(times), 3),
                'tokens_per_second': round(50 / (sum(times) / len(times)), 1)  # Estimate
            }
        else:
            return {'error': 'All benchmark iterations failed'}
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.executor:
                self.executor.shutdown(wait=True)
            
            with self.model_lock:
                if self.model:
                    del self.model
                    self.model = None
            
            logger.info("✅ LLM client cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")