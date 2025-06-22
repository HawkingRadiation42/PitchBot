"""
Configuration settings for audio processing.
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class AudioProcessingConfig:
    """Configuration for audio processing pipeline."""
    
    # Whisper Configuration
    whisper_model: str = "base"
    language: str = "en"

    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o" # For summarization, not transcription
    openai_base_url: Optional[str] = None
    
    # Llama Configuration
    llama_api_key: Optional[str] = None
    llama_model: str = "Llama-4-Maverick-17B-128E-Instruct-FP8"
    llama_base_url: str = "https://api.llama-api.com/v1"
    
    # Processing Configuration
    max_file_size_mb: int = 100
    supported_formats: tuple = (".opus", ".mp3", ".wav", ".m4a", ".flac", ".ogg")
    
    def __post_init__(self):
        """Load API keys from environment if not provided."""
        if self.openai_api_key is None:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if self.llama_api_key is None:
            self.llama_api_key = os.getenv("LLAMA_API_KEY")
    
    def validate(self) -> bool:
        """Validate that required configuration is present."""
        # The local whisper model does not need an API key.
        # We only need the Llama key for the summarization/scoring part.
        if not self.llama_api_key:
            raise ValueError("Llama API key is required. Set LLAMA_API_KEY environment variable.")
        
        return True


# Default configuration instance
default_config = AudioProcessingConfig() 