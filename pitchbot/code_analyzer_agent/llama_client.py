"""
LLAMA API Client for code analysis.
"""

import os
import json
import asyncio
import aiohttp
from typing import Optional, Dict, Any
from pathlib import Path


class LlamaClient:
    """Client for interacting with LLAMA API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LLAMA client.
        
        Args:
            api_key: LLAMA API key. If None, will try to get from environment.
        """
        self.api_key = api_key or os.getenv('LLAMA_API_KEY_GANI')
        if not self.api_key:
            raise ValueError("LLAMA API key is required. Set LLAMA_API_KEY environment variable or pass it directly.")
        
        self.base_url = "https://api.llama.com"
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _get_session(self):
        """Get or create aiohttp session."""
        if not self.session:
            # Create connector with SSL verification disabled for development
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            self.session = aiohttp.ClientSession(connector=connector)
        return self.session
    
    async def analyze_code_file(self, file_path: str, content: str) -> str:
        """
        Analyze a single code file using LLAMA API.
        
        Args:
            file_path: Path to the code file
            content: Content of the code file
            
        Returns:
            Analysis of the code file
        """
        # Create a prompt for analyzing individual code files
        file_name = Path(file_path).name
        language = self._detect_language(Path(file_path).suffix)
        
        # Create messages for file analysis
        messages = [
            {
                "role": "system", 
                "content": "You are a senior software architect and code reviewer. Analyze code files and provide concise, insightful feedback."
            },
            {
                "role": "user", 
                "content": f"""Analyze this {language} code file '{file_name}' and provide insights:

```{language.lower()}
{content}
```

Please provide a brief analysis focusing on:
1. Purpose and functionality of this file
2. Key components, classes, or functions
3. Code quality observations
4. Any potential issues or improvements
5. Dependencies and relationships

Keep the analysis concise but informative (2-3 sentences per point)."""
            }
        ]
        
        try:
            response = await self.generate_response_with_messages(messages)
            return response
        except Exception as e:
            return f"Error analyzing file {file_name}: {str(e)}"
    
    async def generate_response_with_messages(self, messages: list) -> str:
        """
        Generate response using LLAMA API with messages format.
        
        Args:
            messages: List of message objects with role and content
            
        Returns:
            Generated response from LLAMA
        """
        session = await self._get_session()
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'Llama-4-Maverick-17B-128E-Instruct-FP8',
            'messages': messages,
            'temperature': 0.3,
        }
        
        # Debug: Print request details
        # print(f"🔍 LLAMA API Request URL: {self.base_url}/v1/chat/completions")
        # print(f"🔍 LLAMA API Request Payload:")
        # print(json.dumps(payload, indent=2))
        
        try:
            async with session.post(
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=180)
            ) as response:
                
                # Debug: Print response status and headers
                # print(f"🔍 LLAMA API Response Status: {response.status}")
                # print(f"🔍 LLAMA API Response Headers: {dict(response.headers)}")
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Debug: Print full response
                    # print(f"🔍 LLAMA API Full Response:")
                    # print(json.dumps(data, indent=2))
                    
                    # LLAMA API uses different response format than OpenAI
                    if 'completion_message' in data:
                        # LLAMA API format
                        return data['completion_message']['content']['text']
                    elif 'choices' in data:
                        # OpenAI format (fallback)
                        return data['choices'][0]['message']['content']
                    else:
                        raise Exception(f"Unexpected LLAMA API response format: {list(data.keys())}")
                else:
                    error_text = await response.text()
                    print(f"🔍 LLAMA API Error Response: {error_text}")
                    raise Exception(f"LLAMA API error {response.status}: {error_text}")
                    
        except asyncio.TimeoutError:
            raise Exception("LLAMA API request timed out")
        except aiohttp.ClientError as e:
            raise Exception(f"LLAMA API client error: {str(e)}")
        except KeyError as e:
            raise Exception(f"Unexpected LLAMA API response format: {str(e)}")

    async def generate_response(self, prompt: str) -> str:
        """
        Generate response using LLAMA API with simple prompt.
        
        Args:
            prompt: The prompt to send to LLAMA
            
        Returns:
            Generated response from LLAMA
        """
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that provides detailed and accurate responses."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        return await self.generate_response_with_messages(messages)
    
    def _detect_language(self, extension: str) -> str:
        """Detect programming language from file extension."""
        language_mapping = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.jsx': 'React JSX',
            '.tsx': 'React TSX',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.h': 'C Header',
            '.hpp': 'C++ Header',
            '.cs': 'C#',
            '.go': 'Go',
            '.rs': 'Rust',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.scala': 'Scala',
            '.clj': 'Clojure',
            '.hs': 'Haskell',
            '.ml': 'OCaml',
            '.fs': 'F#',
            '.vb': 'Visual Basic',
            '.pl': 'Perl',
            '.sh': 'Shell',
            '.bash': 'Bash',
            '.zsh': 'Zsh',
            '.fish': 'Fish',
            '.ps1': 'PowerShell',
            '.r': 'R',
            '.sql': 'SQL',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.less': 'Less',
            '.vue': 'Vue',
            '.svelte': 'Svelte'
        }
        
        return language_mapping.get(extension.lower(), 'Unknown')
    
    async def close(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None 