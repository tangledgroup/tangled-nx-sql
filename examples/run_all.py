#!/usr/bin/env python3
"""Run all nx_sql examples to verify they work correctly."""

import importlib.util
import os
import sys
from pathlib import Path

EXAMPLES_DIR = Path(__file__).parent

# Import the spec-kit skill helper if available
try:
    from examples.utils import print_docstring
except ImportError:
    # Fallback: simple decorator
    def print_docstring(func):
        return func


def find_examples():
    """Find all example Python files (excluding run_all.py and __pycache__)."""
    examples = []
    for root, dirs, files in os.walk(EXAMPLES_DIR):
        # Skip __pycache__ and the run_all script itself
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for f in sorted(files):
            if f.endswith('.py') and f not in ('run_all.py', 'utils.py'):
                examples.append(os.path.join(root, f))
    return examples


def run_example(filepath):
    """Run a single example file."""
    relpath = os.path.relpath(filepath, EXAMPLES_DIR)
    print(f"\n{'='*60}")
    print(f"Running: {relpath}")
    print(f"{'='*60}")

    try:
        spec = importlib.util.spec_from_file_location("example", filepath)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return True, None
    except Exception as e:
        return False, str(e)


def main():
    examples = find_examples()

    if not examples:
        print("No example files found!")
        sys.exit(1)

    print(f"Found {len(examples)} examples to run\n")

    passed = 0
    failed = 0
    failures = []

    for filepath in examples:
        relpath = os.path.relpath(filepath, EXAMPLES_DIR)
        success, error = run_example(filepath)

        if success:
            print(f"  ✓ PASSED")
            passed += 1
        else:
            print(f"  ✗ FAILED: {error}")
            failed += 1
            failures.append((relpath, error))

    # Summary
    print(f"\n{'='*60}")
    print(f"Summary: {passed} passed, {failed} failed out of {len(examples)}")
    print(f"{'='*60}")

    if failures:
        print("\nFailures:")
        for relpath, error in failures:
            print(f"  {relpath}: {error}")
        sys.exit(1)
    else:
        print("\nAll examples passed! ✓")


if __name__ == "__main__":
    main()
