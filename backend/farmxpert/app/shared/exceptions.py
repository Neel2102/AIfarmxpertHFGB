"""
Custom Exceptions for FarmXpert Platform
Common exception classes used across all agents
"""

from typing import Optional, Dict, Any


class FarmXpertException(Exception):
    """Base exception for all FarmXpert errors"""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class AgentException(FarmXpertException):
    """Exception raised by agent operations"""
    pass


class WeatherServiceException(AgentException):
    """Exception raised by weather service operations"""
    
    def __init__(self, message: str, service_name: Optional[str] = None):
        super().__init__(message, "WEATHER_SERVICE_ERROR")
        self.service_name = service_name
        if service_name:
            self.details["service"] = service_name


class GrowthAnalysisException(AgentException):
    """Exception raised by growth analysis operations"""
    
    def __init__(self, message: str, crop_type: Optional[str] = None):
        super().__init__(message, "GROWTH_ANALYSIS_ERROR")
        self.crop_type = crop_type
        if crop_type:
            self.details["crop_type"] = crop_type


class LLMServiceException(AgentException):
    """Exception raised by LLM service operations"""
    
    def __init__(self, message: str, provider: Optional[str] = None):
        super().__init__(message, "LLM_SERVICE_ERROR")
        self.provider = provider
        if provider:
            self.details["provider"] = provider


class ValidationException(FarmXpertException):
    """Exception raised for input validation errors"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, "VALIDATION_ERROR")
        self.field = field
        if field:
            self.details["field"] = field


class ConfigurationException(FarmXpertException):
    """Exception raised for configuration errors"""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(message, "CONFIGURATION_ERROR")
        self.config_key = config_key
        if config_key:
            self.details["config_key"] = config_key


class ExternalServiceException(FarmXpertException):
    """Exception raised for external service failures"""
    
    def __init__(self, message: str, service_url: Optional[str] = None, status_code: Optional[int] = None):
        super().__init__(message, "EXTERNAL_SERVICE_ERROR")
        self.service_url = service_url
        self.status_code = status_code
        if service_url:
            self.details["service_url"] = service_url
        if status_code:
            self.details["status_code"] = status_code


class OrchestratorException(FarmXpertException):
    """Exception raised by orchestrator operations"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code or "ORCHESTRATOR_ERROR", details)
