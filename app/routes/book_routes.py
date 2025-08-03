from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import (APIRouter, Depends, File, HTTPException, Query, Request,
                     Response, Security, status)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_async_db
from app.models.app_models import Author, User
from app.repositories.book_repository import BookRepository
from app.repositories.user_logic import get_current_active_user
from app.schemas import book_schemas
from app.services.book_service import BookService

router = APIRouter(prefix="/api/v1/books", tags=["routes for the book"])
 

@router.post(
    "/create-book",
    response_model=book_schemas.BookResponseCreateSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_author_book(
    author: Annotated[Author, Security(get_current_active_user, scopes=["author"])],
    book_data: Annotated[book_schemas.BookCreateSchema, File()],
    async_session: AsyncSession = Depends(get_async_db),
) -> book_schemas.BookResponseCreateSchema:
    """
    Create a new book for the authenticated author.

    This endpoint allows an authenticated user with the "author" scope to create a new book.
    The request must include valid book data,and can include images (sent as form-data).

    Args:
        author (Author): The currently authenticated user with "author" scope.
        book_data (book_schemas.BookCreateSchema): Data required to create the book, including uploaded images.
        async_session (AsyncSession): SQLAlchemy asynchronous session for database operations.

    Returns:
        BookResponseCreateSchema: A response schema containing details of the created book.

    Raises:
        HTTPException:
            - 400 Bad Request if a database integrity error occurs (e.g., duplicate book).
            - 500 Internal Server Error for any unexpected exceptions.
    """

    try:
        repo = BookRepository(
            book_data=book_data, author=author, async_session=async_session
        )
        service = BookService(repo)
        return await service.save_book()
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An error occurred: {str(e.orig)}",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.get(
    "/list-all-books",
    response_model=list[book_schemas.BookFilterResponse],
    status_code=status.HTTP_200_OK,
)
async def get_all_books(
    user: Annotated[User, Depends(get_current_active_user)],
    order_by: Annotated[
        book_schemas.OrderByEnum, Query(description="order by date of publish or price")
    ],
    description: Annotated[str | None, Query()] = None,
    date_of_publish: Annotated[
        date | None, Query(description="Return books published on or after this date.")
    ] = None,
    min_price: Annotated[
        Decimal | None,
        Query(ge=0, le=9999.99, description="Minimum book price"),
    ] = 0.01,
    max_price: Annotated[
        Decimal | None,
        Query(ge=0, le=9999.99, description="Maximum book price"),
    ] = 9999.99,
    status: Annotated[
        book_schemas.BookStatusEnum | None,
        Query(description="status is eighter draft or published."),
    ] = None,
    author: Annotated[
        str | None,
        Query(description="you have to pass the name of the author"),
    ] = None,
    title: Annotated[
        str | None,
        Query(description="provide the the title of the book"),
    ] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    async_session: AsyncSession = Depends(get_async_db),
) -> list[book_schemas.BookFilterResponse]:
    """
    Retrieve a paginated and filtered list of books.

    This endpoint allows authenticated users to query all books with optional filters and ordering.

    Filtering options include:
    - `title`: Partial match on the book title (XSS-safe).
    - `description`: Partial match on the book description (XSS-safe).
    - `author`: Exact match on the author's name.
    - `min_price` and `max_price`: Price range filter.
    - `date_of_publish`: Return books published on or after this date.
    - `status`: Filter by book status (`draft` or `published`).
    - `order_by`: Order results by `date_of_publish` or `price`.

    Pagination is controlled with:
    - `offset`: Number of items to skip before starting to collect the result set.
    - `limit`: Maximum number of items to return (1–100).

    Requires:
    - Authenticated user (`get_current_active_user`).

    Returns:
        List[BookFilterResponse]: A list of books with their metadata and cover images.

    Raises:
        HTTPException 400: On database integrity errors or bad input.
        HTTPException 404: If a specified author is not found.
        HTTPException 500: For unexpected internal server errors.
    """
    try:
        repo = BookRepository(
            user=user,
            async_session=async_session,
            title=title,
            description=description,
            date_of_publish=date_of_publish,
            min_price=min_price,
            max_price=max_price,
            status=status,
            author=author,
            order_by=order_by,
            offset=offset,
            limit=limit,
        )
        service = BookService(repo)
        return await service.get_all_books()
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"An error occurred: {str(e.orig)}",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.get(
    "/filter_books_by_criteria",
    description="filter books by : author_name , price , date_of_publish",
    response_model=list[book_schemas.BookFilterResponse],
)
async def filter_book_by_user_criteria(
    price: Annotated[Decimal, Query(ge=0.01, le=9999.99)],
    date_of_publish: Annotated[date, Query(description="the format is 2012-03-20")],
    order_by: Annotated[Literal["price", "date_of_publish"], Query()],
    filter_book_order_mode: Annotated[Literal["ascending", "descending"], Query()],
    author_name: Annotated[str | None, Query(max_length=30)] = None,
    async_session=Depends(get_async_db),
) -> list[book_schemas.BookFilterResponse]:
    """
    Filter books based on user-defined criteria.

    This endpoint allows users to filter books using the following query parameters:
    - Author name (optional)
    - Price (required, must be between 0.01 and 9999.99)
    - Date of publish (required, format: YYYY-MM-DD)
    - Order mode: ascending or descending (required)
    - Order by: price or date_of_publish (required)

    The results are paginated (offset=2, limit=10) and ordered based on the chosen field and direction.

    Args:
        price (Decimal): The price threshold for filtering books.
        date_of_publish (date): The date threshold for filtering books.
        order_by (Literal): The field to order the results by ("price" or "date_of_publish").
        filter_book_order_mode (Literal): The sorting direction ("ascending" or "descending").
        author_name (str, optional): Filter by author name if provided.
        async_session: The database session dependency.

    Returns:
        list[BookFilterResponse]: A list of books matching the filtering criteria.

    Raises:
        HTTPException: If the specified author does not exist (404) or an internal error occurs (500).
    """

    try:
        repo = BookRepository(
            author_name=author_name,
            price=price,
            date_of_publish=date_of_publish,
            async_session=async_session,
            filter_book_order_mode=filter_book_order_mode,
            filter_book_order_by=order_by,
        )
        service = BookService(repo)
        return await service.filter_books_by_criteria()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.get("/the-most-sold-book")
