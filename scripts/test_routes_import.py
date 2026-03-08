"""
Test the agent routes import directly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from farmxpert.interfaces.api.routes.agent_routes import router
    print("✅ Agent routes imported successfully")
    print(f"📊 Router prefix: {router.prefix}")
    print(f"🔗 Available routes:")
    for route in router.routes:
        print(f"  - {route.methods} {route.path}")
        
except Exception as e:
    print(f"❌ Agent routes import failed: {e}")
    import traceback
    traceback.print_exc()

try:
    from farmxpert.core.agent_routes import router as core_agent_router
    print("\n✅ Core agent routes imported successfully")
    print(f"📊 Router prefix: {core_agent_router.prefix}")
    print(f"🔗 Available routes:")
    for route in core_agent_router.routes:
        print(f"  - {route.methods} {route.path}")
        
except Exception as e:
    print(f"❌ Core agent routes import failed: {e}")
    import traceback
    traceback.print_exc()
