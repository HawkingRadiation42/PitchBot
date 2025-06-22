"""
Code Analyzer Agent

Main agent for analyzing GitHub repositories and providing comprehensive code analysis.
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
import asyncio
import aiohttp
from urllib.parse import urlparse

from .file_utils import CodeFileFilter
from .llama_client import LlamaClient


class CodeAnalyzerAgent:
    """Main agent for analyzing code repositories."""
    
    def __init__(self, llama_api_key: Optional[str] = None, max_workers: int = 5):
        """Initialize the code analyzer agent."""
        self.llama_client = LlamaClient(llama_api_key)
        self.file_filter = CodeFileFilter()
        self.max_workers = max_workers
        self.semaphore = asyncio.Semaphore(max_workers)
        
    async def analyze_github_repository(self, github_url: str) -> Dict[str, Any]:
        """
        Analyze a GitHub repository and return comprehensive analysis.
        
        Args:
            github_url: GitHub repository URL
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            # Clone repository to temporary directory
            repo_path = await self._clone_repository(github_url)
            
            # Get all relevant code files
            code_files = self.file_filter.get_code_files(repo_path)
            
            # Step 1: Analyze each file individually with simplified prompts
            file_contexts = await self._analyze_files_step1(code_files)
            
            # Step 2: Generate exhaustive summary
            exhaustive_summary = await self._generate_exhaustive_summary(file_contexts)
            
            # Step 3: Generate detailed analysis
            detailed_analysis = await self._generate_detailed_analysis(file_contexts)
            
            # Clean up LLAMA client session
            await self.llama_client.close()
            
            # Clean up temporary directory
            shutil.rmtree(repo_path)
            
            # Combine results
            result = detailed_analysis.copy()
            result["exhaustive_summary"] = exhaustive_summary
            
            return result
            
        except Exception as e:
            return {
                "error": f"Failed to analyze repository: {str(e)}",
                "summary": "",
                "exhaustive_summary": "",
                "stacks": [],
                "problem_solved": "",
                "pitfalls": [],
                "improvements": []
            }
    
    async def _clone_repository(self, github_url: str) -> str:
        """Clone GitHub repository to temporary directory."""
        # Parse GitHub URL to get repository name
        parsed_url = urlparse(github_url)
        repo_name = parsed_url.path.strip('/').split('/')[-1]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        repo_path = os.path.join(temp_dir, repo_name)
        
        # Clone repository
        import subprocess
        try:
            subprocess.run(['git', 'clone', github_url, repo_path], 
                         check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to clone repository: {e.stderr.decode()}")
        
        return repo_path
    
    async def _analyze_files_step1(self, code_files: List[str]) -> List[Dict[str, str]]:
        """Step 1: Analyze each code file using simplified LLAMA API calls in parallel."""
        print(f"🔄 Processing {len(code_files)} files with {self.max_workers} parallel workers...")
        
        # Create tasks for parallel processing
        tasks = [self._analyze_single_file(file_path) for file_path in code_files]
        
        # Execute tasks in parallel with progress tracking
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and None results
        file_contexts = []
        successful = 0
        errors = 0
        
        for result in results:
            if isinstance(result, Exception):
                errors += 1
                print(f"❌ Task failed: {result}")
            elif result is not None:
                file_contexts.append(result)
                successful += 1
            else:
                errors += 1
        
        print(f"✅ Completed: {successful} files analyzed, {errors} errors")
        return file_contexts

    async def _analyze_single_file(self, file_path: str) -> Optional[Dict[str, str]]:
        """Analyze a single file with semaphore-based concurrency control."""
        async with self.semaphore:  # Limit concurrent API calls
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Skip very large files (> 10KB)
                if len(content) > 10000:
                    print(f"⏭️  Skipping large file: {file_path} ({len(content)} bytes)")
                    return None
                
                print(f"🔍 Analyzing: {file_path}")
                
                # Use simplified prompt as specified
                messages = [
                    {"role": "system", "content": "You are a senior software architect."},
                    {"role": "user", "content": f"Analyze this code:\n\n```{content}```"}
                ]
                
                context = await self.llama_client.generate_response_with_messages(messages)
                
                print(f"✅ Completed: {file_path}")
                
                # Store with fileName, context, and code as specified
                return {
                    "fileName": file_path,
                    "context": context,
                    "code": content
                }
                
            except Exception as e:
                print(f"❌ Error analyzing file {file_path}: {e}")
                return None
    
    async def _generate_exhaustive_summary(self, file_contexts: List[Dict[str, str]]) -> str:
        """Step 2: Generate exhaustive summary of what problem the repo solves."""
        # Prepare context with file information
        context_data = []
        for file_context in file_contexts:
            context_data.append(f"File: {file_context['fileName']}")
            context_data.append(f"Context: {file_context['context']}")
            context_data.append(f"Code: {file_context['code']}")
            context_data.append("-" * 50)
        
        context_string = "\n".join(context_data)
        
        # Generate exhaustive summary
        messages = [
            {"role": "system", "content": "You are a senior software architect."},
            {"role": "user", "content": f"Analyze this repo and generative exhaustive summary:\n\n```{context_string}```"}
        ]
        
        try:
            summary = await self.llama_client.generate_response_with_messages(messages)
            return summary
        except Exception as e:
            return f"Error generating exhaustive summary: {str(e)}"
    
    async def _generate_detailed_analysis(self, file_contexts: List[Dict[str, str]]) -> Dict[str, Any]:
        """Step 3: Generate detailed analysis with specific structure."""
        # Prepare context with file information
        context_data = []
        for file_context in file_contexts:
            context_data.append(f"File: {file_context['fileName']}")
            context_data.append(f"Context: {file_context['context']}")
            context_data.append(f"Code: {file_context['code']}")
            context_data.append("-" * 50)
        
        context_string = "\n".join(context_data)
        
        # Generate detailed analysis with specified prompt
        messages = [
            {"role": "system", "content": "You are a senior software architect."},
            {"role": "user", "content": f"""Analyze this repo and generative exhaustive summary:

```{context_string}```

Please provide a detailed analysis covering:

1. **Code Quality Assessment** :
   - Code organization and structure
   - Naming conventions and readability
   - Error handling practices
   - Code complexity and maintainability

2. **Scalability Analysis**:
   - Architecture patterns used
   - Database design considerations
   - Performance bottlenecks
   - Resource management

3. **Design Pitfalls** (List specific issues):
   - Anti-patterns identified
   - Tight coupling issues
   - Missing abstractions
   - Security vulnerabilities

5. **Overall Recommendations**:
   - Priority improvements
   - Best practices to implement
   - Long-term technical debt concerns

Please return your analysis in the following JSON format:
{{
  "summary": "Brief overview of the codebase",
  "stacks": ["list", "of", "technologies", "used"],
  "problem_solved": "What problem this codebase solves",
  "pitfalls": ["list", "of", "identified", "issues"],
  "improvements": ["list", "of", "recommended", "improvements"]
}}"""}
        ]
        
        try:
            response = await self.llama_client.generate_response_with_messages(messages)
            
            # Try to parse JSON response
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # If JSON parsing fails, create structured response
                return {
                    "summary": response[:500] + "..." if len(response) > 500 else response,
                    "stacks": self._extract_technologies(response),
                    "problem_solved": "Analysis available in summary",
                    "pitfalls": self._extract_pitfalls(response),
                    "improvements": self._extract_improvements(response)
                }
                
        except Exception as e:
            return {
                "error": f"Failed to generate analysis: {str(e)}",
                "summary": "",
                "stacks": [],
                "problem_solved": "",
                "pitfalls": [],
                "improvements": []
            }
    
    def _extract_technologies(self, text: str) -> List[str]:
        """Extract technologies from analysis text."""
        # Simple keyword extraction for common technologies
        technologies = []
        tech_keywords = [
            'python', 'javascript', 'typescript', 'react', 'vue', 'angular',
            'node.js', 'express', 'fastapi', 'django', 'flask', 'spring',
            'java', 'c++', 'c#', 'go', 'rust', 'php', 'ruby', 'rails',
            'postgresql', 'mysql', 'mongodb', 'redis', 'docker', 'kubernetes'
        ]
        
        text_lower = text.lower()
        for tech in tech_keywords:
            if tech in text_lower:
                technologies.append(tech.title())
        
        return list(set(technologies))
    
    def _extract_pitfalls(self, text: str) -> List[str]:
        """Extract pitfalls from analysis text."""
        # Extract sentences containing pitfall indicators
        pitfall_indicators = [
            'issue', 'problem', 'pitfall', 'vulnerability', 'anti-pattern',
            'tight coupling', 'missing', 'lacks', 'weakness'
        ]
        
        sentences = text.split('.')
        pitfalls = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if any(indicator in sentence.lower() for indicator in pitfall_indicators):
                if len(sentence) > 10:  # Filter out very short sentences
                    pitfalls.append(sentence)
        
        return pitfalls[:5]  # Return top 5 pitfalls
    
    def _extract_improvements(self, text: str) -> List[str]:
        """Extract improvements from analysis text."""
        # Extract sentences containing improvement indicators
        improvement_indicators = [
            'recommend', 'improve', 'enhancement', 'should', 'could',
            'better', 'optimize', 'refactor', 'implement'
        ]
        
        sentences = text.split('.')
        improvements = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if any(indicator in sentence.lower() for indicator in improvement_indicators):
                if len(sentence) > 10:  # Filter out very short sentences
                    improvements.append(sentence)
        
        return improvements[:5]  # Return top 5 improvements 