"""
Verify development auth bypass implementation.
"""

import sys
sys.path.insert(0, 'c:/Users/itsni/.gemini/antigravity/scratch/faculty_selection')

# Mock the environment
import os
os.environ['ENV'] = 'development'
os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost/test'
os.environ['SECRET_KEY'] = 'dev-secret-key-minimum-32-characters-long'
os.environ['GOOGLE_CLIENT_ID'] = 'test-client-id'
os.environ['GOOGLE_CLIENT_SECRET'] = 'test-secret'
os.environ['GOOGLE_REDIRECT_URI'] = 'http://localhost:8000/callback'

try:
    # Import after setting env vars
    from app.core.config import settings
    from app.auth.dependencies import get_current_user
    import asyncio
    
    print("✅ Configuration loaded")
    print(f"   ENV: {settings.ENV}")
    
    # Test development bypass
    async def test_dev_bypass():
        print("\n🧪 Testing development auth bypass...")
        
        # Call without session cookie (should bypass in dev mode)
        user = await get_current_user(faculty_session=None)
        
        print(f"\n✅ Auth bypass successful!")
        print(f"   Staff ID: {user.staff_id}")
        print(f"   Email: {user.email}")
        print(f"   Name: {user.name}")
        print(f"   Is Coordinator: {user.is_coordinator}")
        
        # Verify expected values
        assert user.staff_id == 1, "Expected staff_id=1"
        assert user.is_coordinator == True, "Expected is_coordinator=True"
        assert user.email == "dev@example.com", "Expected dev email"
        
        print("\n✅ All assertions passed!")
        print("\n📝 Note: Check logs for bypass warning message")
    
    # Run test
    asyncio.run(test_dev_bypass())
    
    print("\n✅ Verification complete: Development auth bypass is working correctly")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
