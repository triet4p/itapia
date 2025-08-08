# api_gateway/app/api/v1/endpoints/profiles.py

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
# Dependencies để lấy service và user hiện tại
from app.dependencies import get_profile_service
from app.dependencies import get_current_user_dep
from app.core.exceptions import NoDataError, AuthError, DBError

# Schemas để validate request/response và định nghĩa kiểu dữ liệu
from itapia_common.schemas.api.profiles import ProfileCreateRequest, ProfileUpdateRequest, ProfileResponse
from itapia_common.schemas.entities.profiles import ProfileCreate, ProfileUpdate, ProfileEntity
from itapia_common.schemas.entities.users import UserEntity # Giả sử UserEntity được định nghĩa ở đây

# Service class để xử lý logic nghiệp vụ
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
    tags=['User Profiles']
)
def create_user_profile(
    profile_in: ProfileCreateRequest,
    profile_service: ProfileService = Depends(get_profile_service),
    current_user: UserEntity = Depends(get_current_user_dep)
):
    """
    Create a new investment profile for the current logged-in user.
    """
    try:
        # Service sẽ xử lý toàn bộ logic tạo mới
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
        # Bắt các lỗi tiềm ẩn, ví dụ như vi phạm ràng buộc UNIQUE (user_id, profile_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Unknown Error: {str(e)}"
        )

@router.get(
    "/profiles", 
    response_model=List[ProfileResponse], 
    tags=['User Profiles']
)
def get_user_profiles(
    profile_service: ProfileService = Depends(get_profile_service),
    current_user: UserEntity = Depends(get_current_user_dep)
):
    """
    Get all investment profiles for the current logged-in user.
    """
    profiles = profile_service.get_profiles_by_user(user_id=current_user.user_id)
    return [_change_from_entity_to_response(profile)
            for profile in profiles]

@router.get(
    "/profiles/{profile_id}", 
    response_model=ProfileResponse, 
    tags=['User Profiles']
)
def get_user_profile_details(
    profile_id: str,
    profile_service: ProfileService = Depends(get_profile_service),
    current_user: UserEntity = Depends(get_current_user_dep)
):
    """
    Get details of a specific investment profile.
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
        # Bắt các lỗi tiềm ẩn, ví dụ như vi phạm ràng buộc UNIQUE (user_id, profile_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Unknown Error: {str(e)}"
        )

@router.put(
    "/profiles/{profile_id}", 
    response_model=ProfileResponse, 
    tags=['User Profiles']
)
def update_user_profile(
    profile_id: str,
    profile_in: ProfileUpdateRequest,
    profile_service: ProfileService = Depends(get_profile_service),
    current_user: UserEntity = Depends(get_current_user_dep)
):
    """
    Update an existing investment profile.
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
        # Bắt các lỗi tiềm ẩn, ví dụ như vi phạm ràng buộc UNIQUE (user_id, profile_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Unknown Error: {str(e)}"
        )

@router.delete(
    "/profiles/{profile_id}", 
    response_model=ProfileResponse, 
    tags=['User Profiles']
)
def delete_user_profile(
    profile_id: str,
    profile_service: ProfileService = Depends(get_profile_service),
    current_user: UserEntity = Depends(get_current_user_dep)
):
    """
    Delete an investment profile.
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
        # Bắt các lỗi tiềm ẩn, ví dụ như vi phạm ràng buộc UNIQUE (user_id, profile_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Unknown Error: {str(e)}"
        )