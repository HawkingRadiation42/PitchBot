#!/usr/bin/env python3
"""
Simple test script for audio processing pipeline.
"""

import os
import asyncio
from pitchbot.audio_processor import AudioProcessor
from utils.rubric_scoring import RubricScorer


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
    
    # Initialize processor and rubric scorer
    try:
        processor = AudioProcessor()
        print("✅ AudioProcessor initialized successfully")
        
        scorer = RubricScorer()
        print("✅ RubricScorer initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize components: {e}")
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
        # Step 1: Process audio (transcription + summarization)
        result = await processor.process_audio(test_file)
        processor.print_result(result)
        
        # Step 2: Score the summary using rubric
        print("\n🏆 Starting rubric scoring...")
        scoring_result = await scorer.score(result.summary)
        
        # Print rubric scoring results
        print("\n" + "="*80)
        print("🏆 RUBRIC SCORING RESULT")
        print("="*80)
        print(scoring_result)
        print("="*80)
        
        print("\n✅ Complete pipeline test completed successfully!")
        print("   ✅ Transcription → ✅ Summarization → ✅ Rubric Scoring")
        return 0
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        print("\nMake sure your environment variables are set:")
        print("  export OPENAI_API_KEY='your-openai-key'")
        print("  export LLAMA_API_KEY='your-llama-key'")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main())) 