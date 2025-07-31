from abc import ABC, abstractmethod


class AbstractUserInterface(ABC):
    """
    Abstract base class defining the contract for user-related operations.

    This interface establishes a blueprint for implementing core user authentication
    and account management functionalities. Subclasses must provide concrete implementations
    for all methods to ensure consistent behavior across different user types
    (e.g., regular users, authors, admins).

    Methods:
        sign_up(): Handle the user registration process.
        sign_in(): Authenticate the user and return an access token.
        logout(): Invalidate the user's current session or token.
        create_access_token_from_refresh(): Generate a new access token using a valid refresh token.
        update_user_author_password(): Update the user's password securely.
        deactivate_account(): Temporarily disable a user account.
        reactivate_account(): Reactivate a previously deactivated account.
        update_user_author_email(): Change the user's email address.
        update_user_author_name(): Update the user's display name.
        upload_user_author_image(): Upload or update the user's profile image.
        remove_account(): Permanently delete the user account and related data.
    """

    
    @abstractmethod
    def sign_up(self) -> None:
        pass

    @abstractmethod
    def sign_in(self) -> None:
        pass

    @abstractmethod
    def logout(self) -> None:
        pass

    @abstractmethod
    def create_access_token_from_refresh(self) -> None:
        pass

    @abstractmethod
    def update_user_author_password(self) -> None:
        pass

    @abstractmethod
    def deactivate_account(self) -> None:
        pass

    @abstractmethod
    def reactivate_account(self) -> None:
        pass

    @abstractmethod
    def update_user_author_email(self) -> None:
        pass

    @abstractmethod
    def update_user_author_name(self) -> None:
        pass

    @abstractmethod
    def upload_user_author_image(self) -> None:
        pass
    
    @abstractmethod
    def remove_account(self)->None:
        pass
    
    @abstractmethod
    def update_user_balance(self)->None:
        pass

    @abstractmethod
    def order_history_summary_for_user(self) -> None:
        pass

    @abstractmethod
    def high_spending_users(self) -> None:
        pass