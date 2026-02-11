from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
from datetime import datetime


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Retrieve a user from the database by their ID.

    Args:
        db (Session): SQLAlchemy database session
        user_id (int): The unique identifier of the user

    Returns:
        Optional[User]: The user object if found, None otherwise
    """
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Retrieve a user from the database by their email address.

    Args:
        db (Session): SQLAlchemy database session
        email (str): The email address to search for

    Returns:
        Optional[User]: The user object if found, None otherwise
    """
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Retrieve a user from the database by their username.

    Args:
        db (Session): SQLAlchemy database session
        username (str): The username to search for

    Returns:
        Optional[User]: The user object if found, None otherwise
    """
    return db.query(User).filter(User.username == username).first()


def authenticate_user(
    db: Session,
    username: str,
    password: str,
) -> Optional[User]:
    """Authenticate a user using their username/email and password.

    Attempts to authenticate using the provided credentials. First tries to
    find the user by username, then by email if username lookup fails.

    Args:
        db (Session): SQLAlchemy database session
        username (str): The username or email to authenticate with
        password (str): The plain text password to verify

    Returns:
        Optional[User]: Authenticated user object if successful, None otherwise
    """
    # Try to find user by username first
    user = get_user_by_username(db, username)

    # If not found, try by email
    if not user:
        user = get_user_by_email(db, username)

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


def create_user(db: Session, user: UserCreate) -> Optional[User]:
    """Create a new user in the database.

    Args:
        db (Session): SQLAlchemy database session
        user (UserCreate): Pydantic model containing the new user's information

    Returns:
        Optional[User]: Created user object if successful, None if creation
                       fails (e.g., due to duplicate email/username)

    Note:
        Handles password hashing automatically before storage
        Performs automatic rollback on integrity errors (ex: duplicate emails)
    """
    try:
        hashed_password = get_password_hash(user.password)
        db_user = User(
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            bio=user.bio,
            avatar_url=user.avatar_url,
            hashed_password=hashed_password,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        return None


def update_user(
    db: Session,
    user_id: int,
    user_update: UserUpdate,
) -> Optional[User]:
    """Update an existing user's information.

    Args:
        db (Session): SQLAlchemy database session
        user_id (int): The ID of the user to update
        user_update (UserUpdate): Pydantic model containing the fields to update

    Returns:
        Optional[User]: Updated user object if successful, None if user not found

    Note:
        Only updates fields that are provided in the user_update object
        Automatically updates the updated_at timestamp
    """
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None

    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)

    db_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_user)
    return db_user


def update_last_login(db: Session, user_id: int) -> None:
    """Update the last login timestamp for a user.

    Args:
        db (Session): SQLAlchemy database session
        user_id (int): The ID of the user to update

    Note:
        Silently fails if the user is not found
        Updates the last_login field to current UTC timestamp
    """
    db_user = get_user_by_id(db, user_id)
    if db_user:
        db_user.last_login = datetime.utcnow()
        db.commit()


def increment_user_generations(db: Session, user_id: int) -> None:
    """Increment the generation counters for a user.

    Increases both total_generations and monthly_generations counts by 1.

    Args:
        db (Session): SQLAlchemy database session
        user_id (int): The ID of the user to update

    Note:
        Silently fails if the user is not found
        Updates both total and monthly generation counts
    """
    db_user = get_user_by_id(db, user_id)
    if db_user:
        db_user.total_generations += 1
        db_user.monthly_generations += 1
        db.commit()


def reset_monthly_generations(db: Session, user_id: int) -> None:
    """Reset the monthly generation count for a user.

    Args:
        db (Session): SQLAlchemy database session
        user_id (int): The ID of the user to reset

    Note:
        Silently fails if the user is not found
        Sets monthly_generations to 0 and updates last_generation_reset timestamp
    """
    db_user = get_user_by_id(db, user_id)
    if db_user:
        db_user.monthly_generations = 0
        db_user.last_generation_reset = datetime.utcnow()
        db.commit()
