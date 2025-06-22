"""
Main entry point for PitchBot application.
"""

import sys
import asyncio
from typing import Optional, Union
import argparse

import uvicorn
from fastapi import FastAPI, File, UploadFile, Form
from dotenv import load_dotenv

# Load environment variables from .env file in the root directory
load_dotenv()

# Import the processors
from .video_processor import process_video
from .pdf_processor import process_pdf
from .url_processor import process_url
from .company_url_processor import process_company_url

# Import agentic search components
from .agentic_search.enhanced_research_pipeline import EnhancedResearchPipeline


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


# --- FastAPI Application ---
app = FastAPI(
    title="PitchBot API",
    description="API for processing and analyzing startup pitches.",
    version="0.1.0"
)

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
    
    # Map results to their respective modules
    result_index = 0
    
    if final_video_file and hasattr(final_video_file, 'size') and final_video_file.size and final_video_file.size > 0:
        if result_index < len(parallel_results):
            structured_results["modules"]["video_analysis"] = {
                "module_name": "Video Processor",
                "input_file": final_video_file.filename,
                "status": "completed",
                "result": parallel_results[result_index]
            }
            result_index += 1
    
    if final_pdf_document and final_pdf_document.filename:
        if result_index < len(parallel_results):
            structured_results["modules"]["pdf_analysis"] = {
                "module_name": "PDF Processor", 
                "input_file": final_pdf_document.filename,
                "status": "completed",
                "result": parallel_results[result_index]
            }
            result_index += 1
    
    if source_url:
        if result_index < len(parallel_results):
            structured_results["modules"]["github_analysis"] = {
                "module_name": "GitHub Repository Analyzer",
                "input_url": source_url,
                "status": "completed", 
                "result": parallel_results[result_index]
            }
            result_index += 1
    
    if company_url:
        if result_index < len(parallel_results):
            structured_results["modules"]["company_analysis"] = {
                "module_name": "Company Website Analyzer",
                "input_url": company_url,
                "status": "completed",
                "result": parallel_results[result_index]
            }
            result_index += 1
    
    # Add agentic search results to structured response
    if agentic_search_result:
        structured_results["modules"]["market_research"] = {
            "module_name": "Agentic Market Research",
            "input_summary": "Combined analysis from all processed modules",
            "status": "completed" if "error" not in agentic_search_result else "failed",
            "search_queries": agentic_search_result.get("search_queries", []),
            "total_pages_analyzed": agentic_search_result.get("total_pages_analyzed", 0),
            "analysis": agentic_search_result.get("analysis", ""),
            "error": agentic_search_result.get("error", None)
        }

    return {
        "message": "Pitch assets received and processed successfully.",
        "analysis": structured_results
    }

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