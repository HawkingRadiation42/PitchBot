"""
Allow PitchBot to be executed as a module with `python -m pitchbot`.
"""

import sys
from .main import main

if __name__ == "__main__":
    sys.exit(main()) 