"""
Performance benchmark tests for the Enhanced Color Picker.
"""

import unittest
import time
import tempfile
import os
import shutil
from PIL import Image
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor

from enhanced_color_picker.services.image_service import ImageService
from enhanced_color_picker.services.color_service import ColorService
from enhanced_color_picker.services.palette_service import PaletteService
from enhanced_color_picker.services.analysis_service import AnalysisService
from enhanced_color_picker.utils.image_utils import extract_dominant_colors, calculate_average_color
from enhanced_color_picker.utils.color_utils import calculate_contrast_ratio, get_complementary_color
from enhanced_color_picker.models.image_data import ImageData
from enhanced_color_picker.models.color_data import ColorData


class PerformanceTimer:
    """Context manager for timing operations."""
    
    def __init__(self, operation_name):
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
    
    @property
    def elapsed_time(self):
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None


class TestImageProcessingPerformance(unittest.TestCase):
    """Test performance of image processing operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.image_service = ImageService()
        self.analysis_service = AnalysisService()
        
        # Create test images of different sizes
        self.test_images = {}
        
        # Small image (100x100)
        small_image = Image.new('RGB', (100, 100))
        pixels = []
        for y in range(100):
            for x in range(100):
                r = int((x / 100) * 255)
                g = int((y / 100) * 255)
                b = int(((x + y) / 200) * 255)
                pixels.append((r, g, b))
        small_image.putdata(pixels)
        self.test_images['small'] = os.path.join(self.temp_dir, 'small.png')
        small_image.save(self.test_images['small'])
        
        # Medium image (500x500)
        medium_image = Image.new('RGB', (500, 500))
        pixels = []
        for y in range(500):
            for x in range(500):
                r = int((x / 500) * 255)
                g = int((y / 500) * 255)
                b = int(((x + y) / 1000) * 255)
                pixels.append((r, g, b))
        medium_image.putdata(pixels)
        self.test_images['medium'] = os.path.join(self.temp_dir, 'medium.png')
        medium_image.save(self.test_images['medium'])
        
        # Large image (1000x1000)
        large_image = Image.new('RGB', (1000, 1000))
        pixels = []
        for y in range(1000):
            for x in range(1000):
                r = int((x / 1000) * 255)
                g = int((y / 1000) * 255)
                b = int(((x + y) / 2000) * 255)
                pixels.append((r, g, b))
        large_image.putdata(pixels)
        self.test_images['large'] = os.path.join(self.temp_dir, 'large.png')
        large_image.save(self.test_images['large'])
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_image_loading_performance(self):
        """Test image loading performance across different sizes."""
        performance_results = {}
        
        for size_name, image_path in self.test_images.items():
            with PerformanceTimer(f"load_{size_name}_image") as timer:
                image_data = ImageData.from_file(image_path)
            
            performance_results[size_name] = {
                'load_time': timer.elapsed_time,
                'pixels': image_data.total_pixels,
                'file_size': os.path.getsize(image_path)
            }
            
            # Performance expectations
            if size_name == 'small':
                self.assertLess(timer.elapsed_time, 0.1, "Small image loading too slow")
            elif size_name == 'medium':
                self.assertLess(timer.elapsed_time, 0.5, "Medium image loading too slow")
            elif size_name == 'large':
                self.assertLess(timer.elapsed_time, 2.0, "Large image loading too slow")
        
        # Print performance results
        print("\nImage Loading Performance:")
        for size, results in performance_results.items():
            print(f"{size}: {results['load_time']:.4f}s, "
                  f"{results['pixels']} pixels, "
                  f"{results['file_size']} bytes")
    
    def test_dominant_color_extraction_performance(self):
        """Test dominant color extraction performance."""
        performance_results = {}
        
        for size_name, image_path in self.test_images.items():
            image_data = ImageData.from_file(image_path)
            
            # Test different color counts
            for num_colors in [3, 5, 10]:
                with PerformanceTimer(f"extract_{num_colors}_colors_{size_name}") as timer:
                    dominant_colors = extract_dominant_colors(image_data, num_colors=num_colors)
                
                key = f"{size_name}_{num_colors}_colors"
                performance_results[key] = {
                    'extraction_time': timer.elapsed_time,
                    'colors_found': len(dominant_colors),
                    'pixels': image_data.total_pixels
                }
                
                # Performance expectations
                if size_name == 'small':
                    self.assertLess(timer.elapsed_time, 1.0, f"Small image {num_colors}-color extraction too slow")
                elif size_name == 'medium':
                    self.assertLess(timer.elapsed_time, 5.0, f"Medium image {num_colors}-color extraction too slow")
                elif size_name == 'large':
                    self.assertLess(timer.elapsed_time, 15.0, f"Large image {num_colors}-color extraction too slow")
        
        # Print performance results
        print("\nDominant Color Extraction Performance:")
        for key, results in performance_results.items():
            print(f"{key}: {results['extraction_time']:.4f}s, "
                  f"{results['colors_found']} colors found")
    
    def test_average_color_calculation_performance(self):
        """Test average color calculation performance."""
        performance_results = {}
        
        for size_name, image_path in self.test_images.items():
            image_data = ImageData.from_file(image_path)
            
            with PerformanceTimer(f"average_color_{size_name}") as timer:
                average_color = calculate_average_color(image_data)
            
            performance_results[size_name] = {
                'calculation_time': timer.elapsed_time,
                'pixels': image_data.total_pixels,
                'average_color': average_color.hex
            }
            
            # Performance expectations
            if size_name == 'small':
                self.assertLess(timer.elapsed_time, 0.1, "Small image average color calculation too slow")
            elif size_name == 'medium':
                self.assertLess(timer.elapsed_time, 0.5, "Medium image average color calculation too slow")
            elif size_name == 'large':
                self.assertLess(timer.elapsed_time, 2.0, "Large image average color calculation too slow")
        
        # Print performance results
        print("\nAverage Color Calculation Performance:")
        for size, results in performance_results.items():
            print(f"{size}: {results['calculation_time']:.4f}s, "
                  f"color: {results['average_color']}")
    
    def test_image_resize_performance(self):
        """Test image resizing performance."""
        performance_results = {}
        
        for size_name, image_path in self.test_images.items():
            image_data = ImageData.from_file(image_path)
            
            # Test different resize targets
            resize_targets = [(200, 200), (500, 500), (800, 800)]
            
            for target_size in resize_targets:
                with PerformanceTimer(f"resize_{size_name}_to_{target_size[0]}x{target_size[1]}") as timer:
                    resized_image = image_data.resize(target_size)
                
                key = f"{size_name}_to_{target_size[0]}x{target_size[1]}"
                performance_results[key] = {
                    'resize_time': timer.elapsed_time,
                    'original_pixels': image_data.total_pixels,
                    'new_pixels': resized_image.total_pixels
                }
                
                # Performance expectations (resizing should be fast)
                self.assertLess(timer.elapsed_time, 1.0, f"Image resize {key} too slow")
        
        # Print performance results
        print("\nImage Resize Performance:")
        for key, results in performance_results.items():
            print(f"{key}: {results['resize_time']:.4f}s")


class TestColorOperationPerformance(unittest.TestCase):
    """Test performance of color operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.color_service = ColorService()
        
        # Create test colors
        self.test_colors = [
            ColorData(255, 0, 0),    # Red
            ColorData(0, 255, 0),    # Green
            ColorData(0, 0, 255),    # Blue
            ColorData(255, 255, 0),  # Yellow
            ColorData(255, 0, 255),  # Magenta
            ColorData(0, 255, 255),  # Cyan
            ColorData(128, 128, 128), # Gray
            ColorData(255, 128, 64), # Orange
            ColorData(64, 128, 255), # Light Blue
            ColorData(128, 255, 64), # Light Green
        ]
    
    def test_color_conversion_performance(self):
        """Test color conversion performance."""
        num_iterations = 1000
        
        with PerformanceTimer("batch_color_conversions") as timer:
            for _ in range(num_iterations):
                for color in self.test_colors:
                    # Convert to all formats
                    conversions = self.color_service.convert_to_all_formats(color)
        
        total_conversions = num_iterations * len(self.test_colors) * 5  # 5 formats
        conversions_per_second = total_conversions / timer.elapsed_time
        
        print(f"\nColor Conversion Performance:")
        print(f"Total conversions: {total_conversions}")
        print(f"Time: {timer.elapsed_time:.4f}s")
        print(f"Conversions per second: {conversions_per_second:.0f}")
        
        # Should be able to do at least 10,000 conversions per second
        self.assertGreater(conversions_per_second, 10000, "Color conversions too slow")
    
    def test_contrast_calculation_performance(self):
        """Test contrast ratio calculation performance."""
        num_iterations = 1000
        
        with PerformanceTimer("batch_contrast_calculations") as timer:
            for _ in range(num_iterations):
                for i, color1 in enumerate(self.test_colors):
                    for j, color2 in enumerate(self.test_colors):
                        if i != j:  # Don't compare color with itself
                            contrast_ratio = calculate_contrast_ratio(color1, color2)
        
        total_calculations = num_iterations * len(self.test_colors) * (len(self.test_colors) - 1)
        calculations_per_second = total_calculations / timer.elapsed_time
        
        print(f"\nContrast Calculation Performance:")
        print(f"Total calculations: {total_calculations}")
        print(f"Time: {timer.elapsed_time:.4f}s")
        print(f"Calculations per second: {calculations_per_second:.0f}")
        
        # Should be able to do at least 50,000 calculations per second
        self.assertGreater(calculations_per_second, 50000, "Contrast calculations too slow")
    
    def test_color_harmony_generation_performance(self):
        """Test color harmony generation performance."""
        harmony_types = ['complementary', 'analogous', 'triadic', 'tetradic', 'monochromatic']
        num_iterations = 100
        
        performance_results = {}
        
        for harmony_type in harmony_types:
            with PerformanceTimer(f"generate_{harmony_type}_harmony") as timer:
                for _ in range(num_iterations):
                    for color in self.test_colors:
                        harmony = self.color_service.generate_color_harmony(color, harmony_type)
            
            total_generations = num_iterations * len(self.test_colors)
            generations_per_second = total_generations / timer.elapsed_time
            
            performance_results[harmony_type] = {
                'time': timer.elapsed_time,
                'generations_per_second': generations_per_second
            }
            
            # Should be able to generate at least 1,000 harmonies per second
            self.assertGreater(generations_per_second, 1000, 
                             f"{harmony_type} harmony generation too slow")
        
        print(f"\nColor Harmony Generation Performance:")
        for harmony_type, results in performance_results.items():
            print(f"{harmony_type}: {results['generations_per_second']:.0f} generations/sec")
    
    def test_color_analysis_performance(self):
        """Test comprehensive color analysis performance."""
        num_iterations = 100
        
        with PerformanceTimer("comprehensive_color_analysis") as timer:
            for _ in range(num_iterations):
                for color in self.test_colors:
                    analysis = self.color_service.analyze_color(color)
        
        total_analyses = num_iterations * len(self.test_colors)
        analyses_per_second = total_analyses / timer.elapsed_time
        
        print(f"\nColor Analysis Performance:")
        print(f"Total analyses: {total_analyses}")
        print(f"Time: {timer.elapsed_time:.4f}s")
        print(f"Analyses per second: {analyses_per_second:.0f}")
        
        # Should be able to do at least 500 comprehensive analyses per second
        self.assertGreater(analyses_per_second, 500, "Color analysis too slow")


