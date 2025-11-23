#!/usr/bin/env python3
"""
Verification script for Trip CRUD tools.

This script verifies that all 4 trip tools are properly implemented
and follow the required patterns.
"""

import inspect
from tools import create_trip, get_trip, list_trips, create_trips_batch


def verify_tool(tool_module, tool_name):
    """Verify a tool module has required components."""
    print(f"\n✓ Checking {tool_name}...")

    # Check INPUT_SCHEMA exists
    if not hasattr(tool_module, 'INPUT_SCHEMA'):
        print("  ✗ Missing INPUT_SCHEMA")
        return False
    print("  ✓ INPUT_SCHEMA defined")

    # Check execute function exists and is async
    if not hasattr(tool_module, 'execute'):
        print("  ✗ Missing execute function")
        return False

    execute_func = getattr(tool_module, 'execute')
    if not inspect.iscoroutinefunction(execute_func):
        print("  ✗ execute function is not async")
        return False
    print("  ✓ async execute function defined")

    # Check execute signature
    sig = inspect.signature(execute_func)
    params = list(sig.parameters.keys())
    if params != ['arguments']:
        print(f"  ✗ execute signature incorrect: {params}")
        return False
    print("  ✓ execute signature correct")

    return True


def main():
    """Verify all trip tools."""
    print("=" * 60)
    print("Trip CRUD Tools Verification")
    print("=" * 60)

    tools = [
        (create_trip, "create_trip"),
        (get_trip, "get_trip"),
        (list_trips, "list_trips"),
        (create_trips_batch, "create_trips_batch"),
    ]

    all_valid = True
    for tool_module, tool_name in tools:
        if not verify_tool(tool_module, tool_name):
            all_valid = False

    print("\n" + "=" * 60)
    if all_valid:
        print("✓ All trip tools are properly implemented!")
    else:
        print("✗ Some tools have issues")
    print("=" * 60)


if __name__ == "__main__":
    main()
