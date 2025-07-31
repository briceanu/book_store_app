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

    def __init__(self, repository: AuthorRepository) -> Self:
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

    async def get_author_names_by_number_of_books_published(self) -> list:
        """
        Retrieve a list of authors ordered by the number of books they have published.

        Delegates the query to the repository layer to fetch author names,
        typically sorted in descending order of published book count.

        Returns:
            List[str] | List[AuthorSummary]: A list of author names or structured responses
            depending on the repository's return type.
        """
        return await self.repository.get_authors_by_number_of_published_books()

    async def authors_with_no_books(self):
        """
        Service method to retrieve authors who have not published any books.

        Delegates the operation to the repository layer, which performs the database query
        to identify authors without any associated books.

        Returns:
            list: A list of Author model instances with no published books.
        """
        return await self.repository.get_authors_with_no_published_books()
    
    async def top_paid_authors(self):
        """
        Retrieve the top three authors ranked by total earnings from book sales.

        Returns:
            List[Author]: A list of the top three authors with the highest total sales revenue.
        """
        return await self.repository.top_three_paid_authors()

    async def authors_that_sold_more_than_nr_books(self):
        """
        Retrieve authors who have sold more than a specified number of books.

        Returns:
            list[dict]: A list of authors along with the total number of books they've sold,
                        filtered by a minimum threshold defined elsewhere in the repository.
        """
        return await self.repository.authors_that_sold_more_than_a_specific_nr_of_books() 
    
    async def authors_revenue_check(self):
        """
        Asynchronously retrieves revenue data for all authors.

        Returns:
            A list or dictionary (depending on repository implementation) containing
            revenue details for each author, such as total sales, number of books sold,
            or other aggregated metrics.
        """
        return await self.repository.authors_revenue()
    
    async def author_top_sold_book(self):
        """
        Retrieves the best-selling book for the currently authenticated author.

        Returns:
            The book with the highest number of sales associated with the author.

        Raises:
            HTTPException: If the author has no books or sales data available.
        """
        return await self.repository.author_best_selling_book()