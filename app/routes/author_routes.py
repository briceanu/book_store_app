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

    try:
        repo = AuthorRepository(
            author=author, async_session=async_session, author_description=description
        )
        service = AuthorService(repo)
        return await service.save_author_description()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        )
