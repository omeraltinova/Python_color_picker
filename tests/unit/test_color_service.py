"""
Unit tests for ColorService.
"""

import unittest
from enhanced_color_picker.services.color_service import ColorService, ColorHarmony, WCAGLevel
from enhanced_color_picker.models.color_data import ColorData
from enhanced_color_picker.models.enums import ColorFormat, ColorBlindnessType
from enhanced_color_picker.core.exceptions import ColorConversionError, ValidationError


class TestColorService(unittest.TestCase):
    """Test cases for ColorService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = ColorService()
        self.red = ColorData(255, 0, 0)
        self.green = ColorData(0, 255, 0)
        self.blue = ColorData(0, 0, 255)
        self.white = ColorData(255, 255, 255)
        self.black = ColorData(0, 0, 0)
        self.gray = ColorData(128, 128, 128)
    
    def test_convert_color_to_rgb(self):
        """Test color conversion to RGB format."""
        result = self.service.convert_color(self.red, ColorFormat.RGB)
        
        self.assertEqual(result['format'], 'rgb')
        self.assertEqual(result['value'], (255, 0, 0))
        self.assertEqual(result['string'], 'rgb(255, 0, 0)')
        self.assertEqual(result['css'], 'rgb(255, 0, 0)')
        self.assertEqual(result['original_color'], self.red)
        
        # Test with alpha
        red_alpha = ColorData(255, 0, 0, 0.5)
        result_alpha = self.service.convert_color(red_alpha, ColorFormat.RGB)
        self.assertEqual(result_alpha['string'], 'rgba(255, 0, 0, 0.5)')
        self.assertEqual(result_alpha['css'], 'rgba(255, 0, 0, 0.5)')
    
    def test_convert_color_to_hex(self):
        """Test color conversion to HEX format."""
        result = self.service.convert_color(self.red, ColorFormat.HEX)
        
        self.assertEqual(result['format'], 'hex')
        self.assertEqual(result['value'], '#FF0000')
        self.assertEqual(result['string'], '#FF0000')
        self.assertEqual(result['css'], '#FF0000')
    
    def test_convert_color_to_hsl(self):
        """Test color conversion to HSL format."""
        result = self.service.convert_color(self.red, ColorFormat.HSL)
        
        self.assertEqual(result['format'], 'hsl')
        self.assertIsInstance(result['value'], tuple)
        self.assertEqual(len(result['value']), 3)
        self.assertIn('hsl(', result['string'])
        self.assertIn('hsl(', result['css'])
    
    def test_convert_color_to_hsv(self):
        """Test color conversion to HSV format."""
        result = self.service.convert_color(self.red, ColorFormat.HSV)
        
        self.assertEqual(result['format'], 'hsv')
        self.assertIsInstance(result['value'], tuple)
        self.assertEqual(len(result['value']), 3)
        self.assertIn('hsv(', result['string'])
        self.assertEqual(result['css'], self.red.hex)  # HSV not supported in CSS
    
    def test_convert_color_to_cmyk(self):
        """Test color conversion to CMYK format."""
        result = self.service.convert_color(self.red, ColorFormat.CMYK)
        
        self.assertEqual(result['format'], 'cmyk')
        self.assertIsInstance(result['value'], tuple)
        self.assertEqual(len(result['value']), 4)
        self.assertIn('cmyk(', result['string'])
        self.assertEqual(result['css'], self.red.hex)  # CMYK not supported in CSS
    
    def test_convert_to_all_formats(self):
        """Test conversion to all supported formats."""
        conversions = self.service.convert_to_all_formats(self.red)
        
        expected_formats = ['rgb', 'hex', 'hsl', 'hsv', 'cmyk']
        for format_name in expected_formats:
            self.assertIn(format_name, conversions)
            self.assertEqual(conversions[format_name]['format'], format_name)
    
    def test_get_programming_formats(self):
        """Test programming language specific formats."""
        formats = self.service.get_programming_formats(self.red)
        
        expected_languages = ['python', 'javascript', 'java', 'csharp', 'css']
        for lang in expected_languages:
            self.assertIn(lang, formats)
            self.assertIsInstance(formats[lang], dict)
        
        # Check specific format examples
        self.assertEqual(formats['python']['tuple'], '(255, 0, 0)')
        self.assertEqual(formats['javascript']['array'], '[255, 0, 0]')
        self.assertIn('Color', formats['java']['color'])
        self.assertIn('Color.FromArgb', formats['csharp']['color'])
        self.assertEqual(formats['css']['hex'], '#FF0000')
    
    def test_check_wcag_compliance(self):
        """Test WCAG accessibility compliance checking."""
        # High contrast (white on black)
        compliance = self.service.check_wcag_compliance(self.white, self.black)
        
        self.assertIn('contrast_ratio', compliance)
        self.assertIn('ratio_string', compliance)
        self.assertIn('wcag_aa', compliance)
        self.assertIn('wcag_aaa', compliance)
        self.assertIn('recommendations', compliance)
        
        self.assertGreater(compliance['contrast_ratio'], 20)  # Should be ~21:1
        self.assertTrue(compliance['wcag_aa']['normal_text'])
        self.assertTrue(compliance['wcag_aa']['large_text'])
        self.assertTrue(compliance['wcag_aaa']['normal_text'])
        self.assertTrue(compliance['wcag_aaa']['large_text'])
        
        # Low contrast (same colors)
        low_contrast = self.service.check_wcag_compliance(self.white, self.white)
        self.assertAlmostEqual(low_contrast['contrast_ratio'], 1.0, places=1)
        self.assertFalse(low_contrast['wcag_aa']['normal_text'])
        self.assertFalse(low_contrast['wcag_aaa']['normal_text'])
        
        # Should have suggestions for poor contrast
        if low_contrast['contrast_ratio'] < 4.5:
            self.assertIn('suggestions', low_contrast)
    
    def test_generate_color_harmony_complementary(self):
        """Test complementary color harmony generation."""
        harmony = self.service.generate_color_harmony(self.red, ColorHarmony.COMPLEMENTARY)
        
        self.assertEqual(harmony['type'], ColorHarmony.COMPLEMENTARY)
        self.assertEqual(harmony['base_color'], self.red)
        self.assertEqual(len(harmony['colors']), 1)
        self.assertIn('description', harmony)
        self.assertEqual(harmony['total_colors'], 2)  # base + 1 complement
        
        # Complementary of red should be cyan-ish
        complement = harmony['colors'][0]
        self.assertEqual(complement.r, 0)
        self.assertEqual(complement.g, 255)
        self.assertEqual(complement.b, 255)
    
    def test_generate_color_harmony_analogous(self):
        """Test analogous color harmony generation."""
        harmony = self.service.generate_color_harmony(self.red, ColorHarmony.ANALOGOUS, count=3)
        
        self.assertEqual(harmony['type'], ColorHarmony.ANALOGOUS)
        self.assertEqual(len(harmony['colors']), 3)
        self.assertEqual(harmony['total_colors'], 4)  # base + 3 analogous
        
        # All colors should have similar saturation and value
        base_s, base_v = self.red.hsv[1], self.red.hsv[2]
        for color in harmony['colors']:
            h, s, v = color.hsv
            self.assertAlmostEqual(s, base_s, places=1)
            self.assertAlmostEqual(v, base_v, places=1)
    
    def test_generate_color_harmony_triadic(self):
        """Test triadic color harmony generation."""
        harmony = self.service.generate_color_harmony(self.red, ColorHarmony.TRIADIC)
        
        self.assertEqual(harmony['type'], ColorHarmony.TRIADIC)
        self.assertEqual(len(harmony['colors']), 2)
        self.assertEqual(harmony['total_colors'], 3)  # base + 2 triadic
        
        # Colors should be 120 degrees apart
        base_h = self.red.hsv[0]
        expected_hues = [(base_h + 120) % 360, (base_h + 240) % 360]
        
        for i, color in enumerate(harmony['colors']):
            actual_h = color.hsv[0]
            self.assertAlmostEqual(actual_h, expected_hues[i], places=0)
    
    def test_generate_color_harmony_tetradic(self):
        """Test tetradic color harmony generation."""
        harmony = self.service.generate_color_harmony(self.red, ColorHarmony.TETRADIC)
        
        self.assertEqual(harmony['type'], ColorHarmony.TETRADIC)
        self.assertEqual(len(harmony['colors']), 3)
        self.assertEqual(harmony['total_colors'], 4)  # base + 3 tetradic
    
    def test_generate_color_harmony_monochromatic(self):
        """Test monochromatic color harmony generation."""
        harmony = self.service.generate_color_harmony(self.red, ColorHarmony.MONOCHROMATIC, count=4)
        
        self.assertEqual(harmony['type'], ColorHarmony.MONOCHROMATIC)
        self.assertEqual(len(harmony['colors']), 4)
        self.assertEqual(harmony['total_colors'], 5)  # base + 4 monochromatic
        
        # All colors should have the same hue
        base_h = self.red.hsv[0]
        for color in harmony['colors']:
            actual_h = color.hsv[0]
            self.assertAlmostEqual(actual_h, base_h, places=1)
    
    def test_generate_color_harmony_split_complementary(self):
        """Test split complementary color harmony generation."""
        harmony = self.service.generate_color_harmony(self.red, ColorHarmony.SPLIT_COMPLEMENTARY)
        
        self.assertEqual(harmony['type'], ColorHarmony.SPLIT_COMPLEMENTARY)
        self.assertEqual(len(harmony['colors']), 2)
        self.assertIn('split', harmony['description'].lower())
    
    def test_generate_color_harmony_invalid_type(self):
        """Test color harmony generation with invalid type."""
        with self.assertRaises(ValidationError):
            self.service.generate_color_harmony(self.red, "invalid_harmony_type")
    
    def test_simulate_color_blindness_all_types(self):
        """Test color blindness simulation for all types."""
        simulations = self.service.simulate_color_blindness_all_types(self.red)
        
        # Should have simulations for all blindness types
        expected_types = [type.value for type in ColorBlindnessType]
        for blindness_type in expected_types:
            if blindness_type in simulations:  # Some might be skipped on failure
                simulated = simulations[blindness_type]
                self.assertIsInstance(simulated, ColorData)
                self.assertEqual(simulated.alpha, self.red.alpha)
    
    def test_analyze_color(self):
        """Test comprehensive color analysis."""
        analysis = self.service.analyze_color(self.red)
        
        # Check required sections
        required_sections = ['basic_info', 'properties', 'accessibility', 'color_blindness', 'harmonies']
        for section in required_sections:
            self.assertIn(section, analysis)
        
        # Check basic info
        basic_info = analysis['basic_info']
        self.assertEqual(basic_info['rgb'], self.red.rgb)
        self.assertEqual(basic_info['hex'], self.red.hex)
        
        # Check properties
        properties = analysis['properties']
        self.assertIn('luminance', properties)
        self.assertIn('is_dark', properties)
        self.assertIn('is_light', properties)
        self.assertIn('temperature', properties)
        self.assertIn('readable_text_color', properties)
        
        # Check accessibility
        accessibility = analysis['accessibility']
        self.assertIn('contrast_with_white', accessibility)
        self.assertIn('contrast_with_black', accessibility)
        
        # Check color blindness simulations
        self.assertIsInstance(analysis['color_blindness'], dict)
        
        # Check harmonies
        self.assertIsInstance(analysis['harmonies'], dict)
    
    def test_find_similar_colors(self):
        """Test finding similar colors."""
        color_list = [
            ColorData(255, 50, 50),   # Light red (similar)
            ColorData(200, 0, 0),     # Dark red (similar)
            ColorData(0, 255, 0),     # Green (different)
            ColorData(0, 0, 255),     # Blue (different)
            ColorData(255, 100, 100)  # Pink (somewhat similar)
        ]
        
        similar = self.service.find_similar_colors(self.red, color_list, max_distance=100.0, max_results=3)
        
        self.assertIsInstance(similar, list)
        self.assertLessEqual(len(similar), 3)
        
        for result in similar:
            self.assertIn('color', result)
            self.assertIn('distance', result)
            self.assertIn('similarity_percent', result)
            self.assertIsInstance(result['color'], ColorData)
            self.assertGreaterEqual(result['distance'], 0)
            self.assertGreaterEqual(result['similarity_percent'], 0)
            self.assertLessEqual(result['similarity_percent'], 100)
        
        # Results should be sorted by distance (most similar first)
        if len(similar) > 1:
            for i in range(len(similar) - 1):
                self.assertLessEqual(similar[i]['distance'], similar[i + 1]['distance'])
    
    def test_blend_colors(self):
        """Test color blending/gradient creation."""
        gradient = self.service.blend_colors(self.red, self.blue, steps=3)
        
        self.assertEqual(len(gradient), 5)  # start + 3 steps + end
        self.assertEqual(gradient[0].rgb, self.red.rgb)
        self.assertEqual(gradient[-1].rgb, self.blue.rgb)
        
        # Middle colors should be blends
        for i in range(1, len(gradient) - 1):
            color = gradient[i]
            self.assertTrue(0 <= color.r <= 255)
            self.assertTrue(0 <= color.g <= 255)
            self.assertTrue(0 <= color.b <= 255)
    
    def test_get_color_name_approximation(self):
        """Test color name approximation."""
        # Test basic colors
        red_name = self.service.get_color_name_approximation(self.red)
        self.assertIn('Red', red_name)
        
        green_name = self.service.get_color_name_approximation(self.green)
        self.assertIn('Green', green_name)
        
        blue_name = self.service.get_color_name_approximation(self.blue)
        self.assertIn('Blue', blue_name)
        
        # Test special cases
        white_name = self.service.get_color_name_approximation(self.white)
        self.assertIn('White', white_name)
        
        black_name = self.service.get_color_name_approximation(self.black)
        self.assertIn('Black', black_name)
        
        gray_name = self.service.get_color_name_approximation(self.gray)
        self.assertIn('Gray', gray_name)
    
    def test_supported_formats_and_types(self):
        """Test supported formats and types queries."""
        formats = self.service.get_supported_formats()
        self.assertIsInstance(formats, list)
        self.assertIn('rgb', formats)
        self.assertIn('hex', formats)
        self.assertIn('hsl', formats)
        
        blindness_types = self.service.get_supported_blindness_types()
        self.assertIsInstance(blindness_types, list)
        self.assertIn('protanopia', blindness_types)
        self.assertIn('deuteranopia', blindness_types)
        self.assertIn('tritanopia', blindness_types)
    
    def test_validation_methods(self):
        """Test format and type validation methods."""
        self.assertTrue(self.service.validate_color_format('rgb'))
        self.assertTrue(self.service.validate_color_format('RGB'))  # Case insensitive
        self.assertFalse(self.service.validate_color_format('invalid'))
        
        self.assertTrue(self.service.validate_blindness_type('protanopia'))
        self.assertTrue(self.service.validate_blindness_type('PROTANOPIA'))  # Case insensitive
        self.assertFalse(self.service.validate_blindness_type('invalid'))


class TestColorServiceEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions for ColorService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = ColorService()
    
    def test_conversion_with_alpha(self):
        """Test color conversions with alpha channel."""
        semi_transparent = ColorData(255, 0, 0, 0.5)
        
        # All conversions should preserve alpha
        for format_enum in ColorFormat:
            result = self.service.convert_color(semi_transparent, format_enum)
            self.assertEqual(result['original_color'].alpha, 0.5)
    
    def test_extreme_color_values(self):
        """Test with extreme color values."""
        # Maximum values
        max_color = ColorData(255, 255, 255, 1.0)
        analysis = self.service.analyze_color(max_color)
        self.assertIsInstance(analysis, dict)
        
        # Minimum values
        min_color = ColorData(0, 0, 0, 0.0)
        analysis = self.service.analyze_color(min_color)
        self.assertIsInstance(analysis, dict)
    
    def test_harmony_with_edge_hues(self):
        """Test harmony generation with edge hue values."""
        # Color with hue near 360
        near_360 = ColorData.from_hsv(359, 100, 100)
        
        harmony = self.service.generate_color_harmony(near_360, ColorHarmony.COMPLEMENTARY)
        self.assertEqual(len(harmony['colors']), 1)
        
        # Hue should wrap around correctly
        complement = harmony['colors'][0]
        comp_h = complement.hsv[0]
        expected_h = (359 + 180) % 360  # Should be 179
        self.assertAlmostEqual(comp_h, expected_h, places=0)
    
    def test_empty_color_list_similarity(self):
        """Test similarity search with empty color list."""
        similar = self.service.find_similar_colors(ColorData(255, 0, 0), [], max_distance=50.0)
        self.assertEqual(len(similar), 0)
    
    def test_zero_steps_gradient(self):
        """Test gradient creation with zero steps."""
        gradient = self.service.blend_colors(ColorData(255, 0, 0), ColorData(0, 0, 255), steps=0)
        self.assertEqual(len(gradient), 2)  # Just start and end colors


if __name__ == '__main__':
    unittest.main()