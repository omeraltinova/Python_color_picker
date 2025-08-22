"""
Test runner for the Enhanced Color Picker test suite.
"""

import unittest
import sys
import os
import argparse
import time
from io import StringIO

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class ColoredTestResult(unittest.TextTestResult):
    """Test result class with colored output."""
    
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.success_count = 0
        self.start_time = None
    
    def startTest(self, test):
        super().startTest(test)
        if self.start_time is None:
            self.start_time = time.time()
    
    def addSuccess(self, test):
        super().addSuccess(test)
        self.success_count += 1
        if self.verbosity > 1:
            self.stream.write(f"\033[92m✓\033[0m {test._testMethodName}\n")
    
    def addError(self, test, err):
        super().addError(test, err)
        if self.verbosity > 1:
            self.stream.write(f"\033[91m✗\033[0m {test._testMethodName} (ERROR)\n")
    
    def addFailure(self, test, err):
        super().addFailure(test, err)
        if self.verbosity > 1:
            self.stream.write(f"\033[91m✗\033[0m {test._testMethodName} (FAIL)\n")
    
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        if self.verbosity > 1:
            self.stream.write(f"\033[93m-\033[0m {test._testMethodName} (SKIP: {reason})\n")
    
    def printSummary(self):
        """Print test summary with colors."""
        total_time = time.time() - self.start_time if self.start_time else 0
        
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        
        total_tests = self.testsRun
        print(f"Total tests run: {total_tests}")
        print(f"\033[92mPassed: {self.success_count}\033[0m")
        
        if self.failures:
            print(f"\033[91mFailed: {len(self.failures)}\033[0m")
        
        if self.errors:
            print(f"\033[91mErrors: {len(self.errors)}\033[0m")
        
        if self.skipped:
            print(f"\033[93mSkipped: {len(self.skipped)}\033[0m")
        
        print(f"Time: {total_time:.2f}s")
        
        if self.wasSuccessful():
            print(f"\n\033[92m✓ ALL TESTS PASSED!\033[0m")
        else:
            print(f"\n\033[91m✗ SOME TESTS FAILED!\033[0m")


class TestSuiteRunner:
    """Main test suite runner."""
    
    def __init__(self):
        self.test_categories = {
            'unit': 'tests.unit',
            'integration': 'tests.integration',
            'ui': 'tests.ui',
            'performance': 'tests.performance'
        }
    
    def discover_tests(self, category=None, pattern='test*.py'):
        """Discover tests in specified category or all categories."""
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        if category and category in self.test_categories:
            # Load specific category
            try:
                category_suite = loader.discover(
                    self.test_categories[category],
                    pattern=pattern,
                    top_level_dir='.'
                )
                suite.addTest(category_suite)
            except ImportError as e:
                print(f"Warning: Could not load {category} tests: {e}")
        else:
            # Load all categories
            for cat_name, cat_path in self.test_categories.items():
                try:
                    category_suite = loader.discover(
                        cat_path,
                        pattern=pattern,
                        top_level_dir='.'
                    )
                    suite.addTest(category_suite)
                except ImportError as e:
                    print(f"Warning: Could not load {cat_name} tests: {e}")
        
        return suite
    
    def run_tests(self, category=None, verbosity=2, failfast=False, pattern='test*.py'):
        """Run the test suite."""
        print("Enhanced Color Picker Test Suite")
        print("="*50)
        
        if category:
            print(f"Running {category} tests...")
        else:
            print("Running all tests...")
        
        # Discover tests
        suite = self.discover_tests(category, pattern)
        
        if suite.countTestCases() == 0:
            print("No tests found!")
            return False
        
        print(f"Found {suite.countTestCases()} tests")
        print("-"*50)
        
        # Run tests
        runner = unittest.TextTestRunner(
            verbosity=verbosity,
            failfast=failfast,
            resultclass=ColoredTestResult,
            stream=sys.stdout
        )
        
        result = runner.run(suite)
        
        # Print summary
        if hasattr(result, 'printSummary'):
            result.printSummary()
        
        return result.wasSuccessful()
    
    def run_specific_test(self, test_path, verbosity=2):
        """Run a specific test by path (e.g., 'tests.unit.test_color_utils.TestColorUtils.test_calculate_contrast_ratio')."""
        print(f"Running specific test: {test_path}")
        print("-"*50)
        
        loader = unittest.TestLoader()
        
        try:
            suite = loader.loadTestsFromName(test_path)
        except (ImportError, AttributeError) as e:
            print(f"Error loading test: {e}")
            return False
        
        runner = unittest.TextTestRunner(
            verbosity=verbosity,
            resultclass=ColoredTestResult,
            stream=sys.stdout
        )
        
        result = runner.run(suite)
        
        if hasattr(result, 'printSummary'):
            result.printSummary()
        
        return result.wasSuccessful()
    
    def list_tests(self, category=None):
        """List all available tests."""
        suite = self.discover_tests(category)
        
        print("Available tests:")
        print("-"*30)
        
        def print_test_cases(test_suite, indent=0):
            for test in test_suite:
                if isinstance(test, unittest.TestSuite):
                    print_test_cases(test, indent)
                else:
                    test_name = f"{test.__class__.__module__}.{test.__class__.__name__}.{test._testMethodName}"
                    print("  " * indent + test_name)
        
        print_test_cases(suite)
        print(f"\nTotal: {suite.countTestCases()} tests")


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(description='Enhanced Color Picker Test Runner')
    
    parser.add_argument(
        'category',
        nargs='?',
        choices=['unit', 'integration', 'ui', 'performance', 'all'],
        default='all',
        help='Test category to run (default: all)'
    )
    
    parser.add_argument(
        '-v', '--verbosity',
        type=int,
        choices=[0, 1, 2],
        default=2,
        help='Test output verbosity (default: 2)'
    )
    
    parser.add_argument(
        '-f', '--failfast',
        action='store_true',
        help='Stop on first failure'
    )
    
    parser.add_argument(
        '-p', '--pattern',
        default='test*.py',
        help='Test file pattern (default: test*.py)'
    )
    
    parser.add_argument(
        '-t', '--test',
        help='Run specific test (e.g., tests.unit.test_color_utils.TestColorUtils.test_calculate_contrast_ratio)'
    )
    
    parser.add_argument(
        '-l', '--list',
        action='store_true',
        help='List all available tests'
    )
    
    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored output'
    )
    
    args = parser.parse_args()
    
    # Disable colors if requested or if not in a terminal
    if args.no_color or not sys.stdout.isatty():
        # Remove color codes from ColoredTestResult
        ColoredTestResult.addSuccess = unittest.TextTestResult.addSuccess
        ColoredTestResult.addError = unittest.TextTestResult.addError
        ColoredTestResult.addFailure = unittest.TextTestResult.addFailure
        ColoredTestResult.addSkip = unittest.TextTestResult.addSkip
    
    runner = TestSuiteRunner()
    
    if args.list:
        category = None if args.category == 'all' else args.category
        runner.list_tests(category)
        return
    
    if args.test:
        success = runner.run_specific_test(args.test, args.verbosity)
    else:
        category = None if args.category == 'all' else args.category
        success = runner.run_tests(
            category=category,
            verbosity=args.verbosity,
            failfast=args.failfast,
            pattern=args.pattern
        )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()