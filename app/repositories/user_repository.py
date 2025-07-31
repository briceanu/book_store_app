import os, shutil, uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import jwt
from fastapi import BackgroundTasks, HTTPException, status, UploadFile
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from jwt import ExpiredSignatureError
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from sqlalchemy import select, update, delete, func, desc, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only

from app.interfaces.user_interface import AbstractUserInterface
from app.models.app_models import User, Author, Order, OrderItem, Book
from app.redis_client import redis_client
from app.repositories import user_logic
from app.repositories.user_logic import black_list_token, is_token_blacklisted
from app.schemas import user_schemas, author_schemas
from app.send_email import send_in_background
from dataclasses import dataclass

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@dataclass
class UserRepository(AbstractUserInterface):
    """
    Repository class for managing user and author operations.

    This class encapsulates all logic related to user and author account management,
    including registration, authentication, profile updates, password changes,
    and media uploads.

    Attributes:
        async_session (AsyncSession | None): SQLAlchemy async session for database operations.
        user_data_sign_up (UserAuthorSignUpSchema | None): Schema for user/author registration.
        background_tasks (BackgroundTasks | None): FastAPI background task manager for async jobs.
        form_data (OAuth2PasswordRequestForm | None): OAuth2 credentials used for login.
        token (TokenData | None): JWT token data used for authenticated requests.
        update_password_data (UpdatePassword | None): Schema for updating user password.
        user (User | None): The current authenticated user.
        author (Author | None): The current authenticated author (if applicable).
        update_email (UpdateEmail | None): Schema for updating user email.
        update_name (UpdateName | None): Schema for updating user name.
        author_description (AuthorDescription | None): Schema for updating author's bio/description.
        photo (UploadFile | None): Profile image uploaded by the user or author.
    """

    async_session: AsyncSession | None = None
    user_data_sign_up: user_schemas.UserAuthorSignUpSchema | None = None
    background_tasks: BackgroundTasks | None = None
    form_data: OAuth2PasswordRequestForm | None = None
    token: user_schemas.TokenData | None = None
    update_password_data: user_schemas.UpdatePassword | None = None
    user: User | None = None
    update_email: user_schemas.UpdateEmail | None = None
    update_name: user_schemas.UpdateName | None = None
    author_description: author_schemas.AuthorDescription | None = None
    author: Author | None = None
    photo: UploadFile | None = None
    balance: user_schemas.BalanceSchemaIn | None = None
    user_id: uuid.UUID | None = None
    amount_spent: Decimal | None = None

    async def sign_up(self) -> user_schemas.SignUpSchemaResponse:
        """
        Register a new user or author based on scopes,
        inserting into appropriate tables using ORM.
        """

        hashed_password = pwd_context.hash(self.user_data_sign_up.password)
        common_fields = {
            "name": self.user_data_sign_up.name,
            "password": hashed_password,
            "email": self.user_data_sign_up.email,
            "is_active": True,
            "scopes": self.user_data_sign_up.scopes,
        }
        if "author" in self.user_data_sign_up.scopes:
            new_user = Author(**common_fields)
        else:
            new_user = User(**common_fields)
        self.async_session.add(new_user)
        await self.async_session.commit()

        await send_in_background(
            [self.user_data_sign_up.email],
            self.background_tasks,
            self.user_data_sign_up.name,
        )

        return user_schemas.SignUpSchemaResponse(
            success="Your account has been created."
        )

    async def sign_in(self) -> user_schemas.Token:
        """
        Authenticate a user and generate JWT access and refresh tokens.

        - Verifies user credentials via `user_logic.authenticate_user`.
        - Raises HTTP 401 Unauthorized if authentication fails.
        - Creates an access token valid for 30 minutes and a refresh token valid for 8 hours.
        - Includes user scopes in the token payload for authorization purposes.

        Returns:
            Token: An object containing the bearer token type, access token, and refresh token.

        Raises:
            HTTPException: If username or password is invalid (401 Unauthorized).
        """
        unauthorized_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        user = await user_logic.authenticate_user(
            self.form_data.username,
            self.form_data.password,
            self.async_session,
            self.form_data.scopes,
        )
        if not user:
            raise unauthorized_exception
        access_token = user_logic.create_access_token(
            timedelta(minutes=30),
            data={"sub": self.form_data.username, "scopes": user.scopes},
        )
        refresh_token = user_logic.create_refresh_token(
            timedelta(hours=8),
            data={"sub": self.form_data.username, "scopes": user.scopes},
        )
        return user_schemas.Token(
            token_type="bearer",
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def logout(self) -> user_schemas.LogoutResponseSchema:
        """
        Logs out the user by blacklisting the provided JWT token.

        This function extracts the unique token identifier (JTI) from the given
        JWT, calculates its remaining time-to-live (TTL), and stores it in a
        Redis blacklist. This ensures that the token can no longer be used for
        authentication, effectively logging the user out.

        Args:
            token (str): The JWT access or refresh token to be invalidated.

        Returns:
            dict: A confirmation message indicating successful logout.

        Raises:
            HTTPException: If the token is invalid or malformed.
        """

        invalid_token = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
        )
        try:
            payload = jwt.decode(
                self.token,
                os.getenv("REFRESH_SECRET"),
                algorithms=os.getenv("ALGORITHM"),
            )
            jti = payload.get("jti")
            exp = payload.get("exp")
            if not jti or not exp:
                raise invalid_token
            if redis_client.exists(f"blacklist:{jti}") == 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Token already blacklisted",
                )
            ttl = exp - int(datetime.now(timezone.utc).timestamp())
            black_list_token(jti, ttl)
            return user_schemas.LogoutResponseSchema(success="Logged out successfully")

        except InvalidTokenError:
            raise invalid_token

    async def create_access_token_from_refresh(
        self,
    ) -> user_schemas.NewAccessTokenResponseSchema:
        """
        Generate a new access token from a valid refresh token.

        This method performs the following steps:
        1. Decodes the provided refresh JWT token using the REFRESH_SECRET and algorithm.
        2. Validates the existence of the token's JWT ID (`jti`) and associated user (`sub`).
        3. Checks whether the refresh token has been blacklisted.
        4. Verifies that the token's scopes are present and still permitted for the user.
        5. Issues a new access token with the user's current scopes and returns it.

        Returns:
            NewAccessTokenResponseSchema: A Pydantic response schema containing the new access token.

        Raises:
            HTTPException (400): If the token is malformed or the user doesn't exist.
            HTTPException (401): If the token is expired, revoked, or permissions are insufficient.
        """
        try:
            payload = jwt.decode(
                self.token,
                os.getenv("REFRESH_SECRET"),
                algorithms=os.getenv("ALGORITHM"),
            )
            jti = payload.get("jti")
            token_scopes = payload.get("scopes", [])
            username = payload.get("sub")
            # If the token does not contain a jwt id or the user is
            # not a valid user saved in the db raise  400 error
            user_in_db = (
                await self.async_session.execute(
                    select(User)
                    .options(load_only(User.name, User.scopes))
                    .where(User.name == username)
                )
            ).scalar_one_or_none()
            if not jti or not user_in_db:
                raise HTTPException(status_code=400, detail="Invalid refresh token")

            if is_token_blacklisted(jti) == 1:
                raise HTTPException(status_code=401, detail="Token has been revoked")
            if not token_scopes:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not enough permissions",
                )
            for scope in token_scopes:
                if scope not in user_in_db.scopes:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Not enough permissions",
                    )
            access_token = user_logic.create_access_token(
                timedelta(minutes=30),
                data={"sub": user_in_db.name, "scopes": user_in_db.scopes},
            )
            return user_schemas.NewAccessTokenResponseSchema(access_token=access_token)
        except ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Refresh token has expired")
        except InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

    async def update_user_author_password(
        self,
    ) -> user_schemas.UpdatePasswordResponseSchema:
        """
        Update the password for the current user in the database.

        This method hashes the new password provided in `self.update_password_data.new_password`
        and updates the `password` field for the user identified by `self.user.name`.
        After executing the update query, the changes are committed to the database.

        Returns:
            UpdateUsernameResponseSchema: A response schema indicating that the password was updated successfully.

        Raises:
            HTTPException:
                - Raises a 400 Bad Request error if no rows were updated, indicating the password could not be changed
                (possibly because the user was not found).
        """

        update_password = await self.async_session.execute(
            update(User)
            .values(password=pwd_context.hash(self.update_password_data.new_password))
            .where(User.name == self.user.name)
        )
        if update_password.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not update password",
            )
        await self.async_session.commit()
        return user_schemas.UpdatePasswordResponseSchema(
            success="Update password successfully."
        )

    async def deactivate_account(self) -> user_schemas.DeactivateAccountResponseSchema:
        """
        Deactivates the current user's account by setting `is_active` to False.

        This method modifies the `is_active` field on the user instance to indicate
        the account is no longer active, then commits the change to the database.

        Returns:
            DeactivateAccountResponseSchema: A response object indicating successful deactivation.
        """

        stmt = update(User).values(is_active=False).where(User.name == self.user.name)

        result = await self.async_session.execute(stmt)
        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not deactivate account",
            )
        await self.async_session.commit()
        return user_schemas.DeactivateAccountResponseSchema(
            success="Account deactivated."
        )

    async def reactivate_account(self) -> user_schemas.ReactivateAccountResponseSchema:
        """
        Reactivates a deactivated user account by setting `is_active` to True.

        This method first checks if the account is already active. If so, it raises an
        HTTP 400 error. Otherwise, it updates the user's `is_active` field in the database
        using a SQL UPDATE statement. If the update affects no rows, an error is raised.
        Upon success, the change is committed and a response schema is returned.

        Raises:
            HTTPException: If the account is already active or the update fails.

        Returns:
            ReactivateAccountResponseSchema: A response indicating successful reactivation.
        """

        if self.user.is_active == True:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Account already active"
            )

        stmt = update(User).values(is_active=True).where(User.name == self.user.name)
        result = await self.async_session.execute(stmt)
        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not reactivate account",
            )
        await self.async_session.commit()
        return user_schemas.ReactivateAccountResponseSchema(
            success="Account reactivated."
        )

    async def update_user_author_email(self) -> user_schemas.UpdateEmailResponseSchema:
        """
        Updates the email address of the current user in the database.

        Executes an asynchronous SQL UPDATE statement to set the user's email
        to the new email provided in `self.update_email.new_email`. If no rows
        are affected by the update (i.e., the user does not exist or update fails),
        raises an HTTP 400 error.

        Returns:
            UpdateEmailResponseSchema: A response schema indicating successful email update.

        Raises:
            HTTPException: If the email update fails (no rows affected).
        """

        stmt = (
            update(User)
            .values(email=self.update_email.new_email)
            .where(User.name == self.user.name)
        )
        result = await self.async_session.execute(stmt)
        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not update email",
            )
        await self.async_session.commit()
        return user_schemas.UpdateEmailResponseSchema(success="Email updated.")

    async def update_user_author_name(self) -> user_schemas.UpdateNameResponseSchema:
        """
        Updates the name of the current user in the database.

        Executes an asynchronous SQL UPDATE statement to set the user's name
        to the new name provided in `self.update_name.name`. If no rows
        are affected by the update (i.e., the user does not exist or update fails),
        raises an HTTP 400 error.

        Returns:
            UpdateNameResponseSchema: A response schema indicating successful name update.

        Raises:
            HTTPException: If the name update fails (no rows affected).
        """

        stmt = (
            update(User)
            .values(name=self.update_name.new_name)
            .where(User.name == self.user.name)
        )
        result = await self.async_session.execute(stmt)
        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not update name",
            )
        await self.async_session.commit()
        return user_schemas.UpdateNameResponseSchema(success="Name updated.")

    async def upload_user_author_image(self) -> user_schemas.UploadImageResponseSchema:
        """
        Uploads a user's profile image, replacing the old one if it exists.
        Enforces a 3.5 MB file size limit.

        Args:
            image (UploadFile): The image file uploaded via multipart/form-data.
            user (User): The user uploading the image.
            async_session (AsyncSession): SQLAlchemy async session.

        Returns:
            dict: Success message.
        """
        # in a production application the image bytes are saved on a cloud server
        MAX_FILE_SIZE = 3.5 * 1024 * 1024

        # --- Check file size ---
        self.photo.image.file.seek(0, os.SEEK_END)
        file_size = self.photo.image.file.tell()
        self.photo.image.file.seek(0)  # Reset file pointer

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds 3.5 MB limit",
            )

        # --- Create user image directory ---
        base_dir = "app/users_images"
        img_dir = os.path.join(base_dir, self.user.name)
        os.makedirs(img_dir, exist_ok=True)

        # --- Delete old photo if it exists ---
        user_photo = (
            await self.async_session.execute(
                select(User.image_url).where(User.id == self.user.id)
            )
        ).scalar_one_or_none()

        if user_photo and os.path.exists(user_photo):
            try:
                os.remove(user_photo)
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Failed to remove old photo: {str(e)}"
                )
        # writing the file on the server
        file_path = os.path.join(img_dir, self.photo.image.filename)

        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(self.photo.image.file, buffer)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred while saving the file: {str(e)}",
            )

        # save the image_url path in the db
        stmt = (
            update(User).values(image_url=file_path).where(User.name == self.user.name)
        )
        result = await self.async_session.execute(stmt)
        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed"
            )

        await self.async_session.commit()

        return user_schemas.UploadImageResponseSchema(success="Image uploaded.")

    async def remove_account(self) -> user_schemas.RemovedUserAuthorAccountSchema:
        """
        Deletes the currently authenticated user's account based on their username.

        Returns:
            RemovedUserAuthorAccountSchema: A response indicating successful account removal.

        Raises:
            HTTPException: If no user with the specified name exists in the database.
        """

        stmt = delete(User).where(User.name == self.user.name)
        result = await self.async_session.execute(stmt)
        await self.async_session.commit()

        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No account with the name {self.user.name} found.",
            )
        return user_schemas.RemovedUserAuthorAccountSchema(success="Account reomved.")

    async def update_user_balance(self) -> user_schemas.BalanceUpdateSchemaResponse:
        """
        Updates the balance of the currently authenticated user.

        This method performs an update on the User table, setting the user's balance
        to the new value provided in `self.balance.value`, based on their username.
        If no user is found with the given name, an HTTP 400 error is raised.

        Returns:
            BalanceUpdateSchemaResponse: A response object indicating the balance update
            was successful.

        Raises:
            HTTPException: If the user is not found or the update operation affects no rows.
        """

        stmt = (
            update(User)
            .where(User.name == self.user.name)
            .values(balance=self.balance.value)
        )
        result = await self.async_session.execute(stmt)
        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not update balance",
            )
        await self.async_session.commit()
        return user_schemas.BalanceUpdateSchemaResponse(success="Balance updated.")

    async def order_history_summary_for_user(self):
        stmt = (
            select(
                Order.order_id,
                func.coalesce(func.sum(OrderItem.quantity).label("quantity"), 0),
                func.coalesce(
                    func.sum(OrderItem.items_total_price).label("total_price"), 0
                ),
            )
            .where(Order.user_id == self.user_id)
            .join(OrderItem, Order.order_id == OrderItem.order_id)
            .group_by(
                Order.order_id,
            )
        )
        result = (await self.async_session.execute(stmt)).all()
        return [
            {"order id": order_id, "quantity": quantity, "total price": total_price}
            for order_id, quantity, total_price in result
        ]

    # High-Spending Users
    # Identify users who have spent more than a specific amount (e.g., $500) in total orders.
    async def high_spending_users(self):
        """
        Retrieve users who have spent more than a specified amount on orders.

        This method calculates the total amount each user has spent by summing
        the `items_total_price` of all their order items. It then filters to include
        only those users whose total spending exceeds `self.amount_spent`.
        The results are ordered in descending order of total amount spent.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each containing the user's name
            and their total amount spent, formatted as:
                [{'user name': <str>, 'amount spent': <float>}]
        """
        amount_spent_by_client = func.coalesce(
            func.sum(OrderItem.items_total_price), 0
        ).label("client_amount_spent")
        stmt = (
            select(User.name, amount_spent_by_client)
            .join(Order, Order.user_id == User.id)
            .join(OrderItem, OrderItem.order_id == Order.order_id)
            .group_by(User.id,User.name)
            .having(amount_spent_by_client > self.amount_spent)
            .order_by(desc(amount_spent_by_client))
        )
        result = (await self.async_session.execute(stmt)).all()
        return [{"user name": name, "amount spent": amount} for name, amount in result]
 