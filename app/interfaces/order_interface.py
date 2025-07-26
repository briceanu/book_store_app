from abc import ABC ,abstractmethod


class AbstractOrderInterface(ABC):
    """
    Abstract base class for defining the interface of an order system.

    Any class that inherits from this interface must implement the `place_order` method,
    which defines how an order is placed within the system.
    """


    @abstractmethod
    def place_order(self) -> None:
        pass