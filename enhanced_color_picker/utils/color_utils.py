"""
Color utility functions for conversions, calculations, and color theory operations.
"""

import math
from typing import List, Tuple, Optional
from ..models.color_data import ColorData
from ..models.enums import ColorBlindnessType


def calculate_contrast_ratio(color1: ColorData, color2: ColorData) -> float:
    """
    Calculate WCAG contrast ratio between two colors.
    
    Args:
        color1: First color
        color2: Second color
        
    Returns:
        Contrast ratio (1:1 to 21:1)
    """
    lum1 = color1.get_luminance()
    lum2 = color2.get_luminance()
    
    # Ensure lighter color is in numerator
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    
    return (lighter + 0.05) / (darker + 0.05)


def meets_wcag_aa(color1: ColorData, color2: ColorData, large_text: bool = False) -> bool:
    """
    Check if color combination meets WCAG AA standards.
    
    Args:
        color1: First color
        color2: Second color
        large_text: True if text is large (18pt+ or 14pt+ bold)
        
    Returns:
        True if meets WCAG AA standards
    """
    ratio = calculate_contrast_ratio(color1, color2)
    threshold = 3.0 if large_text else 4.5
    return ratio >= threshold


def meets_wcag_aaa(color1: ColorData, color2: ColorData, large_text: bool = False) -> bool:
    """
    Check if color combination meets WCAG AAA standards.
    
    Args:
        color1: First color
        color2: Second color
        large_text: True if text is large (18pt+ or 14pt+ bold)
        
    Returns:
        True if meets WCAG AAA standards
    """
    ratio = calculate_contrast_ratio(color1, color2)
    threshold = 4.5 if large_text else 7.0
    return ratio >= threshold


def get_complementary_color(color: ColorData) -> ColorData:
    """
    Get the complementary color (opposite on color wheel).
    
    Args:
        color: Input color
        
    Returns:
        Complementary color
    """
    h, s, v = color.hsv
    complementary_h = (h + 180) % 360
    return ColorData.from_hsv(complementary_h, s, v, color.alpha)


