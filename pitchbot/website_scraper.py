"""
AI Website Scraper - Comprehensive web scraping with intelligent content analysis.

This module provides a production-ready website scraper that combines:
- Sitemap parsing and discovery
- Content-aware filtering and scoring
- Strategic crawling with rate limiting
- Limited recursive discovery
- Llama 4 API integration for content analysis
"""

import asyncio
import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser

import aiohttp
import requests
from bs4 import BeautifulSoup

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")
except ImportError:
    pass

# Import existing text processor for Llama integration
from .pdf_ingest.text_processor import TextProcessor

logger = logging.getLogger(__name__)


@dataclass
class PageInfo:
    """Information about a page to be scraped."""
    url: str
    title: str = ""
    content_score: float = 0.0
    word_count: int = 0
    depth: int = 0
    source: str = "unknown"  # 'sitemap', 'recursive', 'internal_link'
    last_modified: Optional[str] = None
    priority: float = 0.5
    changefreq: Optional[str] = None


@dataclass
class ScrapingResult:
    """Result of scraping a single page."""
    page_info: PageInfo
    summary: str = ""
    key_points: List[str] = field(default_factory=list)
    outbound_links: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    timestamp: str = ""
    error: Optional[str] = None


class ContentScorer:
    """Intelligent content scoring system for prioritizing URLs."""
    
    def __init__(self):
        # High-value URL patterns (positive scoring)
        self.high_value_patterns = [
            r'/how-it-works/?', r'/pricing/?', r'/use-cases/?', r'/help/?', 
            r'/blog/?', r'/articles/?', r'/docs/?', r'/features/?', 
            r'/solutions/?', r'/guides/?', r'/tutorials/?', r'/documentation/?',
            r'/news/?', r'/post/?', r'/about/?', r'/product/?', r'/services/?'
        ]
        
        # Low-value URL patterns (negative scoring)
        self.low_value_patterns = [
            r'/contact/?', r'/privacy/?', r'/terms/?', r'/login/?', 
            r'/cart/?', r'/checkout/?', r'/search/?', r'/sitemap/?',
            r'/robots\.txt', r'/favicon\.ico', r'/\.(css|js|png|jpg|jpeg|gif|svg|pdf)$'
        ]
        
        # Content indicators for scoring
        self.content_indicators = [
            'article', 'main', 'content', 'post', 'entry', 'story',
            'section', 'chapter', 'page-content', 'text-content'
        ]
        
        # Semantic HTML tags that indicate content
        self.semantic_tags = [
            'article', 'section', 'main', 'aside', 'nav', 'header', 'footer',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'blockquote', 'pre'
        ]
    
    def score_url(self, url: str) -> float:
        """Score a URL based on its pattern."""
        score = 0.5  # Base score
        
        url_lower = url.lower()
        
        # Check high-value patterns
        for pattern in self.high_value_patterns:
            if re.search(pattern, url_lower):
                score += 0.3
                break
        
        # Check low-value patterns
        for pattern in self.low_value_patterns:
            if re.search(pattern, url_lower):
                score -= 0.4
                break
        
        # Bonus for root domain
        if urlparse(url).path in ['', '/']:
            score += 0.2
        
        return max(0.0, min(1.0, score))
    
    def score_content(self, soup: BeautifulSoup, html: str) -> Tuple[float, int]:
        """Score content based on analysis."""
        score = 0.5  # Base score
        word_count = 0
        
        # Extract main content
        main_content = self._extract_main_content(soup)
        if main_content:
            text = main_content.get_text()
            word_count = len(text.split())
            
            # Score based on word count
            if word_count > 1000:
                score += 0.3
            elif word_count > 500:
                score += 0.2
            elif word_count > 100:
                score += 0.1
            else:
                score -= 0.2
            
            # Score based on semantic structure
            semantic_count = len(main_content.find_all(self.semantic_tags))
            if semantic_count > 10:
                score += 0.2
            elif semantic_count > 5:
                score += 0.1
            
            # Score based on headings
            headings = main_content.find_all(['h1', 'h2', 'h3'])
            if len(headings) > 3:
                score += 0.2
            elif len(headings) > 1:
                score += 0.1
        
        # Check for meta tags
        meta_description = soup.find('meta', attrs={'name': 'description'})
        if meta_description and meta_description.get('content'):
            score += 0.1
        
        # Check for article structure
        if soup.find('article'):
            score += 0.2
        
        return max(0.0, min(1.0, score)), word_count
    
    def _extract_main_content(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """Extract the main content area from the page."""
        # Try common content selectors
        selectors = [
            'main', 'article', '[role="main"]', '.main-content', '.content',
            '.post-content', '.entry-content', '.article-content', '#content',
            '#main', '.main', '.page-content'
        ]
        
        for selector in selectors:
            content = soup.select_one(selector)
            if content:
                return content
        
        # Fallback: find the largest text container
        text_containers = soup.find_all(['div', 'section', 'article'])
        if text_containers:
            largest_container = max(text_containers, 
                                  key=lambda x: len(x.get_text().split()))
            return largest_container
        
        return None


class RobustWebsiteScraper:
    """Main orchestrator for comprehensive website scraping."""
    
    def __init__(
        self,
        base_url: str,
        max_depth: int = 10,
        max_pages: int = 1000,
        delay: float = 1.0,
        concurrent_requests: int = 5,
        content_threshold: float = 0.4,
        cache_duration: int = 3600,
        llama_api_key: Optional[str] = None,
        llama_model: str = "Llama-4-Maverick-17B-128E-Instruct-FP8"
    ):
        """
        Initialize the website scraper.
        
        Args:
            base_url: Starting URL for scraping
            max_depth: Maximum crawl depth
            max_pages: Maximum pages to process
            delay: Delay between requests in seconds
            concurrent_requests: Maximum concurrent requests
            content_threshold: Minimum content score to process
            cache_duration: Cache duration in seconds
            llama_api_key: Llama API key (defaults to LLAMA_API_KEY env var)
            llama_model: Llama model to use
        """
        self.base_url = base_url.rstrip('/')
        self.domain = urlparse(base_url).netloc
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.delay = delay
        self.concurrent_requests = concurrent_requests
        self.content_threshold = content_threshold
        self.cache_duration = cache_duration
        
        # Initialize components
        self.content_scorer = ContentScorer()
        self.text_processor = TextProcessor(api_key=llama_api_key, model=llama_model)
        
        # State tracking
        self.processed_urls: Set[str] = set()
        self.url_cache: Dict[str, Tuple[float, Any]] = {}
        self.robots_parser: Optional[RobotFileParser] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore: Optional[asyncio.Semaphore] = None
        
        # Results
        self.results: List[ScrapingResult] = []
        self.start_time = time.time()
        
        logger.info(f"Initialized scraper for {base_url}")
    
    async def scrape_comprehensive(self) -> List[ScrapingResult]:
        """Main method to perform comprehensive website scraping."""
        logger.info(f"Starting comprehensive scraping of {self.base_url}")
        
        try:
            # Initialize async components
            self.session = aiohttp.ClientSession(
                headers={'User-Agent': 'PitchBot-WebsiteScraper/1.0'},
                timeout=aiohttp.ClientTimeout(total=30)
            )
            self.semaphore = asyncio.Semaphore(self.concurrent_requests)
            
            # Phase 1: Check robots.txt
            await self._check_robots_txt()
            
            # Phase 2: Discover sitemaps
            sitemap_urls = await self._discover_sitemap()
            
            # Phase 3: Parse sitemaps and get initial URLs
            all_urls = []
            for sitemap_url in sitemap_urls:
                urls = await self._parse_sitemap(sitemap_url)
                all_urls.extend(urls)
            
            # Phase 4: If no URLs from sitemaps, start with homepage
            if not all_urls:
                logger.info("No URLs found in sitemaps, starting with homepage")
                homepage_info = PageInfo(
                    url=self.base_url,
                    source='homepage',
                    priority=1.0
                )
                all_urls = [homepage_info]
            
            # Phase 5: Prioritize URLs
            prioritized_urls = self._prioritize_urls(all_urls)
            
            # Phase 6: Strategic crawling
            await self._strategic_crawl(prioritized_urls)
            
            # Phase 7: Limited recursive discovery (enhanced)
            await self._recursive_discovery()
            
            logger.info(f"Scraping completed. Processed {len(self.results)} pages")
            return self.results
            
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            raise
        finally:
            if self.session:
                await self.session.close()
    
    async def _check_robots_txt(self):
        """Check robots.txt for crawling permissions."""
        try:
            robots_url = urljoin(self.base_url, '/robots.txt')
            async with self.session.get(robots_url) as response:
                if response.status == 200:
                    robots_content = await response.text()
                    self.robots_parser = RobotFileParser()
                    self.robots_parser.read(robots_content.splitlines())
                    logger.info("Robots.txt parsed successfully")
                else:
                    logger.info("No robots.txt found or not accessible")
        except Exception as e:
            logger.warning(f"Failed to check robots.txt: {e}")
    
    async def _discover_sitemap(self) -> List[str]:
        """Discover sitemap URLs."""
        sitemap_urls = []
        
        # Common sitemap locations
        sitemap_candidates = [
            '/sitemap.xml',
            '/sitemap_index.xml',
            '/sitemaps.xml',
            '/sitemap/sitemap.xml'
        ]
        
        for candidate in sitemap_candidates:
            try:
                sitemap_url = urljoin(self.base_url, candidate)
                async with self.session.get(sitemap_url) as response:
                    if response.status == 200:
                        sitemap_urls.append(sitemap_url)
                        logger.info(f"Found sitemap: {sitemap_url}")
            except Exception as e:
                logger.debug(f"Sitemap not found at {candidate}: {e}")
        
        # Also check robots.txt for sitemap location
        if self.robots_parser:
            try:
                sitemap_from_robots = self.robots_parser.site_maps()
                if sitemap_from_robots:
                    sitemap_urls.extend(sitemap_from_robots)
                    logger.info(f"Found sitemaps in robots.txt: {sitemap_from_robots}")
            except Exception as e:
                logger.debug(f"Failed to get sitemaps from robots.txt: {e}")
        
        return list(set(sitemap_urls))
    
    async def _parse_sitemap(self, sitemap_url: str) -> List[PageInfo]:
        """Parse XML sitemap and extract URLs."""
        urls = []
        
        try:
            async with self.session.get(sitemap_url) as response:
                if response.status != 200:
                    return urls
                
                content = await response.text()
                soup = BeautifulSoup(content, 'xml')
                
                # Handle sitemap index files
                sitemaps = soup.find_all('sitemap')
                if sitemaps:
                    for sitemap in sitemaps:
                        loc = sitemap.find('loc')
                        if loc:
                            sub_urls = await self._parse_sitemap(loc.text.strip())
                            urls.extend(sub_urls)
                    return urls
                
                # Parse regular sitemap
                url_elements = soup.find_all('url')
                for url_elem in url_elements:
                    loc = url_elem.find('loc')
                    if not loc:
                        continue
                    
                    url = loc.text.strip()
                    if not self._is_same_domain(url):
                        continue
                    
                    # Extract additional metadata
                    lastmod = url_elem.find('lastmod')
                    priority = url_elem.find('priority')
                    changefreq = url_elem.find('changefreq')
                    
                    page_info = PageInfo(
                        url=url,
                        source='sitemap',
                        last_modified=lastmod.text.strip() if lastmod else None,
                        priority=float(priority.text.strip()) if priority else 0.5,
                        changefreq=changefreq.text.strip() if changefreq else None
                    )
                    urls.append(page_info)
                
                logger.info(f"Parsed {len(urls)} URLs from sitemap: {sitemap_url}")
                
        except Exception as e:
            logger.error(f"Failed to parse sitemap {sitemap_url}: {e}")
        
        return urls
    
    def _prioritize_urls(self, urls: List[PageInfo]) -> List[PageInfo]:
        """Score and prioritize URLs."""
        for url_info in urls:
            url_info.content_score = self.content_scorer.score_url(url_info.url)
        
        # Sort by content score (descending)
        prioritized = sorted(urls, key=lambda x: x.content_score, reverse=True)
        
        # Filter by content threshold
        filtered = [url for url in prioritized if url.content_score >= self.content_threshold]
        
        logger.info(f"Prioritized {len(filtered)} URLs from {len(urls)} total")
        return filtered[:self.max_pages]
    
    async def _strategic_crawl(self, urls: List[PageInfo]):
        """Process high-priority URLs strategically."""
        tasks = []
        
        for url_info in urls:
            if len(self.results) >= self.max_pages:
                break
            
            if url_info.url in self.processed_urls:
                continue
            
            task = asyncio.create_task(self._process_page(url_info))
            tasks.append(task)
            
            # Add delay between task creation
            await asyncio.sleep(self.delay / self.concurrent_requests)
        
        # Wait for all tasks to complete
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Task failed: {result}")
    
    async def _recursive_discovery(self):
        """Perform limited recursive discovery from processed pages."""
        if len(self.results) >= self.max_pages:
            return
        
        discovered_urls = set()
        
        # Collect new URLs from processed pages
        for result in self.results:
            for link in result.outbound_links:
                if (self._is_same_domain(link) and 
                    link not in self.processed_urls and
                    link not in discovered_urls):
                    discovered_urls.add(link)
        
        # Convert to PageInfo objects and score them
        new_urls = []
        for url in list(discovered_urls)[:self.max_pages - len(self.results)]:
            page_info = PageInfo(url=url, source='recursive')
            page_info.content_score = self.content_scorer.score_url(url)
            if page_info.content_score >= self.content_threshold:
                new_urls.append(page_info)
        
        # Sort by content score for better prioritization
        new_urls.sort(key=lambda x: x.content_score, reverse=True)
        
        # Process new URLs
        if new_urls:
            logger.info(f"Processing {len(new_urls)} discovered URLs from recursive discovery")
            await self._strategic_crawl(new_urls)
        
        # If we still have room and found some URLs, do another round
        if len(self.results) < self.max_pages and len(new_urls) > 0:
            logger.info("Doing another round of recursive discovery")
            await self._recursive_discovery()
    
    async def _process_page(self, page_info: PageInfo) -> Optional[ScrapingResult]:
        """Process a single page."""
        if page_info.url in self.processed_urls:
            return None
        
        self.processed_urls.add(page_info.url)
        start_time = time.time()
        
        try:
            # Check robots.txt
            if self.robots_parser and not self.robots_parser.can_fetch('*', page_info.url):
                logger.info(f"Skipping {page_info.url} (robots.txt)")
                return None
            
            # Fetch page content
            async with self.semaphore:
                html_content = await self._fetch_with_rate_limit(page_info.url)
            
            if not html_content:
                return None
            
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Score content
            content_score, word_count = self.content_scorer.score_content(soup, html_content)
            page_info.content_score = content_score
            page_info.word_count = word_count
            
            # Extract title
            title_tag = soup.find('title')
            if title_tag:
                page_info.title = title_tag.get_text(strip=True)
            
            # Extract links
            outbound_links = self._extract_links(soup, page_info.url)
            
            # Process with Llama API
            summary, key_points = await self._summarize_with_llama(html_content)
            
            processing_time = time.time() - start_time
            
            result = ScrapingResult(
                page_info=page_info,
                summary=summary,
                key_points=key_points,
                outbound_links=outbound_links,
                processing_time=processing_time,
                timestamp=datetime.now().isoformat()
            )
            
            self.results.append(result)
            logger.info(f"Processed {page_info.url} (score: {content_score:.2f})")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process {page_info.url}: {e}")
            error_result = ScrapingResult(
                page_info=page_info,
                processing_time=time.time() - start_time,
                timestamp=datetime.now().isoformat(),
                error=str(e)
            )
            self.results.append(error_result)
            return error_result
    
    async def _fetch_with_rate_limit(self, url: str) -> Optional[str]:
        """Fetch URL content with rate limiting."""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def _batch_fetch_urls(self, urls: List[str]) -> List[str]:
        """Fetch URL content using the provided pattern."""
        bodies = []
        for url in urls:
            try:
                page_response = requests.get(url, timeout=10)
                if page_response.ok:
                    text_snippet = page_response.text[:2000]  # limit to first 2KB for speed
                    bodies.append(f"URL: {url}\n{text_snippet}\n---")
            except Exception as e:
                bodies.append(f"URL: {url}\nError: {str(e)}\n---")
        return bodies
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract links from HTML."""
        links = []
        
        # Extract from anchor tags
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)
            
            # Clean the URL (remove anchors, fragments, etc.)
            clean_url = self._clean_url(absolute_url)
            
            if self._should_crawl(clean_url):
                links.append(clean_url)
        
        # Also check for navigation menus and common link containers
        nav_selectors = [
            'nav a[href]',
            '.nav a[href]',
            '.navigation a[href]',
            '.menu a[href]',
            '.header a[href]',
            '.footer a[href]',
            '[role="navigation"] a[href]',
            '.main-nav a[href]',
            '.primary-nav a[href]'
        ]
        
        for selector in nav_selectors:
            for link in soup.select(selector):
                href = link.get('href')
                if href:
                    absolute_url = urljoin(base_url, href)
                    clean_url = self._clean_url(absolute_url)
                    if self._should_crawl(clean_url):
                        links.append(clean_url)
        
        # Remove duplicates and return
        return list(set(links))
    
    def _clean_url(self, url: str) -> str:
        """Clean URL by removing fragments, query parameters, and normalizing."""
        try:
            parsed = urlparse(url)
            # Remove fragments (#) and normalize
            clean_url = urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                '',  # Remove query parameters
                ''   # Remove fragments
            ))
            # Remove trailing slash for consistency
            if clean_url.endswith('/') and len(clean_url) > len(parsed.scheme + '://' + parsed.netloc):
                clean_url = clean_url.rstrip('/')
            return clean_url
        except Exception:
            return url
    
    def _should_crawl(self, url: str) -> bool:
        """Determine if a URL should be crawled."""
        if not self._is_same_domain(url):
            return False
        
        # Skip obvious non-content files
        skip_extensions = ['.css', '.js', '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico', '.woff', '.woff2', '.ttf', '.eot']
        if any(url.lower().endswith(ext) for ext in skip_extensions):
            return False
        
        # Skip obvious utility pages (but be less restrictive)
        skip_patterns = [
            r'/privacy/?$', r'/terms/?$', r'/contact/?$', r'/search/?$',
            r'/login/?$', r'/signup/?$', r'/cart/?$', r'/checkout/?$',
            r'/robots\.txt$', r'/sitemap\.xml$', r'/favicon\.ico$'
        ]
        if any(re.search(pattern, url.lower()) for pattern in skip_patterns):
            return False
        
        return True
    
    async def _summarize_with_llama(self, html_content: str) -> Tuple[str, List[str]]:
        """Summarize content using Llama API."""
        try:
            # Extract text content
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            
            # Clean text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            if not text.strip():
                return "No content available", []
            
            # Limit text length for API
            if len(text) > 4000:
                text = text[:4000] + "..."
            
            # Generate summary
            summary = self.text_processor.summarize_text(text, "executive")
            
            # Extract key points
            key_points = self.text_processor.extract_key_points(text)
            
            return summary, key_points
            
        except Exception as e:
            logger.error(f"Llama processing failed: {e}")
            return f"Processing failed: {str(e)}", []
    
    def _is_same_domain(self, url: str) -> bool:
        """Check if URL is from the same domain."""
        try:
            parsed = urlparse(url)
            return parsed.netloc == self.domain
        except Exception:
            return False
    
    def get_results_summary(self) -> Dict[str, Any]:
        """Get a summary of scraping results."""
        end_time = time.time()
        total_time = end_time - self.start_time
        
        successful_results = [r for r in self.results if not r.error]
        failed_results = [r for r in self.results if r.error]
        
        return {
            "scraping_session": {
                "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
                "end_time": datetime.fromtimestamp(end_time).isoformat(),
                "base_url": self.base_url,
                "total_pages": len(self.results),
                "successful_pages": len(successful_results),
                "failed_pages": len(failed_results),
                "total_time": total_time,
                "configuration": {
                    "max_depth": self.max_depth,
                    "max_pages": self.max_pages,
                    "delay": self.delay,
                    "concurrent_requests": self.concurrent_requests,
                    "content_threshold": self.content_threshold
                }
            },
            "results": [
                {
                    "url": result.page_info.url,
                    "title": result.page_info.title,
                    "summary": result.summary,
                    "key_points": result.key_points,
                    "content_score": result.page_info.content_score,
                    "word_count": result.page_info.word_count,
                    "processing_time": result.processing_time,
                    "error": result.error
                }
                for result in self.results
            ]
        }
    
    def save_results(self, output_path: str):
        """Save results to JSON file."""
        summary = self.get_results_summary()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to {output_path}")


# Convenience function for quick scraping
async def scrape_website(
    base_url: str,
    max_pages: int = 100,
    output_path: Optional[str] = None,
    **kwargs
) -> List[ScrapingResult]:
    """
    Convenience function for quick website scraping.
    
    Args:
        base_url: URL to scrape
        max_pages: Maximum pages to process
        output_path: Optional path to save results
        **kwargs: Additional arguments for RobustWebsiteScraper
    
    Returns:
        List of scraping results
    """
    scraper = RobustWebsiteScraper(base_url=base_url, max_pages=max_pages, **kwargs)
    results = await scraper.scrape_comprehensive()
    
    if output_path:
        scraper.save_results(output_path)
    
    return results 