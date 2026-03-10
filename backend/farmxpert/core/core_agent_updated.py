"""
Updated Core Agent Router - Now uses centralized tools and database
Simplified imports and cleaner function calls
"""

import json
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

import litellm
from farmxpert.config.settings import settings
from farmxpert.models.farm_models import Farm, AgentInteraction
from farmxpert.tools import (
    get_weather_forecast, get_market_prices, get_mandi_prices,
    analyze_soil_data, get_crop_recommendations, get_fertilizer_recommendations,
    get_irrigation_schedule, diagnose_pest_disease, get_government_schemes,
    web_search, parse_location_string, format_currency, calculate_profit_margin
)
from farmxpert.database import (
    get_database_session, create_user, authenticate_user, create_farm,
    create_crop, save_soil_test, create_task, save_yield_record,
    save_chat_message, get_user_farms, get_farm_crops, get_farm_summary
)
from farmxpert.core.utils.logger import get_logger

# Get the project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]

class CoreAgent:
    """
    Single intelligent agent that routes requests and adapts personality based on role.
    Now uses centralized tools.py and database.py for all operations.
    """
    
    def __init__(self):
        self.logger = get_logger("core_agent")
        self.prompts = self._load_agent_prompts()

    def _is_transient_llm_error(self, exc: Exception) -> bool:
        msg = str(exc) or ""
        m = msg.lower()
        return (
            "unavailable" in m
            or "high demand" in m
            or "503" in m
            or "service unavailable" in m
            or "deadline exceeded" in m
            or "timeout" in m
        )
        
    def _load_agent_prompts(self) -> Dict[str, Any]:
        """Load agent prompts from JSON configuration file"""
        prompts_file = Path(__file__).resolve().parent / "agent_prompts.json"
        
        try:
            with open(prompts_file, 'r', encoding='utf-8') as f:
                prompts_data = json.load(f)
                return prompts_data.get("agents", {})
        except FileNotFoundError:
            self.logger.error(f"Agent prompts file not found: {prompts_file}")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing agent prompts: {e}")
            return {}
    
    def get_available_agents(self) -> List[str]:
        """Get list of available agent roles"""
        return list(self.prompts.keys())
    
    def get_agent_info(self, agent_role: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific agent role"""
        return self.prompts.get(agent_role)
    
    async def process_request(
        self, 
        user_input: str, 
        agent_role: str, 
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Main method to process user requests with specified agent role
        
        Args:
            user_input: The user's query or request
            agent_role: The role/personality to adopt (e.g., "soil_health", "crop_selector")
            context: Additional context information
            session_id: Session identifier for tracking
            user_id: User ID for database operations
            
        Returns:
            Agent response with recommendations, insights, and data
        """
        start_time = datetime.now()
        
        try:
            # Validate agent role
            if agent_role not in self.prompts:
                return self._create_error_response(
                    f"Unknown agent role: {agent_role}. Available roles: {', '.join(self.get_available_agents())}",
                    start_time
                )
            
            agent_config = self.prompts[agent_role]
            
            # Gather tool data based on agent's required tools
            tool_data = await self._gather_tool_data(
                agent_config.get("tools", []),
                user_input,
                context,
                user_id
            )
            
            # Save chat message if session and user provided
            if session_id and user_id:
                try:
                    db = get_database_session()
                    save_chat_message(db, session_id, "user", user_input)
                except Exception as e:
                    self.logger.warning(f"Failed to save user message: {e}")
            
            # 🎯 CONTEXT INJECTOR: Fetch farm data and inject into user input
            farm_context = await self._inject_farm_context(user_id, context)
            
            # Prepend farm context to user input
            enhanced_user_input = f"{farm_context}\n\nUser Query: {user_input}" if farm_context else user_input
            
            # Construct the enhanced prompt
            enhanced_prompt = self._construct_prompt(
                agent_config,
                enhanced_user_input,
                tool_data,
                context
            )
            
            # Call LLM using LiteLLM
            self.logger.info(f"Processing request with agent role: {agent_role}")
            
            # Set up LiteLLM with Gemini model
            model_name = f"gemini/{settings.gemini_model}"

            max_attempts = 3
            last_error: Exception | None = None
            response = None

            for attempt in range(max_attempts):
                try:
                    response = await litellm.acompletion(
                        model=model_name,
                        messages=[{"role": "user", "content": enhanced_prompt}],
                        temperature=settings.gemini_temperature,
                        max_tokens=settings.gemini_max_output_tokens,
                        timeout=settings.gemini_request_timeout,
                    )
                    last_error = None
                    break
                except Exception as e:
                    last_error = e
                    if self._is_transient_llm_error(e) and attempt < max_attempts - 1:
                        delay = 0.6 * (2 ** attempt)
                        self.logger.warning(f"LiteLLM transient error (attempt {attempt + 1}/{max_attempts}): {e}; retrying in {delay:.1f}s")
                        await asyncio.sleep(delay)
                        continue
                    self.logger.error(f"LiteLLM call failed: {e}")
                    break

            if response is None:
                if last_error and self._is_transient_llm_error(last_error):
                    return self._create_error_response(
                        "The AI model is currently busy (high demand). Please try again in a few seconds.",
                        start_time,
                    )
                return self._create_error_response("I couldn't generate a response right now. Please try again.", start_time)

            llm_response = response.choices[0].message.content
            usage_metadata = response.usage
            
            if user_id:
                try:
                    db = get_database_session()
                    farm = db.query(Farm).filter(Farm.user_id == user_id).first()
                    if farm:
                        tokens_used = int(getattr(usage_metadata, "total_tokens", 0) or 0)
                        interaction = AgentInteraction(
                            farm_id=farm.id,
                            agent_name=agent_role,
                            query=user_input,
                            response=llm_response,
                            context_data=context,
                            response_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                            tokens_used=tokens_used,
                            success=True,
                        )
                        db.add(interaction)
                        db.commit()
                except Exception as e:
                    self.logger.warning(f"Failed to save AgentInteraction: {e}")
                    try:
                        db.rollback()
                    except Exception:
                        pass
            
            # Save assistant response if session and user provided
            if session_id and user_id:
                try:
                    db = get_database_session()
                    save_chat_message(db, session_id, "assistant", llm_response)
                except Exception as e:
                    self.logger.warning(f"Failed to save assistant message: {e}")
            
            # Parse and structure the response
            structured_response = self._parse_llm_response(
                llm_response,
                agent_role,
                tool_data,
                start_time,
                usage_metadata
            )
            
            self.logger.info(f"Successfully processed request with {agent_role} agent")
            return structured_response
            
        except Exception as e:
            self.logger.error(f"Error processing request with {agent_role} agent: {e}", exc_info=True)
            return self._create_error_response(str(e), start_time)
    
    async def _gather_tool_data(
        self, 
        required_tools: List[str], 
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Gather data from centralized tools based on agent requirements"""
        tool_data = {}
        context = context or {}
        
        # Extract common parameters from context
        location = context.get("location") or context.get("farm_location") or "Unknown"
        crop = context.get("crop") or context.get("crop_name")
        season = context.get("season") or "Kharif"
        
        # Parse location to get coordinates
        parsed_location = parse_location_string(location)
        
        for tool_name in required_tools:
            try:
                if tool_name == "weather":
                    data = await get_weather_forecast(location, days=7)
                    
                elif tool_name == "market":
                    commodity = crop or "wheat"
                    data = await get_market_prices(commodity, location)
                    
                elif tool_name == "soil":
                    soil_data = context.get("soil_data") or context.get("soil") or {}
                    data = await analyze_soil_data(soil_data, location)
                    
                elif tool_name == "crop":
                    soil_type = context.get("soil_type", "general")
                    land_size = context.get("land_size_acres", 1.0)
                    data = await get_crop_recommendations(location, season, soil_type, land_size)
                    
                elif tool_name == "fertilizer":
                    soil_data = context.get("soil_data") or {}
                    data = await get_fertilizer_recommendations(crop or "wheat", soil_data, location)
                    
                elif tool_name == "irrigation":
                    soil_type = context.get("soil_type", "medium")
                    data = await get_irrigation_schedule(crop or "wheat", location, season, soil_type)
                    
                elif tool_name == "pest_disease":
                    symptoms = context.get("symptoms", user_input)
                    data = await diagnose_pest_disease(symptoms, crop or "unknown", location)
                    
                elif tool_name == "web_scraping":
                    # Use web search for information gathering
                    data = await web_search(user_input, num_results=3)
                    
                elif tool_name == "market_intelligence":
                    # Get mandi prices for detailed market analysis
                    state = parsed_location.get("state", "Unknown")
                    data = await get_mandi_prices(state, crop)
                    
                else:
                    # For tools not yet implemented, provide placeholder
                    data = {"status": f"Tool '{tool_name}' not yet implemented"}
                
                tool_data[tool_name] = data
                self.logger.debug(f"Gathered data from {tool_name} tool")
                
            except Exception as e:
                self.logger.warning(f"Error gathering data from {tool_name} tool: {e}")
                tool_data[tool_name] = {"error": str(e)}
        
        return tool_data
    
    def _construct_prompt(
        self, 
        agent_config: Dict[str, Any], 
        user_input: str,
        tool_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Construct the enhanced prompt for Gemini"""
        
        # Base system prompt
        system_prompt = agent_config.get("system_prompt", "")
        
        # Add examples if available
        examples = agent_config.get("examples", [])
        examples_text = ""
        if examples:
            examples_text = "\n\nExamples of good responses:\n"
            for i, example in enumerate(examples, 1):
                examples_text += f"\nExample {i}:\nInput: {example.get('input', '')}\nOutput: {example.get('output', '')}\n"
        
        # Add tool data
        tool_data_text = ""
        if tool_data:
            tool_data_text = "\n\nAvailable Tool Data:\n"
            for tool_name, data in tool_data.items():
                if isinstance(data, dict) and not data.get("error"):
                    tool_data_text += f"- {tool_name}: {json.dumps(data, indent=2)}\n"
        
        # Add context
        context_text = ""
        if context:
            context_text = f"\n\nAdditional Context: {json.dumps(context, indent=2)}"
        
        # Construct final prompt
        final_prompt = f"""{system_prompt}{examples_text}

Current User Query: {user_input}{tool_data_text}{context_text}

Please provide a comprehensive response following these guidelines:
1. Be specific and actionable
2. Use the available tool data to inform your response
3. Provide clear recommendations
4. Include any relevant warnings or considerations
5. Suggest next steps when appropriate

Format your response as a helpful, expert advisor."""
        
        return final_prompt
    
    def _parse_llm_response(
        self, 
        llm_response: str, 
        agent_role: str,
        tool_data: Dict[str, Any],
        start_time: datetime,
        usage_metadata: Any = None
    ) -> Dict[str, Any]:
        """Parse and structure the LLM response with token metrics"""
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Extract token usage from LiteLLM response
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        
        if usage_metadata:
            prompt_tokens = getattr(usage_metadata, 'prompt_tokens', 0)
            completion_tokens = getattr(usage_metadata, 'completion_tokens', 0)
            total_tokens = getattr(usage_metadata, 'total_tokens', 0)
        
        # Extract recommendations, warnings, and next steps from response
        response_lines = llm_response.split('\n')
        recommendations = []
        warnings = []
        next_steps = []
        
        current_section = None
        for line in response_lines:
            line = line.strip()
            if line.lower().startswith('recommendation'):
                current_section = 'recommendations'
            elif line.lower().startswith('warning'):
                current_section = 'warnings'
            elif line.lower().startswith('next step'):
                current_section = 'next_steps'
            elif line and current_section and not line.lower().startswith(('recommendation', 'warning', 'next')):
                if current_section == 'recommendations':
                    recommendations.append(line)
                elif current_section == 'warnings':
                    warnings.append(line)
                elif current_section == 'next_steps':
                    next_steps.append(line)
        
        # If no structured sections found, treat the whole response as the main response
        if not recommendations and not warnings and not next_steps:
            main_response = llm_response
        else:
            main_response = llm_response
        
        return {
            "agent": agent_role,
            "success": True,
            "response": main_response,
            "recommendations": recommendations[:5],  # Limit to 5 recommendations
            "warnings": warnings[:3],  # Limit to 3 warnings
            "next_steps": next_steps[:5],  # Limit to 5 next steps
            "data": {
                "tool_data": tool_data,
                "agent_config": {
                    "name": self.prompts[agent_role].get("name"),
                    "description": self.prompts[agent_role].get("description"),
                    "category": self.prompts[agent_role].get("category")
                }
            },
            "metadata": {
                "execution_time": execution_time,
                "tools_used": list(tool_data.keys()),
                "timestamp": datetime.utcnow().isoformat()
            },
            "metrics": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            }
        }
    
    async def _inject_farm_context(self, user_id: Optional[int], context: Optional[Dict[str, Any]]) -> str:
        """
        🎯 CONTEXT INJECTOR: Fetch farm data from database and format as context string
        
        Args:
            user_id: User ID to fetch farm data for (defaults to 1 for testing)
            context: Additional context from the request
            
        Returns:
            Formatted context string to prepend to user input
        """
        try:
            # Default to user_id = 1 for testing as requested
            target_user_id = user_id or 1
            
            self.logger.info(f"Injecting farm context for user_id: {target_user_id}")
            
            # Get database session
            db = get_database_session()
            
            # Fetch user's farms
            farms = get_user_farms(db, target_user_id)
            
            if not farms:
                self.logger.info(f"No farms found for user {target_user_id}")
                return "System Note: No farm data found for this user."
            
            # Build context string from farm data
            farm_context_parts = []
            
            for farm in farms:
                farm_info = []
                
                # Basic farm info (using ORM attributes)
                if farm.farm_name:
                    farm_info.append(f"Farm Name: {farm.farm_name}")
                
                # Build location from components
                location_parts = []
                if farm.village:
                    location_parts.append(farm.village)
                if farm.district:
                    location_parts.append(farm.district)
                if farm.state:
                    location_parts.append(farm.state)
                
                if location_parts:
                    farm_info.append(f"Location: {', '.join(location_parts)}")
                
                if farm.soil_type:
                    farm_info.append(f"Soil Type: {farm.soil_type}")
                
                if farm.crop_type:
                    farm_info.append(f"Current Crop: {farm.crop_type}")
                
                # Get crops for this farm
                try:
                    crops = get_farm_crops(db, farm.id)
                    if crops:
                        crop_list = []
                        for crop in crops:
                            crop_info = crop.crop_type
                            if crop.variety:
                                crop_info += f" ({crop.variety})"
                            if crop.status:
                                crop_info += f" - {crop.status}"
                            crop_list.append(crop_info)
                        
                        if crop_list:
                            farm_info.append(f"Crops: {', '.join(crop_list)}")
                except Exception as e:
                    self.logger.warning(f"Failed to fetch crops for farm {farm.id}: {e}")
                
                # Get farm summary
                try:
                    summary = get_farm_summary(db, farm.id)
                    if summary:
                        if summary.get('total_crops'):
                            farm_info.append(f"Total Crops: {summary['total_crops']}")
                        if summary.get('active_tasks'):
                            farm_info.append(f"Active Tasks: {summary['active_tasks']}")
                except Exception as e:
                    self.logger.warning(f"Failed to fetch farm summary for farm {farm.id}: {e}")
                
                if farm_info:
                    farm_context_parts.append(" | ".join(farm_info))
            
            # Combine all farm information
            if farm_context_parts:
                context_string = f"System Note: User Farm Context - {'; '.join(farm_context_parts)}"
                self.logger.info(f"Farm context injected: {context_string[:100]}...")
                return context_string
            else:
                return "System Note: User has farm records but detailed information is not available."
                
        except Exception as e:
            self.logger.error(f"Error injecting farm context: {e}")
            return "System Note: Unable to retrieve farm context at this time."

    def _create_error_response(self, error_message: str, start_time: datetime) -> Dict[str, Any]:
        """Create a standardized error response"""
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "agent": "core_agent",
            "success": False,
            "response": f"I apologize, but I encountered an error: {error_message}",
            "recommendations": ["Please try rephrasing your query", "Check if the agent role is correct"],
            "warnings": ["Service temporarily unavailable"],
            "next_steps": ["Try again in a few moments", "Contact support if issue persists"],
            "data": {},
            "metadata": {
                "execution_time": execution_time,
                "error": error_message,
                "timestamp": datetime.utcnow().isoformat()
            }
        }

