"""
Pydantic schemas for user-related requests and responses.
Provides type-safe validation for user endpoints.
"""

from pydantic import BaseModel, EmailStr, Field, computed_field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum
from uuid import UUID


class UserRole(str, Enum):
    """User role enumeration"""
    CITIZEN = "citizen"
    OFFICIAL = "official"


class UserCreate(BaseModel):
    """Schema for user registration"""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    role: UserRole = UserRole.CITIZEN
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    cnp: Optional[str] = Field(None, max_length=13)


class UserUpdate(BaseModel):
    """Schema for user profile updates"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    cnp: Optional[str] = Field(None, max_length=13)
    avatar_url: Optional[str] = None


class AIExtractedInfoResponse(BaseModel):
    """Schema for AI-extracted personal information"""
    id: str
    extracted_first_name: Optional[str] = None
    extracted_last_name: Optional[str] = None
    extracted_cnp: Optional[str] = None
    extracted_address: Optional[str] = None
    extracted_phone: Optional[str] = None
    extracted_birth_date: Optional[date] = None
    extracted_birth_place: Optional[str] = None
    extracted_nationality: Optional[str] = None
    extracted_id_series: Optional[str] = None
    extracted_id_number: Optional[str] = None
    extracted_issued_by: Optional[str] = None
    extracted_issue_date: Optional[date] = None
    extracted_expiry_date: Optional[date] = None
    source_document_type: Optional[str] = None
    extraction_confidence: Optional[float] = None
    is_verified: bool = False
    verification_status: str = "pending"
    created_at: datetime
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_string(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True


class ScannedDocumentResponse(BaseModel):
    """Schema for user scanned documents"""
    id: str
    original_filename: str
    document_type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    file_size: int
    mime_type: Optional[str] = None
    confidence_score: Optional[float] = None
    processing_status: str = "completed"
    created_at: datetime
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_string(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """Schema for user data responses"""
    id: str
    first_name: str
    last_name: str
    email: str
    role: UserRole
    phone: Optional[str] = None
    address: Optional[str] = None
    cnp: Optional[str] = None
    avatar: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_string(cls, v):
        """Convert UUID to string"""
        if isinstance(v, UUID):
            return str(v)
        return v

    @computed_field
    @property
    def name(self) -> str:
        """Computed field that combines first_name and last_name"""
        return f"{self.first_name} {self.last_name}".strip()

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserProfile(BaseModel):
    """Schema for detailed user profile with AI-extracted information"""
    id: str
    first_name: str
    last_name: str
    email: str
    role: UserRole
    phone: Optional[str] = None
    address: Optional[str] = None
    cnp: Optional[str] = None
    avatar: Optional[str] = None
    created_at: datetime
    
    # AI-extracted information
    ai_extracted_info: List[AIExtractedInfoResponse] = []
    scanned_documents: List[ScannedDocumentResponse] = []
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_string(cls, v):
        """Convert UUID to string"""
        if isinstance(v, UUID):
            return str(v)
        return v
    
    @computed_field
    @property
    def name(self) -> str:
        """Computed field that combines first_name and last_name"""
        return f"{self.first_name} {self.last_name}".strip()
    
    @computed_field
    @property
    def has_verified_documents(self) -> bool:
        """Check if user has any verified AI-extracted documents"""
        return any(info.is_verified for info in self.ai_extracted_info)
    
    @computed_field
    @property
    def most_recent_extracted_info(self) -> Optional[AIExtractedInfoResponse]:
        """Get the most recent AI-extracted information"""
        if not self.ai_extracted_info:
            return None
        return max(self.ai_extracted_info, key=lambda x: x.created_at)
    
    class Config:
        from_attributes = True


class PersonalInfoUpdateRequest(BaseModel):
    """Schema for updating personal information from AI-extracted data"""
    use_extracted_first_name: bool = False
    use_extracted_last_name: bool = False
    use_extracted_cnp: bool = False
    use_extracted_address: bool = False
    use_extracted_phone: bool = False
    extracted_info_id: str
    
    @field_validator('extracted_info_id', mode='before')
    @classmethod
    def convert_uuid_to_string(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v 