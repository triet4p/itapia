# itapia_common/dblib/crud/profiles.py

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

def get_by_id(db: Session, *, profile_id: str):
    """Lấy một profile cụ thể thuộc về một user."""
    query = text("SELECT * FROM investment_profiles WHERE profile_id = :profile_id")
    result = db.execute(query, {"profile_id": profile_id})
    return result.mappings().first()

def get_by_name(db: Session, *, profile_name: str, user_id: str):
    """Lấy một profile cụ thể thuộc về một user."""
    query = text("SELECT * FROM investment_profiles WHERE profile_name = :profile_name AND user_id = :user_id")
    result = db.execute(query, {"profile_name": profile_name, "user_id": user_id})
    return result.mappings().first()

def get_multi_by_user(db: Session, *, user_id: str):
    """Lấy danh sách các profile của một user."""
    query = text("SELECT * FROM investment_profiles WHERE user_id = :user_id ORDER BY created_at DESC")
    result = db.execute(query, {"user_id": user_id})
    return result.mappings().all()

def create(db: Session, *, profile_data: Dict[str, Any]):
    """Tạo một investment profile mới."""
    query = text("""
        INSERT INTO investment_profiles (
            profile_id, user_id, profile_name, description, 
            risk_tolerance, invest_goal, knowledge_exp, capital_income, personal_prefer,
            use_in_advisor, is_default, updated_at
        )
        VALUES (
            :profile_id, :user_id, :profile_name, :description, 
            :risk_tolerance, :invest_goal, :knowledge_exp, :capital_income, :personal_prefer,
            :use_in_advisor, :is_default, NOW()
        )
        RETURNING *
    """)
    result = db.execute(query, profile_data)
    created_row = result.mappings().first()
    db.commit()
    return created_row

def update(db: Session, *, profile_id: str, update_data: Dict[str, Any]):
    """Cập nhật một investment profile."""
    # Xây dựng phần SET của câu lệnh SQL một cách động
    set_clause = ", ".join([f"{key} = :{key}" for key in update_data.keys()])
    
    # Luôn cập nhật trường updated_at
    set_clause += ", updated_at = NOW()"

    query = text(f"""
        UPDATE investment_profiles
        SET {set_clause}
        WHERE profile_id = :profile_id
        RETURNING *
    """)
    
    # Kết hợp data cần update với profile_id
    params = {**update_data, "profile_id": profile_id}
    
    result = db.execute(query, params)
    updated_row = result.mappings().first()
    db.commit()
    return updated_row

def remove(db: Session, *, profile_id: str):
    """Xóa một investment profile."""
    query = text("DELETE FROM investment_profiles WHERE profile_id = :profile_id RETURNING *")
    result = db.execute(query, {"profile_id": profile_id})
    deleted_row = result.mappings().first()
    db.commit()
    return deleted_row