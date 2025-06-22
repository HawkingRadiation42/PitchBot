"""
File utilities for filtering and processing code files.
"""

import os
from pathlib import Path
from typing import List, Set


class CodeFileFilter:
    """Utility class for filtering code files from repositories."""
    
    def __init__(self):
        """Initialize the file filter with predefined patterns."""
        # Code file extensions to include
        self.code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c',
            '.h', '.hpp', '.cs', '.go', '.rs', '.php', '.rb', '.swift',
            '.kt', '.scala', '.clj', '.hs', '.ml', '.fs', '.vb', '.pl',
            '.sh', '.bash', '.zsh', '.fish', '.ps1', '.r', '.sql',
            '.html', '.css', '.scss', '.less', '.vue', '.svelte'
        }
        
        # Extensions to exclude (data, config, etc.)
        self.exclude_extensions = {
            '.md', '.txt', '.log', '.json', '.xml', '.yaml', '.yml',
            '.csv', '.tsv', '.xlsx', '.xls', '.pdf', '.doc', '.docx',
            '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.bmp',
            '.mp4', '.avi', '.mov', '.wmv', '.mp3', '.wav', '.ogg',
            '.zip', '.tar', '.gz', '.rar', '.7z', '.jar', '.war',
            '.pyc', '.pyo', '.class', '.o', '.so', '.dll', '.exe',
            '.lock', '.toml', '.ini', '.cfg', '.conf', '.env'
        }
        
        # Directory patterns to exclude
        self.exclude_directories = {
            '.git', '.svn', '.hg', '__pycache__', '.pytest_cache',
            'node_modules', '.venv', 'venv', 'env', '.env',
            'build', 'dist', 'target', 'bin', 'obj', '.idea',
            '.vscode', '.vs', 'coverage', '.nyc_output', '.cache',
            'logs', 'tmp', 'temp', '.tmp', '.sass-cache',
            '.next', '.nuxt', 'out', 'public', 'static', 'assets'
        }
        
        # File name patterns to exclude (test files)
        self.exclude_patterns = {
            'test_', '_test', '.test.', '.spec.',
            'tests.', 'spec.', 'mock', 'fixture',
            'conftest', 'setup.py', 'setup.cfg',
            'requirements.txt', 'package.json', 'package-lock.json',
            'yarn.lock', 'Dockerfile', 'docker-compose',
            'makefile', 'Makefile', 'CMakeLists.txt',
            'README', 'LICENSE', 'CHANGELOG', 'CONTRIBUTING'
        }
    
    def get_code_files(self, root_path: str) -> List[str]:
        """
        Get all relevant code files from the repository.
        
        Args:
            root_path: Root directory path to scan
            
        Returns:
            List of file paths containing code files
        """
        code_files = []
        root_path = Path(root_path)
        
        for file_path in self._walk_directory(root_path):
            if self._is_code_file(file_path):
                code_files.append(str(file_path))
        
        return code_files
    
    def _walk_directory(self, root_path: Path):
        """Walk through directory structure, excluding unwanted directories."""
        for item in root_path.iterdir():
            if item.is_file():
                yield item
            elif item.is_dir() and not self._should_exclude_directory(item.name):
                yield from self._walk_directory(item)
    
    def _should_exclude_directory(self, dir_name: str) -> bool:
        """Check if directory should be excluded."""
        dir_name_lower = dir_name.lower()
        
        # Check exact matches
        if dir_name_lower in self.exclude_directories:
            return True
        
        # Check patterns
        exclude_patterns = [
            'test', 'tests', '__test__', 'spec', 'specs',
            'mock', 'mocks', 'fixture', 'fixtures',
            'example', 'examples', 'demo', 'demos',
            'doc', 'docs', 'documentation'
        ]
        
        for pattern in exclude_patterns:
            if pattern in dir_name_lower:
                return True
        
        return False
    
    def _is_code_file(self, file_path: Path) -> bool:
        """
        Check if file is a code file that should be analyzed.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file should be analyzed, False otherwise
        """
        # Get file extension
        extension = file_path.suffix.lower()
        
        # Check if extension is excluded
        if extension in self.exclude_extensions:
            return False
        
        # Check if extension is a code extension
        if extension not in self.code_extensions:
            return False
        
        # Check file name patterns
        file_name = file_path.name.lower()
        
        for pattern in self.exclude_patterns:
            if pattern in file_name:
                return False
        
        # Additional checks for test files
        if self._is_test_file(file_path):
            return False
        
        # Check file size (skip very large files > 100KB)
        try:
            if file_path.stat().st_size > 100 * 1024:
                return False
        except OSError:
            return False
        
        return True
    
    def _is_test_file(self, file_path: Path) -> bool:
        """Check if file is a test file based on various indicators."""
        file_name = file_path.name.lower()
        parent_dir = file_path.parent.name.lower()
        
        # Check file name patterns
        test_indicators = [
            'test_', '_test.', '.test.', '_test_',
            'spec_', '_spec.', '.spec.', '_spec_',
            'tests.', 'specs.',
            'conftest.', 'test.py', 'tests.py'
        ]
        
        for indicator in test_indicators:
            if indicator in file_name:
                return True
        
        # Check parent directory
        test_dirs = ['test', 'tests', 'spec', 'specs', '__tests__']
        if parent_dir in test_dirs:
            return True
        
        return False
    
    def get_file_info(self, file_path: str) -> dict:
        """
        Get information about a code file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        path = Path(file_path)
        
        try:
            stat = path.stat()
            return {
                'path': str(path),
                'name': path.name,
                'extension': path.suffix,
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'language': self._detect_language(path.suffix)
            }
        except OSError:
            return {
                'path': str(path),
                'name': path.name,
                'extension': path.suffix,
                'size': 0,
                'modified': 0,
                'language': 'unknown'
            }
    
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