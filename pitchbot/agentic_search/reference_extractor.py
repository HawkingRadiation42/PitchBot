"""
Multi-level reference extraction and web content scraping.
"""

import asyncio
import re
from typing import Optional, Dict, List, Any, Set
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup
import time


class ReferenceExtractor:
    """Handles extraction of references and multi-level web scraping."""
    
    def __init__(self, max_depth: int = 2, max_pages_per_level: int = 5):
        """
        Initialize the reference extractor.
        
        Args:
            max_depth: Maximum depth for reference extraction (1 = current page only, 2 = one level deeper)
            max_pages_per_level: Maximum number of pages to process per level
        """
        self.max_depth = max_depth
        self.max_pages_per_level = max_pages_per_level
        self.session_headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    async def extract_page_content(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extract content and references from a single webpage.
        
        Args:
            url: URL to scrape
            
        Returns:
            Dictionary containing page content, references, and metadata
        """
        if not self._is_valid_url(url):
            return None
            
        try:
            async with httpx.AsyncClient(
                headers=self.session_headers,
                timeout=30.0,
                follow_redirects=True
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                if response.status_code != 200:
                    return None
                
                # Parse HTML content
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "aside"]):
                    script.decompose()
                
                # Extract main content
                content = self._extract_main_content(soup)
                
                # Extract references/links
                references = self._extract_references(soup, url)
                
                # Extract metadata
                metadata = self._extract_metadata(soup, response)
                
                return {
                    'url': url,
                    'title': soup.title.string.strip() if soup.title else '',
                    'content': content,
                    'references': references,
                    'metadata': metadata,
                    'content_length': len(content),
                    'reference_count': len(references)
                }
                
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return None
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main text content from the page."""
        # Try to find main content areas
        main_selectors = [
            'main', 'article', '[role="main"]', '.main-content', 
            '.content', '.post-content', '.entry-content'
        ]
        
        main_content = None
        for selector in main_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        # If no main content found, use body
        if not main_content:
            main_content = soup.find('body')
        
        if main_content:
            # Get text content
            text = main_content.get_text(separator=' ', strip=True)
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
        
        return ''
    
    def _extract_references(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extract relevant references/links from the page."""
        references = []
        seen_urls = set()
        
        # Find all links
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link['href'].strip()
            if not href or href.startswith('#'):
                continue
            
            # Convert relative URLs to absolute
            full_url = urljoin(base_url, href)
            
            # Skip if already seen
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)
            
            # Filter for relevant links
            if self._is_relevant_reference(full_url, link):
                references.append({
                    'url': full_url,
                    'anchor_text': link.get_text(strip=True),
                    'title': link.get('title', ''),
                    'context': self._get_link_context(link)
                })
        
        # Sort by relevance and limit
        references = self._rank_references(references)
        return references[:20]  # Top 20 most relevant references
    
    def _is_relevant_reference(self, url: str, link_element) -> bool:
        """Determine if a reference is relevant for deeper analysis."""
        # Skip certain domains and file types
        skip_domains = {
            'facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com',
            'youtube.com', 'tiktok.com', 'pinterest.com'
        }
        
        skip_extensions = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.exe'}
        
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        # Skip social media and unwanted domains
        if any(skip_domain in domain for skip_domain in skip_domains):
            return False
        
        # Skip unwanted file extensions
        if any(url.lower().endswith(ext) for ext in skip_extensions):
            return False
        
        # Skip mailto and tel links
        if url.startswith(('mailto:', 'tel:')):
            return False
        
        # Prefer links with relevant anchor text
        anchor_text = link_element.get_text(strip=True).lower()
        relevant_keywords = [
            'research', 'study', 'report', 'analysis', 'market', 'industry',
            'competitor', 'company', 'startup', 'technology', 'innovation',
            'whitepaper', 'case study', 'survey', 'data', 'statistics'
        ]
        
        if any(keyword in anchor_text for keyword in relevant_keywords):
            return True
        
        # Check if link is in content areas (not navigation)
        parent_classes = []
        parent = link_element.parent
        while parent and len(parent_classes) < 3:
            if parent.get('class'):
                parent_classes.extend(parent['class'])
            parent = parent.parent
        
        parent_class_str = ' '.join(parent_classes).lower()
        nav_indicators = ['nav', 'menu', 'header', 'footer', 'sidebar']
        
        # Prefer content links over navigation links
        if not any(indicator in parent_class_str for indicator in nav_indicators):
            return True
        
        return False
    
    def _get_link_context(self, link_element) -> str:
        """Get surrounding context for the link."""
        # Get parent paragraph or container
        parent = link_element.find_parent(['p', 'div', 'section', 'article'])
        if parent:
            context = parent.get_text(strip=True)
            # Limit context length
            if len(context) > 200:
                context = context[:200] + '...'
            return context
        return ''
    
    def _rank_references(self, references: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Rank references by relevance."""
        # Simple scoring based on anchor text and context
        for ref in references:
            score = 0
            text = (ref['anchor_text'] + ' ' + ref['context']).lower()
            
            # Boost for research-related terms
            research_terms = [
                'research', 'study', 'report', 'analysis', 'market research',
                'industry report', 'whitepaper', 'case study', 'survey',
                'competitor analysis', 'market analysis'
            ]
            
            for term in research_terms:
                if term in text:
                    score += 3
            
            # Boost for company/startup related terms
            business_terms = [
                'company', 'startup', 'business', 'enterprise', 'corporation',
                'firm', 'organization', 'venture'
            ]
            
            for term in business_terms:
                if term in text:
                    score += 2
            
            # Boost for technology terms
            tech_terms = [
                'technology', 'innovation', 'platform', 'solution', 'product',
                'service', 'application', 'software'
            ]
            
            for term in tech_terms:
                if term in text:
                    score += 1
            
            ref['relevance_score'] = score
        
        # Sort by score (descending)
        return sorted(references, key=lambda x: x['relevance_score'], reverse=True)
    
    def _extract_metadata(self, soup: BeautifulSoup, response) -> Dict[str, Any]:
        """Extract page metadata."""
        metadata = {
            'content_type': response.headers.get('content-type', ''),
            'last_modified': response.headers.get('last-modified', ''),
            'page_size': len(response.content),
        }
        
        # Extract meta tags
        meta_description = soup.find('meta', attrs={'name': 'description'})
        if meta_description:
            metadata['description'] = meta_description.get('content', '')
        
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            metadata['keywords'] = meta_keywords.get('content', '')
        
        # Extract Open Graph data
        og_tags = soup.find_all('meta', attrs={'property': lambda x: x and x.startswith('og:')})
        for tag in og_tags:
            property_name = tag.get('property', '').replace('og:', '')
            metadata[f'og_{property_name}'] = tag.get('content', '')
        
        return metadata
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid and accessible."""
        try:
            parsed = urlparse(url)
            return bool(parsed.netloc and parsed.scheme in ['http', 'https'])
        except:
            return False
    
    async def extract_multi_level_references(
        self,
        initial_urls: List[str],
        max_depth: int = None
    ) -> Dict[str, Any]:
        """
        Extract references at multiple levels from initial URLs.
        
        Args:
            initial_urls: List of URLs to start with
            max_depth: Override default max depth
            
        Returns:
            Dictionary containing multi-level reference data
        """
        max_depth = max_depth or self.max_depth
        
        result = {
            'levels': {},
            'all_pages': [],
            'reference_graph': {},
            'summary': {
                'total_pages_scraped': 0,
                'total_references_found': 0,
                'levels_processed': 0
            }
        }
        
        current_urls = initial_urls[:self.max_pages_per_level]
        processed_urls = set()
        
        for level in range(max_depth):
            if not current_urls:
                break
            
            print(f"\n🔍 Processing Level {level + 1}: {len(current_urls)} URLs")
            
            level_data = {
                'pages': [],
                'next_level_urls': []
            }
            
            # Process URLs at current level
            tasks = []
            for url in current_urls:
                if url not in processed_urls:
                    tasks.append(self.extract_page_content(url))
                    processed_urls.add(url)
            
            # Execute scraping tasks concurrently (with rate limiting)
            pages = []
            for i in range(0, len(tasks), 3):  # Process 3 at a time
                batch = tasks[i:i+3]
                batch_results = await asyncio.gather(*batch, return_exceptions=True)
                
                for page_data in batch_results:
                    if isinstance(page_data, dict):
                        pages.append(page_data)
                        result['all_pages'].append(page_data)
                        
                        # Collect references for next level
                        if level < max_depth - 1:  # Don't collect refs on last level
                            next_urls = [ref['url'] for ref in page_data['references'][:5]]
                            level_data['next_level_urls'].extend(next_urls)
                
                # Rate limiting
                if i + 3 < len(tasks):
                    await asyncio.sleep(1)
            
            level_data['pages'] = pages
            result['levels'][f'level_{level + 1}'] = level_data
            
            # Prepare URLs for next level
            next_urls = list(set(level_data['next_level_urls']))  
            next_urls = [url for url in next_urls if url not in processed_urls]
            current_urls = next_urls[:self.max_pages_per_level]
            
            result['summary']['levels_processed'] = level + 1
            print(f"✅ Level {level + 1} completed: {len(pages)} pages scraped")
        
        # Update summary statistics
        result['summary']['total_pages_scraped'] = len(result['all_pages'])
        result['summary']['total_references_found'] = sum(
            len(page['references']) for page in result['all_pages']
        )
        
        return result
    
    async def enhance_brave_search_results(self, brave_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Enhance Brave search results with deeper reference extraction.
        
        Args:
            brave_results: List of structured results from Brave Search
            
        Returns:
            Enhanced results with multi-level references
        """
        # Extract URLs from Brave search results
        initial_urls = [result['url'] for result in brave_results[:self.max_pages_per_level]]
        
        print(f"\n🔗 Enhancing {len(initial_urls)} Brave Search results with reference extraction...")
        
        # Extract multi-level references
        reference_data = await self.extract_multi_level_references(initial_urls)
        
        # Combine with original Brave results
        enhanced_results = {
            'original_brave_results': brave_results,
            'reference_extraction': reference_data,
            'enhancement_summary': {
                'original_results': len(brave_results),
                'pages_scraped': reference_data['summary']['total_pages_scraped'],
                'references_found': reference_data['summary']['total_references_found'],
                'levels_processed': reference_data['summary']['levels_processed']
            }
        }
        
        return enhanced_results


# Helper function to integrate with existing search workflow
async def enhance_search_with_references(
    brave_search_results: List[Dict[str, Any]],
    max_depth: int = 2,
    max_pages_per_level: int = 5
) -> Dict[str, Any]:
    """
    Convenience function to enhance Brave search results with reference extraction.
    
    Args:
        brave_search_results: Results from BraveSearchClient
        max_depth: Maximum depth for reference extraction
        max_pages_per_level: Maximum pages to process per level
        
    Returns:
        Enhanced results with multi-level references
    """
    extractor = ReferenceExtractor(max_depth=max_depth, max_pages_per_level=max_pages_per_level)
    return await extractor.enhance_brave_search_results(brave_search_results)
