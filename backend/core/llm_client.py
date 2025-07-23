"""
LLM client for Mistral 7B with streaming support
Uses llama-cpp-python for CPU-optimized inference with fallback support
"""
import asyncio
from typing import AsyncGenerator, Optional
import logging
import os

from backend.core.config import get_settings
from backend.models.database import get_config_value, SessionLocal

# Try to import llama-cpp-python, fallback to mock if not available
try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    logging.warning("llama-cpp-python not available, using fallback responses")

logger = logging.getLogger(__name__)

class LLMClient:
    """Mistral 7B LLM client with streaming capabilities"""
    
    def __init__(self):
        self.settings = get_settings()
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the Mistral model with CPU optimization or use fallback"""
        if not LLAMA_CPP_AVAILABLE:
            logger.warning("🔄 Using fallback LLM - llama-cpp-python not installed")
            self.model = None
            return
            
        if not os.path.exists(self.settings.model_path):
            logger.warning(f"🔄 Model file not found at {self.settings.model_path}, using fallback")
            self.model = None
            return
            
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
            logger.error(f"❌ Failed to load model: {e}, using fallback")
            self.model = None
    
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
            # Fallback response when model is not available
            fallback_response = self._generate_fallback_response(query, context)
            for char in fallback_response:
                yield char
                await asyncio.sleep(0.05)  # Simulate streaming
            return
        
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
            return self._generate_fallback_response(query, context)
        
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
    
    def _generate_fallback_response(self, query: str, context: str) -> str:
        """Generate a fallback response when the LLM is not available"""
        if context.strip():
            return f"""Based on the provided documentation, I can help answer your question about: "{query}"

The relevant information from the documentation shows:

{context[:500]}...

[Note: This is a fallback response. The full LLM model is not currently loaded. To get more detailed responses, please ensure the Mistral model is downloaded and available at the configured path.]

For immediate assistance, please refer to the source documentation or contact your IT support team."""
        else:
            return f"""I understand you're asking about: "{query}"

However, I don't have access to relevant documentation at the moment, and the full LLM model is not currently loaded.

[Note: This is a fallback response. To get detailed answers, please ensure:
1. Relevant documents are uploaded to the system
2. The Mistral model is downloaded and available
3. The vector database contains the necessary information]

For immediate assistance, please contact your IT support team."""
    
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