"""
Audio transcription using OpenAI's gpt-4o-transcribe model.
"""

import os
import asyncio
from pathlib import Path
from typing import Optional

import aiofiles
from openai import AsyncOpenAI

from .config import AudioProcessingConfig, default_config


class AudioTranscriber:
    """Handles audio-to-text transcription using OpenAI's gpt-4o-transcribe."""
    
    def __init__(self, config: Optional[AudioProcessingConfig] = None):
        """Initialize the transcriber with configuration."""
        self.config = config or default_config
        self.config.validate()
        
        self.client = AsyncOpenAI(
            api_key=self.config.openai_api_key,
            base_url=self.config.openai_base_url
        )
    
    def _validate_audio_file(self, file_path: str) -> Path:
        """Validate that the audio file exists and has supported format."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        if path.suffix.lower() not in self.config.supported_formats:
            raise ValueError(
                f"Unsupported file format: {path.suffix}. "
                f"Supported formats: {', '.join(self.config.supported_formats)}"
            )
        
        # Check file size
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.config.max_file_size_mb:
            raise ValueError(
                f"File too large: {file_size_mb:.1f}MB. "
                f"Maximum size: {self.config.max_file_size_mb}MB"
            )
        
        return path
    
    async def transcribe(self, file_path: str) -> str:
        """
        Transcribe audio file to text using OpenAI's gpt-4o-transcribe.
        
        Args:
            file_path: Absolute path to the audio file
            
        Returns:
            Transcribed text
        """
        validated_path = self._validate_audio_file(file_path)
        
        try:
            # Read the audio file
            async with aiofiles.open(validated_path, 'rb') as audio_file:
                audio_data = await audio_file.read()
            
            # Call OpenAI transcription API
            response = await self.client.audio.transcriptions.create(
                model=self.config.openai_model,
                file=(validated_path.name, audio_data),
                response_format="text"
            )
            
            return response
            
        except Exception as e:
            raise RuntimeError(f"Transcription failed: {str(e)}") from e 