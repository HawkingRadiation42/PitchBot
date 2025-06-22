"""
Main Document Ingestion orchestrator combining local extraction and Llama processing.
Supports both PDF and HTML files.
"""

import logging
import os
import time
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Suppress PyMuPDF warnings
logging.getLogger('fitz').setLevel(logging.CRITICAL)
logging.getLogger('PyMuPDF').setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore", category=UserWarning, module="fitz")

# Load environment variables from .env file in project root
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env")
except ImportError:
    pass

from .pdf_processor import PDFProcessor
from .text_processor import TextProcessor
from .html_processor import HTMLProcessor

logger = logging.getLogger(__name__)


class DocumentIngest:
    """
    Main Document Ingestion orchestrator that combines local document extraction with Llama text processing.
    
    Supports both PDF and HTML files, providing a simple interface for end-to-end document processing
    with both raw extraction and AI-enhanced insights.
    """
    
    def __init__(self, llama_api_key: Optional[str] = None, llama_model: str = "Llama-4-Maverick-17B-128E-Instruct-FP8"):
        """
        Initialize the document ingestion system.
        
        Args:
            llama_api_key: Llama API key (defaults to LLAMA_API_KEY env var)
            llama_model: Llama model to use for text processing
        """
        self.pdf_processor = PDFProcessor()
        self.html_processor = HTMLProcessor()
        self.text_processor = TextProcessor(api_key=llama_api_key, model=llama_model)
        
        logger.info("Document Ingestion system initialized")
    
    def process_document(self, file_path: Union[str, Path], process_with_llama: bool = True, extract_images: bool = True) -> Dict[str, Any]:
        """
        Process a document (PDF or HTML) with focus on key point extraction using Llama.
        
        Args:
            file_path: Path to the document file (PDF or HTML)
            process_with_llama: Whether to process with Llama API
            extract_images: Whether to extract and analyze images from document
            
        Returns:
            Processing results focused on key points
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {
                "success": False,
                "errors": [f"File not found: {file_path}"],
                "processing_time": 0
            }
        
        # Determine file type and process accordingly
        file_extension = file_path.suffix.lower()
        
        if file_extension == '.pdf':
            return self.process_pdf(file_path, process_with_llama, extract_images)
        elif file_extension in ['.html', '.htm']:
            return self.process_html(file_path, process_with_llama, extract_images)
        else:
            return {
                "success": False,
                "errors": [f"Unsupported file type: {file_extension}. Supported: .pdf, .html, .htm"],
                "processing_time": 0
            }
    
    def process_html(self, html_path: Union[str, Path], process_with_llama: bool = True, extract_images: bool = True) -> Dict[str, Any]:
        """
        Process HTML file with focus on key point extraction using Llama, including image analysis.
        
        Args:
            html_path: Path to the HTML file
            process_with_llama: Whether to process with Llama API
            extract_images: Whether to extract and analyze images from HTML
            
        Returns:
            Processing results focused on key points
        """
        start_time = time.time()
        html_path = Path(html_path)
        
        if not html_path.exists():
            return {
                "success": False,
                "errors": [f"HTML file not found: {html_path}"],
                "processing_time": time.time() - start_time
            }
        
        try:
            # Extract text, metadata, and images
            extraction_result = self.html_processor.extract_from_file(html_path)
            
            if not extraction_result["success"]:
                return {
                    "success": False,
                    "errors": extraction_result["errors"],
                    "processing_time": time.time() - start_time
                }
            
            result = {
                "file_path": str(html_path),
                "file_type": "html",
                "metadata": extraction_result["metadata"],
                "extraction_method": extraction_result["extraction_method"],
                "extraction_time": extraction_result["processing_time"],
                "llama_processing": False,
                "success": True,
                "errors": []
            }
            
            # Extract and save images if requested
            extracted_images = []
            if extract_images and extraction_result["images"]:
                try:
                    extracted_images = self.html_processor.save_images(extraction_result["images"])
                    result["images_extracted"] = len(extracted_images)
                    result["image_paths"] = extracted_images
                    result["image_info"] = extraction_result["images"]
                except Exception as e:
                    logger.warning(f"Image extraction failed: {e}")
                    result["images_extracted"] = 0
                    result["image_paths"] = []
                    result["image_info"] = extraction_result["images"]
            
            # Process with Llama if requested and content is available
            if process_with_llama and (extraction_result["text"].strip() or extracted_images):
                try:
                    llama_start_time = time.time()
                    
                    # Clean and structure text
                    cleaned_data = self.text_processor.clean_and_structure(extraction_result["text"])
                    
                    # Extract key points with business focus, including images
                    logger.info(f"Starting key point extraction with {len(extracted_images)} images")
                    key_points_json = self.text_processor.extract_key_points_json(
                        cleaned_data["cleaned_text"], 
                        extracted_images if extracted_images else None
                    )
                    
                    # Check if we got meaningful results
                    total_points = sum(len(points) for points in key_points_json.values())
                    if total_points == 0 or (len(key_points_json) == 1 and "General" in key_points_json and len(key_points_json["General"]) == 1 and not key_points_json["General"][0].strip()):
                        logger.warning("Image processing may have failed, retrying with text-only analysis")
                        # Retry with text-only analysis
                        key_points_json = self.text_processor.extract_key_points_json(
                            cleaned_data["cleaned_text"], 
                            None  # No images
                        )
                    
                    # Convert JSON structure to flat list for backward compatibility
                    key_points = []
                    for category, points in key_points_json.items():
                        for point in points:
                            if point.strip():  # Only add non-empty points
                                key_points.append(f"[{category}] {point}")
                    
                    result["key_points"] = key_points
                    result["key_points_json"] = key_points_json  # Keep structured format too
                    
                    # Add text statistics for context
                    result["text_stats"] = {
                        "word_count": cleaned_data["word_count"],
                        "sentence_count": cleaned_data["sentence_count"],
                        "paragraph_count": cleaned_data["paragraph_count"]
                    }
                    
                    result["llama_processing"] = True
                    result["llama_processing_time"] = time.time() - llama_start_time
                    
                    logger.info(f"Successfully extracted {len(key_points)} key points")
                    
                except Exception as e:
                    logger.error(f"Llama processing failed: {e}")
                    result["errors"].append(f"Llama processing failed: {str(e)}")
                    result["llama_processing"] = False
            
            result["processing_time"] = time.time() - start_time
            return result
            
        except Exception as e:
            logger.error(f"HTML processing failed: {e}")
            return {
                "success": False,
                "errors": [str(e)],
                "processing_time": time.time() - start_time
            }
    
    def process_url(self, url: str, process_with_llama: bool = True, extract_images: bool = True) -> Dict[str, Any]:
        """
        Process content from a URL with focus on key point extraction using Llama.
        
        Args:
            url: URL to process
            process_with_llama: Whether to process with Llama API
            extract_images: Whether to extract and analyze images from the webpage
            
        Returns:
            Processing results focused on key points
        """
        start_time = time.time()
        
        try:
            # Extract text, metadata, and images from URL
            extraction_result = self.html_processor.extract_from_url(url)
            
            if not extraction_result["success"]:
                return {
                    "success": False,
                    "errors": extraction_result["errors"],
                    "processing_time": time.time() - start_time
                }
            
            result = {
                "url": url,
                "file_type": "html",
                "metadata": extraction_result["metadata"],
                "extraction_method": extraction_result["extraction_method"],
                "extraction_time": extraction_result["processing_time"],
                "llama_processing": False,
                "success": True,
                "errors": []
            }
            
            # Extract and save images if requested
            extracted_images = []
            if extract_images and extraction_result["images"]:
                try:
                    extracted_images = self.html_processor.save_images(extraction_result["images"])
                    result["images_extracted"] = len(extracted_images)
                    result["image_paths"] = extracted_images
                    result["image_info"] = extraction_result["images"]
                except Exception as e:
                    logger.warning(f"Image extraction failed: {e}")
                    result["images_extracted"] = 0
                    result["image_paths"] = []
                    result["image_info"] = extraction_result["images"]
            
            # Process with Llama if requested and content is available
            if process_with_llama and (extraction_result["text"].strip() or extracted_images):
                try:
                    llama_start_time = time.time()
                    
                    # Clean and structure text
                    cleaned_data = self.text_processor.clean_and_structure(extraction_result["text"])
                    
                    # Extract key points with business focus, including images
                    logger.info(f"Starting key point extraction with {len(extracted_images)} images")
                    key_points_json = self.text_processor.extract_key_points_json(
                        cleaned_data["cleaned_text"], 
                        extracted_images if extracted_images else None
                    )
                    
                    # Check if we got meaningful results
                    total_points = sum(len(points) for points in key_points_json.values())
                    if total_points == 0 or (len(key_points_json) == 1 and "General" in key_points_json and len(key_points_json["General"]) == 1 and not key_points_json["General"][0].strip()):
                        logger.warning("Image processing may have failed, retrying with text-only analysis")
                        # Retry with text-only analysis
                        key_points_json = self.text_processor.extract_key_points_json(
                            cleaned_data["cleaned_text"], 
                            None  # No images
                        )
                    
                    # Convert JSON structure to flat list for backward compatibility
                    key_points = []
                    for category, points in key_points_json.items():
                        for point in points:
                            if point.strip():  # Only add non-empty points
                                key_points.append(f"[{category}] {point}")
                    
                    result["key_points"] = key_points
                    result["key_points_json"] = key_points_json  # Keep structured format too
                    
                    # Add text statistics for context
                    result["text_stats"] = {
                        "word_count": cleaned_data["word_count"],
                        "sentence_count": cleaned_data["sentence_count"],
                        "paragraph_count": cleaned_data["paragraph_count"]
                    }
                    
                    result["llama_processing"] = True
                    result["llama_processing_time"] = time.time() - llama_start_time
                    
                    logger.info(f"Successfully extracted {len(key_points)} key points")
                    
                except Exception as e:
                    logger.error(f"Llama processing failed: {e}")
                    result["errors"].append(f"Llama processing failed: {str(e)}")
                    result["llama_processing"] = False
            
            result["processing_time"] = time.time() - start_time
            return result
            
        except Exception as e:
            logger.error(f"URL processing failed: {e}")
            return {
                "success": False,
                "errors": [str(e)],
                "processing_time": time.time() - start_time
            }
    
    def process_pdf(self, pdf_path: Union[str, Path], process_with_llama: bool = True, extract_images: bool = True) -> Dict[str, Any]:
        """
        Process PDF with focus on key point extraction using Llama, including image analysis.
        
        Args:
            pdf_path: Path to the PDF file
            process_with_llama: Whether to process with Llama API
            extract_images: Whether to extract and analyze images from PDF
            
        Returns:
            Processing results focused on key points
        """
        start_time = time.time()
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            return {
                "success": False,
                "errors": [f"PDF file not found: {pdf_path}"],
                "processing_time": time.time() - start_time
            }
        
        try:
            # Extract text, tables, and metadata
            extraction_result = self.pdf_processor.extract_all(pdf_path)
            
            if not extraction_result["success"]:
                return {
                    "success": False,
                    "errors": extraction_result["errors"],
                    "processing_time": time.time() - start_time
                }
            
            result = {
                "pdf_path": str(pdf_path),
                "metadata": extraction_result["metadata"],
                "extraction_method": extraction_result["extraction_method"],
                "extraction_time": extraction_result["processing_time"],
                "llama_processing": False,
                "success": True,
                "errors": []
            }
            
            # Extract images if requested
            extracted_images = []
            if extract_images:
                try:
                    extracted_images = self.pdf_processor.extract_images(pdf_path)
                    result["images_extracted"] = len(extracted_images)
                    result["image_paths"] = extracted_images
                except Exception as e:
                    logger.warning(f"Image extraction failed: {e}")
                    result["images_extracted"] = 0
                    result["image_paths"] = []
            
            # Process with Llama if requested and content is available
            if process_with_llama and (extraction_result["text"].strip() or extracted_images):
                try:
                    llama_start_time = time.time()
                    
                    # Clean and structure text
                    cleaned_data = self.text_processor.clean_and_structure(extraction_result["text"])
                    
                    # Extract key points with business focus, including images
                    logger.info(f"Starting key point extraction with {len(extracted_images)} images")
                    key_points_json = self.text_processor.extract_key_points_json(
                        cleaned_data["cleaned_text"], 
                        extracted_images if extracted_images else None
                    )
                    
                    # Check if we got meaningful results
                    total_points = sum(len(points) for points in key_points_json.values())
                    if total_points == 0 or (len(key_points_json) == 1 and "General" in key_points_json and len(key_points_json["General"]) == 1 and not key_points_json["General"][0].strip()):
                        logger.warning("Image processing may have failed, retrying with text-only analysis")
                        # Retry with text-only analysis
                        key_points_json = self.text_processor.extract_key_points_json(
                            cleaned_data["cleaned_text"], 
                            None  # No images
                        )
                    
                    # Convert JSON structure to flat list for backward compatibility
                    key_points = []
                    for category, points in key_points_json.items():
                        for point in points:
                            if point.strip():  # Only add non-empty points
                                key_points.append(f"[{category}] {point}")
                    
                    result["key_points"] = key_points
                    result["key_points_json"] = key_points_json  # Keep structured format too
                    
                    # Add text statistics for context
                    result["text_stats"] = {
                        "word_count": cleaned_data["word_count"],
                        "sentence_count": cleaned_data["sentence_count"],
                        "paragraph_count": cleaned_data["paragraph_count"]
                    }
                    
                    # Include tables if available
                    if extraction_result["tables"]:
                        result["tables"] = extraction_result["tables"]
                    
                    result["llama_processing"] = True
                    result["llama_processing_time"] = time.time() - llama_start_time
                    
                    logger.info(f"Successfully extracted {len(key_points)} key points")
                    
                except Exception as e:
                    logger.error(f"Llama processing failed: {e}")
                    result["errors"].append(f"Llama processing failed: {str(e)}")
                    result["llama_processing"] = False
            
            result["processing_time"] = time.time() - start_time
            return result
            
        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            return {
                "success": False,
                "errors": [str(e)],
                "processing_time": time.time() - start_time
            }
    
    def extract_only(self, pdf_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Extract PDF content without Llama processing.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Raw extraction results
        """
        return self.process_pdf(pdf_path, process_with_llama=False)
    
    def batch_process(self, pdf_paths: List[Union[str, Path]], process_with_llama: bool = True) -> List[Dict[str, Any]]:
        """
        Process multiple PDF files in batch.
        
        Args:
            pdf_paths: List of PDF file paths
            process_with_llama: Whether to process with Llama API
            
        Returns:
            List of processing results for each PDF
        """
        results = []
        
        for pdf_path in pdf_paths:
            try:
                result = self.process_pdf(pdf_path, process_with_llama)
                results.append(result)
            except Exception as e:
                logger.error(f"Batch processing failed for {pdf_path}: {e}")
                results.append({
                    "pdf_path": str(pdf_path),
                    "success": False,
                    "errors": [str(e)]
                })
        
        return results
    
    def summarize_pdf(self, pdf_path: Union[str, Path], summary_type: str = "executive") -> str:
        """
        Get a quick summary of a PDF.
        
        Args:
            pdf_path: Path to the PDF file
            summary_type: Type of summary ("executive", "detailed", "bullet")
            
        Returns:
            Generated summary
        """
        try:
            # Extract text only
            extraction_result = self.pdf_processor.extract_text(pdf_path)
            
            if not extraction_result.strip():
                return "No text could be extracted from the PDF."
            
            # Generate summary
            summary = self.text_processor.summarize_text(extraction_result, summary_type)
            return summary
            
        except Exception as e:
            logger.error(f"PDF summarization failed: {e}")
            return f"Summarization failed: {str(e)}"
    
    def get_pdf_insights(self, pdf_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Get comprehensive insights from a PDF.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with key insights and analysis
        """
        try:
            # Extract text
            text = self.pdf_processor.extract_text(pdf_path)
            
            if not text.strip():
                return {
                    "success": False,
                    "error": "No text could be extracted from the PDF."
                }
            
            # Clean and structure
            cleaned_data = self.text_processor.clean_and_structure(text)
            
            # Generate various insights
            insights = {
                "summary": self.text_processor.summarize_text(cleaned_data["cleaned_text"]),
                "key_points": self.text_processor.extract_key_points(cleaned_data["cleaned_text"]),
                "text_stats": {
                    "word_count": cleaned_data["word_count"],
                    "sentence_count": cleaned_data["sentence_count"],
                    "paragraph_count": cleaned_data["paragraph_count"],
                    "structure": cleaned_data["structure"]
                }
            }
            
            # Answer common questions
            common_questions = [
                "What is the main topic or purpose of this document?",
                "What are the key findings or conclusions?",
                "Who is the target audience?",
                "What actions or recommendations are suggested?"
            ]
            
            qa_results = self.text_processor.answer_questions(cleaned_data["cleaned_text"], common_questions)
            insights["qa_analysis"] = qa_results
            
            # Generate custom insights
            custom_insights_prompt = """Provide a comprehensive analysis of this document covering:
            1. Document type and purpose
            2. Key themes and topics
            3. Important data, statistics, or metrics
            4. Main arguments or conclusions
            5. Potential implications or recommendations
            6. Overall assessment of document quality and completeness
            
            Format as a structured analysis:"""
            
            custom_insights = self.text_processor.process_custom(cleaned_data["cleaned_text"], custom_insights_prompt)
            insights["comprehensive_analysis"] = custom_insights
            
            return {
                "success": True,
                "insights": insights,
                "metadata": self.pdf_processor.extract_metadata(pdf_path)
            }
            
        except Exception as e:
            logger.error(f"PDF insights generation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def answer_questions(self, pdf_path: Union[str, Path], questions: List[str]) -> Dict[str, str]:
        """
        Answer specific questions about a PDF.
        
        Args:
            pdf_path: Path to the PDF file
            questions: List of questions to answer
            
        Returns:
            Dictionary mapping questions to answers
        """
        try:
            text = self.pdf_processor.extract_text(pdf_path)
            
            if not text.strip():
                return {"error": "No text could be extracted from the PDF."}
            
            return self.text_processor.answer_questions(text, questions)
            
        except Exception as e:
            logger.error(f"Question answering failed: {e}")
            return {"error": f"Question answering failed: {str(e)}"}
    
    def process_custom(self, pdf_path: Union[str, Path], prompt: str) -> str:
        """
        Process PDF with a custom prompt.
        
        Args:
            pdf_path: Path to the PDF file
            prompt: Custom prompt to use
            
        Returns:
            Custom processing result
        """
        try:
            text = self.pdf_processor.extract_text(pdf_path)
            
            if not text.strip():
                return "No text could be extracted from the PDF."
            
            return self.text_processor.process_custom(text, prompt)
            
        except Exception as e:
            logger.error(f"Custom processing failed: {e}")
            return f"Custom processing failed: {str(e)}"
    
    def get_key_points(self, pdf_path: Union[str, Path]) -> List[str]:
        """
        Extract key points from PDF with business focus.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of key points organized by business categories
        """
        try:
            result = self.process_pdf(pdf_path, process_with_llama=True)
            
            if not result["success"]:
                logger.error(f"Failed to process PDF: {result['errors']}")
                return []
            
            if not result.get("llama_processing", False):
                logger.warning("Llama processing was not successful")
                return []
            
            return result.get("key_points", [])
            
        except Exception as e:
            logger.error(f"Key point extraction failed: {e}")
            return []


# Backward compatibility
class PDFIngest(DocumentIngest):
    """
    Backward compatibility class for PDF processing.
    Use DocumentIngest for new code that supports both PDF and HTML.
    """
    
    def __init__(self, llama_api_key: Optional[str] = None, llama_model: str = "Llama-4-Maverick-17B-128E-Instruct-FP8"):
        """Initialize the PDF ingestion system (backward compatibility)."""
        super().__init__(llama_api_key, llama_model)
        logger.info("PDFIngest initialized (backward compatibility)")
    
    def process_pdf(self, pdf_path: Union[str, Path], process_with_llama: bool = True, extract_images: bool = True) -> Dict[str, Any]:
        """
        Process PDF with focus on key point extraction using Llama, including image analysis.
        
        Args:
            pdf_path: Path to the PDF file
            process_with_llama: Whether to process with Llama API
            extract_images: Whether to extract and analyze images from PDF
            
        Returns:
            Processing results focused on key points
        """
        return super().process_pdf(pdf_path, process_with_llama, extract_images) 