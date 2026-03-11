"""
Orchestrator LLM Service
Generates summaries across agent outputs.
"""

import os
from typing import Any, Dict, List, Optional
from pathlib import Path

from dotenv import load_dotenv
from farmxpert.app.config import settings
from farmxpert.app.shared.utils import logger

# Gemini - Use new package
try:
    import google.genai as genai
    GENAI_PACKAGE = "new"
except ImportError:
    import google.generativeai as genai
    GENAI_PACKAGE = "old"

# Load project-level .env for backward compatibility
_FILE_PATH = Path(__file__).resolve()
_PROJECT_ROOT = _FILE_PATH.parents[4]
if not (_PROJECT_ROOT / ".env").exists():
    _PROJECT_ROOT = _FILE_PATH.parents[5]
env_path = _PROJECT_ROOT / ".env"
logger.info(f"Loading .env from: {env_path} (exists: {env_path.exists()})")
load_dotenv(env_path)

GEMINI_API_KEY = settings.gemini_api_key or settings.google_api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = settings.openai_api_key or os.getenv("OPENAI_API_KEY")

if GEMINI_API_KEY:
    if not os.getenv("GOOGLE_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY
    # Only configure for old package
    if GENAI_PACKAGE == "old":
        genai.configure(api_key=GEMINI_API_KEY)

try:
    from openai import OpenAI
    if OPENAI_API_KEY:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
    else:
        openai_client = None
except ImportError:
    openai_client = None

SYSTEM_PROMPT = """
You are FarmXpert, a brilliant, empathetic, and highly expert agricultural AI advisor.
You communicate exactly like a top-tier human consultant—natural, conversational, fluid, and incredibly helpful.
You have vast knowledge of agronomy, soil science, crop management, and economics.

CRITICAL INSTRUCTION: 
1. Always use the data provided in 'BEHIND-THE-SCENES AGENT ANALYSIS RESULTS'.
2. If location, soil type, or crop name are provided in the context, DO NOT ask the farmer for them. 
3. Acknowledge these specific details (e.g., "Since your farm in [District] has [Soil Type]...") to show you are paying attention.
4. Your response must be conversational. Never just list data like a robot.
5. Synthesize the findings into actionable, friendly, and step-by-step guidance.
6. If the user says something simple like 'hii', respond warmly as a personal advisor would, perhaps mentioning a quick highlight from the current farm status.
7. Keep responses concise but high-impact. Use a professional yet reassuring tone.
"""


class OrchestratorLLMService:
    """LLM summary generation for orchestrator responses."""

    @staticmethod
    def generate_summary(
        query: Optional[str],
        weather_analysis: Optional[Dict[str, Any]],
        growth_analysis: Optional[Dict[str, Any]],
        irrigation_analysis: Optional[Dict[str, Any]] = None,
        fertilizer_analysis: Optional[Dict[str, Any]] = None,
        soil_health_analysis: Optional[Dict[str, Any]] = None,
        market_intelligence_analysis: Optional[Dict[str, Any]] = None,
        task_scheduler_analysis: Optional[Dict[str, Any]] = None,
        recommendations: Optional[List[str]] = None,
        system_prompt: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> Optional[str]:
        prompt = OrchestratorLLMService._build_prompt(
            query=query,
            weather_analysis=weather_analysis,
            growth_analysis=growth_analysis,
            irrigation_analysis=irrigation_analysis,
            fertilizer_analysis=fertilizer_analysis,
            soil_health_analysis=soil_health_analysis,
            market_intelligence_analysis=market_intelligence_analysis,
            task_scheduler_analysis=task_scheduler_analysis,
            recommendations=recommendations or [],
            chat_history=chat_history or []
        )

        # Try Gemini first as requested
        summary = OrchestratorLLMService._call_gemini(prompt, system_prompt=system_prompt)
        if summary:
            return summary

        # Fallback to OpenAI
        summary = OrchestratorLLMService._call_openai(prompt)
        if summary:
            return summary

        # Generate a basic summary if LLM is unavailable
        logger.warning("Both Gemini and OpenAI summaries unavailable, generating fallback summary")
        return OrchestratorLLMService._generate_fallback_summary(
            query, weather_analysis, growth_analysis, irrigation_analysis,
            fertilizer_analysis, soil_health_analysis, market_intelligence_analysis,
            task_scheduler_analysis, recommendations
        )
    
    @staticmethod
    def _generate_fallback_summary(
        query: Optional[str],
        weather_analysis: Optional[Dict[str, Any]],
        growth_analysis: Optional[Dict[str, Any]],
        irrigation_analysis: Optional[Dict[str, Any]],
        fertilizer_analysis: Optional[Dict[str, Any]],
        soil_health_analysis: Optional[Dict[str, Any]],
        market_intelligence_analysis: Optional[Dict[str, Any]],
        task_scheduler_analysis: Optional[Dict[str, Any]],
        recommendations: Optional[List[str]]
    ) -> str:
        """Generate a fallback summary when LLM is unavailable"""
        summaries = []
        
        # Weather summary
        if weather_analysis and isinstance(weather_analysis, dict):
            weather = weather_analysis.get('weather', {})
            if weather:
                temp = weather.get('temperature', 'N/A')
                condition = weather.get('weather_condition', 'varied')
                humidity = weather.get('humidity', 'N/A')
                summaries.append(f"Current conditions: {temp}°C with {condition} weather and {humidity}% humidity.")
        
        # Growth summary
        if growth_analysis and isinstance(growth_analysis, dict):
            crop_info = growth_analysis.get('crop_info', {})
            if crop_info:
                stage = crop_info.get('growth_stage', 'N/A')
                health = crop_info.get('health_status', 'normal')
                summaries.append(f"Your crop is in the {stage} stage and showing {health} health.")
        
        # Irrigation summary
        if irrigation_analysis and isinstance(irrigation_analysis, dict):
            status = irrigation_analysis.get('status', 'adequate')
            rec = irrigation_analysis.get('recommendation', '')
            if rec:
                summaries.append(f"Irrigation status is {status}. {rec}")
        
        # Fertilizer summary
        if fertilizer_analysis and isinstance(fertilizer_analysis, dict):
            status = fertilizer_analysis.get('status', 'adequate')
            summaries.append(f"Nutrient levels appear {status}.")
        
        # Soil Health summary
        if soil_health_analysis and isinstance(soil_health_analysis, dict):
            score = soil_health_analysis.get('health_score') or soil_health_analysis.get('analysis', {}).get('health_score', 'N/A')
            summaries.append(f"Soil health score is {score}.")

        # Task Scheduler summary
        if task_scheduler_analysis and isinstance(task_scheduler_analysis, dict):
            tasks = task_scheduler_analysis.get('tasks_for_today') or task_scheduler_analysis.get('scheduled_tasks', [])
            if tasks:
                summaries.append(f"You have {len(tasks)} tasks scheduled for today.")
        
        # Market summary
        if market_intelligence_analysis and isinstance(market_intelligence_analysis, dict):
            # Check multiple potential keys
            analysis = market_intelligence_analysis.get('analysis', {}) or market_intelligence_analysis
            market = analysis.get('recommended_market') or analysis.get('best_market')
            price = analysis.get('best_price') or analysis.get('current_price')
            if market:
                summaries.append(f"Best market opportunity: {market} with price around ₹{price}/quintal.")
        
        # Recommendations
        if recommendations:
            summaries.append(f"Key recommendations: {'; '.join(recommendations[:3])}")
        
        # If we have summaries, join them with a friendly intro
        if summaries:
            intro = "Analysis complete! "
            if query and ("hi" in query.lower() or "hello" in query.lower()):
                intro = "Hello! I've analyzed your farm's latest data. "
            return intro + " ".join(summaries)
        
        return "I've processed your request and looked through the agent data, but I couldn't generate a detailed summary at the moment. Please check the individual agent results below for specific insights."

    @staticmethod
    def _build_prompt(
        query: Optional[str],
        weather_analysis: Optional[Dict[str, Any]],
        growth_analysis: Optional[Dict[str, Any]],
        irrigation_analysis: Optional[Dict[str, Any]] = None,
        fertilizer_analysis: Optional[Dict[str, Any]] = None,
        soil_health_analysis: Optional[Dict[str, Any]] = None,
        market_intelligence_analysis: Optional[Dict[str, Any]] = None,
        task_scheduler_analysis: Optional[Dict[str, Any]] = None,
        recommendations: Optional[List[str]] = None,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        # Extract meaningful information from weather analysis
        weather_section = "No weather data available"
        if weather_analysis:
            if isinstance(weather_analysis, dict):
                # Check for weather data in different possible structures
                weather_info = weather_analysis.get('weather', {})
                if weather_info:
                    temp = weather_info.get('temperature', 'N/A')
                    humidity = weather_info.get('humidity', 'N/A')
                    condition = weather_info.get('weather_condition', weather_info.get('description', 'N/A'))
                    weather_section = f"Temperature: {temp}°C, Humidity: {humidity}%, Conditions: {condition}"
                else:
                    # Try nested structure
                    current = weather_analysis.get('current', {})
                    if current:
                        temp = current.get('temperature', 'N/A')
                        humidity = current.get('humidity', 'N/A')
                        desc = current.get('description', 'N/A')
                        weather_section = f"Temperature: {temp}°C, Humidity: {humidity}%, Conditions: {desc}"
                    else:
                        weather_section = "Weather data processed but no current conditions available"
            else:
                weather_section = f"Weather analysis available: {type(weather_analysis).__name__}"

        # Extract meaningful information from growth analysis
        growth_section = "No crop growth data available"
        if growth_analysis:
            if isinstance(growth_analysis, dict):
                crop_info = growth_analysis.get('crop_info', {})
                if crop_info:
                    crop_name = crop_info.get('crop_name', 'Unknown')
                    stage = crop_info.get('growth_stage', 'Unknown')
                    health = crop_info.get('health_status', 'Unknown')
                    growth_section = f"Crop: {crop_name}, Stage: {stage}, Health: {health}"
                else:
                    growth_section = "Growth analysis processed but no crop details available"
            else:
                growth_section = f"Growth analysis available: {type(growth_analysis).__name__}"

        # Extract meaningful information from irrigation analysis
        irrigation_section = "No irrigation data available"
        if irrigation_analysis and isinstance(irrigation_analysis, dict):
            status = irrigation_analysis.get('status', 'Unknown')
            rec = irrigation_analysis.get('recommendation')
            if rec:
                irrigation_section = f"Irrigation Status: {status}, Recommendation: {rec}"
            else:
                irrigation_section = f"Irrigation Status: {status}"
        elif irrigation_analysis:
            irrigation_section = f"Irrigation analysis available: {type(irrigation_analysis).__name__}"

        # Extract meaningful information from fertilizer analysis
        fertilizer_section = "No fertilizer data available"
        if fertilizer_analysis:
            if isinstance(fertilizer_analysis, dict):
                status = fertilizer_analysis.get('status', 'Unknown')
                recommendations = fertilizer_analysis.get('recommendations', [])
                if recommendations:
                    rec_count = len(recommendations)
                    fertilizer_section = f"Fertilizer Status: {status}, {rec_count} recommendations available"
                else:
                    fertilizer_section = f"Fertilizer Status: {status}"
            elif hasattr(fertilizer_analysis, 'status'):
                status = fertilizer_analysis.status
                if hasattr(fertilizer_analysis, 'recommendations') and fertilizer_analysis.recommendations:
                    rec_count = len(fertilizer_analysis.recommendations)
                    fertilizer_section = f"Fertilizer Status: {status}, {rec_count} recommendations available"
                else:
                    fertilizer_section = f"Fertilizer Status: {status}"
            else:
                fertilizer_section = f"Fertilizer analysis available: {type(fertilizer_analysis).__name__}"

        # Extract meaningful information from soil health analysis
        soil_health_section = "No soil health data available"
        if soil_health_analysis:
            if isinstance(soil_health_analysis, dict):
                health_score = soil_health_analysis.get('health_score', 'N/A')
                red_alert = soil_health_analysis.get('red_alert', False)
                issues_count = len(soil_health_analysis.get('issues_detected', []))
                rec_count = len(soil_health_analysis.get('recommendations', {}).get('chemical', [])) + len(soil_health_analysis.get('recommendations', {}).get('organic', []))
                soil_health_section = f"Soil Health Score: {health_score}, Red Alert: {red_alert}, Issues: {issues_count}, Recommendations: {rec_count}"
            else:
                soil_health_section = f"Soil health analysis available: {type(soil_health_analysis).__name__}"

        market_intelligence_section = "No market intelligence data available"
        if market_intelligence_analysis:
            if isinstance(market_intelligence_analysis, dict):
                # Check for direct market data
                if market_intelligence_analysis.get('recommended_market'):
                    best_market = market_intelligence_analysis.get('recommended_market', 'N/A')
                    best_price = market_intelligence_analysis.get('best_price', 'N/A')
                    confidence = market_intelligence_analysis.get('confidence', 'N/A')
                    revenue = market_intelligence_analysis.get('estimated_revenue', 'N/A')
                    market_intelligence_section = f"Best Market: {best_market}, Best Price: Rs. {best_price}/quintal, Confidence: {confidence}, Projected Revenue: Rs. {revenue}"
                else:
                    # Try nested structure
                    analysis = market_intelligence_analysis.get('analysis', {})
                    if analysis:
                        best_market = analysis.get('recommended_market', 'N/A')
                        best_price = analysis.get('best_price', 'N/A')
                        confidence = analysis.get('confidence', 'N/A')
                        revenue = analysis.get('estimated_revenue_best', 'N/A')
                        market_intelligence_section = f"Best Market: {best_market}, Best Price: Rs. {best_price}/quintal, Confidence: {confidence}, Projected Revenue: Rs. {revenue}"
                    else:
                        market_intelligence_section = f"Market intelligence analysis available: {type(market_intelligence_analysis).__name__}"
            else:
                market_intelligence_section = f"Market intelligence data available: {type(market_intelligence_analysis).__name__}"

        task_scheduler_section = "No task scheduling data available"
        if task_scheduler_analysis:
            if isinstance(task_scheduler_analysis, dict):
                tasks = task_scheduler_analysis.get('tasks_for_today', [])
                if tasks:
                    task_count = len(tasks)
                    high_priority_count = len([t for t in tasks if t.get('priority') == 'High'])
                    task_scheduler_section = f"Tasks: {task_count} total, {high_priority_count} high priority"
                    # Add task details
                    task_details = []
                    for task in tasks[:3]:  # Show first 3 tasks
                        task_name = task.get('task', 'Unknown')
                        priority = task.get('priority', 'N/A')
                        task_details.append(f"{task_name} ({priority})")
                    if task_details:
                        task_scheduler_section += f" - {', '.join(task_details)}"
                else:
                    task_scheduler_section = f"Task scheduling analysis available: {type(task_scheduler_analysis).__name__}"
            else:
                task_scheduler_section = f"Task scheduling data available: {type(task_scheduler_analysis).__name__}"

        rec_text = "\n".join(f"- {r}" for r in (recommendations or [])) if recommendations else "None"
        
        # Build conversational memory block
        history_text = "No previous conversation."
        if chat_history:
            history_lines = []
            for msg in chat_history:
                role = "Farmer" if msg.get("role") == "user" else "FarmXpert"
                content = msg.get("content", "").replace("\n", " ")
                history_lines.append(f"{role}: {content}")
            history_text = "\n".join(history_lines)

        return (
            f"--- RECENT CONVERSATION HISTORY ---\n"
            f"{history_text}\n"
            f"-----------------------------------\n\n"
            f"Farmer's Latest Query: {query or 'N/A'}\n\n"
            f"--- BEHIND-THE-SCENES AGENT ANALYSIS RESULTS ---\n"
            f"Weather: {weather_section}\n"
            f"Crop Growth: {growth_section}\n"
            f"Irrigation: {irrigation_section}\n"
            f"Fertilizer: {fertilizer_section}\n"
            f"Soil Health: {soil_health_section}\n"
            f"Market Intelligence: {market_intelligence_section}\n"
            f"Task Schedule: {task_scheduler_section}\n"
            f"Recommendations:\n{rec_text}\n"
            f"------------------------------------------------\n\n"
            "INSTRUCTIONS:\n"
            "You just received a new query from the farmer. Review the RECENT CONVERSATION HISTORY to maintain context and flow.\n"
            "Do NOT just dump the BEHIND-THE-SCENES AGENT ANALYSIS RESULTS to the user. Instead, read them, synthesize them, and craft a brilliantly helpful, natural, and conversational response.\n"
            "If the user is asking a follow-up question (e.g. 'what about xyz?'), make sure your answer flows naturally from your previous response in the history.\n"
            "Sound like a genuine, hyper-intelligent farm advisor. Keep it engaging, authoritative, but incredibly accessible."
        )

    @staticmethod
    def _call_gemini(prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """Call Gemini API for LLM summary generation"""
        try:
            if not GEMINI_API_KEY:
                logger.error("Gemini API key not configured. Check your .env file.")
                return None

            # Use Gemini 2.5 Flash as it has available quota and is state-of-the-art
            model_name = "models/gemini-2.5-flash"
            effective_system_prompt = system_prompt or SYSTEM_PROMPT
            
            if GENAI_PACKAGE == "new":
                # New package API
                client = genai.Client(api_key=GEMINI_API_KEY)
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config={
                        "system_instruction": effective_system_prompt
                    }
                )
                if response and hasattr(response, 'text'):
                    return response.text.strip()
            else:
                # Old package API
                try:
                    model = genai.GenerativeModel(
                        model_name=model_name,
                        system_instruction=effective_system_prompt
                    )
                except TypeError:
                    # Fallback for older google-generativeai versions
                    model = genai.GenerativeModel(model_name=model_name)
                    prompt = f"SYSTEM INSTRUCTIONS:\n{effective_system_prompt}\n\nUSER PROMPT:\n{prompt}"
                    
                response = model.generate_content(prompt)
                if getattr(response, "text", None):
                    return response.text.strip()
            return None

        except Exception as e:
            error_str = str(e).lower()
            if "quota" in error_str or "rate limit" in error_str:
                logger.warning(f"Gemini API quota exceeded: {e}")
            elif "api key" in error_str:
                logger.error(f"Gemini API key error: {e}")
            else:
                logger.error(f"Gemini API call failed: {e}")
            return None

    @staticmethod
    def _call_openai(prompt: str) -> Optional[str]:
        try:
            if not openai_client:
                return None
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI summary error: {str(e)}")
            return None
