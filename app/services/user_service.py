from app.repositories.user_repository import UserRepository
from app.schemas import user_schemas


class UserService:
    """
    Service layer for user-related operations.

    Acts as an intermediary between the API layer and the user repository,
    handling user account creation and login logic asynchronously.

    Attributes:
        repository (UserRepository): Instance of UserRepository for data access.
    """

    def __init__(self, repository: UserRepository):
        """
        Initialize the UserService with a UserRepository instance.

        Args:
            repository (UserRepository): The repository responsible for user data operations.
        """
        self.repository = repository

    async def create_user_account(self) -> user_schemas.SignUpSchemaResponse:
        """
        Create a new user account asynchronously.

        Returns:
            Result of the repository's sign_up method, typically a user instance or confirmation.
        """
        return await self.repository.sign_up()

    async def login_user(self) -> user_schemas.Token:
        """
        Authenticate and log in a user asynchronously.

        Returns:
            Result of the repository's sign_in method, typically authentication tokens or user info.
        """
        return await self.repository.sign_in()

    async def login_out_user(self) -> user_schemas.LogoutResponseSchema:
        """
        Logs out the currently authenticated user.

        This method delegates the logout logic to the repository layer,
        which may handle tasks such as invalidating tokens, clearing session data,
        or updating user state in the database.

        Returns:
            Any: The result of the logout operation from the repository.
        """
        return await self.repository.logout()

    async def get_access_token_from_refresh_token(
        self,
    ) -> user_schemas.NewAccessTokenResponseSchema:
        """
        Asynchronously generates a new access token using the existing refresh token.

        Returns:
            str: A newly created access token.

        Raises:
            Exception: If token creation fails or the refresh token is invalid or expired.
        """
        return await self.repository.create_access_token_from_refresh()

    async def update_user_author_password(
        self,
    ) -> user_schemas.UpdatePasswordResponseSchema:
        """
        Update the authenticated user's password.

        Delegates the actual password update operation to the repository layer,
        which handles password hashing and database update.

        Returns:
            bool: True if the password was successfully updated, False otherwise.
        """
        return await self.repository.update_user_author_password()

    async def deactivate_account(self) -> user_schemas.DeactivateAccountResponseSchema:
        """
        Asynchronously deactivate the current user's account.

        This method calls the repository layer to perform the deactivation logic,
        such as setting an 'is_active' flag to False or marking the account as deactivated
        in the database.

        Returns:
            Any: The result returned by the repository's deactivate_account method,
            typically a success status or updated user object.
        """
        return await self.repository.deactivate_account()

    async def reactivate_account(self) -> user_schemas.ReactivateAccountResponseSchema:
        """
        Reactivates the current user's account.

        This method delegates the reactivation logic to the repository layer,
        typically by setting the `is_active` field of the user to `True` and committing
        the change to the database.

        Returns:
            DeactivateAccountResponseSchema: A response object indicating successful reactivation.
        """
        return await self.repository.reactivate_account()

    async def update_email(self) -> user_schemas.UpdateEmailResponseSchema:
        """
        Updates the email address of the current user.

        This method delegates the email update operation to the repository layer,
        which handles validating the new email and persisting the change in the database.

        Returns:
            An appropriate response schema indicating the success or failure of the update.
        """
        return await self.repository.update_user_author_email()

    async def update_name(self) -> user_schemas.UpdateNameResponseSchema:
        """
        Updates the name of the current user.

        This method calls the repository layer to perform the update operation,
        including validation and saving the new name in the database.

        Returns:
            An appropriate response schema indicating the outcome of the update.
        """
        return await self.repository.update_user_author_name()

    async def upload_profile_image(self) -> user_schemas.UploadImageResponseSchema:
        """
        Asynchronously uploads the profile image for a user with an author role.

        This method delegates the upload logic to the repository layer,
        which handles the actual image storage process (e.g., saving to disk or cloud storage).

        Returns:
            The result of the image upload operation from the repository.
        """
        return await self.repository.upload_user_author_image()

    async def remove_both_user_author_account(
        self,
    ) -> user_schemas.RemovedUserAuthorAccountSchema:
        """
        Asynchronously deletes both the user and corresponding author account.

        This method delegates the account removal logic to the repository layer,
        ensuring that all related data (user and author) are removed from the system
        in a single operation.

        Returns:
            RemovedUserAuthorAccountSchema: A schema indicating successful deletion
            along with any relevant metadata (e.g., confirmation message, deleted IDs).
        """

        return await self.repository.remove_account()

    async def update_balance(self) -> user_schemas.BalanceUpdateSchemaResponse:
        """
        Asynchronously updates the current user's balance using the repository layer.

        Returns:
            BalanceUpdateSchemaResponse: A Pydantic schema containing a success message.
        """
        return await self.repository.update_user_balance()
