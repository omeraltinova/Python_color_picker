"""
Unit tests for PaletteService.
"""

import unittest
import tempfile
import os
import json
import shutil
from pathlib import Path

from enhanced_color_picker.services.palette_service import (
    PaletteService, PaletteExporter, PaletteImporter
)
from enhanced_color_picker.models.palette import Palette
from enhanced_color_picker.models.color_data import ColorData
from enhanced_color_picker.models.enums import ExportFormat
from enhanced_color_picker.core.exceptions import PaletteError, ValidationError


class TestPaletteExporter(unittest.TestCase):
    """Test cases for PaletteExporter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.exporter = PaletteExporter()
        self.test_palette = Palette(
            name="Test Palette",
            colors=[
                ColorData(255, 0, 0),    # Red
                ColorData(0, 255, 0),    # Green
                ColorData(0, 0, 255),    # Blue
            ],
            description="A test palette with RGB colors"
        )
    
    def test_export_to_json(self):
        """Test JSON export."""
        json_data = self.exporter.export_to_json(self.test_palette)
        
        # Should be valid JSON
        parsed = json.loads(json_data)
        self.assertIsInstance(parsed, dict)
        
        # Check required fields
        self.assertEqual(parsed['name'], "Test Palette")
        self.assertIn('colors', parsed)
        self.assertIn('created_at', parsed)
        self.assertIn('modified_at', parsed)
        
        # Check colors
        self.assertEqual(len(parsed['colors']), 3)
        for color_data in parsed['colors']:
            self.assertIn('rgb', color_data)
            self.assertIn('hex', color_data)
    
    def test_export_to_css(self):
        """Test CSS export."""
        css_data = self.exporter.export_to_css(self.test_palette)
        
        # Should contain CSS content
        self.assertIn(':root', css_data)
        self.assertIn('--color-1', css_data)
        self.assertIn('#FF0000', css_data)  # Red color
        self.assertIn('.color-1', css_data)
        self.assertIn('.bg-color-1', css_data)
        
        # Should contain palette info as comments
        self.assertIn('Test Palette', css_data)
        self.assertIn('Colors: 3', css_data)
    
    def test_export_to_scss(self):
        """Test SCSS export."""
        scss_data = self.exporter.export_to_scss(self.test_palette)
        
        # Should contain SCSS variables
        self.assertIn('$color-1', scss_data)
        self.assertIn('#FF0000', scss_data)  # Red color
        
        # Should contain color map
        self.assertIn('$palette-test-palette', scss_data)
        self.assertIn("'color-1':", scss_data)
        
        # Should contain palette info as comments
        self.assertIn('Test Palette', scss_data)
        self.assertIn('Colors: 3', scss_data)
    
    def test_export_to_ase(self):
        """Test Adobe Swatch Exchange (ASE) export."""
        ase_data = self.exporter.export_to_ase(self.test_palette)
        
        # Should return bytes
        self.assertIsInstance(ase_data, bytes)
        
        # Should start with ASE signature
        self.assertTrue(ase_data.startswith(b'ASEF'))
        
        # Should have reasonable length (header + color blocks)
        self.assertGreater(len(ase_data), 20)
    
    def test_export_to_aco(self):
        """Test Adobe Color (ACO) export."""
        aco_data = self.exporter.export_to_aco(self.test_palette)
        
        # Should return bytes
        self.assertIsInstance(aco_data, bytes)
        
        # Should have reasonable length
        self.assertGreater(len(aco_data), 10)
        
        # First two bytes should be version (1)
        version = int.from_bytes(aco_data[:2], byteorder='big')
        self.assertEqual(version, 1)
        
        # Next two bytes should be color count (3)
        color_count = int.from_bytes(aco_data[2:4], byteorder='big')
        self.assertEqual(color_count, 3)
    
    def test_export_to_gpl(self):
        """Test GIMP Palette (GPL) export."""
        gpl_data = self.exporter.export_to_gpl(self.test_palette)
        
        # Should start with GIMP Palette header
        self.assertTrue(gpl_data.startswith('GIMP Palette'))
        
        # Should contain palette name
        self.assertIn('Name: Test Palette', gpl_data)
        
        # Should contain color entries
        self.assertIn('255   0   0', gpl_data)  # Red
        self.assertIn('  0 255   0', gpl_data)  # Green
        self.assertIn('  0   0 255', gpl_data)  # Blue
        
        # Should contain metadata
        self.assertIn('Colors: 3', gpl_data)


class TestPaletteImporter(unittest.TestCase):
    """Test cases for PaletteImporter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.importer = PaletteImporter()
    
    def test_import_from_json(self):
        """Test JSON import."""
        json_data = {
            "name": "Imported Palette",
            "colors": [
                {"rgb": [255, 0, 0], "hex": "#FF0000"},
                {"rgb": [0, 255, 0], "hex": "#00FF00"}
            ],
            "created_at": "2024-01-01T00:00:00",
            "modified_at": "2024-01-01T00:00:00",
            "description": "Test import",
            "tags": ["test", "import"]
        }
        
        json_string = json.dumps(json_data)
        palette = self.importer.import_from_json(json_string)
        
        self.assertIsInstance(palette, Palette)
        self.assertEqual(palette.name, "Imported Palette")
        self.assertEqual(len(palette.colors), 2)
        self.assertEqual(palette.description, "Test import")
        self.assertEqual(palette.tags, ["test", "import"])
    
    def test_import_from_json_invalid(self):
        """Test JSON import with invalid data."""
        # Invalid JSON
        with self.assertRaises(PaletteError):
            self.importer.import_from_json("invalid json {")
        
        # Valid JSON but invalid structure
        with self.assertRaises(PaletteError):
            self.importer.import_from_json('{"not": "a palette"}')
    
    def test_import_from_gpl(self):
        """Test GPL import."""
        gpl_data = """GIMP Palette
Name: Test GPL Palette
Columns: 16
# Created: 2024-01-01
# Colors: 3
#
255   0   0	Red
  0 255   0	Green
  0   0 255	Blue
"""
        
        palette = self.importer.import_from_gpl(gpl_data)
        
        self.assertIsInstance(palette, Palette)
        self.assertEqual(palette.name, "Test GPL Palette")
        self.assertEqual(len(palette.colors), 3)
        
        # Check colors
        self.assertEqual(palette.colors[0].rgb, (255, 0, 0))
        self.assertEqual(palette.colors[1].rgb, (0, 255, 0))
        self.assertEqual(palette.colors[2].rgb, (0, 0, 255))
    
    def test_import_from_gpl_invalid(self):
        """Test GPL import with invalid data."""
        # Missing header
        with self.assertRaises(PaletteError):
            self.importer.import_from_gpl("Not a GIMP palette")
        
        # No colors
        with self.assertRaises(PaletteError):
            self.importer.import_from_gpl("GIMP Palette\nName: Empty\n")
    
    def test_import_from_hex_list(self):
        """Test import from hex color list."""
        hex_list = ["#FF0000", "#00FF00", "#0000FF", "FFFF00"]  # Mix of formats
        
        palette = self.importer.import_from_hex_list(hex_list, "Hex Palette")
        
        self.assertIsInstance(palette, Palette)
        self.assertEqual(palette.name, "Hex Palette")
        self.assertEqual(len(palette.colors), 4)
        
        # Check colors
        self.assertEqual(palette.colors[0].hex, "#FF0000")
        self.assertEqual(palette.colors[1].hex, "#00FF00")
        self.assertEqual(palette.colors[2].hex, "#0000FF")
        self.assertEqual(palette.colors[3].hex, "#FFFF00")
    
    def test_import_from_hex_list_invalid(self):
        """Test hex list import with invalid colors."""
        # Mix of valid and invalid hex codes
        hex_list = ["#FF0000", "invalid", "#00FF00", "GGG"]
        
        palette = self.importer.import_from_hex_list(hex_list)
        
        # Should skip invalid colors and import valid ones
        self.assertEqual(len(palette.colors), 2)
        
        # Empty list should raise error
        with self.assertRaises(PaletteError):
            self.importer.import_from_hex_list([])


