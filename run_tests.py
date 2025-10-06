#!/usr/bin/env python3
"""
🧪 Master Test Runner
מריץ את כל הבדיקות של הפרויקט
"""

import sys
import os
from pathlib import Path
import unittest
from datetime import datetime
import argparse

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header(text):
    """Print colored header"""
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}{text:^60}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}\n")


def run_all_tests(verbose=2):
    """Run all test files"""
    
    print_header("🧪 Covered Calls Manager - Test Suite")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Discover and run tests
    test_dir = project_root / 'tests'
    
    if not test_dir.exists():
        print(f"{RED}❌ Test directory not found: {test_dir}{RESET}")
        return False
    
    # Create test loader
    loader = unittest.TestLoader()
    
    # Discover all tests
    suite = loader.discover(
        start_dir=str(test_dir),
        pattern='test_*.py',
        top_level_dir=str(project_root)
    )
    
    # Count tests
    test_count = suite.countTestCases()
    print(f"Found {test_count} tests\n")
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=verbose)
    result = runner.run(suite)
    
    # Print summary
    print_header("📊 Test Summary")
    
    print(f"Tests run: {result.testsRun}")
    print(f"{GREEN}✅ Passed: {result.testsRun - len(result.failures) - len(result.errors)}{RESET}")
    
    if result.failures:
        print(f"{RED}❌ Failed: {len(result.failures)}{RESET}")
    
    if result.errors:
        print(f"{RED}❌ Errors: {len(result.errors)}{RESET}")
    
    if result.skipped:
        print(f"{YELLOW}⏭️  Skipped: {len(result.skipped)}{RESET}")
    
    # Success rate
    if result.testsRun > 0:
        success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / 
                       result.testsRun * 100)
        print(f"\nSuccess Rate: {success_rate:.1f}%")
    
    print(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Return success status
    return result.wasSuccessful()


def run_specific_test(test_file, verbose=2):
    """Run a specific test file"""
    
    print_header(f"🧪 Running {test_file}")
    
    # Load the test file
    test_path = project_root / 'tests' / test_file
    
    if not test_path.exists():
        print(f"{RED}❌ Test file not found: {test_path}{RESET}")
        return False
    
    # Load tests from file
    loader = unittest.TestLoader()
    suite = loader.discover(
        start_dir=str(test_path.parent),
        pattern=test_file,
        top_level_dir=str(project_root)
    )
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=verbose)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def run_coverage():
    """Run tests with coverage"""
    print_header("📊 Running Tests with Coverage")
    
    try:
        import coverage
    except ImportError:
        print(f"{RED}❌ Coverage.py not installed{RESET}")
        print("Install with: pip install coverage")
        return False
    
    # Create coverage object
    cov = coverage.Coverage()
    
    # Start coverage
    cov.start()
    
    # Run tests
    success = run_all_tests(verbose=1)
    
    # Stop coverage
    cov.stop()
    cov.save()
    
    # Generate report
    print("\n" + "=" * 60)
    print("Coverage Report:")
    print("=" * 60)
    cov.report()
    
    # Generate HTML report
    html_dir = project_root / 'htmlcov'
    cov.html_report(directory=str(html_dir))
    print(f"\n{GREEN}📊 HTML coverage report: {html_dir}/index.html{RESET}")
    
    return success


def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(
        description='Run tests for Covered Calls Manager'
    )
    
    parser.add_argument(
        '--file', '-f',
        help='Run specific test file (e.g., test_config_manager.py)',
        type=str
    )
    
    parser.add_argument(
        '--coverage', '-c',
        help='Run with coverage report',
        action='store_true'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        help='Verbosity level (0-2)',
        type=int,
        default=2
    )
    
    args = parser.parse_args()
    
    # Change to project directory
    os.chdir(project_root)
    
    # Run tests
    if args.coverage:
        success = run_coverage()
    elif args.file:
        success = run_specific_test(args.file, verbose=args.verbose)
    else:
        success = run_all_tests(verbose=args.verbose)
    
    # Exit with appropriate code
    if success:
        print(f"\n{GREEN}✅ All tests passed!{RESET}\n")
        sys.exit(0)
    else:
        print(f"\n{RED}❌ Some tests failed{RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
