#!/usr/bin/env python3
"""
Extract key points from PDF and save to JSON file.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Redirect stderr to suppress PyMuPDF warnings
stderr_fd = sys.stderr.fileno()
with open(os.devnull, 'w') as devnull:
    os.dup2(devnull.fileno(), stderr_fd)

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from pitchbot.pdf_ingest import PDFIngest


def extract_pdf_to_json(pdf_path: str, output_path: str = None, extract_images: bool = True):
    """
    Extract key points from PDF and save to JSON file, including image analysis.
    
    Args:
        pdf_path: Path to the PDF file
        output_path: Path for the JSON output file (optional)
        extract_images: Whether to extract and analyze images from PDF
    """
    # Initialize the ingestion system
    try:
        ingest = PDFIngest()
        print(f"Processing PDF: {pdf_path}")
        if extract_images:
            print("🔍 Including image analysis...")
    except Exception as e:
        print(f"❌ Failed to initialize PDFIngest: {e}")
        return
    
    # Process the PDF
    try:
        result = ingest.process_pdf(pdf_path, process_with_llama=True, extract_images=extract_images)
        
        if not result["success"]:
            print(f"❌ PDF processing failed: {result['errors']}")
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
            "pdf_info": {
                "filename": result["pdf_path"],
                "pages": result["metadata"]["pages"],
                "extraction_method": result["extraction_method"],
                "processing_time": result["processing_time"],
                "llama_processing_time": result.get("llama_processing_time", 0),
                "extraction_date": datetime.now().isoformat()
            },
            "text_stats": result.get("text_stats", {}),
            "images": {
                "extracted_count": result.get("images_extracted", 0),
                "image_paths": result.get("image_paths", [])
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
            pdf_name = Path(pdf_path).stem
            output_path = f"{pdf_name}_key_points.json"
        
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
        print(f"❌ Error processing PDF: {e}")


def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python extract_to_json.py <pdf_path> [output_json_path] [--no-images]")
        print("Example: python extract_to_json.py public/example_document.pdf")
        print("Example: python extract_to_json.py public/example_document.pdf output.json")
        print("Example: python extract_to_json.py public/example_document.pdf output.json --no-images")
        return
    
    pdf_path = sys.argv[1]
    output_path = None
    extract_images = True
    
    # Parse arguments
    for arg in sys.argv[2:]:
        if arg == "--no-images":
            extract_images = False
        elif not arg.startswith("--"):
            output_path = arg
    
    if not Path(pdf_path).exists():
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    extract_pdf_to_json(pdf_path, output_path, extract_images)


if __name__ == "__main__":
    main() 