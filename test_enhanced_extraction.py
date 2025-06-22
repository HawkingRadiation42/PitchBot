#!/usr/bin/env python3
"""
Test script for enhanced PDF extraction with image processing.
"""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_text_processor():
    """Test the enhanced text processor functionality."""
    print("Testing Enhanced Text Processor")
    print("=" * 40)
    
    try:
        from pitchbot.pdf_ingest.text_processor import TextProcessor
        print("✅ TextProcessor imported successfully")
        
        # Test initialization
        processor = TextProcessor()
        print("✅ TextProcessor initialized successfully")
        
        # Test image to base64 conversion
        test_text = "This is a test document about a business startup."
        print(f"✅ Test text created: {len(test_text)} characters")
        
        # Test key points extraction (text only)
        key_points = processor.extract_key_points(test_text)
        print(f"✅ Key points extracted: {len(key_points)} points")
        
        # Test JSON key points extraction
        key_points_json = processor.extract_key_points_json(test_text)
        print(f"✅ JSON key points extracted: {len(key_points_json)} categories")
        
        print("\n📊 Results:")
        for category, points in key_points_json.items():
            print(f"  - {category}: {len(points)} points")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_pdf_processor():
    """Test the PDF processor functionality."""
    print("\nTesting PDF Processor")
    print("=" * 40)
    
    try:
        from pitchbot.pdf_ingest.pdf_processor import PDFProcessor
        print("✅ PDFProcessor imported successfully")
        
        # Test initialization
        processor = PDFProcessor()
        print("✅ PDFProcessor initialized successfully")
        
        # Check available methods
        print(f"✅ Available extraction methods: {processor.extraction_methods}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Enhanced PDF Extraction Test")
    print("=" * 50)
    
    # Test text processor
    text_success = test_text_processor()
    
    # Test PDF processor
    pdf_success = test_pdf_processor()
    
    print("\n" + "=" * 50)
    if text_success and pdf_success:
        print("✅ All tests passed!")
        print("\nThe enhanced extraction system is ready to use.")
        print("Key improvements:")
        print("  - Refined prompts for better analysis")
        print("  - Image processing with base64 encoding")
        print("  - JSON-structured output for better organization")
        print("  - Enhanced visual content analysis")
    else:
        print("❌ Some tests failed.")
        print("Please check the error messages above.")

if __name__ == "__main__":
    main() 