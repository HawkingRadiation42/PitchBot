"""
HTML Processor for extracting content from HTML files and web pages.
"""

import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from urllib.parse import urljoin, urlparse

# Optional imports for HTML processing
try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError as e:
    BEAUTIFULSOUP_AVAILABLE = False
    # Note: logger is defined later, so we'll log this after logger initialization

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None

if TYPE_CHECKING:
    from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class HTMLProcessor:
    """
    HTML Processor for extracting text, metadata, and images from HTML files.
    
    Features:
    - Extract text content from HTML files
    - Extract metadata (title, description, keywords)
    - Extract and save images
    - Handle both local HTML files and URLs
    - Clean and structure extracted content
    """
    
    def __init__(self):
        """Initialize the HTML processor."""
        if not BEAUTIFULSOUP_AVAILABLE:
            logger.warning("BeautifulSoup not available. Install with: pip install beautifulsoup4")
        
        self.session = None
        if REQUESTS_AVAILABLE:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
        
        logger.info("HTML Processor initialized")
    
    def extract_from_file(self, html_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Extract content from a local HTML file.
        
        Args:
            html_path: Path to the HTML file
            
        Returns:
            Dictionary containing extracted content
        """
        html_path = Path(html_path)
        if not html_path.exists():
            return {
                "success": False,
                "errors": [f"HTML file not found: {html_path}"],
                "processing_time": 0
            }
        
        start_time = time.time()
        
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            return self._process_html_content(html_content, str(html_path))
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"HTML file processing failed: {e}")
            return {
                "success": False,
                "errors": [str(e)],
                "processing_time": processing_time
            }
    
    def extract_from_url(self, url: str) -> Dict[str, Any]:
        """
        Extract content from a URL.
        
        Args:
            url: URL to extract content from
            
        Returns:
            Dictionary containing extracted content
        """
        if not REQUESTS_AVAILABLE:
            return {
                "success": False,
                "errors": ["requests library not available. Install with: pip install requests"],
                "processing_time": 0
            }
        
        start_time = time.time()
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            html_content = response.text
            return self._process_html_content(html_content, url)
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"URL processing failed: {e}")
            return {
                "success": False,
                "errors": [str(e)],
                "processing_time": processing_time
            }
    
    def _process_html_content(self, html_content: str, source: str) -> Dict[str, Any]:
        """
        Process HTML content and extract text, metadata, and images.
        
        Args:
            html_content: Raw HTML content
            source: Source identifier (file path or URL)
            
        Returns:
            Dictionary containing extracted content
        """
        start_time = time.time()
        
        if not BEAUTIFULSOUP_AVAILABLE:
            return {
                "success": False,
                "errors": ["BeautifulSoup not available. Install with: pip install beautifulsoup4"],
                "processing_time": time.time() - start_time
            }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract text content
            text_content = self._extract_text(soup)
            
            # Extract metadata
            metadata = self._extract_metadata(soup, source)
            
            # Extract images
            images = self._extract_images(soup, source)
            
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "text": text_content,
                "metadata": metadata,
                "images": images,
                "processing_time": processing_time,
                "extraction_method": "beautifulsoup",
                "errors": []
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"HTML content processing failed: {e}")
            return {
                "success": False,
                "errors": [str(e)],
                "processing_time": processing_time
            }
    
    def _extract_text(self, soup: "BeautifulSoup") -> str:
        """
        Extract clean text content from HTML.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Clean text content
        """
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Extract text from specific content areas
        content_selectors = [
            'main', 'article', '.content', '.main-content', '.post-content',
            '.entry-content', '.article-content', '.page-content'
        ]
        
        content_text = ""
        for selector in content_selectors:
            elements = soup.select(selector)
            for element in elements:
                content_text += element.get_text(separator=' ', strip=True) + "\n"
        
        # If no specific content areas found, extract from body
        if not content_text.strip():
            body = soup.find('body')
            if body:
                content_text = body.get_text(separator=' ', strip=True)
            else:
                content_text = soup.get_text(separator=' ', strip=True)
        
        # Clean up the text
        content_text = self._clean_text(content_text)
        
        return content_text
    
    def _extract_metadata(self, soup: "BeautifulSoup", source: str) -> Dict[str, Any]:
        """
        Extract metadata from HTML.
        
        Args:
            soup: BeautifulSoup object
            source: Source identifier
            
        Returns:
            Dictionary containing metadata
        """
        metadata = {
            "source": source,
            "title": "",
            "description": "",
            "keywords": [],
            "author": "",
            "language": "",
            "charset": "",
            "viewport": "",
            "robots": "",
            "canonical_url": "",
            "og_title": "",
            "og_description": "",
            "og_image": "",
            "twitter_title": "",
            "twitter_description": "",
            "twitter_image": ""
        }
        
        # Basic metadata
        title_tag = soup.find('title')
        if title_tag:
            metadata["title"] = title_tag.get_text(strip=True)
        
        # Meta tags
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            name = meta.get('name', '').lower()
            property = meta.get('property', '').lower()
            content = meta.get('content', '')
            
            if name == 'description':
                metadata["description"] = content
            elif name == 'keywords':
                metadata["keywords"] = [kw.strip() for kw in content.split(',') if kw.strip()]
            elif name == 'author':
                metadata["author"] = content
            elif name == 'robots':
                metadata["robots"] = content
            elif property == 'og:title':
                metadata["og_title"] = content
            elif property == 'og:description':
                metadata["og_description"] = content
            elif property == 'og:image':
                metadata["og_image"] = content
            elif name == 'twitter:title':
                metadata["twitter_title"] = content
            elif name == 'twitter:description':
                metadata["twitter_description"] = content
            elif name == 'twitter:image':
                metadata["twitter_image"] = content
        
        # Language
        html_tag = soup.find('html')
        if html_tag:
            metadata["language"] = html_tag.get('lang', '')
        
        # Charset
        charset_meta = soup.find('meta', charset=True)
        if charset_meta:
            metadata["charset"] = charset_meta.get('charset', '')
        
        # Viewport
        viewport_meta = soup.find('meta', attrs={'name': 'viewport'})
        if viewport_meta:
            metadata["viewport"] = viewport_meta.get('content', '')
        
        # Canonical URL
        canonical_link = soup.find('link', attrs={'rel': 'canonical'})
        if canonical_link:
            metadata["canonical_url"] = canonical_link.get('href', '')
        
        return metadata
    
    def _extract_images(self, soup: "BeautifulSoup", source: str) -> List[Dict[str, Any]]:
        """
        Extract image information from HTML.
        
        Args:
            soup: BeautifulSoup object
            source: Source identifier
            
        Returns:
            List of image dictionaries
        """
        images = []
        img_tags = soup.find_all('img')
        
        for img in img_tags:
            img_info = {
                "src": img.get('src', ''),
                "alt": img.get('alt', ''),
                "title": img.get('title', ''),
                "width": img.get('width', ''),
                "height": img.get('height', ''),
                "class": img.get('class', []),
                "id": img.get('id', '')
            }
            
            # Resolve relative URLs
            if img_info["src"] and not img_info["src"].startswith(('http://', 'https://', 'data:')):
                if source.startswith('http'):
                    img_info["src"] = urljoin(source, img_info["src"])
            
            images.append(img_info)
        
        return images
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text.
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove empty lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Join lines with proper spacing
        text = '\n'.join(lines)
        
        # Remove common web artifacts
        text = re.sub(r'Cookie Policy|Privacy Policy|Terms of Service|Contact Us|About Us|Home|Login|Sign Up', '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def save_images(self, images: List[Dict[str, Any]], output_dir: Union[str, Path] = None) -> List[str]:
        """
        Download and save images from HTML.
        
        Args:
            images: List of image dictionaries
            output_dir: Directory to save images
            
        Returns:
            List of saved image paths
        """
        if not REQUESTS_AVAILABLE or not PIL_AVAILABLE:
            logger.warning("requests or PIL not available, cannot download images")
            return []
        
        if output_dir is None:
            import tempfile
            output_dir = Path(tempfile.mkdtemp(prefix="html_images_"))
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        saved_paths = []
        
        for i, img_info in enumerate(images):
            src = img_info.get('src', '')
            if not src or src.startswith('data:'):
                continue
            
            try:
                response = self.session.get(src, timeout=10)
                response.raise_for_status()
                
                # Determine file extension
                content_type = response.headers.get('content-type', '')
                if 'jpeg' in content_type or 'jpg' in content_type:
                    ext = '.jpg'
                elif 'png' in content_type:
                    ext = '.png'
                elif 'gif' in content_type:
                    ext = '.gif'
                elif 'webp' in content_type:
                    ext = '.webp'
                else:
                    ext = '.jpg'  # Default
                
                # Save image
                filename = f"image_{i+1}{ext}"
                image_path = output_dir / filename
                
                with open(image_path, 'wb') as f:
                    f.write(response.content)
                
                saved_paths.append(str(image_path))
                logger.info(f"Saved image: {image_path}")
                
            except Exception as e:
                logger.warning(f"Failed to download image {src}: {e}")
                continue
        
        return saved_paths 