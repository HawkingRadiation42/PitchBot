#!/usr/bin/env python3
"""
Extract key points from HTML files/URLs and save to JSON file.
"""

import json
import sys
import os
import logging
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from pitchbot.pdf_ingest import DocumentIngest


def extract_html_to_json(input_path: str, output_path: str = None, extract_images: bool = True):
    """
    Extract key points from HTML file or URL and save to JSON file, including image analysis.
    
    Args:
        input_path: Path to the HTML file or URL
        output_path: Path for the JSON output file (optional)
        extract_images: Whether to extract and analyze images from HTML
    """
    # Initialize the ingestion system
    try:
        ingest = DocumentIngest()
        print(f"Processing: {input_path}")
        if extract_images:
            print("🔍 Including image analysis...")
    except Exception as e:
        print(f"❌ Failed to initialize DocumentIngest: {e}")
        return
    
    # Determine if input is a URL or file path
    parsed_url = urlparse(input_path)
    is_url = bool(parsed_url.scheme and parsed_url.netloc)
    
    # Process the HTML
    try:
        if is_url:
            result = ingest.process_url(input_path, process_with_llama=True, extract_images=extract_images)
        else:
            result = ingest.process_html(input_path, process_with_llama=True, extract_images=extract_images)
        
        if not result["success"]:
            print(f"❌ HTML processing failed: {result['errors']}")
            return
        
        if not result.get("llama_processing", False):
            print("❌ Llama processing was not successful")
            return
        
        # Extract key points
        key_points = result.get("key_points", [])
        
        if not key_points:
            print("⚠️  No key points extracted")
            return
        
        # Organize key points by category
        organized_points = {}
        general_points = []
        
        for point in key_points:
            if point.startswith('[') and ']' in point:
                category = point[1:point.find(']')]
                content = point[point.find(']')+2:]
                if category not in organized_points:
                    organized_points[category] = []
                organized_points[category].append(content)
            else:
                general_points.append(point)
        
        if general_points:
            organized_points["General"] = general_points
        
        # Create JSON structure
        json_data = {
            "source_info": {
                "input": input_path,
                "type": "url" if is_url else "file",
                "title": result["metadata"].get("title", ""),
                "description": result["metadata"].get("description", ""),
                "extraction_method": result["extraction_method"],
                "processing_time": result["processing_time"],
                "llama_processing_time": result.get("llama_processing_time", 0),
                "extraction_date": datetime.now().isoformat()
            },
            "text_stats": result.get("text_stats", {}),
            "images": {
                "extracted_count": result.get("images_extracted", 0),
                "image_paths": result.get("image_paths", []),
                "image_info": result.get("image_info", [])
            },
            "key_points": {
                "total_count": len(key_points),
                "by_category": result.get("key_points_json", organized_points),
                "flat_list": key_points
            },
            "metadata": result["metadata"]
        }
        
        # Determine output path
        if output_path is None:
            if is_url:
                # Create filename from URL
                domain = parsed_url.netloc.replace('.', '_')
                path = parsed_url.path.replace('/', '_').replace('.', '_')
                if not path or path == '_':
                    path = 'home'
                output_path = f"{domain}{path}_key_points.json"
            else:
                # Create filename from HTML file
                html_name = Path(input_path).stem
                output_path = f"{html_name}_key_points.json"
        
        # Save to JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Successfully extracted {len(key_points)} key points")
        if result.get("images_extracted", 0) > 0:
            print(f"🖼️  Analyzed {result['images_extracted']} images")
        print(f"📁 Saved to: {output_path}")
        
        # Print summary
        print(f"\n📊 Summary:")
        print(f"  - Total key points: {len(key_points)}")
        print(f"  - Images analyzed: {result.get('images_extracted', 0)}")
        print(f"  - Categories: {list(organized_points.keys())}")
        for category, points in organized_points.items():
            print(f"    - {category}: {len(points)} points")
        
    except Exception as e:
        print(f"❌ Error processing HTML: {e}")


def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python extract_html_to_json.py <html_file_or_url> [output_json_path] [--no-images]")
        print("Examples:")
        print("  python extract_html_to_json.py example.html")
        print("  python extract_html_to_json.py https://example.com")
        print("  python extract_html_to_json.py example.html output.json")
        print("  python extract_html_to_json.py https://example.com output.json --no-images")
        return
    
    input_path = sys.argv[1]
    output_path = None
    extract_images = True
    
    # Parse arguments
    for arg in sys.argv[2:]:
        if arg == "--no-images":
            extract_images = False
        elif not arg.startswith("--"):
            output_path = arg
    
    # Check if input is a URL or file
    parsed_url = urlparse(input_path)
    is_url = bool(parsed_url.scheme and parsed_url.netloc)
    
    if not is_url and not Path(input_path).exists():
        print(f"❌ HTML file not found: {input_path}")
        return
    
    extract_html_to_json(input_path, output_path, extract_images)


if __name__ == "__main__":
    main() 