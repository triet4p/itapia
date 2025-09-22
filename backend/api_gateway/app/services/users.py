import uuid

from app.core.exceptions import DBError, NoDataError
from app.crud.users import create, get_by_google_id, get_by_id
from itapia_common.schemas.entities.users import UserCreate, UserEntity
from sqlalchemy.orm import Session


class UserService:
    """Service class for managing users."""

    def __init__(self, rdbms_session: Session):
        """Initialize UserService with a database session.

        Args:
            rdbms_session (Session): Database session for performing CRUD operations
        """
        self.rdbms_session = rdbms_session

    def create_user(self, user: UserCreate) -> UserEntity:
        """Create a new user in the database.

        Args:
            user (UserCreate): UserCreate object containing user information

        Returns:
            UserEntity: The created user

        Raises:
            DBError: If user creation fails
        """
        user_id = uuid.uuid4().hex
        user_entity = UserEntity(user_id=user_id, is_active=True, **user.model_dump())
        row = create(self.rdbms_session, user_entity.model_dump())

        if row:
            return UserEntity(**row)

        raise DBError(f"Can not create user with id {user_id}")

    def get_user_by_google_id(self, google_id: str) -> UserEntity:
        """Get a user by their Google ID.

        Args:
            google_id (str): Google ID of the user

        Returns:
            UserEntity: The user with the specified Google ID

        Raises:
            NoDataError: If no user is found with the given Google ID
        """
        row = get_by_google_id(self.rdbms_session, google_id)

        if row:
            return UserEntity(**row)
        raise NoDataError(f"Not found user with google id {google_id}")

    def get_user_by_id(self, user_id: str) -> UserEntity:
        """Get a user by their user ID.

        Args:
            user_id (str): ID of the user

        Returns:
            UserEntity: The user with the specified ID

        Raises:
            NoDataError: If no user is found with the given ID
        """
        row = get_by_id(self.rdbms_session, user_id)

        if row:
            return UserEntity(**row)
        raise NoDataError(f"Not found user with id {user_id}")

    def get_or_create(self, user: UserCreate) -> UserEntity:
        """Get a user by Google ID, or create a new user if not found.

        Args:
            user (UserCreate): UserCreate object containing user information

        Returns:
            UserEntity: The existing or newly created user
        """
        row = get_by_google_id(self.rdbms_session, user.google_id)

        if row:
            return UserEntity(**row)

        else:
            return self.create_user(user)
