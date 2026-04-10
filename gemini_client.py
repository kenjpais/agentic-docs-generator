"""Gemini LLM client for generating documentation."""

import os
import time
from typing import Optional
from google import genai
from google.genai import types
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for interacting with Google Gemini API."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "models/gemini-2.5-flash"):
        """
        Initialize Gemini client.

        Args:
            api_key: Gemini API key
            model_name: Name of the Gemini model to use
        """
        api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required")

        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def generate(self, prompt: str, max_retries: int = 3) -> str:
        """
        Generate content using Gemini.

        Args:
            prompt: The prompt to send to Gemini
            max_retries: Maximum number of retry attempts

        Returns:
            Generated text content
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"Generating content with Gemini (attempt {attempt + 1}/{max_retries})")

                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.7,
                        top_p=0.8,
                        top_k=40,
                        max_output_tokens=2048,
                    )
                )

                if response.text:
                    logger.info("Successfully generated content")
                    return response.text
                else:
                    logger.warning("Empty response from Gemini")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    return ""

            except Exception as e:
                logger.error(f"Error generating content: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise

        return ""

    def generate_with_safety(self, prompt: str) -> str:
        """
        Generate content with additional safety settings.

        Args:
            prompt: The prompt to send to Gemini

        Returns:
            Generated text content
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=2048,
                    safety_settings=[
                        types.SafetySetting(
                            category='HARM_CATEGORY_HARASSMENT',
                            threshold='BLOCK_NONE'
                        ),
                        types.SafetySetting(
                            category='HARM_CATEGORY_HATE_SPEECH',
                            threshold='BLOCK_NONE'
                        ),
                        types.SafetySetting(
                            category='HARM_CATEGORY_SEXUALLY_EXPLICIT',
                            threshold='BLOCK_NONE'
                        ),
                        types.SafetySetting(
                            category='HARM_CATEGORY_DANGEROUS_CONTENT',
                            threshold='BLOCK_NONE'
                        ),
                    ]
                )
            )
            return response.text if response.text else ""
        except Exception as e:
            logger.error(f"Error generating content with safety settings: {str(e)}")
            # Fallback to regular generation
            return self.generate(prompt)
