#!/usr/bin/env python3
"""
Simple test script for audio processing pipeline.
"""

import os
import asyncio
from pitchbot.audio_processor import AudioProcessor


async def main():
    """Test the audio processing pipeline asynchronously."""
    
    # Check environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable not set")
        return 1
    
    if not os.getenv("LLAMA_API_KEY"):
        print("❌ LLAMA_API_KEY environment variable not set")
        return 1
    
    print("✅ Environment variables set")
    
    # Initialize processor
    try:
        processor = AudioProcessor()
        print("✅ AudioProcessor initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize AudioProcessor: {e}")
        return 1
    
    print("\n🎵 Audio processing pipeline is ready!")
    
    # Test with actual file
    test_file = "/Users/deepanshgandhi/Downloads/audio.mp3"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        print("\nTo test with your own audio file, run:")
        print("  pitchbot process-audio /path/to/your/audio.opus")
        return 1
    
    print(f"\n🎵 Testing with file: {test_file}")
    print("🚀 Starting async audio processing...")
    
    try:
        result = await processor.process_audio(test_file)
        processor.print_result(result)
        print("\n✅ Async test completed successfully!")
        return 0
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        print("\nMake sure your environment variables are set:")
        print("  export OPENAI_API_KEY='your-openai-key'")
        print("  export LLAMA_API_KEY='your-llama-key'")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main())) 