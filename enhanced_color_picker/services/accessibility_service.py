"""
Accessibility Service for WCAG compliance checking and color accessibility features.

This service provides functionality for:
- WCAG contrast ratio calculations
- AA/AAA compliance checking
- Color accessibility recommendations
- Accessibility report generation
"""

import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

from ..models.color_data import ColorData
from ..models.enums import ColorFormat


class WCAGLevel(Enum):
    """WCAG compliance levels"""
    AA_NORMAL = "AA_NORMAL"  # 4.5:1 for normal text
    AA_LARGE = "AA_LARGE"    # 3:1 for large text
    AAA_NORMAL = "AAA_NORMAL"  # 7:1 for normal text
    AAA_LARGE = "AAA_LARGE"   # 4.5:1 for large text


@dataclass
class ContrastResult:
    """Result of contrast ratio calculation"""
    ratio: float
    passes_aa_normal: bool
    passes_aa_large: bool
    passes_aaa_normal: bool
    passes_aaa_large: bool
    recommendation: str


@dataclass
class AccessibilityReport:
    """Comprehensive accessibility report for colors"""
    foreground_color: ColorData
    background_color: ColorData
    contrast_result: ContrastResult
    color_blind_safe: bool
    recommendations: List[str]
    alternative_colors: List[ColorData]


