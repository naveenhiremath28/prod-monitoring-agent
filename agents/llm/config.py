"""
LLM Configuration module for Azure OpenAI integration
"""
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class LLMConfig:
    """Configuration class for LLM providers"""
    
    @staticmethod
    def get_azure_openai_config() -> Dict[str, Any]:
        """Get Azure OpenAI configuration from environment variables"""
        return {
            "azure_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
            "azure_deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            "model": os.getenv("AZURE_OPENAI_MODEL", "gpt-4"),
            "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
            "temperature": float(os.getenv("AZURE_OPENAI_TEMPERATURE", "0.1")),
            "max_tokens": int(os.getenv("AZURE_OPENAI_MAX_TOKENS", "500")),
        }
    
    @staticmethod
    def get_openai_config() -> Dict[str, Any]:
        """Get OpenAI configuration from environment variables"""
        return {
            "api_key": os.getenv("OPENAI_API_KEY"),
            "model": os.getenv("OPENAI_MODEL", "gpt-4"),
            "temperature": float(os.getenv("OPENAI_TEMPERATURE", "0.1")),
            "max_tokens": int(os.getenv("OPENAI_MAX_TOKENS", "500")),
        }
    
    @staticmethod
    def validate_azure_config(config: Dict[str, Any]) -> bool:
        """Validate Azure OpenAI configuration"""
        required_fields = ["azure_endpoint", "api_key", "azure_deployment"]
        return all(config.get(field) for field in required_fields)
    
    @staticmethod
    def validate_openai_config(config: Dict[str, Any]) -> bool:
        """Validate OpenAI configuration"""
        return bool(config.get("api_key"))
