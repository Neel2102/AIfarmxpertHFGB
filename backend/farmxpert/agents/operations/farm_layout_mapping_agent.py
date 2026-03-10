from __future__ import annotations
from typing import Dict, Any, List
import math
from farmxpert.core.base_agent.enhanced_base_agent import EnhancedBaseAgent
from farmxpert.services.tools import FieldMappingTool
from farmxpert.services.gemini_service import gemini_service


class FarmLayoutMappingAgent(EnhancedBaseAgent):
    name = "farm_layout_mapping_agent"
    description = "Helps with field organization, plot allocation, crop rotation plans — all via logic-based planning, not imagery"

    async def handle(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate farm layout and mapping using geospatial tools (simulated)"""
        tools = inputs.get("tools", {})
        context = inputs.get("context", {})
        query = inputs.get("query", "")

        total_farm_size = context.get("total_farm_size", inputs.get("total_farm_size", 0))
        soil_types = context.get("soil_types", inputs.get("soil_types", {}))
        water_sources = context.get("water_sources", inputs.get("water_sources", []))
        planned_crops = context.get("planned_crops", inputs.get("planned_crops", []))
        existing_infrastructure = context.get("existing_infrastructure", inputs.get("existing_infrastructure", []))
        crop_rotation_history = context.get("crop_rotation_history", inputs.get("crop_rotation_history", {}))
        region = context.get("farm_location", inputs.get("location", "unknown"))
        field_boundaries = context.get("field_boundaries", [])
        overlays = context.get("overlays", {"irrigation": water_sources, "infrastructure": existing_infrastructure})

        # Generate field layout
        field_layout = self._generate_field_layout(total_farm_size, soil_types, water_sources)

        # Mapping tools
        map_layers = {}
        shape_analysis = {}
        map_exports = {}

        if "field_mapping" in tools and field_boundaries:
            try:
                map_layers = await tools["field_mapping"].generate_field_map(field_boundaries, overlays, region)
            except Exception as e:
                self.logger.warning(f"Failed to generate field map: {e}")

            try:
                shape_analysis = await tools["field_mapping"].analyze_field_shapes(field_boundaries)
            except Exception as e:
                self.logger.warning(f"Failed to analyze field shapes: {e}")

            try:
                map_exports = await tools["field_mapping"].export_map(map_layers, ["geojson", "png"])
            except Exception as e:
                self.logger.warning(f"Failed to export map: {e}")

        # Allocate crops to fields
        crop_allocation = self._allocate_crops_to_fields(field_layout, planned_crops, soil_types)

        # Create crop rotation plan
        rotation_plan = self._create_crop_rotation_plan(crop_allocation, crop_rotation_history)

        # Optimize layout for efficiency
        layout_optimization = self._optimize_layout(field_layout, existing_infrastructure, water_sources)

        # Synthesize narrative
        prompt = f"""
You are a farm layout and mapping specialist. Based on the following, provide a clear, actionable mapping plan and layout guidance.

Query: "{query}"
Region: {region}
Field Layout: {json.dumps(field_layout[:2], indent=2)}
Shape Analysis: {json.dumps(shape_analysis.get('areas', {}), indent=2)}
Map Exports: {json.dumps(map_exports.get('exports', {}), indent=2)}
Crop Allocation: {json.dumps(crop_allocation.get('field_allocations', {}), indent=2)}
Rotation Plan: {json.dumps(rotation_plan.get('rotation_cycles', {}), indent=2)}

Provide: map_summary, layout_plan, irrigation_overview, rotation_notes, export_links, next_steps
"""
        response = await gemini_service.generate_response(prompt, {"agent": self.name, "task": "farm_layout_mapping"})

        return {
            "agent": self.name,
            "success": True,
            "response": response,
            "data": {
                "total_farm_size_acres": total_farm_size,
                "field_layout": field_layout,
                "crop_allocation": crop_allocation,
                "crop_rotation_plan": rotation_plan,
                "layout_optimization": layout_optimization,
                "mapping": {"layers": map_layers, "shape_analysis": shape_analysis, "exports": map_exports}
            },
            "efficiency_score": self._calculate_efficiency_score(field_layout, crop_allocation),
            "recommendations": self._generate_layout_recommendations(field_layout, crop_allocation),
            "metadata": {"model": "gemini", "tools_used": list(tools.keys())}
        }
    
    def _generate_field_layout(self, total_size: float, soil_types: Dict, water_sources: List[str]) -> List[Dict[str, Any]]:
        """Generate optimal field layout based on farm characteristics"""
        fields = []
        
        # Calculate optimal field sizes based on total farm size
        if total_size <= 10:
            # Small farm - 2-3 fields
            num_fields = 2
            field_size = total_size / num_fields
        elif total_size <= 50:
            # Medium farm - 4-6 fields
            num_fields = 4
            field_size = total_size / num_fields
        else:
            # Large farm - 6-10 fields
            num_fields = min(8, int(total_size / 10))
            field_size = total_size / num_fields
        
        # Create fields with different characteristics
        for i in range(num_fields):
            field = {
                "field_id": f"field_{i+1}",
                "size_acres": round(field_size, 2),
                "shape": self._determine_field_shape(field_size),
                "soil_type": self._assign_soil_type(soil_types, i),
                "water_access": self._determine_water_access(water_sources, i, num_fields),
                "slope": self._estimate_slope(i),
                "drainage": self._assess_drainage(i),
                "accessibility": self._assess_accessibility(i, num_fields)
            }
            fields.append(field)
        
        return fields
    
    def _allocate_crops_to_fields(self, fields: List[Dict], planned_crops: List[str], soil_types: Dict) -> Dict[str, Any]:
        """Allocate crops to fields based on soil compatibility and field characteristics"""
        allocation = {
            "field_allocations": {},
            "crop_requirements": {},
            "compatibility_score": {}
        }
        
        # Define crop requirements
        crop_requirements = {
            "wheat": {
                "soil_preference": ["loam", "clay_loam"],
                "water_needs": "moderate",
                "field_size_min": 5,
                "drainage_needs": "good"
            },
            "maize": {
                "soil_preference": ["loam", "silt_loam"],
                "water_needs": "high",
                "field_size_min": 3,
                "drainage_needs": "excellent"
            },
            "pulses": {
                "soil_preference": ["loam", "sandy_loam"],
                "water_needs": "low",
                "field_size_min": 2,
                "drainage_needs": "good"
            },
            "rice": {
                "soil_preference": ["clay", "clay_loam"],
                "water_needs": "very_high",
                "field_size_min": 5,
                "drainage_needs": "poor"  # Rice needs water retention
            },
            "cotton": {
                "soil_preference": ["loam", "sandy_loam"],
                "water_needs": "moderate",
                "field_size_min": 3,
                "drainage_needs": "good"
            }
        }
        
        # Allocate crops to fields
        for field in fields:
            field_id = field["field_id"]
            best_crop = None
            best_score = 0
            
            for crop in planned_crops:
                if crop in crop_requirements:
                    score = self._calculate_crop_field_compatibility(crop, field, crop_requirements[crop])
                    if score > best_score:
                        best_score = score
                        best_crop = crop
            
            if best_crop:
                allocation["field_allocations"][field_id] = {
                    "crop": best_crop,
                    "compatibility_score": best_score,
                    "expected_yield": self._estimate_yield(best_crop, field),
                    "planting_density": self._calculate_planting_density(best_crop, field["size_acres"])
                }
                allocation["compatibility_score"][field_id] = best_score
        
        return allocation
    
    def _create_crop_rotation_plan(self, allocation: Dict, history: Dict) -> Dict[str, Any]:
        """Create crop rotation plan for sustainable farming"""
        rotation_plan = {
            "rotation_cycles": {},
            "sustainability_score": 0,
            "nutrient_management": {},
            "pest_management": {}
        }
        
        # Define rotation groups
        rotation_groups = {
            "cereals": ["wheat", "maize", "rice"],
            "legumes": ["pulses", "soybeans", "peanuts"],
            "fiber": ["cotton", "jute"],
            "oilseeds": ["sunflower", "mustard"]
        }
        
        # Create 3-year rotation plan
        for field_id, field_data in allocation["field_allocations"].items():
            current_crop = field_data["crop"]
            
            # Determine rotation sequence
            rotation_sequence = self._determine_rotation_sequence(current_crop, rotation_groups, history.get(field_id, []))
            
            rotation_plan["rotation_cycles"][field_id] = {
                "year_1": current_crop,
                "year_2": rotation_sequence[0],
                "year_3": rotation_sequence[1],
                "benefits": self._calculate_rotation_benefits(current_crop, rotation_sequence)
            }
        
        # Calculate overall sustainability score
        rotation_plan["sustainability_score"] = self._calculate_sustainability_score(rotation_plan["rotation_cycles"])
        
        return rotation_plan
    
    def _optimize_layout(self, fields: List[Dict], infrastructure: List[str], water_sources: List[str]) -> Dict[str, Any]:
        """Optimize farm layout for efficiency and accessibility"""
        optimization = {
            "access_roads": [],
            "irrigation_layout": [],
            "storage_locations": [],
            "efficiency_improvements": [],
            "cost_estimates": {}
        }
        
        # Design access roads
        optimization["access_roads"] = self._design_access_roads(fields, infrastructure)
        
        # Design irrigation layout
        if water_sources:
            optimization["irrigation_layout"] = self._design_irrigation_layout(fields, water_sources)
        
        # Recommend storage locations
        optimization["storage_locations"] = self._recommend_storage_locations(fields, infrastructure)
        
        # Suggest efficiency improvements
        optimization["efficiency_improvements"] = [
            "Consolidate small fields for better equipment efficiency",
            "Create buffer zones between fields for pest management",
            "Establish windbreaks for crop protection",
            "Plan for future expansion areas"
        ]
        
        # Estimate costs
        optimization["cost_estimates"] = {
            "road_construction": len(optimization["access_roads"]) * 5000,
            "irrigation_setup": len(optimization["irrigation_layout"]) * 3000,
            "storage_facilities": len(optimization["storage_locations"]) * 10000
        }
        
        return optimization
    
    def _determine_field_shape(self, field_size: float) -> str:
        """Determine optimal field shape based on size"""
        if field_size <= 5:
            return "rectangular"
        elif field_size <= 15:
            return "square"
        else:
            return "rectangular"  # Better for large equipment
    
    def _assign_soil_type(self, soil_types: Dict, field_index: int) -> str:
        """Assign soil type to field"""
        if not soil_types:
            return "loam"  # Default
        
        soil_list = list(soil_types.keys())
        return soil_list[field_index % len(soil_list)]
    
    def _determine_water_access(self, water_sources: List[str], field_index: int, total_fields: int) -> str:
        """Determine water access for field"""
        if not water_sources:
            return "rainfed"
        
        # Distribute water sources across fields
        if field_index < len(water_sources):
            return water_sources[field_index]
        else:
            return "rainfed"
    
    def _estimate_slope(self, field_index: int) -> str:
        """Estimate field slope"""
        slopes = ["flat", "gentle", "moderate", "steep"]
        return slopes[field_index % len(slopes)]
    
    def _assess_drainage(self, field_index: int) -> str:
        """Assess field drainage"""
        drainage_types = ["excellent", "good", "moderate", "poor"]
        return drainage_types[field_index % len(drainage_types)]
    
    def _assess_accessibility(self, field_index: int, total_fields: int) -> str:
        """Assess field accessibility"""
        if field_index == 0:
            return "excellent"  # First field is most accessible
        elif field_index < total_fields // 2:
            return "good"
        else:
            return "moderate"
    
    def _calculate_crop_field_compatibility(self, crop: str, field: Dict, requirements: Dict) -> float:
        """Calculate compatibility score between crop and field"""
        score = 0.0
        
        # Soil compatibility
        if field["soil_type"] in requirements["soil_preference"]:
            score += 0.4
        
        # Water access compatibility
        if requirements["water_needs"] == "high" and field["water_access"] != "rainfed":
            score += 0.3
        elif requirements["water_needs"] == "low":
            score += 0.3
        
        # Field size compatibility
        if field["size_acres"] >= requirements["field_size_min"]:
            score += 0.2
        
        # Drainage compatibility
        if requirements["drainage_needs"] == field["drainage"]:
            score += 0.1
        
        return score
    
    def _estimate_yield(self, crop: str, field: Dict) -> float:
        """Estimate crop yield for field"""
        base_yields = {
            "wheat": 2.5,  # tons per acre
            "maize": 3.0,
            "pulses": 1.2,
            "rice": 2.8,
            "cotton": 0.8
        }
        
        base_yield = base_yields.get(crop, 2.0)
        
        # Adjust for field conditions
        adjustments = {
            "excellent": 1.2,
            "good": 1.0,
            "moderate": 0.8,
            "poor": 0.6
        }
        
        soil_adjustment = adjustments.get(field["soil_type"], 1.0)
        drainage_adjustment = adjustments.get(field["drainage"], 1.0)
        
        return round(base_yield * soil_adjustment * drainage_adjustment * field["size_acres"], 2)
    
    def _calculate_planting_density(self, crop: str, field_size: float) -> Dict[str, Any]:
        """Calculate planting density for crop"""
        densities = {
            "wheat": {"seeds_per_acre": 120000, "row_spacing": "6 inches"},
            "maize": {"seeds_per_acre": 28000, "row_spacing": "30 inches"},
            "pulses": {"seeds_per_acre": 80000, "row_spacing": "12 inches"},
            "rice": {"seeds_per_acre": 100000, "row_spacing": "8 inches"},
            "cotton": {"seeds_per_acre": 40000, "row_spacing": "36 inches"}
        }
        
        crop_density = densities.get(crop, {"seeds_per_acre": 50000, "row_spacing": "12 inches"})
        total_seeds = int(crop_density["seeds_per_acre"] * field_size)
        
        return {
            "seeds_per_acre": crop_density["seeds_per_acre"],
            "row_spacing": crop_density["row_spacing"],
            "total_seeds_needed": total_seeds,
            "field_size_acres": field_size
        }
    
    def _determine_rotation_sequence(self, current_crop: str, rotation_groups: Dict, history: List[str]) -> List[str]:
        """Determine crop rotation sequence"""
        # Find which group current crop belongs to
        current_group = None
        for group_name, crops in rotation_groups.items():
            if current_crop in crops:
                current_group = group_name
                break
        
        # Select crops from different groups for rotation
        rotation_crops = []
        for group_name, crops in rotation_groups.items():
            if group_name != current_group:
                rotation_crops.extend(crops)
        
        # Return 2 crops for 3-year rotation
        return rotation_crops[:2]
    
    def _calculate_rotation_benefits(self, current_crop: str, rotation_crops: List[str]) -> List[str]:
        """Calculate benefits of crop rotation"""
        benefits = []
        
        if "pulses" in rotation_crops:
            benefits.append("Nitrogen fixation for soil health")
        
        if current_crop in ["wheat", "maize"] and any(crop in ["pulses", "soybeans"] for crop in rotation_crops):
            benefits.append("Break pest and disease cycles")
        
        if "rice" in rotation_crops:
            benefits.append("Water management benefits")
        
        benefits.append("Improved soil structure")
        benefits.append("Better nutrient utilization")
        
        return benefits
    
    def _calculate_sustainability_score(self, rotation_cycles: Dict) -> float:
        """Calculate overall sustainability score"""
        total_score = 0
        num_fields = len(rotation_cycles)
        
        for field_data in rotation_cycles.values():
            # Score based on diversity
            crops = [field_data["year_1"], field_data["year_2"], field_data["year_3"]]
            diversity_score = len(set(crops)) / 3  # 1.0 if all different
            
            # Score based on benefits
            benefit_score = len(field_data["benefits"]) / 5  # Normalize to 0-1
            
            total_score += (diversity_score + benefit_score) / 2
        
        return round(total_score / num_fields * 100, 1)  # Return as percentage
    
    def _design_access_roads(self, fields: List[Dict], infrastructure: List[str]) -> List[Dict[str, Any]]:
        """Design access roads for farm"""
        roads = []
        
        # Main access road
        roads.append({
            "road_id": "main_access",
            "type": "primary",
            "width_meters": 6,
            "surface": "gravel",
            "estimated_cost": 15000,
            "serves_fields": [field["field_id"] for field in fields[:3]]
        })
        
        # Secondary roads
        if len(fields) > 3:
            roads.append({
                "road_id": "secondary_access",
                "type": "secondary",
                "width_meters": 4,
                "surface": "dirt",
                "estimated_cost": 8000,
                "serves_fields": [field["field_id"] for field in fields[3:]]
            })
        
        return roads
    
    def _design_irrigation_layout(self, fields: List[Dict], water_sources: List[str]) -> List[Dict[str, Any]]:
        """Design irrigation layout"""
        irrigation_systems = []
        
        for i, field in enumerate(fields):
            if field["water_access"] != "rainfed":
                irrigation_systems.append({
                    "field_id": field["field_id"],
                    "system_type": "drip" if field["size_acres"] < 10 else "sprinkler",
                    "water_source": water_sources[i % len(water_sources)],
                    "coverage_percentage": 100,
                    "estimated_cost": field["size_acres"] * 500
                })
        
        return irrigation_systems
    
    def _recommend_storage_locations(self, fields: List[Dict], infrastructure: List[str]) -> List[Dict[str, Any]]:
        """Recommend storage facility locations"""
        storage_locations = []
        
        # Central storage near main access
        storage_locations.append({
            "location_id": "central_storage",
            "type": "grain_storage",
            "capacity_tons": 100,
            "location": "near_field_1",
            "estimated_cost": 25000
        })
        
        # Equipment storage
        storage_locations.append({
            "location_id": "equipment_shed",
            "type": "equipment_storage",
            "capacity": "medium",
            "location": "near_main_access",
            "estimated_cost": 15000
        })
        
        return storage_locations
    
    def _calculate_efficiency_score(self, field_layout: List[Dict], crop_allocation: Dict) -> float:
        """Calculate overall farm layout efficiency score"""
        # Simple scoring based on field sizes and crop allocation
        total_score = 0
        
        # Field size efficiency (prefer medium-sized fields)
        for field in field_layout:
            if 5 <= field["size_acres"] <= 20:
                total_score += 10
            elif field["size_acres"] < 5:
                total_score += 5
            else:
                total_score += 8
        
        # Crop allocation efficiency
        allocation_score = len(crop_allocation["field_allocations"]) * 5
        total_score += allocation_score
        
        # Normalize to 0-100
        max_possible = len(field_layout) * 10 + len(field_layout) * 5
        return round((total_score / max_possible) * 100, 1)
    
    def _generate_layout_recommendations(self, field_layout: List[Dict], crop_allocation: Dict) -> List[str]:
        """Generate layout improvement recommendations"""
        recommendations = []
        
        # Analyze field sizes
        small_fields = [f for f in field_layout if f["size_acres"] < 5]
        if small_fields:
            recommendations.append(f"Consider consolidating {len(small_fields)} small fields for better efficiency")
        
        # Analyze crop distribution
        allocated_fields = len(crop_allocation["field_allocations"])
        total_fields = len(field_layout)
        if allocated_fields < total_fields:
            recommendations.append(f"Utilize {total_fields - allocated_fields} unallocated fields")
        
        # General recommendations
        recommendations.extend([
            "Maintain buffer zones between fields for pest management",
            "Plan for future expansion areas",
            "Consider windbreaks for crop protection",
            "Optimize irrigation system layout for water efficiency"
        ])
        
        return recommendations
