"""
PDF Processor for local PDF text extraction with multiple fallback methods.
"""

import logging
import os
import sys
import time
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from contextlib import redirect_stderr, redirect_stdout

# Suppress all PyMuPDF warnings and logging
logging.getLogger('fitz').setLevel(logging.CRITICAL)
logging.getLogger('PyMuPDF').setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore", category=UserWarning, module="fitz")

# Suppress PyMuPDF C-level messages during imports
original_stdout = sys.stdout
original_stderr = sys.stderr
sys.stdout = open(os.devnull, 'w')
sys.stderr = open(os.devnull, 'w')

if TYPE_CHECKING:
    import fitz
    import pdfplumber
    import PyPDF2
    from pdfminer.high_level import extract_text as pdfminer_extract_text

logger = logging.getLogger(__name__)

# PyMuPDF (fitz) - Most reliable PDF library
PYMUPDF_AVAILABLE = False
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
    logger.info("PyMuPDF (fitz) successfully imported")
except ImportError as e:
    logger.warning(f"Could not import 'fitz' (PyMuPDF): {e}")
    try:
        import pymupdf as fitz
        PYMUPDF_AVAILABLE = True
        logger.info("PyMuPDF imported as pymupdf")
    except ImportError as e2:
        logger.warning(f"Could not import 'pymupdf' as 'fitz': {e2}")

# pdfplumber - Good for tables and structured data
PDFPLUMBER_AVAILABLE = False
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
    logger.info("pdfplumber successfully imported")
except ImportError as e:
    logger.warning(f"Could not import 'pdfplumber': {e}")

# pdfminer.six - Fallback extraction
PDFMINER_AVAILABLE = False
try:
    from pdfminer.high_level import extract_text as pdfminer_extract_text
    PDFMINER_AVAILABLE = True
    logger.info("pdfminer.six successfully imported")
except ImportError as e:
    logger.warning(f"Could not import 'pdfminer.six': {e}")

# PyPDF2 - Basic fallback
PYPDF2_AVAILABLE = False
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
    logger.info("PyPDF2 successfully imported")
except ImportError as e:
    logger.warning(f"Could not import 'PyPDF2': {e}")

# Restore stdout and stderr
sys.stdout.close()
sys.stderr.close()
sys.stdout = original_stdout
sys.stderr = original_stderr

