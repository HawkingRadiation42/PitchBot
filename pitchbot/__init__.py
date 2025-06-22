"""
PitchBot - AI-powered pitch assistant for creating compelling presentations and proposals.
"""

__version__ = "0.1.0"
__author__ = "LlamaCon"
__email__ = "your.email@example.com"

from .main import main
from .pdf_ingest import PDFIngest, PDFProcessor, TextProcessor
from .website_scraper import RobustWebsiteScraper, ContentScorer, PageInfo, ScrapingResult, scrape_website

__all__ = [
    "main", 
    "PDFIngest", 
    "PDFProcessor", 
    "TextProcessor",
    "RobustWebsiteScraper",
    "ContentScorer", 
    "PageInfo", 
    "ScrapingResult", 
    "scrape_website"
] 