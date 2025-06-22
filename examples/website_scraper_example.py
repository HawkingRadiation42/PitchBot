#!/usr/bin/env python3
"""
Example usage of the AI Website Scraper.

This script demonstrates various ways to use the website scraper:
1. Basic scraping with default settings
2. Custom configuration
3. Batch processing
4. Results analysis
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pitchbot.website_scraper import RobustWebsiteScraper, scrape_website


def setup_logging():
    """Setup logging for the example."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


async def basic_scraping_example():
    """Example 1: Basic scraping with default settings."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Scraping")
    print("="*60)
    
    url = "https://example.com"  # Replace with actual URL
    
    print(f"Scraping {url} with default settings...")
    
    try:
        results = await scrape_website(
            base_url=url,
            max_pages=10,
            output_path="basic_scraping_results.json"
        )
        
        print(f"✅ Scraped {len(results)} pages")
        
        # Show top results
        if results:
            print("\nTop 3 pages by content score:")
            sorted_results = sorted(results, key=lambda r: r.page_info.content_score, reverse=True)
            for i, result in enumerate(sorted_results[:3]):
                if not result.error:
                    print(f"  {i+1}. {result.page_info.title or result.page_info.url}")
                    print(f"     Score: {result.page_info.content_score:.2f}")
                    print(f"     Words: {result.page_info.word_count}")
                    print(f"     Summary: {result.summary[:100]}...")
        
    except Exception as e:
        print(f"❌ Basic scraping failed: {e}")


async def custom_configuration_example():
    """Example 2: Custom configuration for specific needs."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Custom Configuration")
    print("="*60)
    
    url = "https://example.com"  # Replace with actual URL
    
    print(f"Scraping {url} with custom settings...")
    
    try:
        # Create scraper with custom configuration
        scraper = RobustWebsiteScraper(
            base_url=url,
            max_pages=20,
            max_depth=3,
            delay=2.0,  # More polite crawling
            concurrent_requests=3,  # Fewer concurrent requests
            content_threshold=0.6,  # Higher quality threshold
            cache_duration=7200  # 2 hours cache
        )
        
        print("Configuration:")
        print(f"  Max pages: {scraper.max_pages}")
        print(f"  Max depth: {scraper.max_depth}")
        print(f"  Delay: {scraper.delay}s")
        print(f"  Concurrent requests: {scraper.concurrent_requests}")
        print(f"  Content threshold: {scraper.content_threshold}")
        
        # Start scraping
        results = await scraper.scrape_comprehensive()
        
        # Save results
        scraper.save_results("custom_scraping_results.json")
        
        print(f"✅ Scraped {len(results)} pages with custom settings")
        
        # Show summary
        summary = scraper.get_results_summary()
        session_info = summary["scraping_session"]
        print(f"Total time: {session_info['total_time']:.2f} seconds")
        print(f"Successful pages: {session_info['successful_pages']}")
        print(f"Failed pages: {session_info['failed_pages']}")
        
    except Exception as e:
        print(f"❌ Custom scraping failed: {e}")