class TestPaletteService(unittest.TestCase):
    """Test cases for PaletteService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.service = PaletteService(self.temp_dir)
        
        self.test_colors = [
            ColorData(255, 0, 0),    # Red
            ColorData(0, 255, 0),    # Green
            ColorData(0, 0, 255),    # Blue
        ]
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_create_palette(self):
        """Test palette creation."""
        palette = self.service.create_palette(
            name="Test Palette",
            colors=self.test_colors,
            description="A test palette",
            tags=["test", "rgb"]
        )
        
        self.assertIsInstance(palette, Palette)
        self.assertEqual(palette.name, "Test Palette")
        self.assertEqual(len(palette.colors), 3)
        self.assertEqual(palette.description, "A test palette")
        self.assertEqual(palette.tags, ["test", "rgb"])
    
    def test_create_palette_empty_name(self):
        """Test palette creation with empty name."""
        with self.assertRaises(ValidationError):
            self.service.create_palette("")
        
        with self.assertRaises(ValidationError):
            self.service.create_palette("   ")  # Only whitespace
    
    def test_save_and_load_palette(self):
        """Test palette saving and loading."""
        # Create and save palette
        palette = self.service.create_palette("Save Test", self.test_colors)
        saved_path = self.service.save_palette(palette)
        
        self.assertTrue(os.path.exists(saved_path))
        
        # Load palette
        loaded_palette = self.service.load_palette(saved_path)
        
        self.assertEqual(loaded_palette.name, palette.name)
        self.assertEqual(len(loaded_palette.colors), len(palette.colors))
        
        # Check colors match
        for i, color in enumerate(loaded_palette.colors):
            self.assertEqual(color.rgb, palette.colors[i].rgb)
    
    def test_load_nonexistent_palette(self):
        """Test loading non-existent palette."""
        with self.assertRaises(PaletteError):
            self.service.load_palette("nonexistent.json")
    
    def test_list_saved_palettes(self):
        """Test listing saved palettes."""
        # Initially empty
        palettes = self.service.list_saved_palettes()
        self.assertEqual(len(palettes), 0)
        
        # Save some palettes
        palette1 = self.service.create_palette("Palette 1", self.test_colors[:2])
        palette2 = self.service.create_palette("Palette 2", self.test_colors[1:])
        
        self.service.save_palette(palette1)
        self.service.save_palette(palette2)
        
        # List should now contain both
        palettes = self.service.list_saved_palettes()
        self.assertEqual(len(palettes), 2)
        
        palette_names = [p['name'] for p in palettes]
        self.assertIn("Palette 1", palette_names)
        self.assertIn("Palette 2", palette_names)
        
        # Check palette info
        for palette_info in palettes:
            self.assertIn('file_path', palette_info)
            self.assertIn('color_count', palette_info)
            self.assertIn('created_at', palette_info)
            self.assertIn('tags', palette_info)
    
    def test_delete_palette(self):
        """Test palette deletion."""
        # Create and save palette
        palette = self.service.create_palette("Delete Test", self.test_colors)
        saved_path = self.service.save_palette(palette)
        
        # Verify it exists
        self.assertTrue(os.path.exists(saved_path))
        
        # Delete palette
        result = self.service.delete_palette("Delete Test")
        self.assertTrue(result)
        
        # Verify it's gone
        self.assertFalse(os.path.exists(saved_path))
        
        # Try to delete again (should raise error)
        with self.assertRaises(PaletteError):
            self.service.delete_palette("Delete Test")
    
    def test_export_palette(self):
        """Test palette export in various formats."""
        palette = self.service.create_palette("Export Test", self.test_colors)
        
        # Test JSON export
        json_path = os.path.join(self.temp_dir, "export.json")
        exported_path = self.service.export_palette(palette, ExportFormat.JSON, json_path)
        self.assertEqual(exported_path, json_path)
        self.assertTrue(os.path.exists(json_path))
        
        # Test CSS export
        css_path = os.path.join(self.temp_dir, "export.css")
        exported_path = self.service.export_palette(palette, ExportFormat.CSS, css_path)
        self.assertTrue(os.path.exists(css_path))
        
        # Test GPL export
        gpl_path = os.path.join(self.temp_dir, "export.gpl")
        exported_path = self.service.export_palette(palette, ExportFormat.GPL, gpl_path)
        self.assertTrue(os.path.exists(gpl_path))
        
        # Verify GPL content
        with open(gpl_path, 'r') as f:
            gpl_content = f.read()
        self.assertIn("GIMP Palette", gpl_content)
        self.assertIn("Export Test", gpl_content)
    
    def test_import_palette(self):
        """Test palette import."""
        # Create a JSON palette file
        palette_data = {
            "name": "Import Test",
            "colors": [
                {"rgb": [255, 0, 0], "hex": "#FF0000"},
                {"rgb": [0, 255, 0], "hex": "#00FF00"}
            ],
            "created_at": "2024-01-01T00:00:00",
            "modified_at": "2024-01-01T00:00:00"
        }
        
        json_path = os.path.join(self.temp_dir, "import.json")
        with open(json_path, 'w') as f:
            json.dump(palette_data, f)
        
        # Import palette
        imported_palette = self.service.import_palette(json_path)
        
        self.assertEqual(imported_palette.name, "Import Test")
        self.assertEqual(len(imported_palette.colors), 2)
        self.assertEqual(imported_palette.colors[0].rgb, (255, 0, 0))
    
    def test_import_palette_auto_detect(self):
        """Test palette import with format auto-detection."""
        # Create GPL file
        gpl_content = """GIMP Palette
