"""LLM client wrapper for Groq API."""

import logging
from typing import List, Dict
from groq import Groq

from app.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMClient:
    """Wrapper for Groq API to generate conversational responses."""
    
    def __init__(self, api_key: str = None, model_name: str = None, temperature: float = None):
        """
        Initialize the LLM client.
        
        Args:
            api_key: Groq API key (defaults to config)
            model_name: Model name to use (defaults to config)
            temperature: Temperature for generation (defaults to config)
            
        Raises:
            ValueError: If API key is missing
        """
        self.api_key = api_key or config.GROQ_API_KEY
        self.model_name = model_name or config.MODEL_NAME
        self.temperature = temperature if temperature is not None else config.TEMPERATURE
        
        if not self.api_key:
            raise ValueError(
                "Groq API key is required. Please set GROQ_API_KEY in your .env file or environment variables."
            )
        
        logger.info(f"Initializing LLM client with model: {self.model_name}")
        logger.info(f"Temperature: {self.temperature}")
        
        try:
            self.client = Groq(api_key=self.api_key)
            logger.info("LLM client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            raise
    
    def generate(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 1024
    ) -> str:
        """
        Generate a response using the LLM.
        
        Args:
            system_prompt: System prompt defining behavior
            messages: List of message dictionaries with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
            
        Raises:
            Exception: If API request fails
        """
        try:
            # Prepare messages with system prompt
            full_messages = [
                {"role": "system", "content": system_prompt}
            ] + messages
            
            logger.info(f"Generating response with {len(messages)} messages")
            logger.debug(f"System prompt length: {len(system_prompt)} chars")
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=full_messages,
                temperature=self.temperature,
                max_tokens=max_tokens,
                top_p=1.0,
                stream=False
            )
            
            # Extract generated text
            generated_text = response.choices[0].message.content
            
            # Log token usage
            if hasattr(response, 'usage'):
                logger.info(
                    f"Token usage - Prompt: {response.usage.prompt_tokens}, "
                    f"Completion: {response.usage.completion_tokens}, "
                    f"Total: {response.usage.total_tokens}"
                )
            
            logger.info(f"Generated response length: {len(generated_text)} chars")
            
            return generated_text
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise Exception(f"Failed to generate response: {str(e)}")
    
    def generate_with_fallback(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        fallback_message: str = "I apologize, but I'm having trouble generating a response right now. Please try again."
    ) -> str:
        """
        Generate a response with fallback on error.
        
        Args:
            system_prompt: System prompt defining behavior
            messages: List of message dictionaries
            fallback_message: Message to return if generation fails
            
        Returns:
            Generated text or fallback message
        """
        try:
            return self.generate(system_prompt, messages)
        except Exception as e:
            logger.warning(f"Using fallback message due to error: {e}")
            return fallback_message
