from abc import ABC, abstractmethod
class ProductSchema():
    pass

class BookRepository(ABC):
    @abstractmethod
    def get_all_products(self) -> list[ProductSchema]:
        pass

    @abstractmethod
    def remove_product(self)->None:
        pass