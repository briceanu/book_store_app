from fastapi import (
    APIRouter,
    Depends,
    status,
    HTTPException,
    Security,
    Body,
)
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.db_connection import get_async_db
from app.repositories.author_repository import AuthorRepository
from app.services.author_service import AuthorService
from app.schemas import author_schemas
from typing import Annotated
from app.models.app_models import  Author
from app.repositories.user_logic import get_current_active_user
from sqlalchemy.exc import IntegrityError

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