class PDFProcessor:
    """
    PDF Processor for extracting text, tables, and metadata from PDF files.
    
    Uses multiple extraction methods with intelligent fallback logic:
    1. PyMuPDF (fitz) - General text extraction
    2. pdfplumber - Tables and structured data
    3. pdfminer - Fallback extraction
    4. PyPDF2 - Basic fallback
    """
    
    def __init__(self):
        """Initialize the PDF processor with available extraction methods."""
        self.extraction_methods = []
        
        if PYMUPDF_AVAILABLE:
            self.extraction_methods.append("pymupdf")
        if PDFPLUMBER_AVAILABLE:
            self.extraction_methods.append("pdfplumber")
        if PDFMINER_AVAILABLE:
            self.extraction_methods.append("pdfminer")
        if PYPDF2_AVAILABLE:
            self.extraction_methods.append("pypdf2")
            
        if not self.extraction_methods:
            logger.error("No PDF processing libraries available!")
            logger.error("Available packages (from pip list):")
            try:
                import subprocess
                result = subprocess.run(['pip', 'list'], capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if 'pdf' in line.lower():
                        logger.error(f"  {line}")
            except:
                pass
            
            raise ImportError(
                "No PDF processing libraries available. "
                "Please install at least one of: pymupdf, pdfplumber, pdfminer.six, PyPDF2"
            )
        
        logger.info(f"PDF Processor initialized with methods: {self.extraction_methods}")
    
    def extract_text(self, pdf_path: Union[str, Path]) -> str:
        """
        Extract text from PDF using the best available method.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as string
            
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            Exception: If all extraction methods fail
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Try PyMuPDF first (best general extraction)
        if PYMUPDF_AVAILABLE:
            try:
                return self._extract_with_pymupdf(pdf_path)
            except Exception as e:
                logger.warning(f"PyMuPDF extraction failed: {e}")
        
        # Try pdfplumber
        if PDFPLUMBER_AVAILABLE:
            try:
                return self._extract_with_pdfplumber(pdf_path)
            except Exception as e:
                logger.warning(f"pdfplumber extraction failed: {e}")
        
        # Try pdfminer
        if PDFMINER_AVAILABLE:
            try:
                return self._extract_with_pdfminer(pdf_path)
            except Exception as e:
                logger.warning(f"pdfminer extraction failed: {e}")
        
        # Try PyPDF2 as last resort
        if PYPDF2_AVAILABLE:
            try:
                return self._extract_with_pypdf2(pdf_path)
            except Exception as e:
                logger.warning(f"PyPDF2 extraction failed: {e}")
        
        raise Exception("All PDF extraction methods failed")
    
    def extract_tables(self, pdf_path: Union[str, Path]) -> List[List[List[str]]]:
        """
        Extract tables from PDF using pdfplumber.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of tables, where each table is a list of rows (list of strings)
        """
        if not PDFPLUMBER_AVAILABLE:
            logger.warning("pdfplumber not available, cannot extract tables")
            return []
        
        pdf_path = Path(pdf_path)
        tables = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)
        except Exception as e:
            logger.error(f"Error extracting tables: {e}")
        
        return tables
    
    def extract_metadata(self, pdf_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Extract metadata from PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing metadata
        """
        pdf_path = Path(pdf_path)
        metadata = {
            "filename": pdf_path.name,
            "file_size": pdf_path.stat().st_size,
            "pages": 0,
            "title": None,
            "author": None,
            "subject": None,
            "creator": None,
            "producer": None,
            "creation_date": None,
            "modification_date": None,
        }
        
        # Try PyMuPDF for metadata
        if PYMUPDF_AVAILABLE:
            try:
                # Suppress C-level print statements from PyMuPDF using context managers
                with redirect_stdout(open(os.devnull, 'w')), redirect_stderr(open(os.devnull, 'w')):
                    doc = fitz.open(pdf_path)
                    metadata["pages"] = len(doc)
                    
                    if doc.metadata:
                        metadata.update({
                            "title": doc.metadata.get("title"),
                            "author": doc.metadata.get("author"),
                            "subject": doc.metadata.get("subject"),
                            "creator": doc.metadata.get("creator"),
                            "producer": doc.metadata.get("producer"),
                            "creation_date": doc.metadata.get("creationDate"),
                            "modification_date": doc.metadata.get("modDate"),
                        })
                    doc.close()
                    
            except Exception as e:
                logger.warning(f"Error extracting metadata with PyMuPDF: {e}")
        
        # Fallback to PyPDF2 for basic metadata
        if metadata["pages"] == 0 and PYPDF2_AVAILABLE:
            try:
                with open(pdf_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    metadata["pages"] = len(reader.pages)
                    
                    if reader.metadata:
                        metadata.update({
                            "title": reader.metadata.get("/Title"),
                            "author": reader.metadata.get("/Author"),
                            "subject": reader.metadata.get("/Subject"),
                            "creator": reader.metadata.get("/Creator"),
                            "producer": reader.metadata.get("/Producer"),
                            "creation_date": reader.metadata.get("/CreationDate"),
                            "modification_date": reader.metadata.get("/ModDate"),
                        })
            except Exception as e:
                logger.warning(f"Error extracting metadata with PyPDF2: {e}")
        
        return metadata
    
    def extract_all(self, pdf_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Extract text, tables, and metadata from PDF.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing text, tables, and metadata
        """
        start_time = time.time()
        
        try:
            text = self.extract_text(pdf_path)
            tables = self.extract_tables(pdf_path)
            metadata = self.extract_metadata(pdf_path)
            
            processing_time = time.time() - start_time
            
            return {
                "text": text,
                "tables": tables,
                "metadata": metadata,
                "processing_time": processing_time,
                "extraction_method": self._get_used_method(),
                "success": True,
                "errors": []
            }
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"PDF extraction failed: {e}")
            
            return {
                "text": "",
                "tables": [],
                "metadata": self.extract_metadata(pdf_path),
                "processing_time": processing_time,
                "extraction_method": "none",
                "success": False,
                "errors": [str(e)]
            }
    
    def _extract_with_pymupdf(self, pdf_path: Path) -> str:
        """Extract text using PyMuPDF."""
        # Suppress C-level print statements from PyMuPDF using context managers
        with redirect_stdout(open(os.devnull, 'w')), redirect_stderr(open(os.devnull, 'w')):
            doc = fitz.open(pdf_path)
            text = ""
            
            for page in doc:
                text += page.get_text()
            
            doc.close()
            return text
    
    def _extract_with_pdfplumber(self, pdf_path: Path) -> str:
        """Extract text using pdfplumber."""
        text = ""
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        return text
    
    def _extract_with_pdfminer(self, pdf_path: Path) -> str:
        """Extract text using pdfminer."""
        return pdfminer_extract_text(pdf_path)
    
    def _extract_with_pypdf2(self, pdf_path: Path) -> str:
        """Extract text using PyPDF2."""
        text = ""
        
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        
        return text
    
    def _get_used_method(self) -> str:
        """Get the method that was successfully used for extraction."""
        if PYMUPDF_AVAILABLE:
            return "pymupdf"
        elif PDFPLUMBER_AVAILABLE:
            return "pdfplumber"
        elif PDFMINER_AVAILABLE:
            return "pdfminer"
        elif PYPDF2_AVAILABLE:
            return "pypdf2"
        else:
            return "none"
    
    def extract_images(self, pdf_path: Union[str, Path], output_dir: Union[str, Path] = None) -> List[str]:
        """
        Extract images from PDF and save them to files.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save extracted images (defaults to temp directory)
            
        Returns:
            List of paths to extracted image files
        """
        if not PYMUPDF_AVAILABLE:
            logger.warning("PyMuPDF not available, cannot extract images")
            return []
        
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return []
        
        # Create output directory
        if output_dir is None:
            import tempfile
            output_dir = Path(tempfile.mkdtemp(prefix="pdf_images_"))
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        image_paths = []
        
        try:
            # Suppress C-level print statements from PyMuPDF using context managers
            with redirect_stdout(open(os.devnull, 'w')), redirect_stderr(open(os.devnull, 'w')):
                doc = fitz.open(pdf_path)
                
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    
                    # Get image list from page
                    image_list = page.get_images()
                    
                    for img_index, img in enumerate(image_list):
                        try:
                            # Get image data
                            xref = img[0]
                            pix = fitz.Pixmap(doc, xref)
                            
                            # Skip if image is too small (likely icons)
                            if pix.width < 100 or pix.height < 100:
                                pix = None
                                continue
                            
                            # Convert to RGB if necessary
                            if pix.n - pix.alpha < 4:  # GRAY or RGB
                                pix1 = fitz.Pixmap(fitz.csRGB, pix)
                                pix = pix1
                            
                            # Save image
                            image_filename = f"page_{page_num + 1}_img_{img_index + 1}.png"
                            image_path = output_dir / image_filename
                            pix.save(str(image_path))
                            
                            image_paths.append(str(image_path))
                            logger.info(f"Extracted image: {image_path}")
                            
                            pix = None
                            
                        except Exception as e:
                            logger.warning(f"Failed to extract image {img_index} from page {page_num + 1}: {e}")
                            continue
                
                doc.close()
                
        except Exception as e:
            logger.error(f"Error extracting images: {e}")
        
        return image_paths 