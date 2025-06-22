"""
Text Processor using Llama API for text analysis and processing.
"""

import base64
import io
import logging
import os
import time
from typing import Any, Dict, List, Optional, Union

# Load environment variables from .env file in project root
try:
    from dotenv import load_dotenv
    from pathlib import Path
    load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / ".env")
except ImportError:
    pass

# Optional PIL import for image processing
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None

try:
    from llama_api_client import LlamaAPIClient
    from llama_api_client.resources.chat.completions import CompletionsResource
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False

logger = logging.getLogger(__name__)


class TextProcessor:
    """
    Text Processor using Llama API for various text processing tasks.
    
    Features:
    - Smart text chunking for token limits
    - Multiple processing modes (summarization, key points, Q&A)
    - Error handling with retries
    - Graceful degradation to raw text
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "Llama-4-Maverick-17B-128E-Instruct-FP8"):
        """
        Initialize the text processor.
        
        Args:
            api_key: Llama API key (defaults to LLAMA_API_KEY env var)
            model: Llama model to use
        """
        if not LLAMA_AVAILABLE:
            raise ImportError("llama-api-client not available. Please install it first.")
        
        self.api_key = api_key or os.getenv("LLAMA_API_KEY")
        if not self.api_key:
            raise ValueError("Llama API key not provided. Set LLAMA_API_KEY environment variable.")
        
        self.model = model
        self.client = LlamaAPIClient()
        self.completions = CompletionsResource(self.client)
        self.max_tokens = 100000  # Conservative token limit
        self.chunk_overlap = 200  # Overlap between chunks
        
        logger.info(f"Text Processor initialized with model: {model}")
    
    def summarize_text(self, text: str, summary_type: str = "executive") -> str:
        """
        Summarize text using Llama API.
        
        Args:
            text: Text to summarize
            summary_type: Type of summary ("executive", "detailed", "bullet")
            
        Returns:
            Generated summary
        """
        if not text.strip():
            return "No text to summarize."
        
        prompts = {
            "executive": "Provide a concise executive summary of the following text in 9-10 sentences:",
            "detailed": "Provide a detailed summary of the following text, covering all key points:",
            "bullet": "Extract the key points from the following text as bullet points:"
        }
        
        prompt = prompts.get(summary_type, prompts["executive"])
        
        try:
            response = self._call_llama_api(f"{prompt}\n\n{text}")
            return response.strip()
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return f"Summarization failed: {str(e)}"
    
    def _image_to_base64(self, image_path: str, max_size: int = 600) -> Optional[str]:
        """
        Convert image to base64 format with optional resizing.
        
        Args:
            image_path: Path to the image file
            max_size: Maximum dimension for resizing (maintains aspect ratio)
            
        Returns:
            Base64 encoded image string or None if failed
        """
        if not PIL_AVAILABLE:
            logger.warning("PIL/Pillow not available, cannot process images")
            return None
            
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if too large (reduce max_size to avoid token limits)
                if max(img.size) > max_size:
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                    logger.info(f"Resized image from {img.size} to fit within {max_size}x{max_size}")
                
                # Convert to base64 with compression
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=70, optimize=True)  # Reduced quality for smaller size
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                # Check size and warn if too large
                size_mb = len(img_base64) / (1024 * 1024)
                if size_mb > 1:  # If larger than 1MB
                    logger.warning(f"Image {image_path} is {size_mb:.2f}MB, may cause API issues")
                
                logger.info(f"Successfully converted image {image_path} to base64 ({size_mb:.2f}MB)")
                return f"data:image/jpeg;base64,{img_base64}"
                
        except Exception as e:
            logger.warning(f"Failed to convert image {image_path} to base64: {e}")
            return None

    def extract_key_points(self, text: str, images: List[str] = None) -> List[str]:
        """
        Extract key points from text and images with focus on business-relevant information.
        
        Args:
            text: Text to analyze
            images: List of image file paths to analyze
            
        Returns:
            List of key points organized by category
        """
        if not text.strip() and not images:
            return []
        
        # Refined prompt for comprehensive analysis of text and images
        prompt = """You are an expert business analyst. Given the following PDF content, extract as many actionable business key points as possible, including insights from both text and images (provided as base64-encoded JPEGs).

