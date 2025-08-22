"""
Basic test to verify test infrastructure works.
"""

import unittest
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class TestBasicInfrastructure(unittest.TestCase):
    """Test basic test infrastructure."""
    
    def test_python_version(self):
        """Test Python version is adequate."""
        self.assertGreaterEqual(sys.version_info[:2], (3, 8))
    
    def test_imports(self):
        """Test basic imports work."""
        # Test standard library imports
        import json
        import tempfile
        import pathlib
        
        # Test PIL import
        try:
            from PIL import Image
            pil_available = True
        except ImportError:
            pil_available = False
        
        self.assertTrue(pil_available, "PIL/Pillow is required")
    
    def test_project_structure(self):
        """Test project structure exists."""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Check main directories exist
        expected_dirs = [
            'enhanced_color_picker',
            'tests'
        ]
        
        for dir_name in expected_dirs:
            dir_path = os.path.join(project_root, dir_name)
            self.assertTrue(os.path.exists(dir_path), f"Directory {dir_name} should exist")
    
    def test_test_categories(self):
        """Test all test category directories exist."""
        test_root = os.path.dirname(os.path.abspath(__file__))
        
        expected_categories = ['unit', 'integration', 'ui', 'performance']
        
        for category in expected_categories:
            category_path = os.path.join(test_root, category)
            self.assertTrue(os.path.exists(category_path), f"Test category {category} should exist")
            
            # Check __init__.py exists
            init_path = os.path.join(category_path, '__init__.py')
            self.assertTrue(os.path.exists(init_path), f"__init__.py should exist in {category}")
    
    def test_color_data_basic(self):
        """Test basic ColorData functionality."""
        try:
            from enhanced_color_picker.models.color_data import ColorData
            
            # Test basic color creation
            color = ColorData(255, 0, 0)
            self.assertEqual(color.r, 255)
            self.assertEqual(color.g, 0)
            self.assertEqual(color.b, 0)
            self.assertEqual(color.alpha, 1.0)
            
            # Test hex conversion
            self.assertEqual(color.hex, '#FF0000')
            
        except ImportError as e:
            self.fail(f"Could not import ColorData: {e}")
    
    def test_basic_color_utils(self):
        """Test basic color utility functions."""
        try:
            from enhanced_color_picker.models.color_data import ColorData
            
            # Create test colors
            white = ColorData(255, 255, 255)
            black = ColorData(0, 0, 0)
            
            # Test luminance calculation
            white_luminance = white.get_luminance()
            black_luminance = black.get_luminance()
            
            self.assertGreater(white_luminance, black_luminance)
            self.assertAlmostEqual(white_luminance, 1.0, places=1)
            self.assertAlmostEqual(black_luminance, 0.0, places=1)
            
        except ImportError as e:
            self.fail(f"Could not import required modules: {e}")


if __name__ == '__main__':
    unittest.main()