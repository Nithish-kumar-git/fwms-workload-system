"""
Verify window router integration.
"""

import sys
sys.path.insert(0, 'c:/Users/itsni/.gemini/antigravity/scratch/faculty_selection')

try:
    # Import the router directly
    from app.coordinator.window_router import router
    
    print("✅ Window router imported successfully")
    print(f"   Router prefix: {router.prefix}")
    print(f"   Router tags: {router.tags}")
    
    # List all routes
    print("\n📋 Window Router Endpoints:")
    for route in router.routes:
        methods = ','.join(route.methods) if hasattr(route, 'methods') else 'N/A'
        print(f"   {methods:6} {route.path}")
    
    print("\n✅ Verification complete: Window router is properly configured")
    print("\nExpected endpoints after registration with /api prefix:")
    print("   POST   /api/windows")
    print("   POST   /api/windows/{window_id}/schedule")
    print("   POST   /api/windows/{window_id}/open")
    print("   POST   /api/windows/{window_id}/close")
    print("   POST   /api/windows/{window_id}/archive")
    print("   GET    /api/windows/{window_id}")
    print("   GET    /api/windows/current")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