class AccessibilityService:
    """Service for WCAG compliance checking and accessibility features"""
    
    # WCAG contrast ratio thresholds
    WCAG_THRESHOLDS = {
        WCAGLevel.AA_NORMAL: 4.5,
        WCAGLevel.AA_LARGE: 3.0,
        WCAGLevel.AAA_NORMAL: 7.0,
        WCAGLevel.AAA_LARGE: 4.5
    }
    
    def __init__(self):
        """Initialize the accessibility service"""
        pass
    
    def calculate_contrast_ratio(self, color1: ColorData, color2: ColorData) -> float:
        """
        Calculate WCAG contrast ratio between two colors.
        
        Args:
            color1: First color (typically foreground)
            color2: Second color (typically background)
            
        Returns:
            Contrast ratio as float (1:1 to 21:1)
        """
        luminance1 = self._calculate_relative_luminance(color1)
        luminance2 = self._calculate_relative_luminance(color2)
        
        # Ensure lighter color is in numerator
        lighter = max(luminance1, luminance2)
        darker = min(luminance1, luminance2)
        
        # WCAG formula: (L1 + 0.05) / (L2 + 0.05)
        contrast_ratio = (lighter + 0.05) / (darker + 0.05)
        
        return round(contrast_ratio, 2)
    
    def _calculate_relative_luminance(self, color: ColorData) -> float:
        """
        Calculate relative luminance according to WCAG formula.
        
        Args:
            color: Color to calculate luminance for
            
        Returns:
            Relative luminance value (0.0 to 1.0)
        """
        # Convert RGB to 0-1 range
        r, g, b = [c / 255.0 for c in color.rgb]
        
        # Apply gamma correction
        def gamma_correct(c):
            if c <= 0.03928:
                return c / 12.92
            else:
                return pow((c + 0.055) / 1.055, 2.4)
        
        r_linear = gamma_correct(r)
        g_linear = gamma_correct(g)
        b_linear = gamma_correct(b)
        
        # Calculate luminance using WCAG coefficients
        luminance = 0.2126 * r_linear + 0.7152 * g_linear + 0.0722 * b_linear
        
        return luminance
    
    def check_wcag_compliance(self, foreground: ColorData, background: ColorData) -> ContrastResult:
        """
        Check WCAG compliance for color combination.
        
        Args:
            foreground: Foreground color
            background: Background color
            
        Returns:
            ContrastResult with compliance information
        """
        ratio = self.calculate_contrast_ratio(foreground, background)
        
        # Check compliance levels
        passes_aa_normal = ratio >= self.WCAG_THRESHOLDS[WCAGLevel.AA_NORMAL]
        passes_aa_large = ratio >= self.WCAG_THRESHOLDS[WCAGLevel.AA_LARGE]
        passes_aaa_normal = ratio >= self.WCAG_THRESHOLDS[WCAGLevel.AAA_NORMAL]
        passes_aaa_large = ratio >= self.WCAG_THRESHOLDS[WCAGLevel.AAA_LARGE]
        
        # Generate recommendation
        recommendation = self._generate_contrast_recommendation(
            ratio, passes_aa_normal, passes_aa_large, passes_aaa_normal, passes_aaa_large
        )
        
        return ContrastResult(
            ratio=ratio,
            passes_aa_normal=passes_aa_normal,
            passes_aa_large=passes_aa_large,
            passes_aaa_normal=passes_aaa_normal,
            passes_aaa_large=passes_aaa_large,
            recommendation=recommendation
        )
    
    def _generate_contrast_recommendation(self, ratio: float, aa_normal: bool, 
                                        aa_large: bool, aaa_normal: bool, aaa_large: bool) -> str:
        """Generate human-readable recommendation based on contrast ratio"""
        if aaa_normal:
            return f"Excellent contrast ({ratio}:1) - Passes all WCAG levels"
        elif aaa_large:
            return f"Very good contrast ({ratio}:1) - Passes AAA for large text, AA for all text"
        elif aa_normal:
            return f"Good contrast ({ratio}:1) - Passes AA for all text sizes"
        elif aa_large:
            return f"Acceptable contrast ({ratio}:1) - Passes AA for large text only"
        else:
            needed_ratio = self.WCAG_THRESHOLDS[WCAGLevel.AA_LARGE]
            return f"Poor contrast ({ratio}:1) - Needs at least {needed_ratio}:1 for accessibility"
    
    def suggest_accessible_colors(self, base_color: ColorData, target_background: ColorData, 
                                target_level: WCAGLevel = WCAGLevel.AA_NORMAL) -> List[ColorData]:
        """
        Suggest accessible color alternatives that meet WCAG requirements.
        
        Args:
            base_color: Starting color to modify
            target_background: Background color to contrast against
            target_level: Desired WCAG compliance level
            
        Returns:
            List of ColorData objects that meet the requirements
        """
        suggestions = []
        target_ratio = self.WCAG_THRESHOLDS[target_level]
        
        # Try different lightness adjustments
        h, s, l = base_color.hsl
        
        # Generate lighter versions
        for lightness_adjustment in [0.1, 0.2, 0.3, 0.4, 0.5]:
            new_lightness = min(1.0, l + lightness_adjustment)
            suggested_color = self._create_color_from_hsl(h, s, new_lightness)
            
            if self.calculate_contrast_ratio(suggested_color, target_background) >= target_ratio:
                suggestions.append(suggested_color)
        
        # Generate darker versions
        for lightness_adjustment in [0.1, 0.2, 0.3, 0.4, 0.5]:
            new_lightness = max(0.0, l - lightness_adjustment)
            suggested_color = self._create_color_from_hsl(h, s, new_lightness)
            
            if self.calculate_contrast_ratio(suggested_color, target_background) >= target_ratio:
                suggestions.append(suggested_color)
        
        # Remove duplicates and limit results
        unique_suggestions = []
        seen_colors = set()
        
        for color in suggestions:
            color_key = color.hex
            if color_key not in seen_colors:
                seen_colors.add(color_key)
                unique_suggestions.append(color)
        
        return unique_suggestions[:5]  # Return top 5 suggestions
    
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
    
    def generate_accessibility_report(self, foreground: ColorData, 
                                    background: ColorData) -> AccessibilityReport:
        """
        Generate comprehensive accessibility report for color combination.
        
        Args:
            foreground: Foreground color
            background: Background color
            
        Returns:
            AccessibilityReport with detailed analysis
        """
        contrast_result = self.check_wcag_compliance(foreground, background)
        
        # Check if colors are color-blind safe
        color_blind_safe = self._is_color_blind_safe(foreground, background)
        
        # Generate recommendations
        recommendations = self._generate_accessibility_recommendations(
            contrast_result, color_blind_safe
        )
        
        # Suggest alternative colors if needed
        alternative_colors = []
        if not contrast_result.passes_aa_normal:
            alternative_colors = self.suggest_accessible_colors(
                foreground, background, WCAGLevel.AA_NORMAL
            )
        
        return AccessibilityReport(
            foreground_color=foreground,
            background_color=background,
            contrast_result=contrast_result,
            color_blind_safe=color_blind_safe,
            recommendations=recommendations,
            alternative_colors=alternative_colors
        )
    
    def _is_color_blind_safe(self, color1: ColorData, color2: ColorData) -> bool:
        """
        Check if color combination is safe for color-blind users.
        This is a simplified check based on luminance difference.
        """
        luminance_diff = abs(
            self._calculate_relative_luminance(color1) - 
            self._calculate_relative_luminance(color2)
        )
        
        # Colors with significant luminance difference are generally safer
        return luminance_diff > 0.3
    
    def _generate_accessibility_recommendations(self, contrast_result: ContrastResult, 
                                              color_blind_safe: bool) -> List[str]:
        """Generate list of accessibility recommendations"""
        recommendations = []
        
        if not contrast_result.passes_aa_normal:
            recommendations.append(
                "Increase contrast ratio to meet WCAG AA standards (4.5:1 minimum)"
            )
        
        if not contrast_result.passes_aaa_normal:
            recommendations.append(
                "Consider increasing contrast for AAA compliance (7:1 for enhanced accessibility)"
            )
        
        if not color_blind_safe:
            recommendations.append(
                "Color combination may be difficult for color-blind users - consider adding patterns or icons"
            )
        
        if contrast_result.passes_aa_large and not contrast_result.passes_aa_normal:
            recommendations.append(
                "Use larger text sizes (18pt+ or 14pt+ bold) with this color combination"
            )
        
        return recommendations
    
    def get_wcag_compliance_summary(self, contrast_result: ContrastResult) -> Dict[str, Any]:
        """
        Get a summary of WCAG compliance status.
        
        Args:
            contrast_result: ContrastResult to summarize
            
        Returns:
            Dictionary with compliance summary
        """
        return {
            "contrast_ratio": contrast_result.ratio,
            "compliance": {
                "AA": {
                    "normal_text": contrast_result.passes_aa_normal,
                    "large_text": contrast_result.passes_aa_large
                },
                "AAA": {
                    "normal_text": contrast_result.passes_aaa_normal,
                    "large_text": contrast_result.passes_aaa_large
                }
            },
            "overall_grade": self._calculate_overall_grade(contrast_result),
            "recommendation": contrast_result.recommendation
        }
    
    def _calculate_overall_grade(self, contrast_result: ContrastResult) -> str:
        """Calculate overall accessibility grade"""
        if contrast_result.passes_aaa_normal:
            return "AAA"
        elif contrast_result.passes_aa_normal:
            return "AA"
        elif contrast_result.passes_aa_large:
            return "AA (Large Text Only)"
        else:
            return "Fail"