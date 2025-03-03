from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field

class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(20, ge=1, le=100, description="Items per page")
    
class PaginatedResponse(BaseModel):
    """Base model for paginated responses."""
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    total: int = Field(..., description="Total number of items")

class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    
class SuccessResponse(BaseModel):
    """Success response model."""
    success: bool = Field(True, description="Success flag")
    message: Optional[str] = Field(None, description="Success message")
