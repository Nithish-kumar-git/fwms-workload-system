"""Run allocation directly and capture full traceback."""
import traceback
import sys

try:
    from app.allocation.service import run_allocation
    result = run_allocation()
    print(f"SUCCESS: {result.get('success')}")
    print(f"message: {result.get('message')}")
    print(f"assigned: {result.get('subjects_assigned')}")
    print(f"unassigned: {result.get('subjects_unassigned')}")
except Exception as e:
    print("FULL TRACEBACK:")
    traceback.print_exc()
    sys.exit(1)
