"""
Example usage of the Code Analyzer Agent.

This script demonstrates how to use the Code Analyzer Agent to analyze
GitHub repositories and get comprehensive code analysis.
"""

import asyncio
import json
from pitchbot.code_analyzer_agent import CodeAnalyzerAgent


async def example_analysis():
    """Example function showing how to use the Code Analyzer Agent."""
    
    # Initialize the agent (will use LLAMA_API_KEY from environment)
    agent = CodeAnalyzerAgent()
    
    # Example GitHub repository URL
    github_url = "https://github.com/your-username/your-repo"
    
    print(f"🔍 Analyzing repository: {github_url}")
    print("This may take a few minutes as we analyze each code file...")
    
    try:
        # Analyze the repository
        result = await agent.analyze_github_repository(github_url)
        
        # Print results
        print("\n" + "="*80)
        print("📊 ANALYSIS RESULTS")
        print("="*80)
        
        # Print as formatted JSON
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Or access individual components
        print(f"\n📋 Summary: {result.get('summary', 'N/A')}")
        print(f"🛠️  Technologies: {', '.join(result.get('stacks', []))}")
        print(f"💡 Problem Solved: {result.get('problem_solved', 'N/A')}")
        print(f"⚠️  Pitfalls Found: {len(result.get('pitfalls', []))}")
        print(f"🚀 Improvements Suggested: {len(result.get('improvements', []))}")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")


def main():
    """Main function to run the example."""
    print("Code Analyzer Agent - Example Usage")
    print("="*50)
    
    # Check if LLAMA API key is available
    import os
    if not os.getenv('LLAMA_API_KEY'):
        print("⚠️  Warning: LLAMA_API_KEY environment variable not set.")
        print("Make sure to set your LLAMA API key in the .env file.")
        return
    
    # Run the example
    asyncio.run(example_analysis())


if __name__ == "__main__":
    main() 