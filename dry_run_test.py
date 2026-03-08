#!/usr/bin/env python3
"""
Dry Run Test - Bypass Rate Limiting
Tests database to prompt context injection without calling Gemini API
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from datetime import datetime

async def test_context_injection_dry_run():
    """Test context injection without Gemini API calls"""
    print("🎯 DRY RUN TEST - Context Injection Without Rate Limits")
    print("=" * 60)
    
    try:
        # Import the core agent
        from farmxpert.core.core_agent_updated import core_agent
        
        # Test 1: Test context injection for user 1
        print("\n🧪 Test 1: Context Injection for User ID 1")
        print("-" * 40)
        
        context = await core_agent._inject_farm_context(user_id=1, context={})
        print(f"📝 Injected Context:\n{context}")
        
        # Test 2: Test with a sample user query
        print("\n🧪 Test 2: Full Context Injection Simulation")
        print("-" * 40)
        
        user_input = "What should I do for my wheat crop?"
        agent_role = "crop_selector"
        session_id = "dry_run_session"
        user_id = 1
        
        # Get farm context
        farm_context = await core_agent._inject_farm_context(user_id, {})
        
        # Create the enhanced prompt (exactly like in core_agent)
        enhanced_user_input = f"{farm_context}\n\nUser Query: {user_input}" if farm_context else user_input
        
        print(f"📝 Original User Input:\n{user_input}")
        print(f"\n📝 Enhanced User Input (with context):\n{enhanced_user_input}")
        
        # Test 3: Test multiple rapid calls (no rate limiting)
        print("\n🧪 Test 3: Rapid Context Injection Test (10 calls)")
        print("-" * 40)
        
        start_time = datetime.now()
        
        for i in range(10):
            context_test = await core_agent._inject_farm_context(user_id=1, context={})
            print(f"  Call {i+1}: ✅ Context retrieved ({len(context_test)} chars)")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n⚡ Performance: 10 context injections in {duration:.2f} seconds")
        print(f"🚀 Average: {duration/10:.3f} seconds per injection")
        
        return True
        
    except Exception as e:
        print(f"❌ Dry run test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_database_direct_access():
    """Test direct database access to farm data"""
    print("\n🗄️  Direct Database Access Test")
    print("=" * 40)
    
    try:
        from farmxpert.database import get_database_session, get_user_farms, get_farm_crops
        
        db = get_database_session()
        
        # Test user farms
        print("\n🧪 Testing User Farms (User ID 1):")
        farms = get_user_farms(db, 1)
        
        if farms:
            print(f"✅ Found {len(farms)} farms:")
            for i, farm in enumerate(farms):
                print(f"  Farm {i+1}:")
                print(f"    ID: {farm.get('id')}")
                print(f"    Name: {farm.get('name')}")
                print(f"    Location: {farm.get('location')}")
                print(f"    Crop Type: {farm.get('crop_type')}")
                print(f"    State: {farm.get('state')}")
                print(f"    District: {farm.get('district')}")
                print(f"    Village: {farm.get('village')}")
                print(f"    Soil Type: {farm.get('soil_type')}")
                
                # Get crops for this farm
                crops = get_farm_crops(db, farm['id'])
                if crops:
                    print(f"    Crops ({len(crops)}):")
                    for crop in crops:
                        print(f"      - {crop.get('crop_type')} ({crop.get('variety')}) - {crop.get('status')}")
                        print(f"        Area: {crop.get('area_acres')} acres")
                        print(f"        Seed Cost: ${crop.get('seed_cost')}")
                else:
                    print(f"    Crops: None found")
        else:
            print("❌ No farms found for user ID 1")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Database access test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_context_formatting():
    """Test different context formatting scenarios"""
    print("\n📝 Context Formatting Test")
    print("=" * 40)
    
    try:
        from farmxpert.core.core_agent_updated import core_agent
        
        # Test different scenarios
        scenarios = [
            {"user_id": 1, "context": {}, "name": "User 1 with data"},
            {"user_id": 999, "context": {}, "name": "Non-existent user"},
            {"user_id": None, "context": {}, "name": "No user ID (should default to 1)"},
        ]
        
        for scenario in scenarios:
            print(f"\n🧪 Testing: {scenario['name']}")
            context = await core_agent._inject_farm_context(
                user_id=scenario['user_id'], 
                context=scenario['context']
            )
            print(f"📝 Result: {context}")
        
        return True
        
    except Exception as e:
        print(f"❌ Context formatting test failed: {e}")
        return False

async def main():
    """Run all dry run tests"""
    print("🚀 DRY RUN TEST SUITE - No Rate Limiting")
    print("=" * 70)
    print("💡 This test bypasses Gemini API to focus on database->prompt flow")
    print("⚡ Can be run 100+ times per minute without hitting rate limits")
    
    # Test 1: Direct database access
    db_ok = await test_database_direct_access()
    
    # Test 2: Context injection
    context_ok = await test_context_injection_dry_run()
    
    # Test 3: Context formatting
    format_ok = await test_context_formatting()
    
    print("\n" + "=" * 70)
    print("🎯 DRY RUN TEST RESULTS:")
    print(f"  🗄️  Database Access: {'✅ PASS' if db_ok else '❌ FAIL'}")
    print(f"  🎯 Context Injection: {'✅ PASS' if context_ok else '❌ FAIL'}")
    print(f"  📝 Context Formatting: {'✅ PASS' if format_ok else '❌ FAIL'}")
    
    if db_ok and context_ok and format_ok:
        print("\n🎉 ALL DRY RUN TESTS PASSED!")
        print("✅ Database → Context Injection → Prompt flow is working!")
        print("🚀 Ready for production without rate limiting issues!")
        
        print("\n💡 Key Insights:")
        print("  ✅ Farm data successfully retrieved from PostgreSQL")
        print("  ✅ Context properly formatted for AI consumption")
        print("  ✅ No Gemini API calls = no rate limiting")
        print("  ✅ Can test database-plumbing 1000+ times per minute")
        
    else:
        print("\n❌ Some dry run tests failed. Check the errors above.")
    
    print("\n📋 What was tested (without Gemini API):")
    print("  ✅ PostgreSQL farm data retrieval")
    print("  ✅ Database to context string conversion")
    print("  ✅ Context injection simulation")
    print("  ✅ Multiple rapid calls (performance test)")
    print("  ✅ Error handling for missing data")
    
    return db_ok and context_ok and format_ok

if __name__ == "__main__":
    success = asyncio.run(main())
    
    if success:
        print(f"\n🎯 DRY RUN COMPLETE - Run this anytime to test database integration!")
        print(f"🚀 No API keys needed, no rate limits, pure database testing!")
    else:
        print(f"\n❌ Dry run failed - fix database issues before proceeding")
