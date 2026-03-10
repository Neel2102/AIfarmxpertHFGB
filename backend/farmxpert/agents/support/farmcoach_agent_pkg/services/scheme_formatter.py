"""
Scheme formatting and explanation service
"""

from typing import List
from ..models.input_model import SchemeData
from ..models.output_model import SchemeInfo


class SchemeFormatter:
    """Service to format and explain government schemes in farmer-friendly language"""
    
    def __init__(self):
        self.agriculture_keywords = [
            'insurance', 'subsidy', 'income', 'support', 'msp', 'welfare', 
            'crop', 'farmer', 'agriculture', 'loan', 'seed', 'fertilizer',
            'irrigation', 'equipment', 'drought', 'flood', 'pesticide'
        ]
    
    def match_schemes_to_query(self, query: str, schemes_data: List[SchemeData]) -> List[SchemeData]:
        """Match schemes relevant to the farmer's query using keyword matching"""
        query_lower = query.lower()
        matched_schemes = []
        
        for scheme in schemes_data:
            # Check if query keywords match scheme description or name
            scheme_text = f"{scheme.scheme_name.lower()} {scheme.description.lower()}"
            
            # Simple keyword matching
            if any(keyword in query_lower for keyword in self.agriculture_keywords):
                if any(keyword in scheme_text for keyword in self.agriculture_keywords):
                    matched_schemes.append(scheme)
            # Direct text matching
            elif any(word in scheme_text for word in query_lower.split() if len(word) > 2):
                matched_schemes.append(scheme)
        
        return matched_schemes
    
    def simplify_description(self, description: str) -> str:
        """Rewrite description in simple, farmer-friendly language"""
        # Simple rules to make text more farmer-friendly
        simple_words = {
            'financial support': 'money help',
            'provides financial': 'gives money',
            'assistance': 'help',
            'benefits': 'help',
            'initiative': 'scheme',
            'programme': 'scheme',
            'implementation': 'starting',
            'eligible': 'can apply',
            'cultivators': 'farmers',
            'agriculturists': 'farmers',
            'stakeholders': 'people involved'
        }
        
        simplified = description.lower()
        for complex_word, simple_word in simple_words.items():
            simplified = simplified.replace(complex_word, simple_word)
        
        # Remove technical jargon and keep sentences short
        sentences = simplified.split('. ')
        simple_sentences = []
        
        for sentence in sentences:
            if len(sentence) > 100:
                # Break long sentences
                words = sentence.split()
                mid = len(words) // 2
                simple_sentences.append(' '.join(words[:mid]) + '.')
                simple_sentences.append(' '.join(words[mid:]) + '.')
            else:
                simple_sentences.append(sentence + '.')
        
        result = ' '.join(simple_sentences).strip()
        
        # Ensure it doesn't end with multiple periods
        while result.endswith('..'):
            result = result[:-1]
        
        if not result.endswith('.'):
            result += '.'
            
        return result.capitalize()
    
    def format_scheme_info(self, scheme: SchemeData) -> SchemeInfo:
        """Format a single scheme into the output model format"""
        simple_explanation = self.simplify_description(scheme.description)
        
        return SchemeInfo(
            scheme_name=scheme.scheme_name,
            simple_explanation=simple_explanation,
            official_link=scheme.official_url
        )
