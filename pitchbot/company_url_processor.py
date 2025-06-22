"""
Company URL Processor for PitchBot

Handles processing of company URLs using the advanced RobustWebsiteScraper for comprehensive analysis.
"""

from typing import Optional
from urllib.parse import urlparse
from datetime import datetime
import time

from .website_scraper import RobustWebsiteScraper


async def process_company_url(company_url: str) -> str:
    """
    Process a company URL using the advanced RobustWebsiteScraper for comprehensive analysis.
    
    Args:
        company_url: The company URL to process
        
    Returns:
        Formatted analysis report as a string
    """
    if not company_url:
        return "No company URL provided."

    print(f"🌐 Company URL processing started for: {company_url}")

    # Validate URL format
    try:
        parsed_url = urlparse(company_url)
        if not (parsed_url.scheme and parsed_url.netloc):
            return f"❌ Invalid URL format: {company_url}"
    except Exception as e:
        return f"❌ URL parsing error: {e}"

    print(f"🔍 Starting comprehensive website analysis...")
    
    start_time = time.time()
    
    try:
        # Initialize the RobustWebsiteScraper with optimized settings for company analysis
        scraper = RobustWebsiteScraper(
            base_url=company_url,
            max_depth=3,  # Limited depth for company sites
            max_pages=25,  # Reasonable number for company analysis
            delay=1.0,  # Respectful crawling
            concurrent_requests=3,  # Conservative concurrency
            content_threshold=0.3,  # Lower threshold to capture more content
            cache_duration=3600
        )
        
        # Perform comprehensive scraping
        results = await scraper.scrape_comprehensive()
        
        if not results:
            return "⚠️ No content could be extracted from the company website"
        
        # Get processing summary
        summary = scraper.get_results_summary()
        processing_time = time.time() - start_time
        
        # Format the results into a comprehensive report
        formatted_result = format_company_url_analysis_v2(results, summary, company_url, processing_time)
        
        successful_pages = len([r for r in results if not r.error])
        total_key_points = sum(len(r.key_points) for r in results if not r.error)
        
        print(f"✅ Company URL processing complete")
        print(f"📊 Processed {successful_pages} pages, extracted {total_key_points} key insights")
        
        return formatted_result
        
    except Exception as e:
        error_msg = f"❌ Error processing company URL: {e}"
        print(error_msg)
        return error_msg


