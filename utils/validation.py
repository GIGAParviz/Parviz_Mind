from typing import Dict, Any
from utils.language import Language, ResponseLength, ResponseStyle

class ValidationError(Exception):
    """Exception for validation errors."""
    
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

def validate_language(language):
    """Validate language value."""
    try:
        if isinstance(language, str):
            language = Language(language)
        return language
    except ValueError:
        valid_values = ", ".join([e.value for e in Language])
        raise ValidationError(f"Invalid language. Valid values are: {valid_values}")

def validate_response_length(length):
    """Validate response length value."""
    try:
        if isinstance(length, str):
            length = ResponseLength(length)
        return length
    except ValueError:
        valid_values = ", ".join([e.value for e in ResponseLength])
        raise ValidationError(f"Invalid response length. Valid values are: {valid_values}")

def validate_response_style(style):
    """Validate response style value."""
    try:
        if isinstance(style, str):
            style = ResponseStyle(style)
        return style
    except ValueError:
        valid_values = ", ".join([e.value for e in ResponseStyle])
        raise ValidationError(f"Invalid response style. Valid values are: {valid_values}")

def validate_creativity(creativity):
    """Validate creativity value."""
    try:
        creativity = float(creativity)
        if creativity < 0 or creativity > 1:
            raise ValueError()
        return creativity
    except (ValueError, TypeError):
        raise ValidationError("Creativity must be a float between 0 and 1")

def validate_chat_request(data):
    """Validate chat request data."""
    if not data:
        raise ValidationError("Request data is required")
    
    # Validate required fields
    required_fields = ["user_id", "query"]
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Missing required field: {field}")
    
    # Validate query
    if not data["query"].strip():
        raise ValidationError("Query cannot be empty")
    
    # Validate optional fields
    if "language" in data:
        data["language"] = validate_language(data["language"])
    
    if "response_length" in data:
        data["response_length"] = validate_response_length(data["response_length"])
    
    if "tone" in data:
        data["tone"] = validate_response_style(data["tone"])
    
    if "creativity" in data:
        data["creativity"] = validate_creativity(data["creativity"])
    
    return data

def validate_agent_request(data):
    """Validate agent request data."""
    if not data:
        raise ValidationError("Request data is required")
    
    # Validate required fields for agent creation
    if "name" not in data:
        raise ValidationError("Agent name is required")
    
    if "level" in data:
        try:
            from schemas.agents import AgentLevel
            if isinstance(data["level"], str):
                data["level"] = AgentLevel(data["level"])
        except ValueError:
            from schemas.agents import AgentLevel
            valid_values = ", ".join([e.value for e in AgentLevel])
            raise ValidationError(f"Invalid agent level. Valid values are: {valid_values}")
    
    if "hourly_rate" in data:
        try:
            hourly_rate = float(data["hourly_rate"])
            if hourly_rate <= 0:
                raise ValueError()
            data["hourly_rate"] = hourly_rate
        except (ValueError, TypeError):
            raise ValidationError("Hourly rate must be a positive number")
    
    if "status" in data:
        try:
            from schemas.agents import AgentStatus
            if isinstance(data["status"], str):
                data["status"] = AgentStatus(data["status"])
        except ValueError:
            from schemas.agents import AgentStatus
            valid_values = ", ".join([e.value for e in AgentStatus])
            raise ValidationError(f"Invalid agent status. Valid values are: {valid_values}")
    
    return data
