"""
Mock Market Intelligence Service for testing orchestrator integration
Enhanced with real market data for cotton in Gujarat
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional


class MockMarketIntelligenceService:
    """Mock service for testing market intelligence integration with real market data"""
    
    def __init__(self):
        """Initialize the mock service"""
        self.agent_info = {
            "name": "Market Intelligence Agent",
            "version": "2.0.0",
            "capabilities": [
                "Market price analysis",
                "Revenue projections", 
                "Market recommendations",
                "Price trend analysis"
            ],
            "supported_crops": ["cotton", "wheat", "groundnut", "sesame"],
            "supported_states": ["Gujarat", "Punjab", "Maharashtra"],
            "data_sources": ["agmarknet", "historical_data"]
        }
        
        # Real market data for cotton in Gujarat (simulated but realistic)
        self.cotton_gujarat_markets = {
            "Rajkot APMC": {
                "price": 7850,
                "trend": "stable",
                "confidence": 0.85,
                "volume": "high"
            },
            "Viramgam APMC": {
                "price": 7870,
                "trend": "increasing",
                "confidence": 0.90,
                "volume": "very_high"
            },
            "Ahmedabad APMC": {
                "price": 7750,
                "trend": "stable",
                "confidence": 0.80,
                "volume": "high"
            },
            "Surat APMC": {
                "price": 7800,
                "trend": "decreasing",
                "confidence": 0.75,
                "volume": "medium"
            },
            "Vadodara APMC": {
                "price": 7720,
                "trend": "stable",
                "confidence": 0.70,
                "volume": "medium"
            }
        }
    
    async def comprehensive_analyze(self, crop_info: Dict[str, Any], location: Dict[str, Any], farm_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Perform comprehensive market analysis
        """
        try:
            # Simulate processing time
            await asyncio.sleep(0.2)
            
            # Extract crop and location info
            crop_name = crop_info.get('name', 'unknown')
            state = location.get('state', 'Gujarat')
            district = location.get('district', 'Ahmedabad')
            area_hectares = farm_info.get('area_hectares', 1) if farm_info else 1
            expected_yield = farm_info.get('expected_yield_quintals_per_hectare', 15) if farm_info else 15
            
            # Use the same logic as quick_analyze
            return await self.quick_analyze(
                crop=crop_name,
                state=state,
                area_hectares=area_hectares,
                expected_yield_quintals_per_hectare=expected_yield,
                district=district
            )
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Comprehensive analysis failed: {str(e)}",
                "error_type": "ProcessingError"
            }
    
    async def quick_analyze(self, crop: str, state: str, area_hectares: Optional[float] = None, 
                          expected_yield_quintals_per_hectare: Optional[float] = None,
                          district: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform quick market analysis with real market data
        """
        try:
            # Simulate processing time
            await asyncio.sleep(0.1)
            
            # Check if we have data for the requested crop and state
            if crop.lower() == "cotton" and state.lower() == "gujarat":
                # Sort markets by price (highest first)
                sorted_markets = sorted(
                    self.cotton_gujarat_markets.items(),
                    key=lambda x: x[1]["price"],
                    reverse=True
                )
                
                # Get top 3 markets
                top_3_markets = sorted_markets[:3]
                
                # Calculate estimated revenue
                total_yield = (expected_yield_quintals_per_hectare or 15) * (area_hectares or 1)
                best_price = top_3_markets[0][1]["price"]
                estimated_revenue = total_yield * best_price
                
                # Create market recommendations
                recommendations = []
                for i, (market_name, market_data) in enumerate(top_3_markets):
                    if i == 0:
                        recommendations.append(f"Best price: {market_name} at Rs. {market_data['price']}/quintal")
                    elif i == 1:
                        recommendations.append(f"Good alternative: {market_name} at Rs. {market_data['price']}/quintal")
                    else:
                        recommendations.append(f"Consider: {market_name} at Rs. {market_data['price']}/quintal")
                
                analysis = {
                    "recommended_market": top_3_markets[0][0],
                    "best_price": top_3_markets[0][1]["price"],
                    "average_price": sum(market_data["price"] for _, market_data in top_3_markets) / len(top_3_markets),
                    "confidence": top_3_markets[0][1]["confidence"],
                    "estimated_revenue": estimated_revenue,
                    "top_markets": [
                        {
                            "name": market_name,
                            "price": market_data["price"],
                            "trend": market_data["trend"],
                            "confidence": market_data["confidence"]
                        }
                        for market_name, market_data in top_3_markets
                    ],
                    "recommendations": recommendations,
                    "market_trend": "stable to increasing",
                    "volume_analysis": "High trading volume observed in major markets"
                }
                
                return {
                    "success": True,
                    "data": analysis,
                    "timestamp": datetime.now().isoformat(),
                    "processing_time": 0.1
                }
            else:
                return {
                    "success": False,
                    "error": f"No market data available for {crop} in {state}",
                    "error_type": "NoDataError"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Analysis failed: {str(e)}",
                "error_type": "ProcessingError"
            }
    
    async def comprehensive_analyze(self, crop_info: Dict[str, Any], location: Dict[str, Any],
                                   farm_info: Dict[str, Any], 
                                   preferences: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Mock comprehensive market analysis
        """
        # For now, just call quick analyze with extracted data
        return await self.quick_analyze(
            crop=crop_info.get("name", "unknown"),
            state=location.get("state", "unknown"),
            area_hectares=farm_info.get("area_hectares"),
            expected_yield_quintals_per_hectare=farm_info.get("expected_yield_quintals_per_hectare"),
            district=location.get("district")
        )
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return self.agent_info


# Create singleton instance
mock_market_intelligence_service = MockMarketIntelligenceService()
