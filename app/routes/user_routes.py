from typing import Annotated
from decimal import Decimal
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    Header,
    HTTPException,
    Security,
    status,
    Query,
)
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_async_db
from app.models.app_models import User, Author
from app.repositories.user_logic import get_current_active_user, get_current_user
from app.repositories.user_repository import UserRepository
from app.schemas import user_schemas
from app.services.user_service import UserService
import uuid

router = APIRouter(prefix="/api/v1/user", tags=["routes for the user and author"])


@router.post(
    "/sign-up",
    response_model=user_schemas.SignUpSchemaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def user_sign_up(
    user_data_sign_up: user_schemas.UserAuthorSignUpSchema,
    background_tasks: BackgroundTasks,
    async_session: AsyncSession = Depends(get_async_db),
) -> user_schemas.SignUpSchemaResponse:
    """
    Register a new user account.

    This endpoint creates a new user by:
    - Validating the provided name, email, password, and scopes.
    - Hashing the user's password before storing it in the database.
    - Saving the user to the database.
    - Sending a welcome email in the background.

    Args:
        user_data (UserAuthorSignUpSchema): The input schema containing name, email, password, and scopes.
        background_tasks (BackgroundTasks): FastAPI's background task manager for sending async emails.
        async_session (AsyncSession): Dependency-injected asynchronous SQLAlchemy session.

    Returns:
        SignUpSchemaResponse: A message confirming successful account creation.

    Raises:
        HTTPException 400: If a database constraint (e.g., unique email) fails.
        HTTPException 500: For any unexpected internal server error.
    """

    try:
        repo = UserRepository(
            background_tasks=background_tasks,
            async_session=async_session,
            user_data_sign_up=user_data_sign_up,
        )
        service = UserService(repo)
        return await service.create_user_account()
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An error occurred: {str(e.orig)}",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.post(
    "/sign-in", status_code=status.HTTP_200_OK, response_model=user_schemas.Token
)
async def login_user_for_tokens(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    async_session: AsyncSession = Depends(get_async_db),
) -> user_schemas.Token:
    """
    Authenticate a user and issue access and refresh tokens.

    This endpoint validates user credentials provided through an OAuth2-compatible form
    and issues a JWT access token (valid for 30 minutes) and a refresh token (valid for 8 hours).
    Tokens include the user's scopes for authorization purposes.

    Args:
        form_data (OAuth2PasswordRequestForm): Form containing `username`, `password`, and optional `scopes`.
        async_session (AsyncSession): Asynchronous database session dependency.

    Returns:
        Token: A response schema containing the bearer token type, access token, and refresh token.

    Raises:
        HTTPException 400: If a database integrity error occurs.
        HTTPException 401: If the user credentials are invalid.
        HTTPException 500: If an unexpected server error occurs.
    """

    try:
        repo = UserRepository(form_data=form_data, async_session=async_session)
        service = UserService(repo)
        return await service.login_user()
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An error occurred: {str(e.orig)}",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    response_model=user_schemas.LogoutResponseSchema,
)
async def logout_user(
    token: Annotated[str, Header()],
) -> user_schemas.LogoutResponseSchema:
    """
    Log out the user by blacklisting their JWT token.

    This endpoint receives a JWT token via the `Authorization` header and invalidates it
    by adding its unique identifier (JTI) to a Redis blacklist. This prevents any future
    use of the token, effectively logging the user out.

    Args:
        token (str): The JWT token passed in the request header.

    Returns:
        LogoutResponseSchema: A confirmation message indicating successful logout.

    Raises:
        HTTPException 400: If the token is invalid or already blacklisted.
        HTTPException 500: If an unexpected error occurs during processing.
    """

    try:
        repo = UserRepository(token=token)
        service = UserService(repo)
        return await service.login_out_user()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.post(
    "/new_access_token",
    status_code=status.HTTP_200_OK,
    response_model=user_schemas.NewAccessTokenResponseSchema,
)
async def get_new_token_from_refresh_token(
    token: Annotated[str, Header()], async_session: AsyncSession = Depends(get_async_db)
) -> user_schemas.NewAccessTokenResponseSchema:
    """
    Generate a new access token using a valid refresh token.

    This endpoint decodes and verifies the provided refresh token from the request headers.
    If the token is valid and not blacklisted, a new access token is generated and returned.

    Args:
        token (str): The refresh token provided in the request headers.
        async_session (AsyncSession): SQLAlchemy async session for database operations.

    Returns:
        NewAccessTokenResponseSchema: The response containing the new access token.

    Raises:
        HTTPException 401: If the refresh token is invalid, expired, or revoked.
        HTTPException 400: If required token claims are missing or the user does not exist.
        HTTPException 500: For any unexpected server error.
    """

    try:
        repo = UserRepository(async_session=async_session, token=token)
        service = UserService(repo)
        return await service.get_access_token_from_refresh_token()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.patch(
    "/update-password",
    status_code=status.HTTP_200_OK,
    response_model=user_schemas.UpdatePasswordResponseSchema,
)
async def update_user_author_password(
    update_password_data: user_schemas.UpdatePassword,
    user: Annotated[User, Depends(get_current_active_user)],
    async_session: AsyncSession = Depends(get_async_db),
) -> user_schemas.UpdatePasswordResponseSchema:
    """
    Endpoint to update the authenticated user's password.

    This endpoint allows an authenticated user with the appropriate scopes ('user' or 'author')
    to update their password securely.

    Args:
        user (User): The currently authenticated user, injected via dependency.
        update_password_data (UpdatePassword): The new password data validated by Pydantic schema.
        async_session (AsyncSession): Async SQLAlchemy session injected via dependency.

    Raises:
        HTTPException 401 Unauthorized: If the user does not have the required scopes.
        HTTPException 400 Bad Request: For validation or update errors (handled in the service).
        HTTPException 500 Internal Server Error: For unexpected errors during password update.

    Returns:
        UpdatePasswordResponseSchema: Response confirming successful password update.
    """

    if not ("user" in user.scopes or "author" in user.scopes):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
        )

    try:
        repo = UserRepository(
            async_session=async_session,
            update_password_data=update_password_data,
            user=user,
        )
        service = UserService(repo)
        return await service.update_user_author_password()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.patch(
    "/deactivate-account",
    status_code=status.HTTP_200_OK,
    response_model=user_schemas.DeactivateAccountResponseSchema,
)
async def deactivate_current_account(
    user: Annotated[User, Depends(get_current_active_user)],
    async_session: AsyncSession = Depends(get_async_db),
) -> user_schemas.DeactivateAccountResponseSchema:
    """
    Deactivate the currently authenticated user account.

    Only users with the "user" or "author" scope are allowed to perform this action.
    The method initializes the repository and service layers to handle the deactivation
    logic, and returns a success response on completion.

    Args:
        user (User): The currently authenticated user, injected via dependency.
        async_session (AsyncSession): SQLAlchemy async database session.

    Returns:
        DeactivateAccountResponseSchema: A response indicating successful deactivation.

    Raises:
        HTTPException:
            - 401 if the user lacks required scopes.
            - 500 if an unexpected error occurs during deactivation.
    """

    if not ("user" in user.scopes or "author" in user.scopes):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
        )

    try:
        repo = UserRepository(user=user, async_session=async_session)
        service = UserService(repo)
        return await service.deactivate_account()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.patch(
    "/reactivate-account",
    status_code=status.HTTP_200_OK,
    response_model=user_schemas.ReactivateAccountResponseSchema,
)
async def reactivate_current_account(
    user: Annotated[User, Depends(get_current_user)],
    async_session: AsyncSession = Depends(get_async_db),
) -> user_schemas.ReactivateAccountResponseSchema:
    """
    Reactivate the currently authenticated user's account.

    This endpoint allows a deactivated user to reactivate their account,
    provided they have the "user" or "author" scope.

    Args:
        user (User): The currently authenticated user, resolved from the access token.
        async_session (AsyncSession): The SQLAlchemy async session for DB operations.

    Returns:
        ReactivateAccountResponseSchema: A response schema confirming reactivation.

    Raises:
        HTTPException:
            - 401 Unauthorized: If the user lacks "user" or "author" scope.
            - 500 Internal Server Error: If an unexpected error occurs during reactivation.
    """

    if not ("user" in user.scopes or "author" in user.scopes):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
        )

    try:
        repo = UserRepository(user=user, async_session=async_session)
        service = UserService(repo)
        return await service.reactivate_account()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.patch(
    "/update-email",
    status_code=status.HTTP_200_OK,
    response_model=user_schemas.UpdateEmailResponseSchema,
)
async def update_user_author_email(
    new_email: Annotated[user_schemas.UpdateEmail, Body()],
    user: Annotated[User, Depends(get_current_active_user)],
    async_session: AsyncSession = Depends(get_async_db),
) -> user_schemas.UpdateEmailResponseSchema:
    """
    Update the email address of the currently authenticated user.

    This endpoint allows users with the "user" or "author" scope to update
    their registered email address. The new email is validated and passed
    to the service layer for processing.

    Args:
        new_email (UpdateEmail): A Pydantic model containing the new email address.
        user (User): The currently authenticated user.
        async_session (AsyncSession): SQLAlchemy async session used for database operations.

    Returns:
        UpdateEmailResponseSchema: A response schema confirming the email update.

    Raises:
        HTTPException:
            - 401 Unauthorized: If the user lacks the required "user" or "author" scope.
            - 500 Internal Server Error: If an unexpected error occurs during the update process.
    """

    if not ("user" in user.scopes or "author" in user.scopes):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
        )

    try:
        repo = UserRepository(
            user=user, async_session=async_session, update_email=new_email
        )
        service = UserService(repo)
        return await service.update_email()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.patch(
    "/update-name",
    status_code=status.HTTP_200_OK,
    response_model=user_schemas.UpdateNameResponseSchema,
)
async def update_user_author_name(
    new_name: Annotated[user_schemas.UpdateName, Body()],
    user: Annotated[User, Depends(get_current_active_user)],
    async_session: AsyncSession = Depends(get_async_db),
) -> user_schemas.UpdateNameResponseSchema:
    """
    Update the full name of the currently authenticated user.

    This endpoint allows users with the "user" or "author" scope to change their
    first and/or last name. The provided data is validated and passed to the
    service layer for persistence.

    Args:
        new_name (UpdateName): A Pydantic model containing the new name data.
        user (User): The currently authenticated user.
        async_session (AsyncSession): SQLAlchemy async session used for database operations.

    Returns:
        UpdateNameResponseSchema: A response schema confirming the updated name.

    Raises:
        HTTPException:
            - 401 Unauthorized: If the user lacks the required "user" or "author" scope.
            - 500 Internal Server Error: If an unexpected error occurs during the update process.
    """

    if not ("user" in user.scopes or "author" in user.scopes):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
        )

    try:
        repo = UserRepository(
            user=user, async_session=async_session, update_name=new_name
        )
        service = UserService(repo)
        return await service.update_name()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.patch(
    "/upload-photo",
    status_code=status.HTTP_200_OK,
    response_model=user_schemas.UpdateNameResponseSchema,
)
async def upload_photo(
    user: Annotated[User, Depends(get_current_active_user)],
    photo: user_schemas.UploadImageSchema = Depends(),
    async_session: AsyncSession = Depends(get_async_db),
) -> user_schemas.UploadImageResponseSchema:
    """
    Upload a new profile photo for the authenticated user.

    This endpoint allows authenticated users with either the "user" or "author" scope
    to upload or update their profile photo. The uploaded image is received via form data
    and processed by the UserService, which stores it (e.g., in AWS S3 or another cloud provider).

    Args:
        user (User): The currently authenticated user.
        photo (UploadImageSchema): The uploaded photo file, parsed from form data.
        async_session (AsyncSession): SQLAlchemy async database session.

    Returns:
        UploadImageResponseSchema: Contains metadata or URL of the uploaded image.

    Raises:
        HTTPException (401): If the user does not have the required scope.
        HTTPException (500): If an unexpected error occurs during upload.
    """

    if not ("user" in user.scopes or "author" in user.scopes):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
        )

    try:
        repo = UserRepository(user=user, photo=photo, async_session=async_session)
        service = UserService(repo)
        return await service.upload_profile_image()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.post(
    "/remove-account",
    status_code=status.HTTP_200_OK,
    response_model=user_schemas.RemovedUserAuthorAccountSchema,
)
async def remove_user_author_account(
    user: User = Depends(get_current_active_user),
    async_session: AsyncSession = Depends(get_async_db),
) -> user_schemas.RemovedUserAuthorAccountSchema:
    """
    Endpoint to remove both the user and the associated author account.

    Args:
        user (User): The currently authenticated user, injected via dependency.
        async_session (AsyncSession): Async SQLAlchemy session, injected via dependency.

    Returns:
        RemovedUserAuthorAccountSchema: Schema indicating successful removal of user and author account.

    Raises:
        HTTPException 400: If a database integrity error occurs (e.g., foreign key constraint).
        HTTPException 500: For any unexpected internal server errors.
    """

    try:
        repo = UserRepository(user=user, async_session=async_session)
        service = UserService(repo)
        return await service.remove_both_user_author_account()
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An error occurred: {str(e.orig)}",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.patch(
    "/update-user-balance",
    status_code=status.HTTP_200_OK,
    response_model=user_schemas.BalanceUpdateSchemaResponse,
)
async def update_user_balance(
    user: Annotated[User, Depends(get_current_active_user)],
    balance: Annotated[user_schemas.BalanceSchemaIn, Body()],
    async_session: AsyncSession = Depends(get_async_db),
) -> user_schemas.BalanceUpdateSchemaResponse:
    """
    Update the balance of the currently authenticated user.

    This endpoint allows users with the "user" or "author" scope to update their
    balance. The new balance must be provided as a query parameter and must be a
    non-negative decimal number with up to 6 digits and 2 decimal places.

    Args:
        user (User): The currently authenticated user, injected via dependency.
        balance (BalanceSchemaIn): The new balance, validated by a Pydantic schema, provided via query parameters.
        async_session (AsyncSession): The asynchronous SQLAlchemy session dependency.

    Returns:
        BalanceUpdateSchemaResponse: A response schema containing the updated balance.

    Raises:
        HTTPException (401): If the user does not have the required permissions.
        HTTPException (500): If an unexpected error occurs during the update process.
    """
    if not ("user" in user.scopes or "author" in user.scopes):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not enough permissions",
        )
    try:
        repo = UserRepository(user=user, async_session=async_session, balance=balance)
        service = UserService(repo)
        return await service.update_balance()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.get(
    "/history",
    status_code=status.HTTP_200_OK,
)
async def get_user_order_history(
    user_id: Annotated[uuid.UUID, Query()],
    async_session: AsyncSession = Depends(get_async_db),
):
    try:
        repo = UserRepository(async_session=async_session, user_id=user_id)
        service = UserService(repo)
        return await service.user_order_history()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.get(
    "/top-spent",
    status_code=status.HTTP_200_OK,
)
async def get_user_order_history(
    amount_spent: Annotated[Decimal, Query(decimal_places=2, max_digits=6)],
    async_session: AsyncSession = Depends(get_async_db),
):
    try:
        repo = UserRepository(async_session=async_session, amount_spent=amount_spent)
        service = UserService(repo)
        return await service.users_that_spent_over_an_amount()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )
