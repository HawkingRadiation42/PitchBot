"""
Main entry point for PitchBot application.
"""

import sys
import asyncio
from typing import Optional, Union
import argparse
import json
import os
from datetime import datetime

import uvicorn
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
# Add LLAMA API client import
from llama_api_client import AsyncLlamaAPIClient

# Load environment variables from .env file in the root directory
load_dotenv()

# Import the processors
from .video_processor import process_video
from .pdf_processor import process_pdf
from .url_processor import process_url
from .company_url_processor import process_company_url

# Import agentic search components
from .agentic_search.enhanced_research_pipeline import EnhancedResearchPipeline

# Import rubric scoring
import sys
import re
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from utils.rubric_scoring import RubricScorer


class StartupResearcher:
    """Enhanced startup research with multi-level reference extraction."""
    
    def __init__(self, enable_reference_extraction: bool = True, max_depth: int = 2, max_pages_per_level: int = 5):
        """Initialize the enhanced research pipeline."""
        self.pipeline = EnhancedResearchPipeline(
            max_depth=max_depth,
            max_pages_per_level=max_pages_per_level
        )
        self.enable_reference_extraction = enable_reference_extraction
    
    async def conduct_research(self, idea_summary: str) -> dict:
        """
        Conduct comprehensive research using enhanced pipeline.
        
        Args:
            idea_summary: Summary of the startup idea
            
        Returns:
            Dictionary containing all research data and analysis in a compatible format
        """
        print("🔍 Starting Enhanced Agentic Market Research...")
        
        # Run the enhanced research pipeline
        results = await self.pipeline.run_comprehensive_research(
            idea_summary=idea_summary,
            enable_reference_extraction=self.enable_reference_extraction,
            max_search_results=10
        )
        
        # Convert enhanced results to the format expected by your FastAPI endpoint
        research_data = {
            "idea_summary": results["idea_summary"],
            "search_queries": results["search_queries"],
            "web_results": results["search_results"]["web_results"],
            "total_pages_analyzed": results["pipeline_summary"]["total_pages_analyzed"],
            "analysis": results["analysis"],
            # Additional enhanced data
            "enhanced_references": results.get("enhanced_references"),
            "pipeline_summary": results["pipeline_summary"]
        }
        
        return research_data


# --- LLAMA API Summarization Functions ---
class ModuleSummarizer:
    """Handles LLAMA API summarization for each module."""
    
    def __init__(self):
        """Initialize the LLAMA API client for summarization."""
        api_key = os.getenv("LLAMA_API_KEY")
        if not api_key:
            raise ValueError("LLAMA_API_KEY environment variable not set.")
        
        self.client = AsyncLlamaAPIClient(
            api_key=api_key,
        )
        self.model = "Llama-4-Maverick-17B-128E-Instruct-FP8"
    
    async def summarize_module_result(self, module_name: str, module_result: str) -> str:
        """
        Summarize a module's analysis result using LLAMA API.
        
        Args:
            module_name: Name of the module (e.g., "Video Analysis", "PDF Analysis")
            module_result: The raw analysis result from the module
            
        Returns:
            Summarized version of the module result
        """
        if not module_result or not module_result.strip():
            return "No content available for summarization."
        
        prompt = f"""You are an expert startup pitch analyst. Please provide a concise, professional summary of the following {module_name} results.

**Instructions:**
- Extract the most important insights and findings
- Highlight key strengths and potential concerns
- Keep the summary focused and actionable
- Use bullet points for clarity
- Limit to 300 words
- Write the summary directly do not say here is the summary or anything like that

**{module_name} Results to Summarize:**
{module_result}

**Summary:**"""

        try:
            response = await self.client.chat.completions.create(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                max_completion_tokens=200,
                temperature=0.3
            )
            
            summary = response.completion_message.content.text.strip()
            print("------here-------")
            
            return summary
            
        except Exception as e:
            print(f"❌ LLAMA summarization failed for {module_name}: {str(e)}")
            return f"Summarization failed: {str(e)}"


# Initialize the module summarizer
summarizer = None

