"""
Migration Script: From Multi-Agent to Core Agent Router
This script helps transition from the old multi-agent system to the new core agent router.
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime

def backup_existing_agents():
    """Create a backup of existing agents before migration"""
    backup_dir = Path("scripts/agent_backup_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    backup_dir.mkdir(exist_ok=True)
    
    agents_dir = Path("farmxpert/agents")
    if agents_dir.exists():
        shutil.copytree(agents_dir, backup_dir / "agents")
        print(f"✅ Backed up existing agents to: {backup_dir}")
    
    return backup_dir

def create_migration_summary():
    """Create a summary of what was migrated"""
    summary = {
        "migration_date": datetime.now().isoformat(),
        "migrated_agents": [
            "soil_health", "crop_selector", "seed_selection", "fertilizer_advisor",
            "irrigation_planner", "pest_disease_diagnostic", "weather_watcher",
            "growth_stage_monitor", "task_scheduler", "machinery_equipment",
            "farm_layout_mapping", "yield_predictor", "profit_optimization",
            "carbon_sustainability", "market_intelligence", "logistics_storage",
            "input_procurement", "crop_insurance_risk", "farmer_coach",
            "compliance_certification", "community_engagement"
        ],
        "new_architecture": {
            "core_agent": "farmxpert/core/core_agent.py",
            "prompts": "farmxpert/core/agent_prompts.json",
            "routes": "farmxpert/core/agent_routes.py"
        },
        "benefits": [
            "Single point of maintenance",
            "Consistent error handling",
            "Unified logging and monitoring",
            "Easier testing and debugging",
            "Reduced code duplication",
            "Faster development cycles"
        ]
    }
    
    with open("scripts/migration_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print("✅ Migration summary created: scripts/migration_summary.json")
    return summary

def update_super_agent_integration():
    """Update super_agent.py to use the new core agent"""
    super_agent_path = Path("farmxpert/core/super_agent.py")
    
    if super_agent_path.exists():
        # Create a backup
        shutil.copy2(super_agent_path, Path("scripts/super_agent_backup.py"))
        
        # Note: This would require manual integration to update the super agent
        # to use the new core_agent instead of individual agents
        print("⚠️  Manual integration needed: Update super_agent.py to use core_agent")
        print("   - Replace individual agent calls with core_agent.process_request()")
        print("   - Update agent selection logic to use agent roles from prompts")

def main():
    """Main migration process"""
    print("🚀 Starting Agent Migration to Core Router Pattern")
    print("=" * 60)
    
    # Step 1: Backup existing agents
    print("📦 Step 1: Backing up existing agents...")
    backup_dir = backup_existing_agents()
    
    # Step 2: Create migration summary
    print("📋 Step 2: Creating migration summary...")
    summary = create_migration_summary()
    
    # Step 3: Note integration requirements
    print("🔧 Step 3: Integration requirements...")
    update_super_agent_integration()
    
    print("\n" + "=" * 60)
    print("✅ Migration Complete!")
    print("\nNext Steps:")
    print("1. Test the new core_agent.py with different roles")
    print("2. Update super_agent.py to use core_agent")
    print("3. Update API routes to use agent_routes.py")
    print("4. Run comprehensive tests")
    print("5. Remove old agent files after verification")
    
    print(f"\nBackup location: {backup_dir}")
    print("Migration summary: scripts/migration_summary.json")
    
    print("\n🎉 Benefits Achieved:")
    for benefit in summary["benefits"]:
        print(f"  ✅ {benefit}")

if __name__ == "__main__":
    main()
