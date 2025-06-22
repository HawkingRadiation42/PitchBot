#!/usr/bin/env python3
"""
Command-line interface for the AI Website Scraper.

Usage:
    python scrape_website.py <url> [options]
    
Examples:
    python scrape_website.py https://example.com
    python scrape_website.py https://example.com --max-pages 50 --output results.json
    python scrape_website.py https://example.com --delay 2.0 --concurrent 3
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from urllib.parse import urlparse

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from pitchbot.website_scraper import RobustWebsiteScraper, scrape_website


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def validate_url(url: str) -> str:
    """Validate and normalize URL."""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            raise ValueError("Invalid URL: no domain found")
        return url
    except Exception as e:
        raise ValueError(f"Invalid URL: {e}")


async def main():
    """Main function to handle command line scraping."""
    parser = argparse.ArgumentParser(
        description="AI Website Scraper - Comprehensive web scraping with intelligent content analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scrape_website.py https://example.com
  python scrape_website.py https://example.com --max-pages 50 --output results.json
  python scrape_website.py https://example.com --delay 2.0 --concurrent 3 --verbose
  python scrape_website.py https://example.com --content-threshold 0.6 --max-depth 3
        """
    )
    
    # Required arguments
    parser.add_argument(
        'url',
        help='URL to scrape (e.g., https://example.com)'
    )
    
    # Optional arguments
    parser.add_argument(
        '--output', '-o',
        help='Output file path for results (default: auto-generated)'
    )
    
    parser.add_argument(
        '--max-pages', '-m',
        type=int,
        default=100,
        help='Maximum number of pages to scrape (default: 100)'
    )
    
    parser.add_argument(
        '--max-depth', '-d',
        type=int,
        default=5,
        help='Maximum crawl depth (default: 5)'
    )
    
    parser.add_argument(
        '--delay', '-w',
        type=float,
        default=1.0,
        help='Delay between requests in seconds (default: 1.0)'
    )
    
    parser.add_argument(
        '--concurrent', '-c',
        type=int,
        default=5,
        help='Maximum concurrent requests (default: 5)'
    )
    
    parser.add_argument(
        '--content-threshold', '-t',
        type=float,
        default=0.4,
        help='Minimum content score to process (0.0-1.0, default: 0.4)'
    )
    
    parser.add_argument(
        '--cache-duration',
        type=int,
        default=3600,
        help='Cache duration in seconds (default: 3600)'
    )
    
    parser.add_argument(
        '--llama-model',
        default="Llama-4-Maverick-17B-128E-Instruct-FP8",
        help='Llama model to use for content analysis'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be scraped without actually doing it'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Validate URL
        url = validate_url(args.url)
        logger.info(f"Starting scrape of: {url}")
        
        if args.dry_run:
            logger.info("DRY RUN MODE - No actual scraping will be performed")
            logger.info(f"Configuration:")
            logger.info(f"  Max pages: {args.max_pages}")
            logger.info(f"  Max depth: {args.max_depth}")
            logger.info(f"  Delay: {args.delay}s")
            logger.info(f"  Concurrent requests: {args.concurrent}")
            logger.info(f"  Content threshold: {args.content_threshold}")
            logger.info(f"  Llama model: {args.llama_model}")
            return
        
        # Determine output path
        if args.output:
            output_path = args.output
        else:
            # Auto-generate output path
            domain = urlparse(url).netloc.replace('.', '_')
            output_path = f"{domain}_scraping_results.json"
        
        # Create scraper
        scraper = RobustWebsiteScraper(
            base_url=url,
            max_depth=args.max_depth,
            max_pages=args.max_pages,
            delay=args.delay,
            concurrent_requests=args.concurrent,
            content_threshold=args.content_threshold,
            cache_duration=args.cache_duration,
            llama_model=args.llama_model
        )
        
        # Start scraping
        logger.info("Starting comprehensive website scraping...")
        results = await scraper.scrape_comprehensive()
        
        # Save results
        scraper.save_results(output_path)
        
        # Print summary
        summary = scraper.get_results_summary()
        session_info = summary["scraping_session"]
        
        print("\n" + "="*60)
        print("SCRAPING COMPLETED")
        print("="*60)
        print(f"Base URL: {session_info['base_url']}")
        print(f"Total pages processed: {session_info['total_pages']}")
        print(f"Successful pages: {session_info['successful_pages']}")
        print(f"Failed pages: {session_info['failed_pages']}")
        print(f"Total time: {session_info['total_time']:.2f} seconds")
        print(f"Results saved to: {output_path}")
        
        if results:
            print(f"\nTop pages by content score:")
            sorted_results = sorted(results, key=lambda r: r.page_info.content_score, reverse=True)
            for i, result in enumerate(sorted_results[:5]):
                if not result.error:
                    print(f"  {i+1}. {result.page_info.title or result.page_info.url}")
                    print(f"     Score: {result.page_info.content_score:.2f}, Words: {result.page_info.word_count}")
        
        print("="*60)
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 