For images, analyze and describe any charts, graphs, tables, UI/UX elements, or visual data. If the image contains text, extract and summarize it. If the image is a graph or chart, describe the axes, trends, and any notable data points.

Focus especially on these critical business areas:

1. **Product Market Fit & Target Audience**:
   - Target market definition, size, and demographics
   - Customer pain points, needs, and use cases
   - Product positioning and unique value proposition
   - Market validation evidence and customer feedback
   - User personas and customer segments

2. **Visual Content Analysis**:
   - Charts, graphs, and data visualizations (extract specific metrics and trends)
   - Images, diagrams, and infographics (describe key elements and insights)
   - Tables with key metrics, comparisons, or financial data
   - UI/UX elements, product screenshots, or mockups
   - Brand elements, logos, and visual identity
   - Any visual content that supports the business case or product story

3. **Monetization & Financial Viability**:
   - Revenue models, pricing strategies, and pricing tiers
   - Financial projections, forecasts, and key metrics
   - Cost structure, unit economics, and profitability analysis
   - Funding requirements, use of funds, and investment needs
   - Break-even analysis, margins, and financial sustainability
   - Revenue streams and monetization channels

4. **Data & Analytics Insights**:
   - Key performance indicators (KPIs) and success metrics
   - Market data, statistics, and industry benchmarks
   - User metrics, growth data, and engagement statistics
   - Competitive analysis data and market positioning
   - Industry trends, market size, and growth projections
   - Data-driven insights and evidence

5. **Competitive Landscape & Positioning**:
   - Direct and indirect competitors (names, features, positioning)
   - Competitive advantages, differentiators, and unique features
   - Market share information and competitive positioning
   - Barriers to entry and competitive moats
   - SWOT analysis and competitive threats
   - Market gaps and opportunities

6. **Business Model & Go-to-Market Strategy**:
   - Go-to-market strategy and customer acquisition approach
   - Sales and marketing strategies, channels, and tactics
   - Partnerships, collaborations, and ecosystem relationships
   - Risk factors, challenges, and mitigation strategies
   - Business model canvas elements
   - Scalability and growth strategies

7. **Technical & Product Insights**:
   - Technology stack, architecture, and technical capabilities
   - Product features, functionality, and roadmap
   - Technical differentiators and innovation
   - Development timeline and milestones
   - Technical challenges and solutions

Please provide specific, actionable insights with concrete details, numbers, and examples from each category. For visual content, describe what you see and extract any data, metrics, or insights shown in charts, graphs, or images.

Format your response as a structured list with clear categorization. Use bullet points or numbered lists for each category."""

        try:
            # Prepare content for API call
            content_parts = []
            
            # Add text content
            if text.strip():
                content_parts.append(f"TEXT CONTENT:\n{text}")
            
            # Add image content as base64
            if images:
                for i, image_path in enumerate(images):
                    base64_image = self._image_to_base64(image_path)
                    if base64_image:
                        content_parts.append(f"IMAGE {i+1} (Base64):\n{base64_image}")
                        logger.info(f"Added image {i+1} to analysis")
                    else:
                        logger.warning(f"Failed to convert image {i+1} to base64")
            
            # Combine all content
            full_content = "\n\n".join(content_parts)
            
            # Make API call
            response = self._call_llama_api(f"{prompt}\n\n{full_content}")
            
            # Parse the response and organize by categories
            points = []
            current_category = "General"
            
            for line in response.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                # Check for category headers
                category_keywords = [
                    'product market fit', 'target audience', 'visual content', 'visual analysis',
                    'monetization', 'financial', 'data & analytics', 'data analytics', 'analytics insights',
                    'competitive landscape', 'competitive positioning', 'business model', 'go-to-market',
                    'technical', 'product insights'
                ]
                
                if any(keyword in line.lower() for keyword in category_keywords):
                    current_category = line.strip('*#1234567890. ')
                    continue
                
                # Extract bullet points and numbered items
                if line and (line[0].isdigit() or line.startswith('•') or line.startswith('-') or line.startswith('*')):
                    # Remove numbering/bullets and clean up
                    point = line.lstrip('0123456789.-•* ').strip()
                    if point:
                        points.append(f"[{current_category}] {point}")
                elif line and len(line) > 20:  # Likely a key point even without bullet
                    points.append(f"[{current_category}] {line}")
            
            # If no structured points found, return the raw response
            if not points:
                return [response.strip()]
            
            return points
            
        except Exception as e:
            logger.error(f"Key point extraction failed: {e}")
            return [f"Key point extraction failed: {str(e)}"]
    
    def extract_key_points_json(self, text: str, images: List[str] = None) -> Dict[str, List[str]]:
        """
        Extract key points from text and images with JSON-structured output.
        
        Args:
            text: Text to analyze
            images: List of image file paths to analyze
            
        Returns:
            Dictionary with categories as keys and lists of key points as values
        """
        if not text.strip() and not images:
            return {}
        
        # JSON-structured prompt
        prompt = """You are an expert business analyst. Analyze the following PDF content and extract key business insights from both text and images.

