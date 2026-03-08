"""
Debug the agent roles endpoint issue
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from farmxpert.core.core_agent_updated import core_agent
    print("✅ Core agent imported successfully")
    
    # Test getting available agents
    agents = core_agent.get_available_agents()
    print(f"📊 Available agents: {len(agents)}")
    print(f"🔗 First few agents: {agents[:5]}")
    
    # Test getting agent info
    if agents:
        first_agent = agents[0]
        info = core_agent.get_agent_info(first_agent)
        print(f"ℹ️  Info for {first_agent}: {info is not None}")
        if info:
            print(f"📝 Description: {info.get('description', 'N/A')[:50]}...")
    
    # Test the full roles endpoint logic
    roles_info = {}
    for role in agents:
        agent_info = core_agent.get_agent_info(role)
        if agent_info:
            roles_info[role] = agent_info.get("description", "No description available")
    
    print(f"🎯 Roles info created: {len(roles_info)} roles")
    print(f"📝 Sample roles: {list(roles_info.keys())[:3]}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
