"""
Color Blindness Simulation Service for Enhanced Color Picker.

This service provides functionality for:
- Simulating different types of color blindness
- Real-time color blindness preview
- Color blindness-safe palette suggestions
- Color blindness testing tools
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from PIL import Image

from ..models.color_data import ColorData
from ..models.enums import ColorBlindnessType


@dataclass
class ColorBlindnessSimulation:
    """Result of color blindness simulation"""
    original_color: ColorData
    simulated_color: ColorData
    blindness_type: ColorBlindnessType
    severity: float
    is_distinguishable: bool


@dataclass
class PaletteAccessibilityAnalysis:
    """Analysis of palette accessibility for color blind users"""
    original_palette: List[ColorData]
    problematic_pairs: List[Tuple[int, int]]  # Indices of colors that are hard to distinguish
    accessibility_score: float  # 0-1 score
    recommendations: List[str]
    safe_alternatives: List[ColorData]


class ColorBlindnessService:
    """Service for color blindness simulation and accessibility checking"""
    
    # Color blindness transformation matrices
    # Based on Brettel, Viénot and Mollon JOSA 14/10 1997
    # and Machado, Oliveira and Fernandes IEEE CG&A 29/4 2009
    
    TRANSFORMATION_MATRICES = {
        ColorBlindnessType.PROTANOPIA: {
            'matrix': np.array([
                [0.567, 0.433, 0.000],
                [0.558, 0.442, 0.000],
                [0.000, 0.242, 0.758]
            ])
        },
        ColorBlindnessType.DEUTERANOPIA: {
            'matrix': np.array([
                [0.625, 0.375, 0.000],
                [0.700, 0.300, 0.000],
                [0.000, 0.300, 0.700]
            ])
        },
        ColorBlindnessType.TRITANOPIA: {
            'matrix': np.array([
                [0.950, 0.050, 0.000],
                [0.000, 0.433, 0.567],
                [0.000, 0.475, 0.525]
            ])
        },
        ColorBlindnessType.PROTANOMALY: {
            'matrix': np.array([
                [0.817, 0.183, 0.000],
                [0.333, 0.667, 0.000],
                [0.000, 0.125, 0.875]
            ])
        },
        ColorBlindnessType.DEUTERANOMALY: {
            'matrix': np.array([
                [0.800, 0.200, 0.000],
                [0.258, 0.742, 0.000],
                [0.000, 0.142, 0.858]
            ])
        },
        ColorBlindnessType.TRITANOMALY: {
            'matrix': np.array([
                [0.967, 0.033, 0.000],
                [0.000, 0.733, 0.267],
                [0.000, 0.183, 0.817]
            ])
        }
    }
    
    def __init__(self):
        """Initialize the color blindness service"""
        pass
    
    def simulate_color_blindness(self, color: ColorData, 
                                blindness_type: ColorBlindnessType,
                                severity: float = 1.0) -> ColorBlindnessSimulation:
        """
        Simulate color blindness for a single color.
        
        Args:
            color: Original color to simulate
            blindness_type: Type of color blindness to simulate
            severity: Severity of color blindness (0.0 to 1.0)
            
        Returns:
            ColorBlindnessSimulation with original and simulated colors
        """
        # Convert RGB to linear RGB (remove gamma correction)
        linear_rgb = self._rgb_to_linear(color.rgb)
        
        # Apply color blindness transformation
        transformation_matrix = self.TRANSFORMATION_MATRICES[blindness_type]['matrix']
        
        # Apply severity factor
        if severity < 1.0:
            identity_matrix = np.eye(3)
            transformation_matrix = (
                severity * transformation_matrix + 
                (1 - severity) * identity_matrix
            )
        
        # Transform the color
        simulated_linear = np.dot(transformation_matrix, linear_rgb)
        
        # Convert back to sRGB
        simulated_rgb = self._linear_to_rgb(simulated_linear)
        
        # Clamp values to valid range
        simulated_rgb = np.clip(simulated_rgb, 0, 255).astype(int)
        
        # Create simulated color
        simulated_color = ColorData.from_rgb(*simulated_rgb)
        
        # Check if colors are distinguishable
        is_distinguishable = self._are_colors_distinguishable(color, simulated_color)
        
        return ColorBlindnessSimulation(
            original_color=color,
            simulated_color=simulated_color,
            blindness_type=blindness_type,
            severity=severity,
            is_distinguishable=is_distinguishable
        )
    
    def simulate_image_color_blindness(self, image: Image.Image, 
                                     blindness_type: ColorBlindnessType,
                                     severity: float = 1.0) -> Image.Image:
        """
        Simulate color blindness for an entire image.
        
        Args:
            image: PIL Image to simulate
            blindness_type: Type of color blindness
            severity: Severity of color blindness
            
        Returns:
            PIL Image with color blindness simulation applied
        """
        # Convert image to numpy array
        img_array = np.array(image.convert('RGB'))
        
        # Normalize to 0-1 range
        img_linear = img_array.astype(np.float32) / 255.0
        
        # Apply gamma correction to get linear RGB
        img_linear = np.where(img_linear <= 0.04045,
                             img_linear / 12.92,
                             np.power((img_linear + 0.055) / 1.055, 2.4))
        
        # Get transformation matrix
        transformation_matrix = self.TRANSFORMATION_MATRICES[blindness_type]['matrix']
        
        # Apply severity
        if severity < 1.0:
            identity_matrix = np.eye(3)
            transformation_matrix = (
                severity * transformation_matrix + 
                (1 - severity) * identity_matrix
            )
        
        # Reshape for matrix multiplication
        original_shape = img_linear.shape
        img_reshaped = img_linear.reshape(-1, 3)
        
        # Apply transformation
        img_transformed = np.dot(img_reshaped, transformation_matrix.T)
        
        # Reshape back
        img_transformed = img_transformed.reshape(original_shape)
        
        # Convert back to sRGB
        img_srgb = np.where(img_transformed <= 0.0031308,
                           img_transformed * 12.92,
                           1.055 * np.power(img_transformed, 1/2.4) - 0.055)
        
        # Convert to 8-bit and clamp
        img_final = np.clip(img_srgb * 255, 0, 255).astype(np.uint8)
        
        # Convert back to PIL Image
        return Image.fromarray(img_final, 'RGB')
    
    def _rgb_to_linear(self, rgb: Tuple[int, int, int]) -> np.ndarray:
        """Convert sRGB to linear RGB"""
        rgb_normalized = np.array(rgb) / 255.0
        
        # Apply inverse gamma correction
        linear = np.where(rgb_normalized <= 0.04045,
                         rgb_normalized / 12.92,
                         np.power((rgb_normalized + 0.055) / 1.055, 2.4))
        
        return linear
    
    def _linear_to_rgb(self, linear_rgb: np.ndarray) -> np.ndarray:
        """Convert linear RGB to sRGB"""
        # Apply gamma correction
        srgb = np.where(linear_rgb <= 0.0031308,
                       linear_rgb * 12.92,
                       1.055 * np.power(linear_rgb, 1/2.4) - 0.055)
        
        # Convert to 8-bit
        return (srgb * 255).astype(int)
    
    def _are_colors_distinguishable(self, color1: ColorData, color2: ColorData,
                                  threshold: float = 10.0) -> bool:
        """
        Check if two colors are distinguishable (using Delta E CIE76).
        
        Args:
            color1: First color
            color2: Second color
            threshold: Minimum Delta E for distinguishability
            
        Returns:
            True if colors are distinguishable
        """
        # Convert to LAB color space for better perceptual difference
        lab1 = self._rgb_to_lab(color1.rgb)
        lab2 = self._rgb_to_lab(color2.rgb)
        
        # Calculate Delta E CIE76
        delta_e = np.sqrt(
            (lab1[0] - lab2[0])**2 + 
            (lab1[1] - lab2[1])**2 + 
            (lab1[2] - lab2[2])**2
        )
        
        return delta_e >= threshold
    
    def _rgb_to_lab(self, rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
        """Convert RGB to LAB color space"""
        # First convert to XYZ
        r, g, b = [x / 255.0 for x in rgb]
        
        # Apply gamma correction
        r = ((r + 0.055) / 1.055) ** 2.4 if r > 0.04045 else r / 12.92
        g = ((g + 0.055) / 1.055) ** 2.4 if g > 0.04045 else g / 12.92
        b = ((b + 0.055) / 1.055) ** 2.4 if b > 0.04045 else b / 12.92
        
        # Convert to XYZ using sRGB matrix
        x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
        y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
        z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041
        
        # Normalize by D65 illuminant
        x = x / 0.95047
        y = y / 1.00000
        z = z / 1.08883
        
        # Convert to LAB
        fx = x**(1/3) if x > 0.008856 else (7.787 * x + 16/116)
        fy = y**(1/3) if y > 0.008856 else (7.787 * y + 16/116)
        fz = z**(1/3) if z > 0.008856 else (7.787 * z + 16/116)
        
        l = 116 * fy - 16
        a = 500 * (fx - fy)
        b = 200 * (fy - fz)
        
        return (l, a, b)
    
    def analyze_palette_accessibility(self, palette: List[ColorData],
                                    blindness_types: Optional[List[ColorBlindnessType]] = None) -> PaletteAccessibilityAnalysis:
        """
        Analyze a color palette for color blindness accessibility.
        
        Args:
            palette: List of colors to analyze
            blindness_types: Types of color blindness to test (default: all)
            
        Returns:
            PaletteAccessibilityAnalysis with accessibility information
        """
        if blindness_types is None:
            blindness_types = list(ColorBlindnessType)
        
        problematic_pairs = []
        all_simulations = {}
        
        # Simulate all colors for all blindness types
        for blindness_type in blindness_types:
            all_simulations[blindness_type] = [
                self.simulate_color_blindness(color, blindness_type)
                for color in palette
            ]
        
        # Check all color pairs for distinguishability
        for i in range(len(palette)):
            for j in range(i + 1, len(palette)):
                is_problematic = False
                
                for blindness_type in blindness_types:
                    sim_i = all_simulations[blindness_type][i]
                    sim_j = all_simulations[blindness_type][j]
                    
                    if not self._are_colors_distinguishable(
                        sim_i.simulated_color, sim_j.simulated_color
                    ):
                        is_problematic = True
                        break
                
                if is_problematic:
                    problematic_pairs.append((i, j))
        
        # Calculate accessibility score
        total_pairs = len(palette) * (len(palette) - 1) // 2
        accessibility_score = 1.0 - (len(problematic_pairs) / max(total_pairs, 1))
        
        # Generate recommendations
        recommendations = self._generate_palette_recommendations(
            palette, problematic_pairs, accessibility_score
        )
        
        # Suggest safe alternatives for problematic colors
        safe_alternatives = self._suggest_safe_alternatives(palette, problematic_pairs)
        
        return PaletteAccessibilityAnalysis(
            original_palette=palette,
            problematic_pairs=problematic_pairs,
            accessibility_score=accessibility_score,
            recommendations=recommendations,
            safe_alternatives=safe_alternatives
        )
    
    def _generate_palette_recommendations(self, palette: List[ColorData],
                                        problematic_pairs: List[Tuple[int, int]],
                                        score: float) -> List[str]:
        """Generate recommendations for palette accessibility"""
        recommendations = []
        
        if score >= 0.9:
            recommendations.append("Excellent! This palette is highly accessible for color-blind users.")
        elif score >= 0.7:
            recommendations.append("Good accessibility, but some improvements possible.")
        elif score >= 0.5:
            recommendations.append("Moderate accessibility concerns - consider adjustments.")
        else:
            recommendations.append("Poor accessibility - significant changes needed.")
        
        if problematic_pairs:
            recommendations.append(
                f"Found {len(problematic_pairs)} color pairs that may be difficult to distinguish."
            )
            recommendations.append(
                "Consider adjusting lightness or saturation of problematic colors."
            )
        
        if len(palette) > 8:
            recommendations.append(
                "Large palettes can be challenging - consider using patterns or shapes as additional indicators."
            )
        
        return recommendations
    
    def _suggest_safe_alternatives(self, palette: List[ColorData],
                                 problematic_pairs: List[Tuple[int, int]]) -> List[ColorData]:
        """Suggest color-blind safe alternatives"""
        alternatives = []
        
        # Get indices of problematic colors
        problematic_indices = set()
        for i, j in problematic_pairs:
            problematic_indices.add(i)
            problematic_indices.add(j)
        
        # Generate alternatives for problematic colors
        for idx in problematic_indices:
            original_color = palette[idx]
            h, s, l = original_color.hsl
            
            # Try different lightness values
            for lightness_adjustment in [-0.3, -0.2, 0.2, 0.3]:
                new_lightness = max(0.1, min(0.9, l + lightness_adjustment))
                alternative = self._create_color_from_hsl(h, s, new_lightness)
                
                # Check if this alternative is better
                if self._is_better_alternative(alternative, palette, idx):
                    alternatives.append(alternative)
                    break
        
        return alternatives
    
    def _create_color_from_hsl(self, h: float, s: float, l: float) -> ColorData:
        """Create ColorData from HSL values"""
        # Convert HSL to RGB
        def hsl_to_rgb(h, s, l):
            def hue_to_rgb(p, q, t):
                if t < 0:
                    t += 1
                if t > 1:
                    t -= 1
                if t < 1/6:
                    return p + (q - p) * 6 * t
                if t < 1/2:
                    return q
                if t < 2/3:
                    return p + (q - p) * (2/3 - t) * 6
                return p
            
            if s == 0:
                r = g = b = l  # achromatic
            else:
                q = l * (1 + s) if l < 0.5 else l + s - l * s
                p = 2 * l - q
                r = hue_to_rgb(p, q, h + 1/3)
                g = hue_to_rgb(p, q, h)
                b = hue_to_rgb(p, q, h - 1/3)
            
            return int(r * 255), int(g * 255), int(b * 255)
        
        r, g, b = hsl_to_rgb(h, s, l)
        return ColorData.from_rgb(r, g, b)
    
    def _is_better_alternative(self, alternative: ColorData, palette: List[ColorData],
                             original_index: int) -> bool:
        """Check if an alternative color is better than the original"""
        # Test against all major color blindness types
        test_types = [ColorBlindnessType.PROTANOPIA, ColorBlindnessType.DEUTERANOPIA, 
                     ColorBlindnessType.TRITANOPIA]
        
        for blindness_type in test_types:
            alt_sim = self.simulate_color_blindness(alternative, blindness_type)
            
            # Check distinguishability from other colors in palette
            for i, other_color in enumerate(palette):
                if i == original_index:
                    continue
                
                other_sim = self.simulate_color_blindness(other_color, blindness_type)
                
                if not self._are_colors_distinguishable(
                    alt_sim.simulated_color, other_sim.simulated_color
                ):
                    return False
        
        return True
    
    def get_color_blindness_info(self, blindness_type: ColorBlindnessType) -> Dict[str, str]:
        """Get information about a specific type of color blindness"""
        info = {
            ColorBlindnessType.PROTANOPIA: {
                "name": "Protanopia",
                "description": "Complete absence of red cone cells",
                "prevalence": "~1% of males",
                "affected_colors": "Red-green spectrum",
                "severity": "Complete"
            },
            ColorBlindnessType.DEUTERANOPIA: {
                "name": "Deuteranopia", 
                "description": "Complete absence of green cone cells",
                "prevalence": "~1% of males",
                "affected_colors": "Red-green spectrum",
                "severity": "Complete"
            },
            ColorBlindnessType.TRITANOPIA: {
                "name": "Tritanopia",
                "description": "Complete absence of blue cone cells",
                "prevalence": "~0.01% of population",
                "affected_colors": "Blue-yellow spectrum",
                "severity": "Complete"
            },
            ColorBlindnessType.PROTANOMALY: {
                "name": "Protanomaly",
                "description": "Reduced sensitivity of red cone cells",
                "prevalence": "~1% of males",
                "affected_colors": "Red-green spectrum",
                "severity": "Partial"
            },
            ColorBlindnessType.DEUTERANOMALY: {
                "name": "Deuteranomaly",
                "description": "Reduced sensitivity of green cone cells", 
                "prevalence": "~5% of males",
                "affected_colors": "Red-green spectrum",
                "severity": "Partial"
            },
            ColorBlindnessType.TRITANOMALY: {
                "name": "Tritanomaly",
                "description": "Reduced sensitivity of blue cone cells",
                "prevalence": "~0.01% of population", 
                "affected_colors": "Blue-yellow spectrum",
                "severity": "Partial"
            }
        }
        
        return info.get(blindness_type, {})
    
    def get_all_blindness_types_info(self) -> Dict[ColorBlindnessType, Dict[str, str]]:
        """Get information about all color blindness types"""
        return {
            blindness_type: self.get_color_blindness_info(blindness_type)
            for blindness_type in ColorBlindnessType
        }