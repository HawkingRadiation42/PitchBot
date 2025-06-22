"""
PDF Processor for PitchBot

Handles processing of PDF documents using the PDFIngest system for key point extraction.
"""

import tempfile
import os
import json
from typing import Optional
from fastapi import UploadFile
from pathlib import Path
from datetime import datetime

from .pdf_ingest import PDFIngest


async def process_pdf(pdf_document: Optional[UploadFile]) -> str:
    """
    Process a PDF document by extracting key points using the PDFIngest system.
    
    Args:
        pdf_document: The uploaded PDF file
        
    Returns:
        Formatted analysis report as a string
    """
    if not pdf_document or not pdf_document.filename:
        return "No PDF document provided."

    print(f"📄 PDF processing started for: {pdf_document.filename}")

    # Use a temporary file to handle PDF processing
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        try:
            # Write PDF content to temp file
            content = await pdf_document.read()
            temp_pdf.write(content)
            temp_pdf.flush()
            pdf_path = temp_pdf.name

            print(f"🔍 Extracting key points from PDF (including image analysis)...")
            
            # Initialize the PDFIngest system
            try:
                ingest = PDFIngest()
            except Exception as e:
                return f"❌ Failed to initialize PDFIngest: {e}"

            # Process the PDF with Llama and image extraction
            try:
                result = ingest.process_pdf(pdf_path, process_with_llama=True, extract_images=True)
                
                if not result["success"]:
                    return f"❌ PDF processing failed: {result['errors']}"
                
                if not result.get("llama_processing", False):
                    return "❌ Llama processing was not successful"
                
                # Extract key points
                key_points = result.get("key_points", [])
                
                if not key_points:
                    return "⚠️ No key points extracted from PDF"
                
                # Format the results into a comprehensive report
                formatted_result = format_pdf_analysis(result, pdf_document.filename)
                
                print(f"✅ PDF processing complete - extracted {len(key_points)} key points")
                if result.get("images_extracted", 0) > 0:
                    print(f"🖼️ Analyzed {result['images_extracted']} images")
                
                return formatted_result
                
            except Exception as e:
                error_msg = f"❌ Error processing PDF: {e}"
                print(error_msg)
                return error_msg
                
        finally:
            # Clean up temporary file
            try:
                os.unlink(pdf_path)
            except:
                pass


def format_pdf_analysis(result: dict, filename: str) -> str:
    """
    Format the PDF analysis results into a readable report.
    
    Args:
        result: Analysis results from PDFIngest
        filename: Original filename
        
    Returns:
        Formatted analysis report
    """
    report_lines = []
    
    # Header
    report_lines.append("=" * 80)
    report_lines.append("📄 PDF DOCUMENT ANALYSIS REPORT")
    report_lines.append("=" * 80)
    
    # Document Info
    report_lines.append(f"\n📋 DOCUMENT INFORMATION:")
    report_lines.append("-" * 40)
    report_lines.append(f"Filename: {filename}")
    report_lines.append(f"Pages: {result['metadata']['pages']}")
    report_lines.append(f"Extraction Method: {result['extraction_method']}")
    report_lines.append(f"Processing Time: {result['processing_time']:.2f} seconds")
    if result.get("llama_processing_time"):
        report_lines.append(f"AI Analysis Time: {result['llama_processing_time']:.2f} seconds")
    
    # Text Statistics
    if result.get("text_stats"):
        stats = result["text_stats"]
        report_lines.append(f"\n📊 DOCUMENT STATISTICS:")
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
        report_lines.append(f"\n🎯 KEY POINTS BY CATEGORY:")
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
        report_lines.append(f"\n📝 ALL KEY POINTS:")
        report_lines.append("-" * 40)
        for i, point in enumerate(key_points, 1):
            report_lines.append(f"  {i}. {point}")
    
    # Summary
    report_lines.append(f"\n📈 ANALYSIS SUMMARY:")
    report_lines.append("-" * 40)
    report_lines.append(f"Total Key Points Extracted: {len(key_points)}")
    report_lines.append(f"Categories Identified: {len(key_points_json)}")
    if result.get("images_extracted", 0) > 0:
        report_lines.append(f"Images Analyzed: {result['images_extracted']}")
    report_lines.append(f"Processing Status: ✅ Success")
    
    report_lines.append("\n" + "=" * 80)
    
    return "\n".join(report_lines) 