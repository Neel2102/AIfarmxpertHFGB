"""
Authorized Web Search Service for REAL government scheme data
STRICT RULES: Only authorized government domains, no summarization, direct extraction
"""

import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import time


class AuthorizedWebSearchService:
    """Service to fetch ONLY from authorized government domains"""
    
    AUTHORIZED_DOMAINS = [
        '.gov.in',
        '.nic.in',
        'india.gov.in'
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def is_authorized_domain(self, url: str) -> bool:
        """Check if URL is from authorized government domain"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            for auth_domain in self.AUTHORIZED_DOMAINS:
                if domain.endswith(auth_domain):
                    return True
            
            return False
        except:
            return False
    
    def search_google_for_schemes(self, query: str) -> List[Dict[str, str]]:
        """
        Perform real-time web search for government schemes
        Returns only authorized government domain results
        """
        print(f"🔍 Performing real-time web search for: '{query}'")
        
        # Note: In production, you would use a real search API
        # For demo, we'll search known government scheme URLs directly
        
        # Known authorized government scheme URLs
        authorized_urls = [
            'https://pmfby.gov.in',
            'https://pmkisan.gov.in', 
            'https://kisan.gov.in',
            'https://soilhealth.dac.gov.in',
            'https://agricoop.gov.in',
            'https://agrimachinery.nic.in',
            'https://pgsindia-ncof.gov.in',
            'https://rkvy.nic.in',
            'https://nabard.org',
            'https://agriculture.gov.in'
        ]
        
        search_results = []
        
        # Search through authorized URLs for relevant schemes
        for url in authorized_urls:
            if self.is_authorized_domain(url):
                try:
                    response = self.session.get(url, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Extract title and description
                        title = self.extract_title(soup, url)
                        description = self.extract_description(soup, url)
                        
                        if title and description:
                            search_results.append({
                                'title': title,
                                'description': description,
                                'url': url,
                                'domain': urlparse(url).netloc
                            })
                    
                    time.sleep(1)  # Respect servers
                    
                except Exception as e:
                    print(f"⚠️  Error accessing {url}: {e}")
                    continue
        
        print(f"✅ Found {len(search_results)} results from authorized domains")
        return search_results
    
    def extract_title(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract scheme name from official page"""
        # Try multiple title sources
        title_selectors = [
            'h1',
            '.page-title',
            '.scheme-title',
            'title',
            '.main-title',
            'h2'
        ]
        
        for selector in title_selectors:
            elements = soup.select(selector)
            if elements:
                title = elements[0].get_text(strip=True)
                # Clean up title
                title = re.sub(r'\s+', ' ', title)
                if len(title) > 5:  # Valid title
                    return title
        
        return None
    
    def extract_description(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract official description from page content"""
        # Try multiple description sources
        desc_selectors = [
            '.description',
            '.scheme-description',
            '.content p',
            '.main-content p',
            'meta[name="description"]',
            '.intro p'
        ]
        
        for selector in desc_selectors:
            elements = soup.select(selector)
            if elements:
                desc_text = elements[0].get_text(strip=True)
                if selector.startswith('meta'):
                    desc_text = elements[0].get('content', '')
                
                # Clean up description
                desc_text = re.sub(r'\s+', ' ', desc_text)
                if len(desc_text) > 20:  # Valid description
                    return desc_text
        
        # Fallback: Get first paragraph
        paragraphs = soup.find_all('p')
        if paragraphs:
            desc = paragraphs[0].get_text(strip=True)
            if len(desc) > 20:
                return desc
        
        return None
    
    def fetch_scheme_details(self, url: str) -> Optional[Dict[str, str]]:
        """Fetch detailed information from a specific government URL"""
        if not self.is_authorized_domain(url):
            print(f"❌ Unauthorized domain: {url}")
            return None
        
        try:
            print(f"📄 Fetching details from: {url}")
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                title = self.extract_title(soup, url)
                description = self.extract_description(soup, url)
                
                if title and description:
                    return {
                        'scheme_name': title,
                        'description': description,
                        'official_url': url,
                        'source': urlparse(url).netloc
                    }
            
        except Exception as e:
            print(f"❌ Error fetching {url}: {e}")
        
        return None
    
    def search_authorized_schemes(self, query: str) -> List[Dict[str, str]]:
        """
        Main search method following strict rules
        Returns ONLY authorized government schemes without modification
        """
        print(f"🔍 Searching authorized government domains for: '{query}'")
        
        # Step 1: Perform web search
        search_results = self.search_google_for_schemes(query)
        
        # Step 2: Filter by query relevance
        relevant_results = []
        query_lower = query.lower()
        
        for result in search_results:
            title_lower = result['title'].lower()
            desc_lower = result['description'].lower()
            
            # Check if query matches title or description
            query_terms = query_lower.split()
            if any(term in title_lower or term in desc_lower for term in query_terms if len(term) > 2):
                relevant_results.append(result)
        
        # Step 3: Fetch detailed information from official pages
        authorized_schemes = []
        for result in relevant_results:
            scheme_details = self.fetch_scheme_details(result['url'])
            if scheme_details:
                authorized_schemes.append(scheme_details)
        
        if not authorized_schemes:
            print("❌ No official government scheme found for this query.")
        
        return authorized_schemes
    
    def get_scheme_by_exact_name(self, scheme_name: str) -> Optional[Dict[str, str]]:
        """Get specific scheme by exact name from authorized sources"""
        # Search for exact scheme name
        results = self.search_authorized_schemes(scheme_name)
        
        for result in results:
            if scheme_name.lower() in result['scheme_name'].lower():
                return result
        
        return None
