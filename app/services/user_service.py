from app.repositories.user_repository import UserRepository


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

    async def create_user_account(self):
        """
        Create a new user account asynchronously.

        Returns:
            Result of the repository's sign_up method, typically a user instance or confirmation.
        """
        return await self.repository.sign_up()

    async def login_user(self):
        """
        Authenticate and log in a user asynchronously.

        Returns:
            Result of the repository's sign_in method, typically authentication tokens or user info.
        """
        return await self.repository.sign_in()

    async def login_out_user(self):
        """
        Logs out the currently authenticated user.

        This method delegates the logout logic to the repository layer,
        which may handle tasks such as invalidating tokens, clearing session data,
        or updating user state in the database.

        Returns:
            Any: The result of the logout operation from the repository.
        """
        return await self.repository.logout()

    
    async def get_access_token_from_refresh_token(self):
        """
        Asynchronously generates a new access token using the existing refresh token.

        Returns:
            str: A newly created access token.

        Raises:
            Exception: If token creation fails or the refresh token is invalid or expired.
        """
        return await self.repository.create_access_token_from_refresh()
    

    async def update_user_author_password(self):
        """
        Update the authenticated user's password.

        Delegates the actual password update operation to the repository layer,
        which handles password hashing and database update.

        Returns:
            bool: True if the password was successfully updated, False otherwise.
        """
        return await self.repository.update_user_author_password()
    

    async def deactiacte_account(self):
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
    

    async def reactivate_account(self):
        """
        Reactivates the current user's account.

        This method delegates the reactivation logic to the repository layer,
        typically by setting the `is_active` field of the user to `True` and committing
        the change to the database.

        Returns:
            DeactivateAccountResponseSchema: A response object indicating successful reactivation.
        """
        return await self.repository.reactivate_account()
    

    async def update_email(self):
        """
        Updates the email address of the current user.

        This method delegates the email update operation to the repository layer,
        which handles validating the new email and persisting the change in the database.

        Returns:
            An appropriate response schema indicating the success or failure of the update.
        """
        return await self.repository.update_user_author_email()
    
    async def update_name(self):
        """
        Updates the name of the current user.

        This method calls the repository layer to perform the update operation,
        including validation and saving the new name in the database.

        Returns:
            An appropriate response schema indicating the outcome of the update.
        """
        return await self.repository.update_user_author_name()
        
    async def add_author_biography(self):
        """
        Asynchronously add or update the biography/description for an author.

        This method delegates the task to the repository layer to persist the
        author's descriptive information (bio) in the database.

        Returns:
            The result of the repository operation, typically a success confirmation or updated author data.
        """
        return await self.repository.add_author_description()


    async def upload_profile_image(self):
        """
        Asynchronously uploads the profile image for a user with an author role.

        This method delegates the upload logic to the repository layer,
        which handles the actual image storage process (e.g., saving to disk or cloud storage).

        Returns:
            The result of the image upload operation from the repository.
        """
        return await self.repository.upload_user_author_image()
