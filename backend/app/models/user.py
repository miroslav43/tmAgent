"""
User model for authentication and profile management.
Supports citizen and official roles with profile data and activity tracking.
"""

from sqlalchemy import Column, String, DateTime, Text, CheckConstraint, Boolean, Date, ForeignKey, Float, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func, text
from sqlalchemy.orm import relationship
import uuid
from enum import Enum

from ..db.database import Base


class UserRole(str, Enum):
    """User role enumeration"""
    CITIZEN = "citizen"
    OFFICIAL = "official"


class User(Base):
    """
    User model for authentication and profile management
    """
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="citizen")
    
    # Profile information
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    address = Column(Text)
    date_of_birth = Column(Date)
    cnp = Column(String(13))  # Romanian personal numeric code
    avatar = Column(Text)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())
    
    # Add check constraint for role
    __table_args__ = (
        CheckConstraint("role IN ('citizen', 'official')", name='users_role_check'),
    )
    
    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    ai_extracted_info = relationship("UserAIExtractedInfo", back_populates="user", cascade="all, delete-orphan")
    scanned_documents = relationship("UserScannedDocument", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


class UserAIExtractedInfo(Base):
    """
    AI-extracted personal information from scanned documents
    """
    __tablename__ = "user_ai_extracted_info"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Extracted personal information
    extracted_first_name = Column(String(100))
    extracted_last_name = Column(String(100))
    extracted_cnp = Column(String(13))
    extracted_address = Column(Text)
    extracted_phone = Column(String(20))
    extracted_birth_date = Column(Date)
    extracted_birth_place = Column(String(255))
    extracted_nationality = Column(String(100))
    extracted_id_series = Column(String(10))
    extracted_id_number = Column(String(20))
    extracted_issued_by = Column(String(255))
    extracted_issue_date = Column(Date)
    extracted_expiry_date = Column(Date)
    
    # Source document information
    source_document_type = Column(String(50))  # "carte_identitate", "pasaport", "certificat_nastere", etc.
    source_document_path = Column(Text)
    extraction_confidence = Column(Float)  # 0.0 - 1.0
    
    # AI processing metadata
    extracted_data_raw = Column(JSONB)  # Raw AI response
    processing_notes = Column(Text)
    ai_model_used = Column(String(50), default="gemini-2.0-flash")
    
    # Status tracking
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime)
    verification_status = Column(String(20), default="pending")  # pending, approved, rejected
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())
    
    # Relationships
    user = relationship("User", back_populates="ai_extracted_info")
    
    def __repr__(self):
        return f"<UserAIExtractedInfo(id={self.id}, user_id={self.user_id}, type={self.source_document_type})>"


class UserScannedDocument(Base):
    """
    Documents scanned by users with OCR processing results
    """
    __tablename__ = "user_scanned_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Document information
    original_filename = Column(String(255), nullable=False)
    document_type = Column(String(50))  # Category detected by AI
    title = Column(String(255))  # AI-generated title
    description = Column(Text)  # AI-generated description
    
    # File storage
    file_path = Column(Text, nullable=False)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100))
    
    # OCR results
    transcribed_text = Column(Text)  # Full OCR text
    metadata_json = Column(JSONB)  # Structured metadata from AI
    confidence_score = Column(Float)  # Overall OCR confidence
    
    # AI processing
    ai_model_used = Column(String(50), default="gemini-2.0-flash")
    processing_time = Column(Float)  # Seconds
    
    # Status
    processing_status = Column(String(20), default="completed")  # processing, completed, failed
    error_message = Column(Text)
    
    # Privacy and access
    is_private = Column(Boolean, default=True)  # User-specific by default
    shared_with_officials = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())
    
    # Relationships
    user = relationship("User", back_populates="scanned_documents")
    
    def __repr__(self):
        return f"<UserScannedDocument(id={self.id}, user_id={self.user_id}, filename={self.original_filename})>"


class UserActivity(Base):
    """
    User activity tracking model
    """
    __tablename__ = "user_activity"
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"), index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(255), nullable=False)
    details = Column(Text)
    ip_address = Column(String(45))  # IPv6 support
    user_agent = Column(Text)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<UserActivity(id={self.id}, user_id={self.user_id}, action={self.action})>" 