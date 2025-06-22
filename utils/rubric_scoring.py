"""
Rubric scoring using OpenAI SDK to call Llama API, returning structured JSON results.
"""

import asyncio
import json
import re
from typing import Optional, Dict, Any

from llama_api_client import AsyncLlamaAPIClient

# Import config from the main package
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from pitchbot.audio_processor.config import AudioProcessingConfig, default_config


class RubricScorer:
    """Handles rubric-based scoring using Llama model with structured JSON output."""
    
    def __init__(self, config: Optional[AudioProcessingConfig] = None):
        """Initialize the rubric scorer with configuration."""
        self.config = config or default_config
        self.config.validate()
        
        # Initialize Llama API client
        self.client = AsyncLlamaAPIClient(
            api_key=self.config.llama_api_key
        )
    
    def _create_rubric_prompt(self, extracted_info: str) -> str:
        """
        Create a grounded evaluation prompt for scoring a project pitch based on predefined rubric criteria.
        Returns structured JSON format.
        """
        prompt = f"""You are an expert VC analyst assistant helping evaluate early-stage projects based on pitch content. The information below has been extracted from a live pitch presentation and demo. Your task is to assign scores across four specific judging criteria, based solely on this information.

For each criterion:
- Provide a score out of 100
- Offer a clear, concise justification grounded in the provided content
- Do not make assumptions beyond the given information

Rubric Criteria:

1. **Impact**  
   - What is the project's long-term potential for success, growth, and impact?  
   - Does it align with one of the problem statements listed above?  
   - Is the project useful, and for whom?

2. **Demo**  
   - How well has the team implemented the idea?  
   - Does the demo function as intended?

3. **Creativity**  
   - Is the concept of the project innovative or novel?  
   - Is the implementation or demo uniquely executed?

4. **Pitch**  
   - How effectively does the team communicate and present their project?  
   - Was the value proposition clear and compelling?

Only use the information provided below to score. Do not fill in gaps or infer missing details.

---
**Extracted Information:**  
\"\"\"{extracted_info}\"\"\"

---

You must respond with a valid JSON object in exactly this format:

{{
  "impact": {{
    "score": [number between 0-100],
    "justification": "[detailed justification based on the content]"
  }},
  "demo": {{
    "score": [number between 0-100],
    "justification": "[detailed justification based on the content]"
  }},
  "creativity": {{
    "score": [number between 0-100],
    "justification": "[detailed justification based on the content]"
  }},
  "pitch": {{
    "score": [number between 0-100],
    "justification": "[detailed justification based on the content]"
  }}
}}

Ensure the response is valid JSON with lowercase keys and proper formatting.
"""
        return prompt
    
    def _parse_scoring_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse the LLM response and extract scoring information into structured format.
        
        Args:
            response_text: Raw response from the LLM
            
        Returns:
            Dictionary with scoring results
        """
        try:
            # Try to parse as JSON first
            if response_text.strip().startswith('{'):
                return json.loads(response_text.strip())
            
            # Extract JSON from response if it's wrapped in other text
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            
            # Fallback: Parse the structured text format manually
            criteria = ['impact', 'demo', 'creativity', 'pitch']
            results = {}
            
            for criterion in criteria:
                # Look for the criterion pattern
                pattern = rf'\*\*{criterion.title()}\*\*:?\s*(\d+)/100\s*\*?[Jj]ustification:?\*?\s*(.+?)(?=\*\*|\Z)'
                match = re.search(pattern, response_text, re.IGNORECASE | re.DOTALL)
                
                if match:
                    score = int(match.group(1))
                    justification = match.group(2).strip()
                    results[criterion.lower()] = {
                        "score": score,
                        "justification": justification
                    }
                else:
                    # Default fallback if parsing fails
                    results[criterion.lower()] = {
                        "score": 0,
                        "justification": f"Could not parse {criterion} scoring from response"
                    }
            
            return results
            
        except Exception as e:
            # Return error structure if all parsing fails
            return {
                "impact": {"score": 0, "justification": f"Parsing error: {str(e)}"},
                "demo": {"score": 0, "justification": f"Parsing error: {str(e)}"},
                "creativity": {"score": 0, "justification": f"Parsing error: {str(e)}"},
                "pitch": {"score": 0, "justification": f"Parsing error: {str(e)}"}
            }
    
    async def score(self, extracted_info: str) -> Dict[str, Any]:
        """
        Score the given extracted information using rubric-based evaluation.
        
        Args:
            extracted_info: Extracted information to score (transcribed text, summary, etc.)
            
        Returns:
            Dictionary containing structured rubric scoring results
        """
        if not extracted_info.strip():
            raise ValueError("Input extracted_info is empty")
        
        prompt = self._create_rubric_prompt(extracted_info)
        
        try:
            response = await self.client.chat.completions.create(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                model=self.config.llama_model
            )
            
            # Extract the text from the response (Llama API format)
            scoring_text = response.completion_message.content.text.strip()
            
            # Parse into structured format
            scoring_result = self._parse_scoring_response(scoring_text)
            
            return scoring_result
            
        except Exception as e:
            raise RuntimeError(f"Rubric scoring failed: {str(e)}") from e
    
    async def score_legacy_format(self, extracted_info: str) -> str:
        """
        Score the given extracted information and return in legacy text format.
        
        Args:
            extracted_info: Extracted information to score
            
        Returns:
            Legacy text format scoring result
        """
        structured_result = await self.score(extracted_info)
        
        # Convert back to legacy format
        legacy_lines = []
        for criterion in ['impact', 'demo', 'creativity', 'pitch']:
            data = structured_result.get(criterion, {})
            score = data.get('score', 0)
            justification = data.get('justification', 'No justification available')
            
            legacy_lines.append(f"**{criterion.title()}**: {score}/100")
            legacy_lines.append(f"*Justification:* {justification}")
            legacy_lines.append("")  # Empty line for spacing
        
        return "\n".join(legacy_lines)
    
    def update_rubric_template(self, custom_rubric_template: str):
        """
        Update the rubric template for customization.
        
        Args:
            custom_rubric_template: Custom rubric template with {extracted_info} placeholder
        """
        def _custom_rubric(extracted_info: str) -> str:
            return custom_rubric_template.format(extracted_info=extracted_info)
        
        self._create_rubric_prompt = _custom_rubric 