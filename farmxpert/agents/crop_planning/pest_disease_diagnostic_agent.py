from __future__ import annotations
from typing import Dict, Any, List, Optional
from farmxpert.core.base_agent.enhanced_base_agent import EnhancedBaseAgent
from farmxpert.services.tools import ImageRecognitionTool, VoiceToTextTool, DiseasePredictionTool, PestDiseaseTool
from farmxpert.services.gemini_service import gemini_service
from farmxpert.services.providers.pest_disease_inference import PestDiseaseInferenceProvider


class PestDiseaseDiagnosticAgent(EnhancedBaseAgent):
    name = "pest_disease_diagnostic"
    description = "Diagnoses pest and disease issues using image recognition, voice processing, and predictive modeling"

    def _get_system_prompt(self) -> str:
        return """You are a Pest & Disease Diagnostic Agent specializing in comprehensive plant health analysis and treatment recommendations.

Your expertise includes:
- Image-based disease and pest identification
- Voice-to-text processing for symptom descriptions
- Disease prediction and outbreak forecasting
- Integrated pest management strategies
- Treatment recommendations and prevention
- Economic impact assessment

Always provide accurate diagnoses with practical treatment solutions and preventive measures."""

    def _get_examples(self) -> List[Dict[str, str]]:
        return [
            {
                "input": "My wheat leaves have yellow spots and are wilting",
                "output": "Based on the symptoms described, this appears to be a combination of fungal disease (likely leaf blight) and possible root rot. I recommend applying a copper-based fungicide immediately and improving field drainage. Monitor for 3-5 days and consider soil testing for nutrient deficiencies."
            },
            {
                "input": "I see small insects on my cotton plants",
                "output": "The insects you're seeing are likely aphids or whiteflies. I recommend applying neem oil spray (2-3ml per liter) in the early morning or evening. Monitor the population for 5-7 days and repeat treatment if necessary. Consider introducing beneficial insects like ladybugs for long-term control."
            }
        ]

    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pest and disease diagnosis using dynamic tools and comprehensive analysis"""
        try:
            # Get tools from inputs
            tools = inputs.get("tools", {})
            context = inputs.get("context", {})
            query = inputs.get("query", "")
            
            # Extract parameters
            crop = self._extract_crop_from_query(query) or context.get("crop", "wheat")
            location = context.get("farm_location", inputs.get("location", "unknown"))
            symptoms = context.get("symptoms", inputs.get("symptoms", []))
            image_data = context.get("image_data", {})
            voice_data = context.get("voice_data", {})
            environmental_data = context.get("environmental_data", {})
            
            # Initialize data containers
            image_analysis_data = {}
            voice_analysis_data = {}
            disease_prediction_data = {}
            risk_analysis_data = {}
            
            # Get image-based disease/pest identification using inference provider
            if image_data:
                try:
                    provider = PestDiseaseInferenceProvider.get_default()
                    # Extract image bytes from context (base64 or direct)
                    image_bytes = image_data.get("bytes") or image_data.get("data")
                    if isinstance(image_bytes, str):
                        import base64
                        image_bytes = base64.b64decode(image_bytes.split(",")[-1])
                    if image_bytes:
                        inference_result = await provider.infer_from_bytes(image_bytes, crop=crop, location=location)
                        if inference_result.success:
                            image_analysis_data = {
                                "success": True,
                                "disease_name": inference_result.diagnosis.get("disease_pest_name") if inference_result.diagnosis else "unknown",
                                "confidence": inference_result.confidence,
                                "severity": inference_result.severity,
                                "symptoms": inference_result.diagnosis.get("symptoms_description") if inference_result.diagnosis else "",
                                "treatment": inference_result.diagnosis.get("treatment_recommendations") if inference_result.diagnosis else [],
                                "provider": inference_result.provider,
                            }
                        else:
                            image_analysis_data = {"success": False, "error": inference_result.error, "provider": inference_result.provider}
                    else:
                        image_analysis_data = {"success": False, "error": "No image bytes provided"}
                except Exception as e:
                    self.logger.warning(f"Failed to run inference: {e}")
                    image_analysis_data = {"success": False, "error": str(e)}
            
            # Get voice description processing
            if "voice_to_text" in tools and voice_data:
                try:
                    voice_analysis_data = await tools["voice_to_text"].process_voice_description(
                        voice_data, crop, location
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to process voice data: {e}")
            
            # Get disease prediction
            if "disease_prediction" in tools and environmental_data:
                try:
                    disease_prediction_data = await tools["disease_prediction"].predict_disease_outbreak(
                        environmental_data, crop, location
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to predict disease outbreak: {e}")
            
            # Get risk analysis
            if "disease_prediction" in tools:
                try:
                    historical_data = context.get("historical_data", {})
                    current_conditions = context.get("current_conditions", environmental_data)
                    risk_analysis_data = await tools["disease_prediction"].analyze_disease_risk_factors(
                        historical_data, current_conditions, crop, location
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to analyze risk factors: {e}")
            
            # Build comprehensive prompt for Gemini
            prompt = f"""
You are an expert pest and disease diagnostic specialist. Based on the following comprehensive analysis, provide detailed diagnosis and treatment recommendations for the farmer.

Farmer's Query: "{query}"