class TestPaletteOperationPerformance(unittest.TestCase):
    """Test performance of palette operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.palette_service = PaletteService(self.temp_dir)
        
        # Create test colors
        self.test_colors = [ColorData(i * 25, (i * 30) % 256, (i * 45) % 256) 
                           for i in range(50)]  # 50 colors
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_palette_creation_performance(self):
        """Test palette creation performance."""
        num_palettes = 100
        
        with PerformanceTimer("create_palettes") as timer:
            for i in range(num_palettes):
                palette = self.palette_service.create_palette(
                    name=f"Test Palette {i}",
                    colors=self.test_colors[:10],  # 10 colors per palette
                    description=f"Test palette number {i}"
                )
        
        palettes_per_second = num_palettes / timer.elapsed_time
        
        print(f"\nPalette Creation Performance:")
        print(f"Created {num_palettes} palettes in {timer.elapsed_time:.4f}s")
        print(f"Palettes per second: {palettes_per_second:.0f}")
        
        # Should be able to create at least 1,000 palettes per second
        self.assertGreater(palettes_per_second, 1000, "Palette creation too slow")
    
    def test_palette_save_load_performance(self):
        """Test palette save and load performance."""
        # Create test palettes
        palettes = []
        for i in range(10):
            palette = self.palette_service.create_palette(
                name=f"Save Test Palette {i}",
                colors=self.test_colors[:20],  # 20 colors per palette
                description=f"Save test palette {i}"
            )
            palettes.append(palette)
        
        # Test save performance
        with PerformanceTimer("save_palettes") as save_timer:
            saved_paths = []
            for palette in palettes:
                path = self.palette_service.save_palette(palette)
                saved_paths.append(path)
        
        save_rate = len(palettes) / save_timer.elapsed_time
        
        # Test load performance
        with PerformanceTimer("load_palettes") as load_timer:
            loaded_palettes = []
            for path in saved_paths:
                palette = self.palette_service.load_palette(path)
                loaded_palettes.append(palette)
        
        load_rate = len(saved_paths) / load_timer.elapsed_time
        
        print(f"\nPalette Save/Load Performance:")
        print(f"Save rate: {save_rate:.0f} palettes/sec")
        print(f"Load rate: {load_rate:.0f} palettes/sec")
        
        # Performance expectations
        self.assertGreater(save_rate, 50, "Palette saving too slow")
        self.assertGreater(load_rate, 100, "Palette loading too slow")
        
        # Verify data integrity
        for original, loaded in zip(palettes, loaded_palettes):
            self.assertEqual(original.name, loaded.name)
            self.assertEqual(len(original.colors), len(loaded.colors))
    
    def test_palette_export_performance(self):
        """Test palette export performance."""
        from enhanced_color_picker.models.enums import ExportFormat
        
        # Create large palette
        large_palette = self.palette_service.create_palette(
            name="Large Export Test",
            colors=self.test_colors,  # 50 colors
            description="Large palette for export testing"
        )
        
        export_formats = [
            ExportFormat.JSON,
            ExportFormat.CSS,
            ExportFormat.SCSS,
            ExportFormat.GPL
        ]
        
        performance_results = {}
        
        for export_format in export_formats:
            export_path = os.path.join(self.temp_dir, f"export.{export_format.value}")
            
            with PerformanceTimer(f"export_{export_format.value}") as timer:
                self.palette_service.export_palette(large_palette, export_format, export_path)
            
            file_size = os.path.getsize(export_path)
            
            performance_results[export_format.value] = {
                'time': timer.elapsed_time,
                'file_size': file_size,
                'colors': len(large_palette.colors)
            }
            
            # Should export quickly
            self.assertLess(timer.elapsed_time, 1.0, f"{export_format.value} export too slow")
        
        print(f"\nPalette Export Performance:")
        for format_name, results in performance_results.items():
            print(f"{format_name}: {results['time']:.4f}s, {results['file_size']} bytes")


class TestMemoryUsagePerformance(unittest.TestCase):
    """Test memory usage and performance under load."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.process = psutil.Process()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def get_memory_usage(self):
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024
    
    def test_memory_usage_under_load(self):
        """Test memory usage under heavy load."""
        initial_memory = self.get_memory_usage()
        
        # Create large image
        large_image = Image.new('RGB', (2000, 2000))
        pixels = []
        for y in range(2000):
            for x in range(2000):
                r = (x * y) % 256
                g = (x + y) % 256
                b = (x - y) % 256
                pixels.append((r, g, b))
        large_image.putdata(pixels)
        
        large_image_path = os.path.join(self.temp_dir, 'large_memory_test.png')
        large_image.save(large_image_path)
        
        # Load and process image multiple times
        max_memory = initial_memory
        
        for i in range(5):
            image_data = ImageData.from_file(large_image_path)
            
            # Extract dominant colors
            dominant_colors = extract_dominant_colors(image_data, num_colors=10)
            
            # Calculate average color
            average_color = calculate_average_color(image_data)
            
            # Create palette
            palette_service = PaletteService(self.temp_dir)
            palette = palette_service.create_palette(
                f"Memory Test {i}",
                dominant_colors + [average_color]
            )
            
            current_memory = self.get_memory_usage()
            max_memory = max(max_memory, current_memory)
            
            # Clean up references
            del image_data, dominant_colors, average_color, palette
        
        memory_increase = max_memory - initial_memory
        
        print(f"\nMemory Usage Test:")
        print(f"Initial memory: {initial_memory:.1f} MB")
        print(f"Maximum memory: {max_memory:.1f} MB")
        print(f"Memory increase: {memory_increase:.1f} MB")
        
        # Memory increase should be reasonable (less than 500MB for this test)
        self.assertLess(memory_increase, 500, "Excessive memory usage")
    
    def test_concurrent_operations_performance(self):
        """Test performance under concurrent operations."""
        # Create test image
        test_image = Image.new('RGB', (500, 500))
        pixels = []
        for y in range(500):
            for x in range(500):
                pixels.append((x % 256, y % 256, (x + y) % 256))
        test_image.putdata(pixels)
        
        test_image_path = os.path.join(self.temp_dir, 'concurrent_test.png')
        test_image.save(test_image_path)
        
        def process_image():
            """Process image in a thread."""
            image_data = ImageData.from_file(test_image_path)
            dominant_colors = extract_dominant_colors(image_data, num_colors=5)
            average_color = calculate_average_color(image_data)
            return len(dominant_colors)
        
        # Test concurrent processing
        num_threads = 4
        num_operations_per_thread = 5
        
        with PerformanceTimer("concurrent_operations") as timer:
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = []
                for _ in range(num_threads * num_operations_per_thread):
                    future = executor.submit(process_image)
                    futures.append(future)
                
                # Wait for all operations to complete
                results = [future.result() for future in futures]
        
        total_operations = len(results)
        operations_per_second = total_operations / timer.elapsed_time
        
        print(f"\nConcurrent Operations Performance:")
        print(f"Total operations: {total_operations}")
        print(f"Time: {timer.elapsed_time:.4f}s")
        print(f"Operations per second: {operations_per_second:.1f}")
        
        # Should handle concurrent operations efficiently
        self.assertGreater(operations_per_second, 5, "Concurrent operations too slow")
        
        # All operations should succeed
        self.assertEqual(len(results), total_operations)
        for result in results:
            self.assertGreater(result, 0)  # Should find some colors


