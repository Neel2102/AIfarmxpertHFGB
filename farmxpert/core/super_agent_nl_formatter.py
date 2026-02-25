"""
Natural Language Formatter for SuperAgent Responses
Converts structured JSON responses into clean, conversational natural language
"""

from typing import Dict, Any, List


def format_response_as_natural_language(
    query: str,
    response_data: Dict[str, Any],
    agent_names: List[str],
    context: Dict[str, Any] = None
) -> str:
    """
    Convert structured response into natural, conversational language
    
    Args:
        query: Original user query
        response_data: Structured response from agents
        agent_names: List of agents that contributed
        context: Optional context (locale, conversational mode, etc.)
        
    Returns:
        Clean natural language response string that feels like expert guidance
    """
    # Check if conversational mode is enabled (default to True for better UX)
    conversational = context.get("conversational", True) if context else True
    
    # Extract key components
    answer = response_data.get("answer") or response_data.get("response") or ""
    recommendations = response_data.get("recommendations", [])
    warnings = response_data.get("warnings", [])
    next_steps = response_data.get("next_steps", [])
    
    # Build natural language response
    parts = []
    
    # Main answer - this should be the detailed response
    if answer:
        parts.append(answer)
    
    # Recommendations - format as helpful tips
    if recommendations:
        if conversational:
            parts.append("\n\n🌱 **Here's what I recommend:**")
        else:
            parts.append("\n\n**Recommendations:**")
        for i, rec in enumerate(recommendations, 1):
            # Clean up recommendation text
            rec_text = str(rec).strip()
            if rec_text:
                parts.append(f"\n• {rec_text}")
    
    # Warnings - format as important alerts
    if warnings:
        if conversational:
            parts.append("\n\n⚠️ **Important to keep in mind:**")
        else:
            parts.append("\n\n**Important Warnings:**")
        for warning in warnings:
            warning_text = str(warning).strip()
            if warning_text:
                parts.append(f"\n⚠️ {warning_text}")
    
    # Next steps - format as actionable guidance
    if next_steps:
        if conversational:
            parts.append("\n\n📋 **Your action plan:**")
        else:
            parts.append("\n\n**Next Steps:**")
        for i, step in enumerate(next_steps, 1):
            step_text = str(step).strip()
            if step_text:
                parts.append(f"\n{i}. {step_text}")
    
    
    # Fallback if no content
    if not parts:
        return ("I'd be happy to help you with your farming questions! To give you the best advice, "
                "could you share some details about:\n\n"
                "• What crop you're growing\n"
                "• Your location or region\n"
                "• Any specific concerns or challenges you're facing\n\n"
                "With this information, I can provide personalized recommendations for your farm.")
    
    return "".join(parts)


import re

def create_simple_greeting_response(query: str) -> str:
    """Handle simple greetings intelligently"""
    q_lower = query.lower().strip()
    
    # Greetings (hi, hello, etc.)
    greeting_pattern = r"^(hi+|hello|hey|hola|namaste|namaskar|good\s*(morning|afternoon|evening)|greetings).{0,20}$"
    if re.match(greeting_pattern, q_lower):
        return ("Hello! I'm FarmXpert, your AI farming assistant. "
                "I can help you with crop selection, pest management, irrigation planning, "
                "weather forecasts, and much more. What would you like to know about your farm today?")
    
    # How are you
    if any(phrase in q_lower for phrase in ["how are you", "how r u", "what's up", "whats up"]):
        return ("I'm doing great, thank you for asking! I'm here and ready to help you with "
                "all your farming needs. What can I assist you with today?")
    
    # Thank you
    if any(phrase in q_lower for phrase in ["thank you", "thanks", "thank u", "dhanyavaad"]):
        return ("You're very welcome! I'm always here to help. Feel free to ask me anything "
                "about farming, crops, weather, or agricultural best practices anytime!")
    
    # Goodbye
    if any(phrase in q_lower for phrase in ["bye", "goodbye", "see you", "good night"]):
        return ("Goodbye! Wishing you a bountiful harvest. Come back anytime you need farming advice. "
                "Happy farming! 🌾")
    
    # Fallback for safety
    return ("Hello! I'm FarmXpert. How can I help you with your farming activities today?")


def is_simple_query(query: str) -> bool:
    """Check if query is a simple greeting/small talk"""
    q_lower = query.lower().strip()
    
    # Greeting pattern
    greeting_pattern = r"^(hi+|hello|hey|hola|namaste|namaskar|good\s*(morning|afternoon|evening)|greetings).{0,20}$"
    if re.match(greeting_pattern, q_lower):
        return True
        
    simple_patterns = [
        "how are you", "how r u", "what's up", "whats up",
        "thank you", "thanks", "thank u", "dhanyavaad",
        "bye", "goodbye", "see you", "good night"
    ]
    # Use word boundary check or exact constraints for others
    # For simplicity in this helper, strict substring is okay for phrases, but 'hi' was the dangerous one.
    return any(pattern in q_lower for pattern in simple_patterns)
