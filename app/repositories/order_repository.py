from app.interfaces.order_interface import AbstractOrderInterface
from app.models.app_models import User, Book, OrderItem, Order, Author
from app.schemas.order_schema import OrderItemSchemaCreate, OrderPlaceSuccessfully
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import load_only, noload
from fastapi.exceptions import HTTPException
from fastapi import status
from collections import defaultdict
from decimal import Decimal
from dataclasses import dataclass
from app.repositories.order_email_task import create_pdf_and_send_email_task


@dataclass
class OrderRepository(AbstractOrderInterface):
    user: User | None = None
    order_data: OrderItemSchemaCreate | None = None
    async_session: AsyncSession | None = None

    async def place_order(self) -> OrderPlaceSuccessfully:
        try:
            client_supplied_product_ids = [
                product_id.book_id for product_id in self.order_data.items
            ]

            stmt = (
                select(Book)
                .options(
                    load_only(
                        Book.book_id, Book.price, Book.number_of_items, Book.author_id
                    ),
                    noload("*"),
                )
                .where(Book.book_id.in_(client_supplied_product_ids))
            )

            result = await self.async_session.execute(stmt)
            valid_products_in_db = result.scalars().all()
            all_product_ids = [book.book_id for book in valid_products_in_db]
            valid_author_ids = [book.author_id for book in valid_products_in_db]
            for product_id in client_supplied_product_ids:
                if product_id not in all_product_ids:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"No book with the id {product_id}",
                    )

            # Create lookup dictionaries
            book_lookup_price = {
                book.book_id: book.price for book in valid_products_in_db
            }
            book_lookup_quantity = {
                book.book_id: book.number_of_items for book in valid_products_in_db
            }
            ordered_quantities = {
                item.book_id: item.quantity for item in self.order_data.items
            }
            order_items_list = []
            items_total_price_list = []
            data_to_send_as_pdf = []
            # get authors from db
            stmt = (
                select(Author)
                .options(load_only(Author.id, Author.total_sales), noload("*"))
                .where(Author.id.in_(valid_author_ids))
            )
            authors = (await self.async_session.execute(stmt)).unique().scalars().all()

            for item in self.order_data.items:
                book_price = book_lookup_price.get(item.book_id)
                book_quantity = book_lookup_quantity.get(item.book_id)
                items_total_price = item.quantity * book_price
                items_total_price_list.append(items_total_price)

                if item.quantity > book_quantity:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"There {'are' if book_quantity > 1 else 'is'} only {book_quantity} "
                        f"item{'s' if book_quantity > 1 else ''} left. "
                        f"Product ID: {item.book_id}",
                    )

                order_table = OrderItem(
                    book_id=item.book_id,
                    quantity=item.quantity,
                    book_price=book_price,
                    items_total_price=items_total_price,
                )
                order_items_list.append(order_table)
                # generate data to send in the pdf
                data_to_send_as_pdf.append(
                    {
                        "book_id": item.book_id,
                        "quantity": item.quantity,
                        "book_price": book_price,
                        "items_total_price": items_total_price,
                    }
                )
            total_price = sum(items_total_price_list)
            if self.user.balance < total_price:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient funds. Available: {self.user.balance}, Required: {total_price}",
                )

            # decrese the amount of money of the user from the account
            self.user.balance -= total_price

            order_table = Order(
                user_id=self.user.id,
                items=order_items_list,
                order_status=item.order_status,
                order_total_price=total_price,
            )

            author_id_total_price_dict = defaultdict(Decimal)
            for book in valid_products_in_db:
                book_id = book.book_id
                author_id = book.author_id
                price = book_lookup_price[book.book_id]
                quantity = ordered_quantities.get(book_id, 0)
                total_price = price * quantity
                author_id_total_price_dict[author_id] += total_price

                # Check constraint before decreasing
                if quantity > book.number_of_items:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"There {'are' if book_quantity > 1 else 'is'} only {book_quantity} "
                        f"item{'s' if book_quantity > 1 else ''} left. "
                        f"Product ID: {item.book_id}",
                    )
            for author in authors:
                author.total_sales += author_id_total_price_dict.get(author.id)

            self.async_session.add(order_table)
            await self.async_session.commit()
            # use celery to create the pdf and send email
            create_pdf_and_send_email_task.delay(self.user.email,data_to_send_as_pdf)
            return OrderPlaceSuccessfully(
                success="Order placed successfully.An email has been sent to your email address."
            )
        except Exception as e:
            await self.async_session.rollback()
            raise e
        finally:
            await self.async_session.close()
