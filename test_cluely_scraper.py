#!/usr/bin/env python3
"""
Test script to demonstrate the improved scraper on Cluely.
"""

import asyncio
import json
from pathlib import Path

from pitchbot.website_scraper import scrape_website


async def test_cluely_scraping():
    """Test the scraper on Cluely website."""
    print("🤖 Testing Improved Website Scraper on Cluely")
    print("=" * 60)
    
    # Scrape Cluely with improved settings
    results = await scrape_website(
        base_url="https://cluely.com/",
        max_pages=10,
        delay=1.0,
        output_path="cluely_demo_results.json"
    )
    
    print(f"\n✅ Scraping completed successfully!")
    print(f"📊 Results Summary:")
    print(f"   - Total pages found: {len(results)}")
    print(f"   - Successful pages: {len([r for r in results if not r.error])}")
    print(f"   - Failed pages: {len([r for r in results if r.error])}")
    
    print(f"\n📄 Pages Discovered:")
    for i, result in enumerate(results, 1):
        print(f"   {i}. {result.page_info.url}")
        print(f"      Title: {result.page_info.title}")
        print(f"      Content Score: {result.page_info.content_score:.2f}")
        print(f"      Word Count: {result.page_info.word_count}")
        if result.summary:
            print(f"      Summary: {result.summary[:100]}...")
        print()
    
    # Show some key insights
    if results:
        print(f"🔍 Key Insights:")
        best_page = max(results, key=lambda r: r.page_info.content_score)
        print(f"   - Highest scoring page: {best_page.page_info.url} (Score: {best_page.content_score:.2f})")
        
        total_words = sum(r.page_info.word_count for r in results)
        print(f"   - Total content analyzed: {total_words} words")
        
        if best_page.key_points:
            print(f"   - Key business insights found: {len(best_page.key_points)} points")
    
    print(f"\n💾 Results saved to: cluely_demo_results.json")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_cluely_scraping()) 