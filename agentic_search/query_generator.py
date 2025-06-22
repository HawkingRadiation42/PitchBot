"""
Generate search queries from an idea summary using a Llama model.
Enhanced with multi-level reference extraction capabilities.
"""

import asyncio
import json
import os
from typing import Optional, List, Dict, Any

import httpx
from llama_api_client import AsyncLlamaAPIClient

# We will now import the whole config module to access the model name
from . import config
from .reference_extractor import ReferenceExtractor, enhance_search_with_references


class SearchQueryGenerator:
    """Handles generation of search queries using a Llama model with reference extraction."""
    
    def __init__(self, enable_reference_extraction: bool = False, max_depth: int = 2, max_pages_per_level: int = 3):
        """
        Initialize the generator with configuration.
        
        Args:
            enable_reference_extraction: Whether to enable multi-level reference extraction
            max_depth: Maximum depth for reference extraction (if enabled)
            max_pages_per_level: Maximum pages to process per level (if enabled)
        """
        api_key = os.getenv("LLAMA_API_KEY")
        if not api_key:
            raise ValueError("LLAMA_API_KEY environment variable not set.")

        self.client = AsyncLlamaAPIClient(
            api_key=api_key,
        )
        # We will use the model from the config file.
        self.model = config.default_config.llama_model
        
        # Reference extraction configuration
        self.enable_reference_extraction = enable_reference_extraction
        self.reference_extractor = None
        if enable_reference_extraction:
            self.reference_extractor = ReferenceExtractor(
                max_depth=max_depth,
                max_pages_per_level=max_pages_per_level
            )
    
    def _create_query_generation_prompt(self, idea_summary: str) -> str:
        """
        Create a prompt for generating strategic search queries.
        """
        prompt = f"""You are a world-class market research analyst. Your task is to generate targeted search queries to research a startup idea based on its summary. These queries should uncover crucial information about the market, competitors, and the idea's novelty.

Your queries should investigate the following areas:
1.  **Direct Competitors**: Who is building a similar product or service?
2.  **Indirect Competitors**: Who is solving the same core problem with a different approach?
3.  **Market Size and Trends**: What is the total addressable market (TAM), and what are the growth trends?
4.  **Uniqueness & Differentiation**: Are there patents, research papers, or articles discussing this?
5.  **Customer Pain Points**: What are people complaining about with existing solutions?
6.  **Technological Feasibility**: Are there any technical hurdles or required innovations?

Here is the idea summary:
\"\"\"{idea_summary}\"\"\"

From the areas above, generate the top 10 most important search queries that an investor should use to evaluate this idea's potential. The output must be a JSON formatted list of exactly 10 strings.

Example format:
["most important query 1", "most important query 2", ..., "most important query 10"]
"""
        return prompt

    def _create_reference_based_query_prompt(self, idea_summary: str, reference_content: str) -> str:
        """
        Create a prompt for generating additional queries based on extracted references.
        """
        prompt = f"""You are a market research analyst. Based on the startup idea and the reference content extracted from web pages, generate additional targeted search queries that will help uncover deeper insights.

Startup Idea:
\"\"\"{idea_summary}\"\"\"

Reference Content Summary:
\"\"\"{reference_content[:2000]}...\"\"\"

Based on the insights from the reference content, generate 5 additional strategic search queries that will help investigate:
- Gaps or opportunities mentioned in the reference content
- Specific competitors or companies mentioned
- Technical details or implementation approaches
- Market segments or use cases identified
- Regulatory or compliance considerations

Output must be a JSON formatted list of exactly 5 strings.

Example format:
["specific query based on references 1", "specific query based on references 2", ..., "specific query based on references 5"]
"""
        return prompt

    async def generate_queries(self, idea_summary: str) -> List[str]:
        """
        Generate search queries for the given idea summary.
        
        Args:
            idea_summary: A summary of the startup idea.
            
        Returns:
            A list of search queries.
        """
        if not idea_summary.strip():
            raise ValueError("Input idea summary is empty")
        
        prompt = self._create_query_generation_prompt(idea_summary)
        print(prompt)
        try:
            response = await self.client.chat.completions.create(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
            )
            
            content = response.completion_message.content.text
            queries = json.loads(content)
            
            if isinstance(queries, dict) and "queries" in queries:
                 return queries["queries"]
            elif isinstance(queries, list):
                return queries
            else:
                raise ValueError("The model did not return a valid list of queries in JSON format.")

        except json.JSONDecodeError:
            # The model might not return perfect JSON. We can try to extract from a code block.
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            try:
                queries = json.loads(content)
                if isinstance(queries, dict) and "queries" in queries:
                    return queries["queries"]
                elif isinstance(queries, list):
                    return queries
            except json.JSONDecodeError:
                raise RuntimeError(f"Failed to decode JSON from model response: {content}")

        except Exception as e:
            raise RuntimeError(f"Query generation failed: {str(e)}") from e

    async def generate_reference_based_queries(self, idea_summary: str, reference_data: Dict[str, Any]) -> List[str]:
        """
        Generate additional queries based on extracted reference content.
        
        Args:
            idea_summary: A summary of the startup idea
            reference_data: Data from reference extraction
            
        Returns:
            A list of additional search queries based on references
        """
        if not self.enable_reference_extraction:
            return []
        
        # Extract key content from reference data
        reference_content = self._summarize_reference_content(reference_data)
        
        if not reference_content.strip():
            return []
        
        prompt = self._create_reference_based_query_prompt(idea_summary, reference_content)
        
        try:
            response = await self.client.chat.completions.create(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
            )
            
            content = response.completion_message.content.text
            
            # Handle JSON parsing similar to generate_queries
            try:
                queries = json.loads(content)
            except json.JSONDecodeError:
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                queries = json.loads(content)
            
            if isinstance(queries, dict) and "queries" in queries:
                return queries["queries"]
            elif isinstance(queries, list):
                return queries
            else:
                return []
                
        except Exception as e:
            print(f"Warning: Reference-based query generation failed: {str(e)}")
            return []

    def _summarize_reference_content(self, reference_data: Dict[str, Any]) -> str:
        """
        Summarize reference content for query generation.
        
        Args:
            reference_data: Data from reference extraction
            
        Returns:
            Summarized content string
        """
        summary_parts = []
        
        # Extract key information from all pages
        for page in reference_data.get('all_pages', [])[:5]:  # Top 5 pages
            title = page.get('title', '')
            content = page.get('content', '')[:500]  # First 500 chars
            
            if title and content:
                summary_parts.append(f"Page: {title}\nContent: {content}")
        
        return "\n\n".join(summary_parts)

    async def enhance_search_results_with_references(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Enhance search results with multi-level reference extraction.
        
        Args:
            search_results: List of search results from BraveSearchClient
            
        Returns:
            Enhanced results with reference extraction data
        """
        if not self.enable_reference_extraction or not self.reference_extractor:
            return {
                'original_results': search_results,
                'reference_extraction': None,
                'enhancement_enabled': False
            }
        
        print(f"\n🔗 Enhancing {len(search_results)} search results with reference extraction...")
        
        try:
            enhanced_results = await self.reference_extractor.enhance_brave_search_results(search_results)
            enhanced_results['enhancement_enabled'] = True
            return enhanced_results
        except Exception as e:
            print(f"Warning: Reference extraction failed: {str(e)}")
            return {
                'original_results': search_results,
                'reference_extraction': None,
                'enhancement_enabled': False,
                'error': str(e)
            }

    async def generate_comprehensive_queries(self, idea_summary: str, initial_search_results: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Generate comprehensive queries including reference-based queries if enabled.
        
        Args:
            idea_summary: A summary of the startup idea
            initial_search_results: Optional initial search results to enhance with references
            
        Returns:
            Dictionary containing all generated queries and reference data
        """
        result = {
            'primary_queries': [],
            'reference_based_queries': [],
            'total_queries': 0,
            'reference_extraction_data': None
        }
        
        # Generate primary queries
        result['primary_queries'] = await self.generate_queries(idea_summary)
        
        # If reference extraction is enabled and we have search results, enhance them
        if self.enable_reference_extraction and initial_search_results:
            enhanced_results = await self.enhance_search_results_with_references(initial_search_results)
            result['reference_extraction_data'] = enhanced_results
            
            # Generate additional queries based on references
            if enhanced_results.get('reference_extraction'):
                reference_queries = await self.generate_reference_based_queries(
                    idea_summary, 
                    enhanced_results['reference_extraction']
                )
                result['reference_based_queries'] = reference_queries
        
        result['total_queries'] = len(result['primary_queries']) + len(result['reference_based_queries'])
        
        return result

    def update_prompt_template(self, custom_prompt_template: str):
        """
        Update the prompt template for customization.
        
        Args:
            custom_prompt_template: Custom prompt template with {idea_summary} placeholder
        """
        def _custom_prompt(idea_summary: str) -> str:
            return custom_prompt_template.format(idea_summary=idea_summary)
        
        self._create_query_generation_prompt = _custom_prompt 