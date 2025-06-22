"""
Configuration for the agentic search module.
"""

import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class LlamaConfig:
    """Configuration for Llama API client."""
    
    llama_api_key: Optional[str] = None
    llama_model: str = "Llama-4-Maverick-17B-128E-Instruct-FP8"
    llama_base_url: str = "https://api.llama-api.com"
    
    def __post_init__(self):
        """Load API keys from environment if not provided."""
        if self.llama_api_key is None:
            self.llama_api_key = os.getenv("LLAMA_API_KEY")
    
    def validate(self):
        """Validate that required configuration is present."""
        if not self.llama_api_key:
            raise ValueError("Llama API key is required. Set LLAMA_API_KEY environment variable.")
        
        if not self.llama_model:
            raise ValueError("Llama model is not specified.")
        
        return True


# Default configuration instance
default_config = LlamaConfig() 