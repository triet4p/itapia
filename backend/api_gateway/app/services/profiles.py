# itapia_common/dblib/services/profiles.py

import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json

from app.crud import profiles as profile_crud
from app.core.exceptions import AuthError, NoDataError, DBError
from itapia_common.schemas.entities.profiles import ProfileCreate, ProfileUpdate, ProfileEntity

class ProfileService:
    """Service class for managing investment profiles."""
    
    def __init__(self, db_session: Session):
        """Initialize ProfileService with a database session.
        
        Args:
            db_session (Session): Database session for performing CRUD operations
        """
        self.db = db_session
        
    def _convert_parts_to_json_string(self, data: BaseModel) -> Dict[str, Any]:
        """Helper function to convert nested Pydantic objects to JSON strings.
        
        This function is essential for working with JSONB columns.
        
        Args:
            data (BaseModel): Pydantic model to convert
            
        Returns:
            Dict[str, Any]: Dictionary with nested objects converted to JSON strings
        """
        # exclude_unset=True is important for the update function
        dump = data.model_dump(exclude_unset=True) 
        for key, value in dump.items():
            # If value is a Pydantic object (like RiskTolerancePart),
            # convert it to a JSON string.
            if isinstance(value, dict):
                dump[key] = json.dumps(value)
        return dump

    def get_profile_by_id(self, *, profile_id: str, user_id: str) -> ProfileEntity:
        """Get a profile by its ID and verify user ownership.
        
        Args:
            profile_id (str): ID of the profile to retrieve
            user_id (str): ID of the user requesting the profile
            
        Returns:
            ProfileEntity: The requested profile
            
        Raises:
            NoDataError: If profile with the given ID is not found
            AuthError: If the user doesn't own the profile
        """
        row = profile_crud.get_by_id(self.db, profile_id=profile_id)
        entity = ProfileEntity.model_validate(row) if row else None
        
        if entity is None:
            raise NoDataError(f'Not found profile with id {profile_id}')
        if user_id != entity.user_id:
            raise AuthError(f'Profile with id {profile_id} can not accessed by user {user_id}')
        
        return entity
    
    def get_profile_by_name(self, *, profile_name: str, user_id: str) -> ProfileEntity:
        """Get a profile by its name and verify user ownership.
        
        Args:
            profile_name (str): Name of the profile to retrieve
            user_id (str): ID of the user requesting the profile
            
        Returns:
            ProfileEntity: The requested profile
            
        Raises:
            NoDataError: If profile with the given name is not found for the user
            AuthError: If the user doesn't own the profile
        """
        row = profile_crud.get_by_name(self.db, profile_name=profile_name, user_id=user_id)
        entity = ProfileEntity.model_validate(row) if row else None
        
        if entity is None:
            raise NoDataError(f'Not found profile with name {profile_name} for user {user_id}')
        if user_id != entity.user_id:
            raise AuthError(f'Profile with id {entity.profile_id} can not accessed by user {user_id}')
        
        return entity

    def get_profiles_by_user(self, *, user_id: str) -> List[ProfileEntity]:
        """Get all profiles belonging to a user.
        
        Args:
            user_id (str): ID of the user whose profiles to retrieve
            
        Returns:
            List[ProfileEntity]: List of profiles belonging to the user
        """
        rows = profile_crud.get_multi_by_user(self.db, user_id=user_id)
        return [ProfileEntity.model_validate(row) for row in rows]

    def create_profile(self, *, profile_in: ProfileCreate, user_id: str) -> ProfileEntity:
        """Create a new investment profile.
        
        Args:
            profile_in (ProfileCreate): Profile data for creation
            user_id (str): ID of the user who owns the profile
            
        Returns:
            ProfileEntity: The created profile
            
        Raises:
            DBError: If profile creation fails
        """
        profile_id = uuid.uuid4().hex
        
        # Convert the entire Pydantic object to a dict, including jsonifying the parts
        profile_data_to_db = self._convert_parts_to_json_string(profile_in)
        
        # Add the required IDs
        profile_data_to_db["profile_id"] = profile_id
        profile_data_to_db["user_id"] = user_id
        
        created_row = profile_crud.create(self.db, profile_data=profile_data_to_db)
        
        if created_row is None:
            raise DBError("Failed to create profile in database.")
        
        return ProfileEntity.model_validate(created_row)

    def update_profile(self, *, profile_id: str, user_id: str, profile_in: ProfileUpdate) -> ProfileEntity:
        """Update an existing investment profile.
        
        Args:
            profile_id (str): ID of the profile to update
            user_id (str): ID of the user who owns the profile
            profile_in (ProfileUpdate): Profile data to update
            
        Returns:
            ProfileEntity: The updated profile
            
        Raises:
            NoDataError: If profile with the given ID is not found
            AuthError: If the user doesn't own the profile
            DBError: If profile update fails
        """
        profile_to_update = self.get_profile_by_id(profile_id=profile_id, user_id=user_id)
        # Get a dict containing the fields to update, removing None values
        update_data = self._convert_parts_to_json_string(profile_in)
        
        if not update_data:
            # If there's nothing to update, return the current profile
            return profile_to_update

        updated_row = profile_crud.update(self.db, profile_id=profile_id, update_data=update_data)
        entity = ProfileEntity.model_validate(updated_row) if updated_row else None
        
        if entity is None:
            raise DBError(f'Not found profile with id {profile_id} in update')
        return entity

    def remove_profile(self, *, profile_id: str, user_id: str) -> ProfileEntity:
        """Remove an investment profile.
        
        Args:
            profile_id (str): ID of the profile to remove
            user_id (str): ID of the user who owns the profile
            
        Returns:
            ProfileEntity: The removed profile
            
        Raises:
            NoDataError: If profile with the given ID is not found
            AuthError: If the user doesn't own the profile
            DBError: If profile deletion fails
        """
        profile_to_delete = self.get_profile_by_id(profile_id=profile_id, user_id=user_id)
        deleted_row = profile_crud.remove(self.db, profile_id=profile_id)
        entity = ProfileEntity.model_validate(deleted_row) if deleted_row else None
        if entity is None:
            raise DBError(f'Not found profile with id {profile_id} in delete')
        return entity