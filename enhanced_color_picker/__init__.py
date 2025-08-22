"""
Enhanced Color Picker - A modern, feature-rich color picker application.

This package provides a comprehensive color picking tool with advanced features
including zoom, pan, color analysis, palette management, and accessibility support.
"""

__version__ = "1.0.0"
__author__ = "Enhanced Color Picker Team"
__description__ = "Advanced color picker with professional features"

# Package-level imports for convenience
from .core.config import Config
from .core.event_bus import EventBus

# Import application class conditionally
try:
    from .core.application import EnhancedColorPickerApp
    __all__ = [
        "EnhancedColorPickerApp",
        "Config", 
        "EventBus"
    ]
except ImportError:
    # Tkinter not available, skip GUI components
    __all__ = [
        "Config", 
        "EventBus"
    ]