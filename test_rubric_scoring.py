"""
Test script for the new structured JSON rubric scoring functionality.
"""

import asyncio
import json
from utils.rubric_scoring import RubricScorer


async def test_rubric_scoring():
    """Test the new rubric scoring functionality."""
    
    # Sample pitch content to test with
    test_pitch = """
    Our startup, EcoTrack, is developing an AI-powered mobile app that helps individuals 
    track their carbon footprint in real-time. The app connects to smart home devices, 
    transportation apps, and shopping platforms to automatically calculate environmental impact.
    
    The demo showed a working prototype where users can see their daily CO2 emissions, 
    get personalized recommendations to reduce their footprint, and compete with friends 
    in sustainability challenges. We've already tested with 100 beta users who reduced 
    their carbon footprint by an average of 23% in the first month.
    
    Our business model includes freemium subscriptions and partnerships with eco-friendly 
    brands. We're seeking $500K to scale our team and expand to corporate clients.
    
    The market for sustainability apps is growing rapidly, with climate consciousness 
    at an all-time high. Our unique AI approach and gamification elements set us apart 
    from existing carbon tracking solutions.
    """
    
    try:
        print("🧪 Testing new rubric scoring functionality...")
        print("=" * 60)
        
        # Initialize the scorer
        scorer = RubricScorer()
        print("✅ RubricScorer initialized successfully")
        
        # Test structured JSON scoring
        print("\n🎯 Testing structured JSON scoring...")
        structured_result = await scorer.score(test_pitch)
        
        print("✅ Structured scoring completed!")
        print("\n📊 JSON Result:")
        print(json.dumps(structured_result, indent=2))
        
        # Verify the structure
        expected_keys = ['impact', 'demo', 'creativity', 'pitch']
        for key in expected_keys:
            if key in structured_result:
                score = structured_result[key].get('score', 'Missing')
                justification = structured_result[key].get('justification', 'Missing')
                print(f"\n✅ {key.upper()}:")
                print(f"   Score: {score}/100")
                print(f"   Justification: {justification[:100]}...")
            else:
                print(f"❌ Missing key: {key}")
        
        # Test legacy format for backward compatibility
        print("\n🔄 Testing legacy format compatibility...")
        legacy_result = await scorer.score_legacy_format(test_pitch)
        print("✅ Legacy format test completed!")
        print("\n📝 Legacy Format Result:")
        print(legacy_result[:500] + "..." if len(legacy_result) > 500 else legacy_result)
        
        print("\n" + "=" * 60)
        print("🎉 All tests completed successfully!")
        
        return structured_result
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return None


async def main():
    """Main test function."""
    print("🚀 Starting Rubric Scoring Tests")
    print("This will test the new OpenAI SDK integration with Llama API")
    print("and structured JSON output format.")
    print()
    
    result = await test_rubric_scoring()
    
    if result:
        print("\n📈 Summary of Results:")
        total_score = sum(result[key]['score'] for key in result if 'score' in result[key])
        avg_score = total_score / 4
        print(f"Average Score: {avg_score:.1f}/100")
        
        # Show individual scores
        for criterion in ['impact', 'demo', 'creativity', 'pitch']:
            if criterion in result:
                score = result[criterion]['score']
                print(f"{criterion.title()}: {score}/100")


if __name__ == "__main__":
    asyncio.run(main()) 