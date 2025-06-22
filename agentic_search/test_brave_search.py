#!/usr/bin/env python3
"""
Test script for Brave Search API integration.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from .brave_search import BraveSearchClient

# Load environment variables
load_dotenv()

async def main() -> int:
    """
    Test the Brave Search API integration.
    """
    
    # Check environment variables
    if not os.getenv("BRAVE_API_KEY"):
        print("❌ BRAVE_API_KEY environment variable not set.")
        print("   Please add to your .env file: BRAVE_API_KEY='your-key'")
        print("   Get your free API key at: https://api.search.brave.com/")
        return 1
    
    print("✅ Environment variables set")

    # Initialize Brave Search client
    try:
        brave_client = BraveSearchClient()
        print("✅ BraveSearchClient initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize BraveSearchClient: {e}")
        return 1

    print("\n🔍 Brave Search API is ready!")
    
    # Test query - startup research related
    test_query = "AI freelance writing platform competitors market size"

    print(f"\n🚀 Testing search with query: '{test_query}'")

    try:
        # Perform the search
        search_response = await brave_client.search(test_query, count=5)
        
        # Print the formatted results
        brave_client.print_search_results(search_response)
        
        # Also show the raw structure for one result
        web_results = brave_client.extract_web_results(search_response)
        if web_results:
            print("\n" + "="*80)
            print("📋 SAMPLE STRUCTURED DATA (First Result)")
            print("="*80)
            first_result = web_results[0]
            for key, value in first_result.items():
                if value:  # Only show non-empty fields
                    if isinstance(value, (dict, list)):
                        print(f"{key}: {type(value).__name__} with {len(value) if hasattr(value, '__len__') else 'data'}")
                    else:
                        display_value = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                        print(f"{key}: {display_value}")

        print("\n✅ Brave Search test completed successfully!")
        return 0
        
    except Exception as e:
        print(f"❌ Search test failed: {str(e)}")
        print("\nMake sure your BRAVE_API_KEY is correct and you have API credits.")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 