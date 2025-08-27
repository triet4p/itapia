from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
from app.services.auth.security import get_authorized_url, create_access_token
from app.services.users import UserService
from app.dependencies import get_users_service
import app.services.auth.google as google
from app.core.exceptions import AuthError, NoDataError, DBError, ServerCredError
from app.core.config import FRONTEND_CALLBACK_URL, FRONTEND_LOGIN_ERR_URL

from itapia_common.schemas.api.auth import AuthorizationURLResponse

router = APIRouter()

@router.get('/auth/google/login', response_model=AuthorizationURLResponse, tags=['Auth'])
def google_login():
    try:
        url = get_authorized_url()
        return AuthorizationURLResponse(authorization_url=url)
    except ServerCredError as e:
        raise HTTPException(status_code=401, detail=e.detail, headers=e.header)
    except Exception as ex:
        raise HTTPException(status_code=500, detail='Unknown Error occured in servers')

@router.get("/auth/google/callback")
async def google_callback(code: str, 
                          user_service: UserService = Depends(get_users_service)):
    try:
        # 1 & 2. Lấy token và thông tin user từ Google
        google_tokens = await google.get_google_tokens(code=code)
        user_info = await google.get_google_user_info(access_token=google_tokens["access_token"])

        # 3. Tìm hoặc tạo user trong CSDL
        user_in_db = user_service.get_or_create(user_info)

        # 4. Tạo JWT của ITAPIA
        # Payload của token sẽ chứa ID user trong hệ thống của bạn
        access_token = create_access_token(subject=user_in_db.user_id)
        
        # 5. Redirect về frontend
        # TODO: Đưa URL này vào biến môi trường
        frontend_callback_url = f'{FRONTEND_CALLBACK_URL}?token={access_token}'
        return RedirectResponse(url=frontend_callback_url)

    except ServerCredError as e:
        # Nếu có lỗi trong quá trình giao tiếp với Google, redirect về trang login của frontend với thông báo lỗi
        # TODO: Đưa URL này vào biến môi trường
        return RedirectResponse(url=f"{FRONTEND_LOGIN_ERR_URL}?error={e.detail}")
    except Exception as ex:
        raise HTTPException(status_code=500, detail='Unknown Error occured in servers')