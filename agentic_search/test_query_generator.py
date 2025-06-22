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
    
    def __init__(self, enable_reference_extraction: bool = False):
        """Initialize the research components."""
        self.query_generator = SearchQueryGenerator(
            enable_reference_extraction=enable_reference_extraction,
            max_depth=2,
            max_pages_per_level=3
        )
        self.brave_client = BraveSearchClient()
        self.analyzer = ResearchAnalyzer()
        self.enable_reference_extraction = enable_reference_extraction
    
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
        
        # Generate search queries (comprehensive if reference extraction is enabled)
        try:
            if self.enable_reference_extraction:
                # First generate primary queries
                primary_queries = await self.query_generator.generate_queries(idea_summary)
                print(f"✅ Generated {len(primary_queries)} primary queries")
                
                # Execute initial searches to get results for reference extraction
                print(f"\n🔍 Executing initial searches for reference extraction...")
                initial_search_results = []
                for i, query in enumerate(primary_queries[:3], 1):  # Use first 3 queries
                    try:
                        print(f"  • Searching [{i}/3]: {query[:50]}...")
                        search_response = await self.brave_client.search(query, count=5)
                        web_results = self.brave_client.extract_web_results(search_response)
                        initial_search_results.extend(web_results[:3])  # Top 3 results per query
                        print(f"    ✅ Found {len(web_results)} results")
                    except Exception as e:
                        print(f"    ❌ Search failed: {str(e)}")
                
                print(f"\n🔗 Starting comprehensive query generation with reference extraction...")
                print(f"   • Initial search results collected: {len(initial_search_results)}")
                
                # Now generate comprehensive queries with reference extraction
                comprehensive_result = await self.query_generator.generate_comprehensive_queries(
                    idea_summary, 
                    initial_search_results
                )
                
                queries = comprehensive_result['primary_queries'] + comprehensive_result['reference_based_queries']
                research_data["search_queries"] = queries
                research_data["primary_queries"] = comprehensive_result['primary_queries']
                research_data["reference_based_queries"] = comprehensive_result['reference_based_queries']
                research_data["reference_extraction_data"] = comprehensive_result.get('reference_extraction_data')
                
                print(f"✅ Generated {len(queries)} total queries")
                print(f"   • Primary queries: {len(comprehensive_result['primary_queries'])}")
                print(f"   • Reference-based queries: {len(comprehensive_result['reference_based_queries'])}")
                
                # Print detailed reference extraction results
                if comprehensive_result.get('reference_extraction_data'):
                    self._print_reference_extraction_details(comprehensive_result['reference_extraction_data'])
                
            else:
                # Generate basic queries
                queries = await self.query_generator.generate_queries(idea_summary)
                research_data["search_queries"] = queries
                print(f"✅ Generated {len(queries)} search queries")
            
            print(f"\n📋 All Generated Queries:")
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
    
    def _print_reference_extraction_details(self, reference_data: dict) -> None:
        """Print detailed information about reference extraction process."""
        print(f"\n" + "="*80)
        print(f"🔗 REFERENCE EXTRACTION DETAILS")
        print(f"="*80)
        
        if not reference_data.get('reference_extraction'):
            print(f"❌ No reference extraction data available")
            return
        
        ref_extract = reference_data['reference_extraction']
        summary = ref_extract.get('summary', {})
        
        print(f"\n📊 Extraction Summary:")
        print(f"   • Total pages scraped: {summary.get('total_pages_scraped', 0)}")
        print(f"   • Total references found: {summary.get('total_references_found', 0)}")
        print(f"   • Levels processed: {summary.get('levels_processed', 0)}")
        
        # Print details for each level
        levels = ref_extract.get('levels', {})
        for level_key in sorted(levels.keys()):
            level_data = levels[level_key]
            level_num = level_key.replace('level_', '')
            
            print(f"\n🔍 Level {level_num} Details:")
            print(f"   • Pages processed: {len(level_data.get('pages', []))}")
            
            # Show each page that was scraped
            for i, page in enumerate(level_data.get('pages', []), 1):
                print(f"\n   📄 Page {i}:")
                print(f"      • Title: {page.get('title', 'N/A')[:80]}...")
                print(f"      • URL: {page.get('url', 'N/A')}")
                print(f"      • Content length: {page.get('content_length', 0)} chars")
                print(f"      • References found: {page.get('reference_count', 0)}")
                
                # Show top references from this page
                references = page.get('references', [])
                if references:
                    print(f"      • Top references:")
                    for j, ref in enumerate(references[:5], 1):  # Show top 5 references
                        anchor_text = ref.get('anchor_text', '').strip()
                        if anchor_text:
                            anchor_preview = anchor_text[:60] + '...' if len(anchor_text) > 60 else anchor_text
                            print(f"        {j}. {anchor_preview}")
                            print(f"           URL: {ref.get('url', 'N/A')}")
                            if ref.get('context'):
                                context_preview = ref.get('context', '')[:80] + '...' if len(ref.get('context', '')) > 80 else ref.get('context', '')
                                print(f"           Context: {context_preview}")
                else:
                    print(f"      • No references found on this page")
            
            # Show URLs that will be processed at next level
            next_urls = level_data.get('next_level_urls', [])
            if next_urls:
                print(f"\n   🔗 URLs queued for next level ({len(next_urls)}):")
                for j, url in enumerate(next_urls[:3], 1):  # Show first 3
                    print(f"      {j}. {url}")
                if len(next_urls) > 3:
                    print(f"      ... and {len(next_urls) - 3} more")
        
        print(f"\n" + "="*80)
    
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

    # Initialize researcher (test both modes)
    try:
        # Test basic mode first
        print("\n🧪 Testing BASIC mode (without reference extraction)...")
        researcher_basic = StartupResearcher(enable_reference_extraction=False)
        print("✅ Basic StartupResearcher initialized successfully")
        print("   • SearchQueryGenerator: Ready (basic mode)")
        print("   • BraveSearchClient: Ready") 
        print("   • ResearchAnalyzer: Ready")
        
        # Test enhanced mode
        print("\n🚀 Testing ENHANCED mode (with reference extraction)...")
        researcher_enhanced = StartupResearcher(enable_reference_extraction=True)
        print("✅ Enhanced StartupResearcher initialized successfully")
        print("   • SearchQueryGenerator: Ready (with reference extraction)")
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

    try:
        # Test basic mode
        print("\n" + "="*80)
        print("🧪 BASIC MODE RESEARCH (No Reference Extraction)")
        print("="*80)
        print("🔄 Starting basic research process...")
        
        basic_research_data = await researcher_basic.conduct_research(idea_summary)
        
        print("\n📊 Basic Research Report:")
        researcher_basic.print_research_summary(basic_research_data)
        
        # Test enhanced mode
        print("\n" + "="*80)
        print("🚀 ENHANCED MODE RESEARCH (With Reference Extraction)")
        print("="*80)
        print("🔄 Starting enhanced research process...")
        
        enhanced_research_data = await researcher_enhanced.conduct_research(idea_summary)
        
        print("\n📊 Enhanced Research Report:")
        researcher_enhanced.print_research_summary(enhanced_research_data)
        
        # Compare results
        print("\n" + "="*80)
        print("⚖️  COMPARISON SUMMARY")
        print("="*80)
        
        basic_queries = len(basic_research_data.get('search_queries', []))
        enhanced_queries = len(enhanced_research_data.get('search_queries', []))
        basic_pages = basic_research_data.get('total_pages_analyzed', 0)
        enhanced_pages = enhanced_research_data.get('total_pages_analyzed', 0)
        
        print(f"📊 Query Generation:")
        print(f"   • Basic Mode: {basic_queries} queries")
        print(f"   • Enhanced Mode: {enhanced_queries} queries")
        print(f"   • Improvement: +{enhanced_queries - basic_queries} queries ({((enhanced_queries/basic_queries - 1)*100):.1f}% more)")
        
        print(f"\n📄 Data Collection:")
        print(f"   • Basic Mode: {basic_pages} pages analyzed")
        print(f"   • Enhanced Mode: {enhanced_pages} pages analyzed")
        
        if enhanced_research_data.get('reference_based_queries'):
            print(f"\n🔗 Reference-based Queries Generated:")
            for i, query in enumerate(enhanced_research_data['reference_based_queries'], 1):
                print(f"   {i}. {query}")
        
        # Show reference extraction summary if available
        if enhanced_research_data.get('reference_extraction_data'):
            ref_data = enhanced_research_data['reference_extraction_data']
            if ref_data.get('reference_extraction'):
                ref_summary = ref_data['reference_extraction']['summary']
                print(f"\n📊 Reference Extraction Summary:")
                print(f"   • Pages scraped during reference extraction: {ref_summary.get('total_pages_scraped', 0)}")
                print(f"   • Total references discovered: {ref_summary.get('total_references_found', 0)}")
                print(f"   • Reference extraction levels: {ref_summary.get('levels_processed', 0)}")
        
        print(f"\n✅ Both research modes completed successfully!")
        
        return 0
        
    except Exception as e:
        print(f"❌ Research pipeline failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 