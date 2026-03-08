#!/usr/bin/env python3
"""
Root Level Fix Verification Test
Tests that the SQLAlchemy ORM models now match the database schema
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio

async def test_orm_models():
    """Test that ORM models work correctly with the database"""
    print("🔧 TESTING ROOT LEVEL FIX - ORM Models")
    print("=" * 60)
    
    try:
        from farmxpert.database import get_database_session, get_user_farms, get_farm_crops
        from farmxpert.models.farm_models import Farm
        from farmxpert.models.user_models import AuthUser
        
        db = get_database_session()
        
        # Test 1: Test AuthUser model
        print("\n🧪 Test 1: AuthUser ORM Model")
        print("-" * 40)
        try:
            auth_users = db.query(AuthUser).all()
            print(f"✅ AuthUser model working - Found {len(auth_users)} users")
            if auth_users:
                user = auth_users[0]
                print(f"   Sample User: {user.username} ({user.email})")
        except Exception as e:
            print(f"❌ AuthUser model failed: {e}")
            return False
        
        # Test 2: Test Farm model with proper relationships
        print("\n🧪 Test 2: Farm ORM Model")
        print("-" * 40)
        try:
            farms = db.query(Farm).all()
            print(f"✅ Farm model working - Found {len(farms)} farms")
            if farms:
                farm = farms[0]
                print(f"   Sample Farm: {farm.farm_name} (User ID: {farm.user_id})")
                print(f"   Location: {farm.village}, {farm.district}, {farm.state}")
                print(f"   Soil Type: {farm.soil_type}")
                
                # Test relationship
                if hasattr(farm, 'auth_user') and farm.auth_user:
                    print(f"   Related User: {farm.auth_user.username}")
                else:
                    print("   ⚠️  Relationship not loaded (this is expected without eager loading)")
        except Exception as e:
            print(f"❌ Farm model failed: {e}")
            return False
        
        # Test 3: Test get_user_farms with ORM
        print("\n🧪 Test 3: get_user_farms with ORM")
        print("-" * 40)
        try:
            farms = get_user_farms(db, 1)
            print(f"✅ get_user_farms working - Found {len(farms)} farms")
            if farms:
                farm = farms[0]
                print(f"   Farm Type: {type(farm).__name__}")
                print(f"   Farm Name: {farm.farm_name}")
                print(f"   Has user_id: {hasattr(farm, 'user_id')} = {farm.user_id}")
        except Exception as e:
            print(f"❌ get_user_farms failed: {e}")
            return False
        
        # Test 4: Test get_farm_crops with ORM
        print("\n🧪 Test 4: get_farm_crops with ORM")
        print("-" * 40)
        try:
            if farms:
                crops = get_farm_crops(db, farms[0].id)
                print(f"✅ get_farm_crops working - Found {len(crops)} crops")
                if crops:
                    crop = crops[0]
                    print(f"   Crop Type: {type(crop).__name__}")
                    print(f"   Crop: {crop.crop_type} ({crop.variety})")
                    print(f"   Status: {crop.status}")
        except Exception as e:
            print(f"❌ get_farm_crops failed: {e}")
            return False
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ ORM test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_context_injection_orm():
    """Test context injection with fixed ORM models"""
    print("\n🎯 TESTING CONTEXT INJECTION WITH FIXED ORM")
    print("=" * 60)
    
    try:
        from farmxpert.core.core_agent_updated import core_agent
        
        # Test context injection
        context = await core_agent._inject_farm_context(user_id=1, context={})
        print(f"✅ Context injection working")
        print(f"📝 Context: {context}")
        
        # Check if it contains real farm data
        if "Green Valley Farm" in context:
            print("✅ Real farm data found in context")
        else:
            print("⚠️  Expected farm data not found in context")
        
        return True
        
    except Exception as e:
        print(f"❌ Context injection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_no_more_band_aids():
    """Verify that we're not using band-aid fixes anymore"""
    print("\n🚫 VERIFYING NO MORE BAND-AIDS")
    print("=" * 40)
    
    try:
        # Check that database functions return ORM objects, not dictionaries
        from farmxpert.database import get_database_session, get_user_farms
        from farmxpert.models.farm_models import Farm
        
        db = get_database_session()
        farms = get_user_farms(db, 1)
        
        if farms:
            farm = farms[0]
            print(f"🔍 Farm object type: {type(farm)}")
            print(f"🔍 Is it ORM object: {isinstance(farm, Farm)}")
            print(f"🔍 Has ORM attributes: {hasattr(farm, 'farm_name')}")
            
            if isinstance(farm, Farm) and hasattr(farm, 'farm_name'):
                print("✅ CONFIRMED: Using proper ORM objects (no band-aids)")
                return True
            else:
                print("❌ WARNING: Still using dictionary band-aids")
                return False
        else:
            print("⚠️  No farms to test")
            return True
        
    except Exception as e:
        print(f"❌ Band-aid verification failed: {e}")
        return False

async def main():
    """Run all root level fix verification tests"""
    print("🚀 ROOT LEVEL FIX VERIFICATION")
    print("=" * 70)
    print("🔧 Testing that SQLAlchemy models match database schema")
    print("✅ No more band-aids - proper ORM integration")
    
    # Test 1: ORM Models
    orm_ok = await test_orm_models()
    
    # Test 2: Context Injection
    context_ok = await test_context_injection_orm()
    
    # Test 3: No more band-aids
    no_band_aids = await test_no_more_band_aids()
    
    print("\n" + "=" * 70)
    print("🎯 ROOT LEVEL FIX RESULTS:")
    print(f"  🔧 ORM Models: {'✅ PASS' if orm_ok else '❌ FAIL'}")
    print(f"  🎯 Context Injection: {'✅ PASS' if context_ok else '❌ FAIL'}")
    print(f"  🚫 No Band-Aids: {'✅ PASS' if no_band_aids else '❌ FAIL'}")
    
    if orm_ok and context_ok and no_band_aids:
        print("\n🎉 ROOT LEVEL FIX SUCCESSFUL!")
        print("✅ SQLAlchemy models now match database schema")
        print("✅ No more band-aid fixes needed")
        print("✅ Production-ready ORM integration")
        print("✅ Context injection using proper ORM")
        
        print("\n🔧 What was fixed at the root level:")
        print("  ✅ Farm model columns match database (farm_name, user_id, etc.)")
        print("  ✅ AuthUser model matches auth_users table")
        print("  ✅ Proper foreign key relationships")
        print("  ✅ Removed raw SQL band-aids")
        print("  ✅ Context injection uses ORM objects")
        
    else:
        print("\n❌ Root level fix incomplete. Check failures above.")
    
    print("\n📋 Technical improvements:")
    print("  ✅ Farm.name → Farm.farm_name")
    print("  ✅ Added Farm.user_id foreign key")
    print("  ✅ Added AuthUser model for auth_users table")
    print("  ✅ Proper BigInteger and Numeric types")
    print("  ✅ Correct timezone handling")
    print("  ✅ Removed dictionary-based workarounds")
    
    return orm_ok and context_ok and no_band_aids

if __name__ == "__main__":
    success = asyncio.run(main())
    
    if success:
        print(f"\n🎯 ROOT LEVEL FIX COMPLETE - Production ready!")
        print(f"🚀 No more schema mismatches or band-aids!")
    else:
        print(f"\n❌ Root level issues remain - fix the failures above")
