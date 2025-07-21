"""
LLM client for Mistral 7B with streaming support
Uses llama-cpp-python for CPU-optimized inference
"""
import asyncio
from typing import AsyncGenerator, Optional
import logging
from llama_cpp import Llama

from backend.core.config import get_settings
from backend.models.database import get_config_value, SessionLocal

logger = logging.getLogger(__name__)

class LLMClient:
    """Mistral 7B LLM client with streaming capabilities"""
    
    def __init__(self):
        self.settings = get_settings()
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the Mistral model with CPU optimization"""
        try:
            logger.info(f"Loading model from: {self.settings.model_path}")
            
            self.model = Llama(
                model_path=self.settings.model_path,
                n_ctx=4096,  # Context window
                n_threads=4,  # CPU threads
                n_gpu_layers=0,  # CPU only
                verbose=False
            )
            
            logger.info("✅ Mistral model loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            raise RuntimeError(f"Could not load LLM model: {e}")
    
    def _build_prompt(self, query: str, context: str) -> str:
        """Build the complete prompt with system instructions and context"""
        
        # Get current system prompt from database
        db = SessionLocal()
        try:
            system_prompt = get_config_value(
                db, 
                "system_prompt", 
                "You are an IT support assistant. Answer using only the provided documentation."
            )
        finally:
            db.close()
        
        prompt = f"""<s>[INST] {system_prompt}

Context:
{context}

User Query: {query}

Your Response: [/INST]"""
        
        return prompt
    
    async def generate_stream(self, query: str, context: str) -> AsyncGenerator[str, None]:
        """Generate streaming response from the LLM"""
        
        if not self.model:
            raise RuntimeError("Model not loaded")
        
        # Get current model parameters
        db = SessionLocal()
        try:
            temperature = float(get_config_value(db, "temperature", "0.7"))
            top_p = float(get_config_value(db, "top_p", "1.0"))
        finally:
            db.close()
        
        prompt = self._build_prompt(query, context)
        
        # Generate tokens in a separate thread to avoid blocking
        def generate_tokens():
            return self.model(
                prompt,
                max_tokens=1500,
                temperature=temperature,
                top_p=top_p,
                echo=False,
                stream=True,
                stop=["</s>", "[/INST]"]
            )
        
        # Run generation in thread pool
        loop = asyncio.get_event_loop()
        token_generator = await loop.run_in_executor(None, generate_tokens)
        
        # Stream tokens
        for token_data in token_generator:
            if 'choices' in token_data and len(token_data['choices']) > 0:
                token = token_data['choices'][0]['text']
                if token:
                    yield token
                    # Small delay for smooth streaming
                    await asyncio.sleep(0.01)
    
    async def generate(self, query: str, context: str) -> str:
        """Generate complete response (non-streaming)"""
        
        if not self.model:
            raise RuntimeError("Model not loaded")
        
        db = SessionLocal()
        try:
            temperature = float(get_config_value(db, "temperature", "0.7"))
            top_p = float(get_config_value(db, "top_p", "1.0"))
        finally:
            db.close()
        
        prompt = self._build_prompt(query, context)
        
        # Generate complete response
        loop = asyncio.get_event_loop()
        
        def generate_complete():
            return self.model(
                prompt,
                max_tokens=1500,
                temperature=temperature,
                top_p=top_p,
                echo=False,
                stream=False
            )
        
        result = await loop.run_in_executor(None, generate_complete)
        
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['text'].strip()
        
        return "I apologize, but I couldn't generate a response. Please try again."
    
    def update_parameters(self, temperature: float, top_p: float):
        """Update model generation parameters"""
        # Parameters are retrieved from database on each generation
        # This method exists for compatibility but parameters are stored in DB
        logger.info(f"Model parameters will be updated: temperature={temperature}, top_p={top_p}")
    
    def reload_model(self):
        """Reload the model (for configuration changes)"""
        try:
            self._load_model()
        except Exception as e:
            logger.error(f"Failed to reload model: {e}")
            raise