async def get_summarizer():
    """Get or create the module summarizer instance."""
    global summarizer
    if summarizer is None:
        try:
            summarizer = ModuleSummarizer()
        except Exception as e:
            print(f"⚠️ Could not initialize LLAMA summarizer: {e}")
            return None
    return summarizer


async def add_module_summary(module_name: str, module_result: str) -> Optional[str]:
    """
    Add LLAMA API summary to a module result.
    
    Args:
        module_name: Name of the module for summarization
        module_result: The module's analysis result
        
    Returns:
        Summary string or None if summarization fails
    """
    try:
        print(f"🤖 Generating LLAMA summary for {module_name}...")
        summarizer_instance = await get_summarizer()
        
        if summarizer_instance is None:
            print(f"⚠️ Summarizer not available for {module_name}")
            return None
            
        summary = await summarizer_instance.summarize_module_result(module_name, module_result)
        print(f"✅ {module_name} LLAMA summary completed!")
        return summary
        
    except Exception as e:
        print(f"❌ {module_name} LLAMA summarization failed: {str(e)}")
        return None


# --- Rubric Scoring Functions ---
async def add_rubric_scores(content: str, module_name: str) -> dict:
    """
    Score content using rubric scorer and return structured results.
    
    Args:
        content: The content to score
        module_name: Name of the module for logging
        
    Returns:
        Dictionary containing rubric scores or None if scoring fails
    """
    try:
        print(f"🎯 Scoring {module_name} with rubric system...")
        scorer = RubricScorer()
        rubric_scores = await scorer.score(content)
        
        # Calculate average score for summary
        total_score = sum(rubric_scores[key]['score'] for key in rubric_scores if 'score' in rubric_scores[key])
        avg_score = total_score / 4 if len(rubric_scores) >= 4 else 0
        
        print(f"✅ {module_name} rubric scoring completed! Average: {avg_score:.1f}/100")
        return rubric_scores
        
    except Exception as e:
        print(f"❌ {module_name} rubric scoring failed: {str(e)}")
        return {
            "impact": {"score": 0, "justification": f"Scoring failed: {str(e)}"},
            "demo": {"score": 0, "justification": f"Scoring failed: {str(e)}"},
            "creativity": {"score": 0, "justification": f"Scoring failed: {str(e)}"},
            "pitch": {"score": 0, "justification": f"Scoring failed: {str(e)}"}
        }


# --- Text Formatting Functions ---
def format_llama_summary(summary_text: str) -> str:
    """
    Format llama summary text by converting markdown-style formatting to clean, readable text.
    Converts to HTML with proper structure for frontend display.
    
    Args:
        summary_text: The raw llama summary text with markdown formatting
        
    Returns:
        HTML formatted text with proper structure
    """
    if not summary_text:
        return ""
    
    try:
        # Start with clean text
        formatted_text = summary_text.strip()
        
        # Convert markdown bold headers to HTML headers
        formatted_text = re.sub(r'\*\*([^*]+):\*\*', r'<h4>\1:</h4>', formatted_text)
        
        # Convert bullet points to proper HTML list items
        # First, identify bullet point sections
        lines = formatted_text.split('\n')
        html_lines = []
        in_list = False
        
        for line in lines:
            line = line.strip()
            if not line:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append('<br>')
                continue
                
            # Check if line is a bullet point
            if re.match(r'^\* ', line):
                if not in_list:
                    html_lines.append('<ul>')
                    in_list = True
                # Clean up the bullet point and add as list item
                bullet_text = re.sub(r'^\* ', '', line)
                bullet_text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', bullet_text)
                html_lines.append(f'<li>{bullet_text}</li>')
            else:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                # Handle regular text (possibly headers)
                if '<h4>' in line:
                    html_lines.append(line)
                else:
                    # Clean up any remaining asterisks
                    line = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', line)
                    html_lines.append(f'<p>{line}</p>')
        
        # Close any remaining list
        if in_list:
            html_lines.append('</ul>')
        
        formatted_html = '\n'.join(html_lines)
        
        # Clean up multiple consecutive line breaks
        formatted_html = re.sub(r'(<br>\s*){2,}', '<br>', formatted_html)
        
        return formatted_html
        
    except Exception as e:
        print(f"⚠️ Error formatting llama summary: {e}")
        # Fallback to simple text formatting
        try:
            simple_format = summary_text
            simple_format = re.sub(r'\*\*([^*]+):\*\*', r'\1:', simple_format)
            simple_format = re.sub(r'^\* ', '• ', simple_format, flags=re.MULTILINE)
            simple_format = re.sub(r'\*\*([^*]+)\*\*', r'\1', simple_format)
            return simple_format
        except:
            return summary_text


