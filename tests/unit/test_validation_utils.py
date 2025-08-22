"""
Unit tests for validation utilities.
"""

import unittest
import tempfile
import os
import json
from pathlib import Path
from PIL import Image

from enhanced_color_picker.utils.validation_utils import (
    FileValidator, InputValidator, MemoryLimitEnforcer,
    get_file_validator, get_input_validator, get_memory_enforcer,
    SecurityConfig
)
from enhanced_color_picker.models.enums import ColorFormat
from enhanced_color_picker.core.exceptions import ValidationError, FileOperationError


class TestFileValidator(unittest.TestCase):
    """Test cases for file validation utilities."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.validator = FileValidator()
        
        # Create test files
        self.test_files = {}
        
        # Valid image file
        image = Image.new('RGB', (10, 10), color=(255, 0, 0))
        self.test_files['valid_image'] = os.path.join(self.temp_dir, 'test.png')
        image.save(self.test_files['valid_image'])
        
        # Valid JSON palette
        palette_data = {
            "name": "Test Palette",
            "colors": [
                {"rgb": [255, 0, 0], "hex": "#FF0000"},
                {"rgb": [0, 255, 0], "hex": "#00FF00"}
            ],
            "created_at": "2024-01-01T00:00:00",
            "modified_at": "2024-01-01T00:00:00"
        }
        self.test_files['valid_palette'] = os.path.join(self.temp_dir, 'palette.json')
        with open(self.test_files['valid_palette'], 'w') as f:
            json.dump(palette_data, f)
        
        # Invalid file (wrong extension)
        self.test_files['invalid_ext'] = os.path.join(self.temp_dir, 'test.exe')
        with open(self.test_files['invalid_ext'], 'w') as f:
            f.write('malicious content')
        
        # Empty file
        self.test_files['empty'] = os.path.join(self.temp_dir, 'empty.png')
        with open(self.test_files['empty'], 'w') as f:
            pass
    
    def tearDown(self):
        """Clean up test fixtures."""
        for file_path in self.test_files.values():
            if os.path.exists(file_path):
                os.remove(file_path)
        os.rmdir(self.temp_dir)
    
    def test_validate_image_file_success(self):
        """Test successful image file validation."""
        result = self.validator.validate_image_file(self.test_files['valid_image'])
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['file_path'], self.test_files['valid_image'])
        self.assertGreater(result['file_size'], 0)
        self.assertIn('mime_type', result)
        self.assertIn('image_info', result)
        
        # Check image info
        image_info = result['image_info']
        self.assertEqual(image_info['width'], 10)
        self.assertEqual(image_info['height'], 10)
        self.assertIn('mode', image_info)
        self.assertIn('format', image_info)
    
    def test_validate_image_file_not_found(self):
        """Test image validation with non-existent file."""
        with self.assertRaises(FileOperationError):
            self.validator.validate_image_file('nonexistent.png')
    
    def test_validate_image_file_invalid_extension(self):
        """Test image validation with invalid extension."""
        with self.assertRaises(ValidationError) as context:
            self.validator.validate_image_file(self.test_files['invalid_ext'])
        
        self.assertIn('extension', str(context.exception).lower())
    
    def test_validate_image_file_empty(self):
        """Test image validation with empty file."""
        with self.assertRaises(ValidationError):
            self.validator.validate_image_file(self.test_files['empty'])
    
    def test_validate_palette_file_success(self):
        """Test successful palette file validation."""
        result = self.validator.validate_palette_file(self.test_files['valid_palette'])
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['file_path'], self.test_files['valid_palette'])
        self.assertGreater(result['file_size'], 0)
        self.assertIn('palette_data', result)
        
        # Check palette data
        palette_data = result['palette_data']
        self.assertIn('colors', palette_data)
        self.assertIsInstance(palette_data['colors'], list)
    
    def test_validate_palette_file_invalid_json(self):
        """Test palette validation with invalid JSON."""
        invalid_json_file = os.path.join(self.temp_dir, 'invalid.json')
        with open(invalid_json_file, 'w') as f:
            f.write('invalid json content {')
        
        with self.assertRaises(ValidationError):
            self.validator.validate_palette_file(invalid_json_file)
        
        os.remove(invalid_json_file)
    
    def test_validate_config_file_success(self):
        """Test successful config file validation."""
        config_data = {"theme": "dark", "language": "en"}
        config_file = os.path.join(self.temp_dir, 'config.json')
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        result = self.validator.validate_config_file(config_file)
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['file_path'], config_file)
        self.assertIn('config_data', result)
        
        os.remove(config_file)
    
    def test_security_config_constants(self):
        """Test security configuration constants."""
        config = SecurityConfig()
        
        # Check that limits are reasonable
        self.assertGreater(config.MAX_IMAGE_SIZE, 0)
        self.assertGreater(config.MAX_PALETTE_SIZE, 0)
        self.assertGreater(config.MAX_CONFIG_SIZE, 0)
        self.assertGreater(config.MAX_IMAGE_PIXELS, 0)
        self.assertGreater(config.MAX_PALETTE_COLORS, 0)
        
        # Check that extension sets are not empty
        self.assertGreater(len(config.ALLOWED_IMAGE_EXTENSIONS), 0)
        self.assertGreater(len(config.ALLOWED_PALETTE_EXTENSIONS), 0)
        self.assertGreater(len(config.DANGEROUS_EXTENSIONS), 0)
    
    def test_path_traversal_protection(self):
        """Test path traversal attack protection."""
        # Create a file with suspicious path
        suspicious_paths = [
            '../../../etc/passwd',
            '..\\..\\windows\\system32\\config',
            '/etc/shadow',
            'C:\\Windows\\System32\\config'
        ]
        
        for suspicious_path in suspicious_paths:
            with self.assertRaises(ValidationError):
                # This should fail due to path traversal protection
                self.validator._check_path_traversal(Path(suspicious_path))


class TestInputValidator(unittest.TestCase):
    """Test cases for input validation utilities."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = InputValidator()
    
    def test_validate_rgb_color(self):
        """Test RGB color validation."""
        # Valid RGB values
        self.assertTrue(self.validator.validate_color_value([255, 0, 0], ColorFormat.RGB))
        self.assertTrue(self.validator.validate_color_value([0, 255, 0], ColorFormat.RGB))
        self.assertTrue(self.validator.validate_color_value([0, 0, 255], ColorFormat.RGB))
        self.assertTrue(self.validator.validate_color_value([128, 128, 128], ColorFormat.RGB))
        
        # Invalid RGB values
        with self.assertRaises(ValidationError):
            self.validator.validate_color_value([256, 0, 0], ColorFormat.RGB)  # Out of range
        
        with self.assertRaises(ValidationError):
            self.validator.validate_color_value([-1, 0, 0], ColorFormat.RGB)  # Negative
        
        with self.assertRaises(ValidationError):
            self.validator.validate_color_value([255, 0], ColorFormat.RGB)  # Wrong length
        
        with self.assertRaises(ValidationError):
            self.validator.validate_color_value("255,0,0", ColorFormat.RGB)  # Wrong type
    
    def test_validate_hex_color(self):
        """Test HEX color validation."""
        # Valid HEX values
        self.assertTrue(self.validator.validate_color_value("#FF0000", ColorFormat.HEX))
        self.assertTrue(self.validator.validate_color_value("#00FF00", ColorFormat.HEX))
        self.assertTrue(self.validator.validate_color_value("#0000FF", ColorFormat.HEX))
        self.assertTrue(self.validator.validate_color_value("FF0000", ColorFormat.HEX))  # Without #
        self.assertTrue(self.validator.validate_color_value("#F00", ColorFormat.HEX))  # Short form
        self.assertTrue(self.validator.validate_color_value("F00", ColorFormat.HEX))  # Short without #
        
        # Invalid HEX values
        with self.assertRaises(ValidationError):
            self.validator.validate_color_value("#GG0000", ColorFormat.HEX)  # Invalid characters
        
        with self.assertRaises(ValidationError):
            self.validator.validate_color_value("#FF00", ColorFormat.HEX)  # Wrong length
        
        with self.assertRaises(ValidationError):
            self.validator.validate_color_value(255, ColorFormat.HEX)  # Wrong type
    
    def test_validate_hsl_color(self):
        """Test HSL color validation."""
        # Valid HSL values
        self.assertTrue(self.validator.validate_color_value([0, 100, 50], ColorFormat.HSL))
        self.assertTrue(self.validator.validate_color_value([180, 50, 75], ColorFormat.HSL))
        self.assertTrue(self.validator.validate_color_value([360, 0, 100], ColorFormat.HSL))
        
        # Invalid HSL values
        with self.assertRaises(ValidationError):
            self.validator.validate_color_value([361, 50, 50], ColorFormat.HSL)  # Hue out of range
        
        with self.assertRaises(ValidationError):
            self.validator.validate_color_value([180, 101, 50], ColorFormat.HSL)  # Saturation out of range
        
        with self.assertRaises(ValidationError):
            self.validator.validate_color_value([180, 50, 101], ColorFormat.HSL)  # Lightness out of range
    
    def test_validate_hsv_color(self):
        """Test HSV color validation."""
        # Valid HSV values
        self.assertTrue(self.validator.validate_color_value([0, 100, 100], ColorFormat.HSV))
        self.assertTrue(self.validator.validate_color_value([180, 50, 75], ColorFormat.HSV))
        
        # Invalid HSV values
        with self.assertRaises(ValidationError):
            self.validator.validate_color_value([361, 50, 50], ColorFormat.HSV)  # Hue out of range
        
        with self.assertRaises(ValidationError):
            self.validator.validate_color_value([180, 101, 50], ColorFormat.HSV)  # Saturation out of range
    
    def test_validate_cmyk_color(self):
        """Test CMYK color validation."""
        # Valid CMYK values
        self.assertTrue(self.validator.validate_color_value([0, 100, 100, 0], ColorFormat.CMYK))
        self.assertTrue(self.validator.validate_color_value([50, 50, 50, 25], ColorFormat.CMYK))
        
        # Invalid CMYK values
        with self.assertRaises(ValidationError):
            self.validator.validate_color_value([101, 50, 50, 0], ColorFormat.CMYK)  # Out of range
        
        with self.assertRaises(ValidationError):
            self.validator.validate_color_value([50, 50, 50], ColorFormat.CMYK)  # Wrong length
    
    def test_validate_coordinates(self):
        """Test coordinate validation."""
        # Valid coordinates
        self.assertTrue(self.validator.validate_coordinates(10, 20))
        self.assertTrue(self.validator.validate_coordinates(0, 0))
        self.assertTrue(self.validator.validate_coordinates(10.5, 20.5))
        
        # With max values
        self.assertTrue(self.validator.validate_coordinates(10, 20, max_x=100, max_y=100))
        
        # Invalid coordinates
        with self.assertRaises(ValidationError):
            self.validator.validate_coordinates(-1, 10)  # Negative x
        
        with self.assertRaises(ValidationError):
            self.validator.validate_coordinates(10, -1)  # Negative y
        
        with self.assertRaises(ValidationError):
            self.validator.validate_coordinates(101, 10, max_x=100, max_y=100)  # Exceeds max_x
        
        with self.assertRaises(ValidationError):
            self.validator.validate_coordinates(10, 101, max_x=100, max_y=100)  # Exceeds max_y
        
        with self.assertRaises(ValidationError):
            self.validator.validate_coordinates("10", 20)  # Wrong type
    
    def test_validate_palette_name(self):
        """Test palette name validation."""
        # Valid names
        self.assertTrue(self.validator.validate_palette_name("My Palette"))
        self.assertTrue(self.validator.validate_palette_name("Palette-123"))
        self.assertTrue(self.validator.validate_palette_name("Simple"))
        
        # Invalid names
        with self.assertRaises(ValidationError):
            self.validator.validate_palette_name("")  # Empty
        
        with self.assertRaises(ValidationError):
            self.validator.validate_palette_name("   ")  # Only whitespace
        
        with self.assertRaises(ValidationError):
            self.validator.validate_palette_name("A" * 101)  # Too long
        
        with self.assertRaises(ValidationError):
            self.validator.validate_palette_name("Invalid<Name")  # Invalid characters
        
        with self.assertRaises(ValidationError):
            self.validator.validate_palette_name(123)  # Wrong type


