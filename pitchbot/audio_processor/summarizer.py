"""
Text summarization using Llama-4-Maverick-17B-128E-Instruct-FP8 model.
"""

import asyncio
from typing import Optional

import httpx
from llama_api_client import AsyncLlamaAPIClient

from .config import AudioProcessingConfig, default_config


class TextSummarizer:
    """Handles text summarization using Llama model."""
    
    def __init__(self, config: Optional[AudioProcessingConfig] = None):
        """Initialize the summarizer with configuration."""
        self.config = config or default_config
        self.config.validate()
        
        self.client = AsyncLlamaAPIClient(
            api_key=self.config.llama_api_key,
            base_url=self.config.llama_base_url
        )
    
    def _create_summary_prompt(self, transcribed_text: str) -> str:
        """
        Create a focused and grounded prompt for summarizing a live pitch presentation.
        """
        prompt = f"""You are an expert analyst specializing in summarizing startup and project pitch presentations. The following is a transcribed recording of a live pitch session.

    Your task is to generate a structured summary that strictly reflects what was actually said—without making any assumptions or adding external knowledge. Do not hallucinate or infer intent unless it is clearly stated.

    Please extract and organize the summary under the following headings:
    - **Idea Summary**: What is the core idea or product being pitched?
    - **Problem Being Solved**: What pain point or market gap is the speaker addressing?
    - **Proposed Solution**: How does the idea solve the problem?
    - **Target Users / Market**: Who is this idea for?
    - **Differentiation**: What makes this idea unique or better than existing alternatives?
    - **Current Progress**: Any mention of prototypes, demos, or current status
    - **Next Steps / Ask**: Any specific requests, action items, or future plans mentioned

    Only use the information provided in the transcript. If a section cannot be confidently filled, state "Not mentioned."
    If any clearly stated, relevant information from the transcript does not fit neatly into the sections above, include it at the end under a heading called **Additional Noteworthy Points**. Otherwise, omit it.

    Transcribed pitch:
    \"\"\"{transcribed_text}\"\"\"
    """
        return prompt

    
    async def summarize(self, text: str) -> str:
        """
        Summarize the given text using Llama model.
        
        Args:
            text: Text to summarize (usually transcribed audio)
            
        Returns:
            Summary of the text
        """
        if not text.strip():
            raise ValueError("Input text is empty")
        
        prompt = self._create_summary_prompt(text)
        
        try:
            response = await self.client.chat.completions.create(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                model=self.config.llama_model
            )
            
            # Extract the text from the response structure
            # Based on the actual response: response.completion_message.content.text
            summary = response.completion_message.content.text.strip()
            return summary
            
        except Exception as e:
            raise RuntimeError(f"Summarization failed: {str(e)}") from e
    
    def update_prompt_template(self, custom_prompt_template: str):
        """
        Update the prompt template for customization.
        
        Args:
            custom_prompt_template: Custom prompt template with {transcribed_text} placeholder
        """
        def _custom_prompt(transcribed_text: str) -> str:
            return custom_prompt_template.format(transcribed_text=transcribed_text)
        
        self._create_summary_prompt = _custom_prompt 