For images, carefully analyze and extract:
1. Any text content visible in the images (headlines, labels, numbers, descriptions)
2. Charts and graphs - describe the data, trends, axes, and key metrics shown
3. UI/UX elements - describe buttons, menus, interfaces, and user interactions
4. Visual data - tables, infographics, diagrams, and their key information
5. Brand elements - logos, colors, design patterns, and visual identity
6. Screenshots - describe what's being shown, features, and functionality

When analyzing images, be specific about:
- Exact text content you can read
- Numbers, percentages, and metrics shown
- Chart types and what they represent
- UI elements and their purpose
- Visual hierarchy and layout
- Any business-relevant information displayed

Return your analysis as a valid JSON object with the following structure:
{
  "product_market_fit": ["key point 1", "key point 2", ...],
  "visual_content": ["key point 1", "key point 2", ...],
  "monetization": ["key point 1", "key point 2", ...],
  "data_analytics": ["key point 1", "key point 2", ...],
  "competitive_landscape": ["key point 1", "key point 2", ...],
  "business_model": ["key point 1", "key point 2", ...],
  "technical_insights": ["key point 1", "key point 2", ...]
}

Focus on:
- Product Market Fit: target market, customer needs, positioning, validation
- Visual Content: charts, graphs, images, UI/UX, brand elements, text content from images
- Monetization: revenue models, pricing, financial projections, funding
- Data Analytics: KPIs, metrics, market data, user statistics
- Competitive Landscape: competitors, advantages, market positioning
- Business Model: go-to-market, strategy, partnerships, risks
- Technical Insights: technology, features, architecture, roadmap

