
from typing import Optional, List
from test_proj.models.schemas.product import Product
from test_proj.interfaces.product_repository import ProductRepository

class ProductService:
    def __init__(self, repository: ProductRepository):
        self.repository = repository

    def get_product(self, product_id: int) -> Optional[Product]:
        return self.repository.get_by_id(product_id)

    def create_product(self, product: Product) -> None:
        self.repository.add(product)

    def list_products(self) -> List[Product]:
        return self.repository.list_all()