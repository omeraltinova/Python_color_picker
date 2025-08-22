"""
Test configuration and fixtures for pytest (if used).
"""

import pytest
import tempfile
import os
import shutil
from PIL import Image

from enhanced_color_picker.models.color_data import ColorData
from enhanced_color_picker.models.image_data import ImageData


@pytest.fixture
def temp_directory():
    """Create a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_colors():
    """Provide sample colors for testing."""
    return [
        ColorData(255, 0, 0),    # Red
        ColorData(0, 255, 0),    # Green
        ColorData(0, 0, 255),    # Blue
        ColorData(255, 255, 0),  # Yellow
        ColorData(255, 0, 255),  # Magenta
        ColorData(0, 255, 255),  # Cyan
        ColorData(255, 255, 255), # White
        ColorData(0, 0, 0),      # Black
        ColorData(128, 128, 128), # Gray
    ]


@pytest.fixture
def test_image(temp_directory):
    """Create a test image for testing."""
    # Create a simple test image
    image = Image.new('RGB', (50, 50))
    pixels = []
    for y in range(50):
        for x in range(50):
            if x < 25:
                pixels.append((255, 0, 0))  # Red half
            else:
                pixels.append((0, 0, 255))  # Blue half
    image.putdata(pixels)
    
    image_path = os.path.join(temp_directory, 'test_image.png')
    image.save(image_path)
    
    return ImageData.from_file(image_path)


@pytest.fixture
def large_test_image(temp_directory):
    """Create a large test image for performance testing."""
    image = Image.new('RGB', (500, 500))
    pixels = []
    for y in range(500):
        for x in range(500):
            r = int((x / 500) * 255)
            g = int((y / 500) * 255)
            b = int(((x + y) / 1000) * 255)
            pixels.append((r, g, b))
    image.putdata(pixels)
    
    image_path = os.path.join(temp_directory, 'large_test_image.png')
    image.save(image_path)
    
    return ImageData.from_file(image_path)


@pytest.fixture
def mock_services():
    """Provide mock services for testing."""
    from unittest.mock import Mock
    
    return {
        'image_service': Mock(),
        'color_service': Mock(),
        'palette_service': Mock(),
        'analysis_service': Mock(),
        'export_service': Mock()
    }


# Test markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "ui: mark test as a UI test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_display: mark test as requiring a display"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "ui" in str(item.fspath):
            item.add_marker(pytest.mark.ui)
            item.add_marker(pytest.mark.requires_display)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)


# Skip tests that require display if no display is available
def pytest_runtest_setup(item):
    """Setup for individual test runs."""
    if "requires_display" in [mark.name for mark in item.iter_markers()]:
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            root.destroy()
        except tk.TclError:
            pytest.skip("No display available for UI tests")


# Custom assertions
def assert_color_equal(color1, color2, tolerance=0):
    """Assert that two colors are equal within tolerance."""
    assert abs(color1.r - color2.r) <= tolerance, f"Red values differ: {color1.r} vs {color2.r}"
    assert abs(color1.g - color2.g) <= tolerance, f"Green values differ: {color1.g} vs {color2.g}"
    assert abs(color1.b - color2.b) <= tolerance, f"Blue values differ: {color1.b} vs {color2.b}"
    assert abs(color1.alpha - color2.alpha) <= tolerance/255, f"Alpha values differ: {color1.alpha} vs {color2.alpha}"


def assert_performance_acceptable(elapsed_time, max_time, operation_name):
    """Assert that operation completed within acceptable time."""
    assert elapsed_time <= max_time, f"{operation_name} took {elapsed_time:.4f}s, expected <= {max_time}s"


# Add custom assertions to pytest namespace
pytest.assert_color_equal = assert_color_equal
pytest.assert_performance_acceptable = assert_performance_acceptable