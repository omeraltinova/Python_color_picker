#!/usr/bin/env python3
"""
Main entry point for Enhanced Color Picker application.

This script provides the main entry point for running the Enhanced Color Picker
application with command-line argument support.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from enhanced_color_picker.core.application import main

if __name__ == "__main__":
    main()