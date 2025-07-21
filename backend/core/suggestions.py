"""
Follow-up question suggestions generation
"""
import re
from typing import List, Dict
import logging

from backend.core.llm_client import LLMClient

logger = logging.getLogger(__name__)

class SuggestionGenerator:
    """Generate contextual follow-up questions"""
    
    def __init__(self):
        self.llm_client = LLMClient()
        
        # Predefined suggestion templates for common IT topics
        self.suggestion_templates = {
            'password': [
                "How do I create a strong password?",
                "What are the password requirements?",
                "How often should I change my password?",
                "What is two-factor authentication?"
            ],
            'vpn': [
                "How do I connect to the VPN?", 
                "What if VPN connection fails?",
                "Can I use VPN on mobile devices?",
                "Which VPN server should I choose?"
            ],
            'printer': [
                "How do I add a network printer?",
                "What if my print job is stuck?",
                "How do I share a printer?",
                "How do I troubleshoot printer issues?"
            ],
            'email': [
                "How do I set up email on my phone?",
                "What is the email server configuration?",
                "How do I create an email signature?",
                "How do I set up an out-of-office message?"
            ],
            'network': [
                "How do I connect to WiFi?",
                "What if internet is slow?",
                "How do I troubleshoot network issues?",
                "What are the network security policies?"
            ],
            'software': [
                "How do I install new software?",
                "What software is approved for use?",
                "How do I update my applications?",
                "What if software won't start?"
            ]
        }
    
    async def generate_suggestions(self, query: str, context_chunks: List[Dict]) -> List[str]:
        """
        Generate contextual follow-up questions
        
        Args:
            query: User's original query
            context_chunks: Retrieved context chunks
            
        Returns:
            List of suggested follow-up questions
        """
        try:
            # First, try template-based suggestions
            template_suggestions = self._get_template_suggestions(query)
            
            if template_suggestions:
                return template_suggestions[:4]
            
            # Fall back to LLM-generated suggestions
            return await self._generate_llm_suggestions(query, context_chunks)
            
        except Exception as e:
            logger.warning(f"Suggestion generation failed: {e}")
            return self._get_fallback_suggestions()
    
    def _get_template_suggestions(self, query: str) -> List[str]:
        """Get suggestions based on predefined templates"""
        
        query_lower = query.lower()
        
        # Check for keywords in query
        for topic, suggestions in self.suggestion_templates.items():
            if topic in query_lower:
                # Filter out suggestions too similar to original query
                filtered_suggestions = []
                for suggestion in suggestions:
                    if not self._is_too_similar(query_lower, suggestion.lower()):
                        filtered_suggestions.append(suggestion)
                
                return filtered_suggestions[:4]
        
        return []
    
    def _is_too_similar(self, query1: str, query2: str) -> bool:
        """Check if two queries are too similar"""
        
        # Simple word overlap check
        words1 = set(re.findall(r'\\w+', query1))
        words2 = set(re.findall(r'\\w+', query2))
        
        # If more than 70% of words overlap, consider too similar
        if len(words1) == 0 or len(words2) == 0:
            return False
        
        overlap = len(words1.intersection(words2))
        similarity = overlap / min(len(words1), len(words2))
        
        return similarity > 0.7
    
    async def _generate_llm_suggestions(self, query: str, context_chunks: List[Dict]) -> List[str]:
        """Generate suggestions using LLM"""
        
        # Summarize context for prompt
        context_summary = ""
        if context_chunks:
            # Take key information from chunks
            topics = []
            for chunk in context_chunks[:3]:  # Use first 3 chunks
                # Extract topic indicators
                text_snippet = chunk['text'][:200] + "..." if len(chunk['text']) > 200 else chunk['text']
                topics.append(text_snippet)
            
            context_summary = " Related topics: " + " ".join(topics)
        
        prompt = f"""Based on this IT support question, suggest 4 related follow-up questions that users might ask next.

User asked: "{query}"{context_summary}

Generate 4 specific, actionable follow-up questions. Return only the questions, one per line:"""
        
        try:
            response = await self.llm_client.generate(prompt, "")
            
            # Parse suggestions from response
            suggestions = []
            for line in response.split('\\n'):
                line = line.strip()
                if line and not line.startswith('1.') and not line.startswith('-'):
                    # Clean up the line
                    line = re.sub(r'^\\d+\\.\\s*', '', line)  # Remove numbering
                    line = re.sub(r'^[-•]\\s*', '', line)     # Remove bullets
                    
                    if len(line) > 10 and line.endswith('?'):
                        suggestions.append(line)
            
            return suggestions[:4]
            
        except Exception as e:
            logger.warning(f"LLM suggestion generation failed: {e}")
            return self._get_fallback_suggestions()
    
    def _get_fallback_suggestions(self) -> List[str]:
        """Get generic fallback suggestions"""
        
        return [
            "How can I troubleshoot this issue?",
            "What are the system requirements?", 
            "Where can I find more documentation?",
            "Who should I contact for additional help?"
        ]

# Global instance for easy access
suggestion_generator = SuggestionGenerator()

async def generate_suggestions(query: str, context_chunks: List[Dict]) -> List[str]:
    """Convenience function for generating suggestions"""
    return await suggestion_generator.generate_suggestions(query, context_chunks)