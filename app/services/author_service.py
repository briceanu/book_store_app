from typing import Self

from app.repositories.author_repository import AuthorRepository
from app.schemas import author_schemas

class AuthorService:
    """
    Service layer for handling business logic related to authors.

    This class delegates database interactions to the AuthorRepository and
    provides a clean interface for higher-level operations such as updating 
    an author's description.

    Attributes:
        repository (AuthorRepository): An instance of AuthorRepository used for database operations.

    Methods:
        save_author_description(): Asynchronously saves or updates the author's description
            using data provided to the repository.
    """


    def __init__(self,repository:AuthorRepository) -> Self:
        self.repository = repository



    async def save_author_description(self) -> author_schemas.AuthorDescriptionResponse:
        """
        Asynchronously saves or updates the author's description in the database.

        This method delegates the operation to the repository layer and returns
        a structured response containing the updated author description data.

        Returns:
            AuthorDescriptionResponse: A response schema containing the updated description.
        """

        return await self.repository.set_author_description()

        