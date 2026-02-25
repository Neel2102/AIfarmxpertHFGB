import sys
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add repo root to path
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "farmxpert"))

from farmxpert.core.super_agent import SuperAgent
from farmxpert.services.gemini_service import GeminiService

async def test_routing():
    print("Testing SuperAgent routing logic...")
    
    # Mock Gemini Service
    with patch("farmxpert.core.super_agent.gemini_service") as mock_gemini:
        # Define side effect for generate_response
        async def mock_generate_response(prompt, *args, **kwargs):
            if "Suggest a crop" in prompt:
                return '["crop_selector", "soil_health"]'
            elif "yellow spots" in prompt:
                return '["pest_disease_diagnostic"]'
            elif "rice field need" in prompt:
                return '["irrigation_planner"]'
            elif "wheat seeds" in prompt:
                return '["seed_selection"]'
            return '["crop_selector", "farmer_coach"]'

        mock_gemini.generate_response.side_effect = mock_generate_response
        
        agent = SuperAgent()
        
        test_cases = [
            ("Suggest a crop for clay soil in Gujarat", "crop_selector"),
            ("My wheat leaves have yellow spots", "pest_disease_diagnostic"),
            ("How much water does my rice field need?", "irrigation_planner"),
            ("Best high yield wheat seeds for Punjab", "seed_selection"),
        ]
        
        failed = []
        
        for query, expected_agent in test_cases:
            print(f"\nQuery: '{query}'")
            try:
                # We only care about _select_agents result
                selected_agents = await agent._select_agents(query)
                print(f"Selected agents: {selected_agents}")
                
                if expected_agent in selected_agents:
                    print(f"[OK] Correctly routed to {expected_agent}")
                else:
                    print(f"[FAIL] Failed to route to {expected_agent}")
                    failed.append((query, expected_agent, selected_agents))
                    
            except Exception as e:
                print(f"[ERROR] Error during routing: {e}")
                failed.append((query, expected_agent, str(e)))

        if failed:
            print(f"\nFailed cases: {len(failed)}")
            sys.exit(1)
        else:
            print("\nAll routing tests passed!")

if __name__ == "__main__":
    asyncio.run(test_routing())
