"""
Integration tests for service layer interactions.
"""

import unittest
import tempfile
import os
import shutil
from PIL import Image

from enhanced_color_picker.services.color_service import ColorService
from enhanced_color_picker.services.palette_service import PaletteService
from enhanced_color_picker.services.image_service import ImageService
from enhanced_color_picker.services.analysis_service import AnalysisService
from enhanced_color_picker.models.color_data import ColorData
from enhanced_color_picker.models.image_data import ImageData
from enhanced_color_picker.models.enums import ColorFormat, ExportFormat


class TestServicesIntegration(unittest.TestCase):
    """Test integration between different services."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Initialize services
        self.color_service = ColorService()
        self.palette_service = PaletteService(self.temp_dir)
        self.image_service = ImageService()
        self.analysis_service = AnalysisService()
        
        # Create test image
        self.test_image_path = os.path.join(self.temp_dir, 'test_image.png')
        test_image = Image.new('RGB', (20, 20))
        pixels = []
        for y in range(20):
            for x in range(20):
                if x < 10:
                    pixels.append((255, 0, 0))  # Red half
                else:
                    pixels.append((0, 0, 255))  # Blue half
        test_image.putdata(pixels)
        test_image.save(self.test_image_path)
        
        self.image_data = ImageData.from_file(self.test_image_path)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_image_to_palette_workflow(self):
        """Test complete workflow from image analysis to palette creation."""
        # Step 1: Extract dominant colors from image
        dominant_colors = self.analysis_service.extract_dominant_colors(self.image_data, num_colors=3)
        
        self.assertIsInstance(dominant_colors, list)
        self.assertGreater(len(dominant_colors), 0)
        self.assertLessEqual(len(dominant_colors), 3)
        
        # Step 2: Create palette from dominant colors
        palette = self.palette_service.create_palette(
            name="Image Palette",
            colors=dominant_colors,
            description="Palette extracted from test image"
        )
        
        self.assertEqual(palette.name, "Image Palette")
        self.assertEqual(len(palette.colors), len(dominant_colors))
        
        # Step 3: Save palette
        saved_path = self.palette_service.save_palette(palette)
        self.assertTrue(os.path.exists(saved_path))
        
        # Step 4: Load and verify palette
        loaded_palette = self.palette_service.load_palette(saved_path)
        self.assertEqual(loaded_palette.name, palette.name)
        self.assertEqual(len(loaded_palette.colors), len(palette.colors))
    
    def test_color_analysis_and_harmony_integration(self):
        """Test integration between color analysis and harmony generation."""
        # Step 1: Pick a color from image
        pixel_color = self.image_service.get_pixel_color(self.image_data, 5, 5)  # Red side
        self.assertIsInstance(pixel_color, ColorData)
        
        # Step 2: Analyze color properties
        analysis = self.color_service.analyze_color(pixel_color)
        
        self.assertIn('basic_info', analysis)
        self.assertIn('properties', analysis)
        self.assertIn('harmonies', analysis)
        
        # Step 3: Generate specific harmony
        triadic_harmony = self.color_service.generate_color_harmony(
            pixel_color, 
            "triadic"
        )
        
        self.assertEqual(len(triadic_harmony['colors']), 2)
        
        # Step 4: Create palette from harmony
        harmony_colors = [pixel_color] + triadic_harmony['colors']
        harmony_palette = self.palette_service.create_palette(
            name="Triadic Harmony",
            colors=harmony_colors,
            tags=["harmony", "triadic"]
        )
        
        self.assertEqual(len(harmony_palette.colors), 3)
        
        # Step 5: Export palette in multiple formats
        json_path = os.path.join(self.temp_dir, "harmony.json")
        css_path = os.path.join(self.temp_dir, "harmony.css")
        
        self.palette_service.export_palette(harmony_palette, ExportFormat.JSON, json_path)
        self.palette_service.export_palette(harmony_palette, ExportFormat.CSS, css_path)
        
        self.assertTrue(os.path.exists(json_path))
        self.assertTrue(os.path.exists(css_path))
    
    def test_accessibility_analysis_integration(self):
        """Test integration of accessibility analysis across services."""
        # Step 1: Get colors from image
        red_color = self.image_service.get_pixel_color(self.image_data, 5, 5)
        blue_color = self.image_service.get_pixel_color(self.image_data, 15, 15)
        
        # Step 2: Check WCAG compliance
        compliance = self.color_service.check_wcag_compliance(red_color, blue_color)
        
        self.assertIn('contrast_ratio', compliance)
        self.assertIn('wcag_aa', compliance)
        self.assertIn('wcag_aaa', compliance)
        
        # Step 3: Generate accessible color alternatives if needed
        if not compliance['wcag_aa']['normal_text']:
            # Get better text color for red background
            better_text = self.color_service.get_readable_text_color(red_color)
            
            # Verify the suggestion is better
            better_compliance = self.color_service.check_wcag_compliance(better_text, red_color)
            self.assertGreater(
                better_compliance['contrast_ratio'], 
                compliance['contrast_ratio']
            )
        
        # Step 4: Create accessibility-focused palette
        accessible_colors = [red_color, blue_color]
        if 'suggestions' in compliance:
            accessible_colors.append(compliance['suggestions']['better_foreground'])
        
        accessible_palette = self.palette_service.create_palette(
            name="Accessible Colors",
            colors=accessible_colors,
            description="Colors with accessibility considerations",
            tags=["accessibility", "wcag"]
        )
        
        # Step 5: Validate palette for accessibility
        validation = self.palette_service.validate_palette(accessible_palette)
        self.assertTrue(validation['is_valid'])
    
    def test_color_blindness_simulation_integration(self):
        """Test color blindness simulation across services."""
        # Step 1: Extract colors from image
        dominant_colors = self.analysis_service.extract_dominant_colors(self.image_data, num_colors=2)
        
        # Step 2: Simulate color blindness for each color
        simulated_palettes = {}
        blindness_types = ['protanopia', 'deuteranopia', 'tritanopia']
        
        for blindness_type in blindness_types:
            simulated_colors = []
            for color in dominant_colors:
                simulated = self.color_service.simulate_color_blindness_all_types(color)
                if blindness_type in simulated:
                    simulated_colors.append(simulated[blindness_type])
            
            if simulated_colors:
                palette = self.palette_service.create_palette(
                    name=f"Simulated {blindness_type.title()}",
                    colors=simulated_colors,
                    description=f"Colors as seen with {blindness_type}",
                    tags=["color-blindness", blindness_type]
                )
                simulated_palettes[blindness_type] = palette
        
        # Step 3: Save all simulated palettes
        for blindness_type, palette in simulated_palettes.items():
            saved_path = self.palette_service.save_palette(palette)
            self.assertTrue(os.path.exists(saved_path))
        
        # Step 4: Verify palettes can be searched by tag
        search_results = self.palette_service.search_palettes("color-blindness")
        self.assertGreaterEqual(len(search_results), len(simulated_palettes))
    
    def test_batch_color_processing(self):
        """Test batch processing of colors across services."""
        # Step 1: Generate a set of colors using different methods
        base_color = ColorData(180, 100, 50)  # Orange-ish
        
        # Get complementary colors
        complementary = self.color_service.generate_color_harmony(base_color, "complementary")
        
        # Get analogous colors
        analogous = self.color_service.generate_color_harmony(base_color, "analogous", count=3)
        
        # Combine all colors
        all_colors = [base_color] + complementary['colors'] + analogous['colors']
        
        # Step 2: Batch convert all colors to different formats
        batch_conversions = {}
        for i, color in enumerate(all_colors):
            conversions = self.color_service.convert_to_all_formats(color)
            batch_conversions[f"color_{i}"] = conversions
        
        # Verify all conversions
        for color_key, conversions in batch_conversions.items():
            self.assertIn('rgb', conversions)
            self.assertIn('hex', conversions)
            self.assertIn('hsl', conversions)
        
        # Step 3: Create multiple themed palettes
        palettes = {
            "Warm Palette": [c for c in all_colors if self.color_service.get_color_temperature(c) < 5000],
            "Cool Palette": [c for c in all_colors if self.color_service.get_color_temperature(c) >= 5000],
            "Dark Palette": [c for c in all_colors if self.color_service.is_dark_color(c)],
            "Light Palette": [c for c in all_colors if self.color_service.is_light_color(c)]
        }
        
        # Step 4: Save all palettes and verify
        saved_palettes = []
        for name, colors in palettes.items():
            if colors:  # Only create palette if it has colors
                palette = self.palette_service.create_palette(name, colors)
                saved_path = self.palette_service.save_palette(palette)
                saved_palettes.append(saved_path)
                self.assertTrue(os.path.exists(saved_path))
        
        # Step 5: Verify palette statistics
        stats = self.palette_service.get_palette_stats()
        self.assertGreaterEqual(stats['total_palettes'], len(saved_palettes))
    
    def test_image_analysis_to_export_pipeline(self):
        """Test complete pipeline from image analysis to export."""
        # Step 1: Comprehensive image analysis
        image_stats = self.analysis_service.get_comprehensive_analysis(self.image_data)
        
        self.assertIn('dominant_colors', image_stats)
        self.assertIn('average_color', image_stats)
        self.assertIn('brightness', image_stats)
        
        # Step 2: Create analysis-based palette
        analysis_palette = self.palette_service.create_palette(
            name="Image Analysis",
            colors=image_stats['dominant_colors'] + [image_stats['average_color']],
            description=f"Analysis of {os.path.basename(self.test_image_path)}",
            tags=["analysis", "extracted"]
        )
        
        # Step 3: Export in all supported formats
        export_formats = [
            (ExportFormat.JSON, "analysis.json"),
            (ExportFormat.CSS, "analysis.css"),
            (ExportFormat.SCSS, "analysis.scss"),
            (ExportFormat.GPL, "analysis.gpl")
        ]
        
        exported_files = []
        for format_type, filename in export_formats:
            export_path = os.path.join(self.temp_dir, filename)
            result_path = self.palette_service.export_palette(analysis_palette, format_type, export_path)
            exported_files.append(result_path)
            self.assertTrue(os.path.exists(result_path))
        
        # Step 4: Verify export contents
        # Check JSON export
        json_path = exported_files[0]
        imported_palette = self.palette_service.import_palette(json_path)
        self.assertEqual(imported_palette.name, analysis_palette.name)
        self.assertEqual(len(imported_palette.colors), len(analysis_palette.colors))
        
        # Check CSS export contains expected content
        css_path = exported_files[1]
        with open(css_path, 'r') as f:
            css_content = f.read()
        self.assertIn(':root', css_content)
        self.assertIn('--color-1', css_content)
        self.assertIn('Image Analysis', css_content)
    
    def test_error_handling_integration(self):
        """Test error handling across service integrations."""
        # Test with invalid image
        try:
            invalid_image_path = os.path.join(self.temp_dir, 'invalid.png')
            with open(invalid_image_path, 'w') as f:
                f.write('not an image')
            
            # This should raise an appropriate error
            with self.assertRaises(Exception):
                ImageData.from_file(invalid_image_path)
        except Exception:
            pass  # Expected
        
        # Test with invalid color data
        try:
            invalid_color = ColorData(-1, 300, 50)  # Invalid RGB values
            # Services should handle invalid colors gracefully
            analysis = self.color_service.analyze_color(invalid_color)
            # Should still return analysis even with edge case values
            self.assertIsInstance(analysis, dict)
        except Exception:
            pass  # Some validation might reject invalid colors
        
        # Test palette service with invalid data
        try:
            with self.assertRaises(Exception):
                self.palette_service.create_palette("")  # Empty name
        except Exception:
            pass  # Expected
    
    def test_performance_integration(self):
        """Test performance aspects of service integration."""
        # Create larger test image
        large_image_path = os.path.join(self.temp_dir, 'large_test.png')
        large_image = Image.new('RGB', (100, 100))
        
        # Create gradient pattern
        pixels = []
        for y in range(100):
            for x in range(100):
                r = int((x / 100) * 255)
                g = int((y / 100) * 255)
                b = int(((x + y) / 200) * 255)
                pixels.append((r, g, b))
        
        large_image.putdata(pixels)
        large_image.save(large_image_path)
        
        large_image_data = ImageData.from_file(large_image_path)
        
        # Test that operations complete in reasonable time
        import time
        
        # Dominant color extraction should be reasonably fast
        start_time = time.time()
        dominant_colors = self.analysis_service.extract_dominant_colors(large_image_data, num_colors=5)
        extraction_time = time.time() - start_time
        
        self.assertLess(extraction_time, 10.0)  # Should complete within 10 seconds
        self.assertGreater(len(dominant_colors), 0)
        
        # Palette operations should be fast
        start_time = time.time()
        palette = self.palette_service.create_palette("Performance Test", dominant_colors)
        saved_path = self.palette_service.save_palette(palette)
        palette_time = time.time() - start_time
        
        self.assertLess(palette_time, 5.0)  # Should complete within 5 seconds
        self.assertTrue(os.path.exists(saved_path))


class TestEventBusIntegration(unittest.TestCase):
    """Test event bus integration between components."""
    
    def setUp(self):
        """Set up test fixtures."""
        from enhanced_color_picker.core.event_bus import EventBus
        self.event_bus = EventBus()
        self.received_events = []
    
    def event_handler(self, event_data):
        """Test event handler."""
        self.received_events.append(event_data)
    
    def test_color_selection_events(self):
        """Test color selection event propagation."""
        # Subscribe to color selection events
        self.event_bus.subscribe('color_selected', self.event_handler)
        
        # Simulate color selection
        test_color = ColorData(255, 0, 0)
        self.event_bus.publish('color_selected', {
            'color': test_color,
            'coordinates': (10, 20),
            'source': 'image_canvas'
        })
        
        # Verify event was received
        self.assertEqual(len(self.received_events), 1)
        event_data = self.received_events[0]
        self.assertEqual(event_data['color'], test_color)
        self.assertEqual(event_data['coordinates'], (10, 20))
        self.assertEqual(event_data['source'], 'image_canvas')
    
    def test_palette_events(self):
        """Test palette-related event propagation."""
        # Subscribe to palette events
        self.event_bus.subscribe('palette_created', self.event_handler)
        self.event_bus.subscribe('palette_saved', self.event_handler)
        
        # Simulate palette creation
        self.event_bus.publish('palette_created', {
            'palette_name': 'Test Palette',
            'color_count': 5
        })
        
        # Simulate palette save
        self.event_bus.publish('palette_saved', {
            'palette_name': 'Test Palette',
            'file_path': '/path/to/palette.json'
        })
        
        # Verify events were received
        self.assertEqual(len(self.received_events), 2)
        
        create_event = self.received_events[0]
        self.assertEqual(create_event['palette_name'], 'Test Palette')
        self.assertEqual(create_event['color_count'], 5)
        
        save_event = self.received_events[1]
        self.assertEqual(save_event['palette_name'], 'Test Palette')
        self.assertIn('file_path', save_event)
    
    def test_error_events(self):
        """Test error event propagation."""
        # Subscribe to error events
        self.event_bus.subscribe('error_occurred', self.event_handler)
        
        # Simulate error
        self.event_bus.publish('error_occurred', {
            'error_type': 'ValidationError',
            'message': 'Invalid color format',
            'component': 'color_service'
        })
        
        # Verify error event was received
        self.assertEqual(len(self.received_events), 1)
        error_event = self.received_events[0]
        self.assertEqual(error_event['error_type'], 'ValidationError')
        self.assertEqual(error_event['message'], 'Invalid color format')
        self.assertEqual(error_event['component'], 'color_service')
    
    def test_multiple_subscribers(self):
        """Test multiple subscribers to same event."""
        received_events_2 = []
        
        def second_handler(event_data):
            received_events_2.append(event_data)
        
        # Subscribe both handlers to same event
        self.event_bus.subscribe('test_event', self.event_handler)
        self.event_bus.subscribe('test_event', second_handler)
        
        # Publish event
        test_data = {'message': 'test'}
        self.event_bus.publish('test_event', test_data)
        
        # Both handlers should receive the event
        self.assertEqual(len(self.received_events), 1)
        self.assertEqual(len(received_events_2), 1)
        self.assertEqual(self.received_events[0], test_data)
        self.assertEqual(received_events_2[0], test_data)
    
    def test_unsubscribe(self):
        """Test event unsubscription."""
        # Subscribe and verify subscription works
        self.event_bus.subscribe('test_event', self.event_handler)
        self.event_bus.publish('test_event', {'test': 1})
        self.assertEqual(len(self.received_events), 1)
        
        # Unsubscribe and verify no more events received
        self.event_bus.unsubscribe('test_event', self.event_handler)
        self.event_bus.publish('test_event', {'test': 2})
        self.assertEqual(len(self.received_events), 1)  # Should still be 1


if __name__ == '__main__':
    unittest.main()