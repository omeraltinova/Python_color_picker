"""
Core module for Enhanced Color Picker.

Contains the main application controller, configuration management,
event bus system, and core exception classes.
"""

from .application import EnhancedColorPickerApp
from .config import Config
from .event_bus import EventBus
from .exceptions import (
    ColorPickerError,
    ImageLoadError,
    ColorConversionError,
    PaletteError,
    ValidationError
)

__all__ = [
    "EnhancedColorPickerApp",
    "Config",
    "EventBus",
    "ColorPickerError",
    "ImageLoadError", 
    "ColorConversionError",
    "PaletteError",
    "ValidationError"
]