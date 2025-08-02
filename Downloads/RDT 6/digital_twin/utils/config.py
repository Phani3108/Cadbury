"""
Configuration management for Digital Twin.
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from pydantic import Field
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

# Load environment-specific config
load_dotenv(f".env.{os.getenv('MODE','development')}", override=True)

class Settings(BaseSettings):
    """Application settings with environment-specific defaults."""
    
    # Environment
    MODE: str = Field(default="dev", env="MODE")
    SEARCH_BACKEND: str = Field(default="chroma", env="SEARCH_BACKEND")
    LLM_CHEAP: str = Field(default="gpt-3.5-turbo", env="LLM_CHEAP")
    LLM_HEAVY: str = Field(default="gpt-4o-mini", env="LLM_HEAVY")
    TOOLS_MOCK: bool = Field(default=True, env="TOOLS_MOCK")
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    OPENAI_API_TYPE: str = Field(default="openai", env="OPENAI_API_TYPE")
    
    # Local Search
    CHROMA_PERSIST_DIRECTORY: str = Field(default="./data/chroma", env="CHROMA_PERSIST_DIRECTORY")
    
    # Local Data
    DATA_DIR: str = Field(default="./data", env="DATA_DIR")
    CACHE_DIR: str = Field(default="./cache", env="CACHE_DIR")
    
    # Development Features
    RERANKER_ENABLED: bool = Field(default=False, env="RERANKER_ENABLED")
    ADVANCED_RAG: bool = Field(default=False, env="ADVANCED_RAG")
    QDF_ENABLED: bool = Field(default=True, env="QDF_ENABLED")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="{time} | {level} | {name} | {message}", env="LOG_FORMAT")
    
    # Testing
    DEEPEVAL_GROUNDING_THRESHOLD: float = Field(default=0.9, env="DEEPEVAL_GROUNDING_THRESHOLD")
    TOKEN_COST_LIMIT: int = Field(default=100000, env="TOKEN_COST_LIMIT")
    
    # Azure (for future prod)
    AZURE_OPENAI_ENDPOINT: Optional[str] = Field(default=None, env="AZURE_OPENAI_ENDPOINT")
    AZURE_SEARCH_ENDPOINT: Optional[str] = Field(default=None, env="AZURE_SEARCH_ENDPOINT")
    AZURE_SEARCH_KEY: Optional[str] = Field(default=None, env="AZURE_SEARCH_KEY")
    AZURE_LOG_ANALYTICS_WORKSPACE_ID: Optional[str] = Field(default=None, env="AZURE_LOG_ANALYTICS_WORKSPACE_ID")
    TEAMS_WEBHOOK_URL: Optional[str] = Field(default=None, env="TEAMS_WEBHOOK_URL")

def get_settings() -> Settings:
    """Get application settings."""
    return Settings()

def openai_kwargs(model_key: str) -> Dict[str, Any]:
    """Generate OpenAI API kwargs based on environment."""
    if os.getenv("OPENAI_API_TYPE") == "azure":
        return dict(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("AZURE_OPENAI_ENDPOINT")+"/openai/deployments/",
            default_model=os.getenv(model_key),
            api_type="azure",
            api_version="2024-06-01-preview",
        )
    return dict(
        api_key=os.getenv("OPENAI_API_KEY")
    )

def get_model_key(is_heavy: bool = False) -> str:
    """Get the appropriate model key based on workload."""
    return "LLM_HEAVY" if is_heavy else "LLM_CHEAP"

def is_development() -> bool:
    """Check if running in development mode."""
    return os.getenv("MODE") == "dev"

def is_production() -> bool:
    """Check if running in production mode."""
    return os.getenv("MODE") == "prod"

def is_local_search() -> bool:
    """Check if using local search backend."""
    return os.getenv("SEARCH_BACKEND") == "chroma"

def is_mock_tools() -> bool:
    """Check if tools should be mocked."""
    return os.getenv("TOOLS_MOCK", "true").lower() == "true" 