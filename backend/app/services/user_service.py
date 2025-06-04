"""
User service for business logic related to user management.
Handles user creation, authentication, profile updates, and queries.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from typing import Optional, List
from uuid import UUID
import asyncio

from ..models.user import User, UserRole, UserAIExtractedInfo, UserScannedDocument
from ..schemas.user import UserCreate, UserUpdate, UserResponse, UserProfile, PersonalInfoUpdateRequest
from ..core.security import get_password_hash, verify_password
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


class UserService:
    """
    Service class for user-related business logic
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user account
        """
        # Check if user already exists
        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash the password
        password_hash = get_password_hash(user_data.password)
        
        # Create user
        db_user = User(
            email=user_data.email,
            password_hash=password_hash,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
            role=user_data.role or "citizen"
        )
        
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        
        # Send welcome email asynchronously (don't wait for it)
        asyncio.create_task(self._send_welcome_email_async(db_user))
        
        return db_user
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address
        """
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get user by ID
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_profile(self, user_id: UUID) -> Optional[UserProfile]:
        """
        Get complete user profile with AI-extracted information and scanned documents
        """
        result = await self.db.execute(
            select(User)
            .options(
                selectinload(User.ai_extracted_info),
                selectinload(User.scanned_documents)
            )
            .where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        return UserProfile.model_validate(user)
    
    async def update_user_profile(self, user_id: UUID, user_data: UserUpdate) -> User:
        """
        Update user profile information
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update fields if provided
        if user_data.first_name is not None:
            user.first_name = user_data.first_name
        if user_data.last_name is not None:
            user.last_name = user_data.last_name
        if user_data.phone is not None:
            user.phone = user_data.phone
        if user_data.address is not None:
            user.address = user_data.address
        if user_data.cnp is not None:
            user.cnp = user_data.cnp
        if user_data.avatar_url is not None:
            user.avatar = user_data.avatar_url
        
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    async def update_profile_from_extracted_info(self, user_id: UUID, 
                                                update_request: PersonalInfoUpdateRequest) -> User:
        """
        Update user profile using AI-extracted information
        """
        # Get the user
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get the extracted info
        result = await self.db.execute(
            select(UserAIExtractedInfo)
            .where(
                UserAIExtractedInfo.id == UUID(update_request.extracted_info_id),
                UserAIExtractedInfo.user_id == user_id
            )
        )
        extracted_info = result.scalar_one_or_none()
        
        if not extracted_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Extracted information not found"
            )
        
        # Update user profile based on selected fields
        if update_request.use_extracted_first_name and extracted_info.extracted_first_name:
            user.first_name = extracted_info.extracted_first_name
        
        if update_request.use_extracted_last_name and extracted_info.extracted_last_name:
            user.last_name = extracted_info.extracted_last_name
        
        if update_request.use_extracted_cnp and extracted_info.extracted_cnp:
            user.cnp = extracted_info.extracted_cnp
        
        if update_request.use_extracted_address and extracted_info.extracted_address:
            user.address = extracted_info.extracted_address
        
        if update_request.use_extracted_phone and extracted_info.extracted_phone:
            user.phone = extracted_info.extracted_phone
        
        # Mark the extracted info as verified if it was used
        if any([
            update_request.use_extracted_first_name,
            update_request.use_extracted_last_name,
            update_request.use_extracted_cnp,
            update_request.use_extracted_address,
            update_request.use_extracted_phone
        ]):
            extracted_info.is_verified = True
            extracted_info.verification_status = "approved"
            from datetime import datetime
            extracted_info.verified_at = datetime.now()
        
        await self.db.commit()
        await self.db.refresh(user)
        
        logger.info(f"Updated user profile {user_id} from AI-extracted info {update_request.extracted_info_id}")
        return user
    
    async def get_user_extracted_info(self, user_id: UUID) -> List[UserAIExtractedInfo]:
        """
        Get all AI-extracted information for a user
        """
        result = await self.db.execute(
            select(UserAIExtractedInfo)
            .where(UserAIExtractedInfo.user_id == user_id)
            .order_by(UserAIExtractedInfo.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_user_scanned_documents(self, user_id: UUID) -> List[UserScannedDocument]:
        """
        Get all scanned documents for a user
        """
        result = await self.db.execute(
            select(UserScannedDocument)
            .where(UserScannedDocument.user_id == user_id)
            .order_by(UserScannedDocument.created_at.desc())
        )
        return result.scalars().all()
    
    async def verify_extracted_info(self, user_id: UUID, extracted_info_id: UUID, 
                                   is_approved: bool, notes: str = None) -> UserAIExtractedInfo:
        """
        Verify or reject AI-extracted information
        """
        result = await self.db.execute(
            select(UserAIExtractedInfo)
            .where(
                UserAIExtractedInfo.id == extracted_info_id,
                UserAIExtractedInfo.user_id == user_id
            )
        )
        extracted_info = result.scalar_one_or_none()
        
        if not extracted_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Extracted information not found"
            )
        
        extracted_info.is_verified = is_approved
        extracted_info.verification_status = "approved" if is_approved else "rejected"
        if notes:
            extracted_info.processing_notes = notes
        
        from datetime import datetime
        extracted_info.verified_at = datetime.now()
        
        await self.db.commit()
        await self.db.refresh(extracted_info)
        
        return extracted_info
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user with email and password
        """
        user = await self.get_user_by_email(email)
        if not user:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        # Update last login
        from datetime import datetime
        user.last_login = datetime.now()
        await self.db.commit()
        
        return user
    
    async def list_users(self, skip: int = 0, limit: int = 100, role: str = None) -> List[User]:
        """
        List users with pagination and optional role filter
        """
        query = select(User)
        
        if role:
            query = query.where(User.role == role)
        
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def deactivate_user(self, user_id: UUID) -> User:
        """
        Deactivate a user account
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_active = False
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    async def activate_user(self, user_id: UUID) -> User:
        """
        Activate a user account
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_active = True
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    async def _send_welcome_email_async(self, user: User):
        """
        Send welcome email asynchronously (placeholder implementation)
        """
        try:
            # Placeholder for email sending logic
            logger.info(f"Sending welcome email to {user.email}")
            # Implement actual email sending here
            await asyncio.sleep(0.1)  # Simulate async email sending
        except Exception as e:
            logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
    
    async def get_profile_completion_status(self, user_id: UUID) -> dict:
        """
        Get profile completion status based on filled fields and AI-extracted info
        """
        user_profile = await self.get_user_profile(user_id)
        if not user_profile:
            return {"completion_percentage": 0, "missing_fields": [], "has_ai_data": False}
        
        # Define required fields for complete profile
        required_fields = {
            "first_name": user_profile.first_name,
            "last_name": user_profile.last_name,
            "phone": user_profile.phone,
            "address": user_profile.address,
            "cnp": user_profile.cnp
        }
        
        filled_fields = sum(1 for value in required_fields.values() if value)
        total_fields = len(required_fields)
        completion_percentage = int((filled_fields / total_fields) * 100)
        
        missing_fields = [field for field, value in required_fields.items() if not value]
        
        # Check if there's AI-extracted data that could fill missing fields
        has_usable_ai_data = False
        if user_profile.ai_extracted_info:
            for extracted_info in user_profile.ai_extracted_info:
                if not extracted_info.is_verified:  # Unverified data can still be used
                    if any([
                        extracted_info.extracted_first_name and not user_profile.first_name,
                        extracted_info.extracted_last_name and not user_profile.last_name,
                        extracted_info.extracted_phone and not user_profile.phone,
                        extracted_info.extracted_address and not user_profile.address,
                        extracted_info.extracted_cnp and not user_profile.cnp
                    ]):
                        has_usable_ai_data = True
                        break
        
        return {
            "completion_percentage": completion_percentage,
            "missing_fields": missing_fields,
            "has_ai_data": len(user_profile.ai_extracted_info) > 0,
            "has_usable_ai_data": has_usable_ai_data,
            "verified_documents": len([info for info in user_profile.ai_extracted_info if info.is_verified]),
            "total_scanned_documents": len(user_profile.scanned_documents)
        } 