# --- Domain Extraction Functions ---
def extract_domain_from_company_analysis(result_text: str) -> str:
    """
    Extract the domain/industry from company analysis result text.
    
    Args:
        result_text: The company analysis result string
        
    Returns:
        Extracted domain or "Unknown" if not found
    """
    try:
        # Convert to string if not already
        text = str(result_text)
        
        # Look for various domain patterns
        domain_patterns = [
            r"Domain:\s*([^\n\r]+)",
            r"Industry:\s*([^\n\r]+)", 
            r"Sector:\s*([^\n\r]+)",
            r"Field:\s*([^\n\r]+)",
            r"Business Domain:\s*([^\n\r]+)",
            r"Company Domain:\s*([^\n\r]+)"
        ]
        
        for pattern in domain_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                domain = match.group(1).strip()
                # Clean up common prefixes/suffixes
                domain = re.sub(r'^[:\-\s]+|[:\-\s]+$', '', domain)
                if domain and domain.lower() not in ['unknown', 'n/a', 'not specified']:
                    return domain
        
        # If no explicit domain found, try to infer from common keywords
        business_keywords = {
            'software': 'Technology/Software',
            'ai': 'Artificial Intelligence',
            'tech': 'Technology', 
            'health': 'Healthcare',
            'medical': 'Healthcare',
            'finance': 'Financial Services',
            'fintech': 'Financial Technology',
            'ecommerce': 'E-commerce',
            'retail': 'Retail',
            'education': 'Education',
            'edtech': 'Educational Technology',
            'marketing': 'Marketing',
            'consulting': 'Consulting',
            'manufacturing': 'Manufacturing',
            'logistics': 'Logistics',
            'energy': 'Energy',
            'real estate': 'Real Estate',
            'food': 'Food & Beverage',
            'entertainment': 'Entertainment',
            'media': 'Media',
            'gaming': 'Gaming',
            'automotive': 'Automotive',
            'blockchain': 'Blockchain/Crypto',
            'cryptocurrency': 'Blockchain/Crypto'
        }
        
        text_lower = text.lower()
        for keyword, domain in business_keywords.items():
            if keyword in text_lower:
                return domain
                
        return "Unknown"
        
    except Exception as e:
        print(f"⚠️ Error extracting domain: {e}")
        return "Unknown"


# --- JSON Storage Functions ---
def save_analysis_to_json(analysis_data: dict, json_file_path: str = "pitch_analysis_history.json") -> None:
    """
    Save analysis data to a JSON file as a list of dictionaries.
    Each API call appends a new dictionary to the list.
    
    Args:
        analysis_data: The complete analysis dictionary to save
        json_file_path: Path to the JSON file (defaults to pitch_analysis_history.json)
    """
    try:
        # Add timestamp to the data
        timestamped_data = {
            "timestamp": datetime.now().isoformat(),
            "data": analysis_data
        }
        
        # Check if file exists and load existing data
        if os.path.exists(json_file_path):
            try:
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    
                # Ensure existing_data is a list
                if not isinstance(existing_data, list):
                    existing_data = []
            except (json.JSONDecodeError, IOError):
                print(f"⚠️ Could not read existing JSON file. Creating new one.")
                existing_data = []
        else:
            existing_data = []
        
        # Append new data
        existing_data.append(timestamped_data)
        
        # Save back to file
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Analysis saved to {json_file_path} (Total records: {len(existing_data)})")
        
    except Exception as e:
        print(f"❌ Failed to save analysis to JSON: {str(e)}")


# --- FastAPI Application ---
app = FastAPI(
    title="PitchBot API",
    description="API for processing and analyzing startup pitches.",
    version="0.1.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/pitch-history/")
