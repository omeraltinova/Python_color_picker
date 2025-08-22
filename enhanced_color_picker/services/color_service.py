"""
ColorService - Comprehensive color conversion, accessibility, and harmony service.

This service provides color operations including format conversions, WCAG compliance
checking, color harmony generation, and color blindness simulation.
"""

from typing import List, Dict, Any, Optional, Tuple
import math

from ..models.color_data import ColorData
from ..models.enums import ColorFormat, ColorBlindnessType
from ..utils.color_utils import (
    calculate_contrast_ratio, meets_wcag_aa, meets_wcag_aaa,
    get_complementary_color, get_analogous_colors, get_triadic_colors,
    get_tetradic_colors, get_monochromatic_colors, simulate_color_blindness,
    get_color_temperature, blend_colors, get_color_distance,
    is_dark_color, is_light_color, get_readable_text_color
)
from ..core.exceptions import ColorConversionError, ValidationError


class ColorHarmony:
    """Color harmony schemes and relationships."""
    
    COMPLEMENTARY = "complementary"
    ANALOGOUS = "analogous"
    TRIADIC = "triadic"
    TETRADIC = "tetradic"
    MONOCHROMATIC = "monochromatic"
    SPLIT_COMPLEMENTARY = "split_complementary"
    DOUBLE_COMPLEMENTARY = "double_complementary"


class WCAGLevel:
    """WCAG compliance levels."""
    
    AA_NORMAL = "AA_normal"      # 4.5:1 for normal text
    AA_LARGE = "AA_large"        # 3:1 for large text
    AAA_NORMAL = "AAA_normal"    # 7:1 for normal text
    AAA_LARGE = "AAA_large"      # 4.5:1 for large text


