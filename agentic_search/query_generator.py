"""
Generate search queries from an idea summary using a Llama model.
"""

import asyncio
import json
import os
from typing import Optional, List

import httpx
from llama_api_client import AsyncLlamaAPIClient

# We will now import the whole config module to access the model name
from . import config


class SearchQueryGenerator:
    """Handles generation of search queries using a Llama model."""
    
    def __init__(self):
        """Initialize the generator with configuration."""
        api_key = os.getenv("LLAMA_API_KEY")
        if not api_key:
            raise ValueError("LLAMA_API_KEY environment variable not set.")

        self.client = AsyncLlamaAPIClient(
            api_key=api_key,
        )
        # We will use the model from the config file.
        self.model = config.default_config.llama_model
    
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

    def update_prompt_template(self, custom_prompt_template: str):
        """
        Update the prompt template for customization.
        
        Args:
            custom_prompt_template: Custom prompt template with {idea_summary} placeholder
        """
        def _custom_prompt(idea_summary: str) -> str:
            return custom_prompt_template.format(idea_summary=idea_summary)
        
        self._create_query_generation_prompt = _custom_prompt 