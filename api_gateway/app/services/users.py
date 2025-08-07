from typing import List
from sqlalchemy.orm import Session
from app.crud.users import get_by_google_id, create, get_by_id
from app.schemas.users import UserEntity, UserCreate
import uuid

class UserService:
    def __init__(self, rdbms_session: Session):
        self.rdbms_session = rdbms_session
        
    def create_user(self, user: UserCreate) -> UserEntity|None:
        user_id = uuid.uuid4().hex
        user_entity = UserEntity(
            user_id=user_id,
            is_active=True,
            **user.model_dump()
        )
        row = create(self.rdbms_session, user_entity.model_dump())
        
        if row:
            return UserEntity(**row)
        return None
    
    def get_user_by_google_id(self, google_id: str) -> UserEntity|None:
        row = get_by_google_id(self.rdbms_session, google_id)
        
        if row:
            return UserEntity(**row)
        return None
    
    def get_user_by_id(self, user_id: str) -> UserEntity|None:
        row = get_by_id(self.rdbms_session, user_id)
        
        if row:
            return UserEntity(**row)
        return None
    
    def get_or_create(self, user: UserCreate) -> UserEntity|None:
        row = get_by_google_id(self.rdbms_session, user.google_id)
        
        if row:
            return UserEntity(**row)
        
        else:
            return self.create_user(user)
        