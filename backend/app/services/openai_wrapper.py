"""
OpenAI wrapper for OCR and document processing
Alternative to Gemini when quota is exhausted
"""

import os
import base64
import logging
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class OpenAIProcessor:
    """Wrapper for OpenAI API to handle OCR and document processing"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenAI client"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY must be set")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o"  # GPT-4o supports vision
        logger.info("OpenAI processor initialized with model: gpt-4o")
    
    async def process_document_with_vision(
        self, 
        prompt: str, 
        file_data: bytes, 
        mime_type: str,
        temperature: float = 0.1,
        max_tokens: int = 8000
    ) -> str:
        """
        Process document using OpenAI Vision API
        
        Args:
            prompt: System prompt for OCR/analysis
            file_data: Document bytes
            mime_type: MIME type (image/jpeg, image/png, application/pdf)
            temperature: Model temperature
            max_tokens: Maximum output tokens
            
        Returns:
            Extracted text or analysis result
        """
        try:
            # Encode image to base64
            base64_image = base64.b64encode(file_data).decode('utf-8')
            
            # Determine image type
            if mime_type == "image/jpeg" or mime_type == "image/jpg":
                image_url = f"data:image/jpeg;base64,{base64_image}"
            elif mime_type == "image/png":
                image_url = f"data:image/png;base64,{base64_image}"
            elif mime_type == "application/pdf":
                # For PDF, we assume first page is converted to image
                image_url = f"data:image/jpeg;base64,{base64_image}"
            else:
                raise ValueError(f"Unsupported MIME type: {mime_type}")
            
            logger.info(f"Calling OpenAI Vision API for document processing")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url,
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            result = response.choices[0].message.content
            logger.info(f"OpenAI Vision API call successful")
            return result
            
        except Exception as e:
            logger.error(f"OpenAI Vision API call failed: {str(e)}")
            raise Exception(f"OpenAI processing failed: {str(e)}")
    
    async def process_text(
        self,
        prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1000,
        response_format: str = None
    ) -> str:
        """
        Process text-only request (e.g., metadata extraction)
        
        Args:
            prompt: Input prompt
            temperature: Model temperature
            max_tokens: Maximum output tokens
            response_format: Optional response format (e.g., "json_object")
            
        Returns:
            Model response
        """
        try:
            logger.info("Calling OpenAI API for text processing")
            
            kwargs = {
                "model": "gpt-4o-mini",  # Use mini for text-only tasks
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            if response_format == "json":
                kwargs["response_format"] = {"type": "json_object"}
            
            response = self.client.chat.completions.create(**kwargs)
            
            result = response.choices[0].message.content
            logger.info("OpenAI text API call successful")
            return result
            
        except Exception as e:
            logger.error(f"OpenAI text API call failed: {str(e)}")
            raise Exception(f"OpenAI text processing failed: {str(e)}")
