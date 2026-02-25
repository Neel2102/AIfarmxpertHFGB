from __future__ import annotations
from typing import Dict, Any, List, Optional
from enum import Enum
import re
from dataclasses import dataclass
from farmxpert.core.utils.logger import get_logger


class IntentType(Enum):
    """Enumeration of all possible farmer intents"""
    CROP_PLANNING = "crop_planning"
    PEST_DISEASE_DIAGNOSIS = "pest_disease_diagnosis"
    YIELD_OPTIMIZATION = "yield_optimization"
    TASK_SCHEDULING = "task_scheduling"
    MARKET_ANALYSIS = "market_analysis"
    SOIL_HEALTH = "soil_health"
    WEATHER_QUERY = "weather_query"
    FERTILIZER_ADVICE = "fertilizer_advice"
    IRRIGATION_PLANNING = "irrigation_planning"
    HARVEST_PLANNING = "harvest_planning"
    RISK_MANAGEMENT = "risk_management"
    FARMER_SUPPORT = "farmer_support"
    GENERAL_QUERY = "general_query"


@dataclass
class IntentResult:
    """Result of intent classification"""
    intent_type: IntentType
    confidence: float
    entities: Dict[str, Any]
    original_query: str
    language: str = "en"


class IntentEngine:
    """Engine for understanding farmer queries and classifying intents"""
    
    def __init__(self):
        self.logger = get_logger("intent_engine")
        self._intent_patterns = self._build_intent_patterns()
        self._entity_extractors = self._build_entity_extractors()
    
    def _build_intent_patterns(self) -> Dict[IntentType, List[str]]:
        """Build keyword patterns for each intent type"""
        return {
            IntentType.CROP_PLANNING: [
                r"what.*plant|what.*crop|which.*crop|plant.*next|sow.*what",
                r"crop.*planning|crop.*selection|best.*crop|recommend.*crop",
                r"what.*grow|growing.*season|planting.*season"
            ],
            IntentType.PEST_DISEASE_DIAGNOSIS: [
                r"pest|disease|bug|insect|fungus|mold|mildew|blight",
                r"yellow.*leaf|brown.*spot|white.*spot|rot|wilt",
                r"damage.*plant|plant.*sick|treatment.*pest|spray.*what",
                r"leaves.*yellow|spots.*white|spots.*brown"
            ],
            IntentType.YIELD_OPTIMIZATION: [
                r"yield|production|output|harvest.*more|increase.*yield",
                r"optimize.*production|maximize.*yield|better.*harvest",
                r"productivity|efficiency|improve.*crop"
            ],
            IntentType.TASK_SCHEDULING: [
                r"schedule|plan.*work|task.*list|daily.*routine|weekly.*plan",
                r"when.*plant|when.*harvest|timing|calendar|schedule.*farm",
                r"work.*plan|operation.*plan|farm.*schedule"
            ],
            IntentType.MARKET_ANALYSIS: [
                r"market|price|demand|supply|sell|profit|revenue|income",
                r"market.*trend|price.*forecast|best.*price|when.*sell",
                r"market.*analysis|economic|financial|cost.*benefit"
            ],
            IntentType.SOIL_HEALTH: [
                r"soil|fertility|nutrient|ph|nitrogen|phosphorus|potassium",
                r"soil.*test|soil.*health|soil.*condition|soil.*quality",
                r"fertilizer|manure|compost|soil.*preparation"
            ],
            IntentType.WEATHER_QUERY: [
                r"weather|rain|temperature|humidity|forecast|climate",
                r"rainfall|drought|flood|storm|seasonal.*weather",
                r"weather.*condition|weather.*prediction"
            ],
            IntentType.FERTILIZER_ADVICE: [
                r"fertilizer|npk|urea|dap|organic|inorganic|nutrient.*management",
                r"fertilizer.*application|fertilizer.*timing|fertilizer.*dose",
                r"nutrient.*deficiency|fertilizer.*recommendation"
            ],
            IntentType.IRRIGATION_PLANNING: [
                r"irrigation|water|drip|sprinkler|flood|water.*management",
                r"irrigation.*schedule|water.*requirement|irrigation.*timing",
                r"drought.*resistant|water.*conservation"
            ],
            IntentType.HARVEST_PLANNING: [
                r"harvest|harvesting|maturity|ripening|harvest.*time",
                r"when.*harvest|harvest.*schedule|post.*harvest|storage",
                r"harvest.*method|harvest.*equipment"
            ],
            IntentType.RISK_MANAGEMENT: [
                r"risk|insurance|protection|safety|prevention|mitigation",
                r"crop.*insurance|risk.*management|disaster.*preparation",
                r"weather.*risk|market.*risk|production.*risk"
            ],
            IntentType.FARMER_SUPPORT: [
                r"help|support|advice|guidance|training|education|learning",
                r"certification|compliance|community|expert|consultant",
                r"farmer.*support|agricultural.*extension|best.*practice"
            ]
        }
    
    def _build_entity_extractors(self) -> Dict[str, callable]:
        """Build entity extraction functions"""
        return {
            "location": self._extract_location,
            "crop": self._extract_crop,
            "time_period": self._extract_time_period,
            "measurement": self._extract_measurement,
            "symptoms": self._extract_symptoms
        }
    
    def classify_intent(self, query: str) -> IntentResult:
        """Classify the intent of a farmer query"""
        query_lower = query.lower().strip()
        
        # Detect language (simple detection for now)
        language = self._detect_language(query)
        
        # Extract entities first
        entities = self._extract_entities(query_lower)
        
        # Classify intent
        best_intent = IntentType.GENERAL_QUERY
        best_confidence = 0.0
        
        for intent_type, patterns in self._intent_patterns.items():
            confidence = self._calculate_confidence(query_lower, patterns)
            if confidence > best_confidence:
                best_confidence = confidence
                best_intent = intent_type
        
        self.logger.info("intent_classified", 
                        query=query, 
                        intent=best_intent.value, 
                        confidence=best_confidence,
                        entities=entities)
        
        return IntentResult(
            intent_type=best_intent,
            confidence=best_confidence,
            entities=entities,
            original_query=query,
            language=language
        )
    
    def _calculate_confidence(self, query: str, patterns: List[str]) -> float:
        """Calculate confidence score for intent classification"""
        matches = 0
        total_patterns = len(patterns)
        
        for pattern in patterns:
            if re.search(pattern, query, re.IGNORECASE):
                matches += 1
        
        # Base confidence on pattern matches
        base_confidence = matches / total_patterns if total_patterns > 0 else 0.0
        
        # Boost confidence for multiple matches
        if matches > 1:
            base_confidence *= 1.2
        
        # Cap at 1.0
        return min(base_confidence, 1.0)
    
    def _extract_entities(self, query: str) -> Dict[str, Any]:
        """Extract entities from the query"""
        entities = {}
        
        for entity_type, extractor in self._entity_extractors.items():
            result = extractor(query)
            if result:
                entities[entity_type] = result
        
        return entities
    
    def _extract_location(self, query: str) -> Optional[str]:
        """Extract location information"""
        # Simple location extraction - can be enhanced with NLP
        location_patterns = [
            r"in\s+([a-zA-Z\s]+?)(?:\s+state|\s+district|\s+area|$)",
            r"at\s+([a-zA-Z\s]+?)(?:\s+state|\s+district|\s+area|$)",
            r"from\s+([a-zA-Z\s]+?)(?:\s+state|\s+district|\s+area|$)",
            r"location\s+([a-zA-Z\s]+?)(?:\s+state|\s+district|\s+area|$)"
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_crop(self, query: str) -> Optional[str]:
        """Extract crop information"""
        crops = [
            "wheat", "rice", "maize", "cotton", "sugarcane", "potato", "tomato",
            "onion", "chilli", "pepper", "corn", "soybean", "pulses", "millets",
            "bajra", "jowar", "ragi", "tur", "moong", "urad", "chana", "masoor"
        ]
        
        for crop in crops:
            if crop in query:
                return crop
        
        return None
    
    def _extract_time_period(self, query: str) -> Optional[str]:
        """Extract time period information"""
        time_patterns = [
            r"next\s+(week|month|season|year)",
            r"this\s+(week|month|season|year)",
            r"in\s+(\d+)\s+(days|weeks|months)",
            r"(january|february|march|april|may|june|july|august|september|october|november|december)"
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def _extract_measurement(self, query: str) -> Optional[Dict[str, Any]]:
        """Extract measurement information"""
        measurement_patterns = [
            r"(\d+(?:\.\d+)?)\s*(acre|hectare|ha|kg|ton|quintal|litre|l)",
            r"(\d+(?:\.\d+)?)\s*(percent|%)",
            r"(\d+(?:\.\d+)?)\s*(degree|celsius|fahrenheit)"
        ]
        
        for pattern in measurement_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return {
                    "value": float(match.group(1)),
                    "unit": match.group(2)
                }
        
        return None
    
    def _extract_symptoms(self, query: str) -> Optional[List[str]]:
        """Extract disease/pest symptoms"""
        symptoms = [
            "yellow leaves", "brown spots", "white powder", "black spots",
            "wilting", "rotting", "holes in leaves", "curled leaves",
            "stunted growth", "leaf drop", "fruit drop", "root rot"
        ]
        
        found_symptoms = []
        for symptom in symptoms:
            if symptom in query:
                found_symptoms.append(symptom)
        
        return found_symptoms if found_symptoms else None
    
    def _detect_language(self, query: str) -> str:
        """Detect the language of the query"""
        # Simple language detection - can be enhanced with proper NLP
        hindi_patterns = [
            r"[अ-ह]",
            r"क्या|कैसे|कब|कहाँ|कौन|क्यों",
            r"में|का|की|के|है|हैं|था|थी"
        ]
        
        for pattern in hindi_patterns:
            if re.search(pattern, query):
                return "hi"
        
        return "en"
