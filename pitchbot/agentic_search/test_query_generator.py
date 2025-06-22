#!/usr/bin/env python3
"""
Comprehensive startup research pipeline test script.
"""

import asyncio
import os
import sys
import json
from dotenv import load_dotenv
from .query_generator import SearchQueryGenerator
from .brave_search import BraveSearchClient
from .research_analyzer import ResearchAnalyzer

# Load environment variables
load_dotenv()

class StartupResearcher:
    """Comprehensive startup research using query generation and web search."""
    
    def __init__(self):
        """Initialize the research components."""
        self.query_generator = SearchQueryGenerator()
        self.brave_client = BraveSearchClient()
        self.analyzer = ResearchAnalyzer()
    
    async def conduct_research(self, idea_summary: str) -> dict:
        """
        Conduct comprehensive research on a startup idea.
        
        Args:
            idea_summary: Summary of the startup idea
            
        Returns:
            Dictionary containing all research data and analysis
        """
        research_data = {
            "idea_summary": idea_summary,
            "search_queries": [],
            "web_results": [],
            "total_pages_analyzed": 0,
            "analysis": ""
        }
        
        print("🔍 Step 1: Generating strategic search queries...")
        
        # Generate search queries
        try:
            queries = await self.query_generator.generate_queries(idea_summary)
            research_data["search_queries"] = queries
            print(f"✅ Generated {len(queries)} search queries")
            
            for i, query in enumerate(queries, 1):
                print(f"  {i}. {query}")
        
        except Exception as e:
            print(f"❌ Failed to generate queries: {e}")
            return research_data
        
        print(f"\n🌐 Step 2: Executing web searches for each query...")
        
        # Execute searches for each query
        for i, query in enumerate(queries, 1):
            print(f"\n🔍 Searching [{i}/{len(queries)}]: {query[:60]}...")
            
            try:
                search_response = await self.brave_client.search(query, count=10)
                web_results = self.brave_client.extract_web_results(search_response)
                
                query_data = {
                    "query": query,
                    "results_count": len(web_results),
                    "results": web_results
                }
                
                research_data["web_results"].append(query_data)
                research_data["total_pages_analyzed"] += len(web_results)
                
                print(f"  ✅ Found {len(web_results)} results")
                
                
            except Exception as e:
                print(f"  ❌ Search failed: {e}")
                # Continue with other queries even if one fails
                continue
        
        print(f"\n📊 Step 3: Analyzing collected data...")
        print(f"  📄 Total pages analyzed: {research_data['total_pages_analyzed']}")
        
        # Generate comprehensive analysis using dedicated analyzer
        try:
            analysis = await self.analyzer.analyze_research(idea_summary, research_data)
            research_data["analysis"] = analysis
            print(f"  ✅ Investment analysis completed")
            
        except Exception as e:
            print(f"  ❌ Analysis failed: {e}")
        
        return research_data
    
    def print_research_summary(self, research_data: dict) -> None:
        """Print a formatted summary of the research results."""
        
        if research_data['analysis']:
            # Use the analyzer's dedicated print method for better formatting
            self.analyzer.print_analysis_summary(research_data['idea_summary'], research_data, research_data['analysis'])
        else:
            print("\n" + "="*100)
            print("📊 COMPREHENSIVE STARTUP RESEARCH REPORT")
            print("="*100)
            
            print(f"\n💡 ORIGINAL IDEA:")
            print(f"   {research_data['idea_summary']}")
            
            print(f"\n🔍 RESEARCH SCOPE:")
            print(f"   • Search Queries Generated: {len(research_data['search_queries'])}")
            print(f"   • Total Web Pages Analyzed: {research_data['total_pages_analyzed']}")
            print(f"   • Average Results per Query: {research_data['total_pages_analyzed'] / len(research_data['search_queries']):.1f}")
            
            print(f"\n📋 SEARCH QUERIES USED:")
            for i, query in enumerate(research_data['search_queries'], 1):
                print(f"   {i}. {query}")
            
            print(f"\n❌ Analysis could not be completed.")
            print(f"\n✅ Research data collection completed successfully!")


async def main() -> int:
    """
    Main function to run the comprehensive startup research pipeline.
    """
    
    # Check environment variables
    missing_keys = []
    if not os.getenv("LLAMA_API_KEY"):
        missing_keys.append("LLAMA_API_KEY")
    if not os.getenv("BRAVE_API_KEY"):
        missing_keys.append("BRAVE_API_KEY")
    
    if missing_keys:
        print(f"❌ Missing environment variables: {', '.join(missing_keys)}")
        print("   Please add to your .env file:")
        for key in missing_keys:
            print(f"   {key}='your-key-here'")
        return 1
    
    print("✅ Environment variables set")

    # Initialize researcher
    try:
        researcher = StartupResearcher()
        print("✅ StartupResearcher initialized successfully")
        print("   • SearchQueryGenerator: Ready")
        print("   • BraveSearchClient: Ready") 
        print("   • ResearchAnalyzer: Ready")
    except Exception as e:
        print(f"❌ Failed to initialize researcher: {e}")
        return 1

    print("\n🚀 Comprehensive Startup Research Pipeline Ready!")
    
    # Test idea summary
    idea_summary = (
        "A platform that uses AI to connect freelance writers with businesses "
        "that need high-quality content. The platform will use NLP to match "
        "writers' skills and styles with the specific needs of a business, "
        "ensuring a better fit and reducing the time businesses spend on hiring."
    )

    print(f"\n📝 Analyzing idea: '{idea_summary[:80]}...'")
    print("\n🔄 Starting comprehensive research process...")

    try:
        # Conduct full research
        research_data = await researcher.conduct_research(idea_summary)
        
        # Print comprehensive report
        researcher.print_research_summary(research_data)
        
        return 0
        
    except Exception as e:
        print(f"❌ Research pipeline failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 