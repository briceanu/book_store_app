from app.interfaces.book_interface import AbstractBookInterface
from app.schemas.book_schemas import (
    BookCreateSchema,
    BookResponseCreateSchema,
    BookFilterResponse,
    CoverImageModel,
)
from app.models.app_models import Author, Book, CoverImage, User, OrderItem
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status
import os, shutil
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from sqlalchemy import and_, func, desc
import operator


@dataclass
class BookRepository(AbstractBookInterface):
    """
    Repository class for handling book-related operations.

    This class provides methods for creating and managing books,
    including validation, persistence, and association with authors and users.

    Attributes:
        book_data (BookCreateSchema | None): The input data used to create a book.
        author (Author | None): The currently authenticated author creating the book.
        async_session (AsyncSession | None): The SQLAlchemy async session used for database operations.
        user (User | None): The currently authenticated user (may be different from the author).
    """

    book_data: BookCreateSchema | None = None
    author: Author | None = None
    async_session: AsyncSession | None = None
    user: User | None = None
    title: str | None = None
    description: str | None = None
    date_of_publish: date | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    status: str | None = None
    author: str | None = None
    order_by: str | None = None
    offset: str | None = None
    limit: str | None = None
    author_name: str | None = None
    price: Decimal | None = None
    date_of_publish: date | None = None
    filter_book_order_by: str | None = None
    filter_book_order_mode: str | None = None
    number_of_images: int | None = None

    async def create_book(self) -> BookResponseCreateSchema:
        """
        Creates a new book record along with its optional cover images.

        This method performs the following steps:
        1. Validates that all contributing authors exist in the database.
        2. Creates a new book entry in the database using provided metadata.
        3. Validates the number of uploaded cover images (max 3).
        4. Saves uploaded image files to disk (e.g., local 'uploads' directory).
        5. Performs a bulk insert of image metadata (file path and book reference) into the database.

        Returns:
            BookResponseCreateSchema: A response object indicating successful creation of the book.

        Raises:
            HTTPException: If a contributing author does not exist in the database.
            HTTPException: If more than 3 cover images are uploaded.
        """

        # Step 1: Save the book
        if self.book_data.contributing_authors:
            authors = ",".join(self.book_data.contributing_authors).split(",")
            contributing_authors = [writer for writer in authors]
            # check to see if contributing authors are valid authors in db
            authors_in_db = (
                (
                    await self.async_session.execute(
                        select(Author.name).where(Author.name.in_(contributing_authors))
                    )
                )
                .scalars()
                .all()
            )
            for writer in contributing_authors:
                if writer not in authors_in_db:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(f"No author with the name {writer} found."),
                    )

        book_data = {
            "title": self.book_data.title,
            "description": self.book_data.description,
            "price": self.book_data.price,
            "date_of_publish": self.book_data.date_of_publish,
            "status": self.book_data.status,
            # converting single string of users into multiple string of users
            "contributing_authors": ",".join(self.book_data.contributing_authors).split(
                ","
            ),
            "author_id": self.author.id,
            "number_of_items": self.book_data.number_of_items,
        }

        stmt = insert(Book).values(**book_data).returning(Book.book_id)
        book_id = (await self.async_session.execute(stmt)).scalar_one()

        if len(self.book_data.images) > 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(f"No more than 3 book images allowed."),
            )
        # Step 2: Save cover images
        UPLOAD_DIR = "uploads"
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        # in a real project we save the images in a s3bucket server
        if self.book_data.images:
            cover_image_objects = []
            for image in self.book_data.images:
                file_path = os.path.join(UPLOAD_DIR, image.filename)
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(image.file, buffer)
                cover_image_objects.append({"book_id": book_id, "image_url": file_path})
            # using bulk_insert
            await self.async_session.execute(insert(CoverImage), cover_image_objects)
        await self.async_session.commit()
        return BookResponseCreateSchema(success="book saved.")

    async def fetch_books(self):
        """
        Retrieve a filtered and paginated list of books.

        Applies filters based on optional query parameters such as:
        - `description`: Performs a case-insensitive search in the book description.
        - `title`: Performs a case-insensitive search in the book title.
        - `author`: Matches the exact name of the author and filters by author ID.
        - `min_price` and `max_price`: Filters books whose price falls within the specified range.
        - `date_of_publish`: Returns books published on or after this date.
        - `status`: Filters by the publication status of the book (e.g., draft, published).

        The result is ordered by the field specified in `self.order_by`,
        and paginated using `self.offset` and `self.limit`.

        Returns:
            list[BookFilterResponse]: A list of books matching the filters, including cover images.

        Raises:
            HTTPException: If the provided author name does not exist.
        """
        stmt = select(Book).options(joinedload(Book.cover_images))
        filters = []
        # filtering by description
        if self.description:
            filters.append(Book.description.ilike(f"%{self.description.strip()}%"))
        # filtering by title
        if self.title:
            filters.append(Book.title.ilike(f"%{self.title.strip()}%"))
        # filtering by author
        if self.author:
            author_stmt = select(Author.id).where(Author.name == self.author)
            author_id = (
                await self.async_session.execute(author_stmt)
            ).scalar_one_or_none()
            if author_id:
                filters.append(Book.author_id == author_id)
            else:
                raise HTTPException(
                    status_code=404, detail=f"No author found with name '{self.author}'"
                )
        # filter by price
        if self.min_price and self.max_price:
            filters.append(Book.price.between(self.min_price, self.max_price))
        # filter by date_of_publish
        if self.date_of_publish:
            filters.append(Book.date_of_publish >= self.date_of_publish)
        # filter by status
        if self.status:
            filters.append(Book.status == self.status)

        if filters:
            stmt = stmt.where(and_(*filters))
        stmt = stmt.order_by(self.order_by).offset(self.offset).limit(self.limit)
        result = (await self.async_session.execute(stmt)).unique().scalars().all()

        return [
            BookFilterResponse(
                book_id=book.book_id,
                date_of_publish=book.date_of_publish,
                number_of_items=book.number_of_items,
                description=book.description,
                title=book.title,
                contributing_authors=book.contributing_authors,
                status=book.status,
                price=book.price,
                author_id=book.author_id,
                cover_images=[
                    CoverImageModel(
                        cover_id=ci.cover_id,
                        image_url=ci.image_url,
                        book_id=ci.book_id,
                    )
                    for ci in book.cover_images
                ],
            )
            for book in result
        ]

    # lerning how to filter data

    async def filter_books(self) -> list[BookFilterResponse]:
        """
        Asynchronously filter and retrieve a list of books based on specified criteria.

        Filters books using the following optional attributes from the instance:
        - `author_name`: If provided, filters books by the corresponding author's name.
        - `price`: Filters books by comparing the price based on the `filter_book_order_mode`.
        - `date_of_publish`: Filters books by comparing the publication date based on `filter_book_order_mode`.
        - `filter_book_order_mode`: Determines sorting and comparison direction ("ascending" or "descending").
        - `filter_book_order_by`: The column by which the result set will be ordered.

        The results are paginated with a fixed offset of 2 and a limit of 10.

        Raises:
            HTTPException: If the specified author name does not match any author in the database.

        Returns:
            List[Book]: A list of Book objects that match the filtering criteria.
        """
        author_filter = []
        if self.author_name:
            author = (
                await self.async_session.execute(
                    select(Author).where(Author.name == self.author_name.strip())
                )
            ).scalar()
            if not author:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"no user with the name {self.author_name} found.",
                )
            author_filter.append(author.id)
        price_comparison = (
            operator.ge if self.filter_book_order_mode == "ascending" else operator.le
        )
        date_comparison = (
            operator.le if self.filter_book_order_mode == "descending" else operator.ge
        )
        stmt = (
            select(Book)
            .options(joinedload(Book.cover_images))
            .where(
                and_(
                    price_comparison(Book.price, self.price),
                    date_comparison(Book.date_of_publish, self.date_of_publish),
                ),
            )
            .order_by(self.filter_book_order_by)
            .offset(2)
            .limit(10)
        )
        if author_filter:
            stmt = stmt.where(Book.author_id.in_(author_filter))
        result = (await self.async_session.execute(stmt)).unique().scalars().all()
        return [
            BookFilterResponse(
                book_id=data.book_id,
                date_of_publish=data.date_of_publish,
                number_of_items=data.number_of_items,
                description=data.description,
                title=data.title,
                contributing_authors=data.contributing_authors,
                status=data.status,
                price=data.price,
                author_id=data.author_id,
                cover_images=[
                    CoverImageModel(
                        cover_id=result.cover_id,
                        image_url=result.image_url,
                        book_id=result.book_id,
                    )
                    for book in result
                    for result in book.cover_images
                ],
            )
            for data in result
        ]

        # Most Purchased Book

    async def get_the_most_purchased_book(self):
        """
        Retrieve the most purchased book based on total quantity sold.

        Executes a query to find the book with the highest sum of ordered quantities
        across all order items. It groups results by book ID and title, then returns
        the book with the maximum total sold quantity.

        Returns:
            dict: A dictionary containing:
                - book_id (int): The ID of the most purchased book.
                - title (str): The title of the most purchased book.
                - nr_of_items (int): Total number of items sold for that book.

        Raises:
            Exception: If the query fails or no results are found.
        """
        stmt = (
            select(
                Book.book_id,
                Book.title,
                func.sum(OrderItem.quantity).label("total_quantity"),
            )
            .join(OrderItem, Book.book_id == OrderItem.book_id)
            .group_by(Book.book_id, Book.title)
            .order_by(desc(func.sum(OrderItem.quantity)))  # Most sold book first
            .limit(1)
        )
        result = (await self.async_session.execute(stmt)).first()
        book_id, title, nr_of_items = result
        return {"book_id": book_id, "title": title, "nr_of_items": nr_of_items}

    # Average Book Price per Author
    async def average_book_price_per_author(self):
        """
        Calculate the average price of all books published by each author.

        Performs an outer join between authors and books, computes the average
        book price per author, and returns the results ordered by average price descending.

        Returns:
            List[dict]: A list of dictionaries containing author names and their average book price.
                        Example: [{"name": "Author Name", "average price": 25.50}, ...]

        """

        # For each author, return their name and the average price of all books they've published.
        avg_price = func.coalesce(func.avg(Book.price), 0)
        stmt = (
            select(Author.name, avg_price)
            .outerjoin(Book, Author.id == Book.author_id)
            .group_by(Author.id, Author.name)
            .order_by(desc(avg_price))
        )
        result = (await self.async_session.execute(stmt)).all()
        return [
            {"name": name, "average price": average_price}
            for name, average_price in result
        ]

    async def books_that_have_more_than_nr_cover_images(self):
        """
        Retrieve books that have more than a specified number of cover images attached.

        Uses a SQL query with a join between Book and CoverImage tables, grouping by book,
        and filtering to include only those books with at least 2 cover images.

        Returns:
            List[Book]: A list of Book objects that have 2 or more cover images.
        """
        stmt = (
            select(Book)
            .options(joinedload(Book.cover_images))
            .join(CoverImage, CoverImage.book_id == Book.book_id)
            .group_by(Book.book_id)
            .having(
                func.coalesce(func.count(CoverImage.book_id), 0)
                >= self.number_of_images
            )
        )
        result = (await self.async_session.execute(stmt)).unique().scalars().all()
        return result

    # give the name of the author and show title of all books
    async def get_books_by_author(self):
        """
        Retrieve all books published by a specific author, along with sales data.

        This method looks up the author by name (stored in `self.author_name`),
        and returns all books written by that author, including each book's title,
        ID, publication date, and the total number of sold items (aggregated from order items).

        Returns:
            List[dict]: A list of dictionaries, each containing:
                - author name (str): The full name of the author.
                - book title (str): The title of the book.
                - book id (UUID): The unique identifier of the book.
                - date of publish (str): The ISO-formatted publication date.
                - sold items (int): The total number of items sold for that book.

        Raises:
            HTTPException: If no author with the specified name is found in the database.
        """

        author_id = (
            await self.async_session.execute(
                select(Author.id).where(Author.name == self.author_name)
            )
        ).scalar()
        if not author_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"no author with the name {self.author_name} found.",
            )
        sum_of_books = func.coalesce(func.sum(OrderItem.quantity), 0)
        stmt = (
            select(
                Author.name,
                Book.title,
                Book.book_id,
                Book.date_of_publish,
                sum_of_books,
            )
            .join(OrderItem, OrderItem.book_id == Book.book_id)
            .join(Author, Author.id == Book.author_id)
            .where(Book.author_id == author_id)
            .group_by(Book.book_id, Author.name)
            .order_by(desc(sum_of_books))
        )
        result = (await self.async_session.execute(stmt)).all()
        return [
            {
                "author name": author_name,
                "book title": title,
                "book id": book_id,
                "date of publish": date_of_publish.isoformat(),
                "sold items": sold,
            }
            for author_name, title, book_id, date_of_publish, sold in result
        ]

    # books that have not been bought by a specific author

    async def get_unsold_books_by_author(self):
        """
        Retrieve all books by a specific author that have never been sold.

        This method:
        - Looks up the author by name.
        - Constructs a subquery of all book IDs that have been sold by this author.
        - Retrieves all books written by this author that are not in the sold books list.

        Returns:
            list[Book]: A list of unsold Book objects for the given author.

        Raises:
            HTTPException: If the author with the specified name does not exist (404).
        """
        author_id = (
            await self.async_session.execute(
                select(Author.id).where(Author.name == self.author_name)
            )
        ).scalar()
        if not author_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"no author with the name {self.author_name} found.",
            )
        # all the sold books of one author
        book_subquery = (
            select(OrderItem.book_id)
            .join(Book, OrderItem.book_id == Book.book_id)
            .where(Book.author_id == author_id)
            .group_by(Book.book_id, OrderItem.book_id)
        )
        stmt = (
            select(Book)
            .join(Author, Author.id == Book.author_id)
            .where(and_(~Book.book_id.in_(book_subquery), Book.author_id == author_id))
            .group_by(Author.id, Book.book_id)
        )
        unpublised_books = (await self.async_session.execute(stmt)).scalars().all()
        return unpublised_books


