from abc import ABC,abstractmethod



class AbstractAuthorInterface(ABC):
    @abstractmethod
    def set_author_description(self):
        pass