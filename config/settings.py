"""
Configuration settings for InvestIQ financial agent system.
Loads environment variables and provides typed configuration.
"""
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    alphavantage_api_key: Optional[str] = None
    news_api_key: Optional[str] = None
    
    # Database Configuration - Supabase
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    
    # AI/LLM Configuration - Updated for Gemini
    google_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.5-flash"  # Fast and cost-effective
    max_tokens: int = 2048  # Reduced to save quota
    temperature: float = 0.1  # Lower for more focused responses
    
    # Legacy OpenAI (keeping for backward compatibility)
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-3.5-turbo"
    
    # Application settings
    debug: bool = True
    app_name: str = "InvestIQ Financial Agent"
    version: str = "2.0.0"
    
    # API Configuration
    request_timeout: int = 30
    max_retries: int = 3
    cache_ttl: int = 300  # 5 minutes
    
    # AI Agent Configuration
    max_concurrent_requests: int = 5
    agent_timeout: int = 60
    enable_memory: bool = True
    
    # Agent Selection (Choose one agent type)
    use_optimized_agent: bool = False  # Hybrid agent with manual planning (3-4 LLM calls)
    use_autonomous_agent: bool = True  # Autonomous agent with intelligent batching (3-4 LLM calls)
    enable_parallel_fetching: bool = True  # Enable parallel data fetching
    max_planning_tokens: int = 1024  # Tokens for planning phase
    
    model_config = {
        'env_file': '.env',
        'env_file_encoding': 'utf-8'
    }


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance."""
    return settings