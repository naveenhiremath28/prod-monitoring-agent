"""
LLM Factory for creating and configuring different LLM providers
"""
import tiktoken
from typing import Tuple, Optional, Any
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.callbacks.manager import CallbackManager

from .config import LLMConfig

class TokenCountingHandler(BaseCallbackHandler):
    """Custom callback handler for counting tokens"""
    
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer
        self.total_tokens = 0
    
    def on_llm_start(self, serialized: dict, prompts: list, **kwargs) -> None:
        """Called when LLM starts"""
        for prompt in prompts:
            self.total_tokens += len(self.tokenizer(prompt))
    
    def on_llm_end(self, response: Any, **kwargs) -> None:
        """Called when LLM ends"""
        if hasattr(response, 'generations'):
            for generation in response.generations:
                for gen in generation:
                    if hasattr(gen, 'text'):
                        self.total_tokens += len(self.tokenizer(gen.text))

class LLMFactory:
    """Factory class for creating LLM instances"""
    
    @staticmethod
    def create_llm(llm_class: str = "AzureOpenAI", model_params: Optional[dict] = None) -> Tuple[Any, TokenCountingHandler]:
        """
        Create LLM instance based on the specified class
        
        Args:
            llm_class: Type of LLM to create ("AzureOpenAI" or "OpenAI")
            model_params: Additional model parameters
            
        Returns:
            Tuple of (llm_instance, token_counter)
        """
        if model_params is None:
            model_params = {}
        
        if llm_class == "AzureOpenAI":
            return LLMFactory._create_azure_openai(model_params)
        elif llm_class == "OpenAI":
            return LLMFactory._create_openai(model_params)
        else:
            raise ValueError(f"Unsupported LLM class: {llm_class}")
    
    @staticmethod
    def _create_azure_openai(model_params: dict) -> Tuple[AzureChatOpenAI, TokenCountingHandler]:
        """Create Azure OpenAI LLM instance"""
        config = LLMConfig.get_azure_openai_config()
        
        if not LLMConfig.validate_azure_config(config):
            raise ValueError("Invalid Azure OpenAI configuration. Please check your environment variables.")
        
        # Merge with provided parameters
        config.update(model_params)
        
        # Remove any extra parameters that might cause issues
        other_config = config.pop("other_config", None)
        
        llm = AzureChatOpenAI(**config)
        
        # Create token counter
        try:
            tokenizer = tiktoken.encoding_for_model(config["model"]).encode
        except KeyError:
            # Fallback to cl100k_base encoding for unknown models
            tokenizer = tiktoken.get_encoding("cl100k_base").encode
        
        token_counter = TokenCountingHandler(tokenizer=tokenizer)
        llm.callback_manager = CallbackManager([token_counter])
        
        return llm, token_counter
    
    @staticmethod
    def _create_openai(model_params: dict) -> Tuple[ChatOpenAI, TokenCountingHandler]:
        """Create OpenAI LLM instance"""
        config = LLMConfig.get_openai_config()
        
        if not LLMConfig.validate_openai_config(config):
            raise ValueError("Invalid OpenAI configuration. Please check your environment variables.")
        
        # Merge with provided parameters
        config.update(model_params)
        
        # Remove any extra parameters that might cause issues
        other_config = config.pop("other_config", None)
        config.pop("api_endpoint", None)
        
        llm = ChatOpenAI(**config)
        
        # Create token counter
        try:
            tokenizer = tiktoken.encoding_for_model(config["model"]).encode
        except KeyError:
            # Fallback to cl100k_base encoding for unknown models
            tokenizer = tiktoken.get_encoding("cl100k_base").encode
        
        token_counter = TokenCountingHandler(tokenizer=tokenizer)
        llm.callback_manager = CallbackManager([token_counter])
        
        return llm, token_counter
