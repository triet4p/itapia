from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies import get_current_user_dep
from itapia_common.schemas.api.users import UserResponse
from itapia_common.schemas.entities.users import UserEntity
from app.core.exceptions import NoDataError, AuthError, DBError

router = APIRouter()


@router.get('/users/me', response_model=UserResponse, tags=['Users'])
def get_me(current_user: UserEntity = Depends(get_current_user_dep)):
    try:
        return UserResponse.model_validate(current_user.model_dump())
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