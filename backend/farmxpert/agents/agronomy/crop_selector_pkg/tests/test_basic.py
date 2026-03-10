"""
Quick test to verify the Crop Selector Agent is working correctly
"""

from crop_selector_agent import CropSelectorAgent, FarmerContext
from mock_agents import MockAgentOrchestrator


def test_basic_functionality():
    """Test basic functionality of the Crop Selector Agent"""
    
    print("Testing Crop Selector Agent...")
    
    # Initialize
    crop_selector = CropSelectorAgent()
    orchestrator = MockAgentOrchestrator()
    
    # Create test farmer
    farmer = FarmerContext(
        location={"state": "Punjab", "district": "Ludhiana"},
        season="Kharif",
        land_size_acre=5.0,
        risk_preference="Low"
    )
    
    # Get agent outputs
    agent_outputs = orchestrator.get_all_agent_outputs(
        farmer.location["state"], 
        farmer.location["district"], 
        farmer.season
    )
    
    # Get recommendations
    response = crop_selector.select_crops(
        farmer,
        agent_outputs["weather"],
        agent_outputs["soil"],
        agent_outputs["water"],
        agent_outputs["pest"],
        agent_outputs["market"],
        agent_outputs["government"]
    )
    
    # Verify structure
    assert "situation" in response
    assert "season_risk" in response
    assert "recommendations" in response
    assert "avoid" in response
    assert "reasoning" in response
    assert "next_steps" in response
    assert "assumptions" in response
    assert "confidence" in response
    
    # Verify recommendations structure
    assert "safest" in response["recommendations"]
    assert "balanced" in response["recommendations"]
    assert "higher_risk" in response["recommendations"]
    
    print("All tests passed!")
    print(f"Found {len(response['recommendations']['safest'])} safest crops")
    print(f"Found {len(response['recommendations']['balanced'])} balanced crops")
    print(f"Found {len(response['recommendations']['higher_risk'])} higher-risk crops")
    print(f"Found {len(response['avoid'])} crops to avoid")
    
    return True


if __name__ == "__main__":
    test_basic_functionality()