class TestMemoryLimitEnforcer(unittest.TestCase):
    """Test cases for memory limit enforcement."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.enforcer = MemoryLimitEnforcer(max_memory_mb=100)  # Small limit for testing
    
    def test_check_memory_usage(self):
        """Test memory usage checking."""
        memory_info = self.enforcer.check_memory_usage()
        
        # Check required fields
        required_fields = ['rss', 'vms', 'percent', 'available', 'limit_exceeded']
        for field in required_fields:
            self.assertIn(field, memory_info)
        
        # Check data types
        self.assertIsInstance(memory_info['rss'], int)
        self.assertIsInstance(memory_info['limit_exceeded'], bool)
        
        # Memory values should be non-negative
        self.assertGreaterEqual(memory_info['rss'], 0)
    
    def test_enforce_memory_limit_normal(self):
        """Test memory limit enforcement under normal conditions."""
        # With reasonable limit, should not raise exception
        normal_enforcer = MemoryLimitEnforcer(max_memory_mb=1024)  # 1GB limit
        
        try:
            normal_enforcer.enforce_memory_limit()
        except Exception as e:
            # Should not raise exception under normal conditions
            self.fail(f"Memory limit enforcement failed unexpectedly: {e}")
    
    def test_global_validator_instances(self):
        """Test global validator instance functions."""
        # Test that global instances are created and reused
        validator1 = get_file_validator()
        validator2 = get_file_validator()
        self.assertIs(validator1, validator2)  # Should be same instance
        
        input_validator1 = get_input_validator()
        input_validator2 = get_input_validator()
        self.assertIs(input_validator1, input_validator2)
        
        memory_enforcer1 = get_memory_enforcer()
        memory_enforcer2 = get_memory_enforcer()
        self.assertIs(memory_enforcer1, memory_enforcer2)


class TestValidationUtilsEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions for validation utilities."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.validator = FileValidator()
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
    
    def test_very_large_file_simulation(self):
        """Test handling of very large files (simulated)."""
        # Create a file that would exceed size limits
        large_file = os.path.join(self.temp_dir, 'large.png')
        
        # Create a small file but test the size checking logic
        with open(large_file, 'w') as f:
            f.write('small content')
        
        # Temporarily modify the max size for testing
        original_max_size = self.validator.config.MAX_IMAGE_SIZE
        self.validator.config.MAX_IMAGE_SIZE = 5  # Very small limit
        
        try:
            with self.assertRaises(ValidationError):
                self.validator.validate_image_file(large_file)
        finally:
            # Restore original limit
            self.validator.config.MAX_IMAGE_SIZE = original_max_size
    
    def test_unicode_filenames(self):
        """Test handling of Unicode filenames."""
        unicode_filename = os.path.join(self.temp_dir, 'тест_файл.png')
        
        # Create a simple image with Unicode filename
        image = Image.new('RGB', (5, 5), color=(255, 0, 0))
        image.save(unicode_filename)
        
        # Should handle Unicode filenames correctly
        result = self.validator.validate_image_file(unicode_filename)
        self.assertTrue(result['valid'])
        
        os.remove(unicode_filename)
    
    def test_color_validation_boundary_values(self):
        """Test color validation with boundary values."""
        input_validator = InputValidator()
        
        # Test RGB boundary values
        self.assertTrue(input_validator.validate_color_value([0, 0, 0], ColorFormat.RGB))
        self.assertTrue(input_validator.validate_color_value([255, 255, 255], ColorFormat.RGB))
        
        # Test HSL boundary values
        self.assertTrue(input_validator.validate_color_value([0, 0, 0], ColorFormat.HSL))
        self.assertTrue(input_validator.validate_color_value([360, 100, 100], ColorFormat.HSL))
        
        # Test floating point values
        self.assertTrue(input_validator.validate_color_value([255.0, 0.0, 0.0], ColorFormat.RGB))


if __name__ == '__main__':
    unittest.main()