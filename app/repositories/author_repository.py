from fastapi import HTTPException, status

from sqlalchemy import update, select, func, desc, over

from app.models.app_models import Author, Book, User, OrderItem
from app.interfaces.author_interface import AbstractAuthorInterface
from app.schemas import author_schemas
from sqlalchemy.ext.asyncio import AsyncSession
from dataclasses import dataclass


@dataclass
class AuthorRepository(AbstractAuthorInterface):
    """
    Repository class for managing author-related operations.

    This class implements the AbstractAuthorInterface and provides methods
    to interact with the Author model, including setting the author's description.

    Attributes:
        author (Author | None): The Author instance to operate on.
        author_description (author_schemas.AuthorDescription | None):
            The schema containing the new author description data.
        async_session (AsyncSession | None): SQLAlchemy asynchronous session for database operations.

    Methods:
        set_author_description(): Updates the author's description using provided schema data.
    """

    author: Author | None = None
    author_description: author_schemas.AuthorDescription | None = None
    async_session: AsyncSession | None = None
    nr_of_books: int | None = None
    specified_nr_of_books: int | None = None

    async def set_author_description(self) -> author_schemas.AuthorDescriptionResponse:
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

    # retrieve the name of the authors that have published more than a specified nr of books
    async def get_authors_by_number_of_published_books(self) -> list:
        """
        Retrieve a list of authors who have published more than a specified number of books.

        This method performs a join between the Author and Book tables, groups the result by author name,
        and filters to include only those authors whose total number of published books exceeds `self.nr_of_books`.
        The result is ordered in descending order based on the number of published books.

        Returns:
            List[dict]: A list of dictionaries where each dictionary contains:
                - 'author_name' (str): The name of the author.
                - 'nr_of_books' (int): The total number of books published by the author.
        """

        number_of_books = func.count(Book.book_id)
        stmt = (
            select(
                Author.name,
                number_of_books,
            )
            .join(Book, Book.author_id == Author.id)
            .group_by(User.name)
            .order_by(desc(number_of_books))
            .having(number_of_books > self.nr_of_books)
        )
        result = (await self.async_session.execute(stmt)).all()
        data = [
            {"author_name": author, "nr_of_books": nr_of_books}
            for author, nr_of_books in result
        ]

        return data

    # authors with no books
    async def get_authors_with_no_published_books(self):
        """
        Retrieve a list of authors who have not published any books.

        This method uses a subquery to select all author IDs that appear in the Book table.
        It then returns all authors whose IDs are not in that list, indicating that they have
        no books associated with them.

        Returns:
            list: A list of Author model instances who have not published any books.
        """
        subquery = select(Book.author_id).scalar_subquery()
        stmt = select(Author).where(~Author.id.in_(subquery))
        result = (await self.async_session.execute(stmt)).scalars().all()
        return result

    #  top 3 most paid authors
    async def top_three_paid_authors(self):
        """
        Retrieve the top 3 highest-paid authors based on total sales.

        Returns:
            list[dict]: A list of dictionaries containing the author's name and their total sales,
                        ordered from highest to lowest sales.
        """
        stmt = (
            select(Author.name, Author.total_sales)
            .order_by(desc(Author.total_sales))
            .limit(3)
        )

        result = (await self.async_session.execute(stmt)).all()
        return [
            {"author name": author, "total sales": total_sales}
            for author, total_sales in result
        ]

    # retrive the name of the authors,total_books_sold that have sold atleast nr of books
    async def authors_that_sold_more_than_a_specific_nr_of_books(self):
        """
        Retrieve authors who have sold more than a specified number of books.

        This method calculates the total number of books sold for each author by summing
        the quantities of their books ordered (from the OrderItem table). It returns
        only those authors whose total number of books sold exceeds the threshold defined
        in `self.specified_nr_of_books`.

        Returns:
            list[dict]: A list of dictionaries, each containing:
                - 'author name': Name of the author.
                - 'number of books sold': Total number of books sold by the author.
        """
        total_books_sold = func.coalesce(func.sum(OrderItem.quantity), 0)
        stmt = (
            select(Author.name, total_books_sold)
            .join(Book, Book.author_id == Author.id)
            .join(OrderItem, OrderItem.book_id == Book.book_id)
            .group_by(Author.id, Author.name)
            .having(total_books_sold > self.specified_nr_of_books)
            .order_by(desc(total_books_sold))
        )

        result = (await self.async_session.execute(stmt)).all()
        return [
            {"author name": author, "number of books sold": books}
            for author, books in result
        ]

    async def authors_revenue(self):
        """
        Retrieve revenue statistics for each author, grouped by their books.

        Returns:
            List[Dict]: A list of dictionaries, each containing:
                - author name (str): The name of the author.
                - book title (str): The title of the book.
                - total revenue per book (Decimal): Total revenue generated by the book.
                - units sold (int): Total number of units sold for the book.
                - author total revenue (Decimal): Total revenue generated by all books of the author.

        Notes:
            - Authors are ordered by total revenue (descending).
            - Uses a subquery to compute total revenue per author to avoid exposing the author's ID.
        """

        revenue_per_author = (
            select(
                Author.id.label("author_id"),
                func.coalesce(func.sum(OrderItem.items_total_price), 0).label(
                    "total_revenue"
                ),
            )
            .join(Book, Book.book_id == OrderItem.book_id)
            .join(Author, Author.id == Book.author_id)
            .group_by(Author.id)
        ).subquery()

        total_units_sold = func.coalesce(func.sum(OrderItem.quantity), 0)
        total_revenue_per_book = func.coalesce(func.sum(OrderItem.items_total_price), 0)
        stmt = (
            select(
                Author.name,
                Book.title,
                total_revenue_per_book,
                total_units_sold,
                revenue_per_author.c.total_revenue,
            )
            .join(Book, Book.author_id == Author.id)
            .join(OrderItem, OrderItem.book_id == Book.book_id)
            .join(revenue_per_author, Author.id == revenue_per_author.c.author_id)
            .group_by(
                Book.book_id,
                Author.name,
                Author.total_sales,
                revenue_per_author.c.author_id,
                revenue_per_author.c.total_revenue,
            )
            .order_by(desc(Author.total_sales))
        )
        result = (await self.async_session.execute(stmt)).all()
        return [
            {
                "author name": author,
                "book title": book_title,
                "total revenue per book": book_revenue,
                "units sold": units_sold,
                "author total revenue": author_revenue,
            }
            for author, book_title, book_revenue, units_sold, author_revenue in result
        ]

    # Best-Selling Book per Author
    # For each author, find the single best-selling book based on total quantity sold.
    async def author_best_selling_book(self):
        """
        Retrieves the best-selling book for each author based on total quantity sold.

        This method calculates the sum of sold quantities for each book and ranks them
        using the SQL ROW_NUMBER() window function. It then selects only the top-ranked
        (i.e., best-selling) book per author.

        Returns:
            A list of tuples containing:
                - author_id (UUID): The ID of the author.
                - book_title (str): The title of the best-selling book.
                - total_quantity (int): The total number of units sold for that book.

        Notes:
            - Results are ordered by total_quantity in descending order.
            - Books with the same quantity will be ranked by their appearance in the result set.
        """
        books_with_sales = (
            select(
                Author.id.label("author_id"),
                Author.name.label("author_name"),
                Book.title.label("book_title"),
                func.sum(OrderItem.quantity).label("total_quantity"),
                func.row_number()
                .over(
                    partition_by=Author.id, order_by=func.sum(OrderItem.quantity).desc()
                )
                .label("rank"),
            )
            .select_from(Book)
            .join(OrderItem, OrderItem.book_id == Book.book_id)
            .join(Author, Author.id == Book.author_id)
            .group_by(Author.id, Author.name, Book.title, Book.book_id)
            .cte("ranked_books")
        )

        # OrderItem.book_id
        stmt = (
            select(
                books_with_sales.c.author_id,
                books_with_sales.c.book_title,
                books_with_sales.c.total_quantity,
            )
            .where(books_with_sales.c.rank == 1)
            .order_by(desc(books_with_sales.c.total_quantity))
        )
        result = (await self.async_session.execute(stmt)).all()
        return [
            {
                "author_id": author_id,
                "book_title": book_title,
                "total_quantity": total_quantity,
            }
            for author_id, book_title, total_quantity in result
        ]
