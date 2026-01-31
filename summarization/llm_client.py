"""
LLM client with retry logic and model fallback.
"""
import anthropic
from openai import OpenAI
import time
import json
from typing import Optional, List, Dict, Any
from enum import Enum
import logging

from config import settings

logger = logging.getLogger(__name__)


class ModelProvider(Enum):
    """Supported LLM providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class LLMClient:
    """Unified LLM client with retry and fallback."""
    
    def __init__(
        self,
        primary_model: Optional[str] = None,
        fallback_model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096
    ):
        """
        Initialize LLM client.
        
        Args:
            primary_model: Primary model to use
            fallback_model: Fallback model if primary fails
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
        """
        self.primary_model = primary_model or settings.primary_model
        self.fallback_model = fallback_model or settings.fallback_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize clients
        self.anthropic_client = None
        self.openai_client = None
        
        if settings.anthropic_api_key:
            self.anthropic_client = anthropic.Anthropic(
                api_key=settings.anthropic_api_key
            )
        
        if settings.openai_api_key:
            self.openai_client = OpenAI(
                api_key=settings.openai_api_key
            )
    
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False
    ) -> str:
        """
        Get completion from LLM.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            temperature: Override default temperature
            max_tokens: Override default max tokens
            json_mode: Request JSON response
            
        Returns:
            Model response text
            
        Raises:
            RuntimeError: If all attempts fail
        """
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens if max_tokens is not None else self.max_tokens
        
        # Try primary model
        try:
            return self._call_model(
                self.primary_model,
                prompt,
                system_prompt,
                temp,
                max_tok,
                json_mode
            )
        except Exception as e:
            logger.warning(f"Primary model {self.primary_model} failed: {e}")
            
            # Try fallback model if available
            if self.fallback_model:
                try:
                    logger.info(f"Attempting fallback to {self.fallback_model}")
                    return self._call_model(
                        self.fallback_model,
                        prompt,
                        system_prompt,
                        temp,
                        max_tok,
                        json_mode
                    )
                except Exception as fallback_error:
                    logger.error(f"Fallback model {self.fallback_model} failed: {fallback_error}")
                    raise RuntimeError(f"All models failed. Last error: {fallback_error}")
            else:
                raise RuntimeError(f"Model failed and no fallback configured: {e}")
    
    def _call_model(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        json_mode: bool
    ) -> str:
        """Call specific model with retry logic."""
        provider = self._get_provider(model)
        
        for attempt in range(settings.max_retries):
            try:
                if attempt > 0:
                    delay = settings.rate_limit_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Retry attempt {attempt + 1}, waiting {delay}s")
                    time.sleep(delay)
                
                if provider == ModelProvider.ANTHROPIC:
                    return self._call_anthropic(
                        model, prompt, system_prompt, temperature, max_tokens
                    )
                elif provider == ModelProvider.OPENAI:
                    return self._call_openai(
                        model, prompt, system_prompt, temperature, max_tokens, json_mode
                    )
                else:
                    raise ValueError(f"Unknown provider for model: {model}")
                    
            except Exception as e:
                if attempt == settings.max_retries - 1:
                    raise
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
        
        raise RuntimeError("Max retries exceeded")
    
    def _call_anthropic(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Call Anthropic API."""
        if not self.anthropic_client:
            raise RuntimeError("Anthropic client not initialized")
        
        messages = [{"role": "user", "content": prompt}]
        
        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
        
        response = self.anthropic_client.messages.create(**kwargs)
        
        return response.content[0].text
    
    def _call_openai(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        json_mode: bool
    ) -> str:
        """Call OpenAI API."""
        if not self.openai_client:
            raise RuntimeError("OpenAI client not initialized")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        
        response = self.openai_client.chat.completions.create(**kwargs)
        
        return response.choices[0].message.content
    
    def _get_provider(self, model: str) -> ModelProvider:
        """Determine provider from model name."""
        if model.startswith("claude"):
            return ModelProvider.ANTHROPIC
        elif model.startswith("gpt"):
            return ModelProvider.OPENAI
        else:
            raise ValueError(f"Cannot determine provider for model: {model}")
    
    def parse_json_response(self, response: str) -> dict:
        """
        Parse JSON response, handling markdown code blocks.
        
        Args:
            response: LLM response that should contain JSON
            
        Returns:
            Parsed JSON dictionary
            
        Raises:
            ValueError: If response is not valid JSON
        """
        # Remove markdown code blocks if present
        cleaned = response.strip()
        if cleaned.startswith("```"):
            # Remove opening ```json or ```
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            # Remove closing ```
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
        
        try:
            return json.loads(cleaned.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response[:200]}")
            raise ValueError(f"Invalid JSON response: {e}")