# ============================================================================
# DATABASE INTEGRATION METHODS
# ============================================================================

async def create_user_farm(
    username: str,
    email: str,
    password: str,
    full_name: str,
    farm_name: str,
    farm_location: str,
    farm_size: float
) -> Dict[str, Any]:
    """
    Create a new user and their first farm
    
    Args:
        username: User's username
        email: User's email
        password: User's password
        full_name: User's full name
        farm_name: Farm name
        farm_location: Farm location
        farm_size: Farm size in acres
        
    Returns:
        Success status and created data
    """
    try:
        db = get_database_session()
        
        # Create user
        user = create_user(db, username, email, password, full_name)
        if not user:
            return {"success": False, "error": "Failed to create user"}
        
        # Create farm
        farm = create_farm(
            db, user.id, farm_name, farm_location, farm_size,
            farmer_name=full_name
        )
        if not farm:
            return {"success": False, "error": "Failed to create farm"}
        
        return {
            "success": True,
            "user_id": user.id,
            "farm_id": farm.id,
            "message": "User and farm created successfully"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

async def save_farm_data(
    user_id: int,
    farm_id: int,
    data_type: str,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Save various types of farm data
    
    Args:
        user_id: User ID
        farm_id: Farm ID
        data_type: Type of data (soil_test, crop, task, yield)
        data: Data to save
        
    Returns:
        Success status and saved data
    """
    try:
        db = get_database_session()
        
        if data_type == "soil_test":
            result = save_soil_test(db, farm_id, data)
            
        elif data_type == "crop":
            result = create_crop(
                db, farm_id, data.get("crop_name"),
                data.get("variety"), data.get("sowing_date"),
                data.get("expected_harvest_date"), data.get("area_acres"),
                data.get("status", "planned")
            )
            
        elif data_type == "task":
            result = create_task(
                db, farm_id, data.get("title"), data.get("description"),
                data.get("task_type", "general"), data.get("priority", "medium"),
                data.get("due_date"), data.get("status", "pending")
            )
            
        elif data_type == "yield":
            result = save_yield_record(
                db, data.get("crop_id"), data.get("actual_yield"),
                data.get("yield_unit", "quintals"), data.get("harvest_date"),
                data.get("quality_grade"), data.get("market_price")
            )
            
        else:
            return {"success": False, "error": f"Unknown data type: {data_type}"}
        
        if result:
            return {
                "success": True,
                "data_id": result.id,
                "message": f"{data_type} saved successfully"
            }
        else:
            return {"success": False, "error": f"Failed to save {data_type}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

async def get_user_dashboard(user_id: int) -> Dict[str, Any]:
    """
    Get user's dashboard data
    
    Args:
        user_id: User ID
        
    Returns:
        Dashboard data with farms, crops, tasks, etc.
    """
    try:
        db = get_database_session()
        
        # Import the function from database module
        from farmxpert.database import get_user_dashboard_data
        
        dashboard_data = get_user_dashboard_data(db, user_id)
        
        return {
            "success": True,
            "data": dashboard_data
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# Global instance for easy access
core_agent = CoreAgent()

async def process_farm_request(
    user_input: str, 
    agent_role: str, 
    context: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    user_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Convenience function for processing farm requests
    
    Args:
        user_input: The user's query
        agent_role: The role to process the request
        context: Additional context
        session_id: Session identifier
        user_id: User ID for database operations
        
    Returns:
        Structured response from the agent
    """
    return await core_agent.process_request(user_input, agent_role, context, session_id, user_id)

# Example usage and testing
if __name__ == "__main__":
    async def test_core_agent():
        """Test the core agent with different roles"""
        
        # Test soil health agent
        response = await process_farm_request(
            "My soil pH is 5.8, what should I do?",
            "soil_health",
            {"location": "Punjab", "crop": "wheat"}
        )
        print("Soil Health Response:", response["response"])
        
        # Test crop selector agent
        response = await process_farm_request(
            "What crops should I plant this season?",
            "crop_selector",
            {"season": "Kharif", "location": "Maharashtra"}
        )
        print("Crop Selector Response:", response["response"])
        
        # Test market intelligence agent
        response = await process_farm_request(
            "What are wheat prices now?",
            "market_intelligence",
            {"location": "Delhi"}
        )
        print("Market Intelligence Response:", response["response"])
    
    # Run test
    asyncio.run(test_core_agent())
