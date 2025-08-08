# itapia_common/dblib/services/profiles.py

import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel

from itapia_common.dblib.crud import profiles as profile_crud
from itapia_common.schemas.entities.profiles import ProfileCreate, ProfileUpdate, ProfileEntity

class ProfileService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def get_profile_by_id(self, *, profile_id: str) -> Optional[ProfileEntity]:
        row = profile_crud.get_by_id(self.db, profile_id=profile_id)
        return ProfileEntity.model_validate(row) if row else None
    
    def get_profile_by_name(self, *, profile_name: str, user_id: str) -> Optional[ProfileEntity]:
        row = profile_crud.get_by_name(self.db, profile_name=profile_name, user_id=user_id)
        return ProfileEntity.model_validate(row) if row else None

    def get_profiles_by_user(self, *, user_id: str) -> List[ProfileEntity]:
        rows = profile_crud.get_multi_by_user(self.db, user_id=user_id)
        return [ProfileEntity.model_validate(row) for row in rows]

    def create_profile(self, *, profile_in: ProfileCreate, user_id: str) -> ProfileEntity:
        profile_id = uuid.uuid4().hex
        
        # Chuyển đổi toàn bộ object Pydantic thành dict, bao gồm cả việc jsonify các parts
        profile_data_to_db = profile_in.model_dump()
        
        # Thêm các ID cần thiết
        profile_data_to_db["profile_id"] = profile_id
        profile_data_to_db["user_id"] = user_id
        
        created_row = profile_crud.create(self.db, profile_data=profile_data_to_db)
        return ProfileEntity.model_validate(created_row)

    def update_profile(self, *, profile_id: str, profile_in: ProfileUpdate) -> Optional[ProfileEntity]:
        # Lấy dict chứa các trường cần cập nhật, loại bỏ các giá trị None
        update_data = profile_in.model_dump(exclude_unset=True)
        
        if not update_data:
            # Nếu không có gì để cập nhật, trả về profile hiện tại
            return self.get_profile_by_id(profile_id=profile_id) # Cần user_id thật

        updated_row = profile_crud.update(self.db, profile_id=profile_id, update_data=update_data)
        return ProfileEntity.model_validate(updated_row) if updated_row else None

    def remove_profile(self, *, profile_id: str) -> Optional[ProfileEntity]:
        deleted_row = profile_crud.remove(self.db, profile_id=profile_id)
        return ProfileEntity.model_validate(deleted_row) if deleted_row else None