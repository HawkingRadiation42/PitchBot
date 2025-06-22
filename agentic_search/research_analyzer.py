"""
Research analysis using Llama API for comprehensive startup evaluation.
"""

import os
from typing import Optional, Dict, List, Any
import httpx
from llama_api_client import AsyncLlamaAPIClient

from . import config


class ResearchAnalyzer:
    """Handles comprehensive analysis of startup research data using Llama model."""
    
    def __init__(self):
        """Initialize the analyzer with configuration."""
        api_key = os.getenv("LLAMA_API_KEY")
        if not api_key:
            raise ValueError("LLAMA_API_KEY environment variable not set.")

        self.client = AsyncLlamaAPIClient(
            api_key=api_key,
        )
        # Use the model from the config file
        self.model = config.default_config.llama_model
    
    def _create_analysis_prompt(self, idea_summary: str, research_data: Dict[str, Any]) -> str:
        """
        Create a comprehensive analysis prompt for evaluating startup research data.
        
        Args:
            idea_summary: The original startup idea summary
            research_data: Dictionary containing search queries and web results
        """
        # Aggregate all web results into a structured format (simplified to essential data only)
        web_data_summary = []
        
        for query_data in research_data["web_results"]:
            query = query_data["query"]
            results = query_data["results"]
            
            web_data_summary.append(f"\n=== SEARCH QUERY: {query} ===")
            
            for i, result in enumerate(results[:10], 1):  # Top 10 per query
                web_data_summary.append(f"\n{i}. {result['title']}")
                web_data_summary.append(f"   Description: {result['description']}")
                
                # Include extra_snippets as "content" if available
                # if result.get('extra_snippets'):
                #     content = '; '.join(result['extra_snippets'][:3])  # Use up to 3 snippets as content
                #     web_data_summary.append(f"   Content: {content}")
        
        web_data_text = "\n".join(web_data_summary)
        
        prompt = f"""You are a world-class venture capital analyst and startup advisor with deep expertise in market research and competitive analysis.

    You are evaluating a **startup idea** using the provided **original idea summary** and **web-based research data**. Your goal is to assess the quality, uniqueness, and viability of the current idea in the context of the existing market and competitors.

    ---

    **ORIGINAL STARTUP IDEA SUMMARY:**  
    {idea_summary}

    **RESEARCH COVERAGE:**  
    This research was conducted across {len(research_data['search_queries'])} targeted search queries, analyzing {research_data['total_pages_analyzed']} web pages, market reports, and competitive insights.

    {web_data_text}

    ---

    ## 🔍 ANALYSIS OBJECTIVES

    Your analysis must include the following sections:

    ### 1. DIFFERENCE FROM ORIGINAL IDEA
    - What are the key changes or pivots from the original idea?
    - Are these changes improving the positioning, or diluting the core?
    - Is the revised version more aligned with user demand or market dynamics?

    ### 2. MARKET ANALYSIS
    - Size and growth of the relevant market(s) (include TAM/SAM/SOM if available)
    - Key market trends and shifts affecting this space
    - Who are the target customers and how well-defined are the segments?
    - Is there current momentum or demand in this space?

    ### 3. COMPETITOR ANALYSIS
    - Direct competitors (list specific names found in the research)
    - Indirect or adjacent players solving similar problems
    - Key differentiators between this idea and the competition
    - Strengths and weaknesses of this idea’s positioning

    ### 4. UNIQUENESS & DEFENSIBILITY
    - What makes this idea meaningfully different from existing solutions?
    - Is there technical, operational, or business model defensibility?
    - Can this advantage be sustained or is it easily replicable?

    ### 5. TRACTION SIGNALS (if available)
    - Mentions of similar companies gaining traction
    - User pain point validation or early demand evidence
    - Any investor or customer interest observed in research

    ### 6. GAPS & CONCERNS
    - Are there any obvious flaws, missing pieces, or execution risks?
    - What are the critical unknowns or assumptions that need validation?

    ---

    **INSTRUCTIONS:**
    - Be concise, data-driven, and critical where needed
    - Use only the information in the research data (avoid speculation)
    - Use professional, VC-style language and structured bullet points
    - If a section lacks data, explicitly write **"Not available"**

    ---

    Your analysis will be used to inform future investment and product development decisions. Structure the output clearly under each heading."""
        return prompt


    async def analyze_research(self, idea_summary: str, research_data: Dict[str, Any]) -> str:
        """
        Analyze comprehensive research data and generate investment evaluation.
        
        Args:
            idea_summary: The original startup idea summary
            research_data: Dictionary containing search queries and web results
            
        Returns:
            Comprehensive analysis report as a string
        """
        if not research_data.get("web_results"):
            raise ValueError("No web research data provided for analysis")
        
        prompt = self._create_analysis_prompt(idea_summary, research_data)
        
        try:
            response = await self.client.chat.completions.create(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
            )
            
            analysis = response.completion_message.content.text.strip()
            return analysis
            
        except Exception as e:
            raise RuntimeError(f"Research analysis failed: {str(e)}") from e

    def update_prompt_template(self, custom_prompt_template: str):
        """
        Update the prompt template for customization.
        
        Args:
            custom_prompt_template: Custom prompt template with placeholders
        """
        def _custom_prompt(idea_summary: str, research_data: Dict[str, Any]) -> str:
            return custom_prompt_template.format(
                idea_summary=idea_summary,
                total_pages=research_data['total_pages_analyzed'],
                num_queries=len(research_data['search_queries']),
                web_data="[Web data would be inserted here]"
            )
        
        self._create_analysis_prompt = _custom_prompt

    def print_analysis_summary(self, idea_summary: str, research_data: Dict[str, Any], analysis: str) -> None:
        """
        Print a formatted summary of the analysis results.
        
        Args:
            idea_summary: The original startup idea summary
            research_data: Original research data
            analysis: Generated analysis report
        """
        print("\n" + "="*100)
        print("🎯 COMPREHENSIVE STARTUP INVESTMENT ANALYSIS")
        print("="*100)
        
        print(f"\n💡 STARTUP IDEA ANALYZED:")
        print(f"   {idea_summary}")
        
        print(f"\n📊 RESEARCH SCOPE:")
        print(f"   • Search Queries: {len(research_data['search_queries'])}")
        print(f"   • Web Pages Analyzed: {research_data['total_pages_analyzed']}")
        print(f"   • Data Sources: Brave Search API + Llama Analysis")
        
        print(f"\n📋 SEARCH QUERIES EXECUTED:")
        for i, query in enumerate(research_data['search_queries'], 1):
            print(f"   {i}. {query}")
        
        print(f"\n🎯 INVESTMENT ANALYSIS REPORT:")
        print("="*100)
        print(analysis)
        print("="*100)
        
        print(f"\n✅ Analysis completed successfully!")
        print(f"📈 Ready for investment decision-making!") 