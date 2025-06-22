"""
Main audio processing pipeline that orchestrates transcription and summarization.
"""

import asyncio
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from .config import AudioProcessingConfig, default_config
from .transcriber import AudioTranscriber
from .summarizer import TextSummarizer


@dataclass
class ProcessingResult:
    """Result of audio processing pipeline."""
    file_path: str
    transcribed_text: str
    summary: str
    processing_time_seconds: float
    timestamp: datetime
    metadata: Dict[str, Any]


class AudioProcessor:
    """Main audio processing pipeline that handles the complete workflow."""
    
    def __init__(self, config: Optional[AudioProcessingConfig] = None):
        """Initialize the audio processor with configuration."""
        self.config = config or default_config
        self.transcriber = AudioTranscriber(self.config)
        self.summarizer = TextSummarizer(self.config)
    
    async def process_audio(
        self, 
        file_path: str,
        custom_prompt: Optional[str] = None
    ) -> ProcessingResult:
        """
        Process audio file through complete pipeline: transcription → summarization.
        
        Args:
            file_path: Absolute path to the audio file
            custom_prompt: Optional custom prompt for summarization
            
        Returns:
            ProcessingResult containing transcription, summary, and metadata
        """
        start_time = datetime.now()
        
        try:
            print(f"🎵 Starting async audio processing for: {file_path}")
            
            # Step 1: Transcribe audio to text
            print("📝 Transcribing audio...")
            transcribed_text = await self.transcriber.transcribe(file_path)
            #print(transcribed_text)
            print(f"✅ Transcription complete ({len(transcribed_text)} characters)")
            
            # Step 2: Update prompt if custom one provided
            if custom_prompt:
                self.summarizer.update_prompt_template(custom_prompt)
            
            # Step 3: Summarize transcribed text
            print("🤖 Generating summary...")
            summary = await self.summarizer.summarize(transcribed_text)
            print("✅ Summary complete")
            
            # Calculate processing time
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Create result
            result = ProcessingResult(
                file_path=file_path,
                transcribed_text=transcribed_text,
                summary=summary,
                processing_time_seconds=processing_time,
                timestamp=start_time,
                metadata={
                    "openai_model": self.config.openai_model,
                    "llama_model": self.config.llama_model,
                    "file_size_mb": self._get_file_size_mb(file_path),
                    "transcription_length": len(transcribed_text),
                    "summary_length": len(summary)
                }
            )
            
            print(f"🎉 Async processing complete in {processing_time:.1f} seconds")
            return result
            
        except Exception as e:
            print(f"❌ Processing failed: {str(e)}")
            raise
    
    def _get_file_size_mb(self, file_path: str) -> float:
        """Get file size in MB."""
        try:
            from pathlib import Path
            return Path(file_path).stat().st_size / (1024 * 1024)
        except Exception:
            return 0.0
    
    def print_result(self, result: ProcessingResult):
        """Print a formatted result."""
        print("\n" + "="*80)
        print(f"🎵 ASYNC AUDIO PROCESSING RESULT")
        print("="*80)
        print(f"📁 File: {result.file_path}")
        print(f"⏱️  Processing time: {result.processing_time_seconds:.1f} seconds")
        print(f"📊 File size: {result.metadata['file_size_mb']:.1f} MB")
        print(f"📝 Transcription length: {result.metadata['transcription_length']} characters")
        print(f"📋 Summary length: {result.metadata['summary_length']} characters")
        #print("\n📝 TRANSCRIPTION:")
        #print("-" * 40)
        #print(result.transcribed_text)
        print("\n📋 SUMMARY:")
        print("-" * 40)
        print(result.summary)
        print("="*80) 