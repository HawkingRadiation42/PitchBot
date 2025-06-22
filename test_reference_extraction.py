"""
Test script for multi-level reference extraction functionality.
"""

import asyncio
import sys
import os

# Add the agentic_search module to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'agentic_search'))

from agentic_search.enhanced_research_pipeline import research_startup_idea_comprehensive


async def test_reference_extraction():
    """Test the enhanced research pipeline with reference extraction."""
    
    # Example startup idea
    idea_summary = """
    A SaaS platform that uses AI to automatically generate and optimize 
    social media content for small businesses. The platform analyzes 
    competitor content, trending topics, and brand voice to create 
    personalized posts across multiple social media channels.
    """
    
    print("🚀 Testing Multi-Level Reference Extraction")
    print("=" * 60)
    print(f"Startup Idea: {idea_summary.strip()}")
    print("=" * 60)
    
    try:
        # Run comprehensive research with reference extraction enabled
        results = await research_startup_idea_comprehensive(
            idea_summary=idea_summary,
            max_depth=2,  # Go 2 levels deep
            max_pages_per_level=3,  # Process 3 pages per level
            max_search_results=5,  # 5 search results per query
            enable_reference_extraction=True
        )
        
        print("\n✅ Test completed successfully!")
        
        # Print some key statistics
        summary = results['pipeline_summary']
        print(f"\n📊 FINAL STATISTICS:")
        print(f"   • Search Queries: {summary['queries_executed']}")
        print(f"   • Initial Results: {summary['initial_search_results']}")
        print(f"   • Total Pages Analyzed: {summary['total_pages_analyzed']}")
        print(f"   • Reference Levels: {summary['reference_levels_processed']}")
        
        return results
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_basic_reference_extraction():
    """Test basic reference extraction on a few URLs."""
    
    # Import the reference extractor
    from agentic_search.reference_extractor import ReferenceExtractor
    
    print("\n🔗 Testing Basic Reference Extraction")
    print("=" * 50)
    
    # Create extractor
    extractor = ReferenceExtractor(max_depth=2, max_pages_per_level=10)
    
    # Test URLs (using reliable news/tech sites)
    test_urls = [
        "https://techcrunch.com/2024/01/01/ai-startups-2024/",
        "https://www.forbes.com/sites/forbestechcouncil/",
        "https://venturebeat.com/ai/"
    ]
    
    try:
        print(f"Testing with {len(test_urls)} URLs...")
        
        # Extract multi-level references
        result = await extractor.extract_multi_level_references(test_urls)
        
        print(f"\n✅ Reference extraction completed!")
        print(f"   • Total pages scraped: {result['summary']['total_pages_scraped']}")
        print(f"   • Total references found: {result['summary']['total_references_found']}")
        print(f"   • Levels processed: {result['summary']['levels_processed']}")
        
        # Show some example references
        if result['all_pages']:
            print(f"\n📄 Example page content:")
            for i, page in enumerate(result['all_pages'][:2]):
                print(f"   {i+1}. {page['title']}")
                print(f"      URL: {page['url']}")
                print(f"      Content length: {page['content_length']} chars")
                print(f"      References found: {page['reference_count']}")
                
                if page['references']:
                    print(f"      Top references:")
                    for ref in page['references'][:3]:
                        print(f"        • {ref['anchor_text'][:50]}{'...' if len(ref['anchor_text']) > 50 else ''}")
                        print(f"          {ref['url']}")
        
        return result
        
    except Exception as e:
        print(f"❌ Basic test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def show_usage_examples():
    """Show how to use the multi-level reference extraction."""
    
    print("\n" + "="*80)
    print("📖 USAGE EXAMPLES FOR MULTI-LEVEL REFERENCE EXTRACTION")
    print("="*80)
    
    print("""
🔍 Example 1: Basic Reference Extraction
```python
from agentic_search.reference_extractor import ReferenceExtractor

# Create extractor
extractor = ReferenceExtractor(max_depth=2, max_pages_per_level=5)

# Extract from URLs
urls = ["https://example.com/page1", "https://example.com/page2"]
result = await extractor.extract_multi_level_references(urls)

print(f"Scraped {result['summary']['total_pages_scraped']} pages")
print(f"Found {result['summary']['total_references_found']} references")
```

🚀 Example 2: Enhanced Research Pipeline
```python
from agentic_search.enhanced_research_pipeline import research_startup_idea_comprehensive

# Run comprehensive research
results = await research_startup_idea_comprehensive(
    idea_summary="Your startup idea here...",
    max_depth=2,              # Go 2 levels deep
    max_pages_per_level=5,    # 5 pages per level
    max_search_results=10,    # 10 search results per query
    enable_reference_extraction=True
)
```

🔗 Example 3: Enhance Existing Brave Search Results
```python
from agentic_search.brave_search import BraveSearchClient
from agentic_search.reference_extractor import enhance_search_with_references

# Get initial search results
client = BraveSearchClient()
search_response = await client.search("AI startups 2024")
brave_results = client.extract_web_results(search_response)

# Enhance with reference extraction
enhanced = await enhance_search_with_references(
    brave_results,
    max_depth=2,
    max_pages_per_level=3
)
```

🎯 Key Benefits:
• Discovers content not found in initial search results
• Finds references, citations, and related studies
• Builds comprehensive knowledge graphs
• Identifies competitor mentions and market data
• Extracts deeper insights from industry reports
""")


if __name__ == "__main__":
    print("🧪 Multi-Level Reference Extraction Test Suite")
    print("=" * 60)
    
    # Show usage examples first
    show_usage_examples()
    
    print("\n⚠️  Note: Some dependencies might be missing (beautifulsoup4, httpx)")
    print("Install them with: pip install beautifulsoup4 httpx")
    
    # Uncomment to run actual tests
    # print("\n🚀 Running tests...")
    # asyncio.run(test_basic_reference_extraction())
    # asyncio.run(test_reference_extraction()) 