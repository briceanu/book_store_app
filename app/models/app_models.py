import datetime
import uuid
from datetime import date, datetime

from sqlalchemy import (
    DECIMAL,
    JSON,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    func,
    Boolean
)
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all models"""

    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_`%(constraint_name)s`",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )
    type_annotation_map = {
        datetime: DateTime(timezone=True),
    }

 
class User(Base):
    """
    Represents a base user in the system.

    This model defines common attributes for a standard user, including
    authentication details, profile information, and account status.
    It also supports SQLAlchemy's joined-table inheritance to allow
    specialized user types like 'Author'.

    Table: user

    Attributes:
        id (uuid.UUID): Unique identifier for the user.
        name (str): Unique username or display name.
        password (str): Hashed password used for authentication.
        email (str): Unique email address.
        created_at (datetime): Timestamp when the user was created.
        scopes (list[str]): List of permission scopes or roles assigned to the user.
        image_url (str | None): Optional URL to the user's profile image.
        is_active (bool): Flag indicating whether the user account is active.
        type (str): Discriminator column used for polymorphic identity (e.g., 'user', 'author').
        balance (float): Monetary balance associated with the user's account.

    Notes:
        - This class is used as the base for joined-table inheritance.
        - The `type` field enables polymorphic identity for subclasses like Author.
    """
    
    __tablename__ = "user"

    id: Mapped[uuid.UUID] = mapped_column(
        default=lambda: uuid.uuid4(), primary_key=True, unique=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    scopes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=[])
    image_url: Mapped[str] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    type: Mapped[str] = mapped_column(String(50), nullable=False, default="user")
    balance: Mapped[float] = mapped_column(DECIMAL(4, 2), default=0.00)

    __mapper_args__ = {
        "polymorphic_on": "type",
        "polymorphic_identity": "user",
    }

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name!r})"


author_book_association_table = Table(
    "author_book_association_table",
    Base.metadata,
    Column("author_id", ForeignKey("author.id")),
    Column("book_id", ForeignKey("book.id")),
)


class Author(User):
    """
    Represents an author, a specialized user with additional fields.

    Inherits:
        User: Includes user fields like balance and email.

    Attributes:
        `autor_id (uuid.UUID)`: Foreign key linking to the parent user.
        `description (str | None)`: Optional biography or profile for the author.
        `total_sales (float)`: Total sales attributed to the author.

    Notes:
        - Identified by `polymorphic_identity='author'`.
        - Stored in a separate table from base User.
    """

    __tablename__ = "author"
    id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id"), primary_key=True, use_existing_column=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=True)
    total_sales: Mapped[float] = mapped_column(DECIMAL(6, 2), default=0.00)
    books: Mapped[list["Book"]] = relationship(
        back_populates="authors", secondary=author_book_association_table
    )
    __mapper_args__ = {
        "polymorphic_identity": "author",
    }

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name!r})"


class Book(Base):
    """
    Represents a book entity in the system.

    Attributes:
        `id (uuid.UUID)`: Unique identifier for the book (primary key).
        `title (str)`: Title of the book (max 100 characters).
        `description (str)`: Detailed summary or synopsis of the book.
        `date_of_publish (date)`: The date the book was or will be published.
        `cover_image_url (str)`: URL pointing to the book’s cover image.
        `price (float)`: Price of the book in decimal format (max 9999.99).
        `status (str)`: Publication status of the book. Expected values are 'draft' or 'published'.
        `author (list[Author])`: List of authors associated with the book via a many-to-many relationship.

    Notes:
        - Uses a secondary association table (`author_book_association_table`) to establish many-to-many relationships between books and authors.
        - The `status` field is expected to be limited to predefined states such as 'draft' and 'published'. Consider using an Enum for stricter validation.
    """

    __tablename__ = "book"
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=lambda: uuid.uuid4(), nullable=False
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    date_of_publish: Mapped[date] = mapped_column(Date, nullable=False)
    cover_images: Mapped[list["CoverImage"]] = relationship(
        "CoverImage", back_populates="book"
    )
    price: Mapped[float] = mapped_column(DECIMAL(6, 2), default=0.00, nullable=False)
    status: Mapped[str] = mapped_column(String(), nullable=False)  # draft | published
    authors: Mapped[list[Author]] = relationship(
        back_populates="books", secondary=author_book_association_table
    )

    def __repr__(self):
        return f"{self.__class__.__title__}({self.title!r})"


class CoverImage(Base):
    """
    Represents a cover image associated with a specific book.

    Attributes:
        `image_id (UUID)`: Unique identifier for the image.
        `image_url (str)`: URL pointing to the location of the cover image.
        `book_id (UUID)`: Foreign key referencing the associated Book.
        `book (Book)`: Relationship to the Book model.
    """

    __tablename__ = "cover_image"

    image_id: Mapped[uuid.UUID] = mapped_column(
        default=lambda: uuid.uuid4(), primary_key=True, unique=True
    )
    image_url: Mapped[str] = mapped_column(String, nullable=False)
    book_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("book.id"), nullable=False)
    book: Mapped["Book"] = relationship("Book", back_populates="cover_images")

    def __repr__(self):
        return f"<CoverImage(id={self.image_id}, url={self.image_url}, book_id={self.book_id})>"


class OrderItem(Base):
    """
    Represents an individual item in an order.

    Attributes:
        `order_item_id (UUID)`: Unique identifier for the order item.
        `book_id (UUID)`: Foreign key referencing the purchased Book.
        `quantity (int)`: Quantity of this book in the order.
        `book_price (int)`: Price of a single unit of the book at the time of purchase.
        `total_price (float)`: Total cost for this item (quantity * book_price).
        `order_id (UUID)`: Foreign key referencing the parent Order.
        `order (Order)`: Relationship to the Order model.
    """

    __tablename__ = "order_item"
    order_item_id: Mapped[uuid.UUID] = mapped_column(
        default=lambda: uuid.uuid4(), primary_key=True, unique=True
    )
    book_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("book.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    book_price: Mapped[int] = mapped_column()
    items_total_price: Mapped[float] = mapped_column(DECIMAL(6, 2), nullable=False)
    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("order.order_id"), nullable=False
    )
    order: Mapped["Order"] = relationship(back_populates="items")

    def __repr__(self):
        return (
            f"<OrderItem(id={self.order_item_id}, book_id={self.book_id}, "
            f"quantity={self.quantity}, book_price={self.book_price}, "
            f"total={self.items_total_price}, order_id={self.order_id})>"
        )


class Order(Base):
    """
    Represents a customer order containing one or more order items.

    Attributes:
        `order_id (UUID)`: Unique identifier for the order.
        `user_id (UUID)`: Foreign key referencing the user who placed the order.
        `items (List[OrderItem])`: List of items included in the order.
        `total_price_per_order (float)`: Total cost of all items in the order.
        `created_at (datetime)`: Timestamp of when the order was placed.
        `order_status (str`): Current status of the order (e.g., 'pending', 'shipped').

    """

    __tablename__ = "order"
    order_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=lambda: uuid.uuid4(), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"), nullable=False)
    items: Mapped[list["OrderItem"]] = relationship(OrderItem, back_populates="order")
    order_total_price: Mapped[float] = mapped_column(DECIMAL(6, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )
    order_status: Mapped[str] = mapped_column(String(), nullable=False)

    def __repr__(self):
        return (
            f"<Order(id={self.order_id}, user_id={self.user_id}, "
            f"total_price={self.order_total_price}, status={self.order_status}, "
            f"created_at={self.created_at.isoformat()})>"
        )
