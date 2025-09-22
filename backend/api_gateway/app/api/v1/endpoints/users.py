"""User endpoints for managing user information."""

from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies import get_current_user_dep
from itapia_common.schemas.api.users import UserResponse
from itapia_common.schemas.entities.users import UserEntity
from app.core.exceptions import NoDataError, AuthError, DBError

router = APIRouter()


@router.get('/users/me', 
            response_model=UserResponse, 
            tags=['Users'],
            summary="Get current user information")
def get_me(current_user: UserEntity = Depends(get_current_user_dep)):
    """Get current user information.
    
    Args:
        current_user (UserEntity): Current authenticated user
        
    Returns:
        UserResponse: Current user information
    """
    try:
        return UserResponse.model_validate(current_user.model_dump())
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