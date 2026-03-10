from __future__ import annotations
from typing import List, Dict, Any
import google.generativeai as genai
from farmxpert.config.settings import settings


class GeminiService:
    def __init__(self) -> None:
        api_key = settings.gemini_api_key
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    async def chat(self, messages: List[Dict[str, str]], model: str = "gemini-pro") -> str:
        try:
            # Convert messages to a single prompt
            prompt = ""
            for message in messages:
                role = message.get("role", "user")
                content = message.get("content", "")
                if role == "system":
                    prompt += f"System: {content}\n"
                elif role == "user":
                    prompt += f"User: {content}\n"
                elif role == "assistant":
                    prompt += f"Assistant: {content}\n"
            
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def generate_response(self, prompt: str, context: Dict[str, Any]) -> str:
        try:
            # Create a comprehensive prompt with context
            full_prompt = f"""
            Context: {context}
            
            Question/Task: {prompt}
            
            Please provide a detailed, actionable response based on the context provided.
            """
            
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            return f"Error generating response: {str(e)}"


# Keep the old class name for compatibility
OpenAIService = GeminiService