def format_company_url_analysis_v2(results: list, summary: dict, company_url: str, processing_time: float) -> str:
    """
    Format the company URL analysis results from RobustWebsiteScraper into a readable report.
    
    Args:
        results: List of ScrapingResult objects from RobustWebsiteScraper
        summary: Summary dict from scraper.get_results_summary()
        company_url: Original company URL
        processing_time: Total processing time
        
    Returns:
        Formatted analysis report
    """
    report_lines = []
    
    # Header
    report_lines.append("=" * 80)
    report_lines.append("🌐 COMPANY WEBSITE ANALYSIS REPORT")
    report_lines.append("=" * 80)
    
    # Website Info
    report_lines.append(f"\n🔗 WEBSITE INFORMATION:")
    report_lines.append("-" * 40)
    report_lines.append(f"URL: {company_url}")
    
    # Get homepage info for title/description
    homepage_result = next((r for r in results if r.page_info.url == company_url), None)
    if not homepage_result:
        homepage_result = next((r for r in results if not r.error), None)
    
    if homepage_result and homepage_result.page_info.title:
        report_lines.append(f"Title: {homepage_result.page_info.title}")
    
    session_info = summary.get("scraping_session", {})
    report_lines.append(f"Extraction Method: Advanced website scraping")
    report_lines.append(f"Processing Time: {processing_time:.2f} seconds")
    report_lines.append(f"Pages Analyzed: {session_info.get('successful_pages', 0)}")
    
    # Content Statistics (aggregate)
    successful_results = [r for r in results if not r.error]
    total_words = sum(r.page_info.word_count for r in successful_results)
    avg_content_score = sum(r.page_info.content_score for r in successful_results) / len(successful_results) if successful_results else 0
    
    report_lines.append(f"\n📊 CONTENT STATISTICS:")
    report_lines.append("-" * 40)
    report_lines.append(f"Total Word Count: {total_words:,}")
    report_lines.append(f"Average Content Score: {avg_content_score:.2f}")
    report_lines.append(f"Pages Successfully Processed: {len(successful_results)}")
    if session_info.get('failed_pages', 0) > 0:
        report_lines.append(f"Pages Failed: {session_info['failed_pages']}")
    
    # Categorize key insights by analyzing content
    all_key_points = []
    for result in successful_results:
        all_key_points.extend(result.key_points)
    
    # Simple categorization based on keywords
    categorized_insights = categorize_insights(all_key_points)
    
    if categorized_insights:
        report_lines.append(f"\n🎯 COMPANY INSIGHTS BY CATEGORY:")
        report_lines.append("-" * 40)
        
        for category, points in categorized_insights.items():
            if points:  # Only show categories with points
                report_lines.append(f"\n📌 {category.upper()}:")
                for i, point in enumerate(points, 1):
                    if point.strip():  # Only show non-empty points
                        report_lines.append(f"  {i}. {point}")
    
    # Top Pages by Content Quality
    if len(successful_results) > 1:
        report_lines.append(f"\n🏆 TOP CONTENT PAGES:")
        report_lines.append("-" * 40)
        top_pages = sorted(successful_results, key=lambda r: r.page_info.content_score, reverse=True)[:5]
        for i, result in enumerate(top_pages, 1):
            title = result.page_info.title or "Untitled"
            score = result.page_info.content_score
            words = result.page_info.word_count
            report_lines.append(f"  {i}. {title}")
            report_lines.append(f"     URL: {result.page_info.url}")
            report_lines.append(f"     Score: {score:.2f}, Words: {words:,}")
    
    # All Key Insights (Flat List)
    if all_key_points:
        report_lines.append(f"\n📝 ALL KEY INSIGHTS:")
        report_lines.append("-" * 40)
        for i, point in enumerate(all_key_points[:30], 1):  # Limit to top 30 for readability
            report_lines.append(f"  {i}. {point}")
        
        if len(all_key_points) > 30:
            report_lines.append(f"  ... and {len(all_key_points) - 30} more insights")
    
    # Processing Details
    config = session_info.get('configuration', {})
    report_lines.append(f"\n📋 PROCESSING CONFIGURATION:")
    report_lines.append("-" * 40)
    report_lines.append(f"Max Depth: {config.get('max_depth', 'N/A')}")
    report_lines.append(f"Max Pages: {config.get('max_pages', 'N/A')}")
    report_lines.append(f"Content Threshold: {config.get('content_threshold', 'N/A')}")
    report_lines.append(f"Concurrent Requests: {config.get('concurrent_requests', 'N/A')}")
    
    # Summary
    report_lines.append(f"\n📈 ANALYSIS SUMMARY:")
    report_lines.append("-" * 40)
    report_lines.append(f"Total Key Insights Extracted: {len(all_key_points)}")
    report_lines.append(f"Categories Identified: {len(categorized_insights)}")
    report_lines.append(f"Pages Analyzed: {len(successful_results)}")
    report_lines.append(f"Processing Status: ✅ Success")
    
    report_lines.append("\n" + "=" * 80)
    
    return "\n".join(report_lines)


def categorize_insights(key_points: list) -> dict:
    """
    Categorize key insights based on content keywords.
    
    Args:
        key_points: List of key insight strings
        
    Returns:
        Dictionary with categorized insights
    """
    categories = {
        "Product Market Fit": [],
        "Business Model": [],
        "Technology": [],
        "Competitive Landscape": [],
        "Company Culture": [],
        "Leadership": [],
        "Funding & Growth": [],
        "Partnerships": [],
        "General": []
    }
    
    # Keywords for each category
    category_keywords = {
        "Product Market Fit": ["product", "market", "customer", "user", "solution", "problem", "need", "demand", "target"],
        "Business Model": ["revenue", "monetization", "pricing", "subscription", "business model", "sales", "profit", "income"],
        "Technology": ["technology", "technical", "platform", "software", "API", "infrastructure", "development", "engineering"],
        "Competitive Landscape": ["competitor", "competition", "advantage", "differentiation", "market position", "unique"],
        "Company Culture": ["culture", "values", "mission", "vision", "team", "employee", "workplace", "diversity"],
        "Leadership": ["founder", "CEO", "executive", "leadership", "management", "board", "advisor"],
        "Funding & Growth": ["funding", "investment", "growth", "expansion", "scale", "series", "venture", "capital"],
        "Partnerships": ["partner", "partnership", "collaboration", "integration", "alliance", "relationship"]
    }
    
    for point in key_points:
        point_lower = point.lower()
        categorized = False
        
        # Check each category for keyword matches
        for category, keywords in category_keywords.items():
            if any(keyword in point_lower for keyword in keywords):
                categories[category].append(point)
                categorized = True
                break
        
        # If no category matched, put in General
        if not categorized:
            categories["General"].append(point)
    
    # Remove empty categories
    return {k: v for k, v in categories.items() if v} 