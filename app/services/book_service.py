from app.repositories.book_repository import BookRepository
from app.schemas import book_schemas


class BookService:
    """
    Service layer responsible for handling business logic related to books.

    This class delegates database operations to the BookRepository and
    coordinates data processing tasks such as book creation, validation,
    and transformation to response schemas.

    Attributes:
        repository (BookRepository): The repository instance used to interact with the book data layer.
    """

    def __init__(self, repository: BookRepository):
        self.repository = repository

    async def save_book(self) -> book_schemas.BookResponseCreateSchema:
        """
        Asynchronously creates and saves a new book record in the database.

        This method calls the repository layer to perform the creation logic and
        returns a structured response containing the newly created book data.

        Returns:
            BookResponseCreateSchema: A schema representing the newly created book.
        """
        return await self.repository.create_book()

    async def get_all_books(self):
        """
        Retrieve all books from the repository.

        Returns:
            List[Book]: A list of all books available in the system.
        """
        return await self.repository.fetch_books()

    async def filter_books_by_criteria(self):
        """
        Service method to filter books based on user-defined criteria.

        Delegates the filtering logic to the repository layer, which applies filters such as:
        - Author name (optional)
        - Price comparison (ascending/descending)
        - Publication date comparison (ascending/descending)
        - Ordering by price or date
        - Pagination (limit and offset)

        Returns:
            list: A list of Book model instances that match the filtering criteria.
        """
        return await self.repository.filter_books()

    async def get_the_most_sold_book(self):
        """
        Service method to retrieve the most sold book.

        This method calls the repository layer to determine which book has the highest
        total quantity sold across all order items. The result typically includes the
        book ID and the number of units sold.

        Returns:
            dict: A dictionary containing the book ID and the total number of units sold.
        """
        return await self.repository.get_the_most_purchased_book()

    async def average_book_price(self):
        """
        Retrieve the average price of books for each author.

        Calls the repository method that calculates the average price of all books
        published by each author and returns the results.

        Returns:
            list: A list of tuples or dicts containing author information and their
                  average book price.

        Raises:
            Exception: If the query or data retrieval fails.
        """
        return await self.repository.average_book_price_per_author()

    async def books_with_nr_cover_images(self):
        """
        Fetch books that have more than a specified number of cover images by calling
        the corresponding repository method.

        Returns:
            List[Book]: List of books with more than the given number of cover images.
        """
        return await self.repository.books_that_have_more_than_nr_cover_images()

    async def get_books_by_author_service(self):
        """
        Retrieve a list of books published by a specified author.

        This method delegates the query logic to the repository layer,
        which performs the actual database call to return all books
        associated with a given author.

        Returns:
            List[Book]: A list of Book objects written by the specified author.
        """
        return await self.repository.get_books_by_author()

    async def get_unsold_books_by_author_name(self):
        """
        Retrieve all books written by a specified author that have not been sold.

        This method delegates to the repository to return a list of books authored
        by the specified author (likely stored in `self.author_name`) that have
        zero recorded sales in the system.

        Returns:
            List[dict]: A list of dictionaries, each containing book details
            (such as title, ID, and publication date) for books that have not been sold.

        Raises:
            HTTPException: If the specified author does not exist.
        """

        return await self.repository.get_unsold_books_by_author()
