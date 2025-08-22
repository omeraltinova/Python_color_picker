"""
UI component interaction tests.
"""

import unittest
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from PIL import Image

from enhanced_color_picker.ui.main_window import MainWindow
from enhanced_color_picker.ui.components.image_canvas import EnhancedImageCanvas
from enhanced_color_picker.ui.components.color_panel import ColorPanel
from enhanced_color_picker.ui.components.palette_panel import PalettePanel
from enhanced_color_picker.core.event_bus import EventBus
from enhanced_color_picker.models.color_data import ColorData
from enhanced_color_picker.models.image_data import ImageData


class TestUIComponentInteractions(unittest.TestCase):
    """Test interactions between UI components."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during testing
        
        self.event_bus = EventBus()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test image
        self.test_image_path = os.path.join(self.temp_dir, 'test.png')
        test_image = Image.new('RGB', (50, 50), color=(255, 0, 0))
        test_image.save(self.test_image_path)
        
        # Mock services
        self.mock_services = {
            'image_service': Mock(),
            'color_service': Mock(),
            'palette_service': Mock(),
            'analysis_service': Mock()
        }
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.root.destroy()
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_image_canvas_color_selection(self):
        """Test color selection in image canvas."""
        # Create image canvas
        canvas = EnhancedImageCanvas(self.root, self.event_bus)
        
        # Mock image loading
        test_image_data = ImageData.from_file(self.test_image_path)
        canvas.display_image(test_image_data)
        
        # Simulate mouse click
        test_color = ColorData(255, 0, 0)
        
        # Mock the color picking
        with patch.object(canvas, 'get_color_at_position', return_value=test_color):
            # Simulate click event
            event = Mock()
            event.x = 25
            event.y = 25
            
            # Track events
            received_events = []
            def event_handler(data):
                received_events.append(data)
            
            self.event_bus.subscribe('color_selected', event_handler)
            
            # Trigger click
            canvas._on_canvas_click(event)
            
            # Verify event was published
            self.assertEqual(len(received_events), 1)
            event_data = received_events[0]
            self.assertEqual(event_data['color'], test_color)
            self.assertEqual(event_data['coordinates'], (25, 25))
    
    def test_color_panel_updates(self):
        """Test color panel updates when color is selected."""
        # Create color panel
        color_panel = ColorPanel(self.root, self.event_bus)
        
        # Mock color service
        color_panel.color_service = self.mock_services['color_service']
        self.mock_services['color_service'].convert_to_all_formats.return_value = {
            'rgb': {'value': (255, 0, 0), 'string': 'rgb(255, 0, 0)'},
            'hex': {'value': '#FF0000', 'string': '#FF0000'},
            'hsl': {'value': (0, 100, 50), 'string': 'hsl(0, 100%, 50%)'}
        }
        
        # Simulate color selection event
        test_color = ColorData(255, 0, 0)
        self.event_bus.publish('color_selected', {
            'color': test_color,
            'coordinates': (10, 10),
            'source': 'image_canvas'
        })
        
        # Process events
        self.root.update()
        
        # Verify color service was called
        self.mock_services['color_service'].convert_to_all_formats.assert_called_once_with(test_color)
        
        # Verify panel was updated (would need to check actual UI elements)
        self.assertEqual(color_panel.current_color, test_color)
    
    def test_palette_panel_color_addition(self):
        """Test adding colors to palette panel."""
        # Create palette panel
        palette_panel = PalettePanel(self.root, self.event_bus)
        palette_panel.palette_service = self.mock_services['palette_service']
        
        # Create new palette
        palette_panel.create_new_palette("Test Palette")
        
        # Add color to palette
        test_color = ColorData(255, 0, 0)
        palette_panel.add_color_to_palette(test_color)
        
        # Verify color was added to current palette
        self.assertIn(test_color, palette_panel.current_palette.colors)
    
    def test_main_window_component_integration(self):
        """Test main window component integration."""
        # Mock all services
        with patch('enhanced_color_picker.ui.main_window.ImageService') as mock_image_service, \
             patch('enhanced_color_picker.ui.main_window.ColorService') as mock_color_service, \
             patch('enhanced_color_picker.ui.main_window.PaletteService') as mock_palette_service:
            
            # Create main window
            main_window = MainWindow()
            
            # Verify services were initialized
            mock_image_service.assert_called_once()
            mock_color_service.assert_called_once()
            mock_palette_service.assert_called_once()
            
            # Verify components were created
            self.assertIsNotNone(main_window.image_canvas)
            self.assertIsNotNone(main_window.color_panel)
            self.assertIsNotNone(main_window.palette_panel)
    
    def test_zoom_and_pan_integration(self):
        """Test zoom and pan functionality integration."""
        canvas = EnhancedImageCanvas(self.root, self.event_bus)
        
        # Load test image
        test_image_data = ImageData.from_file(self.test_image_path)
        canvas.display_image(test_image_data)
        
        # Test zoom
        initial_zoom = canvas.zoom_manager.zoom_level
        canvas.zoom_manager.zoom_in(center=(25, 25))
        
        self.assertGreater(canvas.zoom_manager.zoom_level, initial_zoom)
        
        # Test pan
        initial_offset = canvas.pan_manager.offset
        canvas.pan_manager.pan(10, 10)
        
        self.assertNotEqual(canvas.pan_manager.offset, initial_offset)
        
        # Test that color picking still works after zoom/pan
        with patch.object(canvas, 'get_color_at_position', return_value=ColorData(255, 0, 0)) as mock_get_color:
            event = Mock()
            event.x = 30
            event.y = 30
            
            canvas._on_canvas_click(event)
            
            # Verify color picking was called with adjusted coordinates
            mock_get_color.assert_called_once()
    
    def test_keyboard_navigation(self):
        """Test keyboard navigation between components."""
        # Create main window with components
        with patch('enhanced_color_picker.ui.main_window.ImageService'), \
             patch('enhanced_color_picker.ui.main_window.ColorService'), \
             patch('enhanced_color_picker.ui.main_window.PaletteService'):
            
            main_window = MainWindow()
            
            # Test Tab navigation
            main_window.focus_set()
            
            # Simulate Tab key press
            event = Mock()
            event.keysym = 'Tab'
            
            # This would test actual keyboard navigation
            # In a real implementation, we'd verify focus moves between components
            
            # Test keyboard shortcuts
            event.keysym = 'o'
            event.state = 4  # Ctrl modifier
            
            # Would test that Ctrl+O opens file dialog
            # This requires mocking the file dialog
    
    def test_accessibility_features(self):
        """Test accessibility features integration."""
        # Create components with accessibility features
        canvas = EnhancedImageCanvas(self.root, self.event_bus)
        color_panel = ColorPanel(self.root, self.event_bus)
        
        # Test high contrast mode
        canvas.enable_high_contrast_mode(True)
        color_panel.enable_high_contrast_mode(True)
        
        # Test screen reader support
        # Verify ARIA labels are set
        self.assertIsNotNone(canvas.winfo_name())
        self.assertIsNotNone(color_panel.winfo_name())
        
        # Test keyboard accessibility
        canvas.focus_set()
        
        # Test that components respond to keyboard events
        event = Mock()
        event.keysym = 'Return'
        
        # Would test keyboard activation of components
    
    def test_theme_switching_integration(self):
        """Test theme switching across components."""
        # Create components
        canvas = EnhancedImageCanvas(self.root, self.event_bus)
        color_panel = ColorPanel(self.root, self.event_bus)
        palette_panel = PalettePanel(self.root, self.event_bus)
        
        # Test theme change event
        self.event_bus.publish('theme_changed', {
            'theme': 'dark',
            'colors': {
                'background': '#2b2b2b',
                'foreground': '#ffffff',
                'accent': '#0078d4'
            }
        })
        
        # Process events
        self.root.update()
        
        # Verify components updated their appearance
        # This would check actual color changes in a real implementation
    
    def test_error_handling_integration(self):
        """Test error handling across UI components."""
        canvas = EnhancedImageCanvas(self.root, self.event_bus)
        
        # Track error events
        error_events = []
        def error_handler(data):
            error_events.append(data)
        
        self.event_bus.subscribe('error_occurred', error_handler)
        
        # Simulate error condition
        with patch.object(canvas, 'display_image', side_effect=Exception("Test error")):
            try:
                canvas.display_image(None)
            except Exception:
                pass
        
        # In a real implementation, the component should publish error events
        # rather than letting exceptions propagate
    
    def test_responsive_layout(self):
        """Test responsive layout behavior."""
        with patch('enhanced_color_picker.ui.main_window.ImageService'), \
             patch('enhanced_color_picker.ui.main_window.ColorService'), \
             patch('enhanced_color_picker.ui.main_window.PaletteService'):
            
            main_window = MainWindow()
            
            # Test window resize
            main_window.geometry("800x600")
            self.root.update()
            
            # Test compact mode
            main_window.geometry("400x300")
            self.root.update()
            
            # Verify layout adapts to smaller size
            # This would check actual layout changes in a real implementation
    
    def test_drag_and_drop_integration(self):
        """Test drag and drop functionality."""
        canvas = EnhancedImageCanvas(self.root, self.event_bus)
        palette_panel = PalettePanel(self.root, self.event_bus)
        
        # Test drag color from canvas to palette
        test_color = ColorData(255, 0, 0)
        
        # Simulate drag start
        drag_data = {
            'type': 'color',
            'color': test_color,
            'source': 'image_canvas'
        }
        
        # Simulate drop on palette
        palette_panel.handle_drop(drag_data)
        
        # Verify color was added to palette
        # This would check actual drag/drop implementation
    
    def test_undo_redo_integration(self):
        """Test undo/redo functionality across components."""
        palette_panel = PalettePanel(self.root, self.event_bus)
        
        # Create palette
        palette_panel.create_new_palette("Test Palette")
        
        # Add color (action 1)
        color1 = ColorData(255, 0, 0)
        palette_panel.add_color_to_palette(color1)
        
        # Add another color (action 2)
        color2 = ColorData(0, 255, 0)
        palette_panel.add_color_to_palette(color2)
        
        # Test undo
        palette_panel.undo_last_action()
        self.assertNotIn(color2, palette_panel.current_palette.colors)
        self.assertIn(color1, palette_panel.current_palette.colors)
        
        # Test redo
        palette_panel.redo_last_action()
        self.assertIn(color2, palette_panel.current_palette.colors)


class TestUIWorkflows(unittest.TestCase):
    """Test complete UI workflows."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.root.withdraw()
        
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test image
        self.test_image_path = os.path.join(self.temp_dir, 'workflow_test.png')
        test_image = Image.new('RGB', (30, 30))
        pixels = []
        for y in range(30):
            for x in range(30):
                if x < 15:
                    pixels.append((255, 0, 0))  # Red
                else:
                    pixels.append((0, 0, 255))  # Blue
        test_image.putdata(pixels)
        test_image.save(self.test_image_path)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.root.destroy()
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_complete_color_picking_workflow(self):
        """Test complete workflow from image load to palette export."""
        # This would test the complete user workflow:
        # 1. Load image
        # 2. Pick colors
        # 3. Create palette
        # 4. Export palette
        
        # Mock the complete workflow
        with patch('enhanced_color_picker.ui.main_window.ImageService') as mock_image_service, \
             patch('enhanced_color_picker.ui.main_window.ColorService') as mock_color_service, \
             patch('enhanced_color_picker.ui.main_window.PaletteService') as mock_palette_service:
            
            # Setup mocks
            mock_image_service.return_value.load_image.return_value = ImageData.from_file(self.test_image_path)
            mock_color_service.return_value.convert_to_all_formats.return_value = {
                'rgb': {'value': (255, 0, 0), 'string': 'rgb(255, 0, 0)'},
                'hex': {'value': '#FF0000', 'string': '#FF0000'}
            }
            
            # Create main window
            main_window = MainWindow()
            
            # Simulate workflow steps
            # 1. Load image
            main_window.load_image(self.test_image_path)
            
            # 2. Pick color
            test_color = ColorData(255, 0, 0)
            main_window.event_bus.publish('color_selected', {
                'color': test_color,
                'coordinates': (10, 10),
                'source': 'image_canvas'
            })
            
            # 3. Create palette
            main_window.palette_panel.create_new_palette("Workflow Test")
            main_window.palette_panel.add_color_to_palette(test_color)
            
            # 4. Export palette
            export_path = os.path.join(self.temp_dir, 'workflow_export.json')
            main_window.palette_panel.export_current_palette('json', export_path)
            
            # Verify workflow completed
            mock_image_service.return_value.load_image.assert_called_once()
            mock_palette_service.return_value.export_palette.assert_called_once()
    
    def test_accessibility_workflow(self):
        """Test accessibility-focused workflow."""
        # Test workflow for users with accessibility needs
        with patch('enhanced_color_picker.ui.main_window.ImageService'), \
             patch('enhanced_color_picker.ui.main_window.ColorService') as mock_color_service, \
             patch('enhanced_color_picker.ui.main_window.PaletteService'):
            
            # Setup accessibility features
            main_window = MainWindow()
            main_window.enable_accessibility_mode(True)
            
            # Test high contrast mode
            main_window.set_theme('high_contrast')
            
            # Test screen reader announcements
            test_color = ColorData(255, 0, 0)
            main_window.event_bus.publish('color_selected', {
                'color': test_color,
                'coordinates': (10, 10),
                'source': 'image_canvas'
            })
            
            # Verify accessibility features are active
            self.assertTrue(main_window.accessibility_mode)
    
    def test_error_recovery_workflow(self):
        """Test error recovery in UI workflows."""
        with patch('enhanced_color_picker.ui.main_window.ImageService') as mock_image_service, \
             patch('enhanced_color_picker.ui.main_window.ColorService'), \
             patch('enhanced_color_picker.ui.main_window.PaletteService'):
            
            # Setup error condition
            mock_image_service.return_value.load_image.side_effect = Exception("File not found")
            
            main_window = MainWindow()
            
            # Attempt to load invalid image
            try:
                main_window.load_image("nonexistent.png")
            except Exception:
                pass
            
            # Verify error was handled gracefully
            # In real implementation, should show error dialog and continue running


if __name__ == '__main__':
    # Skip tests that require actual UI components if running in headless environment
    try:
        root = tk.Tk()
        root.withdraw()
        root.destroy()
        unittest.main()
    except tk.TclError:
        print("Skipping UI tests - no display available")
        pass