"""
ColorData class with comprehensive color format support.
"""

from dataclasses import dataclass
from typing import Tuple, Optional
import colorsys
import math


@dataclass
class ColorData:
    """
    Comprehensive color data structure supporting multiple formats.
    
    Stores color information in RGB format as the base and provides
    conversion methods to other formats (HEX, HSL, HSV, CMYK).
    """
    
    # Base RGB values (0-255)
    r: int
    g: int
    b: int
    alpha: float = 1.0
    
    def __post_init__(self):
        """Validate RGB values after initialization."""
        self.r = max(0, min(255, int(self.r)))
        self.g = max(0, min(255, int(self.g)))
        self.b = max(0, min(255, int(self.b)))
        self.alpha = max(0.0, min(1.0, float(self.alpha)))
    
    @property
    def rgb(self) -> Tuple[int, int, int]:
        """Get RGB values as tuple."""
        return (self.r, self.g, self.b)
    
    @property
    def rgba(self) -> Tuple[int, int, int, float]:
        """Get RGBA values as tuple."""
        return (self.r, self.g, self.b, self.alpha)
    
    @property
    def hex(self) -> str:
        """Get HEX color code."""
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}".upper()
    
    @property
    def hex_with_alpha(self) -> str:
        """Get HEX color code with alpha channel."""
        alpha_hex = format(int(self.alpha * 255), '02x')
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}{alpha_hex}".upper()
    
    @property
    def hsl(self) -> Tuple[float, float, float]:
        """Get HSL values (H: 0-360, S: 0-100, L: 0-100)."""
        r_norm = self.r / 255.0
        g_norm = self.g / 255.0
        b_norm = self.b / 255.0
        
        h, l, s = colorsys.rgb_to_hls(r_norm, g_norm, b_norm)
        
        # Convert to standard HSL format
        h = h * 360  # 0-360 degrees
        s = s * 100  # 0-100 percent
        l = l * 100  # 0-100 percent
        
        return (round(h, 1), round(s, 1), round(l, 1))
    
    @property
    def hsv(self) -> Tuple[float, float, float]:
        """Get HSV values (H: 0-360, S: 0-100, V: 0-100)."""
        r_norm = self.r / 255.0
        g_norm = self.g / 255.0
        b_norm = self.b / 255.0
        
        h, s, v = colorsys.rgb_to_hsv(r_norm, g_norm, b_norm)
        
        # Convert to standard HSV format
        h = h * 360  # 0-360 degrees
        s = s * 100  # 0-100 percent
        v = v * 100  # 0-100 percent
        
        return (round(h, 1), round(s, 1), round(v, 1))
    
    @property
    def cmyk(self) -> Tuple[float, float, float, float]:
        """Get CMYK values (all 0-100 percent)."""
        r_norm = self.r / 255.0
        g_norm = self.g / 255.0
        b_norm = self.b / 255.0
        
        # Calculate K (black)
        k = 1 - max(r_norm, g_norm, b_norm)
        
        if k == 1:
            # Pure black
            return (0.0, 0.0, 0.0, 100.0)
        
        # Calculate CMY
        c = (1 - r_norm - k) / (1 - k)
        m = (1 - g_norm - k) / (1 - k)
        y = (1 - b_norm - k) / (1 - k)
        
        # Convert to percentages
        c = c * 100
        m = m * 100
        y = y * 100
        k = k * 100
        
        return (round(c, 1), round(m, 1), round(y, 1), round(k, 1))
    
    @classmethod
    def from_rgb(cls, r: int, g: int, b: int, alpha: float = 1.0) -> 'ColorData':
        """Create ColorData from RGB values."""
        return cls(r, g, b, alpha)
    
    @classmethod
    def from_hex(cls, hex_code: str, alpha: float = 1.0) -> 'ColorData':
        """Create ColorData from HEX color code."""
        # Remove # if present
        hex_code = hex_code.lstrip('#')
        
        # Handle 3-digit hex codes
        if len(hex_code) == 3:
            hex_code = ''.join([c*2 for c in hex_code])
        
        # Handle 8-digit hex codes (with alpha)
        if len(hex_code) == 8:
            alpha = int(hex_code[6:8], 16) / 255.0
            hex_code = hex_code[:6]
        
        if len(hex_code) != 6:
            raise ValueError(f"Invalid hex color code: {hex_code}")
        
        try:
            r = int(hex_code[0:2], 16)
            g = int(hex_code[2:4], 16)
            b = int(hex_code[4:6], 16)
            return cls(r, g, b, alpha)
        except ValueError:
            raise ValueError(f"Invalid hex color code: {hex_code}")
    
    @classmethod
    def from_hsl(cls, h: float, s: float, l: float, alpha: float = 1.0) -> 'ColorData':
        """Create ColorData from HSL values."""
        # Normalize values
        h = h / 360.0  # 0-1
        s = s / 100.0  # 0-1
        l = l / 100.0  # 0-1
        
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        
        # Convert to 0-255 range
        r = int(round(r * 255))
        g = int(round(g * 255))
        b = int(round(b * 255))
        
        return cls(r, g, b, alpha)
    
    @classmethod
    def from_hsv(cls, h: float, s: float, v: float, alpha: float = 1.0) -> 'ColorData':
        """Create ColorData from HSV values."""
        # Normalize values
        h = h / 360.0  # 0-1
        s = s / 100.0  # 0-1
        v = v / 100.0  # 0-1
        
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        
        # Convert to 0-255 range
        r = int(round(r * 255))
        g = int(round(g * 255))
        b = int(round(b * 255))
        
        return cls(r, g, b, alpha)
    
    @classmethod
    def from_cmyk(cls, c: float, m: float, y: float, k: float, alpha: float = 1.0) -> 'ColorData':
        """Create ColorData from CMYK values."""
        # Normalize values (0-1)
        c = c / 100.0
        m = m / 100.0
        y = y / 100.0
        k = k / 100.0
        
        # Convert CMYK to RGB
        r = 255 * (1 - c) * (1 - k)
        g = 255 * (1 - m) * (1 - k)
        b = 255 * (1 - y) * (1 - k)
        
        return cls(int(round(r)), int(round(g)), int(round(b)), alpha)
    
    def get_luminance(self) -> float:
        """Calculate relative luminance for WCAG contrast calculations."""
        def _linearize(value: int) -> float:
            """Convert sRGB value to linear RGB."""
            value = value / 255.0
            if value <= 0.03928:
                return value / 12.92
            else:
                return math.pow((value + 0.055) / 1.055, 2.4)
        
        r_linear = _linearize(self.r)
        g_linear = _linearize(self.g)
        b_linear = _linearize(self.b)
        
        # ITU-R BT.709 coefficients
        return 0.2126 * r_linear + 0.7152 * g_linear + 0.0722 * b_linear
    
    def __str__(self) -> str:
        """String representation of the color."""
        return f"ColorData(RGB: {self.rgb}, HEX: {self.hex})"
    
    def __eq__(self, other) -> bool:
        """Check equality with another ColorData object."""
        if not isinstance(other, ColorData):
            return False
        return (self.r == other.r and 
                self.g == other.g and 
                self.b == other.b and 
                abs(self.alpha - other.alpha) < 0.001)