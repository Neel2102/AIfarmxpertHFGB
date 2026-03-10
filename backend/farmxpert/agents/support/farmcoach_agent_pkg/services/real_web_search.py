"""
Real Web Search Service using SerpAPI for dynamic government scheme fetching
STRICT: Only authorized Indian government domains (.gov.in, .nic.in, india.gov.in)
"""

import os
import requests
from typing import List, Dict, Any
from urllib.parse import urlparse
import re
from ..models.input_model import SchemeData


class RealWebSearchService:
    """Service to fetch REAL government schemes using SerpAPI"""
    
    AUTHORIZED_DOMAINS = [
        '.gov.in',
        '.nic.in',
        'india.gov.in'
    ]
    
    def __init__(self):
        # Load SerpAPI key from environment
        self.serpapi_key = os.getenv('SERPAPI_API_KEY')
        if not self.serpapi_key:
            raise ValueError("SERPAPI_API_KEY not found in environment variables")
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def is_authorized_domain(self, url: str) -> bool:
        """Check if URL is from authorized Indian government domain"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            for auth_domain in self.AUTHORIZED_DOMAINS:
                if domain.endswith(auth_domain):
                    return True
            
            return False
        except:
            return False
    
    def search_serpapi(self, query: str) -> List[Dict[str, Any]]:
        """
        Perform real-time Google search using SerpAPI
        Returns only authorized government domain results
        """
        print(f"Performing real-time Google search for: '{query}'")
        
        # Construct search query with site filters for government domains
        search_query = f"{query} site:.gov.in OR site:.nic.in OR site:india.gov.in"
        
        # SerpAPI parameters
        params = {
            'api_key': self.serpapi_key,
            'engine': 'google',
            'q': search_query,
            'num': 20,  # Number of results
            'gl': 'in',  # Geolocation: India
            'hl': 'en'   # Language: English
        }
        
        try:
            response = self.session.get('https://serpapi.com/search', params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract organic results
            organic_results = data.get('organic_results', [])
            print(f"Found {len(organic_results)} total search results")
            
            # Filter to authorized government domains only
            authorized_results = []
            for result in organic_results:
                link = result.get('link', '')
                if self.is_authorized_domain(link):
                    authorized_results.append({
                        'title': result.get('title', ''),
                        'snippet': result.get('snippet', ''),
                        'link': link,
                        'displayed_link': result.get('displayed_link', '')
                    })
            
            print(f"Filtered to {len(authorized_results)} authorized government results")
            return authorized_results
            
        except requests.exceptions.RequestException as e:
            print(f"SerpAPI request failed: {e}")
            return []
        except Exception as e:
            print(f"Error processing SerpAPI response: {e}")
            return []
    
    def remove_duplicates(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate schemes based on URL"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get('link', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        print(f"Removed duplicates: {len(results)} -> {len(unique_results)} unique results")
        return unique_results
    
    def convert_to_scheme_data(self, results: List[Dict[str, Any]]) -> List[SchemeData]:
        """
        Convert SerpAPI results to SchemeData objects
        Using: title → scheme_name, snippet → description, link → official_url
        """
        schemes = []
        
        for result in results:
            title = result.get('title', '').strip()
            snippet = result.get('snippet', '').strip()
            link = result.get('link', '').strip()
            
            # Validate required fields
            if title and snippet and link:
                scheme = SchemeData(
                    scheme_name=title,
                    ministry="Ministry of Agriculture & Farmers Welfare",  # Default
                    description=snippet,
                    state="All",  # Default
                    official_url=link
                )
                schemes.append(scheme)
        
        print(f"Created {len(schemes)} SchemeData objects")
        return schemes
    
    def search_government_schemes(self, farmer_query: str) -> List[SchemeData]:
        """
        Main search method using SerpAPI
        Returns only authorized Indian government schemes
        """
        print(f"Searching authorized Indian government schemes for: '{farmer_query}'")
        
        # Step 1: Perform real-time search
        search_results = self.search_serpapi(farmer_query)
        
        if not search_results:
            print("No authorized government schemes found in search results")
            return []
        
        # Step 2: Remove duplicates
        unique_results = self.remove_duplicates(search_results)
        
        # Step 3: Convert to SchemeData objects
        schemes = self.convert_to_scheme_data(unique_results)
        
        if not schemes:
            print("No valid schemes could be created from search results")
            return []
        
        print(f"Successfully found {len(schemes)} authorized government schemes")
        return schemes
    
    def search_multiple_queries(self, queries: List[str]) -> List[SchemeData]:
        """
        Search multiple queries and combine results
        Useful for comprehensive scheme discovery
        """
        all_schemes = []
        seen_urls = set()
        
        for query in queries:
            print(f"\nSearching for: '{query}'")
            schemes = self.search_government_schemes(query)
            
            # Add only new schemes (avoid duplicates across queries)
            for scheme in schemes:
                if scheme.official_url not in seen_urls:
                    all_schemes.append(scheme)
                    seen_urls.add(scheme.official_url)
        
        print(f"\nTotal unique schemes found: {len(all_schemes)}")
        return all_schemes
