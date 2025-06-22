"""
URL Processor for PitchBot

Handles processing of GitHub repository URLs using the Code Analyzer Agent.
"""

import re
from typing import Optional
from .code_analyzer_agent import CodeAnalyzerAgent


def is_github_url(url: str) -> bool:
    """Check if the URL is a GitHub repository URL."""
    github_pattern = r'https?://github\.com/[\w\-\.]+/[\w\-\.]+/?.*'
    return bool(re.match(github_pattern, url))


async def process_url(url: str) -> str:
    """
    Process a URL - specifically handles GitHub repository analysis.
    
    Args:
        url: The URL to process
        
    Returns:
        Analysis result as a string
    """
    if not url:
        return "No URL provided."
    
    print(f"🔗 URL processing started for: {url}")
    
    # Check if it's a GitHub URL
    if is_github_url(url):
        print("🐙 Detected GitHub repository URL - starting code analysis...")
        
        try:
            # Initialize the Code Analyzer Agent with 10 parallel workers
            agent = CodeAnalyzerAgent(max_workers=15)
            
            # Analyze the GitHub repository
            analysis_result = await agent.analyze_github_repository(url)
            
            # Format the result for display
            if "error" in analysis_result and analysis_result["error"]:
                return f"GitHub repository analysis failed: {analysis_result['error']}"
            
            # Format the analysis into a readable report
            formatted_result = format_github_analysis(analysis_result)
            
            print("✅ GitHub repository analysis complete.")
            return formatted_result
            
        except Exception as e:
            error_msg = f"Failed to analyze GitHub repository: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    else:
        # For non-GitHub URLs, provide a basic response
        print("🌐 Non-GitHub URL detected - basic processing...")
        result = f"URL '{url}' processed. This appears to be a non-GitHub URL. Currently, only GitHub repository analysis is supported."
        print("✅ URL processing complete.")
        return result


def format_github_analysis(analysis: dict) -> str:
    """
    Format the GitHub analysis results into a readable report.
    
    Args:
        analysis: Analysis results from CodeAnalyzerAgent
        
    Returns:
        Formatted analysis report
    """
    report_lines = []
    
    # Header
    report_lines.append("=" * 80)
    report_lines.append("🐙 GITHUB REPOSITORY ANALYSIS REPORT")
    report_lines.append("=" * 80)
    
    # Summary
    if analysis.get("summary"):
        report_lines.append("\n📋 SUMMARY:")
        report_lines.append("-" * 40)
        report_lines.append(analysis["summary"])
    
    # Exhaustive Summary
    if analysis.get("exhaustive_summary"):
        report_lines.append("\n📊 DETAILED ANALYSIS:")
        report_lines.append("-" * 40)
        report_lines.append(analysis["exhaustive_summary"])
    
    # Problem Solved
    if analysis.get("problem_solved"):
        report_lines.append("\n🎯 PROBLEM SOLVED:")
        report_lines.append("-" * 40)
        report_lines.append(analysis["problem_solved"])
    
    # Technology Stack
    if analysis.get("stacks"):
        report_lines.append("\n🛠️  TECHNOLOGY STACK:")
        report_lines.append("-" * 40)
        for i, tech in enumerate(analysis["stacks"], 1):
            report_lines.append(f"  {i}. {tech}")
    
    # Pitfalls
    if analysis.get("pitfalls"):
        report_lines.append("\n⚠️  POTENTIAL PITFALLS:")
        report_lines.append("-" * 40)
        for i, pitfall in enumerate(analysis["pitfalls"], 1):
            report_lines.append(f"  {i}. {pitfall}")
    
    # Improvements
    if analysis.get("improvements"):
        report_lines.append("\n🚀 SUGGESTED IMPROVEMENTS:")
        report_lines.append("-" * 40)
        for i, improvement in enumerate(analysis["improvements"], 1):
            report_lines.append(f"  {i}. {improvement}")
    
    report_lines.append("\n" + "=" * 80)
    
    return "\n".join(report_lines) 