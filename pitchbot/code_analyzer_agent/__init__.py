"""
Code Analyzer Agent Package

This package provides tools and agents for analyzing code structure,
quality, and generating insights about codebases.
"""

__version__ = "0.1.0"
__author__ = "PitchBot"

from .agent import CodeAnalyzerAgent
from .file_utils import CodeFileFilter
from .llama_client import LlamaClient

# Package exports
__all__ = [
    'CodeAnalyzerAgent',
    'CodeFileFilter', 
    'LlamaClient'
] 