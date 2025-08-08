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
    def __init__(self, db_session: Session):
        self.db = db_session
        
    def _convert_parts_to_json_string(self, data: BaseModel) -> Dict[str, Any]:
        """
        Hàm helper để chuyển các object Pydantic lồng nhau thành chuỗi JSON.
        Hàm này rất quan trọng để làm việc với các cột JSONB.
        """
        # exclude_unset=True rất quan trọng cho hàm update
        dump = data.model_dump(exclude_unset=True) 
        for key, value in dump.items():
            # Nếu value là một object Pydantic (như RiskTolerancePart),
            # chuyển nó thành một chuỗi JSON.
            if isinstance(value, dict):
                dump[key] = json.dumps(value)
        return dump

    def get_profile_by_id(self, *, profile_id: str, user_id: str) -> ProfileEntity:
        row = profile_crud.get_by_id(self.db, profile_id=profile_id)
        entity = ProfileEntity.model_validate(row) if row else None
        
        if entity is None:
            raise NoDataError(f'Not found profile with id {profile_id}')
        if user_id != entity.user_id:
            raise AuthError(f'Profile with id {profile_id} can not accessed by user {user_id}')
        
        return entity
    
    def get_profile_by_name(self, *, profile_name: str, user_id: str):
        row = profile_crud.get_by_name(self.db, profile_name=profile_name, user_id=user_id)
        entity = ProfileEntity.model_validate(row) if row else None
        
        if entity is None:
            raise NoDataError(f'Not found profile with name {profile_name} for user {user_id}')
        if user_id != entity.user_id:
            raise AuthError(f'Profile with id {entity.profile_id} can not accessed by user {user_id}')
        
        return entity

    def get_profiles_by_user(self, *, user_id: str) -> List[ProfileEntity]:
        rows = profile_crud.get_multi_by_user(self.db, user_id=user_id)
        return [ProfileEntity.model_validate(row) for row in rows]

    def create_profile(self, *, profile_in: ProfileCreate, user_id: str) -> ProfileEntity:
        profile_id = uuid.uuid4().hex
        
        # Chuyển đổi toàn bộ object Pydantic thành dict, bao gồm cả việc jsonify các parts
        profile_data_to_db = self._convert_parts_to_json_string(profile_in)
        
        # Thêm các ID cần thiết
        profile_data_to_db["profile_id"] = profile_id
        profile_data_to_db["user_id"] = user_id
        
        created_row = profile_crud.create(self.db, profile_data=profile_data_to_db)
        
        if created_row is None:
            raise DBError("Failed to create profile in database.")
        
        return ProfileEntity.model_validate(created_row)

    def update_profile(self, *, profile_id: str, user_id: str, profile_in: ProfileUpdate) -> ProfileEntity:
        profile_to_update = self.get_profile_by_id(profile_id=profile_id, user_id=user_id)
        # Lấy dict chứa các trường cần cập nhật, loại bỏ các giá trị None
        update_data = self._convert_parts_to_json_string(profile_in)
        
        if not update_data:
            # Nếu không có gì để cập nhật, trả về profile hiện tại
            return profile_to_update

        updated_row = profile_crud.update(self.db, profile_id=profile_id, update_data=update_data)
        entity = ProfileEntity.model_validate(updated_row) if updated_row else None
        
        if entity is None:
            raise DBError(f'Not found profile with id {profile_id} in update')
        return entity

    def remove_profile(self, *, profile_id: str, user_id: str) -> ProfileEntity:
        profile_to_delete = self.get_profile_by_id(profile_id=profile_id, user_id=user_id)
        deleted_row = profile_crud.remove(self.db, profile_id=profile_id)
        entity = ProfileEntity.model_validate(deleted_row) if deleted_row else None
        if entity is None:
            raise DBError(f'Not found profile with id {profile_id} in delete')
        return entity