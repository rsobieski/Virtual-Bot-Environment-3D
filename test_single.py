#!/usr/bin/env python3
"""
Simple test runner for a single test with timeout handling.
"""

import unittest
import sys
import time
import threading
import signal


class TimeoutException(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutException("Test timed out")


def run_test_with_timeout(test_name, timeout=10):
    """Run a single test with timeout."""
    print(f"🎯 Running test: {test_name}")
    print(f"⏱️  Timeout: {timeout} seconds")
    print("=" * 50)
    
    # Load the test
    loader = unittest.TestLoader()
    try:
        suite = loader.loadTestsFromName(test_name)
    except Exception as e:
        print(f"❌ Error loading test: {e}")
        return False
    
    # Create a result object
    result = unittest.TestResult()
    
    # Set up timeout (Unix-like systems)
    if hasattr(signal, 'SIGALRM'):
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
    
    start_time = time.time()
    
    try:
        # Run the test
        suite.run(result)
        
        # Cancel alarm
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n⏱️  Test duration: {duration:.2f} seconds")
        
        # Print results
        if result.wasSuccessful():
            print("✅ Test PASSED!")
            return True
        else:
            print("❌ Test FAILED!")
            
            if result.failures:
                print("\nFailures:")
                for test, traceback in result.failures:
                    print(f"  ❌ {test}")
                    print(f"     {traceback.split('AssertionError:')[-1].strip()}")
            
            if result.errors:
                print("\nErrors:")
                for test, traceback in result.errors:
                    print(f"  💥 {test}")
                    print(f"     {traceback.split('Traceback (most recent call last):')[-1].strip()}")
            
            return False
            
    except TimeoutException:
        print(f"\n⏰ Test timed out after {timeout} seconds!")
        return False
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user!")
        return False
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return False


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python test_single.py <test_name> [timeout_seconds]")
        print("Example: python test_single.py tests.test_world.TestWorld.test_step_robot_reproduction 15")
        sys.exit(1)
    
    test_name = sys.argv[1]
    timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    success = run_test_with_timeout(test_name, timeout)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main() 