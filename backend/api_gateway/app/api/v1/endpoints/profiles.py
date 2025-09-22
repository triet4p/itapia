# api_gateway/app/api/v1/endpoints/profiles.py
"""User profile endpoints for managing investment profiles."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
# Dependencies to get service and current user
from app.dependencies import get_profile_service
from app.dependencies import get_current_user_dep
from app.core.exceptions import NoDataError, AuthError, DBError

# Schemas to validate request/response and define data types
from itapia_common.schemas.api.profiles import ProfileCreateRequest, ProfileUpdateRequest, ProfileResponse
from itapia_common.schemas.entities.profiles import ProfileCreate, ProfileUpdate, ProfileEntity
from itapia_common.schemas.entities.users import UserEntity # Assuming UserEntity is defined here

# Service class to handle business logic
from app.services.profiles import ProfileService

router = APIRouter()

def _change_from_entity_to_response(profile_entity: ProfileEntity):
    return ProfileResponse(
        created_at_ts=int(profile_entity.created_at.timestamp()),
        updated_at_ts=int(profile_entity.updated_at.timestamp()),
        **profile_entity.model_dump()
    )

@router.post(
    "/profiles", 
    response_model=ProfileResponse, 
    status_code=status.HTTP_201_CREATED,
    tags=['User Profiles'],
    summary="Create a new investment profile for the current user"
)
def create_user_profile(
    profile_in: ProfileCreateRequest,
    profile_service: ProfileService = Depends(get_profile_service),
    current_user: UserEntity = Depends(get_current_user_dep)
):
    """Create a new investment profile for the current logged-in user.
    
    Args:
        profile_in (ProfileCreateRequest): Profile creation request data
        profile_service (ProfileService): Profile service dependency
        current_user (UserEntity): Current authenticated user
        
    Returns:
        ProfileResponse: Created profile data
    """
    try:
        # Service will handle all creation logic
        created_profile = profile_service.create_profile(
            profile_in=ProfileCreate.model_validate(profile_in.model_dump()), 
            user_id=current_user.user_id
        )
        return _change_from_entity_to_response(created_profile)
    except NoDataError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.msg)
    except DBError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.msg)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.msg)
    except Exception as e:
        # Catch potential errors, e.g., UNIQUE constraint violations (user_id, profile_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Unknown Error: {str(e)}"
        )

@router.get(
    "/profiles", 
    response_model=List[ProfileResponse], 
    tags=['User Profiles'],
    summary="Get all investment profiles for the current user"
)
def get_user_profiles(
    profile_service: ProfileService = Depends(get_profile_service),
    current_user: UserEntity = Depends(get_current_user_dep)
):
    """Get all investment profiles for the current logged-in user.
    
    Args:
        profile_service (ProfileService): Profile service dependency
        current_user (UserEntity): Current authenticated user
        
    Returns:
        List[ProfileResponse]: List of user's investment profiles
    """
    profiles = profile_service.get_profiles_by_user(user_id=current_user.user_id)
    return [_change_from_entity_to_response(profile)
            for profile in profiles]

@router.get(
    "/profiles/{profile_id}", 
    response_model=ProfileResponse, 
    tags=['User Profiles'],
    summary="Get details of a specific investment profile"
)
def get_user_profile_details(
    profile_id: str,
    profile_service: ProfileService = Depends(get_profile_service),
    current_user: UserEntity = Depends(get_current_user_dep)
):
    """Get details of a specific investment profile.
    
    Args:
        profile_id (str): ID of the profile to retrieve
        profile_service (ProfileService): Profile service dependency
        current_user (UserEntity): Current authenticated user
        
    Returns:
        ProfileResponse: Requested profile data
    """
    try:
        profile = profile_service.get_profile_by_id(
            profile_id=profile_id,
            user_id=current_user.user_id
        )
        return _change_from_entity_to_response(profile)
    except NoDataError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.msg)
    except DBError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.msg)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.msg)
    except Exception as e:
        # Catch potential errors, e.g., UNIQUE constraint violations (user_id, profile_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Unknown Error: {str(e)}"
        )

@router.put(
    "/profiles/{profile_id}", 
    response_model=ProfileResponse, 
    tags=['User Profiles'],
    summary="Update an existing investment profile"
)
def update_user_profile(
    profile_id: str,
    profile_in: ProfileUpdateRequest,
    profile_service: ProfileService = Depends(get_profile_service),
    current_user: UserEntity = Depends(get_current_user_dep)
):
    """Update an existing investment profile.
    
    Args:
        profile_id (str): ID of the profile to update
        profile_in (ProfileUpdateRequest): Profile update request data
        profile_service (ProfileService): Profile service dependency
        current_user (UserEntity): Current authenticated user
        
    Returns:
        ProfileResponse: Updated profile data
    """
    try:
        profile = profile_service.update_profile(
            profile_id=profile_id,
            user_id=current_user.user_id,
            profile_in=ProfileUpdate.model_validate(profile_in.model_dump())
        )
        return _change_from_entity_to_response(profile)
    except NoDataError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.msg)
    except DBError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.msg)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.msg)
    except Exception as e:
        # Catch potential errors, e.g., UNIQUE constraint violations (user_id, profile_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Unknown Error: {str(e)}"
        )

@router.delete(
    "/profiles/{profile_id}", 
    response_model=ProfileResponse, 
    tags=['User Profiles'],
    summary="Delete an investment profile"
)
def delete_user_profile(
    profile_id: str,
    profile_service: ProfileService = Depends(get_profile_service),
    current_user: UserEntity = Depends(get_current_user_dep)
):
    """Delete an investment profile.
    
    Args:
        profile_id (str): ID of the profile to delete
        profile_service (ProfileService): Profile service dependency
        current_user (UserEntity): Current authenticated user
        
    Returns:
        ProfileResponse: Deleted profile data
    """
    try:
        profile = profile_service.remove_profile(
            profile_id=profile_id,
            user_id=current_user.user_id
        )
        return _change_from_entity_to_response(profile)
    except NoDataError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.msg)
    except DBError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.msg)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.msg)
    except Exception as e:
        # Catch potential errors, e.g., UNIQUE constraint violations (user_id, profile_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Unknown Error: {str(e)}"
        )