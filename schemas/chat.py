from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime

from utils.language import Language, ResponseLength, ResponseStyle

class ChatRequest(BaseModel):
    """Schema for chat request."""
    user_id: str = Field(..., description="User ID")
    query: str = Field(..., min_length=1, description="User query text")
    model_name: str = Field("groq-llama3", description="AI model to use")
    tone: ResponseStyle = Field(ResponseStyle.CONVERSATIONAL, description="Tone of response")
    language: Language = Field(Language.ENGLISH, description="Response language")
    response_length: ResponseLength = Field(ResponseLength.MEDIUM, description="Desired response length")
    summarize: bool = Field(False, description="Whether to summarize the conversation")
    creativity: float = Field(0.7, ge=0.0, le=1.0, description="Creativity level")
    welcome_message: bool = Field(False, description="Whether this is a welcome message")
    keywords: Optional[List[str]] = Field(None, description="Keywords to include in response")
    exclusion_words: Optional[List[str]] = Field(None, description="Words to exclude from response")
    main_prompt: Optional[str] = Field(None, description="Custom system prompt")
    chatbot_name: str = Field("Parviz", description="Name of the chatbot")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "user123",
                "query": "Tell me about artificial intelligence",
                "model_name": "groq-llama3",
                "tone": "conversational",
                "language": "en",
                "response_length": "medium",
                "creativity": 0.7,
                "summarize": False,
                "chatbot_name": "Parviz"
            }
        }

class MessageBase(BaseModel):
    """Base schema for message."""
    role: str = Field(..., description="Message role (user or assistant)")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(None, description="Message timestamp")

class MessageCreate(MessageBase):
    """Schema for creating a message."""
    conversation_id: str = Field(..., description="Conversation ID")

class MessageResponse(MessageBase):
    """Schema for message response."""
    id: str = Field(..., description="Message ID")
    conversation_id: str = Field(..., description="Conversation ID")
    
    class Config:
        orm_mode = True

class ConversationBase(BaseModel):
    """Base schema for conversation."""
    title: str = Field(..., description="Conversation title")
    model: str = Field(..., description="Model used for conversation")
    language: str = Field(..., description="Conversation language")

class ConversationCreate(ConversationBase):
    """Schema for creating a conversation."""
    user_id: str = Field(..., description="User ID")

class ConversationResponse(ConversationBase):
    """Schema for conversation response."""
    id: str = Field(..., description="Conversation ID")
    user_id: str = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        orm_mode = True

class ChatResponse(BaseModel):
    """Schema for chat response."""
    response: str = Field(..., description="AI response text")
    conversation_id: str = Field(..., description="Conversation ID")
    model: str = Field(..., description="Model used for response")
    tokens: int = Field(..., description="Number of tokens in response")
    price: float = Field(..., description="Price of the response")
    summary: Optional[str] = Field(None, description="Conversation summary")
