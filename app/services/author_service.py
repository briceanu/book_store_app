
from app.repositories.author_repository import AuthorRepository


class AuthorService:
    def __init__(self,repository:AuthorRepository):
        self.repository = repository



    async def save_author_description(self):
        return await self.repository.set_author_description()

        