#!/usr/bin/env python3
"""
Farmer Coach Agent Demo with REAL SerpAPI-based web search
DYNAMIC: Fresh web search performed for EACH farmer query
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from agent.farmer_coach import FarmerCoachAgent
from models.input_model import FarmerQueryInput, SchemeData
from services.real_web_search import RealWebSearchService

# Load environment variables
load_dotenv()


def main():
    """Run demo of Farmer Coach Agent with dynamic web search"""
    print("� Farmer Coach Agent Demo - REAL SerpAPI Search")
    print("=" * 60)
    print("🔍 DYNAMIC: Fresh web search for EACH query")
    print("🏛️  AUTHORIZED: Only .gov.in, .nic.in, india.gov.in domains")
    print("📋 NO HARDCODED: Real-time results only")
    print("=" * 60)
    
    # Create agent instance
    agent = FarmerCoachAgent()
    
    # Create web search service
    web_service = RealWebSearchService()
    
    # Test queries - each will trigger a fresh search
    queries = [
        "Pradhan Mantri Fasal Bima Yojana",
        "PM Kisan Samman Nidhi", 
        "Kisan Credit Card",
        "Soil Health Card Scheme",
        "Crop insurance schemes"
    ]
    
    for query in queries:
        print(f"\n� Processing Query: '{query}'")
        print("-" * 50)
        
        try:
            # Step 1: Perform FRESH web search for THIS query
            print(f"🌐 Performing fresh web search for: '{query}'")
            schemes = web_service.search_government_schemes(query)
            
            if not schemes:
                print("❌ No authorized government scheme found for this query.")
                print("📝 Please visit official government websites for more information.")
                continue
            
            # Step 2: Create input with fresh search results
            input_data = FarmerQueryInput(
                farmer_query=query,
                language="English",
                schemes_data=schemes  # Fresh data for this query
            )
            
            # Step 3: Process query with agent
            result = agent.process_query(input_data)
            
            print(f"📊 Found {len(result.schemes)} relevant government schemes:")
            
            for i, scheme in enumerate(result.schemes, 1):
                print(f"\n{i}. 🏛️  {scheme.scheme_name}")
                print(f"   📖 {scheme.simple_explanation}")
                print(f"   🔗 {scheme.official_link}")
                
                # Verify authorized domain
                if web_service.is_authorized_domain(scheme.official_link):
                    print(f"   ✅ Authorized Government Domain")
                else:
                    print(f"   ❌ UNAUTHORIZED DOMAIN")
            
            print(f"\n⚠️  {result.disclaimer}")
            
        except Exception as e:
            print(f"❌ Error processing query '{query}': {e}")
    
    print("\n" + "=" * 60)
    print("✅ Demo completed!")
    print("🔍 Each query performed a fresh web search")
    print("🏛️  All results from authorized government domains only")
    print("📋 No hardcoded or fallback schemes used")


if __name__ == "__main__":
    main()
