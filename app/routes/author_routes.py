from fastapi import (
    APIRouter,
    Depends,
    status,
    HTTPException,
    Security,
    Body,
    Path,
    Query,
)
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.db_connection import get_async_db
from app.repositories.author_repository import AuthorRepository
from app.services.author_service import AuthorService
from app.schemas import author_schemas
from typing import Annotated
from app.models.app_models import Author
from app.repositories.user_logic import get_current_active_user
from sqlalchemy.exc import IntegrityError
from pydantic import PositiveInt

router = APIRouter(prefix="/api/v1/author", tags=["routes for the  author only"])


@router.patch(
    "/update-author-biography",
    status_code=status.HTTP_200_OK,
    response_model=author_schemas.AuthorDescriptionResponse,
)
async def update_author_biography(
    description: Annotated[author_schemas.AuthorDescription, Body()],
    author: Annotated[Author, Security(get_current_active_user, scopes=["author"])],
    async_session: AsyncSession = Depends(get_async_db),
) -> author_schemas.AuthorDescriptionResponse:
    """
    Update the biography/description of the currently authenticated author.

    This endpoint allows an authenticated user with the "author" scope to
    update their biography information. The updated description is saved
    to the database, and the updated value is returned in the response.

    Args:
        description (AuthorDescription): New biography/description data.
        author (Author): The currently authenticated author (injected via dependency).
        async_session (AsyncSession): SQLAlchemy async session (injected via dependency).

    Returns:
        AuthorDescriptionResponse: The updated author biography wrapped in a response schema.

    Raises:
        HTTPException (403): If the user is not authorized as an author.
        HTTPException (500): If an unexpected server error occurs.
    """
    try:
        repo = AuthorRepository(
            author=author, async_session=async_session, author_description=description
        )
        service = AuthorService(repo)
        return await service.save_author_description()
    except IntegrityError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


# downwords is just for learning how to query the data
@router.get("/authors-with-more-than-nr-books/{nr_of_books}")
async def get_authors_name_with_more_than_nr_of_book(
    nr_of_books: Annotated[PositiveInt, Path(le=999999)],
    async_session=Depends(get_async_db),
) -> list:
    """
    Retrieve the names of authors who have published more than a specified number of books.

    This endpoint joins the Author and Book tables, groups by author, and returns only those
    whose total number of published books exceeds the value provided in the path parameter `nr_of_books`.

    Args:
        nr_of_books (int): A positive integer (max 999999) indicating the minimum number of books an author must have published.
        async_session (AsyncSession): The database session dependency.

    Returns:
        List[dict]: A list of dictionaries, each containing:
            - 'author_name' (str): The name of the author.
            - 'nr_of_books' (int): The number of books the author has published.

    Raises:
        HTTPException: 500 Internal Server Error if an unexpected issue occurs.
    """

    try:
        repo = AuthorRepository(nr_of_books=nr_of_books, async_session=async_session)
        service = AuthorService(repo)
        return await service.get_author_names_by_number_of_books_published()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.get("/authors-with-no-published-books")
async def get_authors_with_no_published_books(
    async_session=Depends(get_async_db),
):
    """
    Retrieve all authors who have not published any books.

    This endpoint identifies and returns authors with no associated books in the database.
    It queries the `Author` table and excludes any authors who appear in the `Book` table.

    Args:
        async_session: Dependency injection for the asynchronous database session.

    Returns:
        list[dict]: A list of dictionaries, each representing an author who has not published any books.

    Raises:
        HTTPException:
            - 500 Internal Server Error if an unexpected error occurs during processing.
    """

    try:
        repo = AuthorRepository(async_session=async_session)
        service = AuthorService(repo)
        return await service.authors_with_no_books()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.get("/top-three-paid-authors")
async def get_top_three_paid_authors(
    async_session=Depends(get_async_db),
):
    """
    Retrieve the top three authors with the highest total earnings from book sales.

    This endpoint calculates the total revenue generated by each author from their book sales
    and returns the top three authors ranked by earnings.

    Returns:
        List[dict]: A list of dictionaries containing author details and their total earnings.

    Raises:
        HTTPException: 500 error if an unexpected issue occurs during the process.
    """

    try:
        repo = AuthorRepository(async_session=async_session)
        service = AuthorService(repo)
        return await service.top_paid_authors()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.get("/authors-that-sold-a-specified-nr-of-books")
async def get_authors_that_sold_a_specified_nr_of_books(
    specified_nr_of_books: Annotated[int, Query(ge=0)],
    async_session=Depends(get_async_db),
):
    """
    Retrieve authors who have sold more than a specified number of books.

    This endpoint returns a list of authors along with the total number of books
    they have sold, filtered by a minimum threshold provided as a query parameter.

    Args:
        specified_nr_of_books (int): Minimum number of books an author must have sold
                                     to be included in the results. Must be ≥ 0.
        async_session (AsyncSession): SQLAlchemy async database session (injected via Depends).

    Returns:
        list[dict]: A list of dictionaries containing:
            - 'author name': The name of the author.
            - 'number of books sold': The total quantity of books sold by the author.

    Raises:
        HTTPException: 500 Internal Server Error if an unexpected exception occurs.
    """
    try:
        repo = AuthorRepository(
            async_session=async_session, specified_nr_of_books=specified_nr_of_books
        )
        service = AuthorService(repo)
        return await service.authors_that_sold_more_than_nr_books()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )


@router.get("/revenue")
async def get_authors_revenue(
    async_session=Depends(get_async_db),
):
    try:
        repo = AuthorRepository(async_session=async_session)
        service = AuthorService(repo)
        return await service.authors_revenue_check()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )



@router.get("/top-sold-book")
async def get_author_top_sold_book(
   async_session: AsyncSession = Depends(get_async_db),
):
 
    try:
        repo = AuthorRepository(async_session=async_session)
        service = AuthorService(repo)
        return await service.author_top_sold_book()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )
