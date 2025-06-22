"""
Main entry point for PitchBot application.
"""

import sys
import asyncio
from typing import Optional
import argparse

from .audio_processor import AudioProcessor


def main(args: Optional[list[str]] = None) -> int:
    """
    Main entry point for PitchBot.
    
    Args:
        args: Command line arguments (defaults to sys.argv[1:])
        
    Returns:
        Exit code (0 for success)
    """
    if args is None:
        args = sys.argv[1:]
    
    parser = argparse.ArgumentParser(
        description="PitchBot - AI-powered pitch assistant"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Audio processing command
    audio_parser = subparsers.add_parser(
        "process-audio", 
        help="Process audio file: transcribe and summarize"
    )
    audio_parser.add_argument(
        "file_path", 
        help="Absolute path to the audio file"
    )
    audio_parser.add_argument(
        "--custom-prompt", 
        help="Custom prompt for summarization (optional)"
    )
    
    # Parse arguments
    parsed_args = parser.parse_args(args)
    
    if parsed_args.command == "process-audio":
        # Run async command with asyncio.run()
        return asyncio.run(_process_audio_command(parsed_args))
    else:
        print("🤖 PitchBot v0.1.0")
        print("AI-powered pitch assistant")
        print("\nAvailable commands:")
        print("  process-audio <file_path>  - Process audio file")
        print("\nExample:")
        print("  pitchbot process-audio /path/to/audio.opus")
        return 0


async def _process_audio_command(args) -> int:
    """Handle audio processing command asynchronously."""
    try:
        processor = AudioProcessor()
        result = await processor.process_audio(
            args.file_path, 
            args.custom_prompt
        )
        processor.print_result(result)
        return 0
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 