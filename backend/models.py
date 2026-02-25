"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import date, datetime


# ============================================================================
# User Models
# ============================================================================

class UserRegister(BaseModel):
    """User registration request"""
    email: EmailStr
    username: str
    password: str
    confirm_password: str
    full_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    age: Optional[int] = None  # Added for personalization
    ethnicity: Optional[str] = None  # Added for personalization
    consent: bool  # Must accept data processing terms
    
    @validator('username')
    def validate_username(cls, v):
        if not v.isalnum():
            raise ValueError('Username must contain only letters and numbers')
        if len(v) < 3 or len(v) > 20:
            raise ValueError('Username must be 3-20 characters long')
        return v.lower()
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('consent')
    def consent_given(cls, v):
        if not v:
            raise ValueError('You must consent to data processing to register')
        return v


class UserLogin(BaseModel):
    """User login request"""
    username_or_email: str
    password: str
    remember_me: bool = False
    
    @validator('username_or_email')
    def normalize_input(cls, v):
        return v.lower().strip()


class UserResponse(BaseModel):
    """User data response (without sensitive fields)"""
    id: int
    email: str
    username: str
    full_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    ethnicity: Optional[str] = None
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


class UserUpdate(BaseModel):
    """User profile update request"""
    full_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    ethnicity: Optional[str] = None
    phone: Optional[str] = None


# ============================================================================
# Session Models
# ============================================================================

class SessionResponse(BaseModel):
    """Session information"""
    session_token: str
    user: UserResponse
    expires_in_hours: int = 24


# ============================================================================
# Response Models
# ============================================================================

class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    success: bool = False


class ReportRequest(BaseModel):
    """Request model for report generation"""
    analysis: dict
    insights: dict
    systems_impact: Optional[dict] = None
    filename: Optional[str] = "report"