Analysis Results:
- Crop: {crop}
- Location: {location}
- Symptoms: {symptoms}
- Image Analysis: {image_analysis_data.get('disease_identification', {})}
- Voice Analysis: {voice_analysis_data.get('symptoms_extracted', {})}
- Disease Prediction: {disease_prediction_data.get('outbreak_probability', {})}
- Risk Analysis: {risk_analysis_data.get('current_risk_level', {})}

Provide comprehensive diagnosis and treatment recommendations including:
1. Primary diagnosis and confidence level
2. Secondary possible conditions
3. Severity assessment and urgency
4. Immediate treatment recommendations
5. Long-term management strategies
6. Prevention measures
7. Economic impact assessment
8. Monitoring and follow-up requirements
9. When to seek professional help
10. Alternative treatment options

Format your response as a natural conversation with the farmer.
"""

            response = await gemini_service.generate_response(prompt, {"agent": self.name, "task": "pest_disease_diagnosis"})

            # If LLM quota/rate limit is hit, fall back to deterministic output
            resp_lower = (response or "").lower()
            if "429" in resp_lower or "quota" in resp_lower or "rate limit" in resp_lower:
                return await self._handle_traditional(inputs)
            
            return {
                "agent": self.name,
                "success": True,
                "response": response,
                "data": {
                    "crop": crop,
                    "location": location,
                    "symptoms": symptoms,
                    "image_analysis_data": image_analysis_data,
                    "voice_analysis_data": voice_analysis_data,
                    "disease_prediction_data": disease_prediction_data,
                    "risk_analysis_data": risk_analysis_data
                },
                "recommendations": self._extract_recommendations_from_data(image_analysis_data, voice_analysis_data),
                "warnings": self._extract_warnings_from_data(disease_prediction_data, risk_analysis_data),
                "metadata": {"model": "gemini", "tools_used": list(tools.keys())}
            }
            
        except Exception as e:
            self.logger.error(f"Error in pest disease diagnostic agent: {e}")
            # Fallback to traditional method
            return await self._handle_traditional(inputs)
    
    async def _handle_traditional(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback traditional pest/disease diagnosis method"""
        symptoms = inputs.get("symptoms", [])
        crop = inputs.get("crop", "unknown")
        location = inputs.get("location", "unknown")
        weather_conditions = inputs.get("weather_conditions", {})
        
        # Stub diagnosis based on common symptoms
        possible_issues = []
        treatments = []
        
        if "yellowing leaves" in symptoms:
            possible_issues.append("Nitrogen deficiency or aphid infestation")
            treatments.append("Apply nitrogen fertilizer or neem oil spray")
            
        if "brown spots" in symptoms:
            possible_issues.append("Fungal disease (blight)")
            treatments.append("Apply copper-based fungicide")
            
        if "wilting" in symptoms:
            possible_issues.append("Root rot or water stress")
            treatments.append("Improve drainage and reduce watering")
            
        if not possible_issues:
            possible_issues.append("No clear diagnosis from symptoms")
            treatments.append("Contact local agricultural extension officer")
            
        return {
            "agent": self.name,
            "success": True,
            "crop": crop,
            "symptoms_analyzed": symptoms,
            "possible_issues": possible_issues,
            "recommended_treatments": treatments,
            "severity_level": "moderate",
            "follow_up_required": True,
            "metadata": {"source": "traditional"}
        }
    
    def _extract_crop_from_query(self, query: str) -> Optional[str]:
        """Extract mentioned crop from user query"""
        query_lower = query.lower()
        crops = ["wheat", "rice", "maize", "cotton", "sugarcane", "groundnut", "soybean", 
                "barley", "mustard", "chickpea", "lentil", "potato", "onion", "tomato"]
        
        for crop in crops:
            if crop in query_lower:
                return crop
        return None
    
    def _extract_recommendations_from_data(self, image_analysis_data: Dict[str, Any], voice_analysis_data: Dict[str, Any]) -> List[str]:
        """Extract recommendations from analysis data"""
        recommendations = []
        
        if isinstance(image_analysis_data, dict):
            if "treatment_recommendations" in image_analysis_data:
                recommendations.append("Image-based treatment recommendations available")
            
            if "prevention_strategies" in image_analysis_data:
                recommendations.append("Prevention strategies provided")
        
        if isinstance(voice_analysis_data, dict):
            if "recommended_steps" in voice_analysis_data:
                recommendations.append("Voice-based action steps available")
            
            if "follow_up_questions" in voice_analysis_data:
                recommendations.append("Follow-up questions for clarification")
        
        return recommendations
    
    def _extract_warnings_from_data(self, disease_prediction_data: Dict[str, Any], risk_analysis_data: Dict[str, Any]) -> List[str]:
        """Extract warnings from analysis data"""
        warnings = []
        
        if isinstance(disease_prediction_data, dict):
            if "high_risk_diseases" in disease_prediction_data:
                high_risk = disease_prediction_data["high_risk_diseases"]
                if isinstance(high_risk, list) and high_risk:
                    warnings.append(f"High-risk diseases identified: {', '.join(high_risk[:2])}")
        
        if isinstance(risk_analysis_data, dict):
            if "current_risk_level" in risk_analysis_data:
                risk_level = risk_analysis_data["current_risk_level"]
                if isinstance(risk_level, str) and risk_level.lower() in ["high", "severe"]:
                    warnings.append(f"High risk level detected: {risk_level}")
        
        return warnings