class ColorService:
    """
    Comprehensive color service for conversions, accessibility, and harmony.
    
    Features:
    - Color format conversions between RGB, HEX, HSL, HSV, CMYK
    - WCAG accessibility compliance checking
    - Color harmony and scheme generation
    - Color blindness simulation
    - Color analysis and recommendations
    """
    
    def __init__(self):
        """Initialize ColorService."""
        self._supported_formats = [format.value for format in ColorFormat]
        self._supported_blindness_types = [type.value for type in ColorBlindnessType]
    
    def convert_color(self, color: ColorData, target_format: ColorFormat) -> Dict[str, Any]:
        """
        Convert color to specified format with detailed information.
        
        Args:
            color: Source color
            target_format: Target format to convert to
            
        Returns:
            Dict containing converted color data and metadata
            
        Raises:
            ColorConversionError: If conversion fails
        """
        try:
            result = {
                'format': target_format.value,
                'original_color': color,
                'converted_at': None
            }
            
            if target_format == ColorFormat.RGB:
                result['value'] = color.rgb
                result['string'] = f"rgb({color.r}, {color.g}, {color.b})"
                result['css'] = f"rgb({color.r}, {color.g}, {color.b})"
                if color.alpha < 1.0:
                    result['string'] = f"rgba({color.r}, {color.g}, {color.b}, {color.alpha})"
                    result['css'] = result['string']
                
            elif target_format == ColorFormat.HEX:
                result['value'] = color.hex
                result['string'] = color.hex
                result['css'] = color.hex
                if color.alpha < 1.0:
                    result['value'] = color.hex_with_alpha
                    result['string'] = color.hex_with_alpha
                    result['css'] = color.hex_with_alpha
                
            elif target_format == ColorFormat.HSL:
                h, s, l = color.hsl
                result['value'] = (h, s, l)
                result['string'] = f"hsl({h:.1f}, {s:.1f}%, {l:.1f}%)"
                result['css'] = f"hsl({h:.1f}, {s:.1f}%, {l:.1f}%)"
                if color.alpha < 1.0:
                    result['string'] = f"hsla({h:.1f}, {s:.1f}%, {l:.1f}%, {color.alpha})"
                    result['css'] = result['string']
                
            elif target_format == ColorFormat.HSV:
                h, s, v = color.hsv
                result['value'] = (h, s, v)
                result['string'] = f"hsv({h:.1f}, {s:.1f}%, {v:.1f}%)"
                result['css'] = color.hex  # HSV not directly supported in CSS
                
            elif target_format == ColorFormat.CMYK:
                c, m, y, k = color.cmyk
                result['value'] = (c, m, y, k)
                result['string'] = f"cmyk({c:.1f}%, {m:.1f}%, {y:.1f}%, {k:.1f}%)"
                result['css'] = color.hex  # CMYK not directly supported in CSS
                
            else:
                raise ColorConversionError(
                    f"Unsupported target format: {target_format}",
                    target_format=target_format.value
                )
            
            return result
            
        except Exception as e:
            raise ColorConversionError(
                f"Failed to convert color to {target_format.value}: {str(e)}",
                source_format="rgb",
                target_format=target_format.value,
                color_value=color
            )
    
    def convert_to_all_formats(self, color: ColorData) -> Dict[str, Dict[str, Any]]:
        """
        Convert color to all supported formats.
        
        Args:
            color: Source color
            
        Returns:
            Dict with all format conversions
        """
        conversions = {}
        
        for format_enum in ColorFormat:
            try:
                conversions[format_enum.value] = self.convert_color(color, format_enum)
            except ColorConversionError:
                # Skip failed conversions
                continue
        
        return conversions
    
    def get_programming_formats(self, color: ColorData) -> Dict[str, str]:
        """
        Get color in various programming language formats.
        
        Args:
            color: Source color
            
        Returns:
            Dict with programming language specific formats
        """
        r, g, b = color.rgb
        alpha = color.alpha
        
        formats = {
            'python': {
                'tuple': f"({r}, {g}, {b})",
                'tuple_normalized': f"({r/255:.3f}, {g/255:.3f}, {b/255:.3f})",
                'hex': f"'{color.hex}'",
                'dict': f"{{'r': {r}, 'g': {g}, 'b': {b}}}",
            },
            'javascript': {
                'array': f"[{r}, {g}, {b}]",
                'object': f"{{r: {r}, g: {g}, b: {b}}}",
                'hex': f"'{color.hex}'",
                'rgb': f"'rgb({r}, {g}, {b})'",
            },
            'java': {
                'color': f"new Color({r}, {g}, {b})",
                'hex': f"Color.decode(\"{color.hex}\")",
                'rgb': f"new Color({r}, {g}, {b})",
            },
            'csharp': {
                'color': f"Color.FromArgb({r}, {g}, {b})",
                'hex': f"ColorTranslator.FromHtml(\"{color.hex}\")",
                'argb': f"Color.FromArgb({int(alpha*255)}, {r}, {g}, {b})",
            },
            'css': {
                'hex': color.hex,
                'rgb': f"rgb({r}, {g}, {b})",
                'hsl': f"hsl({color.hsl[0]:.1f}, {color.hsl[1]:.1f}%, {color.hsl[2]:.1f}%)",
            }
        }
        
        if alpha < 1.0:
            formats['css']['rgba'] = f"rgba({r}, {g}, {b}, {alpha})"
            formats['css']['hsla'] = f"hsla({color.hsl[0]:.1f}, {color.hsl[1]:.1f}%, {color.hsl[2]:.1f}%, {alpha})"
        
        return formats
    
    def check_wcag_compliance(self, foreground: ColorData, background: ColorData) -> Dict[str, Any]:
        """
        Check WCAG accessibility compliance between two colors.
        
        Args:
            foreground: Foreground color (usually text)
            background: Background color
            
        Returns:
            Dict with compliance information
        """
        contrast_ratio = calculate_contrast_ratio(foreground, background)
        
        compliance = {
            'contrast_ratio': contrast_ratio,
            'ratio_string': f"{contrast_ratio:.2f}:1",
            'wcag_aa': {
                'normal_text': meets_wcag_aa(foreground, background, large_text=False),
                'large_text': meets_wcag_aa(foreground, background, large_text=True),
            },
            'wcag_aaa': {
                'normal_text': meets_wcag_aaa(foreground, background, large_text=False),
                'large_text': meets_wcag_aaa(foreground, background, large_text=True),
            },
            'recommendations': []
        }
        
        # Add recommendations
        if not compliance['wcag_aa']['normal_text']:
            compliance['recommendations'].append(
                "Contrast ratio is too low for normal text (WCAG AA requires 4.5:1)"
            )
        
        if not compliance['wcag_aaa']['normal_text']:
            compliance['recommendations'].append(
                "Consider higher contrast for enhanced accessibility (WCAG AAA requires 7:1)"
            )
        
        # Suggest better colors if compliance is poor
        if contrast_ratio < 4.5:
            better_foreground = get_readable_text_color(background)
            compliance['suggestions'] = {
                'better_foreground': better_foreground,
                'better_contrast': calculate_contrast_ratio(better_foreground, background)
            }
        
        return compliance
    
    def generate_color_harmony(self, base_color: ColorData, harmony_type: str, 
                             count: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate color harmony schemes.
        
        Args:
            base_color: Base color for harmony generation
            harmony_type: Type of harmony to generate
            count: Number of colors to generate (for applicable schemes)
            
        Returns:
            Dict with harmony colors and information
        """
        try:
            harmony_colors = []
            scheme_info = {
                'type': harmony_type,
                'base_color': base_color,
                'description': '',
                'colors': []
            }
            
            if harmony_type == ColorHarmony.COMPLEMENTARY:
                harmony_colors = [get_complementary_color(base_color)]
                scheme_info['description'] = "Colors opposite on the color wheel"
                
            elif harmony_type == ColorHarmony.ANALOGOUS:
                count = count or 4
                harmony_colors = get_analogous_colors(base_color, count)
                scheme_info['description'] = "Colors adjacent on the color wheel"
                
            elif harmony_type == ColorHarmony.TRIADIC:
                harmony_colors = get_triadic_colors(base_color)
                scheme_info['description'] = "Colors evenly spaced (120°) on the color wheel"
                
            elif harmony_type == ColorHarmony.TETRADIC:
                harmony_colors = get_tetradic_colors(base_color)
                scheme_info['description'] = "Four colors evenly spaced (90°) on the color wheel"
                
            elif harmony_type == ColorHarmony.MONOCHROMATIC:
                count = count or 5
                harmony_colors = get_monochromatic_colors(base_color, count)
                scheme_info['description'] = "Variations of the same hue with different saturation/brightness"
                
            elif harmony_type == ColorHarmony.SPLIT_COMPLEMENTARY:
                # Split complementary: base + two colors adjacent to complement
                complement = get_complementary_color(base_color)
                h, s, v = complement.hsv
                color1 = ColorData.from_hsv((h + 30) % 360, s, v, complement.alpha)
                color2 = ColorData.from_hsv((h - 30) % 360, s, v, complement.alpha)
                harmony_colors = [color1, color2]
                scheme_info['description'] = "Base color plus two colors adjacent to its complement"
                
            elif harmony_type == ColorHarmony.DOUBLE_COMPLEMENTARY:
                # Double complementary: two pairs of complementary colors
                h, s, v = base_color.hsv
                color1 = ColorData.from_hsv((h + 30) % 360, s, v, base_color.alpha)
                complement1 = get_complementary_color(color1)
                complement2 = get_complementary_color(base_color)
                harmony_colors = [color1, complement1, complement2]
                scheme_info['description'] = "Two pairs of complementary colors"
                
            else:
                raise ValidationError(f"Unknown harmony type: {harmony_type}")
            
            scheme_info['colors'] = harmony_colors
            scheme_info['total_colors'] = len(harmony_colors) + 1  # +1 for base color
            
            return scheme_info
            
        except Exception as e:
            raise ColorConversionError(
                f"Failed to generate {harmony_type} harmony: {str(e)}",
                color_value=base_color
            )
    
    def simulate_color_blindness_all_types(self, color: ColorData) -> Dict[str, ColorData]:
        """
        Simulate color blindness for all types.
        
        Args:
            color: Original color
            
        Returns:
            Dict with simulated colors for each blindness type
        """
        simulations = {}
        
        for blindness_type in ColorBlindnessType:
            try:
                simulated = simulate_color_blindness(color, blindness_type)
                simulations[blindness_type.value] = simulated
            except Exception:
                # Skip failed simulations
                continue
        
        return simulations
    
    def analyze_color(self, color: ColorData) -> Dict[str, Any]:
        """
        Perform comprehensive color analysis.
        
        Args:
            color: Color to analyze
            
        Returns:
            Dict with detailed color analysis
        """
        analysis = {
            'basic_info': {
                'rgb': color.rgb,
                'hex': color.hex,
                'hsl': color.hsl,
                'hsv': color.hsv,
                'cmyk': color.cmyk,
                'alpha': color.alpha
            },
            'properties': {
                'luminance': color.get_luminance(),
                'is_dark': is_dark_color(color),
                'is_light': is_light_color(color),
                'temperature': get_color_temperature(color),
                'readable_text_color': get_readable_text_color(color)
            },
            'accessibility': {
                'contrast_with_white': calculate_contrast_ratio(color, ColorData(255, 255, 255)),
                'contrast_with_black': calculate_contrast_ratio(color, ColorData(0, 0, 0)),
                'wcag_aa_white': meets_wcag_aa(color, ColorData(255, 255, 255)),
                'wcag_aa_black': meets_wcag_aa(color, ColorData(0, 0, 0)),
            },
            'color_blindness': self.simulate_color_blindness_all_types(color),
            'harmonies': {}
        }
        
        # Generate common harmonies
        for harmony_type in [ColorHarmony.COMPLEMENTARY, ColorHarmony.ANALOGOUS, 
                           ColorHarmony.TRIADIC, ColorHarmony.MONOCHROMATIC]:
            try:
                analysis['harmonies'][harmony_type] = self.generate_color_harmony(color, harmony_type)
            except Exception:
                continue
        
        return analysis
    
    def find_similar_colors(self, target_color: ColorData, color_list: List[ColorData], 
                          max_distance: float = 50.0, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Find colors similar to target color from a list.
        
        Args:
            target_color: Color to match
            color_list: List of colors to search
            max_distance: Maximum color distance for similarity
            max_results: Maximum number of results to return
            
        Returns:
            List of similar colors with distance information
        """
        similar_colors = []
        
        for color in color_list:
            distance = get_color_distance(target_color, color)
            if distance <= max_distance:
                similar_colors.append({
                    'color': color,
                    'distance': distance,
                    'similarity_percent': max(0, (max_distance - distance) / max_distance * 100)
                })
        
        # Sort by distance (most similar first)
        similar_colors.sort(key=lambda x: x['distance'])
        
        return similar_colors[:max_results]
    
    def blend_colors(self, color1: ColorData, color2: ColorData, steps: int = 5) -> List[ColorData]:
        """
        Create a gradient between two colors.
        
        Args:
            color1: Start color
            color2: End color
            steps: Number of intermediate steps
            
        Returns:
            List of colors forming a gradient
        """
        gradient = []
        
        for i in range(steps + 2):  # +2 to include start and end colors
            ratio = i / (steps + 1)
            blended = blend_colors(color1, color2, ratio)
            gradient.append(blended)
        
        return gradient
    
    def get_color_name_approximation(self, color: ColorData) -> str:
        """
        Get approximate color name based on HSV values.
        
        Args:
            color: Color to name
            
        Returns:
            Approximate color name
        """
        h, s, v = color.hsv
        
        # Basic color naming based on hue, saturation, and value
        if v < 20:
            return "Very Dark" if s > 50 else "Black"
        elif v > 90 and s < 10:
            return "White"
        elif s < 10:
            if v > 75:
                return "Light Gray"
            elif v > 25:
                return "Gray"
            else:
                return "Dark Gray"
        
        # Color hue names
        hue_names = [
            (0, "Red"), (15, "Red-Orange"), (30, "Orange"), (45, "Yellow-Orange"),
            (60, "Yellow"), (75, "Yellow-Green"), (90, "Green"), (105, "Blue-Green"),
            (120, "Green"), (135, "Green-Cyan"), (150, "Cyan"), (165, "Blue-Cyan"),
            (180, "Cyan"), (195, "Cyan-Blue"), (210, "Blue"), (225, "Blue-Violet"),
            (240, "Blue"), (255, "Violet"), (270, "Violet"), (285, "Red-Violet"),
            (300, "Magenta"), (315, "Red-Violet"), (330, "Red"), (360, "Red")
        ]
        
        # Find closest hue name
        base_name = "Unknown"
        for hue_value, name in hue_names:
            if h <= hue_value:
                base_name = name
                break
        
        # Add saturation/value modifiers
        if s < 30:
            base_name = f"Pale {base_name}"
        elif s > 80:
            if v < 40:
                base_name = f"Dark {base_name}"
            elif v > 80:
                base_name = f"Bright {base_name}"
        
        if v < 30:
            base_name = f"Very Dark {base_name}"
        elif v > 90:
            base_name = f"Very Light {base_name}"
        
        return base_name
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported color formats."""
        return self._supported_formats.copy()
    
    def get_supported_blindness_types(self) -> List[str]:
        """Get list of supported color blindness types."""
        return self._supported_blindness_types.copy()
    
    def validate_color_format(self, format_name: str) -> bool:
        """Check if color format is supported."""
        return format_name.lower() in self._supported_formats
    
    def validate_blindness_type(self, blindness_type: str) -> bool:
        """Check if color blindness type is supported."""
        return blindness_type.lower() in self._supported_blindness_types