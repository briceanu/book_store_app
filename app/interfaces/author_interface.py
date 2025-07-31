from abc import ABC,abstractmethod



class AbstractAuthorInterface(ABC):
    """
    Abstract base class defining the interface for author-specific operations.

    This interface ensures that any implementing class provides functionality
    related to managing an author's profile, including updating the author's description.

    Methods:
        set_author_description(): Define or update the biography or description of the author.
    """


    @abstractmethod
    def set_author_description(self) -> None:
        pass

    @abstractmethod
    def get_authors_by_number_of_published_books(self) -> None:
        pass

    @abstractmethod
    def get_authors_with_no_published_books(self) -> None:
        pass

    @abstractmethod
    def top_three_paid_authors(self) -> None:
        pass

    @abstractmethod
    def authors_that_sold_more_than_a_specific_nr_of_books(self) -> None:
        pass

    @abstractmethod
    def authors_revenue(self) -> None:
        pass

    @abstractmethod
    def author_best_selling_book(self) -> None:
        pass