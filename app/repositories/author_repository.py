from fastapi import HTTPException, status

from sqlalchemy import update

from app.models.app_models import Author
from app.interfaces.author_interface import AbstractAuthorInterface
from app.schemas import author_schemas
from sqlalchemy.ext.asyncio import AsyncSession


class AuthorRepository(AbstractAuthorInterface):
    def __init__(
        self,
        author: Author | None = None,
        async_session: AsyncSession | None = None,
        author_description: author_schemas.AuthorDescription | None = None,
    ):
        self.author: Author | None = author
        self.author_description: author_schemas.AuthorDescription | None = (
            author_description
        )
        self.async_session: AsyncSession | None = async_session

    async def set_author_description(self):
        """
        Sets or updates the description for the current author.

        Executes an asynchronous SQL UPDATE query to change the author's description
        using the value provided in `self.author_description.description`.
        If the update affects no rows (e.g., invalid author ID), an HTTP 400 error is raised.

        Returns:
            AuthorDescriptionResponse: A response schema indicating successful update.

        Raises:
            HTTPException: If the description update fails (no matching author found).
        """

        stmt = (
            update(Author)
            .values(description=self.author_description.description)
            .where(Author.id == self.author.id)
        )
        result = await self.async_session.execute(stmt)
        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not update description.",
            )
        await self.async_session.commit()
        return author_schemas.AuthorDescriptionResponse(success="Description saved.")
