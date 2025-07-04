import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from dotenv import load_dotenv
from fastapi import (
    Depends,
    HTTPException,
    status,
    Security,
)
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from sqlalchemy import (
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.app_models import User
from app.schemas import user_schemas
from pydantic import ValidationError
from app.db.db_connection import get_async_db
from app.redis_client import redis_client

load_dotenv()
from fastapi.security import SecurityScopes

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/user/sign-in",
    scopes={
        "user": "Basic user access",
        "author": "Author-level access",
    },
)


async def authenticate_user(
    username: str, password: str, async_session: AsyncSession, scopes: list[str]
) -> User | None:
    """
    Authenticate a user by validating their username, password.

    This function checks whether a user with the provided username exists in the
    database, verifies the password using the configured password context, and
    ensures the user's scopes match the required scopes.

    Args:
        `username (str)`: The username provided by the client.
        `password (str)`: The plain-text password provided by the client.
        `async_session (AsyncSession)`: The SQLAlchemy async session used to query the database.

    Returns:
        User | None: The authenticated `User` object if authentication is successful,
        or `None` if any validation fails.
    """
    user = (
        await async_session.execute(select(User).where(User.name == username))
    ).scalar_one_or_none()

    if user is None:
        return False
    if not pwd_context.verify(password, user.password):
        return False
    if not scopes:
        return False
    for scope in scopes:
        if scope not in user.scopes:
            return False
    return user


def create_access_token(expires_delta: timedelta, data: dict) -> str:
    """
    Generates a JWT access token containing the provided user data.

    The token is encoded using a secret key and a specified algorithm,
    and includes an expiration time based on the given time delta.

    Args:
        expires_delta (timedelta): The duration after which the token should expire.
        data (dict): The payload data to include in the token (e.g., user identity).

    Returns:
        str: The encoded JWT access token.
    """
    to_encode = data.copy()
    expires = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expires})
    access_token = jwt.encode(
        to_encode, os.getenv("SECRET"), algorithm=os.getenv("ALGORITHM")
    )
    return access_token


def create_refresh_token(expires_delta: timedelta, data: dict) -> str:
    """
    Returns an refresh token after encoding the username, the secret,
    and the algorithm.
    The expiration time for the refresh token is longer than the access
    token
    """
    to_encode = data.copy()
    expires = datetime.now(timezone.utc) + expires_delta
    jti = str(uuid.uuid4())
    to_encode.update({"exp": expires, "jti": jti})
    refresh_token = jwt.encode(
        to_encode, os.getenv("REFRESH_SECRET"), algorithm=os.getenv("ALGORITHM")
    )
    return refresh_token


async def get_current_user(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)],
    async_session: AsyncSession = Depends(get_async_db),
) -> User:
    """
    Retrieve and validate the currently authenticated user using the provided JWT token.

    This function performs the following steps:
    - Extracts and decodes the JWT token.
    - Validates the token signature and expiration.
    - Extracts the user's username and scopes from the token payload.
    - Fetches the user from the database using the username.
    - Ensures the token has all required scopes as specified by the route dependencies.

    Args:
        security_scopes (SecurityScopes): Required scopes for accessing the route.
        token (str): JWT access token provided via the Authorization header.
        async_session (AsyncSession): Dependency-injected SQLAlchemy asynchronous session.

    Returns:
        User: The authenticated user from the database.

    Raises:
        HTTPException 401:
            - If the token is missing, invalid, or expired.
            - If the username is not present in the token.
            - If the user does not exist in the database.
            - If the token lacks the required scopes for the requested resource.
    """

    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    try:
        payload = jwt.decode(
            token, os.getenv("SECRET"), algorithms=[os.getenv("ALGORITHM")]
        )
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", [])
        token_data = user_schemas.TokenData(scopes=token_scopes, username=username)
    except (InvalidTokenError, ValidationError):
        raise credentials_exception
    user_from_db = (
        await async_session.execute(
            select(User).where(User.name == token_data.username)
        )
    ).scalar_one_or_none()
    if user_from_db is None:
        raise credentials_exception
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )
    return user_from_db


async def get_current_active_user(
    current_user: Annotated[User, Security(get_current_user)],
) -> User:
    """
    Ensures the currently authenticated user is active.

    This function is typically used as a FastAPI dependency to enforce that
    only active users can access certain routes.

    Args:
        current_user (User): The authenticated user, provided by `get_current_user`.

    Returns:
        User: The current active user.

    Raises:
        HTTPException 400: If the user is not active.
    """

    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def black_list_token(jti: str, ttl: int) -> None:
    """
    blacklists the token using the token's id and setting
    and setting a time to live.
    """
    redis_client.setex(f"blacklist:{jti}", ttl, "true")


def is_token_blacklisted(jti: str) -> bool:
    """checks to see if the token is already blacklisted"""
    return redis_client.exists(f"blacklist:{jti}") == 1
