"""
Rubric scoring using Llama-4-Maverick-17B-128E-Instruct-FP8 model.
"""

import asyncio
from typing import Optional

import httpx
from llama_api_client import AsyncLlamaAPIClient

# Import config from the main package
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from pitchbot.audio_processor.config import AudioProcessingConfig, default_config


class RubricScorer:
    """Handles rubric-based scoring using Llama model."""
    
    def __init__(self, config: Optional[AudioProcessingConfig] = None):
        """Initialize the rubric scorer with configuration."""
        self.config = config or default_config
        self.config.validate()
        
        self.client = AsyncLlamaAPIClient(
            api_key=self.config.llama_api_key,
            base_url=self.config.llama_base_url
        )
    
    def _create_rubric_prompt(self, extracted_info: str) -> str:
        """
        Create a grounded evaluation prompt for scoring a project pitch based on predefined rubric criteria.
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
Now provide the following format:

**Impact**: [Score]/100  
*Justification:* ...

**Demo**: [Score]/100  
*Justification:* ...

**Creativity**: [Score]/100  
*Justification:* ...

**Pitch**: [Score]/100  
*Justification:* ...
"""
        return prompt
    
    async def score(self, extracted_info: str) -> str:
        """
        Score the given extracted information using rubric-based evaluation.
        
        Args:
            extracted_info: Extracted information to score (transcribed text, summary, etc.)
            
        Returns:
            Rubric-based scoring result
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
            
            # Extract the text from the response structure
            # Based on the actual response: response.completion_message.content.text
            scoring_result = response.completion_message.content.text.strip()
            return scoring_result
            
        except Exception as e:
            raise RuntimeError(f"Rubric scoring failed: {str(e)}") from e
    
    def update_rubric_template(self, custom_rubric_template: str):
        """
        Update the rubric template for customization.
        
        Args:
            custom_rubric_template: Custom rubric template with {extracted_info} placeholder
        """
        def _custom_rubric(extracted_info: str) -> str:
            return custom_rubric_template.format(extracted_info=extracted_info)
        
        self._create_rubric_prompt = _custom_rubric 