class TestUIPerformance(unittest.TestCase):
    """Test UI performance and responsiveness."""
    
    def setUp(self):
        """Set up test fixtures."""
        try:
            import tkinter as tk
            self.root = tk.Tk()
            self.root.withdraw()
            self.ui_available = True
        except:
            self.ui_available = False
    
    def tearDown(self):
        """Clean up test fixtures."""
        if self.ui_available:
            self.root.destroy()
    
    def test_ui_update_performance(self):
        """Test UI update performance."""
        if not self.ui_available:
            self.skipTest("No display available for UI tests")
        
        import tkinter as tk
        from enhanced_color_picker.core.event_bus import EventBus
        from enhanced_color_picker.ui.components.color_panel import ColorPanel
        
        event_bus = EventBus()
        color_panel = ColorPanel(self.root, event_bus)
        
        # Test rapid color updates
        test_colors = [ColorData(i * 10, (i * 15) % 256, (i * 20) % 256) 
                      for i in range(100)]
        
        with PerformanceTimer("ui_color_updates") as timer:
            for color in test_colors:
                color_panel.display_color(color)
                self.root.update_idletasks()
        
        updates_per_second = len(test_colors) / timer.elapsed_time
        
        print(f"\nUI Update Performance:")
        print(f"Color updates per second: {updates_per_second:.0f}")
        
        # Should handle at least 50 updates per second
        self.assertGreater(updates_per_second, 50, "UI updates too slow")
    
    def test_canvas_rendering_performance(self):
        """Test canvas rendering performance."""
        if not self.ui_available:
            self.skipTest("No display available for UI tests")
        
        import tkinter as tk
        from enhanced_color_picker.core.event_bus import EventBus
        from enhanced_color_picker.ui.components.image_canvas import EnhancedImageCanvas
        
        event_bus = EventBus()
        canvas = EnhancedImageCanvas(self.root, event_bus)
        
        # Create test image
        temp_dir = tempfile.mkdtemp()
        try:
            test_image = Image.new('RGB', (200, 200))
            pixels = []
            for y in range(200):
                for x in range(200):
                    pixels.append((x % 256, y % 256, (x + y) % 256))
            test_image.putdata(pixels)
            
            test_image_path = os.path.join(temp_dir, 'canvas_test.png')
            test_image.save(test_image_path)
            
            image_data = ImageData.from_file(test_image_path)
            
            # Test canvas rendering
            with PerformanceTimer("canvas_rendering") as timer:
                for _ in range(10):
                    canvas.display_image(image_data)
                    self.root.update_idletasks()
            
            renders_per_second = 10 / timer.elapsed_time
            
            print(f"\nCanvas Rendering Performance:")
            print(f"Renders per second: {renders_per_second:.1f}")
            
            # Should handle at least 5 renders per second
            self.assertGreater(renders_per_second, 5, "Canvas rendering too slow")
            
        finally:
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    # Run performance tests
    print("Running Enhanced Color Picker Performance Tests")
    print("=" * 50)
    
    unittest.main(verbosity=2)