async def get_the_most_sold_book(async_session: AsyncSession = Depends(get_async_db)):
    """
    Retrieve the most sold book.

    This endpoint calculates and returns the book that has been sold the most based
    on the total quantity across all order items.

    Returns:
        dict: A dictionary containing:
            - book_id (int): The ID of the most sold book.
            - nr_of_sold (int): The total quantity sold.

    Raises:
        HTTPException 404: If the book cannot be found.
        HTTPException 500: If an unexpected error occurs during processing.
    """
    try:
        repo = BookRepository(async_session=async_session)
        service = BookService(repo)
        return await service.get_the_most_sold_book()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.get("/average-book-price")
async def get_the_most_sold_book(async_session: AsyncSession = Depends(get_async_db)):
    """
    Endpoint to retrieve the average price of books per author.

    Calls the service method to fetch average book prices grouped by author,
    returning a list of authors along with their average book price.

    Args:
        async_session (AsyncSession): Database session dependency.

    Returns:
        List[dict]: A list of authors and their average book prices.

    Raises:
        HTTPException: Returns 500 Internal Server Error if any exception occurs.
    """
    try:
        repo = BookRepository(async_session=async_session)
        service = BookService(repo)
        return await service.average_book_price()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.get("/book-with-nr-of-cover-images")
async def get_the_most_sold_book(
    number_of_images: Annotated[
        int, Query(ge=1, description="number of images to query")
    ],
    async_session: AsyncSession = Depends(get_async_db),
):
    """
    Retrieve books that have at least the specified number of cover images.

    Args:
        number_of_images (int): Minimum number of cover images a book must have.
        async_session (AsyncSession): Database session dependency.

    Returns:
        List[Book]: A list of books matching the criteria.

    Raises:
        HTTPException: If any internal error occurs during query execution.
    """
    try:
        repo = BookRepository(
            async_session=async_session, number_of_images=number_of_images
        )
        service = BookService(repo)
        return await service.books_with_nr_cover_images()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.get("/author-books")
async def get_author_books(
    author_name: Annotated[
        str, Query(max_length=200, description="name of the author")
    ],
    async_session: AsyncSession = Depends(get_async_db),
):
    """
    Retrieve all books published by a specific author along with their sales data.

    This endpoint takes an author's name as a query parameter, fetches all books
    written by that author, and returns relevant information such as title, book ID,
    publication date, and the total number of items sold.

    Args:
        author_name (str): The full name of the author to search for.
        async_session (AsyncSession): The SQLAlchemy async session dependency.

    Returns:
        List[dict]: A list of books written by the specified author. Each dictionary contains:
            - author_name (str)
            - book_title (str)
            - book_id (UUID)
            - date_of_publish (str in ISO format)
            - sold_items (int)

    Raises:
        HTTPException:
            - 404 if the author is not found.
            - 500 if an unexpected error occurs.
    """

    try:
        repo = BookRepository(async_session=async_session, author_name=author_name)
        service = BookService(repo)
        return await service.get_books_by_author_service()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.get("/author-unsold-books")
async def get_author_unsold_books(
    author_name: Annotated[
        str, Query(max_length=200, description="name of the author")
    ],
    async_session: AsyncSession = Depends(get_async_db),
):
    """
    Retrieve all books written by a specific author that have never been sold.

    This endpoint:
    - Accepts the author's name as a query parameter.
    - Returns a list of books that have not been purchased by any customer.
    - Raises an error if the author is not found.

    Query Parameters:
        author_name (str): The full name of the author. Must be a string with a maximum length of 200 characters.

    Returns:
        list[Book]: A list of Book objects that have not been sold.

    Raises:
        HTTPException 404: If no author with the given name is found.
        HTTPException 500: For any unexpected server errors.
    """

    try:
        repo = BookRepository(async_session=async_session, author_name=author_name)
        service = BookService(repo)
        return await service.get_unsold_books_by_author_name()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.get("/author-books")
async def get_author_books(
    author_name: Annotated[
        str, Query(max_length=200, description="name of the author")
    ],
    async_session: AsyncSession = Depends(get_async_db),
):
    """
    Retrieve all books published by a specific author along with their sales data.

    This endpoint takes an author's name as a query parameter, fetches all books
    written by that author, and returns relevant information such as title, book ID,
    publication date, and the total number of items sold.

    Args:
        author_name (str): The full name of the author to search for.
        async_session (AsyncSession): The SQLAlchemy async session dependency.

    Returns:
        List[dict]: A list of books written by the specified author. Each dictionary contains:
            - author_name (str)
            - book_title (str)
            - book_id (UUID)
            - date_of_publish (str in ISO format)
            - sold_items (int)

    Raises:
        HTTPException:
            - 404 if the author is not found.
            - 500 if an unexpected error occurs.
    """

    try:
        repo = BookRepository(
            async_session=async_session, author_name=author_name
        )
        service = BookService(repo)
        return await service.get_books_by_author_service()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )





 