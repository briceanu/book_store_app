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