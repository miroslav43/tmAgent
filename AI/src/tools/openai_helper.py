"""
OpenAI helper module for AI Agent tools
Replaces Gemini functionality with OpenAI GPT-4
"""

import os
from openai import OpenAI
from typing import Optional, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)


class OpenAIHelper:
    """Helper class for OpenAI API calls in AI Agent"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenAI client"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY must be set")
        
        self.client = OpenAI(api_key=self.api_key)
        logger.info("OpenAI helper initialized for AI Agent")
    
    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.1,
        max_tokens: int = 1000,
        response_format: Optional[str] = None
    ) -> str:
        """
        Generate text using OpenAI
        
        Args:
            prompt: User prompt
            system_instruction: System instruction
            model: OpenAI model (gpt-4o, gpt-4o-mini)
            temperature: Temperature (0-1)
            max_tokens: Max output tokens
            response_format: Optional format ("json" for JSON mode)
        
        Returns:
            Generated text
        """
        try:
            messages = []
            
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            
            messages.append({"role": "user", "content": prompt})
            
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            if response_format == "json":
                kwargs["response_format"] = {"type": "json_object"}
            
            response = self.client.chat.completions.create(**kwargs)
            
            result = response.choices[0].message.content
            logger.info(f"OpenAI generation successful with {model}")
            return result
            
        except Exception as e:
            logger.error(f"OpenAI generation failed: {str(e)}")
            # Return empty string instead of raising to prevent NoneType errors
            return ""
    
    def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.1,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Generate JSON response using OpenAI
        
        Args:
            prompt: User prompt
            system_instruction: System instruction
            model: OpenAI model
            temperature: Temperature
            max_tokens: Max tokens
        
        Returns:
            Parsed JSON dict
        """
        result = self.generate_text(
            prompt=prompt,
            system_instruction=system_instruction,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format="json"
        )
        
        try:
            return json.loads(result)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            # Try to extract JSON from markdown code blocks
            if "```json" in result:
                json_str = result.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            elif "```" in result:
                json_str = result.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            raise Exception(f"Invalid JSON response: {result[:200]}")


def get_openai_client() -> OpenAIHelper:
    """Get or create OpenAI helper instance"""
    return OpenAIHelper()
