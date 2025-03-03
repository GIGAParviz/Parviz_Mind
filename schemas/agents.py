from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

class AgentStatus(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"

class AgentLevel(str, Enum):
    JUNIOR = "junior"
    INTERMEDIATE = "intermediate"
    SENIOR = "senior"
    EXPERT = "expert"

class AgentBase(BaseModel):
    """Base schema for agent."""
    name: str = Field(..., description="Agent name")
    level: AgentLevel = Field(..., description="Agent expertise level")
    hourly_rate: float = Field(..., gt=0, description="Hourly rate in dollars")
    specialties: Optional[List[str]] = Field(None, description="Agent specialties")
    languages: Optional[List[str]] = Field(None, description="Languages spoken by agent")
    
class AgentCreate(AgentBase):
    """Schema for creating an agent."""
    agent_id: Optional[str] = Field(None, description="Optional agent ID")
    status: AgentStatus = Field(AgentStatus.OFFLINE, description="Initial agent status")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "John Smith",
                "level": "senior",
                "hourly_rate": 75.0,
                "specialties": ["Python", "Machine Learning", "Flask"],
                "languages": ["en", "fa"],
                "status": "offline"
            }
        }

class AgentUpdate(BaseModel):
    """Schema for updating an agent."""
    name: Optional[str] = Field(None, description="Agent name")
    level: Optional[AgentLevel] = Field(None, description="Agent expertise level")
    hourly_rate: Optional[float] = Field(None, gt=0, description="Hourly rate in dollars")
    specialties: Optional[List[str]] = Field(None, description="Agent specialties")
    languages: Optional[List[str]] = Field(None, description="Languages spoken by agent")
    status: Optional[AgentStatus] = Field(None, description="Agent status")
    
    class Config:
        schema_extra = {
            "example": {
                "hourly_rate": 80.0,
                "status": "available"
            }
        }

class AgentResponse(AgentBase):
    """Schema for agent response."""
    id: str = Field(..., description="Agent ID")
    status: AgentStatus = Field(..., description="Agent status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Average rating")
    
    class Config:
        orm_mode = True
        
class AgentRating(BaseModel):
    """Schema for rating an agent."""
    rating: float = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    feedback: Optional[str] = Field(None, description="Feedback comment")
    
    class Config:
        schema_extra = {
            "example": {
                "rating": 4.5,
                "feedback": "Very helpful and knowledgeable agent."
            }
        }

class AgentHandoffRequest(BaseModel):
    """Schema for requesting a handoff to a human agent."""
    conversation_id: str = Field(..., description="Conversation ID")
    reason: str = Field(..., description="Reason for handoff")
    preferred_language: Optional[str] = Field(None, description="Preferred language")
    preferred_level: Optional[AgentLevel] = Field(None, description="Preferred agent level")
    required_specialties: Optional[List[str]] = Field(None, description="Required specialties")
    
    class Config:
        schema_extra = {
            "example": {
                "conversation_id": "conv123",
                "reason": "Need help with complex technical issue",
                "preferred_language": "en",
                "preferred_level": "senior",
                "required_specialties": ["Python", "Flask"]
            }
        }
