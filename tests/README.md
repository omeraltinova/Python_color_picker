# Enhanced Color Picker - Test Suite

This directory contains the comprehensive test suite for the Enhanced Color Picker application.

## Test Structure

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── test_color_utils.py         # Color utility function tests
│   ├── test_image_utils.py         # Image processing utility tests
│   ├── test_validation_utils.py    # Input validation tests
│   ├── test_color_service.py       # Color service tests
│   └── test_palette_service.py     # Palette service tests
├── integration/             # Integration tests for service interactions
│   └── test_services_integration.py # Service layer integration tests
├── ui/                      # UI component and interaction tests
│   ├── test_component_interactions.py # UI component interaction tests
│   └── test_accessibility.py       # Accessibility compliance tests
├── performance/             # Performance and benchmark tests
│   └── test_performance_benchmarks.py # Performance benchmark tests
├── test_runner.py          # Custom test runner with colored output
├── conftest.py             # Test configuration and fixtures
└── README.md               # This file
```

## Test Categories

### Unit Tests
- **Color Utilities**: Test color conversion, contrast calculation, harmony generation
- **Image Utilities**: Test image loading, processing, dominant color extraction
- **Validation Utilities**: Test input validation, file security, memory limits
- **Services**: Test individual service classes (ColorService, PaletteService, etc.)

### Integration Tests
- **Service Integration**: Test interactions between different services
- **Event Bus**: Test event-driven communication between components
- **Workflow Tests**: Test complete user workflows from start to finish

### UI Tests
- **Component Interactions**: Test UI component communication and state management
- **Accessibility**: Test WCAG compliance, keyboard navigation, screen reader support
- **User Workflows**: Test complete UI workflows and error handling

### Performance Tests
- **Image Processing**: Benchmark image loading, resizing, color extraction
- **Color Operations**: Benchmark color conversions, contrast calculations
- **Memory Usage**: Test memory efficiency under load
- **Concurrent Operations**: Test performance under concurrent usage

## Running Tests

### Using the Custom Test Runner

```bash
# Run all tests
python tests/test_runner.py

# Run specific category
python tests/test_runner.py unit
python tests/test_runner.py integration
python tests/test_runner.py ui
python tests/test_runner.py performance

# Run with different verbosity
python tests/test_runner.py -v 1  # Minimal output
python tests/test_runner.py -v 2  # Detailed output (default)

# Run specific test
python tests/test_runner.py -t tests.unit.test_color_utils.TestColorUtils.test_calculate_contrast_ratio

# List all available tests
python tests/test_runner.py -l

# Stop on first failure
python tests/test_runner.py -f

# Run tests matching pattern
python tests/test_runner.py -p "test_color*"
```

### Using Standard unittest

```bash
# Run all tests
python -m unittest discover tests

# Run specific test file
python -m unittest tests.unit.test_color_utils

# Run specific test class
python -m unittest tests.unit.test_color_utils.TestColorUtils

# Run specific test method
python -m unittest tests.unit.test_color_utils.TestColorUtils.test_calculate_contrast_ratio
```

### Using pytest (if installed)

```bash
# Install pytest
pip install pytest pytest-cov

# Run all tests
pytest tests/

# Run specific category
pytest tests/unit/
pytest tests/integration/
pytest tests/ui/
pytest tests/performance/

# Run with coverage
pytest tests/ --cov=enhanced_color_picker

# Run only unit tests
pytest -m unit

# Run excluding slow tests
pytest -m "not slow"

# Run with verbose output
pytest -v tests/
```

## Test Requirements

### Basic Requirements
- Python 3.8+
- PIL/Pillow
- All project dependencies

### Optional Requirements
- `pytest` - For pytest runner support
- `pytest-cov` - For coverage reporting
- `psutil` - For memory usage monitoring in performance tests
- `tkinter` - For UI tests (usually included with Python)

### Display Requirements
UI tests require a display environment. On headless systems, you can:

1. Skip UI tests:
   ```bash
   python tests/test_runner.py unit integration performance
   ```

2. Use virtual display (Linux):
   ```bash
   sudo apt-get install xvfb
   xvfb-run -a python tests/test_runner.py
   ```

## Test Configuration

### Environment Variables
- `SKIP_UI_TESTS` - Set to skip UI tests
- `SKIP_PERFORMANCE_TESTS` - Set to skip performance tests
- `TEST_TIMEOUT` - Set test timeout in seconds

### Test Data
Tests use temporary directories and generated test data. No external test data files are required.

## Writing New Tests

### Unit Test Example
```python
import unittest
from enhanced_color_picker.utils.color_utils import calculate_contrast_ratio
from enhanced_color_picker.models.color_data import ColorData

class TestNewFeature(unittest.TestCase):
    def setUp(self):
        self.test_color = ColorData(255, 0, 0)
    
    def test_new_functionality(self):
        result = some_function(self.test_color)
        self.assertEqual(result, expected_value)
    
    def test_edge_case(self):
        with self.assertRaises(ValueError):
            some_function(invalid_input)
```

### Integration Test Example
```python
import unittest
from enhanced_color_picker.services.color_service import ColorService
from enhanced_color_picker.services.palette_service import PaletteService

class TestServiceIntegration(unittest.TestCase):
    def setUp(self):
        self.color_service = ColorService()
        self.palette_service = PaletteService()
    
    def test_workflow(self):
        # Test complete workflow
        color = ColorData(255, 0, 0)
        harmony = self.color_service.generate_color_harmony(color, "triadic")
        palette = self.palette_service.create_palette("Test", harmony['colors'])
        self.assertEqual(len(palette.colors), 2)
```

### Performance Test Example
```python
import unittest
import time

class TestPerformance(unittest.TestCase):
    def test_operation_performance(self):
        start_time = time.perf_counter()
        
        # Perform operation
        result = expensive_operation()
        
        elapsed_time = time.perf_counter() - start_time
        
        # Assert performance requirement
        self.assertLess(elapsed_time, 1.0, "Operation too slow")
        self.assertIsNotNone(result)
```

## Test Coverage

The test suite aims for high coverage across all components:

- **Unit Tests**: 90%+ coverage of utility functions and service methods
- **Integration Tests**: Coverage of service interactions and workflows
- **UI Tests**: Coverage of component interactions and user workflows
- **Performance Tests**: Benchmark coverage of critical operations

## Continuous Integration

Tests are designed to run in CI environments:

- All tests should be deterministic and not depend on external resources
- UI tests can be skipped in headless environments
- Performance tests include reasonable timeouts for different hardware
- Memory usage tests account for CI environment limitations

## Troubleshooting

### Common Issues

1. **UI Tests Failing**: Ensure display is available or skip UI tests
2. **Performance Tests Failing**: May need adjustment for slower hardware
3. **Import Errors**: Ensure project root is in Python path
4. **Memory Tests Failing**: May need adjustment for memory-constrained environments

### Debug Mode
Run tests with maximum verbosity for debugging:
```bash
python tests/test_runner.py -v 2 --failfast
```

### Test Isolation
Each test is designed to be independent and can be run in isolation:
```bash
python tests/test_runner.py -t tests.unit.test_color_utils.TestColorUtils.test_specific_method
```