"""
Enums for the Enhanced Color Picker application.
"""

from enum import Enum


class ColorFormat(Enum):
    """Supported color formats for display and conversion."""
    RGB = "rgb"
    HEX = "hex"
    HSL = "hsl"
    HSV = "hsv"
    CMYK = "cmyk"


class ColorBlindnessType(Enum):
    """Types of color blindness for simulation."""
    PROTANOPIA = "protanopia"          # Red-blind
    DEUTERANOPIA = "deuteranopia"      # Green-blind
    TRITANOPIA = "tritanopia"          # Blue-blind
    PROTANOMALY = "protanomaly"        # Red-weak
    DEUTERANOMALY = "deuteranomaly"    # Green-weak
    TRITANOMALY = "tritanomaly"        # Blue-weak


class ExportFormat(Enum):
    """Supported export formats for palettes."""
    JSON = "json"
    CSS = "css"
    SCSS = "scss"
    SASS = "sass"
    LESS = "less"
    ASE = "ase"    # Adobe Swatch Exchange
    ACO = "aco"    # Adobe Color
    GPL = "gpl"    # GIMP Palette
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    CSHARP = "csharp"
    SWIFT = "swift"
    KOTLIN = "kotlin"