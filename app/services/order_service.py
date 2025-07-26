from app.repositories.order_repository import OrderRepository


class OrderService:
    def __init__(self, repository: OrderRepository):
        self.repository = repository

    async def buy_books(self):
        return await self.repository.place_order()
