"""
Enhanced research pipeline with multi-level reference extraction.
"""

import asyncio
from typing import Dict, List, Any
from .brave_search import BraveSearchClient
from .query_generator import SearchQueryGenerator
from .research_analyzer import ResearchAnalyzer
from .reference_extractor import ReferenceExtractor


class EnhancedResearchPipeline:
    """Complete research pipeline with multi-level reference extraction."""
    
    def __init__(self, max_depth: int = 2, max_pages_per_level: int = 5):
        """
        Initialize the enhanced research pipeline.
        
        Args:
            max_depth: Maximum depth for reference extraction
            max_pages_per_level: Maximum pages to process per level
        """
        self.query_generator = SearchQueryGenerator()
        self.search_client = BraveSearchClient()
        self.analyzer = ResearchAnalyzer()
        self.reference_extractor = ReferenceExtractor(
            max_depth=max_depth,
            max_pages_per_level=max_pages_per_level
        )
    
    async def run_comprehensive_research(
        self,
        idea_summary: str,
        enable_reference_extraction: bool = True,
        max_search_results: int = 10
    ) -> Dict[str, Any]:
        """
        Run comprehensive research with multi-level reference extraction.
        
        Args:
            idea_summary: The startup idea summary to research
            enable_reference_extraction: Whether to enable multi-level scraping
            max_search_results: Maximum search results per query
            
        Returns:
            Comprehensive research results with analysis
        """
        print("🚀 Starting Comprehensive Research Pipeline")
        print("=" * 60)
        
        # Step 1: Generate search queries
        print("📋 Step 1: Generating targeted search queries...")
        search_queries = await self.query_generator.generate_queries(idea_summary)
        print(f"✅ Generated {len(search_queries)} search queries")
        
        # Step 2: Execute searches
        print("\n🔍 Step 2: Executing search queries...")
        all_search_results = []
        search_data = {
            'search_queries': search_queries,
            'web_results': [],
            'total_pages_analyzed': 0
        }
        
        for i, query in enumerate(search_queries, 1):
            print(f"   Query {i}/{len(search_queries)}: {query}")
            try:
                search_response = await self.search_client.search(
                    query=query,
                    count=max_search_results
                )
                web_results = self.search_client.extract_web_results(search_response)
                all_search_results.extend(web_results)
                
                search_data['web_results'].append({
                    'query': query,
                    'results': web_results
                })
                
                print(f"   ✅ Found {len(web_results)} results")
                
            except Exception as e:
                print(f"   ❌ Search failed: {str(e)}")
                search_data['web_results'].append({
                    'query': query,
                    'results': []
                })
        
        search_data['total_pages_analyzed'] = len(all_search_results)
        print(f"\n✅ Search completed: {len(all_search_results)} total results found")
        
        # Step 3: Enhanced reference extraction (if enabled)
        enhanced_data = None
        if enable_reference_extraction and all_search_results:
            print("\n🔗 Step 3: Extracting references from search results...")
            try:
                enhanced_data = await self.reference_extractor.enhance_brave_search_results(
                    all_search_results
                )
                print(f"✅ Reference extraction completed:")
                print(f"   • Pages scraped: {enhanced_data['enhancement_summary']['pages_scraped']}")
                print(f"   • References found: {enhanced_data['enhancement_summary']['references_found']}")
                print(f"   • Levels processed: {enhanced_data['enhancement_summary']['levels_processed']}")
                
                # Update search data with enhanced information
                search_data['reference_extraction'] = enhanced_data
                search_data['total_pages_analyzed'] += enhanced_data['enhancement_summary']['pages_scraped']
                
            except Exception as e:
                print(f"   ⚠️ Reference extraction failed: {str(e)}")
                print("   Continuing with original search results only...")
        
        # Step 4: Analyze research data
        print(f"\n🎯 Step 4: Analyzing research data...")
        print(f"   • Total pages to analyze: {search_data['total_pages_analyzed']}")
        
        try:
            analysis = await self.analyzer.analyze_research(idea_summary, search_data)
            print("✅ Analysis completed successfully")
            
        except Exception as e:
            print(f"❌ Analysis failed: {str(e)}")
            analysis = f"Analysis failed: {str(e)}"
        
        # Compile comprehensive results
        comprehensive_results = {
            'idea_summary': idea_summary,
            'search_queries': search_queries,
            'search_results': search_data,
            'enhanced_references': enhanced_data,
            'analysis': analysis,
            'pipeline_summary': {
                'queries_executed': len(search_queries),
                'initial_search_results': len(all_search_results),
                'total_pages_analyzed': search_data['total_pages_analyzed'],
                'reference_extraction_enabled': enable_reference_extraction,
                'reference_levels_processed': (
                    enhanced_data['enhancement_summary']['levels_processed'] 
                    if enhanced_data else 0
                )
            }
        }
        
        return comprehensive_results
    
    def print_comprehensive_summary(self, results: Dict[str, Any]) -> None:
        """
        Print a comprehensive summary of the research results.
        
        Args:
            results: Results from run_comprehensive_research
        """
        print("\n" + "="*100)
        print("🎯 COMPREHENSIVE STARTUP RESEARCH SUMMARY")
        print("="*100)
        
        # Basic info
        print(f"\n💡 STARTUP IDEA:")
        print(f"   {results['idea_summary']}")
        
        # Pipeline summary
        summary = results['pipeline_summary']
        print(f"\n📊 RESEARCH SCOPE:")
        print(f"   • Search Queries Executed: {summary['queries_executed']}")
        print(f"   • Initial Search Results: {summary['initial_search_results']}")
        print(f"   • Total Pages Analyzed: {summary['total_pages_analyzed']}")
        
        if summary['reference_extraction_enabled']:
            print(f"   • Reference Extraction: ✅ ENABLED")
            print(f"   • Reference Levels Processed: {summary['reference_levels_processed']}")
            
            if results['enhanced_references']:
                enh_summary = results['enhanced_references']['enhancement_summary']
                print(f"   • Additional Pages Scraped: {enh_summary['pages_scraped']}")
                print(f"   • Total References Found: {enh_summary['references_found']}")
        else:
            print(f"   • Reference Extraction: ❌ DISABLED")
        
        # Search queries
        print(f"\n📋 SEARCH QUERIES EXECUTED:")
        for i, query in enumerate(results['search_queries'], 1):
            print(f"   {i}. {query}")
        
        # Enhanced reference data
        if results['enhanced_references']:
            ref_data = results['enhanced_references']['reference_extraction']
            print(f"\n🔗 MULTI-LEVEL REFERENCE EXTRACTION:")
            
            for level_key, level_data in ref_data['levels'].items():
                level_num = level_key.replace('level_', '')
                pages_count = len(level_data['pages'])
                print(f"   Level {level_num}: {pages_count} pages scraped")
                
                # Show top references for each level
                for page in level_data['pages'][:2]:  # Show top 2 pages per level
                    print(f"     • {page['title'][:80]}{'...' if len(page['title']) > 80 else ''}")
                    print(f"       {page['url']}")
                    if page['references']:
                        print(f"       → {len(page['references'])} references found")
        
        # Analysis results
        print(f"\n🎯 INVESTMENT ANALYSIS:")
        print("="*100)
        print(results['analysis'])
        print("="*100)
        
        print(f"\n✅ Comprehensive research completed!")
        print(f"🚀 Total data sources analyzed: {summary['total_pages_analyzed']}")


# Convenience function for quick research
async def research_startup_idea_comprehensive(
    idea_summary: str,
    max_depth: int = 2,
    max_pages_per_level: int = 5,
    max_search_results: int = 10,
    enable_reference_extraction: bool = True
) -> Dict[str, Any]:
    """
    Comprehensive startup research with multi-level reference extraction.
    
    Args:
        idea_summary: The startup idea to research
        max_depth: Maximum depth for reference extraction
        max_pages_per_level: Maximum pages to process per level
        max_search_results: Maximum search results per query
        enable_reference_extraction: Whether to enable multi-level scraping
        
    Returns:
        Comprehensive research results
    """
    pipeline = EnhancedResearchPipeline(
        max_depth=max_depth,
        max_pages_per_level=max_pages_per_level
    )
    
    results = await pipeline.run_comprehensive_research(
        idea_summary=idea_summary,
        enable_reference_extraction=enable_reference_extraction,
        max_search_results=max_search_results
    )
    
    # Print summary
    pipeline.print_comprehensive_summary(results)
    
    return results 