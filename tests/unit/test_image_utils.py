"""
Unit tests for image processing utilities.
"""

import unittest
import tempfile
import os
from pathlib import Path
from PIL import Image
import numpy as np

from enhanced_color_picker.utils.image_utils import (
    validate_image_format, load_image_with_validation, resize_image_with_quality,
    extract_dominant_colors, get_pixel_color_safe, calculate_average_color,
    create_color_histogram, enhance_image_contrast, apply_gaussian_blur,
    get_image_brightness, detect_edges, get_image_statistics
)
from enhanced_color_picker.models.image_data import ImageData
from enhanced_color_picker.models.color_data import ColorData


class TestImageUtils(unittest.TestCase):
    """Test cases for image utility functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for test images
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test images
        self.test_images = {}
        
        # Small RGB image
        rgb_image = Image.new('RGB', (10, 10), color=(255, 0, 0))
        self.test_images['rgb'] = os.path.join(self.temp_dir, 'test_rgb.png')
        rgb_image.save(self.test_images['rgb'])
        
        # RGBA image with transparency
        rgba_image = Image.new('RGBA', (10, 10), color=(0, 255, 0, 128))
        self.test_images['rgba'] = os.path.join(self.temp_dir, 'test_rgba.png')
        rgba_image.save(self.test_images['rgba'])
        
        # Grayscale image
        gray_image = Image.new('L', (10, 10), color=128)
        self.test_images['gray'] = os.path.join(self.temp_dir, 'test_gray.png')
        gray_image.save(self.test_images['gray'])
        
        # Multi-color image for testing dominant colors
        multi_image = Image.new('RGB', (20, 20))
        pixels = []
        for y in range(20):
            for x in range(20):
                if x < 10:
                    pixels.append((255, 0, 0))  # Red half
                else:
                    pixels.append((0, 0, 255))  # Blue half
        multi_image.putdata(pixels)
        self.test_images['multi'] = os.path.join(self.temp_dir, 'test_multi.png')
        multi_image.save(self.test_images['multi'])
        
        # Create ImageData objects
        self.rgb_image_data = ImageData.from_file(self.test_images['rgb'])
        self.rgba_image_data = ImageData.from_file(self.test_images['rgba'])
        self.multi_image_data = ImageData.from_file(self.test_images['multi'])
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary files
        for file_path in self.test_images.values():
            if os.path.exists(file_path):
                os.remove(file_path)
        os.rmdir(self.temp_dir)
    
    def test_validate_image_format(self):
        """Test image format validation."""
        # Valid formats
        self.assertTrue(validate_image_format(self.test_images['rgb']))
        
        # Create files with different extensions
        valid_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp']
        for ext in valid_extensions:
            test_file = os.path.join(self.temp_dir, f'test{ext}')
            # Create empty file
            with open(test_file, 'w') as f:
                f.write('')
            self.assertTrue(validate_image_format(test_file))
            os.remove(test_file)
        
        # Invalid format
        invalid_file = os.path.join(self.temp_dir, 'test.txt')
        with open(invalid_file, 'w') as f:
            f.write('not an image')
        self.assertFalse(validate_image_format(invalid_file))
        os.remove(invalid_file)
        
        # Non-existent file
        self.assertFalse(validate_image_format('nonexistent.png'))
    
    def test_load_image_with_validation(self):
        """Test image loading with validation."""
        # Valid image
        image_data = load_image_with_validation(self.test_images['rgb'])
        self.assertIsInstance(image_data, ImageData)
        self.assertEqual(image_data.width, 10)
        self.assertEqual(image_data.height, 10)
        
        # Non-existent file
        with self.assertRaises(FileNotFoundError):
            load_image_with_validation('nonexistent.png')
        
        # Invalid format
        invalid_file = os.path.join(self.temp_dir, 'test.txt')
        with open(invalid_file, 'w') as f:
            f.write('not an image')
        
        with self.assertRaises(ValueError):
            load_image_with_validation(invalid_file)
        
        os.remove(invalid_file)
    
    def test_resize_image_with_quality(self):
        """Test image resizing with quality preservation."""
        # Test basic resize
        resized = resize_image_with_quality(self.rgb_image_data, (20, 20), maintain_aspect=False)
        self.assertEqual(resized.width, 20)
        self.assertEqual(resized.height, 20)
        
        # Test aspect ratio maintenance
        resized_aspect = resize_image_with_quality(self.rgb_image_data, (30, 20), maintain_aspect=True)
        self.assertEqual(resized_aspect.width, 20)  # Should fit to height
        self.assertEqual(resized_aspect.height, 20)
        
        # Test with different resampling
        resized_nearest = resize_image_with_quality(
            self.rgb_image_data, (20, 20), 
            maintain_aspect=False, 
            resample=Image.Resampling.NEAREST
        )
        self.assertEqual(resized_nearest.width, 20)
        self.assertEqual(resized_nearest.height, 20)
    
    def test_extract_dominant_colors(self):
        """Test dominant color extraction."""
        # Test with multi-color image
        dominant = extract_dominant_colors(self.multi_image_data, num_colors=2)
        self.assertIsInstance(dominant, list)
        self.assertLessEqual(len(dominant), 2)
        
        for color in dominant:
            self.assertIsInstance(color, ColorData)
            self.assertTrue(0 <= color.r <= 255)
            self.assertTrue(0 <= color.g <= 255)
            self.assertTrue(0 <= color.b <= 255)
        
        # Test with single color image
        dominant_single = extract_dominant_colors(self.rgb_image_data, num_colors=3)
        self.assertIsInstance(dominant_single, list)
        self.assertGreater(len(dominant_single), 0)
        
        # Test with different quality settings
        dominant_fast = extract_dominant_colors(self.multi_image_data, num_colors=2, quality=20)
        self.assertIsInstance(dominant_fast, list)
    
    def test_get_pixel_color_safe(self):
        """Test safe pixel color retrieval."""
        # Valid coordinates
        color = get_pixel_color_safe(self.rgb_image_data, 5, 5)
        self.assertIsInstance(color, ColorData)
        
        # Invalid coordinates (out of bounds)
        color_invalid = get_pixel_color_safe(self.rgb_image_data, 100, 100)
        self.assertIsNone(color_invalid)
        
        # Negative coordinates
        color_negative = get_pixel_color_safe(self.rgb_image_data, -1, -1)
        self.assertIsNone(color_negative)
        
        # Edge coordinates
        color_edge = get_pixel_color_safe(self.rgb_image_data, 9, 9)  # Last valid pixel
        self.assertIsInstance(color_edge, ColorData)
        
        color_beyond = get_pixel_color_safe(self.rgb_image_data, 10, 10)  # Just beyond
        self.assertIsNone(color_beyond)
    
    def test_calculate_average_color(self):
        """Test average color calculation."""
        # Test full image average
        avg_color = calculate_average_color(self.rgb_image_data)
        self.assertIsInstance(avg_color, ColorData)
        
        # For a red image, average should be red-ish
        self.assertGreater(avg_color.r, avg_color.g)
        self.assertGreater(avg_color.r, avg_color.b)
        
        # Test with region
        region = (0, 0, 5, 5)  # Top-left quarter
        avg_region = calculate_average_color(self.rgb_image_data, region)
        self.assertIsInstance(avg_region, ColorData)
        
        # Test with multi-color image
        avg_multi = calculate_average_color(self.multi_image_data)
        self.assertIsInstance(avg_multi, ColorData)
        # Should be somewhere between red and blue
        self.assertGreater(avg_multi.r, 0)
        self.assertGreater(avg_multi.b, 0)
    
    def test_create_color_histogram(self):
        """Test color histogram creation."""
        histogram = create_color_histogram(self.rgb_image_data)
        
        # Should have RGB channels
        self.assertIn('r', histogram)
        self.assertIn('g', histogram)
        self.assertIn('b', histogram)
        
        # Each channel should have 256 bins by default
        self.assertEqual(len(histogram['r']), 256)
        self.assertEqual(len(histogram['g']), 256)
        self.assertEqual(len(histogram['b']), 256)
        
        # All values should be non-negative integers
        for channel in ['r', 'g', 'b']:
            for value in histogram[channel]:
                self.assertIsInstance(value, int)
                self.assertGreaterEqual(value, 0)
        
        # Test with different bin count
        histogram_64 = create_color_histogram(self.rgb_image_data, bins=64)
        for channel in ['r', 'g', 'b']:
            self.assertEqual(len(histogram_64[channel]), 64)
    
    def test_enhance_image_contrast(self):
        """Test image contrast enhancement."""
        enhanced = enhance_image_contrast(self.rgb_image_data, factor=1.5)
        self.assertIsInstance(enhanced, ImageData)
        self.assertEqual(enhanced.width, self.rgb_image_data.width)
        self.assertEqual(enhanced.height, self.rgb_image_data.height)
        
        # Test with factor = 1.0 (no change)
        no_change = enhance_image_contrast(self.rgb_image_data, factor=1.0)
        self.assertIsInstance(no_change, ImageData)
        
        # Test with factor < 1.0 (reduce contrast)
        reduced = enhance_image_contrast(self.rgb_image_data, factor=0.5)
        self.assertIsInstance(reduced, ImageData)
    
    def test_apply_gaussian_blur(self):
        """Test Gaussian blur application."""
        blurred = apply_gaussian_blur(self.rgb_image_data, radius=1.0)
        self.assertIsInstance(blurred, ImageData)
        self.assertEqual(blurred.width, self.rgb_image_data.width)
        self.assertEqual(blurred.height, self.rgb_image_data.height)
        
        # Test with different radius
        blurred_more = apply_gaussian_blur(self.rgb_image_data, radius=2.0)
        self.assertIsInstance(blurred_more, ImageData)
        
        # Test with zero radius
        blurred_zero = apply_gaussian_blur(self.rgb_image_data, radius=0.0)
        self.assertIsInstance(blurred_zero, ImageData)
    
    def test_get_image_brightness(self):
        """Test image brightness calculation."""
        brightness = get_image_brightness(self.rgb_image_data)
        self.assertIsInstance(brightness, float)
        self.assertGreaterEqual(brightness, 0.0)
        self.assertLessEqual(brightness, 1.0)
        
        # Test with different images
        brightness_rgba = get_image_brightness(self.rgba_image_data)
        self.assertIsInstance(brightness_rgba, float)
        self.assertGreaterEqual(brightness_rgba, 0.0)
        self.assertLessEqual(brightness_rgba, 1.0)
        
        # Create a white image for testing
        white_image = Image.new('RGB', (10, 10), color=(255, 255, 255))
        white_path = os.path.join(self.temp_dir, 'white.png')
        white_image.save(white_path)
        white_data = ImageData.from_file(white_path)
        
        white_brightness = get_image_brightness(white_data)
        self.assertGreater(white_brightness, 0.9)  # Should be very bright
        
        os.remove(white_path)
    
    def test_detect_edges(self):
        """Test edge detection."""
        edges = detect_edges(self.rgb_image_data)
        self.assertIsInstance(edges, ImageData)
        self.assertEqual(edges.width, self.rgb_image_data.width)
        self.assertEqual(edges.height, self.rgb_image_data.height)
        self.assertEqual(edges.mode, 'RGB')  # Should be converted back to RGB
    
    def test_get_image_statistics(self):
        """Test comprehensive image statistics."""
        stats = get_image_statistics(self.rgb_image_data)
        
        # Check required fields
        required_fields = [
            'width', 'height', 'aspect_ratio', 'total_pixels',
            'format', 'mode', 'has_transparency', 'file_size',
            'memory_usage', 'brightness'
        ]
        
        for field in required_fields:
            self.assertIn(field, stats)
        
        # Check values
        self.assertEqual(stats['width'], 10)
        self.assertEqual(stats['height'], 10)
        self.assertEqual(stats['total_pixels'], 100)
        self.assertIsInstance(stats['brightness'], float)
        
        # Optional fields might be present
        if 'average_color' in stats:
            self.assertIn('rgb', stats['average_color'])
            self.assertIn('hex', stats['average_color'])
        
        if 'dominant_colors' in stats:
            self.assertIsInstance(stats['dominant_colors'], list)


class TestImageUtilsEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions for image utilities."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a 1x1 pixel image for edge case testing
        tiny_image = Image.new('RGB', (1, 1), color=(128, 128, 128))
        self.tiny_path = os.path.join(self.temp_dir, 'tiny.png')
        tiny_image.save(self.tiny_path)
        self.tiny_data = ImageData.from_file(self.tiny_path)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.tiny_path):
            os.remove(self.tiny_path)
        os.rmdir(self.temp_dir)
    
    def test_tiny_image_processing(self):
        """Test processing of very small images."""
        # Should handle 1x1 images without errors
        dominant = extract_dominant_colors(self.tiny_data, num_colors=1)
        self.assertIsInstance(dominant, list)
        self.assertGreater(len(dominant), 0)
        
        avg_color = calculate_average_color(self.tiny_data)
        self.assertIsInstance(avg_color, ColorData)
        
        brightness = get_image_brightness(self.tiny_data)
        self.assertIsInstance(brightness, float)
    
    def test_invalid_regions(self):
        """Test with invalid region specifications."""
        # Region larger than image
        large_region = (0, 0, 100, 100)
        
        # Should handle gracefully or raise appropriate error
        try:
            avg_color = calculate_average_color(self.tiny_data, large_region)
            self.assertIsInstance(avg_color, ColorData)
        except ValueError:
            pass  # Acceptable to raise ValueError for invalid region
    
    def test_extreme_resize_values(self):
        """Test resizing with extreme values."""
        # Very small resize
        tiny_resize = resize_image_with_quality(self.tiny_data, (1, 1))
        self.assertEqual(tiny_resize.width, 1)
        self.assertEqual(tiny_resize.height, 1)
        
        # Large resize (should work but might be slow)
        large_resize = resize_image_with_quality(self.tiny_data, (100, 100))
        self.assertEqual(large_resize.width, 100)
        self.assertEqual(large_resize.height, 100)
    
    def test_histogram_edge_cases(self):
        """Test histogram creation edge cases."""
        # Test with different bin counts
        for bins in [1, 2, 16, 64, 128, 512]:
            histogram = create_color_histogram(self.tiny_data, bins=bins)
            for channel in ['r', 'g', 'b']:
                self.assertEqual(len(histogram[channel]), bins)


if __name__ == '__main__':
    unittest.main()