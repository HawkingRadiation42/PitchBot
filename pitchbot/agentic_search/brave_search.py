"""
Brave Search API integration for web search queries.
"""

import os
import json
from typing import Optional, Dict, List, Any
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class BraveSearchClient:
    """Handles web search queries using Brave Search API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Brave Search client."""
        self.api_key = api_key or os.getenv("BRAVE_API_KEY")
        if not self.api_key:
            raise ValueError("BRAVE_API_KEY environment variable not set.")
        
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        self.headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key
        }
    
    async def search(self, query: str, count: int = 10, country: str = "US") -> Dict[str, Any]:
        """
        Perform a web search using Brave Search API.
        
        Args:
            query: The search query string
            count: Number of results to return (max 20)
            country: Country code for localized results
            
        Returns:
            Dictionary containing the full Brave Search API response
        """
        if not query.strip():
            raise ValueError("Search query cannot be empty")
        
        params = {
            "q": query,
            "count": min(count, 20),  # Brave API max is 20
            "country": country,
            "search_lang": "en",
            "ui_lang": "en-US",
            "safesearch": "moderate"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.base_url,
                    headers=self.headers,
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Brave Search API error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise RuntimeError(f"Search request failed: {str(e)}")
    
    def extract_web_results(self, search_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract and structure web search results from Brave API response.
        
        Args:
            search_response: Full response from Brave Search API
            
        Returns:
            List of structured web results
        """
        web_results = []
        
        if "web" not in search_response or "results" not in search_response["web"]:
            return web_results
        
        for result in search_response["web"]["results"]:
            structured_result = {
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "description": result.get("description", ""),
                "page_age": result.get("page_age", ""),
                "language": result.get("language", ""),
                "extra_snippets": result.get("extra_snippets", []),
                "meta_url": result.get("meta_url", {}),
                "thumbnail": result.get("thumbnail", {}),
                "schemas": result.get("schemas", []),
                "content_type": result.get("content_type", ""),
                
                # Rich data fields
                "organization": result.get("organization", {}),
                "location": result.get("location", {}),
                "article": result.get("article", {}),
                "product": result.get("product", {}),
                "rating": result.get("rating", {}),
                "profiles": result.get("profiles", []),
                "faq": result.get("faq", {}),
                "creative_work": result.get("creative_work", {}),
            }
            web_results.append(structured_result)
        
        return web_results
    
    def print_search_results(self, search_response: Dict[str, Any]) -> None:
        """
        Print formatted search results to console.
        
        Args:
            search_response: Full response from Brave Search API
        """
        print("=" * 80)
        print("🔍 BRAVE SEARCH RESULTS")
        print("=" * 80)
        
        # Print query information
        if "query" in search_response:
            query_info = search_response["query"]
            print(f"Original Query: {query_info.get('original', 'N/A')}")
            if query_info.get("altered"):
                print(f"Modified Query: {query_info.get('altered')}")
            print(f"Language: {query_info.get('language', {}).get('main', 'N/A')}")
            print()
        
        # Print web results
        web_results = self.extract_web_results(search_response)
        if web_results:
            print(f"📄 WEB RESULTS ({len(web_results)} found):")
            print("-" * 40)
            
            for i, result in enumerate(web_results, 1):
                print(f"\n{i}. {result['title']}")
                print(f"   URL: {result['url']}")
                print(f"   Description: {result['description'][:200]}{'...' if len(result['description']) > 200 else ''}")
                
                if result['page_age']:
                    print(f"   Age: {result['page_age']}")
                
                if result['extra_snippets']:
                    print(f"   Extra Snippets: {len(result['extra_snippets'])} available")
                
                if result['organization']:
                    org = result['organization']
                    print(f"   Organization: {org.get('name', 'N/A')}")
                
                if result['rating']:
                    rating = result['rating']
                    print(f"   Rating: {rating.get('ratingValue', 'N/A')}/{rating.get('bestRating', 'N/A')}")
                
                if result['schemas']:
                    print(f"   Structured Data: {len(result['schemas'])} schemas available")
        
        # Print other result types
        if "news" in search_response and search_response["news"].get("results"):
            news_results = search_response["news"]["results"]
            print(f"\n📰 NEWS RESULTS ({len(news_results)} found):")
            print("-" * 40)
            for i, news in enumerate(news_results[:3], 1):  # Show top 3
                print(f"\n{i}. {news.get('title', 'N/A')}")
                print(f"   Source: {news.get('source', 'N/A')}")
                print(f"   Age: {news.get('age', 'N/A')}")
                print(f"   URL: {news.get('url', 'N/A')}")
        
        if "videos" in search_response and search_response["videos"].get("results"):
            video_results = search_response["videos"]["results"]
            print(f"\n🎥 VIDEO RESULTS ({len(video_results)} found):")
            print("-" * 40)
            for i, video in enumerate(video_results[:3], 1):  # Show top 3
                print(f"\n{i}. {video.get('title', 'N/A')}")
                if video.get('video'):
                    video_data = video['video']
                    print(f"   Duration: {video_data.get('duration', 'N/A')}")
                    print(f"   Views: {video_data.get('views', 'N/A')}")
                    print(f"   Creator: {video_data.get('creator', 'N/A')}")
                print(f"   URL: {video.get('url', 'N/A')}")
        
        if "locations" in search_response and search_response["locations"].get("results"):
            location_results = search_response["locations"]["results"]
            print(f"\n📍 LOCATION RESULTS ({len(location_results)} found):")
            print("-" * 40)
            for i, location in enumerate(location_results[:3], 1):  # Show top 3
                print(f"\n{i}. {location.get('title', 'N/A')}")
                if location.get('postal_address'):
                    addr = location['postal_address']
                    print(f"   Address: {addr.get('displayAddress', 'N/A')}")
                if location.get('rating'):
                    rating = location['rating']
                    print(f"   Rating: {rating.get('ratingValue', 'N/A')}")
                print(f"   URL: {location.get('url', 'N/A')}")
        
        print("\n" + "=" * 80) 