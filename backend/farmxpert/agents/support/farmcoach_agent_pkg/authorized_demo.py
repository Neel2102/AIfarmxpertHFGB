#!/usr/bin/env python3
"""
Authorized Farmer Coach Agent Demo
STRICT RULES: Only authorized government domains, no summarization, direct extraction
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.authorized_farmer_coach import AuthorizedFarmerCoachAgent
from models.input_model import FarmerQueryInput


def main():
    """Run demo of Authorized Farmer Coach Agent"""
    print("Authorized Farmer Coach Agent Demo")
    print("=" * 60)
    print("STRICT RULES: Only authorized government domains")
    print("NO summarization, NO rewriting, DIRECT extraction only")
    print("=" * 60)
    
    # Create authorized agent instance
    agent = AuthorizedFarmerCoachAgent()
    
    # Test queries
    queries = [
        "Pradhan Mantri Fasal Bima Yojana",
        "PM Kisan Samman Nidhi",
        "Kisan Credit Card",
        "Soil Health Card",
        "Crop insurance schemes"
    ]
    
    for query in queries:
        print(f"\nQuery: '{query}'")
        print("-" * 50)
        
        # Create input
        input_data = FarmerQueryInput(
            farmer_query=query,
            language="English",
            schemes_data=[]  # Not used - agent performs real-time search
        )
        
        # Process query with strict rules
        try:
            result = agent.process_query(input_data)
            
            if not result.schemes:
                print("No official government scheme found for this query.")
                print(f"NOTE: {result.disclaimer}")
                continue
            
            print(f"Found {len(result.schemes)} authorized government schemes:")
            
            for i, scheme in enumerate(result.schemes, 1):
                print(f"\n{i}. {scheme.scheme_name}")
                print(f"   Description: {scheme.simple_explanation}")
                print(f"   Official URL: {scheme.official_link}")
                
                # Verify it's authorized domain
                if agent.validate_authorized_domain(scheme.official_link):
                    print("   Authorized Government Domain")
                else:
                    print("   UNAUTHORIZED DOMAIN - This should not happen!")
            
            print(f"\n{result.disclaimer}")
            
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n" + "=" * 60)
    print("Authorized Demo completed!")
    print("All results are from authorized government domains only")
    print("No summarization or rewriting performed")
    print("Information extracted directly from official sources")


if __name__ == "__main__":
    main()