Ensure the response is valid JSON with no additional text before or after."""

        try:
            # Prepare content for API call
            content_parts = []
            
            # Add text content
            if text.strip():
                content_parts.append(f"TEXT CONTENT:\n{text}")
                logger.info(f"Added text content ({len(text)} characters)")
            
            # Add image content as base64
            if images:
                logger.info(f"Processing {len(images)} images...")
                for i, image_path in enumerate(images):
                    base64_image = self._image_to_base64(image_path)
                    if base64_image:
                        content_parts.append(f"IMAGE {i+1} (Base64):\n{base64_image}")
                        logger.info(f"Added image {i+1} to JSON analysis")
                    else:
                        logger.warning(f"Failed to convert image {i+1} to base64")
            
            # Combine all content
            full_content = "\n\n".join(content_parts)
            logger.info(f"Total content length: {len(full_content)} characters")
            
            # Make API call
            logger.info("Making API call to Llama...")
            response = self._call_llama_api(f"{prompt}\n\n{full_content}")
            logger.info(f"API response received: {len(response)} characters")
            
            if not response.strip():
                logger.warning("Empty response from API, falling back to text-only analysis")
                # Fallback to text-only analysis if API returns empty
                if text.strip():
                    return self._fallback_text_analysis(text)
                else:
                    return {"General": ["No content available for analysis"]}
            
            # Try to parse JSON response
            try:
                import json
                # Clean the response to extract JSON
                response_text = response.strip()
                
                # Find JSON object in response
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    result = json.loads(json_str)
                    
                    # Convert to standard format
                    organized_points = {}
                    for category, points in result.items():
                        if isinstance(points, list):
                            organized_points[category.replace('_', ' ').title()] = points
                        else:
                            organized_points[category.replace('_', ' ').title()] = [str(points)]
                    
                    logger.info(f"Successfully parsed JSON response with {len(organized_points)} categories")
                    return organized_points
                else:
                    logger.warning("No JSON object found in response, falling back to text-only analysis")
                    if text.strip():
                        return self._fallback_text_analysis(text)
                    else:
                        return {"General": [response_text]}
                    
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON response: {e}")
                logger.warning(f"Response was: {response_text[:200]}...")
                if text.strip():
                    return self._fallback_text_analysis(text)
                else:
                    return {"General": [response_text]}
            
        except Exception as e:
            logger.error(f"JSON key point extraction failed: {e}")
            if text.strip():
                return self._fallback_text_analysis(text)
            else:
                return {"Error": [f"Key point extraction failed: {str(e)}"]}
    
    def _fallback_text_analysis(self, text: str) -> Dict[str, List[str]]:
        """
        Fallback method for text-only analysis when image processing fails.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with categories as keys and lists of key points as values
        """
        logger.info("Using fallback text-only analysis")
        
        # Simplified prompt for text-only analysis
        prompt = """You are an expert business analyst. Extract key business insights from the following text.

Analyze the text for:
- Product features, benefits, and value propositions
- Target market and customer segments
- Revenue models and monetization strategies
- Market size, growth potential, and competitive landscape
- Technical capabilities and architecture
- Business model and go-to-market strategy
- Key metrics, KPIs, and performance indicators
- Risks, challenges, and opportunities

Return your analysis as a valid JSON object with the following structure:
{
  "product_market_fit": ["key point 1", "key point 2", ...],
  "monetization": ["key point 1", "key point 2", ...],
  "data_analytics": ["key point 1", "key point 2", ...],
  "competitive_landscape": ["key point 1", "key point 2", ...],
  "business_model": ["key point 1", "key point 2", ...],
  "technical_insights": ["key point 1", "key point 2", ...]
}

Focus on extracting actionable business insights from the text content.

