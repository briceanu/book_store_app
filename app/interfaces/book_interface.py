from abc import ABC, abstractmethod


class AbstractBookInterface(ABC):
    """
    Abstract base class defining the contract for book-related operations.

    This interface specifies the essential methods required for managing books
    in the system. Any subclass must implement these methods to handle book creation
    and retrieval consistently across the application.

    Methods:
        create_book(): Handle the creation and persistence of a new book record.
        fetch_books(): Retrieve a list of books, potentially with filtering or pagination.
    """

    @abstractmethod
    def create_book(self) -> None:
        pass

    @abstractmethod
    def fetch_books(self) -> None:
        pass

    @abstractmethod
    def filter_books(self) -> None:
        pass