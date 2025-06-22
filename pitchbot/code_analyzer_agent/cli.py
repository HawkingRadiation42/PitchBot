"""
Command-line interface for the Code Analyzer Agent.
"""

import asyncio
import json
import sys
from typing import Optional
import argparse

from .agent import CodeAnalyzerAgent


async def analyze_repository(github_url: str, api_key: Optional[str] = None) -> dict:
    """
    Analyze a GitHub repository using the Code Analyzer Agent.
    
    Args:
        github_url: GitHub repository URL
        api_key: Optional LLAMA API key
        
    Returns:
        Analysis results as dictionary
    """
    try:
        agent = CodeAnalyzerAgent(llama_api_key=api_key)
        result = await agent.analyze_github_repository(github_url)
        return result
    except Exception as e:
        return {
            "error": f"Failed to analyze repository: {str(e)}",
            "summary": "",
            "stacks": [],
            "problem_solved": "",
            "pitfalls": [],
            "improvements": []
        }


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Analyze GitHub repositories using AI"
    )
    parser.add_argument(
        "github_url",
        help="GitHub repository URL to analyze"
    )
    parser.add_argument(
        "--api-key",
        help="LLAMA API key (optional if set in environment)"
    )
    parser.add_argument(
        "--output",
        choices=["json", "pretty"],
        default="pretty",
        help="Output format (default: pretty)"
    )
    
    args = parser.parse_args()
    
    # Run the analysis
    print(f"Analyzing repository: {args.github_url}")
    print("This may take a few minutes...")
    
    try:
        result = asyncio.run(analyze_repository(args.github_url, args.api_key))
        
        if args.output == "json":
            print(json.dumps(result, indent=2))
        else:
            print_pretty_results(result)
            
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def print_pretty_results(result: dict):
    """Print analysis results in a pretty format."""
    print("\n" + "="*80)
    print("🔍 CODE ANALYSIS RESULTS")
    print("="*80)
    
    if "error" in result and result["error"]:
        print(f"❌ Error: {result['error']}")
        return
    
    # Summary
    if result.get("summary"):
        print("\n📋 SUMMARY")
        print("-" * 40)
        print(result["summary"])
    
    # Technology Stack
    if result.get("stacks"):
        print("\n🛠️  TECHNOLOGY STACK")
        print("-" * 40)
        for tech in result["stacks"]:
            print(f"  • {tech}")
    
    # Problem Solved
    if result.get("problem_solved"):
        print("\n💡 PROBLEM IT SOLVES")
        print("-" * 40)
        print(result["problem_solved"])
    
    # Pitfalls
    if result.get("pitfalls"):
        print("\n⚠️  IDENTIFIED PITFALLS")
        print("-" * 40)
        for i, pitfall in enumerate(result["pitfalls"], 1):
            print(f"  {i}. {pitfall}")
    
    # Improvements
    if result.get("improvements"):
        print("\n🚀 RECOMMENDED IMPROVEMENTS")
        print("-" * 40)
        for i, improvement in enumerate(result["improvements"], 1):
            print(f"  {i}. {improvement}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main() 