Ensure the response is valid JSON with no additional text before or after."""

        try:
            response = self._call_llama_api(f"{prompt}\n\n{text}")
            
            if not response.strip():
                return {"General": ["No insights could be extracted from the text"]}
            
            # Parse JSON response
            import json
            response_text = response.strip()
            
            # Find JSON object in response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                result = json.loads(json_str)
                
                # Convert to standard format
                organized_points = {}
                for category, points in result.items():
                    if isinstance(points, list):
                        organized_points[category.replace('_', ' ').title()] = points
                    else:
                        organized_points[category.replace('_', ' ').title()] = [str(points)]
                
                return organized_points
            else:
                return {"General": [response_text]}
                
        except Exception as e:
            logger.error(f"Fallback text analysis failed: {e}")
            return {"General": ["Analysis failed due to technical issues"]}
    
    def answer_questions(self, text: str, questions: List[str]) -> Dict[str, str]:
        """
        Answer specific questions about the text.
        
        Args:
            text: Text to analyze
            questions: List of questions to answer
            
        Returns:
            Dictionary mapping questions to answers
        """
        if not text.strip() or not questions:
            return {}
        
        results = {}
        
        for question in questions:
            prompt = f"""Based on the following text, answer this question: {question}
            
            Text:
            {text}
            
            Answer:"""
            
            try:
                response = self._call_llama_api(prompt)
                results[question] = response.strip()
            except Exception as e:
                logger.error(f"Question answering failed for '{question}': {e}")
                results[question] = f"Failed to answer: {str(e)}"
        
        return results
    
    def process_custom(self, text: str, prompt: str) -> str:
        """
        Process text with a custom prompt.
        
        Args:
            text: Text to process
            prompt: Custom prompt to use
            
        Returns:
            Processed result
        """
        if not text.strip():
            return "No text to process."
        
        full_prompt = f"{prompt}\n\n{text}"
        
        try:
            response = self._call_llama_api(full_prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"Custom processing failed: {e}")
            return f"Processing failed: {str(e)}"
    
    def clean_and_structure(self, text: str) -> Dict[str, Any]:
        """
        Clean and structure text for better processing.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Dictionary with cleaned text and structure information
        """
        if not text.strip():
            return {
                "cleaned_text": "",
                "word_count": 0,
                "sentence_count": 0,
                "paragraph_count": 0,
                "structure": {}
            }
        
        # Basic cleaning
        cleaned_text = text.strip()
        
        # Count basic metrics
        words = cleaned_text.split()
        sentences = [s.strip() for s in cleaned_text.split('.') if s.strip()]
        paragraphs = [p.strip() for p in cleaned_text.split('\n\n') if p.strip()]
        
        # Analyze structure
        structure = {
            "has_numbers": any(char.isdigit() for char in cleaned_text),
            "has_dates": self._has_dates(cleaned_text),
            "has_emails": self._has_emails(cleaned_text),
            "has_urls": self._has_urls(cleaned_text),
            "avg_sentence_length": len(words) / len(sentences) if sentences else 0,
            "avg_paragraph_length": len(sentences) / len(paragraphs) if paragraphs else 0,
        }
        
        return {
            "cleaned_text": cleaned_text,
            "word_count": len(words),
            "sentence_count": len(sentences),
            "paragraph_count": len(paragraphs),
            "structure": structure
        }
    
    def _call_llama_api(self, prompt: str, max_retries: int = 3) -> str:
        """
        Call Llama API with retry logic.
        
        Args:
            prompt: Prompt to send
            max_retries: Maximum number of retries
            
        Returns:
            API response
        """
        for attempt in range(max_retries):
            try:
                # Chunk text if it's too long
                if len(prompt) > self.max_tokens * 4:  # Rough character estimate
                    chunks = self._chunk_text(prompt)
                    responses = []
                    
                    for chunk in chunks:
                        response = self._make_api_call(chunk)
                        responses.append(response)
                    
                    return "\n\n".join(responses)
                else:
                    return self._make_api_call(prompt)
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                logger.warning(f"API call failed (attempt {attempt + 1}): {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
    
    def _make_api_call(self, prompt: str) -> str:
        """Make a single API call to Llama."""
        try:
            response = self.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=self.max_tokens,
                temperature=0.1,  # Low temperature for consistent results
                top_p=0.9,
                stream=False
            )
            
            # Extract content from the response
            if hasattr(response, 'completion_message') and response.completion_message:
                if hasattr(response.completion_message, 'content'):
                    content = response.completion_message.content
                    if hasattr(content, 'text'):
                        return content.text.strip()
                    elif isinstance(content, str):
                        return content.strip()
            
            # Fallback to string representation
            return str(response)
                
        except Exception as e:
            logger.error(f"API call failed: {e}")
            raise
    
    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks for processing.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1  # +1 for space
            
            if current_length + word_length > self.max_tokens * 4:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    # Keep some overlap
                    overlap_words = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else current_chunk
                    current_chunk = overlap_words
                    current_length = sum(len(w) + 1 for w in overlap_words)
            
            current_chunk.append(word)
            current_length += word_length
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def _has_dates(self, text: str) -> bool:
        """Check if text contains date patterns."""
        import re
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{2,4}',
            r'\d{1,2}-\d{1,2}-\d{2,4}',
            r'\d{4}-\d{2}-\d{2}',
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b'
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _has_emails(self, text: str) -> bool:
        """Check if text contains email addresses."""
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return bool(re.search(email_pattern, text))
    
    def _has_urls(self, text: str) -> bool:
        """Check if text contains URLs."""
        import re
        url_pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?'
        return bool(re.search(url_pattern, text)) 