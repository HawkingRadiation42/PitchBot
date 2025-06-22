"""
Company URL Processor for PitchBot

Handles processing of company URLs using the DocumentIngest system for key point extraction.
"""

from typing import Optional
from urllib.parse import urlparse
from datetime import datetime

from .pdf_ingest import DocumentIngest


async def process_company_url(company_url: str) -> str:
    """
    Process a company URL by extracting key points using the DocumentIngest system.
    
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

    print(f"🔍 Extracting key points from website (including image analysis)...")
    
    # Initialize the DocumentIngest system
    try:
        ingest = DocumentIngest()
    except Exception as e:
        return f"❌ Failed to initialize DocumentIngest: {e}"

    # Process the URL with Llama and image extraction
    try:
        result = ingest.process_url(company_url, process_with_llama=True, extract_images=True)
        
        if not result["success"]:
            return f"❌ Company URL processing failed: {result['errors']}"
        
        if not result.get("llama_processing", False):
            return "❌ Llama processing was not successful"
        
        # Extract key points
        key_points = result.get("key_points", [])
        
        if not key_points:
            return "⚠️ No key points extracted from company website"
        
        # Format the results into a comprehensive report
        formatted_result = format_company_url_analysis(result, company_url)
        
        print(f"✅ Company URL processing complete - extracted {len(key_points)} key points")
        if result.get("images_extracted", 0) > 0:
            print(f"🖼️ Analyzed {result['images_extracted']} images")
        
        return formatted_result
        
    except Exception as e:
        error_msg = f"❌ Error processing company URL: {e}"
        print(error_msg)
        return error_msg


def format_company_url_analysis(result: dict, company_url: str) -> str:
    """
    Format the company URL analysis results into a readable report.
    
    Args:
        result: Analysis results from DocumentIngest
        company_url: Original company URL
        
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
    
    metadata = result.get("metadata", {})
    if metadata.get("title"):
        report_lines.append(f"Title: {metadata['title']}")
    if metadata.get("description"):
        report_lines.append(f"Description: {metadata['description']}")
    
    report_lines.append(f"Extraction Method: {result['extraction_method']}")
    report_lines.append(f"Processing Time: {result['processing_time']:.2f} seconds")
    if result.get("llama_processing_time"):
        report_lines.append(f"AI Analysis Time: {result['llama_processing_time']:.2f} seconds")
    
    # Text Statistics
    if result.get("text_stats"):
        stats = result["text_stats"]
        report_lines.append(f"\n📊 CONTENT STATISTICS:")
        report_lines.append("-" * 40)
        report_lines.append(f"Word Count: {stats.get('word_count', 'N/A')}")
        report_lines.append(f"Sentence Count: {stats.get('sentence_count', 'N/A')}")
        report_lines.append(f"Paragraph Count: {stats.get('paragraph_count', 'N/A')}")
    
    # Image Analysis
    if result.get("images_extracted", 0) > 0:
        report_lines.append(f"\n🖼️ IMAGE ANALYSIS:")
        report_lines.append("-" * 40)
        report_lines.append(f"Images Analyzed: {result['images_extracted']}")
        if result.get("image_paths"):
            report_lines.append(f"Image Files: {len(result['image_paths'])} extracted")
    
    # Key Points by Category
    key_points_json = result.get("key_points_json", {})
    if key_points_json:
        report_lines.append(f"\n🎯 COMPANY INSIGHTS BY CATEGORY:")
        report_lines.append("-" * 40)
        
        for category, points in key_points_json.items():
            if points:  # Only show categories with points
                report_lines.append(f"\n📌 {category.upper()}:")
                for i, point in enumerate(points, 1):
                    if point.strip():  # Only show non-empty points
                        report_lines.append(f"  {i}. {point}")
    
    # All Key Points (Flat List)
    key_points = result.get("key_points", [])
    if key_points:
        report_lines.append(f"\n📝 ALL KEY INSIGHTS:")
        report_lines.append("-" * 40)
        for i, point in enumerate(key_points, 1):
            report_lines.append(f"  {i}. {point}")
    
    # Website Metadata
    if metadata:
        report_lines.append(f"\n📋 WEBSITE METADATA:")
        report_lines.append("-" * 40)
        for key, value in metadata.items():
            if key not in ['title', 'description'] and value:  # Skip already shown items
                report_lines.append(f"{key.title()}: {value}")
    
    # Summary
    report_lines.append(f"\n📈 ANALYSIS SUMMARY:")
    report_lines.append("-" * 40)
    report_lines.append(f"Total Key Insights Extracted: {len(key_points)}")
    report_lines.append(f"Categories Identified: {len(key_points_json)}")
    if result.get("images_extracted", 0) > 0:
        report_lines.append(f"Images Analyzed: {result['images_extracted']}")
    report_lines.append(f"Processing Status: ✅ Success")
    
    report_lines.append("\n" + "=" * 80)
    
    return "\n".join(report_lines) 