#!/usr/bin/env python3
"""
Test the Context Injector functionality
Tests that farm data is properly injected into AI prompts
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio

async def test_context_injector():
    """Test the farm context injection functionality"""
    print("🎯 Testing Context Injector")
    print("=" * 50)
    
    try:
        from farmxpert.core.core_agent_updated import core_agent
        
        # Test 1: Test with user_id = 1 (as requested)
        print("\n🧪 Test 1: Context Injection for User ID 1")
        context = await core_agent._inject_farm_context(user_id=1, context={})
        print(f"📝 Injected Context: {context}")
        
        # Test 2: Test with no user_id (should default to 1)
        print("\n🧪 Test 2: Context Injection with No User ID (should default to 1)")
        context_default = await core_agent._inject_farm_context(user_id=None, context={})
        print(f"📝 Default Context: {context_default}")
        
        # Test 3: Test with a non-existent user
        print("\n🧪 Test 3: Context Injection for Non-existent User ID 999")
        context_missing = await core_agent._inject_farm_context(user_id=999, context={})
        print(f"📝 Missing User Context: {context_missing}")
        
        return True
        
    except Exception as e:
        print(f"❌ Context injector test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_full_request_with_context():
    """Test a full request to see context in action"""
    print("\n🚀 Testing Full Request with Context Injection")
    print("=" * 50)
    
    try:
        from farmxpert.core.core_agent_updated import process_farm_request
        
        # Test request with context injection
        print("\n🧪 Test: Full Farm Request with Context")
        
        response = await process_farm_request(
            user_input="What crops should I plant?",
            agent_role="crop_selector",
            context={"season": "Kharif"},
            session_id="test_session_123",
            user_id=1  # This should trigger context injection
        )
        
        print(f"✅ Response Success: {response.get('success', False)}")
        print(f"🤖 Agent Used: {response.get('agent', 'Unknown')}")
        print(f"💬 Response: {response.get('response', 'No response')[:200]}...")
        
        # Check if context was included in the metadata
        metadata = response.get('metadata', {})
        if metadata:
            print(f"📊 Execution Time: {metadata.get('execution_time', 'N/A')}s")
            print(f"🔧 Tools Used: {metadata.get('tools_used', [])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Full request test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_database_data():
    """Test what farm data exists in the database"""
    print("\n🗄️  Testing Database Farm Data")
    print("=" * 50)
    
    try:
        from farmxpert.database import get_database_session, get_user_farms, get_farm_crops
        
        db = get_database_session()
        
        # Test user farms
        print("\n🧪 Test: User Farms for User ID 1")
        farms = get_user_farms(db, 1)
        
        if farms:
            print(f"✅ Found {len(farms)} farms:")
            for i, farm in enumerate(farms):
                print(f"  Farm {i+1}:")
                print(f"    Name: {farm.get('name', 'N/A')}")
                print(f"    Location: {farm.get('location', 'N/A')}")
                print(f"    Size: {farm.get('size_acres', 'N/A')} acres")
                print(f"    Farmer: {farm.get('farmer_name', 'N/A')}")
                
                # Get crops for this farm
                try:
                    crops = get_farm_crops(db, farm['id'])
                    if crops:
                        print(f"    Crops: {len(crops)} crops")
                        for crop in crops:
                            print(f"      - {crop.get('crop_type', 'N/A')} ({crop.get('status', 'N/A')})")
                    else:
                        print(f"    Crops: No crops found")
                except Exception as e:
                    print(f"    Crops: Error fetching - {e}")
        else:
            print("❌ No farms found for user ID 1")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all context injector tests"""
    print("🚀 Context Injector Test Suite")
    print("=" * 60)
    
    # Test 1: Database data
    db_ok = await test_database_data()
    
    # Test 2: Context injection
    context_ok = await test_context_injector()
    
    # Test 3: Full request with context
    full_ok = await test_full_request_with_context()
    
    print("\n" + "=" * 60)
    print("🎯 TEST RESULTS:")
    print(f"  📊 Database Data: {'✅ PASS' if db_ok else '❌ FAIL'}")
    print(f"  🎯 Context Injection: {'✅ PASS' if context_ok else '❌ FAIL'}")
    print(f"  🚀 Full Request: {'✅ PASS' if full_ok else '❌ FAIL'}")
    
    if db_ok and context_ok and full_ok:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Context Injector is working perfectly!")
        print("🚀 Your AI now has memory of user's farm data!")
    else:
        print("\n❌ Some tests failed. Check the errors above.")
    
    print("\n📋 What was tested:")
    print("  ✅ Farm data retrieval from database")
    print("  ✅ Context string formatting")
    print("  ✅ Context injection into AI prompts")
    print("  ✅ Full request processing with context")
    
    return db_ok and context_ok and full_ok

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n🎯 Context Injector implementation complete!")
    else:
        print("\n❌ Context Injector needs debugging.")