async def get_pitch_history():
    """
    Get pitch analysis history with structured data.
    Returns a list of dictionaries containing timestamp, module analyses, and rubric scores.
    """
    try:
        # Check if the history file exists
        if not os.path.exists("pitch_analysis_history.json"):
            return {"message": "No pitch history found", "data": []}
        
        # Read the history file
        with open("pitch_analysis_history.json", 'r', encoding='utf-8') as f:
            history_data = json.load(f)
        
        # If not a list, convert to list
        if not isinstance(history_data, list):
            history_data = []
        
        # Extract and restructure the data
        structured_history = []
        
        for entry in history_data:
            timestamp = entry.get("timestamp", "")
            analysis_data = entry.get("data", {}).get("analysis", {})
            modules_data = analysis_data.get("modules", {})
            
            # Create structured entry
            structured_entry = {
                "timestamp": timestamp
            }
            
            # Extract data for each module type
            module_mapping = {
                "pdf_analysis": "pdf",
                "video_analysis": "video", 
                "github_analysis": "github",
                "company_analysis": "company_website",
                "market_research": "agentic_research"
            }
            
            for module_key, module_name in module_mapping.items():
                if module_key in modules_data:
                    module_data = modules_data[module_key]
                    
                    # Extract analysis text
                    analysis_text = ""
                    if "result" in module_data:
                        analysis_text = str(module_data["result"])
                    elif "analysis" in module_data:
                        analysis_text = str(module_data["analysis"])
                    
                    # Extract llama summary
                    raw_llama_summary = module_data.get("llama_summary", "")
                    formatted_llama_summary = format_llama_summary(raw_llama_summary) if raw_llama_summary else ""
                    
                    # Extract rubric scores
                    rubric_scores = module_data.get("rubric_scores", {})
                    
                    # Structure module data
                    module_entry = {
                        "analysis": analysis_text,
                        "llama_summary": formatted_llama_summary,
                        "impact": rubric_scores.get("impact", {}).get("score", 0),
                        "demo": rubric_scores.get("demo", {}).get("score", 0),
                        "creativity": rubric_scores.get("creativity", {}).get("score", 0),
                        "pitch": rubric_scores.get("pitch", {}).get("score", 0)
                    }
                    
                    # Add domain for company analysis
                    if module_name == "company_website" and "domain" in module_data:
                        module_entry["domain"] = module_data["domain"]
                    
                    structured_entry[module_name] = module_entry
            
            # Only add entries that have at least one module
            if any(key in structured_entry for key in ["pdf", "video", "github", "company_website", "agentic_research"]):
                structured_history.append(structured_entry)
        
        return {
            "message": f"Retrieved {len(structured_history)} pitch analysis records",
            "data": structured_history
        }
        
    except Exception as e:
        return {
            "message": f"Error reading pitch history: {str(e)}",
            "data": []
        }