async def batch_processing_example():
    """Example 3: Batch processing multiple websites."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Batch Processing")
    print("="*60)
    
    urls = [
        "https://cluely.com/",  # Replace with actual URLs
        "https://www.boundaryml.com/",
        "https://www.spurtest.com/"
    ]
    
    print(f"Batch processing {len(urls)} websites...")
    
    all_results = {}
    
    for i, url in enumerate(urls, 1):
        print(f"\nProcessing website {i}/{len(urls)}: {url}")
        
        try:
            results = await scrape_website(
                base_url=url,
                max_pages=5,  # Small sample for batch processing
                delay=1.0
            )
            
            all_results[url] = {
                "total_pages": len(results),
                "successful_pages": len([r for r in results if not r.error]),
                "failed_pages": len([r for r in results if r.error]),
                "avg_content_score": sum(r.page_info.content_score for r in results if not r.error) / max(len([r for r in results if not r.error]), 1),
                "top_pages": [
                    {
                        "url": r.page_info.url,
                        "title": r.page_info.title,
                        "score": r.page_info.content_score,
                        "summary": r.summary[:100] + "..." if r.summary else ""
                    }
                    for r in sorted(results, key=lambda x: x.page_info.content_score, reverse=True)[:3]
                    if not r.error
                ]
            }
            
            print(f"  ✅ {all_results[url]['successful_pages']} pages processed")
            
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            all_results[url] = {"error": str(e)}
    
    # Save batch results
    with open("batch_scraping_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n✅ Batch processing completed. Results saved to batch_scraping_results.json")


async def content_analysis_example():
    """Example 4: Deep content analysis of scraped results."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Content Analysis")
    print("="*60)
    
    # Load results from previous scraping
    try:
        with open("basic_scraping_results.json", "r") as f:
            data = json.load(f)
        
        results = data.get("results", [])
        
        if not results:
            print("No results found. Run basic scraping example first.")
            return
        
        print(f"Analyzing {len(results)} scraped pages...")
        
        # Content analysis
        successful_results = [r for r in results if not r.get("error")]
        failed_results = [r for r in results if r.get("error")]
        
        print(f"\nSuccess Rate: {len(successful_results)}/{len(results)} ({len(successful_results)/len(results)*100:.1f}%)")
        
        if successful_results:
            # Score distribution
            scores = [r["content_score"] for r in successful_results]
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            min_score = min(scores)
            
            print(f"\nContent Score Analysis:")
            print(f"  Average: {avg_score:.2f}")
            print(f"  Maximum: {max_score:.2f}")
            print(f"  Minimum: {min_score:.2f}")
            
            # Word count analysis
            word_counts = [r["word_count"] for r in successful_results]
            avg_words = sum(word_counts) / len(word_counts)
            total_words = sum(word_counts)
            
            print(f"\nWord Count Analysis:")
            print(f"  Average words per page: {avg_words:.0f}")
            print(f"  Total words scraped: {total_words:,}")
            
            # Top content by score
            print(f"\nTop 5 Pages by Content Score:")
            sorted_results = sorted(successful_results, key=lambda x: x["content_score"], reverse=True)
            for i, result in enumerate(sorted_results[:5]):
                print(f"  {i+1}. {result['title'] or result['url']}")
                print(f"     Score: {result['content_score']:.2f}, Words: {result['word_count']}")
                print(f"     Summary: {result['summary'][:80]}...")
            
            # Key points analysis
            all_key_points = []
            for result in successful_results:
                all_key_points.extend(result.get("key_points", []))
            
            print(f"\nKey Points Analysis:")
            print(f"  Total key points extracted: {len(all_key_points)}")
            print(f"  Average key points per page: {len(all_key_points)/len(successful_results):.1f}")
            
            # Show some key points
            if all_key_points:
                print(f"\nSample Key Points:")
                for i, point in enumerate(all_key_points[:10]):
                    print(f"  {i+1}. {point}")
        
        if failed_results:
            print(f"\nFailed Pages Analysis:")
            print(f"  Failed pages: {len(failed_results)}")
            for result in failed_results[:3]:
                print(f"  - {result['url']}: {result['error']}")
        
    except FileNotFoundError:
        print("No results file found. Run basic scraping example first.")
    except Exception as e:
        print(f"❌ Content analysis failed: {e}")


async def main():
    """Main function to run all examples."""
    setup_logging()
    
    print("🤖 AI Website Scraper Examples")
    print("="*60)
    print("This script demonstrates various ways to use the website scraper.")
    print("Note: Replace example URLs with actual websites you want to scrape.")
    print("="*60)
    
    # Run examples
    await basic_scraping_example()
    await custom_configuration_example()
    await batch_processing_example()
    await content_analysis_example()
    
    print("\n" + "="*60)
    print("✅ All examples completed!")
    print("Check the generated JSON files for detailed results.")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main()) 