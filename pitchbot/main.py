"""
Main entry point for PitchBot application.
"""

import sys
from typing import Optional, List


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for PitchBot.
    
    Args:
        args: Command line arguments (defaults to sys.argv[1:])
        
    Returns:
        Exit code (0 for success)
    """
    if args is None:
        args = sys.argv[1:]
    
    print("🤖 PitchBot v0.1.0")
    print("AI-powered pitch assistant")
    print("Setup complete! Ready for development.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 