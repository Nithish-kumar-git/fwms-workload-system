import sys
import os

def check_imports():
    errors = []
    modules = [
        "app.admin.cycle_service_new",
        "app.admin.cycle_router",
        "app.admin.service",
        "app.preference.window_service",
        "app.allocation.router",
        "app.reports.router",
    ]
    
    for m in modules:
        try:
            __import__(m)
            print(f"OK: {m}")
        except Exception as e:
            print(f"FAIL: {m} -> {e}")
            errors.append(m)
    
    return errors

if __name__ == "__main__":
    errors = check_imports()
    if errors:
        print(f"\nFAILED: {len(errors)} import(s) broken")
        sys.exit(1)
    else:
        print("\nAll imports OK")
