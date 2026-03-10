#!/usr/bin/env python3
"""
Test SerpAPI Integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from services.real_web_search import RealWebSearchService

# Load environment variables
load_dotenv()


def test_serpapi_integration():
    """Test SerpAPI integration with authorized domain filtering"""
    print("Testing SerpAPI Integration")
    print("=" * 50)
    
    try:
        # Create service instance
        web_service = RealWebSearchService()
        print("RealWebSearchService created successfully")
        
        # Test search
        query = "Pradhan Mantri Fasal Bima Yojana"
        print(f"\nTesting search for: '{query}'")
        
        schemes = web_service.search_government_schemes(query)
        
        if schemes:
            print(f"Found {len(schemes)} authorized government schemes:")
            
            for i, scheme in enumerate(schemes[:3], 1):  # Show first 3
                print(f"\n{i}. {scheme.scheme_name}")
                print(f"   {scheme.description[:100]}...")
                print(f"   {scheme.official_url}")
                print(f"   Authorized: {web_service.is_authorized_domain(scheme.official_url)}")
        else:
            print("No schemes found")
        
        # Test domain validation
        print(f"\nTesting domain validation:")
        test_urls = [
            "https://pmfby.gov.in",
            "https://pmkisan.gov.in", 
            "https://soilhealth.dac.gov.in",
            "https://example.com",
            "https://fake-scheme.com"
        ]
        
        for url in test_urls:
            is_auth = web_service.is_authorized_domain(url)
            status = "OK" if is_auth else "NO"
            print(f"   {status} {url}")
        
        print(f"\nSerpAPI integration test completed successfully!")
        
    except Exception as e:
        print(f"Test failed: {e}")


if __name__ == "__main__":
    test_serpapi_integration()
