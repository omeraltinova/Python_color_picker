"""
Unit tests for color utility functions.
"""

import unittest
import math
from enhanced_color_picker.utils.color_utils import (
    calculate_contrast_ratio, meets_wcag_aa, meets_wcag_aaa,
    get_complementary_color, get_analogous_colors, get_triadic_colors,
    get_tetradic_colors, get_monochromatic_colors, simulate_color_blindness,
    get_color_temperature, blend_colors, get_color_distance,
    is_dark_color, is_light_color, get_readable_text_color
)
from enhanced_color_picker.models.color_data import ColorData
from enhanced_color_picker.models.enums import ColorBlindnessType


class TestColorUtils(unittest.TestCase):
    """Test cases for color utility functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.white = ColorData(255, 255, 255)
        self.black = ColorData(0, 0, 0)
        self.red = ColorData(255, 0, 0)
        self.green = ColorData(0, 255, 0)
        self.blue = ColorData(0, 0, 255)
        self.gray = ColorData(128, 128, 128)
    
    def test_calculate_contrast_ratio(self):
        """Test contrast ratio calculation."""
        # Test maximum contrast (white vs black)
        ratio = calculate_contrast_ratio(self.white, self.black)
        self.assertAlmostEqual(ratio, 21.0, places=1)
        
        # Test minimum contrast (same colors)
        ratio = calculate_contrast_ratio(self.white, self.white)
        self.assertAlmostEqual(ratio, 1.0, places=1)
        
        # Test symmetric property
        ratio1 = calculate_contrast_ratio(self.red, self.blue)
        ratio2 = calculate_contrast_ratio(self.blue, self.red)
        self.assertAlmostEqual(ratio1, ratio2, places=2)
        
        # Test known values
        ratio = calculate_contrast_ratio(self.white, self.gray)
        self.assertGreater(ratio, 1.0)
        self.assertLess(ratio, 21.0)
    
    def test_meets_wcag_aa(self):
        """Test WCAG AA compliance checking."""
        # White on black should pass AA
        self.assertTrue(meets_wcag_aa(self.white, self.black))
        self.assertTrue(meets_wcag_aa(self.white, self.black, large_text=True))
        
        # Same colors should fail AA
        self.assertFalse(meets_wcag_aa(self.white, self.white))
        self.assertFalse(meets_wcag_aa(self.black, self.black))
        
        # Test with gray (borderline case)
        light_gray = ColorData(200, 200, 200)
        dark_gray = ColorData(50, 50, 50)
        
        # Should have better contrast than same colors
        ratio = calculate_contrast_ratio(light_gray, dark_gray)
        self.assertGreater(ratio, 1.0)
    
    def test_meets_wcag_aaa(self):
        """Test WCAG AAA compliance checking."""
        # White on black should pass AAA
        self.assertTrue(meets_wcag_aaa(self.white, self.black))
        self.assertTrue(meets_wcag_aaa(self.white, self.black, large_text=True))
        
        # Same colors should fail AAA
        self.assertFalse(meets_wcag_aaa(self.white, self.white))
        
        # AAA is stricter than AA
        medium_gray = ColorData(150, 150, 150)
        aa_result = meets_wcag_aa(self.white, medium_gray)
        aaa_result = meets_wcag_aaa(self.white, medium_gray)
        
        # If AAA passes, AA should also pass
        if aaa_result:
            self.assertTrue(aa_result)
    
    def test_get_complementary_color(self):
        """Test complementary color generation."""
        # Red's complement should be cyan-ish
        red_complement = get_complementary_color(self.red)
        self.assertEqual(red_complement.r, 0)
        self.assertEqual(red_complement.g, 255)
        self.assertEqual(red_complement.b, 255)
        
        # Test hue shift of 180 degrees
        h, s, v = self.red.hsv
        comp_h, comp_s, comp_v = red_complement.hsv
        self.assertAlmostEqual((comp_h - h) % 360, 180, places=0)
        self.assertAlmostEqual(comp_s, s, places=1)
        self.assertAlmostEqual(comp_v, v, places=1)
        
        # Test alpha preservation
        red_alpha = ColorData(255, 0, 0, 0.5)
        complement = get_complementary_color(red_alpha)
        self.assertEqual(complement.alpha, 0.5)
    
    def test_get_analogous_colors(self):
        """Test analogous color generation."""
        analogous = get_analogous_colors(self.red, count=4)
        self.assertEqual(len(analogous), 4)
        
        # All colors should have similar saturation and value
        base_s, base_v = self.red.hsv[1], self.red.hsv[2]
        for color in analogous:
            h, s, v = color.hsv
            self.assertAlmostEqual(s, base_s, places=1)
            self.assertAlmostEqual(v, base_v, places=1)
        
        # Test with different angle
        analogous_wide = get_analogous_colors(self.red, count=2, angle=60.0)
        self.assertEqual(len(analogous_wide), 2)
    
    def test_get_triadic_colors(self):
        """Test triadic color generation."""
        triadic = get_triadic_colors(self.red)
        self.assertEqual(len(triadic), 2)
        
        # Colors should be 120 degrees apart
        base_h = self.red.hsv[0]
        for i, color in enumerate(triadic):
            expected_h = (base_h + 120 * (i + 1)) % 360
            actual_h = color.hsv[0]
            self.assertAlmostEqual(actual_h, expected_h, places=0)
    
    def test_get_tetradic_colors(self):
        """Test tetradic color generation."""
        tetradic = get_tetradic_colors(self.red)
        self.assertEqual(len(tetradic), 3)
        
        # Colors should be 90 degrees apart
        base_h = self.red.hsv[0]
        expected_hues = [(base_h + 90) % 360, (base_h + 180) % 360, (base_h + 270) % 360]
        
        for i, color in enumerate(tetradic):
            actual_h = color.hsv[0]
            self.assertAlmostEqual(actual_h, expected_hues[i], places=0)
    
    def test_get_monochromatic_colors(self):
        """Test monochromatic color generation."""
        monochromatic = get_monochromatic_colors(self.red, count=5)
        self.assertEqual(len(monochromatic), 5)
        
        # All colors should have the same hue
        base_h = self.red.hsv[0]
        for color in monochromatic:
            actual_h = color.hsv[0]
            self.assertAlmostEqual(actual_h, base_h, places=1)
    
    def test_simulate_color_blindness(self):
        """Test color blindness simulation."""
        # Test all blindness types
        for blindness_type in ColorBlindnessType:
            simulated = simulate_color_blindness(self.red, blindness_type)
            
            # Result should be a valid ColorData object
            self.assertIsInstance(simulated, ColorData)
            self.assertTrue(0 <= simulated.r <= 255)
            self.assertTrue(0 <= simulated.g <= 255)
            self.assertTrue(0 <= simulated.b <= 255)
            self.assertEqual(simulated.alpha, self.red.alpha)
        
        # Test that simulation changes the color (for most types)
        protanopia = simulate_color_blindness(self.red, ColorBlindnessType.PROTANOPIA)
        self.assertNotEqual(protanopia.rgb, self.red.rgb)
    
    def test_get_color_temperature(self):
        """Test color temperature estimation."""
        # Test basic temperature estimation
        temp_red = get_color_temperature(self.red)
        temp_blue = get_color_temperature(self.blue)
        temp_white = get_color_temperature(self.white)
        
        # Red should be warmer than blue
        self.assertLess(temp_red, temp_blue)
        
        # All temperatures should be reasonable (1000K - 15000K)
        for temp in [temp_red, temp_blue, temp_white]:
            self.assertGreater(temp, 1000)
            self.assertLess(temp, 15000)
    
    def test_blend_colors(self):
        """Test color blending."""
        # Test 50/50 blend
        blended = blend_colors(self.red, self.blue, 0.5)
        expected_r = (self.red.r + self.blue.r) // 2
        expected_g = (self.red.g + self.blue.g) // 2
        expected_b = (self.red.b + self.blue.b) // 2
        
        self.assertEqual(blended.r, expected_r)
        self.assertEqual(blended.g, expected_g)
        self.assertEqual(blended.b, expected_b)
        
        # Test extreme ratios
        blend_0 = blend_colors(self.red, self.blue, 0.0)
        self.assertEqual(blend_0.rgb, self.red.rgb)
        
        blend_1 = blend_colors(self.red, self.blue, 1.0)
        self.assertEqual(blend_1.rgb, self.blue.rgb)
        
        # Test alpha blending
        red_alpha = ColorData(255, 0, 0, 0.8)
        blue_alpha = ColorData(0, 0, 255, 0.4)
        blended_alpha = blend_colors(red_alpha, blue_alpha, 0.5)
        expected_alpha = (0.8 + 0.4) / 2
        self.assertAlmostEqual(blended_alpha.alpha, expected_alpha, places=2)
    
    def test_get_color_distance(self):
        """Test color distance calculation."""
        # Distance to self should be 0
        distance = get_color_distance(self.red, self.red)
        self.assertAlmostEqual(distance, 0.0, places=1)
        
        # Distance should be symmetric
        dist1 = get_color_distance(self.red, self.blue)
        dist2 = get_color_distance(self.blue, self.red)
        self.assertAlmostEqual(dist1, dist2, places=2)
        
        # Distance should be positive
        distance = get_color_distance(self.white, self.black)
        self.assertGreater(distance, 0)
        
        # Similar colors should have smaller distance
        light_red = ColorData(255, 100, 100)
        dist_similar = get_color_distance(self.red, light_red)
        dist_different = get_color_distance(self.red, self.blue)
        self.assertLess(dist_similar, dist_different)
    
    def test_is_dark_color(self):
        """Test dark color detection."""
        self.assertTrue(is_dark_color(self.black))
        self.assertFalse(is_dark_color(self.white))
        
        # Test with custom threshold
        self.assertTrue(is_dark_color(self.gray, threshold=0.6))
        self.assertFalse(is_dark_color(self.gray, threshold=0.4))
    
    def test_is_light_color(self):
        """Test light color detection."""
        self.assertFalse(is_light_color(self.black))
        self.assertTrue(is_light_color(self.white))
        
        # Should be opposite of is_dark_color with same threshold
        threshold = 0.5
        self.assertEqual(is_light_color(self.gray, threshold), 
                        not is_dark_color(self.gray, threshold))
    
    def test_get_readable_text_color(self):
        """Test readable text color selection."""
        # White background should get black text
        text_color = get_readable_text_color(self.white)
        self.assertEqual(text_color.rgb, (0, 0, 0))
        
        # Black background should get white text
        text_color = get_readable_text_color(self.black)
        self.assertEqual(text_color.rgb, (255, 255, 255))
        
        # Result should always be black or white
        text_color = get_readable_text_color(self.red)
        self.assertIn(text_color.rgb, [(0, 0, 0), (255, 255, 255)])
        
        # Text color should have good contrast with background
        for bg_color in [self.red, self.green, self.blue, self.gray]:
            text_color = get_readable_text_color(bg_color)
            contrast = calculate_contrast_ratio(text_color, bg_color)
            self.assertGreater(contrast, 4.5)  # Should meet WCAG AA


class TestColorUtilsEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions for color utilities."""
    
    def test_extreme_values(self):
        """Test with extreme color values."""
        # Test with maximum values
        max_color = ColorData(255, 255, 255, 1.0)
        min_color = ColorData(0, 0, 0, 0.0)
        
        # Should not raise exceptions
        contrast = calculate_contrast_ratio(max_color, min_color)
        self.assertIsInstance(contrast, float)
        self.assertGreater(contrast, 0)
        
        # Test color distance with extreme values
        distance = get_color_distance(max_color, min_color)
        self.assertIsInstance(distance, float)
        self.assertGreater(distance, 0)
    
    def test_alpha_handling(self):
        """Test alpha channel handling in various functions."""
        semi_transparent = ColorData(255, 0, 0, 0.5)
        
        # Alpha should be preserved in color operations
        complement = get_complementary_color(semi_transparent)
        self.assertEqual(complement.alpha, 0.5)
        
        analogous = get_analogous_colors(semi_transparent, count=2)
        for color in analogous:
            self.assertEqual(color.alpha, 0.5)
    
    def test_hue_wraparound(self):
        """Test hue calculations that wrap around 360 degrees."""
        # Color with hue near 360
        near_360 = ColorData.from_hsv(350, 100, 100)
        
        # Complementary should wrap around correctly
        complement = get_complementary_color(near_360)
        comp_h = complement.hsv[0]
        expected_h = (350 + 180) % 360  # Should be 170
        self.assertAlmostEqual(comp_h, expected_h, places=0)
        
        # Analogous colors should also handle wraparound
        analogous = get_analogous_colors(near_360, count=2, angle=30)
        for color in analogous:
            h = color.hsv[0]
            self.assertTrue(0 <= h < 360)


if __name__ == '__main__':
    unittest.main()