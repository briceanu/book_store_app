from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Security, status, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_async_db
from app.models.app_models import Author, User
from app.repositories.user_logic import get_current_active_user
from app.repositories.book_repository import BookRepository
from app.schemas import book_schemas
from app.services.book_service import BookService
from fastapi import File
from datetime import date
from decimal import Decimal
from pydantic import BeforeValidator, AfterValidator
from app.schemas.validators import protection_against_xss
from typing import Literal

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
    The request must include valid book data including images (sent as form-data).
    The book is saved to the database using a repository and service layer.

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


@router.post(
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
)
async def filter_book_by_user_criteria(
    price: Annotated[Decimal, Query(ge=0.01, le=9999.99)],
    date_of_publish: Annotated[date, Query(description="the format is 2012-03-20")],
    author_name: Annotated[str, Query(max_length=30)],
    order_by: Annotated[Literal["price", "date_of_publish"], Query()],
    filter_book_order_mode: Annotated[Literal["ascending", "descending"], Query()],
    async_session=Depends(get_async_db),
):
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


# filter_books_by_criteria