@app.post("/analyze-pitch/")
async def analyze_pitch(
    pdf_document: Union[UploadFile, str, None] = File(None, description="Optional PDF pitch deck."),
    video_file: Union[UploadFile, str, None] = File(None, description="Optional video of the pitch or demo."),
    source_url: Optional[str] = Form(None, description="Optional URL (e.g., GitHub repo)."),
    company_url: Optional[str] = Form(None, description="Optional company website URL.")
):
    """
    Asynchronously receives all pitch assets, runs processing in parallel,
    and returns a confirmation upon completion.
    """
    print("🚀 Received new pitch analysis request.")
    print(f"PDF document: {pdf_document.filename if hasattr(pdf_document, 'filename') else 'None'}")
    print(f"Video file: {video_file.filename if hasattr(video_file, 'filename') else 'None'}")
    print(f"Source URL: {source_url if source_url else 'None'}")
    print(f"Company URL: {company_url if company_url else 'None'}")
    print(f"DEBUG: Type of video_file received: {type(video_file)}")
    
    # Additional debugging for video file - using direct attribute access
    if hasattr(video_file, 'filename'):
        print(f"DEBUG: video_file.filename = '{video_file.filename}'")
    if hasattr(video_file, 'content_type'):
        print(f"DEBUG: video_file.content_type = '{video_file.content_type}'")
    if hasattr(video_file, 'size'):
        print(f"DEBUG: video_file.size = {video_file.size}")
    else:
        print("DEBUG: video_file has no 'size' attribute")

    # --- Type coercion for optional file uploads ---
    # When a file is not provided, the form sends an empty string `''`
    # We convert it to `None` to handle it cleanly in our logic.
    final_pdf_document: Optional[UploadFile] = pdf_document if hasattr(pdf_document, 'filename') else None
    final_video_file: Optional[UploadFile] = video_file if hasattr(video_file, 'filename') else None

    # --- TRUE PARALLEL EXECUTION ---
    # All tasks run in parallel - PDF, video, GitHub URL, and company URL are completely independent
    print("🚀 Starting parallel processing for ALL tasks...")
    parallel_tasks = []
    
    # Add video processing task if a video is provided
    if final_video_file and hasattr(final_video_file, 'size') and final_video_file.size and final_video_file.size > 0:
        print(f"Adding video processing task for file with size: {final_video_file.size} bytes")
        parallel_tasks.append(
            asyncio.create_task(process_video(final_video_file))
        )
    else:
        print(f"Skipping video processing - no valid video file (size: {getattr(final_video_file, 'size', 'N/A')})")
        
    # Add PDF processing task if a PDF is provided
    if final_pdf_document and final_pdf_document.filename:
        print("Adding PDF processing task...")
        parallel_tasks.append(
            asyncio.create_task(process_pdf(final_pdf_document))
        )
        
    # Add GitHub URL processing task if a URL is provided
    if source_url:
        print("Adding GitHub URL processing task...")
        parallel_tasks.append(
            asyncio.create_task(process_url(source_url))
        )
        
    # Add company URL processing task if a company URL is provided
    if company_url:
        print("Adding company URL processing task...")
        parallel_tasks.append(
            asyncio.create_task(process_company_url(company_url))
        )
        
    # Run all tasks concurrently and wait for them to complete
    if parallel_tasks:
        print(f"🔥 Executing {len(parallel_tasks)} tasks in TRUE PARALLEL...")
        parallel_results = await asyncio.gather(*parallel_tasks)
        print("✅ All parallel processing tasks completed.")
    else:
        parallel_results = []
        print("No tasks to run.")
    
    # --- AGENTIC SEARCH INTEGRATION ---
    # Combine all results into a comprehensive summary for agentic search
    agentic_search_result = None
    if parallel_results:
        print("\n🔍 Step 4: Conducting agentic market research based on combined analysis...")
        
        # Create a combined summary from all processing results
        combined_summary = "STARTUP PITCH ANALYSIS SUMMARY:\n\n"
        
        result_index = 0
        
        if final_video_file and hasattr(final_video_file, 'size') and final_video_file.size and final_video_file.size > 0:
            if result_index < len(parallel_results):
                combined_summary += f"VIDEO ANALYSIS:\n{parallel_results[result_index]}\n\n"
                result_index += 1
        
        if final_pdf_document and final_pdf_document.filename:
            if result_index < len(parallel_results):
                combined_summary += f"PDF DOCUMENT ANALYSIS:\n{parallel_results[result_index]}\n\n"
                result_index += 1
        
        if source_url:
            if result_index < len(parallel_results):
                combined_summary += f"GITHUB REPOSITORY ANALYSIS:\n{parallel_results[result_index]}\n\n"
                result_index += 1
        
        if company_url:
            if result_index < len(parallel_results):
                combined_summary += f"COMPANY WEBSITE ANALYSIS:\n{parallel_results[result_index]}\n\n"
                result_index += 1
        
        # Conduct agentic search research
        try:
            researcher = StartupResearcher()
            agentic_search_result = await researcher.conduct_research(combined_summary)
            print("✅ Agentic market research completed.")
        except Exception as e:
            print(f"❌ Agentic search failed: {e}")
            agentic_search_result = {"error": f"Agentic search failed: {str(e)}"}

    # --- Print Final Results to Console ---
    print("\n" + "="*80)
    print("🎉 FINAL PROCESSING RESULTS 🎉")
    print("="*80)
    
    if parallel_results:
        for i, result in enumerate(parallel_results):
            print("\n" + "-"*80)
            print(f"📄 RESULT {i+1}")
            print("-" * 80)
            print(result)
    else:
        print("No results to display.")
    
    # Print agentic search results
    if agentic_search_result:
        print("\n" + "-"*80)
        print("🔍 AGENTIC MARKET RESEARCH RESULTS")
        print("-" * 80)
        if "analysis" in agentic_search_result and agentic_search_result["analysis"]:
            print(agentic_search_result["analysis"])
        else:
            print("Market research data collected but analysis not available.")
            print(f"Search queries executed: {len(agentic_search_result.get('search_queries', []))}")
            print(f"Total pages analyzed: {agentic_search_result.get('total_pages_analyzed', 0)}")
    
    print("="*80)

    # Create structured response with module identification
    structured_results = {
        "processing_summary": {
            "total_modules": len(parallel_tasks),
            "successful_completions": len(parallel_results),
            "processing_time": "Completed in parallel"
        },
        "modules": {}
    }
    
    # Map results to their respective modules with rubric scoring and LLAMA summarization
    result_index = 0
    
    if final_video_file and hasattr(final_video_file, 'size') and final_video_file.size and final_video_file.size > 0:
        if result_index < len(parallel_results):
            video_result = parallel_results[result_index]
            structured_results["modules"]["video_analysis"] = {
                "module_name": "Video Processor",
                "input_file": final_video_file.filename,
                "status": "completed",
                "result": video_result
            }
            
            # Add LLAMA summarization for video analysis
            video_summary = await add_module_summary("Video Analysis", video_result)
            if video_summary:
                structured_results["modules"]["video_analysis"]["llama_summary"] = video_summary
            
            # Add rubric scoring for video analysis
            video_rubric_scores = await add_rubric_scores(video_result, "Video Analysis")
            structured_results["modules"]["video_analysis"]["rubric_scores"] = video_rubric_scores
            
            result_index += 1
    
    if final_pdf_document and final_pdf_document.filename:
        if result_index < len(parallel_results):
            pdf_result = parallel_results[result_index]
            structured_results["modules"]["pdf_analysis"] = {
                "module_name": "PDF Processor", 
                "input_file": final_pdf_document.filename,
                "status": "completed",
                "result": pdf_result
            }
            
            # Add LLAMA summarization for PDF analysis
            pdf_summary = await add_module_summary("PDF Analysis", pdf_result)
            if pdf_summary:
                structured_results["modules"]["pdf_analysis"]["llama_summary"] = pdf_summary
            
            # Add rubric scoring for PDF analysis
            pdf_rubric_scores = await add_rubric_scores(pdf_result, "PDF Analysis")
            structured_results["modules"]["pdf_analysis"]["rubric_scores"] = pdf_rubric_scores
            
            result_index += 1
    
    if source_url:
        if result_index < len(parallel_results):
            github_result = parallel_results[result_index]
            structured_results["modules"]["github_analysis"] = {
                "module_name": "GitHub Repository Analyzer",
                "input_url": source_url,
                "status": "completed", 
                "result": github_result
            }
            
            # Add LLAMA summarization for GitHub analysis
            github_summary = await add_module_summary("GitHub Analysis", github_result)
            if github_summary:
                structured_results["modules"]["github_analysis"]["llama_summary"] = github_summary
            
            # Add rubric scoring for GitHub analysis
            github_rubric_scores = await add_rubric_scores(github_result, "GitHub Analysis")
            structured_results["modules"]["github_analysis"]["rubric_scores"] = github_rubric_scores
            
            result_index += 1
    
    if company_url:
        if result_index < len(parallel_results):
            company_result = parallel_results[result_index]
            
            # Extract domain from company analysis result
            extracted_domain = extract_domain_from_company_analysis(company_result)
            
            structured_results["modules"]["company_analysis"] = {
                "module_name": "Company Website Analyzer",
                "input_url": company_url,
                "status": "completed",
                "result": company_result,
                "domain": extracted_domain
            }
            
            # Add LLAMA summarization for company analysis
            company_summary = await add_module_summary("Company Analysis", company_result)
            if company_summary:
                structured_results["modules"]["company_analysis"]["llama_summary"] = company_summary
            
            # Add rubric scoring for company analysis
            company_rubric_scores = await add_rubric_scores(company_result, "Company Analysis")
            structured_results["modules"]["company_analysis"]["rubric_scores"] = company_rubric_scores
            
            result_index += 1
    
    # Add agentic search results to structured response
    if agentic_search_result:
        market_research_analysis = agentic_search_result.get("analysis", "")
        structured_results["modules"]["market_research"] = {
            "module_name": "Agentic Market Research",
            "input_summary": "Combined analysis from all processed modules",
            "status": "completed" if "error" not in agentic_search_result else "failed",
            "search_queries": agentic_search_result.get("search_queries", []),
            "total_pages_analyzed": agentic_search_result.get("total_pages_analyzed", 0),
            "analysis": market_research_analysis,
            "error": agentic_search_result.get("error", None)
        }
        
        # Add LLAMA summarization for market research (only if successfully completed)
        if "error" not in agentic_search_result and market_research_analysis:
            market_research_summary = await add_module_summary("Market Research", market_research_analysis)
            if market_research_summary:
                structured_results["modules"]["market_research"]["llama_summary"] = market_research_summary
        
        # Add rubric scoring for market research (only if successfully completed)
        if "error" not in agentic_search_result and market_research_analysis:
            market_research_rubric_scores = await add_rubric_scores(market_research_analysis, "Market Research")
            structured_results["modules"]["market_research"]["rubric_scores"] = market_research_rubric_scores

    # Create the final response
    final_response = {
        "message": "Pitch assets received and processed successfully.",
        "analysis": structured_results
    }
    
    # --- SAVE TO JSON FILE ---
    print("\n💾 Saving analysis to JSON file...")
    save_analysis_to_json(final_response)
    
    return final_response

