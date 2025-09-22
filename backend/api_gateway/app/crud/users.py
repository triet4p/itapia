from sqlalchemy import text
from sqlalchemy.orm import Session


def get_by_google_id(rdbms_session: Session, google_id: str):
    """Get a user by their Google ID."""
    query = text("SELECT * FROM users WHERE google_id = :google_id and is_active=true")
    result = rdbms_session.execute(query, {"google_id": google_id})
    user_row = result.mappings().first()
    return user_row


def get_by_id(rdbms_session: Session, user_id: str):
    """Get a user by their user ID."""
    query = text("SELECT * FROM users WHERE user_id = :user_id and is_active=true")
    result = rdbms_session.execute(query, {"user_id": user_id})
    user_row = result.mappings().first()
    return user_row


def create(rdbms_session: Session, user_data: dict[str, any]):
    """
    Create a new user.
    """
    query = text(
        """
        INSERT INTO users (user_id, email, full_name, avatar_url, google_id, is_active)
        VALUES (:user_id, :email, :full_name, :avatar_url, :google_id, :is_active)
        RETURNING *
    """
    )
    result = rdbms_session.execute(query, user_data)
    created_user_row = result.mappings().first()
    rdbms_session.commit()
    return created_user_row
