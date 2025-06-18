#!/usr/bin/env python3
"""
Comprehensive test runner for the Virtual Bot Environment 3D project.

This script runs all unit tests and provides detailed output including:
- Test results summary
- Coverage information
- Performance metrics
- Failed test details
- Progress tracking for long-running tests
"""

import unittest
import sys
import time
import os
import signal
import threading
from io import StringIO


class TimeoutError(Exception):
    """Custom timeout exception."""
    pass


class ProgressTestRunner(unittest.TextTestRunner):
    """Test runner with progress tracking and timeout support."""
    
    def __init__(self, timeout=30, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timeout = timeout
        self.current_test = None
        self.test_start_time = None
        
    def run(self, test):
        """Run tests with progress tracking."""
        self.test_start_time = time.time()
        self.current_test = None
        
        # Set up timeout handler
        def timeout_handler(signum, frame):
            if self.current_test:
                raise TimeoutError(f"Test {self.current_test} timed out after {self.timeout} seconds")
        
        # Set up signal handler for timeout (Unix-like systems)
        if hasattr(signal, 'SIGALRM'):
            signal.signal(signal.SIGALRM, timeout_handler)
        
        return super().run(test)
    
    def _makeResult(self):
        """Create a custom result object with progress tracking."""
        result = super()._makeResult()
        original_startTest = result.startTest
        original_stopTest = result.stopTest
        
        def startTest(test):
            self.current_test = str(test)
            self.test_start_time = time.time()
            print(f"\n🔄 Running: {self.current_test}")
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(self.timeout)
            return original_startTest(test)
        
        def stopTest(test):
            duration = time.time() - self.test_start_time
            if duration > 5.0:  # Warn if test takes more than 5 seconds
                print(f"⚠️  Slow test: {self.current_test} took {duration:.2f}s")
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)  # Cancel alarm
            self.current_test = None
            return original_stopTest(test)
        
        result.startTest = startTest
        result.stopTest = stopTest
        return result


def run_all_tests():
    """Run all tests and return results."""
    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = 'tests'
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Create a test runner with progress tracking and timeout
    runner = ProgressTestRunner(
        verbosity=1,  # Reduced verbosity to show progress better
        stream=sys.stdout,
        buffer=False,
        timeout=30  # 30 second timeout per test
    )
    
    # Run tests and capture results
    start_time = time.time()
    try:
        result = runner.run(suite)
    except TimeoutError as e:
        print(f"\n⏰ TIMEOUT: {e}")
        result = None
    except KeyboardInterrupt:
        print("\n⏹️  Test execution interrupted by user")
        result = None
    end_time = time.time()
    
    return result, end_time - start_time


def print_test_summary(result, duration):
    """Print a comprehensive test summary."""
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    if result is None:
        print("❌ Test execution was interrupted or timed out")
        print(f"Duration: {duration:.2f} seconds")
        print("="*80)
        return
    
    # Basic statistics
    total_tests = result.testsRun
    failed_tests = len(result.failures)
    error_tests = len(result.errors)
    skipped_tests = len(result.skipped) if hasattr(result, 'skipped') else 0
    passed_tests = total_tests - failed_tests - error_tests - skipped_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Errors: {error_tests}")
    print(f"Skipped: {skipped_tests}")
    print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "N/A")
    print(f"Duration: {duration:.2f} seconds")
    
    # Print failed tests
    if result.failures:
        print("\nFAILED TESTS:")
        print("-" * 40)
        for test, traceback in result.failures:
            print(f"❌ {test}")
            print(f"   {traceback.split('AssertionError:')[-1].strip()}")
            print()
    
    # Print error tests
    if result.errors:
        print("\nERROR TESTS:")
        print("-" * 40)
        for test, traceback in result.errors:
            print(f"💥 {test}")
            print(f"   {traceback.split('Traceback (most recent call last):')[-1].strip()}")
            print()
    
    # Overall result
    if result.wasSuccessful():
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n❌ {failed_tests + error_tests} TESTS FAILED")
    
    print("="*80)


def print_test_coverage():
    """Print test coverage information."""
    print("\nTEST COVERAGE")
    print("-" * 40)
    
    # List all test files
    test_files = []
    for root, dirs, files in os.walk('tests'):
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                test_files.append(os.path.join(root, file))
    
    print(f"Test Files: {len(test_files)}")
    for test_file in sorted(test_files):
        print(f"  ✓ {test_file}")
    
    # List all source files
    source_files = []
    for root, dirs, files in os.walk('vbe_3d'):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                source_files.append(os.path.join(root, file))
    
    print(f"\nSource Files: {len(source_files)}")
    for source_file in sorted(source_files):
        print(f"  📄 {source_file}")


def run_specific_test(test_name, timeout=60):
    """Run a specific test with extended timeout."""
    print(f"\n🎯 Running specific test: {test_name}")
    print("=" * 50)
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(test_name)
    
    runner = ProgressTestRunner(
        verbosity=2,
        stream=sys.stdout,
        buffer=False,
        timeout=timeout
    )
    
    start_time = time.time()
    try:
        result = runner.run(suite)
        end_time = time.time()
        
        print(f"\n⏱️  Test duration: {end_time - start_time:.2f} seconds")
        return result.wasSuccessful()
    except TimeoutError as e:
        print(f"\n⏰ TIMEOUT: {e}")
        return False
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        return False


def main():
    """Main test runner function."""
    print("Virtual Bot Environment 3D - Test Suite")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('tests'):
        print("❌ Error: 'tests' directory not found. Please run from project root.")
        sys.exit(1)
    
    if not os.path.exists('vbe_3d'):
        print("❌ Error: 'vbe_3d' directory not found. Please run from project root.")
        sys.exit(1)
    
    # Check for specific test argument
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        success = run_specific_test(test_name)
        sys.exit(0 if success else 1)
    
    # Run all tests
    print("Running all tests with progress tracking...")
    print("Press Ctrl+C to interrupt long-running tests")
    result, duration = run_all_tests()
    
    # Print summary
    print_test_summary(result, duration)
    print_test_coverage()
    
    # Exit with appropriate code
    if result is None or not result.wasSuccessful():
        print("\n❌ Test suite failed!")
        sys.exit(1)
    else:
        print("\n✅ Test suite completed successfully!")
        sys.exit(0)


if __name__ == '__main__':
    main() 