def get_analogous_colors(color: ColorData, count: int = 2, angle: float = 30.0) -> List[ColorData]:
    """
    Get analogous colors (adjacent on color wheel).
    
    Args:
        color: Base color
        count: Number of analogous colors to generate
        angle: Angle step between colors (degrees)
        
    Returns:
        List of analogous colors
    """
    h, s, v = color.hsv
    colors = []
    
    for i in range(1, count + 1):
        # Generate colors on both sides
        if i % 2 == 1:  # Odd numbers: positive direction
            new_h = (h + angle * ((i + 1) // 2)) % 360
        else:  # Even numbers: negative direction
            new_h = (h - angle * (i // 2)) % 360
        
        colors.append(ColorData.from_hsv(new_h, s, v, color.alpha))
    
    return colors


def get_triadic_colors(color: ColorData) -> List[ColorData]:
    """
    Get triadic colors (120 degrees apart on color wheel).
    
    Args:
        color: Base color
        
    Returns:
        List of two triadic colors
    """
    h, s, v = color.hsv
    
    triadic1 = ColorData.from_hsv((h + 120) % 360, s, v, color.alpha)
    triadic2 = ColorData.from_hsv((h + 240) % 360, s, v, color.alpha)
    
    return [triadic1, triadic2]


def get_tetradic_colors(color: ColorData) -> List[ColorData]:
    """
    Get tetradic colors (90 degrees apart on color wheel).
    
    Args:
        color: Base color
        
    Returns:
        List of three tetradic colors
    """
    h, s, v = color.hsv
    
    colors = []
    for angle in [90, 180, 270]:
        new_h = (h + angle) % 360
        colors.append(ColorData.from_hsv(new_h, s, v, color.alpha))
    
    return colors


def get_monochromatic_colors(color: ColorData, count: int = 4) -> List[ColorData]:
    """
    Get monochromatic colors (same hue, different saturation/value).
    
    Args:
        color: Base color
        count: Number of variations to generate
        
    Returns:
        List of monochromatic colors
    """
    h, s, v = color.hsv
    colors = []
    
    # Generate variations by adjusting saturation and value
    for i in range(count):
        factor = (i + 1) / (count + 1)
        
        # Vary saturation and value
        new_s = s * (0.3 + 0.7 * factor)
        new_v = v * (0.4 + 0.6 * factor)
        
        colors.append(ColorData.from_hsv(h, new_s, new_v, color.alpha))
    
    return colors


def simulate_color_blindness(color: ColorData, blindness_type: ColorBlindnessType) -> ColorData:
    """
    Simulate color blindness effects on a color.
    
    Args:
        color: Original color
        blindness_type: Type of color blindness to simulate
        
    Returns:
        Color as seen by person with specified color blindness
    """
    r, g, b = color.r / 255.0, color.g / 255.0, color.b / 255.0
    
    # Transformation matrices for different types of color blindness
    # Based on Brettel, Viénot and Mollon JOSA 14/10 1997
    
    if blindness_type == ColorBlindnessType.PROTANOPIA:
        # Red-blind (missing L cones)
        new_r = 0.567 * r + 0.433 * g
        new_g = 0.558 * r + 0.442 * g
        new_b = 0.242 * g + 0.758 * b
        
    elif blindness_type == ColorBlindnessType.DEUTERANOPIA:
        # Green-blind (missing M cones)
        new_r = 0.625 * r + 0.375 * g
        new_g = 0.700 * r + 0.300 * g
        new_b = 0.300 * g + 0.700 * b
        
    elif blindness_type == ColorBlindnessType.TRITANOPIA:
        # Blue-blind (missing S cones)
        new_r = 0.950 * r + 0.050 * g
        new_g = 0.433 * g + 0.567 * b
        new_b = 0.475 * g + 0.525 * b
        
    elif blindness_type == ColorBlindnessType.PROTANOMALY:
        # Red-weak (anomalous L cones)
        new_r = 0.817 * r + 0.183 * g
        new_g = 0.333 * r + 0.667 * g
        new_b = 0.125 * g + 0.875 * b
        
    elif blindness_type == ColorBlindnessType.DEUTERANOMALY:
        # Green-weak (anomalous M cones)
        new_r = 0.800 * r + 0.200 * g
        new_g = 0.258 * r + 0.742 * g
        new_b = 0.142 * g + 0.858 * b
        
    elif blindness_type == ColorBlindnessType.TRITANOMALY:
        # Blue-weak (anomalous S cones)
        new_r = 0.967 * r + 0.033 * g
        new_g = 0.733 * g + 0.267 * b
        new_b = 0.183 * g + 0.817 * b
        
    else:
        # Unknown type, return original color
        return color
    
    # Convert back to 0-255 range and create new ColorData
    new_r = max(0, min(255, int(new_r * 255)))
    new_g = max(0, min(255, int(new_g * 255)))
    new_b = max(0, min(255, int(new_b * 255)))
    
    return ColorData(new_r, new_g, new_b, color.alpha)


def get_color_temperature(color: ColorData) -> float:
    """
    Estimate color temperature in Kelvin.
    
    Args:
        color: Input color
        
    Returns:
        Estimated color temperature in Kelvin
    """
    r, g, b = color.r / 255.0, color.g / 255.0, color.b / 255.0
    
    # Simple approximation based on RGB ratios
    if b == 0:
        return 6500  # Default daylight temperature
    
    ratio = r / b
    
    # Rough approximation (not scientifically accurate)
    if ratio > 1.0:
        # Warm colors
        temp = 2000 + (ratio - 1.0) * 2000
        return min(6500, temp)
    else:
        # Cool colors
        temp = 6500 + (1.0 - ratio) * 3500
        return min(10000, temp)


def blend_colors(color1: ColorData, color2: ColorData, ratio: float = 0.5) -> ColorData:
    """
    Blend two colors together.
    
    Args:
        color1: First color
        color2: Second color
        ratio: Blend ratio (0.0 = all color1, 1.0 = all color2)
        
    Returns:
        Blended color
    """
    ratio = max(0.0, min(1.0, ratio))
    inv_ratio = 1.0 - ratio
    
    new_r = int(color1.r * inv_ratio + color2.r * ratio)
    new_g = int(color1.g * inv_ratio + color2.g * ratio)
    new_b = int(color1.b * inv_ratio + color2.b * ratio)
    new_alpha = color1.alpha * inv_ratio + color2.alpha * ratio
    
    return ColorData(new_r, new_g, new_b, new_alpha)


def get_color_distance(color1: ColorData, color2: ColorData) -> float:
    """
    Calculate perceptual distance between two colors using Delta E CIE76.
    
    Args:
        color1: First color
        color2: Second color
        
    Returns:
        Color distance (0 = identical, higher = more different)
    """
    # Convert to LAB color space for perceptual distance
    lab1 = _rgb_to_lab(color1.r, color1.g, color1.b)
    lab2 = _rgb_to_lab(color2.r, color2.g, color2.b)
    
    # Calculate Delta E CIE76
    delta_l = lab1[0] - lab2[0]
    delta_a = lab1[1] - lab2[1]
    delta_b = lab1[2] - lab2[2]
    
    return math.sqrt(delta_l**2 + delta_a**2 + delta_b**2)


def _rgb_to_lab(r: int, g: int, b: int) -> Tuple[float, float, float]:
    """Convert RGB to LAB color space."""
    # Convert RGB to XYZ
    r_norm = r / 255.0
    g_norm = g / 255.0
    b_norm = b / 255.0
    
    # Apply gamma correction
    r_norm = _gamma_correct(r_norm)
    g_norm = _gamma_correct(g_norm)
    b_norm = _gamma_correct(b_norm)
    
    # Convert to XYZ using sRGB matrix
    x = r_norm * 0.4124564 + g_norm * 0.3575761 + b_norm * 0.1804375
    y = r_norm * 0.2126729 + g_norm * 0.7151522 + b_norm * 0.0721750
    z = r_norm * 0.0193339 + g_norm * 0.1191920 + b_norm * 0.9503041
    
    # Normalize by D65 illuminant
    x = x / 0.95047
    y = y / 1.00000
    z = z / 1.08883
    
    # Convert XYZ to LAB
    x = _lab_f(x)
    y = _lab_f(y)
    z = _lab_f(z)
    
    l = 116 * y - 16
    a = 500 * (x - y)
    b = 200 * (y - z)
    
    return (l, a, b)


def _gamma_correct(value: float) -> float:
    """Apply gamma correction for sRGB."""
    if value > 0.04045:
        return math.pow((value + 0.055) / 1.055, 2.4)
    else:
        return value / 12.92


def _lab_f(t: float) -> float:
    """LAB conversion function."""
    if t > 0.008856:
        return math.pow(t, 1/3)
    else:
        return (7.787 * t) + (16/116)


def is_dark_color(color: ColorData, threshold: float = 0.5) -> bool:
    """
    Determine if a color is considered dark.
    
    Args:
        color: Color to check
        threshold: Luminance threshold (0-1)
        
    Returns:
        True if color is dark
    """
    return color.get_luminance() < threshold


def is_light_color(color: ColorData, threshold: float = 0.5) -> bool:
    """
    Determine if a color is considered light.
    
    Args:
        color: Color to check
        threshold: Luminance threshold (0-1)
        
    Returns:
        True if color is light
    """
    return color.get_luminance() >= threshold


def get_readable_text_color(background: ColorData) -> ColorData:
    """
    Get the best text color (black or white) for a given background.
    
    Args:
        background: Background color
        
    Returns:
        Black or white color for optimal readability
    """
    white = ColorData(255, 255, 255)
    black = ColorData(0, 0, 0)
    
    white_contrast = calculate_contrast_ratio(background, white)
    black_contrast = calculate_contrast_ratio(background, black)
    
    return white if white_contrast > black_contrast else black