"""
Configuration management for medical paper summarizer.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Literal


class Settings(BaseSettings):
    """Application settings with validation."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # API Keys
    anthropic_api_key: str = Field(default="", description="Anthropic API key")
    openai_api_key: str = Field(default="", description="OpenAI API key")
    
    # Model Configuration
    primary_model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Primary LLM model"
    )
    fallback_model: str = Field(
        default="gpt-4-turbo-preview",
        description="Fallback LLM model"
    )
    temperature: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="LLM temperature"
    )
    max_tokens: int = Field(
        default=4096,
        ge=512,
        le=8192,
        description="Maximum tokens per response"
    )
    
    # Chunking Configuration
    chunk_size: int = Field(
        default=1000,
        ge=500,
        le=2000,
        description="Target chunk size in tokens"
    )
    chunk_overlap: int = Field(
        default=200,
        ge=50,
        le=500,
        description="Overlap between chunks in tokens"
    )
    max_section_chunks: int = Field(
        default=20,
        ge=5,
        le=50,
        description="Maximum chunks per section"
    )
    
    # Processing Configuration
    max_retries: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum API retry attempts"
    )
    timeout: int = Field(
        default=60,
        ge=10,
        le=300,
        description="API timeout in seconds"
    )
    rate_limit_delay: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Delay between API calls in seconds"
    )
    
    @field_validator("chunk_overlap")
    @classmethod
    def validate_overlap(cls, v: int, info) -> int:
        """Ensure overlap is less than chunk size."""
        chunk_size = info.data.get("chunk_size", 1000)
        if v >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        return v


# Global settings instance
settings = Settings()