# --- Command-Line Interface ---
def main(args: Optional[list[str]] = None) -> int:
    """
    Main entry point for PitchBot.
    
    Args:
        args: Command line arguments (defaults to sys.argv[1:])
        
    Returns:
        Exit code (0 for success)
    """
    if args is None:
        args = sys.argv[1:]
    
    parser = argparse.ArgumentParser(
        description="PitchBot - AI-powered pitch assistant"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Audio processing command
    audio_parser = subparsers.add_parser(
        "process-audio", 
        help="Process audio file: transcribe and summarize"
    )
    audio_parser.add_argument(
        "file_path", 
        help="Absolute path to the audio file"
    )
    audio_parser.add_argument(
        "--custom-prompt", 
        help="Custom prompt for summarization (optional)"
    )
    
    # API server command
    server_parser = subparsers.add_parser("serve", help="Run the FastAPI server")
    server_parser.add_argument("--host", default="127.0.0.1", help="Host to bind the server to")
    server_parser.add_argument("--port", default=8000, type=int, help="Port to run the server on")
    
    # Parse arguments
    parsed_args = parser.parse_args(args)
    
    if parsed_args.command == "process-audio":
        # Run async command with asyncio.run()
        return asyncio.run(_process_audio_command(parsed_args))
    elif parsed_args.command == "serve":
        # Run the API server
        uvicorn.run(
            "pitchbot.main:app", 
            host=parsed_args.host, 
            port=parsed_args.port, 
            reload=True
        )
        return 0
    else:
        print("PitchBot v0.1.0")
        print("AI-powered pitch assistant")
        print("\nAvailable commands:")
        print("  process-audio <file_path>  - Process audio file")
        print("  serve                      - Run the API server")
        print("\nExample:")
        print("  pitchbot serve")
        return 0


async def _process_audio_command(args) -> int:
    """Handle audio processing command asynchronously."""
    try:
        # NOTE: This CLI command still uses file paths.
        # It would need to be adapted to also work with in-memory data
        # or be kept as a file-based utility.
        # For now, we assume it's for file-based processing.
        # To make it work with the new in-memory processor, we would need to read the file first.
        # This part is left as-is to not break existing CLI functionality.
        print("Warning: The 'process-audio' CLI command is not yet updated for in-memory processing.")
        print("Please use the 'serve' command and the API for the new in-memory pipeline.")
        return 1
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 