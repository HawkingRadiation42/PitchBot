"""
Audio transcription using OpenAI's gpt-4o-transcribe model.
"""

import os
import asyncio
from pathlib import Path
from typing import Optional

import aiofiles
from openai import AsyncOpenAI
import whisper
import torch
import io
from pydub import AudioSegment
import numpy as np
from fastapi import UploadFile

from .config import AudioProcessingConfig, default_config


class AudioTranscriber:
    """Handles audio transcription using local Whisper models."""
    
    def __init__(self, config: Optional[AudioProcessingConfig] = None):
        """Initialize the audio transcriber with configuration."""
        self.config = config or default_config
        
        self.model_name = self.config.whisper_model
        self.language = self.config.language
        
        try:
            print(f"Loading Whisper model: {self.model_name}...")
            self.model = whisper.load_model(self.model_name)
            self.fp16 = torch.cuda.is_available()
            print(f"✅ Whisper model '{self.model_name}' loaded successfully.")
        except Exception as e:
            raise RuntimeError(f"Failed to load Whisper model '{self.model_name}': {str(e)}")
        
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
    
    async def transcribe(self, audio_file: UploadFile) -> str:
        """
        Transcribe audio file from in-memory data to text.
        
        Args:
            audio_file: UploadFile object containing audio data.
            
        Returns:
            Transcribed text
        """
        if not audio_file:
            raise ValueError("Audio file is not provided")
        
        try:
            # Read the audio data from the in-memory file
            audio_data = await audio_file.read()
            
            # Use pydub to load audio from bytes and process it
            sound = AudioSegment.from_file(io.BytesIO(audio_data))
            
            # Resample to 16kHz, which is required by Whisper
            sound = sound.set_frame_rate(16000)
            # Ensure it's single channel (mono)
            sound = sound.set_channels(1)
            
            # Convert to a NumPy array of float32
            # Pydub samples are signed integers, so we normalize to [-1, 1]
            samples = np.array(sound.get_array_of_samples()).astype(np.float32) / (2**(sound.sample_width * 8 - 1))
            
            # Transcribe the audio data
            result = self.model.transcribe(
                samples, 
                fp16=self.fp16,
                language=self.language
            )
            
            transcribed_text = result["text"].strip()
            
            if not transcribed_text:
                raise ValueError("Transcription resulted in empty text")
                
            return transcribed_text
            
        except Exception as e:
            # Add filename to error for better debugging
            raise RuntimeError(f"Transcription for {audio_file.filename} failed: {str(e)}") from e
            
    def update_model(self, model_name: str):
        """Update the model used for transcription."""
        try:
            self.model = whisper.load_model(model_name)
            self.fp16 = self.model.is_multilingual # Check if the new model is multilingual
            print(f"✅ Whisper model updated to '{model_name}'.")
        except Exception as e:
            raise RuntimeError(f"Failed to load Whisper model '{model_name}': {str(e)}")
        
    async def transcribe_file(self, file_path: str) -> str:
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