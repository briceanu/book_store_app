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
        return await self.repository.filter_books()