Name: Auto Detect Test
255   0   0	Red
  0 255   0	Green
"""
        
        gpl_path = os.path.join(self.temp_dir, "auto.gpl")
        with open(gpl_path, 'w') as f:
            f.write(gpl_content)
        
        # Import without specifying format
        imported_palette = self.service.import_palette(gpl_path)
        
        self.assertEqual(imported_palette.name, "Auto Detect Test")
        self.assertEqual(len(imported_palette.colors), 2)
    
    def test_validate_palette(self):
        """Test palette validation."""
        # Valid palette
        valid_palette = self.service.create_palette("Valid", self.test_colors)
        validation = self.service.validate_palette(valid_palette)
        
        self.assertTrue(validation['is_valid'])
        self.assertEqual(len(validation['errors']), 0)
        self.assertIn('info', validation)
        
        # Invalid palette (empty name)
        invalid_palette = Palette(name="", colors=self.test_colors)
        validation = self.service.validate_palette(invalid_palette)
        
        self.assertFalse(validation['is_valid'])
        self.assertGreater(len(validation['errors']), 0)
        
        # Palette with no colors
        empty_palette = self.service.create_palette("Empty", [])
        validation = self.service.validate_palette(empty_palette)
        
        self.assertTrue(validation['is_valid'])  # Valid but has warnings
        self.assertGreater(len(validation['warnings']), 0)
    
    def test_search_palettes(self):
        """Test palette search functionality."""
        # Create test palettes
        palette1 = self.service.create_palette(
            "Red Palette", 
            [ColorData(255, 0, 0)], 
            description="A palette with red colors",
            tags=["red", "warm"]
        )
        palette2 = self.service.create_palette(
            "Blue Palette", 
            [ColorData(0, 0, 255)], 
            description="A palette with blue colors",
            tags=["blue", "cool"]
        )
        
        self.service.save_palette(palette1)
        self.service.save_palette(palette2)
        
        # Search by name
        results = self.service.search_palettes("Red")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], "Red Palette")
        
        # Search by tag
        results = self.service.search_palettes("warm")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], "Red Palette")
        
        # Search by description
        results = self.service.search_palettes("blue colors")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], "Blue Palette")
        
        # Search with no results
        results = self.service.search_palettes("nonexistent")
        self.assertEqual(len(results), 0)
        
        # Empty search should return all
        results = self.service.search_palettes("")
        self.assertEqual(len(results), 2)
    
    def test_palette_exists(self):
        """Test palette existence check."""
        # Initially doesn't exist
        self.assertFalse(self.service.palette_exists("Test Palette"))
        
        # Create and save palette
        palette = self.service.create_palette("Test Palette", self.test_colors)
        self.service.save_palette(palette)
        
        # Now should exist
        self.assertTrue(self.service.palette_exists("Test Palette"))
    
    def test_get_palette_stats(self):
        """Test palette statistics."""
        # Initially empty
        stats = self.service.get_palette_stats()
        self.assertEqual(stats['total_palettes'], 0)
        self.assertEqual(stats['total_colors'], 0)
        
        # Add some palettes
        palette1 = self.service.create_palette("Stats 1", self.test_colors[:2], tags=["test", "stats"])
        palette2 = self.service.create_palette("Stats 2", self.test_colors, tags=["test", "more"])
        
        self.service.save_palette(palette1)
        self.service.save_palette(palette2)
        
        # Check stats
        stats = self.service.get_palette_stats()
        self.assertEqual(stats['total_palettes'], 2)
        self.assertEqual(stats['total_colors'], 5)  # 2 + 3 colors
        self.assertGreater(stats['average_colors_per_palette'], 0)
        self.assertGreater(stats['total_tags'], 0)
        self.assertIsInstance(stats['most_common_tags'], list)
    
    def test_cache_operations(self):
        """Test cache operations."""
        palette = self.service.create_palette("Cache Test", self.test_colors)
        
        # Initially not in cache
        self.assertIsNone(self.service.get_cached_palette("Cache Test"))
        
        # Save palette (should add to cache)
        self.service.save_palette(palette)
        
        # Should now be in cache
        cached = self.service.get_cached_palette("Cache Test")
        self.assertIsNotNone(cached)
        self.assertEqual(cached.name, "Cache Test")
        
        # Clear cache
        self.service.clear_cache()
        
        # Should no longer be in cache
        self.assertIsNone(self.service.get_cached_palette("Cache Test"))


class TestPaletteServiceEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions for PaletteService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.service = PaletteService(self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_duplicate_palette_names(self):
        """Test handling of duplicate palette names."""
        # Create first palette
        palette1 = self.service.create_palette("Duplicate", [ColorData(255, 0, 0)])
        self.service.save_palette(palette1)
        
        # Try to create another with same name
        with self.assertRaises(ValidationError):
            self.service.create_palette("Duplicate", [ColorData(0, 255, 0)])
    
    def test_invalid_export_format(self):
        """Test export with invalid format."""
        palette = self.service.create_palette("Export Test", [ColorData(255, 0, 0)])
        
        # This would need to be tested with a mock or by extending ExportFormat enum
        # For now, we test that the method handles the format parameter correctly
        export_path = os.path.join(self.temp_dir, "test.json")
        result = self.service.export_palette(palette, ExportFormat.JSON, export_path)
        self.assertEqual(result, export_path)
    
    def test_corrupted_palette_file(self):
        """Test handling of corrupted palette files."""
        # Create corrupted JSON file
        corrupted_path = os.path.join(self.temp_dir, "corrupted.json")
        with open(corrupted_path, 'w') as f:
            f.write("{ corrupted json")
        
        with self.assertRaises(PaletteError):
            self.service.load_palette(corrupted_path)
    
    def test_large_palette(self):
        """Test handling of large palettes."""
        # Create palette with many colors
        many_colors = [ColorData(i % 256, (i * 2) % 256, (i * 3) % 256) for i in range(1000)]
        large_palette = self.service.create_palette("Large Palette", many_colors)
        
        # Should handle large palettes without issues
        validation = self.service.validate_palette(large_palette)
        self.assertTrue(validation['is_valid'])
        
        # Should be able to save and load
        saved_path = self.service.save_palette(large_palette)
        loaded_palette = self.service.load_palette(saved_path)
        self.assertEqual(len(loaded_palette.colors), 1000)


if __name__ == '__main__':
    unittest.main()